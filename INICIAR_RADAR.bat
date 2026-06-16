@echo off
title Apex-Radar Automotriz
echo Iniciando motor...
:: Levantamos el backend
start /B python -m uvicorn backend.main:app --port 8000
:: Esperamos 3 segundos para que el servidor esté listo
timeout /t 3 >nul
:: Abrimos la interfaz directamente
start "" "http://localhost:8000"
echo.
echo ==================================================
echo APEX-RADAR ACTIVADO. 
echo NO CIERRES ESTA VENTANA NEGRA.
echo ==================================================
pause