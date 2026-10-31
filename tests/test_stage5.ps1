Write-Host "=== ТЕСТ: Этап 5 (Визуализация Graphviz и генерация SVG) ===`n"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "-------------------------------------------------------"
Write-Host "=== 1. Визуализация пакета №1: chalk@4.1.2 (chalk.svg) ==="
python src/main.py --package chalk --repo https://registry.npmjs.org --test-mode false --version 4.1.2 --output chalk.svg --max-depth 4

Write-Host "-------------------------------------------------------"
Write-Host "=== 2. Визуализация пакета №2: http-errors@2.0.0 (http_errors.svg) ==="
python src/main.py --package http-errors --repo https://registry.npmjs.org --test-mode false --version 2.0.0 --output http_errors.svg --max-depth 3

Write-Host "-------------------------------------------------------"
Write-Host "=== 3. Визуализация пакета №3: body-parser@1.20.2 (body_parser.svg) ==="
python src/main.py --package body-parser --repo https://registry.npmjs.org --test-mode false --version 1.20.2 --output body_parser.svg --max-depth 2

Write-Host "-------------------------------------------------------"
Write-Host "=== 4. Визуализация тестового репозитория с циклом (test_graph.svg) ==="
python src/main.py --package A --repo tests/test_repo.txt --test-mode true --version 1.0.0 --output test_graph.svg --max-depth 4

Write-Host "-------------------------------------------------------"
Write-Host "=== 5. Визуализация репозитория с версиями (test_versions.svg) ==="
python src/main.py --package A --repo tests/test_versions.txt --test-mode true --version 2.0 --output test_versions.svg --max-depth 4