@echo off
setlocal
cd /d "%~dp0"
set "APP_PYTHON=.venv\Scripts\python.exe"

if not exist "%APP_PYTHON%" (
  echo [1/3] Creating the local Python environment...
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if errorlevel 1 goto :failed
)

echo [2/3] Checking required packages...
"%APP_PYTHON%" -c "import flask, waitress, numpy, lxml, openpyxl" >nul 2>nul
if errorlevel 1 (
  "%APP_PYTHON%" -m pip install -r requirements.txt
  if errorlevel 1 goto :failed
)

echo [3/3] Starting LS900 analyzer...
"%APP_PYTHON%" run_app.py
goto :eof

:failed
echo.
echo Setup failed. Check the message above, then try again.
pause
exit /b 1
