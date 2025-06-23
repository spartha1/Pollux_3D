# Stop on first error
$ErrorActionPreference = "Stop"

Write-Host "Starting build process..."

# Ensure we're in the correct conda environment
if (-not $env:CONDA_PREFIX) {
    Write-Error "No conda environment activated. Please run: conda activate pythonocc-env"
    exit 1
}

Write-Host "Using conda environment: $env:CONDA_PREFIX"

# Get script directory and setup paths
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$buildDir = Join-Path $scriptDir "build"
$sourceDir = $scriptDir

# Find required tools
$cmakePath = Join-Path $env:CONDA_PREFIX "Library\bin\cmake.exe"
if (-not (Test-Path $cmakePath)) {
    $cmakePath = (Get-Command cmake -ErrorAction SilentlyContinue).Path
}

# Look for ninja in multiple locations
$ninjaLocations = @(
    (Join-Path $env:CONDA_PREFIX "Scripts\ninja.exe"),
    (Join-Path $env:CONDA_PREFIX "Library\bin\ninja.exe"),
    (Get-Command ninja -ErrorAction SilentlyContinue).Path
)
$ninjaPath = $null
foreach ($path in $ninjaLocations) {
    if ($path -and (Test-Path $path)) {
        $ninjaPath = $path
        Write-Host "Found Ninja at: $path"
        break
    }
}

$pythonPath = Join-Path $env:CONDA_PREFIX "python.exe"

# Verify tools exist
if (-not (Test-Path $cmakePath)) {
    Write-Error "CMake not found at: $cmakePath"
    exit 1
}
if (-not $ninjaPath) {
    Write-Error "Ninja not found in any expected location"
    exit 1
}
if (-not (Test-Path $pythonPath)) {
    Write-Error "Python not found at: $pythonPath"
    exit 1
}

# Get Python and NumPy paths
$pythonInclude = Join-Path $env:CONDA_PREFIX "include"
$numpyInclude = Join-Path $env:CONDA_PREFIX "Lib\site-packages\numpy\core\include"
if (-not (Test-Path $numpyInclude)) {
    # Try alternate location
    $numpyInclude = python -c "import numpy; print(numpy.get_include())" | Out-String
    $numpyInclude = $numpyInclude.Trim()
}

# Get OpenCASCADE paths
$occIncludeDir = Join-Path $env:CONDA_PREFIX "Library\include\opencascade"
$occLibDir = Join-Path $env:CONDA_PREFIX "Library\lib"

Write-Host "`nUsing paths:"
Write-Host "  Build dir: $buildDir"
Write-Host "  CMake: $cmakePath"
Write-Host "  Ninja: $ninjaPath"
Write-Host "  Python: $pythonPath"
Write-Host "  Python include: $pythonInclude"
Write-Host "  NumPy include: $numpyInclude"
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
    "-DPython3_ROOT_DIR=$env:CONDA_PREFIX",
    "-DPython3_EXECUTABLE=$pythonPath",
    "-DPYTHON_INCLUDE_DIR=$pythonInclude",
    "-DPYTHON_INCLUDE_DIRS=$pythonInclude",
    "-DNUMPY_INCLUDE_DIR=$numpyInclude",
    "-DOCCT_INCLUDE_DIR=$occIncludeDir",
    "-DOCCT_LIBRARY_DIR=$occLibDir",
    "-DCMAKE_BUILD_TYPE=Release",
    "-DCMAKE_MAKE_PROGRAM=$ninjaPath",
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
