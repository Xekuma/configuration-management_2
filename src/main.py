import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse


def check_test_mode(val, errors):
    if val not in ("true", "false"):
        msg = f"Ошибка --test-mode: нужно 'true'/'false', дано '{val}'."
        errors.append(msg)
    return val == "true"


def check_package(pkg, is_test, errors):
    if not pkg or not pkg.strip():
        errors.append("Ошибка --package: имя пакета пустое.")
    elif is_test and not re.match(r"^[A-Z]+$", pkg):
        msg = f"Ошибка --package: в тесте нужны буквы A-Z ('{pkg}')."
        errors.append(msg)
    elif not is_test:
        pat = r"^(@[a-z0-9-~][a-z0-9-._~]*/)?[a-z0-9-~][a-z0-9-._~]*$"
        if not re.match(pat, pkg):
            errors.append(f"Ошибка --package: неверное имя '{pkg}'.")


def check_repo(repo, is_test, errors):
    if not repo or not repo.strip():
        errors.append("Ошибка --repo: адрес или путь пустой.")
    elif is_test and not os.path.isfile(repo):
        errors.append(f"Ошибка --repo: файл '{repo}' не найден.")
    elif not is_test:
        parsed = urlparse(repo)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            errors.append(f"Ошибка --repo: неверный URL '{repo}'.")


def check_version_and_output(ver, out, errors):
    ver_pat = r"^(\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?|latest)$"
    if not ver or not re.match(ver_pat, ver):
        errors.append(f"Ошибка --version: неверный формат '{ver}'.")

    bad_chars = r'<>:"|?*'
    if not out or not out.endswith(".svg") or len(out) <= 4:
        errors.append(f"Ошибка --output: '{out}' должен быть '.svg'.")
    elif any(c in out for c in bad_chars):
        errors.append(f"Ошибка --output: запрещённые символы в '{out}'.")


def check_depth_and_filter(depth_str, flt, errors):
    try:
        if int(depth_str) <= 0:
            errors.append("Ошибка --max-depth: число должно быть > 0.")
    except ValueError:
        errors.append(f"Ошибка --max-depth: '{depth_str}' не число.")

    if flt is not None:
        if flt == "" or not re.match(r"^[a-zA-Z0-9._-]+$", flt):
            errors.append(f"Ошибка --filter: недопустимая строка '{flt}'.")


def validate_args(args):
    errors = []
    is_test = check_test_mode(args.test_mode, errors)
    check_package(args.package, is_test, errors)
    check_repo(args.repo, is_test, errors)
    check_version_and_output(args.version, args.output, errors)
    check_depth_and_filter(args.max_depth, args.filter_substr, errors)

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)


def create_parser():
    p = argparse.ArgumentParser(description="Визуализатор зависимостей.")
    p.add_argument("--package", required=True, help="Имя пакета.")
    p.add_argument("--repo", required=True, help="URL или путь к файлу.")
    p.add_argument("--test-mode", required=True, help="Режим: true/false.")
    p.add_argument("--version", required=True, help="Версия пакета.")
    p.add_argument("--output", required=True, help="Имя SVG-файла.")
    p.add_argument("--max-depth", required=True, help="Глубина анализа.")
    p.add_argument("--filter", dest="filter_substr", default=None)
    return p


def clean_version(ver_str):
    if not isinstance(ver_str, str):
        return "latest"
    cleaned = re.sub(r"^[\^~>=<v\s]+", "", ver_str.strip())
    if " " in cleaned:
        cleaned = cleaned.split()[0]
    return cleaned if re.match(r"^\d", cleaned) else "latest"


def fetch_npm_deps(repo, package, version):
    url = f"{repo.rstrip('/')}/{package}/{version}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            deps = data.get("dependencies", {})
            if not isinstance(deps, dict):
                return []
            res = []
            for name, vspec in deps.items():
                res.append((name, clean_version(vspec)))
            return res
    except urllib.error.HTTPError as e:
        print(f"Ошибка HTTP {e.code}: {package}@{version}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Ошибка сети для {package}: {e}", file=sys.stderr)
        return []


def load_test_repo(file_path):
    graph = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                pkg, deps_str = line.split(":", 1)
                pkg = pkg.strip()
                deps = re.findall(r"[A-Z]+", deps_str)
                graph[pkg] = deps
    except OSError as e:
        print(f"Ошибка чтения файла '{file_path}': {e}", file=sys.stderr)
        sys.exit(1)
    return graph


def make_fetcher(is_test, repo):
    if is_test:
        test_data = load_test_repo(repo)
        return lambda pkg, _ver: [(d, "latest") for d in test_data.get(pkg, [])]
    return lambda pkg, ver: fetch_npm_deps(repo, pkg, ver)


def dfs_collect(pkg, ver, depth, cfg, state):
    flt = cfg["filter"]
    if (flt and flt in pkg) or depth > cfg["max_depth"]:
        return

    prev_depth = state["visited"].get(pkg)
    if prev_depth is not None and depth >= prev_depth:
        return
    state["visited"][pkg] = depth

    state["in_path"].add(pkg)
    raw_deps = cfg["fetch"](pkg, ver)
    v_deps, v_vers = [], {}
    for name, dver in raw_deps:
        if not (flt and flt in name):
            v_deps.append(name)
            v_vers[name] = dver
    state["graph"][pkg] = v_deps

    for dep in v_deps:
        if dep in state["in_path"]:
            state["cycles"].add((pkg, dep))
        elif depth < cfg["max_depth"]:
            dfs_collect(dep, v_vers.get(dep, "latest"), depth + 1, cfg, state)
    state["in_path"].remove(pkg)


def build_dependency_graph(args):
    is_test = args.test_mode == "true"
    cfg = {
        "max_depth": int(args.max_depth),
        "filter": args.filter_substr,
        "fetch": make_fetcher(is_test, args.repo),
    }
    state = {"graph": {}, "visited": {}, "in_path": set(), "cycles": set()}
    dfs_collect(args.package, args.version, 1, cfg, state)
    return state["graph"], state["cycles"]


def print_results(graph, cycles):
    if not graph:
        print("Граф пуст (корневой пакет отфильтрован или не найден).")
        return
    print("Построенный граф зависимостей:")
    for pkg, deps in graph.items():
        deps_str = ", ".join(deps) if deps else "нет зависимостей"
        print(f"  {pkg} -> [{deps_str}]")
    if cycles:
        print("\nОбнаружены циклические зависимости:")
        for src, dst in sorted(cycles):
            print(f"  {src} -> {dst} (цикл)")


def main():
    args = create_parser().parse_args()
    validate_args(args)
    graph, cycles = build_dependency_graph(args)
    print_results(graph, cycles)


if __name__ == "__main__":
    main()