@echo off
rem Starts the Athena backend, frontend and Celery in their own windows.
rem Safe to run twice: anything already running is left alone.
set ROOT=%~dp0

netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul
if errorlevel 1 (
    start "Athena Backend" /D "%ROOT%backend" cmd /k python manage.py runserver
) else (
    echo Backend already running on port 8000 - skipped.
)

netstat -ano | findstr /R /C:":3000 .*LISTENING" >nul
if errorlevel 1 (
    start "Athena Frontend" /D "%ROOT%frontend" cmd /k npm run dev
) else (
    echo Frontend already running on port 3000 - skipped.
)

rem Celery has no port; look for running processes by command line.
rem Windows cannot run the scheduler inside the worker (-B), so they are two windows.
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -match 'celery' -and $_.CommandLine -match ' worker' }) { exit 0 } else { exit 1 }"
if errorlevel 1 (
    start "Athena Celery Worker" /D "%ROOT%backend" cmd /k python -m celery -A config worker -l info -P solo
) else (
    echo Celery worker already running - skipped.
)

powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -match 'celery' -and $_.CommandLine -match ' beat' }) { exit 0 } else { exit 1 }"
if errorlevel 1 (
    start "Athena Celery Beat" /D "%ROOT%backend" cmd /k python -m celery -A config beat -l info
) else (
    echo Celery beat already running - skipped.
)

echo.
echo Open http://localhost:3000 then reconnect Zerodha (Zerodha page) before 09:15.
timeout /t 8 >nul
