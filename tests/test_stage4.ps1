Write-Host "=== ТЕСТ: Этап 4 (Обратные зависимости и контроль версий) ===`n"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "-------------------------------------------------------"
Write-Host "=== 1. Обратные зависимости для листа G (test_repo.txt) ==="
python src/main.py --package G --repo tests/test_repo.txt --test-mode true --version 1.0.0 --output graph.svg --max-depth 4 --reverse true

Write-Host "-------------------------------------------------------"
Write-Host "=== 2. Обратные зависимости для пакета B (ромб + цикл) ==="
python src/main.py --package B --repo tests/test_repo.txt --test-mode true --version 1.0.0 --output graph.svg --max-depth 4 --reverse true

Write-Host "-------------------------------------------------------"
Write-Host "=== 3. Ограничение глубины обратных зависимостей (F, max-depth = 1) ==="
python src/main.py --package F --repo tests/test_repo.txt --test-mode true --version 1.0.0 --output graph.svg --max-depth 1 --reverse true

Write-Host "-------------------------------------------------------"
Write-Host "=== 4. Фильтрация при поиске обратных зависимостей (B, filter = D) ==="
python src/main.py --package B --repo tests/test_repo.txt --test-mode true --version 1.0.0 --output graph.svg --max-depth 4 --filter D --reverse true

Write-Host "-------------------------------------------------------"
Write-Host "=== 5. Контроль версий: прямой обход для Av1.0 (B==1.0, C<2.0) ==="
python src/main.py --package A --repo tests/test_versions.txt --test-mode true --version 1.0 --output graph.svg --max-depth 4

Write-Host "-------------------------------------------------------"
Write-Host "=== 6. Контроль версий: прямой обход для Av2.0 (B>=1.1, C>=2.0 + цикл) ==="
python src/main.py --package A --repo tests/test_versions.txt --test-mode true --version 2.0 --output graph.svg --max-depth 4

Write-Host "-------------------------------------------------------"
Write-Host "=== 7. Контроль версий: обратные зависимости для Dv1.0 ==="
python src/main.py --package D --repo tests/test_versions.txt --test-mode true --version 1.0 --output graph.svg --max-depth 4 --reverse true

Write-Host "-------------------------------------------------------"
Write-Host "=== 8. Реальный репозиторий npm: обратные зависимости (cookie) ==="
python src/main.py --package cookie --repo https://registry.npmjs.org --test-mode false --version 0.6.0 --output graph.svg --max-depth 1 --reverse true