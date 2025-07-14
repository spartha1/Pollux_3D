# Buscar conda en las ubicaciones comunes
$possibleCondaPaths = @(
    "C:\ProgramData\miniconda3\Scripts\conda.exe",
    "C:\ProgramData\Anaconda3\Scripts\conda.exe",
    "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
    "$env:USERPROFILE\Anaconda3\Scripts\conda.exe"
)

$condaPath = $null
foreach ($path in $possibleCondaPaths) {
    if (Test-Path $path) {
        $condaPath = $path
        break
    }
}

if (-not $condaPath) {
    Write-Host "Error: Could not find conda installation" -ForegroundColor Red
    exit 1
}

Write-Host "Found conda at: $condaPath" -ForegroundColor Green

# Obtener la ruta del directorio actual
$scriptDir = $PSScriptRoot

# Activar el entorno conda
Write-Host "Activating conda environment..." -ForegroundColor Yellow
$condaDir = Split-Path (Split-Path $condaPath)
$activateScript = Join-Path (Split-Path $condaPath) "activate.bat"

# Verificar que el script de activación existe
if (-not (Test-Path $activateScript)) {
    Write-Host "Error: Could not find activate script at: $activateScript" -ForegroundColor Red
    exit 1
}

# Establecer PYTHONPATH y otras variables de entorno
$env:PYTHONPATH = $scriptDir
$env:CONDA_DEFAULT_ENV = "pollux-preview-env"
$env:CONDA_PREFIX = Join-Path $condaDir "envs\pollux-preview-env"
$env:PATH = "$env:CONDA_PREFIX;$env:CONDA_PREFIX\Library\mingw-w64\bin;$env:CONDA_PREFIX\Library\usr\bin;$env:CONDA_PREFIX\Library\msys2\bin;$env:CONDA_PREFIX\Scripts;$env:CONDA_PREFIX\bin;$env:PATH"

# Ejecutar el script de activación usando cmd.exe
Write-Host "Running activation script: $activateScript" -ForegroundColor Yellow
$activateCommand = "call `"$activateScript`" pollux-preview-env"
& cmd.exe /c $activateCommand

# Verificar que estamos usando el Python correcto
$condaPython = Join-Path $env:CONDA_PREFIX "python.exe"
if (-not (Test-Path $condaPython)) {
    Write-Host "Error: Python not found in conda environment: $condaPython" -ForegroundColor Red
    exit 1
}

Write-Host "Using Python from: $condaPython" -ForegroundColor Green

# Instalar dependencias adicionales si no están instaladas
Write-Host "Checking additional dependencies..." -ForegroundColor Yellow
& $condaPython -m pip install slowapi fastapi uvicorn pydantic python-multipart

# Iniciar el servidor FastAPI
Write-Host "Starting preview server..." -ForegroundColor Yellow
& $condaPython "$scriptDir\simple_preview_server.py"
