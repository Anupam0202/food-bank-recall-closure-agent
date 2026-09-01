@echo off
setlocal
cd /d "%~dp0.."

echo [1/7] Locating CPython 3.12...
where py >nul 2>&1
if not errorlevel 1 (
  py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
  if not errorlevel 1 goto use_launcher
)

set "DIRECT_PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if exist "%DIRECT_PY%" goto use_direct

echo ERROR: CPython 3.12 was not found.
echo Install it from https://www.python.org/downloads/ and enable the Python launcher.
exit /b 1

:use_launcher
echo [2/7] Creating a clean virtual environment with the Windows Python launcher...
py -3.12 -m venv --clear .venv
if errorlevel 1 exit /b 1
goto install

:use_direct
echo [2/7] Creating a clean virtual environment with %DIRECT_PY%...
"%DIRECT_PY%" -m venv --clear .venv
if errorlevel 1 exit /b 1

:install
echo [3/7] Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo [4/7] Installing compatible pinned dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1

echo [5/7] Checking imports and dependency consistency...
".venv\Scripts\python.exe" -m pip check
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" scripts\check_dependency_compatibility.py
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" scripts\adk_import_smoke.py
if errorlevel 1 exit /b 1

echo [6/7] Running the regression test suite...
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 exit /b 1

echo [7/7] Verifying real FastAPI health and dashboard rendering...
".venv\Scripts\python.exe" scripts\http_smoke.py
if errorlevel 1 exit /b 1

echo.
echo Setup complete. Start the application with:
echo scripts\run_windows.cmd
endlocal
