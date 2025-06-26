# Limpiar y configurar entorno Python
Write-Host "Cleaning up Python environments..." -ForegroundColor Green

# Desactivar entorno virtual si está activo
if ($env:VIRTUAL_ENV) {
    Write-Host "Deactivating virtual environment..." -ForegroundColor Yellow
    deactivate
}

# Intentar usar conda directamente desde PowerShell
Write-Host "Setting up conda environment..." -ForegroundColor Green
$condaPath = "C:\Users\Leinad\miniconda3\Scripts\conda.exe"

# Verificar que conda existe
if (Test-Path $condaPath) {
    Write-Host "Found conda at: $condaPath" -ForegroundColor Green

    # Activar el entorno pollux-preview-env
    Write-Host "Activating pollux-preview-env..." -ForegroundColor Yellow
    & $condaPath "activate" "pollux-preview-env"

    # Verificar Python path
    Write-Host "`nChecking Python path..." -ForegroundColor Green
    python -c "import sys; print('Python executable:', sys.executable)"

    # Intentar importar OCC
    Write-Host "`nTesting OCC import..." -ForegroundColor Green
    python -c "import OCC; print('OCC version:', OCC.__version__)"
} else {
    Write-Host "Error: Could not find conda at: $condaPath" -ForegroundColor Red
}

Write-Host "`nEnvironment check complete." -ForegroundColor Green
pause
