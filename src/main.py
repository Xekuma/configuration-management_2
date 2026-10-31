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
    ver_pat = r"^(\d+(\.\d+){1,2}(-[a-zA-Z0-9.-]+)?|latest)$"
    if not ver or not re.match(ver_pat, ver):
        errors.append(f"Ошибка --version: неверный формат '{ver}'.")

    bad_chars = r'<>:"|?*'
    l4 = max(0, 4)
    if not out or not out.endswith(".svg") or len(out) <= l4:
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


def check_reverse(val, errors):
    if val not in ("true", "false"):
        msg = f"Ошибка --reverse: нужно 'true'/'false', дано '{val}'."
        errors.append(msg)


def validate_args(args):
    errors = []
    is_test = check_test_mode(args.test_mode, errors)
    check_package(args.package, is_test, errors)
    check_repo(args.repo, is_test, errors)
    check_version_and_output(args.version, args.output, errors)
    check_depth_and_filter(args.max_depth, args.filter_substr, errors)
    check_reverse(args.reverse, errors)

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
    p.add_argument("--reverse", default="false", help="Обратные: true/false.")
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
            return [(k, clean_version(v)) for k, v in deps.items()]
    except urllib.error.HTTPError as e:
        print(f"Ошибка HTTP {e.code}: {package}@{version}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Ошибка сети для {package}: {e}", file=sys.stderr)
        return []


def fetch_npm_reverse(repo, package):
    base = repo.rstrip("/")
    url = f"{base}/-/v1/search?text={package}&size=6"
    hdrs = {"Accept": "application/json", "User-Agent": "DepGraphCLI/1.0"}
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            res = []
            for item in data.get("objects", []):
                pkg = item.get("package", {})
                name = pkg.get("name")
                ver = clean_version(pkg.get("version", "latest"))
                if name and name != package:
                    res.append((name, ver))
            return res
    except Exception as e:
        print(f"Ошибка поиска обратных для {package}: {e}", file=sys.stderr)
        return []


def ver_tuple(v_str):
    nums = [int(x) for x in re.findall(r"\d+", str(v_str))]
    return tuple(nums) if nums else (0,)


def match_ver(v_str, op, target):
    v, t = ver_tuple(v_str), ver_tuple(target)
    ops = {
        "==": v == t, "=": v == t, ">=": v >= t,
        "<=": v <= t, ">": v > t, "<": v < t,
    }
    return ops.get(op, v == t)


def parse_pkg_def(raw_left):
    m = re.match(r"^([A-Z]+)(?:v|@)?(\d+(?:\.\d+)*)?$", raw_left.strip())
    if not m:
        return raw_left.strip(), "latest"
    return m.group(1), (m.group(2) or "latest")


def parse_dep_tokens(deps_str):
    pat = r"([A-Z]+)(?:(>=|<=|==|=|>|<|v|@)(\d+(?:\.\d+)*))?"
    res = []
    for name, op, ver in re.findall(pat, deps_str):
        norm_op = "==" if op in ("v", "@", "=") else (op or "any")
        res.append((name, norm_op, ver or "latest"))
    return res


def load_test_repo(file_path):
    repo_data = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                left, right = line.split(":", 1)
                pkg, ver = parse_pkg_def(left)
                deps = parse_dep_tokens(right)
                repo_data.setdefault(pkg, {})[ver] = deps
    except OSError as e:
        print(f"Ошибка чтения файла '{file_path}': {e}", file=sys.stderr)
        sys.exit(1)
    return repo_data


def resolve_test_ver(repo_data, pkg, op, target_ver):
    versions = list(repo_data.get(pkg, {}).keys())
    if not versions:
        return None
    if op == "any" or target_ver == "latest":
        return max(versions, key=ver_tuple)
    matched = [v for v in versions if match_ver(v, op, target_ver)]
    return max(matched, key=ver_tuple) if matched else None


def fmt_test_node(pkg, ver, repo_data):
    vers = repo_data.get(pkg, {})
    if ver == "latest" and "latest" in vers:
        return pkg
    return f"{pkg}v{ver}" if ver and ver != "latest" else pkg


def build_resolved_test_graph(repo_data):
    resolved = {}
    for pkg, vers_dict in repo_data.items():
        for ver, specs in vers_dict.items():
            src = fmt_test_node(pkg, ver, repo_data)
            resolved[src] = []
            for d_pkg, op, d_ver in specs:
                r_ver = resolve_test_ver(repo_data, d_pkg, op, d_ver)
                if r_ver is not None:
                    dst = fmt_test_node(d_pkg, r_ver, repo_data)
                    resolved[src].append((dst, r_ver))
    return resolved


def invert_resolved_graph(resolved):
    rev = {node: [] for node in resolved}
    for src, targets in resolved.items():
        for dst, _ in targets:
            rev.setdefault(dst, []).append((src, "latest"))
    return rev


def make_test_fetcher(file_path, is_reverse):
    repo_data = load_test_repo(file_path)
    resolved = build_resolved_test_graph(repo_data)
    if is_reverse:
        resolved = invert_resolved_graph(resolved)
    return repo_data, (lambda node, _ver: resolved.get(node, []))


def get_start_test_node(repo_data, pkg, ver):
    if pkg not in repo_data:
        return pkg
    r_ver = resolve_test_ver(repo_data, pkg, "==", ver)
    if r_ver is None:
        r_ver = resolve_test_ver(repo_data, pkg, "any", "latest")
    return fmt_test_node(pkg, r_ver, repo_data)


def make_fetcher(is_test, repo, is_reverse=False):
    if is_test:
        _, fetcher = make_test_fetcher(repo, is_reverse)
        return fetcher
    if is_reverse:
        return lambda pkg, _ver: fetch_npm_reverse(repo, pkg)
    return lambda pkg, ver: fetch_npm_deps(repo, pkg, ver)


def is_filtered(pkg, flt):
    return bool(flt and flt in pkg)


def can_visit(pkg, depth, cfg, state):
    if is_filtered(pkg, cfg["filter"]) or depth > cfg["max_depth"]:
        return False
    prev = state["visited"].get(pkg)
    return prev is None or depth < prev


def dfs_collect(pkg, ver, depth, cfg, state):
    if not can_visit(pkg, depth, cfg, state):
        return

    state["visited"][pkg] = depth
    state["in_path"].add(pkg)

    flt = cfg["filter"]
    raw_deps = cfg["fetch"](pkg, ver)
    valid = [(n, v) for n, v in raw_deps if not is_filtered(n, flt)]
    state["graph"][pkg] = [n for n, _ in valid]

    for dep, dver in valid:
        if dep in state["in_path"]:
            state["cycles"].add((pkg, dep))
        elif depth < cfg["max_depth"]:
            dfs_collect(dep, dver, depth + 1, cfg, state)
    state["in_path"].remove(pkg)


def build_dependency_graph(args):
    is_test = args.test_mode == "true"
    is_rev = args.reverse == "true"
    start_pkg = args.package
    if is_test:
        repo_data, fetch_fn = make_test_fetcher(args.repo, is_rev)
        start_pkg = get_start_test_node(repo_data, args.package, args.version)
    else:
        fetch_fn = make_fetcher(False, args.repo, is_rev)

    cfg = {
        "max_depth": int(args.max_depth),
        "filter": args.filter_substr,
        "fetch": fetch_fn,
    }
    state = {"graph": {}, "visited": {}, "in_path": set(), "cycles": set()}
    dfs_collect(start_pkg, args.version, 1, cfg, state)
    return start_pkg, state["graph"], state["cycles"]


def print_reverse_results(target, graph, cycles):
    deps_set = set()
    for pkg, deps in graph.items():
        if pkg != target:
            deps_set.add(pkg)
        deps_set.update(d for d in deps if d != target)
    dependents = sorted(deps_set)
    if not dependents:
        print(f"Обратные зависимости для пакета {target} не найдены.")
        return
    print(f"Обратные зависимости для пакета {target}:")
    print(f"  Пакеты, зависящие от {target}: {', '.join(dependents)}")
    print("\nГраф обратных связей (от кого <- кто зависит):")
    for pkg, deps in graph.items():
        deps_str = ", ".join(deps) if deps else "нет"
        print(f"  {pkg} <- [{deps_str}]")
    if cycles:
        print("\nОбнаружены циклические зависимости:")
        for src, dst in sorted(cycles):
            print(f"  {src} <- {dst} (цикл)")


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
    start_pkg, graph, cycles = build_dependency_graph(args)
    if args.reverse == "true":
        print_reverse_results(start_pkg, graph, cycles)
    else:
        print_results(graph, cycles)


if __name__ == "__main__":
    main()