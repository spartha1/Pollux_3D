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

# Ensure we're in a conda environment
if (-not $env:CONDA_PREFIX) {
    Write-Error "Not in a conda environment. Please activate a conda environment first."
    exit 1
}

Write-Host "Using conda environment: $env:CONDA_PREFIX"

# Verify we're in the correct environment
$envName = "pythonocc-env"
if ($env:CONDA_DEFAULT_ENV -ne $envName) {
    Write-Error "Please activate the correct conda environment first using: conda activate $envName"
    exit 1
}

# Verify required packages are installed
Write-Host "`nVerifying required packages..."
conda list numpy | Select-String "1.24.3" | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "NumPy 1.24.3 not found. Please run setup_build_env.ps1 first."
    exit 1
}

# Get tool paths from conda environment
$cmakePath = Join-Path $env:CONDA_PREFIX "Library\bin\cmake.exe"
$ninjaPath = Join-Path $env:CONDA_PREFIX "Scripts\ninja.exe"
$pythonPath = Join-Path $env:CONDA_PREFIX "python.exe"

# Get include paths
$pythonInclude = Join-Path $env:CONDA_PREFIX "include"
$numpyInclude = Join-Path $env:CONDA_PREFIX "Lib\site-packages\numpy\core\include"
$occIncludeDir = Join-Path $env:CONDA_PREFIX "Library\include\opencascade"
$occLibDir = Join-Path $env:CONDA_PREFIX "Library\lib"

Write-Host "`nUsing paths:"
Write-Host "  Build dir: $buildDir"
Write-Host "  Python: $pythonPath"
Write-Host "  Python include: $pythonInclude"
Write-Host "  NumPy include: $numpyInclude"
Write-Host "  OpenCASCADE Include: $occIncludeDir"
Write-Host "  OpenCASCADE Lib: $occLibDir"

# Verify paths exist
$paths = @($pythonPath, $cmakePath, $ninjaPath, $numpyInclude, $occIncludeDir, $occLibDir)
foreach ($path in $paths) {
    if (-not (Test-Path $path)) {
        Write-Error "Required path not found: $path"
        exit 1
    }
}

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
