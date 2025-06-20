@echo off
REM Activar el entorno conda
call conda activate polluxw

REM Iniciar el servidor de preview
python simple_preview_server.py

REM Si el servidor se detiene, pausar para ver errores
pause
