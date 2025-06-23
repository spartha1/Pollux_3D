# Stop on first error
$ErrorActionPreference = "Stop"

Write-Host "Starting build process..."

# Get script directory and setup paths
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$buildDir = Join-Path $scriptDir "build"
$sourceDir = $scriptDir

# Install required Python packages
Write-Host "`nInstalling required Python packages..."
# Get Python path before installing packages
$pythonPath = (Get-Command python.exe).Source

Write-Host "Using Python at: $pythonPath"
Write-Host "Installing NumPy through conda..."
conda install -y numpy=1.24.3 --force-reinstall

# Get tool paths
$cmakePath = (Get-Command cmake.exe).Source
$ninjaPath = (Get-Command ninja.exe).Source
$pythonPath = (Get-Command python.exe).Source

# Get Python and NumPy paths
$pythonInclude = Join-Path $env:CONDA_PREFIX "include"
$numpyInclude = Join-Path $pythonInclude "numpy"

# Create numpy.h if it doesn't exist
$numpyHeader = Join-Path $numpyInclude "arrayobject.h"
if (-not (Test-Path $numpyHeader)) {
    Write-Host "Creating NumPy include directory..."
    New-Item -ItemType Directory -Path $numpyInclude -Force | Out-Null

    # Get actual numpy include path
    $actualNumpyInclude = python -c "import numpy; print(numpy.get_include())" | Out-String
    $actualNumpyInclude = $actualNumpyInclude.Trim()

    # Copy numpy headers
    Copy-Item -Path "$actualNumpyInclude\*" -Destination $numpyInclude -Recurse -Force
}

Write-Host "Python include path: $pythonInclude"
Write-Host "NumPy include path: $numpyInclude"

if (-not (Test-Path $pythonInclude)) {
    Write-Error "Python include directory not found at: $pythonInclude"
    exit 1
}
if (-not (Test-Path $numpyInclude)) {
    Write-Error "NumPy include directory not found at: $numpyInclude"
    exit 1
}

# Get OpenCASCADE paths from conda
$condaPrefix = $env:CONDA_PREFIX
$occIncludeDir = Join-Path $condaPrefix "Library\include\opencascade"
$occLibDir = Join-Path $condaPrefix "Library\lib"

Write-Host "Using paths:"
Write-Host "  Build dir: $buildDir"
Write-Host "  Python: $pythonPath"
Write-Host "  OpenCASCADE Include: $occIncludeDir"
Write-Host "  OpenCASCADE Lib: $occLibDir"

# Create build directory
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir | Out-Null
    Write-Host "Created build directory"
}

# Clean any existing CMake cache
if (Test-Path "$buildDir\CMakeCache.txt") {
    Remove-Item -Force "$buildDir\CMakeCache.txt"
    Write-Host "Cleaned CMake cache"
}

# Prepare CMake arguments
$cmakeArgs = @(
    "-G", "Ninja",
    "--log-level=verbose",
    "-DPYTHON_EXECUTABLE=$pythonPath",
    "-DPython3_ROOT_DIR=$condaPrefix",
    "-DPython3_EXECUTABLE=$pythonPath",
    "-DPYTHON_INCLUDE_DIR=$pythonInclude",
    "-DPYTHON_INCLUDE_DIRS=$pythonInclude",
    "-DNUMPY_INCLUDE_DIR=$numpyInclude",
    "-DOCCT_INCLUDE_DIR=$occIncludeDir",
    "-DOCCT_LIBRARY_DIR=$occLibDir",
    "-DCMAKE_BUILD_TYPE=Release",
    "-B", $buildDir,
    "-S", $sourceDir
)

# Run CMake
Write-Host "`nRunning CMake with arguments:"
$cmakeArgs | ForEach-Object { Write-Host "  $_" }

Write-Host "`nConfiguring with CMake..."
& $cmakePath $cmakeArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "CMake configuration failed"
    exit 1
}

Write-Host "`nBuilding with Ninja..."
& $ninjaPath -C $buildDir

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed"
    exit 1
}

Write-Host "`nBuild completed successfully!"
