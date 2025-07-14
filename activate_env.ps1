# Cargar init_conda.ps1 para asegurar que conda está disponible
$initScript = Join-Path $PSScriptRoot "init_conda.ps1"
if (-not (Test-Path $initScript)) {
    Write-Host "Error: Could not find init_conda.ps1" -ForegroundColor Red
    exit 1
}

Write-Host "Initializing Conda..." -ForegroundColor Yellow
. $initScript

# Buscar conda.exe
$condaPath = Get-Command conda -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $condaPath) {
    Write-Host "Error: Conda initialization failed" -ForegroundColor Red
    exit 1
}

# Desactivar entornos activos
Write-Host "Deactivating active environments..." -ForegroundColor Yellow
try {
    & $condaPath "deactivate" 2>$null
} catch {
    Write-Host "Note: No active conda environment to deactivate" -ForegroundColor Yellow
}

# Activar el entorno pollux-preview-env
Write-Host "Activating pollux-preview-env..." -ForegroundColor Yellow
& $condaPath "activate" "pollux-preview-env"

# Verificar que estamos en el entorno correcto
$pythonVersion = python --version 2>&1
$activeEnv = & $condaPath "env" "list" | Select-String "\*"
if (-not ($activeEnv -match "pollux-preview-env")) {
    Write-Host "Error: Failed to activate pollux-preview-env environment" -ForegroundColor Red
    Write-Host "Current environment: $activeEnv" -ForegroundColor Yellow
    Write-Host "Please run 'npm run verify:env' to set up the environment correctly" -ForegroundColor Yellow
    exit 1
}

if (-not ($pythonVersion -like "*3.10*")) {
    Write-Host "Error: Wrong Python version. Expected 3.10, got: $pythonVersion" -ForegroundColor Red
    Write-Host "Please run 'npm run verify:env' to set up the environment correctly" -ForegroundColor Yellow
    exit 1
}

Write-Host "Successfully activated pollux-preview-env with Python $pythonVersion" -ForegroundColor Green
Write-Host "Active Conda environment: $activeEnv" -ForegroundColor Green
