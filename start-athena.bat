@echo off
rem Starts Athena (backend, frontend, Celery worker + beat) as split panes of one window.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-athena.ps1"
