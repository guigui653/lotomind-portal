@echo off
title LotoMind Portal — Servidor
echo ============================================
echo   LotoMind Portal — Iniciando servidor...
echo ============================================
echo.

REM Navega para o diretório do projeto
cd /d "C:\Users\widso\OneDrive\Documentos\Projetos\LotoMega\LotoMindPortal"

REM Inicia o servidor Flask
python app.py

echo.
echo Servidor encerrado. Pressione qualquer tecla para fechar.
pause
