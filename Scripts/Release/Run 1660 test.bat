@echo off
rem Elitewake minimum-machine test: runs the game on Low by itself for about 4 minutes and writes a results file here.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run 1660 test.ps1"
pause
