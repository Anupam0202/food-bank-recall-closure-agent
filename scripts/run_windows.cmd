@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo ERROR: Run scripts\setup_windows.cmd first.
  exit /b 1
)
set "AI_MODE=mock"
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8080
endlocal
