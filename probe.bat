@echo off
chcp 65001 >nul
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo.
echo  Applio должен быть запущен и нажат «Старт».
echo  После нажатия клавиши ГОВОРИ НЕПРЕРЫВНО 10 секунд обычным голосом.
echo.
pause
set PYTHONIOENCODING=utf-8
"%~dp0Applio\env\python.exe" "%~dp0tools\probe_levels.py" 10 > "%~dp0logs\probe.txt"
type "%~dp0logs\probe.txt"
echo.
echo  Результат сохранён в logs\probe.txt
pause
