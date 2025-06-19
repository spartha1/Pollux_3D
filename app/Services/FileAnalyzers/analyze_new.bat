@echo off
setlocal enabledelayedexpansion

REM Get script directory and set up logging
set "SCRIPT_DIR=%~dp0"
set "LOG_FILE=%SCRIPT_DIR%analyze_script.log"

REM Clear log file
echo Starting analysis at %DATE% %TIME% > "%LOG_FILE%"

REM Log paths
echo Script directory: %SCRIPT_DIR% >> "%LOG_FILE%"
echo Log file: %LOG_FILE% >> "%LOG_FILE%"
echo Current directory: %CD% >> "%LOG_FILE%"
echo Input file: %1 >> "%LOG_FILE%"

REM Check if input file exists
if not exist "%~1" (
    echo Error: Input file not found: %1
    echo Error: Input file not found: %1 >> "%LOG_FILE%"
    exit /b 1
)

REM Check if conda is available
echo Checking conda...
where conda > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: conda command not found
    echo Error: conda command not found >> "%LOG_FILE%"
    exit /b 1
)

REM Check if pollux environment exists
echo Checking pollux environment...
conda env list | findstr /C:"pollux" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: pollux environment not found
    echo Error: pollux environment not found >> "%LOG_FILE%"
    exit /b 1
)

REM Run analysis script
echo Running analysis with Python script...
echo Command: conda run -n pollux python "%SCRIPT_DIR%main.py" "%~1"

REM Create temporary output file
set "TEMP_OUT=%TEMP%\analysis_out_%RANDOM%.tmp"

REM Run analysis and capture output
echo Running Python script... Please wait...
call conda run -n pollux python "%SCRIPT_DIR%main.py" "%~1" > "%TEMP_OUT%" 2>&1
set ANALYSIS_ERROR=%ERRORLEVEL%

REM Display and log output
echo Output from Python script:
type "%TEMP_OUT%"
echo. >> "%LOG_FILE%"
echo Python script output: >> "%LOG_FILE%"
type "%TEMP_OUT%" >> "%LOG_FILE%"

REM Clean up temp file
del "%TEMP_OUT%" > nul 2>&1

REM Check for errors
if %ANALYSIS_ERROR% neq 0 (
    echo Error executing Python script. Exit code: %ANALYSIS_ERROR%
    echo Error executing Python script. Exit code: %ANALYSIS_ERROR% >> "%LOG_FILE%"
    exit /b %ANALYSIS_ERROR%
)

echo Analysis completed successfully.
echo Analysis completed successfully. >> "%LOG_FILE%"
exit /b 0
