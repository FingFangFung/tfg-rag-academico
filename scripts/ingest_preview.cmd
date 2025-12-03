@echo off
setlocal
cd /d %~dp0..
call .\.venv\Scripts\activate.bat
python -m app.ingest
echo.
echo [OK] Previsualización creada en: .\data\processed\chunks_preview.txt
pause
endlocal
