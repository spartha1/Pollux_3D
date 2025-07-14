# Activar el entorno de Conda
Write-Host "Activating Conda environment..." -ForegroundColor Yellow

# Cargar init_conda.ps1 para asegurar que conda está disponible
$initScript = Join-Path $PSScriptRoot "init_conda.ps1"
if (-not (Test-Path $initScript)) {
    Write-Host "Error: Could not find init_conda.ps1" -ForegroundColor Red
    exit 1
}

. $initScript

# Buscar conda.exe
$condaPath = Get-Command conda -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $condaPath) {
    Write-Host "Error: Conda initialization failed" -ForegroundColor Red
    exit 1
}

# Verificar si el entorno existe
$envExists = & $condaPath "env" "list" | Select-String "pollux-preview-env"
if (-not $envExists) {
    Write-Host "Error: Environment 'pollux-preview-env' not found. Please run 'npm run verify:env' first." -ForegroundColor Red
    exit 1
}

# Activar el entorno
$condaDir = Split-Path (Split-Path $condaPath)
$activateScript = Join-Path $condaDir "Scripts\activate.bat"

if (-not (Test-Path $activateScript)) {
    Write-Host "Error: Could not find activate script at: $activateScript" -ForegroundColor Red
    Write-Host "Searching for alternative locations..." -ForegroundColor Yellow
    
    # Intentar encontrar activate.bat en otras ubicaciones comunes
    $possiblePaths = @(
        Join-Path $condaDir "shell\condabin\conda-hook.ps1",
        Join-Path $condaDir "condabin\conda-hook.ps1",
        Join-Path $condaDir "Scripts\conda-hook.ps1"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            Write-Host "Found conda-hook at: $path" -ForegroundColor Green
            . $path
            conda activate pollux-preview-env
            break
        }
    }
} else {
    Write-Host "Found activate script at: $activateScript" -ForegroundColor Green
    & $activateScript "pollux-preview-env"
}

# Verificar que estamos usando el Python correcto
$pythonVersion = & python --version 2>&1
if (-not ($pythonVersion -like "*3.10*")) {
    Write-Host "Error: Wrong Python version. Expected 3.10, got: $pythonVersion" -ForegroundColor Red
    exit 1
}

# Verificar que estamos en el entorno correcto
$envPath = & python -c "import sys; print(sys.prefix)"
if (-not ($envPath -like "*pollux-preview-env*")) {
    Write-Host "Error: Not in pollux-preview-env environment" -ForegroundColor Red
    exit 1
}
if (-not $pythonPath -or -not ($pythonPath -like "*pollux-preview-env*")) {
    Write-Host "Error: Failed to activate pollux-preview-env" -ForegroundColor Red
    exit 1
}

Write-Host "Successfully activated pollux-preview-env" -ForegroundColor Green
