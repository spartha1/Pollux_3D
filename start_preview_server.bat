@echo off
echo Starting Preview Server with conda Python...

:: Activar el entorno conda
call C:\Users\Leinad\miniconda3\Scripts\activate.bat pollux-preview-env

:: Mostrar información del entorno
echo Using Python from:
python -c "import sys; print(sys.executable)"

:: Iniciar el servidor
echo.
echo Starting server...
python app/Services/PreviewService/simple_preview_server.py
