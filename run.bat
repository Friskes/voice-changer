@echo off
if not exist "%~dp0Applio\env\python.exe" (
    echo Applio is not installed. Run install.bat first.
    pause
    exit /b 1
)
cd /d "%~dp0Applio"
call run-applio.bat
