@echo off
setlocal
cd /d %~dp0..
if not exist ".venv\Scripts\activate.bat" (
  echo [ERROR] No existe el entorno .venv. Ejecuta primero scripts\setup_venv.cmd
  pause
  exit /b 1
)
call .\.venv\Scripts\activate.bat
python -m streamlit run ui\app_streamlit.py
endlocal
