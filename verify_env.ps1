Write-Host "Verifying environment setup..." -ForegroundColor Yellow

# Importar configuración del entorno
$configScript = Join-Path $PSScriptRoot "config\environment.ps1"
if (-not (Test-Path $configScript)) {
    Write-Host "Error: environment.ps1 not found at: $configScript" -ForegroundColor Red
    exit 1
}

# Inicializar el entorno
$env = . $configScript
Initialize-Environment

# Verificar que el entorno Conda existe
Write-Host "`nVerifying Conda environment..." -ForegroundColor Cyan

if (-not (Test-Path $env.PythonPath)) {
    Write-Host "Creating Conda environment '$($env.CondaName)'..." -ForegroundColor Yellow
    
    # Crear el entorno
    $condaExe = Join-Path $env.CondaScripts "conda.exe"
    & $condaExe create -n $env.CondaName python=$env.PythonVersion -y
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create Conda environment" -ForegroundColor Red
        exit 1
    }
    
    # Instalar dependencias
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    & $env.PythonPath -m pip install -r (Join-Path $env.ProjectRoot "requirements.txt")
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install Python dependencies" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n✅ Environment setup complete!" -ForegroundColor Green
Write-Host "You can now run 'npm run dev:all' to start all services" -ForegroundColor Cyan
