# Stop on first error
$ErrorActionPreference = "Stop"

# Check if running with admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "Script is not running with administrator privileges. Some operations may fail."
    Write-Host "Consider running this script as administrator if you encounter permission errors."
}

Write-Host "Setting up build environment..."

# Environment name
$envName = "pythonocc-env"

# Remove existing environment if it exists
Write-Host "Creating conda environment '$envName'..."
conda env remove -n $envName -y

# Create new environment with Python 3.10
Write-Host "Creating new environment with Python 3.10..."
conda create -n $envName python=3.10 -y

# Activate environment and install packages
Write-Host "Activating environment and installing packages..."
conda activate $envName

# Add conda-forge channel
conda config --add channels conda-forge
conda config --set channel_priority strict

# Install base packages first
$basePackages = @(
    "setuptools",
    "wheel",
    "pip"
)

foreach ($package in $basePackages) {
    Write-Host "Installing $package..."
    conda install -y -c conda-forge $package
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install $package"
        exit 1
    }
}

# Install VC runtime separately to handle permission issues
Write-Host "Installing VC runtime..."
conda install -y -c conda-forge vs2015_runtime vc14_runtime --no-deps
if ($LASTEXITCODE -ne 0) {
    Write-Warning "VC runtime installation had issues - continuing anyway..."
}

# Install required packages
$packages = @(
    "numpy=1.24.3",
    "cmake=3.26.4",
    "ninja=1.11.1",
    "occt=7.7.2",
    "pybind11=2.10.4",
    "eigen=3.4.0"
)

foreach ($package in $packages) {
    Write-Host "Installing $package..."
    # Try normal install first
    conda install -y -c conda-forge $package
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Normal install failed for $package, trying with --no-deps..."
        conda install -y -c conda-forge $package --no-deps
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install $package"
            exit 1
        }
    }
}

# Verify Python and NumPy are available
Write-Host "`nVerifying Python and NumPy..."
python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to import NumPy"
    exit 1
}

# Verify critical packages are in the right place
Write-Host "`nVerifying package installations..."

# Check for Ninja in multiple possible locations
$ninjaLocations = @(
    (Join-Path $env:CONDA_PREFIX "Scripts\ninja.exe"),
    (Join-Path $env:CONDA_PREFIX "Library\bin\ninja.exe"),
    (Get-Command ninja -ErrorAction SilentlyContinue).Path
)

$ninjaFound = $false
foreach ($path in $ninjaLocations) {
    if ($path -and (Test-Path $path)) {
        Write-Host "Found Ninja at: $path"
        $ninjaFound = $true
        break
    }
}

if (-not $ninjaFound) {
    Write-Error "Ninja not found in any expected location. Checked paths:`n$($ninjaLocations -join "`n")"
    exit 1
}

# Check for CMake in multiple possible locations
$cmakeLocations = @(
    (Join-Path $env:CONDA_PREFIX "Library\bin\cmake.exe"),
    (Join-Path $env:CONDA_PREFIX "Scripts\cmake.exe"),
    (Get-Command cmake -ErrorAction SilentlyContinue).Path
)

$cmakeFound = $false
foreach ($path in $cmakeLocations) {
    if ($path -and (Test-Path $path)) {
        Write-Host "Found CMake at: $path"
        $cmakeFound = $true
        break
    }
}

if (-not $cmakeFound) {
    Write-Error "CMake not found in any expected location. Checked paths:`n$($cmakeLocations -join "`n")"
    exit 1
}

Write-Host "`nEnvironment setup complete! Next steps:"
Write-Host "1. Make sure you have activated the environment: conda activate $envName"
Write-Host "2. Run the build script: .\rebuild_final_conda.ps1"
