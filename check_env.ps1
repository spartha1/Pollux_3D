# Limpiar y configurar entorno Python
Write-Host "Cleaning up Python environments..." -ForegroundColor Green

# Cargar el script de inicialización de Conda
$initScript = Join-Path $PSScriptRoot "init_conda.ps1"
if (-not (Test-Path $initScript)) {
    Write-Host "Error: Could not find init_conda.ps1" -ForegroundColor Red
    exit 1
}

. $initScript

# Buscar Conda installation
$possiblePaths = @(
    "$env:USERPROFILE\miniconda3",
    "$env:USERPROFILE\anaconda3",
    "${env:ProgramFiles}\miniconda3",
    "${env:ProgramFiles}\anaconda3",
    "${env:ProgramFiles(x86)}\miniconda3",
    "${env:ProgramFiles(x86)}\anaconda3"
)

$condaDir = $null
foreach ($path in $possiblePaths) {
    if (Test-Path "$path\Scripts\conda.exe") {
        $condaDir = $path
        break
    }
}

if (-not $condaDir) {
    Write-Host "Error: Could not find Conda installation" -ForegroundColor Red
    Write-Host "Please install Miniconda from https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found Conda installation at: $condaDir" -ForegroundColor Green

# Configurar Conda para esta sesión
$env:PATH = "$condaDir;$condaDir\Scripts;$condaDir\Library\bin;$env:PATH"
$condaPath = "$condaDir\Scripts\conda.exe"

# Desactivar cualquier entorno activo primero
Write-Host "Deactivating any active conda environment..." -ForegroundColor Yellow
& $condaPath "deactivate"

# Verificar el entorno
Write-Host "Checking conda environment..." -ForegroundColor Green

# Verificar y limpiar el directorio del entorno si existe
$envPath = Join-Path $condaDir "envs\pollux-preview-env"
if (Test-Path $envPath) {
    Write-Host "Found existing environment directory..." -ForegroundColor Yellow
    
    # Desactivar cualquier entorno activo
    Write-Host "Deactivating any active environment..." -ForegroundColor Yellow
    & $condaPath "deactivate" 2>&1 | Out-Null
    
    # Intentar eliminar el directorio manualmente primero
    Write-Host "Removing environment directory..." -ForegroundColor Yellow
    try {
        # Forzar cierre de cualquier proceso que pueda estar usando el directorio
        $processes = Get-Process | Where-Object { $_.Path -like "*$envPath*" }
        foreach ($process in $processes) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
        
        # Esperar un momento para asegurar que los procesos se han cerrado
        Start-Sleep -Seconds 2
        
        # Eliminar el directorio
        Remove-Item -Path $envPath -Recurse -Force -ErrorAction Stop
        Write-Host "Successfully removed environment directory." -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to remove directory: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Please close any applications that might be using Python and try again." -ForegroundColor Yellow
        exit 1
    }
}

# Crear nuevo entorno
Write-Host "Creating conda environment 'pollux-preview-env' with Python 3.10..." -ForegroundColor Yellow
& $condaPath "create" "-n" "pollux-preview-env" "python=3.10" "-y"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error creating environment. Please try running the script again." -ForegroundColor Red
    exit 1
}

# Activar el entorno pollux-preview-env
Write-Host "Activating pollux-preview-env..." -ForegroundColor Yellow
$activateScript = Join-Path (Split-Path $condaPath) "activate.bat"
& $activateScript "pollux-preview-env"

# Preparar las dependencias
Write-Host "Preparing dependencies..." -ForegroundColor Yellow

# Función auxiliar para instalar dependencias
function global:Install-CondaDependency($name) {
    Write-Host "Installing $name..." -ForegroundColor Yellow
    & $condaPath "install" "-n" "pollux-preview-env" "-c" "conda-forge" "$name" "-y" *>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Installed $name with conda" -ForegroundColor Green
        return $true
    }
    return $false
}

function global:Install-PipDependency($name) {
    $pipName = $name.Split('=')[0]
    $pipVersion = $name.Split('=')[1]
    Write-Host "Installing $name with pip..." -ForegroundColor Yellow
    & $condaPath "run" "-n" "pollux-preview-env" "python" "-m" "pip" "install" "--no-cache-dir" "${pipName}==${pipVersion}" *>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Installed $name with pip" -ForegroundColor Green
        return $true
    }
    Write-Host "⚠️ Failed to install $name" -ForegroundColor Red
    return $false
}

# Lista de todas las dependencias por grupo
$condaGroups = @{
    "base" = @(
        "python=3.10",
        "pip",
        "setuptools",
        "wheel",
        "numpy=1.24.3"
    );
    "visualization" = @(
        "vtk=9.1.0",
        "matplotlib=3.8.0"
    );
    "geometry" = @(
        "occt=7.7.2",
        "pythonocc-core=7.7.2"
    );
    "server" = @(
        "fastapi=0.104.1",
        "uvicorn=0.24.0",
        "pillow=10.0.1",
        "pydantic=2.4.2"
    )
}

# Instalar dependencias por grupo (excluyendo VTK que se maneja por separado)
Write-Host "Installing dependencies..." -ForegroundColor Yellow
foreach ($group in $condaGroups.Keys) {
    if ($group -ne "visualization") {  # Skip visualization group as we handle VTK separately
        Write-Host "`nInstalling $group dependencies..." -ForegroundColor Cyan
        foreach ($dep in $condaGroups[$group]) {
            if (-not (Install-CondaDependency $dep)) {
                Install-PipDependency $dep
            }
        }
    }
}

# Install matplotlib separately from visualization group
Write-Host "`nInstalling matplotlib..." -ForegroundColor Cyan
if (-not (Install-CondaDependency "matplotlib=3.8.0")) {
    Install-PipDependency "matplotlib=3.8.0"
}

# Clean and reinstall VTK and PyVista
Write-Host "`nPreparing for VTK and PyVista installation..." -ForegroundColor Yellow

# Remove existing installations and clean everything
Write-Host "Cleaning conda cache and removing packages..." -ForegroundColor Yellow
& $condaPath "clean" "--all" "-y" 2>&1 | Out-Null
& $condaPath "remove" "-n" "pollux-preview-env" "vtk" "pyvista" "qt" "qt-main" "hdf5" "libtiff" "netcdf4" "--force" "-y" 2>&1 | Out-Null

# Reset conda configuration
Write-Host "Resetting conda configuration..." -ForegroundColor Yellow
& $condaPath "config" "--remove-key" "channels" 2>&1 | Out-Null
& $condaPath "config" "--add" "channels" "conda-forge" "--force"
& $condaPath "config" "--set" "channel_priority" "flexible"

# Update conda itself
Write-Host "Updating conda..." -ForegroundColor Yellow
& $condaPath "update" "-n" "base" "conda" "-y"

# Install Qt first
Write-Host "`nInstalling Qt dependencies..." -ForegroundColor Yellow
& $condaPath "install" "-n" "pollux-preview-env" "-c" "conda-forge" "qt-main=5.15.8" "--no-deps" "-y"

# Update environment variables for Qt
$qtPath = Join-Path $condaDir "envs\pollux-preview-env\Library"
$env:QT_QPA_PLATFORM_PLUGIN_PATH = Join-Path $qtPath "plugins"
$env:QT_PLUGIN_PATH = Join-Path $qtPath "plugins"
$env:QT_DEBUG_PLUGINS = "1"

# Add Qt paths to system PATH
$qtBinPath = Join-Path $qtPath "bin"
$qtLibPath = Join-Path $qtPath "lib"
$qtPluginsPath = Join-Path $qtPath "plugins"
$env:PATH = "$qtBinPath;$qtLibPath;$qtPluginsPath;$env:PATH"

# Set up environment variables
$env:CONDA_DLL_SEARCH_MODIFICATION_ENABLE = 1

# Update PATH with all necessary directories
$libraryBinPath = Join-Path $condaDir "envs\pollux-preview-env\Library\bin"
$libraryLibPath = Join-Path $condaDir "envs\pollux-preview-env\Library\lib"
$qtBinPath = Join-Path $condaDir "envs\pollux-preview-env\Library\plugins"
$env:PATH = "$libraryBinPath;$libraryLibPath;$qtBinPath;$env:PATH"

# Install VTK with minimal dependencies first
Write-Host "`nInstalling VTK..." -ForegroundColor Yellow
& $condaPath "install" "-n" "pollux-preview-env" "-c" "conda-forge" "python=3.10" "vtk=9.1.0" "qt=5.15" "--no-deps" "-y"

# Install remaining VTK dependencies
Write-Host "`nInstalling VTK dependencies..." -ForegroundColor Yellow
& $condaPath "install" "-n" "pollux-preview-env" "-c" "conda-forge" `
    "hdf5=1.12.2" "libtiff=4.4.0" "jsoncpp" "pugixml" "libxml2" "eigen" "double-conversion" "lz4-c" "expat" "zlib" "-y"

# Define pythonPath before using it
$pythonPath = Join-Path $condaDir "envs\pollux-preview-env\python.exe"

# Verify the installation with a simple test first
Write-Host "Verifying VTK installation..." -ForegroundColor Yellow
$vtkTestScript = "import vtk; print('VTK version:', vtk.vtkVersion().GetVTKVersion())"
$vtkTest = & $pythonPath "-c" $vtkTestScript 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "VTK installation failed. Error: $vtkTest" -ForegroundColor Red
    Write-Host "Reinstalling VTK..." -ForegroundColor Yellow
    & $condaPath "install" "-n" "pollux-preview-env" "-c" "conda-forge" "vtk=9.1.0" "-y"
    $vtkTest = & $pythonPath "-c" $vtkTestScript 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "VTK reinstallation failed. Exiting." -ForegroundColor Red
        exit 1
    }
}
Write-Host "VTK installation verified successfully." -ForegroundColor Green

# Install PyVista after VTK is verified
Write-Host "`nInstalling PyVista..." -ForegroundColor Cyan
& $condaPath "install" "-n" "pollux-preview-env" "-c" "conda-forge" "pyvista=0.38.5" "-y"

# Update pip without using conda run to avoid version parsing issues
Write-Host "Updating pip with workaround..." -ForegroundColor Yellow
# Use conda run with error suppression to avoid the version parsing error
& $condaPath "run" "-n" "pollux-preview-env" "python" "-m" "pip" "install" "--upgrade" "pip" "--quiet" 2>&1 | Out-Null

# Instalar dependencias adicionales específicas
Write-Host "`nInstalling additional dependencies..." -ForegroundColor Cyan

# Install numpy-stl with conda run to avoid path issues
Write-Host "Installing numpy-stl..." -ForegroundColor Yellow
& $condaPath "run" "-n" "pollux-preview-env" "python" "-m" "pip" "install" "numpy-stl==3.0.1" "--quiet" "--no-warn-script-location" 2>&1 | Out-Null

# Add all relevant paths to PATH
$scriptsPath = Join-Path $condaDir "envs\pollux-preview-env\Scripts"
$env:PATH = "$scriptsPath;$libraryBinPath;$libraryLibPath;$env:PATH"

# Verify the installation with direct python execution
Write-Host "Verifying numpy-stl installation..." -ForegroundColor Yellow
$stlTestScript = "import stl; print('numpy-stl installation verified')"
$stlTest = & $pythonPath "-c" $stlTestScript 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "numpy-stl verification failed. Installing with conda..." -ForegroundColor Yellow
    & $condaPath "install" "-n" "pollux-preview-env" "-c" "conda-forge" "numpy-stl" "-y" 2>&1 | Out-Null
}

# Verify VTK and PyVista functionality
Write-Host "Verifying VTK and PyVista functionality..." -ForegroundColor Yellow
$testVtkPyvista = "import vtk; import pyvista; print('VTK version:', vtk.vtkVersion().GetVTKVersion()); print('PyVista version:', pyvista.__version__)"
$test = & $pythonPath "-c" $testVtkPyvista 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "VTK/PyVista test failed. Attempting repair..." -ForegroundColor Red
    Write-Host "Error: $test" -ForegroundColor Yellow
    # Clean and reinstall
    & $condaPath "remove" "-n" "pollux-preview-env" "vtk" "pyvista" "--force" "-y"
    & $condaPath "install" "-n" "pollux-preview-env" "-c" "conda-forge" "vtk=9.1.0" "pyvista=0.38.5" "-y"
} else {
    Write-Host "VTK and PyVista are working correctly!" -ForegroundColor Green
}

# Crear archivos temporales para los scripts de prueba
$tempFolder = Join-Path $env:TEMP "pollux_test_scripts"
New-Item -ItemType Directory -Force -Path $tempFolder | Out-Null

$checkPythonPath = Join-Path $tempFolder "check_python.py"
$checkOCC = Join-Path $tempFolder "check_occ.py"
$checkDeps = Join-Path $tempFolder "check_deps.py"

# Script para verificar Python path
@"
import sys
print('Python executable:', sys.executable)
"@ | Out-File -FilePath $checkPythonPath -Encoding utf8

# Script para verificar OCC
@"
import sys
try:
    from OCC import VERSION
    from OCC.Core import VERSION as CORE_VERSION
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
    from OCC.Core.gp import gp_Pnt

    print("pythonocc-core version:", VERSION)
    print("OCC.Core version:", CORE_VERSION)
    
    # Test basic geometry creation
    box = BRepPrimAPI_MakeBox(gp_Pnt(0, 0, 0), 10, 10, 10).Shape()
    print("OCC import and basic geometry test successful!")
except ImportError as e:
    print("Error importing OCC:", str(e))
    sys.exit(1)
except Exception as e:
    print("Error testing OCC functionality:", str(e))
    sys.exit(1)
"@ | Out-File -FilePath $checkOCC -Encoding utf8

# Script para verificar dependencias
@"
import sys
dependencies = {
    "numpy": "numpy",
    "pyvista": "pyvista",
    "fastapi": "fastapi",
    "numpy-stl": "stl",
    "matplotlib": "matplotlib",
    "vtk": "vtk"
}

for module_name, import_name in dependencies.items():
    try:
        module = __import__(import_name)
        version = getattr(module, "__version__", "unknown")
        print(f"{module_name}: {version}")
    except ImportError as e:
        print(f"Error importing {module_name}: {str(e)}")
        sys.exit(1)
"@ | Out-File -FilePath $checkDeps -Encoding utf8

# Ejecutar las verificaciones
Write-Host "`nChecking Python path..." -ForegroundColor Green
& $condaPath "run" "-n" "pollux-preview-env" "python" $checkPythonPath

Write-Host "`nTesting OCC import..." -ForegroundColor Green
& $condaPath "run" "-n" "pollux-preview-env" "python" $checkOCC

Write-Host "`nTesting other dependencies..." -ForegroundColor Green
& $condaPath "run" "-n" "pollux-preview-env" "python" $checkDeps

# Limpiar archivos temporales
Remove-Item -Path $tempFolder -Recurse -Force

Write-Host "`nEnvironment check complete." -ForegroundColor Green
pause
