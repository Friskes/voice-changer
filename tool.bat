@echo off
chcp 65001 >nul
if "%~1"=="" (
    echo Usage: tool ^<script from tools\ without .py^> [args]
    exit /b 1
)
set PYTHONIOENCODING=utf-8
"%~dp0Applio\env\python.exe" "%~dp0tools\%~1.py" %2 %3 %4 %5 %6 %7 %8 %9
