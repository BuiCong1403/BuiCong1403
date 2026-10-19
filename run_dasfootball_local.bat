@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_dasfootball_local.ps1"
if errorlevel 1 echo DasFootball update failed. See the message above.
pause
