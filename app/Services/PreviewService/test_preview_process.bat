@echo off
echo Starting preview server...
start "Preview Server" cmd /c "python simple_preview_server.py"
timeout /t 2
echo Testing preview generation...
powershell -ExecutionPolicy Bypass -File test_preview.ps1
echo Done!
