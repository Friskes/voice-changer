@echo off

setlocal
title Stop Applio

set "APPLIO_DIR=%~dp0Applio\"

powershell -NoProfile -Command "$py = Join-Path $env:APPLIO_DIR 'env\python.exe'; $procs = @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -eq $py }); if (-not $procs) { Write-Host 'Applio is not running.' } else { foreach ($p in $procs) { Write-Host ('Stopping PID ' + $p.ProcessId + ': ' + $p.CommandLine); Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }; Wait-Process -Id $procs.ProcessId -Timeout 10 -ErrorAction SilentlyContinue; Write-Host 'Applio stopped.' }"

powershell -NoProfile -Command "$left = @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($env:APPLIO_DIR, [StringComparison]::OrdinalIgnoreCase) }); if ($left) { Write-Host ''; Write-Host 'Other processes still running from this folder (not stopped):'; $left | ForEach-Object { Write-Host ('  PID ' + $_.ProcessId + ': ' + $_.CommandLine) } }"

echo.
pause
