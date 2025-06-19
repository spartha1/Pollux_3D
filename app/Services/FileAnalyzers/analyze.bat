@echo off
setlocal EnableDelayedExpansion

:: Create a timestamp for the log file
set "timestamp=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "timestamp=%timestamp: =0%"
set "LOG_FILE=%~dp0analyze_script_%timestamp%.log"
set "TEMP_JSON=%TEMP%\analysis_output_%timestamp%.json"
set "ERROR_FILE=%TEMP%\analysis_error_%timestamp%.txt"

:: Start logging
echo ==================== Analysis Start ==================== > "%LOG_FILE%"
echo Start time: %date% %time% >> "%LOG_FILE%"
echo Script directory: %~dp0 >> "%LOG_FILE%"
echo Working directory: %CD% >> "%LOG_FILE%"
echo Log file: %LOG_FILE% >> "%LOG_FILE%"
echo Temp JSON: %TEMP_JSON% >> "%LOG_FILE%"
echo Error file: %ERROR_FILE% >> "%LOG_FILE%"

:: Check if input file argument is provided
if "%~1"=="" (
    echo Error: No input file specified >> "%LOG_FILE%"
    echo {"error": "No input file specified"} > "%TEMP_JSON%"
    goto :output_and_exit
)

echo Input file: %1 >> "%LOG_FILE%"

:: Check if input file exists
if not exist "%~1" (
    echo Error: Input file does not exist: %1 >> "%LOG_FILE%"
    echo {"error": "Input file does not exist: %~1"} > "%TEMP_JSON%"
    goto :output_and_exit
)

:: Try to find Python executable
echo Searching for Python... >> "%LOG_FILE%"

:: First try the absolute path to the virtual environment
set "VENV_PYTHON=C:\xampp\htdocs\laravel\PolluxwWeb\venv\Scripts\python.exe"
if exist "!VENV_PYTHON!" (
    echo Found venv Python: !VENV_PYTHON! >> "%LOG_FILE%"
    set "PYTHON_EXE=!VENV_PYTHON!"
    goto :found_python
)

:: Then try relative path from script directory
set "VENV_PYTHON=%~dp0..\..\venv\Scripts\python.exe"
if exist "!VENV_PYTHON!" (
    echo Found venv Python (relative path): !VENV_PYTHON! >> "%LOG_FILE%"
    set "PYTHON_EXE=!VENV_PYTHON!"
    goto :found_python
)

:: Then try Conda environment
where conda > "%TEMP%\conda_path.txt" 2>&1
if !errorlevel! equ 0 (
    echo Found conda >> "%LOG_FILE%"
    for /f "tokens=*" %%i in ('conda env list ^| findstr pollux') do (
        set "CONDA_ENV=%%i"
        echo Found conda env: !CONDA_ENV! >> "%LOG_FILE%"
    )
    if defined CONDA_ENV (
        set "PYTHON_EXE=conda run -n pollux python"
        echo Using conda Python >> "%LOG_FILE%"
        goto :found_python
    )
)

:: Finally try system Python
where python > "%TEMP%\python_path.txt" 2>&1
if !errorlevel! equ 0 (
    set /p PYTHON_EXE=<"%TEMP%\python_path.txt"
    echo Found system Python: !PYTHON_EXE! >> "%LOG_FILE%"
    goto :found_python
)

echo Error: Python not found >> "%LOG_FILE%"
echo {"error": "Python executable not found"} > "%TEMP_JSON%"
goto :output_and_exit

:found_python
:: Verify Python works and get its version
if "!PYTHON_EXE!"=="conda run -n pollux python" (
    conda run -n pollux python -V > "%TEMP%\python_version.txt" 2>&1
) else (
    "!PYTHON_EXE!" -V > "%TEMP%\python_version.txt" 2>&1
)

if !errorlevel! neq 0 (
    echo Error: Failed to run Python >> "%LOG_FILE%"
    type "%TEMP%\python_version.txt" >> "%LOG_FILE%"
    echo {"error": "Failed to run Python"} > "%TEMP_JSON%"
    goto :output_and_exit
)

set /p PYTHON_VERSION=<"%TEMP%\python_version.txt"
echo Python version: !PYTHON_VERSION! >> "%LOG_FILE%"

:: Set up clean environment variables
set "PYTHONIOENCODING=utf-8"
set "PYTHONUNBUFFERED=1"
set "PYTHONDONTWRITEBYTECODE=1"

echo Running Python analysis... >> "%LOG_FILE%"
if "!PYTHON_EXE!"=="conda run -n pollux python" (
    echo Command: conda run -n pollux python "%~dp0main.py" "%~1" >> "%LOG_FILE%"
    conda run -n pollux python "%~dp0main.py" "%~1" > "%TEMP_JSON%" 2> "%ERROR_FILE%"
) else (
    echo Command: "!PYTHON_EXE!" "%~dp0main.py" "%~1" >> "%LOG_FILE%"
    "!PYTHON_EXE!" "%~dp0main.py" "%~1" > "%TEMP_JSON%" 2> "%ERROR_FILE%"
)

:: Check for errors
if !errorlevel! neq 0 (
    echo Error: Python script failed with code !errorlevel! >> "%LOG_FILE%"
    echo Error output: >> "%LOG_FILE%"
    type "%ERROR_FILE%" >> "%LOG_FILE%"
    echo Standard output: >> "%LOG_FILE%"
    type "%TEMP_JSON%" >> "%LOG_FILE%"

    :: Create error JSON with both stdout and stderr
    set "stdout="
    for /f "delims=" %%i in ('type "%TEMP_JSON%"') do set "stdout=!stdout!%%i"
    set "stderr="
    for /f "delims=" %%i in ('type "%ERROR_FILE%"') do set "stderr=!stderr!%%i"

    echo {"error": "Python script failed with code !errorlevel!", "stdout": "!stdout!", "stderr": "!stderr!"} > "%TEMP_JSON%"
    goto :output_and_exit
)

echo Analysis completed successfully >> "%LOG_FILE%"

:output_and_exit
:: Output the JSON result
type "%TEMP_JSON%"

:: Clean up temp files
del "%TEMP_JSON%" >nul 2>&1
del "%ERROR_FILE%" >nul 2>&1
del "%TEMP%\python_path.txt" >nul 2>&1
del "%TEMP%\python_version.txt" >nul 2>&1
del "%TEMP%\conda_path.txt" >nul 2>&1

exit /b %errorlevel%
