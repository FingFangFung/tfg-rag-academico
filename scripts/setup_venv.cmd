@echo off
setlocal
cd /d %~dp0..

REM --- Crear venv si no existe ---
if not exist ".venv" (
  echo [SETUP] Creando entorno virtual .venv ...
  python -m venv .venv
)

REM --- Activar venv ---
call .\.venv\Scripts\activate.bat

REM --- Actualizar pip (opcional pero recomendado) ---
python -m pip install --upgrade pip

REM --- Instalar dependencias ---
echo [SETUP] Instalando dependencias de requirements.txt ...
pip install -r requirements.txt

echo.
echo [OK] Entorno preparado. Si aun no tienes .env, copia .env.example a .env y pon tu OPENAI_API_KEY.
pause
endlocal
