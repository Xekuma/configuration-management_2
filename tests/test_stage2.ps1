Write-Host "=== ТЕСТ: Этап 2  ===`n"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "-------------------------------------------------------"
Write-Host "=== Корректный запуск  ==="
python src/main.py --package express --repo https://registry.npmjs.org --test-mode false --version 4.19.2 --output graph.svg --max-depth 3

Write-Host "-------------------------------------------------------"
Write-Host "=== Корректный запуск c пакетом без зависимостей ==="
python src/main.py --package lodash --repo https://registry.npmjs.org --test-mode false --version 4.17.21 --output graph.svg --max-depth 3

Write-Host "-------------------------------------------------------"
Write-Host "=== Запуск с несуществующей версией пакета === "
python src/main.py --package express --repo https://registry.npmjs.org --test-mode false --version 99.99.99 --output graph.svg --max-depth 3