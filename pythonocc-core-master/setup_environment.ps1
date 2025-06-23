# Stop on first error
$ErrorActionPreference = "Stop"

Write-Host "Setting up build environment..."

# Add conda-forge channel if not already added
Write-Host "Configuring conda channels..."
conda config --add channels conda-forge

# Install all required packages
Write-Host "Installing required packages..."

# First update conda itself
Write-Host "Updating conda..."
Start-Process -FilePath "conda" -ArgumentList "update -n base -c defaults conda -y" -NoNewWindow -Wait
if ($LASTEXITCODE -ne 0) { Write-Host "Conda update failed, continuing anyway..." }

# Install packages one at a time
Write-Host "`nInstalling build tools..."
Start-Process -FilePath "conda" -ArgumentList "install -y -c conda-forge cmake ninja" -NoNewWindow -Wait
if ($LASTEXITCODE -ne 0) { throw "Failed to install build tools" }

Write-Host "`nInstalling OpenCASCADE..."
Start-Process -FilePath "conda" -ArgumentList "install -y -c conda-forge occt=7.9.0" -NoNewWindow -Wait
if ($LASTEXITCODE -ne 0) { throw "Failed to install OpenCASCADE" }

Write-Host "`nInstalling pythonocc dependencies..."
Start-Process -FilePath "conda" -ArgumentList "install -y -c conda-forge pybind11 eigen=3.4.0" -NoNewWindow -Wait
if ($LASTEXITCODE -ne 0) { throw "Failed to install additional dependencies" }

# Local SWIG setup
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$swigDir = Join-Path $scriptDir "swig-4.2.1"
$swigPath = Join-Path $swigDir "swig.exe"

if (-not (Test-Path $swigPath)) {
    Write-Host "SWIG not found. Running SWIG setup..."
    & "$scriptDir\setup_swig_simple.ps1"
}

Write-Host "Environment setup complete!"
