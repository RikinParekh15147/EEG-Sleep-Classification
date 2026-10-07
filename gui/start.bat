@echo off
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Install Node.js LTS for Windows, then reopen this launcher.
  pause
  exit /b 1
)
if not exist node_modules\electron (
  call npm install
  if errorlevel 1 (pause & exit /b 1)
)
call npm start
if errorlevel 1 pause
