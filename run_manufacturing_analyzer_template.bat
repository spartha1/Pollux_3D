@echo off
REM Script dedicado para ejecutar el analizador de manufactura con entorno conda
REM ESTE ES UN TEMPLATE - usar generate_scripts.php para crear la versión final
setlocal EnableDelayedExpansion

REM Configurar las variables de entorno de conda
REM Estas rutas serán reemplazadas por el script de generación
set CONDA_PREFIX={{CONDA_PREFIX}}
set CONDA_DEFAULT_ENV={{CONDA_ENV}}
set PATH=%CONDA_PREFIX%;%CONDA_PREFIX%\Scripts;%CONDA_PREFIX%\Library\bin;%PATH%

REM Deshabilitar randomización de hash de Python para evitar errores de inicialización
set PYTHONHASHSEED=0

REM Cambiar al directorio del proyecto
cd /d "{{PROJECT_ROOT}}"

REM Ejecutar el analizador usando Python del entorno conda
"{{PYTHON_EXECUTABLE}}" "app\Services\FileAnalyzers\analyze_stl_manufacturing.py" "%1"
