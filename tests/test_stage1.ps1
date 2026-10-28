Write-Host "=== ТЕСТ: Этап 1  ===`n"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "-------------------------------------------------------"
Write-Host "=== Корректный запуск  ==="
python src/main.py --package express --repo https://registry.npmjs.org --test-mode false --version 4.19.2 --output graph.svg --max-depth 3 --filter debug

Write-Host "-------------------------------------------------------"
Write-Host "=== Ошибка имени пакета  (--package) ==="
python src/main.py --package "INVALID_NAME!" --repo https://registry.npmjs.org --test-mode false --version 4.19.2 --output graph.svg --max-depth 3

Write-Host "-------------------------------------------------------"
Write-Host "=== Ошибка URL или пути к файлу (--repo) ==="
python src/main.py --package express --repo "ftp://invalid-url" --test-mode false --version 4.19.2 --output graph.svg --max-depth 3

Write-Host "-------------------------------------------------------"
Write-Host "=== Ошибка режима работы (--test-mode) ==="
python src/main.py --package express --repo https://registry.npmjs.org --test-mode yes --version 4.19.2 --output graph.svg --max-depth 3

Write-Host "-------------------------------------------------------"
Write-Host "=== Ошибка версии пакета (--version) ==="
python src/main.py --package express --repo https://registry.npmjs.org --test-mode false --version "v1.0" --output graph.svg --max-depth 3

Write-Host "-------------------------------------------------------"
Write-Host "=== Ошибка имени выходного файла (--output) ==="
python src/main.py --package express --repo https://registry.npmjs.org --test-mode false --version 4.19.2 --output graph.png --max-depth 3

Write-Host "-------------------------------------------------------"
Write-Host "=== Ошибка максимальной глубины (--max-depth) ==="
python src/main.py --package express --repo https://registry.npmjs.org --test-mode false --version 4.19.2 --output graph.svg --max-depth -2

Write-Host "-------------------------------------------------------"
Write-Host "=== Ошибка подстроки фильтрации (--filter) ==="
python src/main.py --package express --repo https://registry.npmjs.org --test-mode false --version 4.19.2 --output graph.svg --max-depth 3 --filter "bad filter!"