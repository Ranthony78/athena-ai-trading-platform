@echo off
rem Stops the Athena backend (8000), frontend (3000) and Celery.
powershell -NoProfile -Command "foreach ($p in 8000,3000) { Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }; Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -match 'celery' -and $_.CommandLine -match 'config' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo Athena stopped. Close any leftover black windows.
timeout /t 4 >nul
