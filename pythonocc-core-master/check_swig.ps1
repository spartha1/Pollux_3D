# Script to check SWIG setup
$ErrorActionPreference = "Stop"

Write-Host "Checking SWIG installation..."

# Function to get version from swig executable
function Get-SwigVersion {
    param($Path)
    try {
        $output = & $Path -version 2>&1
        if ($output -match "SWIG Version (\d+\.\d+\.\d+)") {
            return $matches[1]
        }
    } catch {}
    return $null
}

# First, ensure we have the right version in conda
Write-Host "`nInstalling SWIG 4.2.1 from conda-forge..."
conda config --add channels conda-forge
conda install -y "swig=4.2.1" --force-reinstall
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install SWIG"
    exit 1
}

# Get conda environment info
$condaInfo = conda info --json | ConvertFrom-Json
$condaPrefix = $condaInfo.active_prefix
if (-not $condaPrefix) { $condaPrefix = $condaInfo.root_prefix }

Write-Host "`nConda environment:"
Write-Host "Prefix: $condaPrefix"

# Find SWIG in conda environment
$swigPath = Join-Path $condaPrefix "Library\bin\swig.exe"
if (Test-Path $swigPath) {
    $version = Get-SwigVersion $swigPath
    Write-Host "`nFound conda SWIG:"
    Write-Host "Path: $swigPath"
    Write-Host "Version: $version"
} else {
    Write-Error "Could not find SWIG in conda environment"
    exit 1
}

# Look for other SWIG installations
Write-Host "`nChecking for other SWIG installations in PATH..."
$env:Path -split ';' | Where-Object { $_ } | ForEach-Object {
    $testPath = Join-Path $_ "swig.exe"
    if (Test-Path $testPath) {
        $version = Get-SwigVersion $testPath
        Write-Host "`nFound additional SWIG:"
        Write-Host "Path: $testPath"
        Write-Host "Version: $version"
    }
}

# Set up environment for CMake
$swigRoot = Split-Path $swigPath -Parent
$condaRoot = Split-Path -Parent (Split-Path -Parent $swigRoot)
$swigShare = Join-Path $condaRoot "Library\share\swig\4.2.1"

Write-Host "`nSWIG paths for CMake:"
Write-Host "SWIG_EXECUTABLE: $swigPath"
Write-Host "SWIG_DIR: $swigShare"
Write-Host "SWIG_LIB: $swigShare"
Write-Host "UseFile path: $swigShare\UseFile.cmake"

Write-Host "`nVerifying paths exist:"
@($swigPath, $swigShare) | ForEach-Object {
    Write-Host "$_`: $(Test-Path $_)"
}
