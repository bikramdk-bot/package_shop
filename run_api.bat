@echo off
cd /d "%~dp0src"
call ..\venv\Scripts\activate
python api_server.py
pause
