@echo off
chcp 65001 >nul
for /L %%i in (1,1,5) do (
    echo Try %%i:
    curl -w "Time: %%{time_total}s\n" -s -X POST http://localhost:8000/api/v1/menu/identify -H "Content-Type: application/json" -d "{\"menu_name_ko\":\"김치찌개\"}" -o nul
)
