@echo off
cd /d "%~dp0"
start "RAG Cukraren - server" .venv\Scripts\python server.py
timeout /t 20 /nobreak >nul
echo.
echo Verejny odkaz na stranku je nizsie (riadok https://....trycloudflare.com).
echo Po zatvoreni tohto okna odkaz prestane fungovat.
echo.
tools\cloudflared.exe tunnel --url http://localhost:8000
