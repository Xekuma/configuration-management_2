import argparse
import os
import re
import sys
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


def main():
    args = create_parser().parse_args()
    validate_args(args)

    config = {
        "package": args.package,
        "repo": args.repo,
        "test_mode": args.test_mode == "true",
        "version": args.version,
        "output": args.output,
        "max_depth": int(args.max_depth),
        "filter": args.filter_substr or "",
    }
    for key, val in config.items():
        print(f"{key}: {val}")


if __name__ == "__main__":
    main()