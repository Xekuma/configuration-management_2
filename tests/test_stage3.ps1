Write-Host "=== ТЕСТ: Этап 3 ===`n"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "-------------------------------------------------------"
Write-Host "=== 1. Тестовый режим: полный обход и обнаружение циклов ==="
python src/main.py --package A --repo tests/test_repo.txt --test-mode true --version 1.0.0 --output graph.svg --max-depth 4

Write-Host "-------------------------------------------------------"
Write-Host "=== 2. Тестовый режим: ограничение глубины (max-depth = 1) ==="
python src/main.py --package A --repo tests/test_repo.txt --test-mode true --version 1.0.0 --output graph.svg --max-depth 1

Write-Host "-------------------------------------------------------"
Write-Host "=== 3. Тестовый режим: фильтрация пакетов (filter = B) ==="
python src/main.py --package A --repo tests/test_repo.txt --test-mode true --version 1.0.0 --output graph.svg --max-depth 4 --filter B

Write-Host "-------------------------------------------------------"
Write-Host "=== 4. Тестовый режим: пакет без зависимостей (пакет G) ==="
python src/main.py --package G --repo tests/test_repo.txt --test-mode true --version 1.0.0 --output graph.svg --max-depth 3

Write-Host "-------------------------------------------------------"
Write-Host "=== 5. Реальный репозиторий npm: транзитивный обход (chalk) ==="
python src/main.py --package chalk --repo https://registry.npmjs.org --test-mode false --version 4.1.2 --output graph.svg --max-depth 4

Write-Host "-------------------------------------------------------"
Write-Host "=== 6. Реальный репозиторий npm: фильтрация (chalk, filter = color) ==="
python src/main.py --package chalk --repo https://registry.npmjs.org --test-mode false --version 4.1.2 --output graph.svg --max-depth 4 --filter color