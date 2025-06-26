@echo off
echo Running OCC import test with conda Python...

:: Activar el entorno conda
call C:\Users\Leinad\miniconda3\Scripts\activate.bat pollux-preview-env

:: Ejecutar el script de prueba usando el Python de conda directamente
C:\Users\Leinad\miniconda3\envs\pollux-preview-env\python.exe app/Services/PreviewService/verify_occ_imports.py
pause
