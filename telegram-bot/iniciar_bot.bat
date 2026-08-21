@echo off
start /min pythonw telegram_collector.py
echo Coletor Telegram iniciado em segundo plano!
timeout /t 2 >nul
