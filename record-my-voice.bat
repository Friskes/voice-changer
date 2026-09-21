@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
"%~dp0Applio\env\python.exe" "%~dp0tools\record_my_voice.py"
pause
