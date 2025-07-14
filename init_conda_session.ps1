Write-Host "Initializing Conda in current session..." -ForegroundColor Yellow

# Obtener la ruta del script init_conda.ps1
$initScript = Join-Path $PSScriptRoot "init_conda.ps1"
if (-not (Test-Path $initScript)) {
    Write-Host "Error: Could not find init_conda.ps1" -ForegroundColor Red
    exit 1
}

# Cargar init_conda.ps1 en la sesión actual
. $initScript

# Verificar que conda está disponible
$condaPath = Get-Command conda -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $condaPath) {
    Write-Host "Error: Conda initialization failed" -ForegroundColor Red
    exit 1
}

Write-Host "`nConda initialized successfully!" -ForegroundColor Green
Write-Host "You can now use conda commands in this session." -ForegroundColor Green
Write-Host "`nTry these commands:" -ForegroundColor Yellow
Write-Host "  conda env list  - List all environments" -ForegroundColor Yellow
Write-Host "  conda info     - Show conda information" -ForegroundColor Yellow
