@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64
call C:\Users\Administrator\AppData\Local\miniconda3\Scripts\activate.bat pyoccenv
cd /d %~dp0
cmake .. -G "Ninja" -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE="C:\Users\Administrator\AppData\Local\miniconda3\envs\pyoccenv\python.exe"
if %ERRORLEVEL% EQU 0 ninja
