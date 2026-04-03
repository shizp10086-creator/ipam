@echo off
title IPAM Ping Proxy
echo Starting Ping Proxy on port 8001...
cd /d "%~dp0backend"
python scripts/ping_proxy.py
pause
