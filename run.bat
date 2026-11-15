@echo off
title Telegram Auto-Ad Broadcaster Pro
cd /d "%~dp0"
mode con: cols=86 lines=32

python sender.py

pause
