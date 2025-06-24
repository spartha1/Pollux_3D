# Stop on first error
$ErrorActionPreference = "Stop"

Write-Host "Starting build process..."

# Ensure we're in the correct conda environment
if (-not $env:CONDA_PREFIX) {
    Write-Error "No conda environment activated. Please run through build_with_vs2.cmd"
    exit 1
}

Write-Host "Using conda environment: $env:CONDA_PREFIX"

# Verify VS environment is properly initialized
Write-Host "`nVerifying Visual Studio environment..."
try {
    $cl = Get-Command cl -ErrorAction Stop
    Write-Host "Found Visual Studio compiler at: $($cl.Path)"
} catch {
    Write-Error "Visual Studio environment not properly initialized. Please run through build_with_vs2.cmd"
    exit 1
}

# Get script directory and setup paths
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$buildDir = Join-Path $scriptDir "build"
$sourceDir = $scriptDir

# Find tools in conda environment
$cmakePath = Join-Path $env:CONDA_PREFIX "Library\bin\cmake.exe"
if (-not (Test-Path $cmakePath)) {
    $cmakePath = (Get-Command cmake -ErrorAction SilentlyContinue).Path
}
if (-not $cmakePath -or -not (Test-Path $cmakePath)) {
    Write-Error "CMake not found. Please ensure it's installed in the conda environment."
    exit 1
}

$ninjaPath = Join-Path $env:CONDA_PREFIX "Library\bin\ninja.exe"
if (-not (Test-Path $ninjaPath)) {
    $ninjaPath = (Get-Command ninja -ErrorAction SilentlyContinue).Path
}
if (-not $ninjaPath -or -not (Test-Path $ninjaPath)) {
    Write-Error "Ninja not found. Please ensure it's installed in the conda environment."
    exit 1
}

$pythonPath = Join-Path $env:CONDA_PREFIX "python.exe"

# Get paths
$pythonInclude = Join-Path $env:CONDA_PREFIX "include"
$pythonLibDir = Join-Path $env:CONDA_PREFIX "libs"
$numpyInclude = python -c "import numpy; print(numpy.get_include())" | Out-String
$numpyInclude = $numpyInclude.Trim()
$occIncludeDir = Join-Path $env:CONDA_PREFIX "Library\include\opencascade"
$occLibDir = Join-Path $env:CONDA_PREFIX "Library\lib"

Write-Host "`nVerifying paths..."
$paths = @{
    "CMake" = $cmakePath
    "Ninja" = $ninjaPath
    "Python" = $pythonPath
    "Python Include" = $pythonInclude
    "Python Library" = $pythonLibDir
    "NumPy Include" = $numpyInclude
    "OpenCASCADE Include" = $occIncludeDir
    "OpenCASCADE Library" = $occLibDir
}

foreach ($item in $paths.GetEnumerator()) {
    if (-not (Test-Path $item.Value)) {
        Write-Error "$($item.Key) not found at: $($item.Value)"
        exit 1
    }
    Write-Host "$($item.Key): $($item.Value)"
}

# Prepare build directory
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir | Out-Null
    Write-Host "Created build directory: $buildDir"
}

# Clean CMake cache
if (Test-Path "$buildDir\CMakeCache.txt") {
    Remove-Item -Force "$buildDir\CMakeCache.txt"
    Write-Host "Cleaned CMake cache"
}

# Set up CMake arguments
$cmakeArgs = @(
    "-G", "Ninja",
    "--log-level=TRACE",
    "-Wdev",
    "--debug-find",
    "-DCMAKE_C_COMPILER=cl",
    "-DCMAKE_CXX_COMPILER=cl",
    "-DCMAKE_VERBOSE_MAKEFILE=ON",
    "-DPYTHON_EXECUTABLE=$pythonPath",
    "-DPython3_ROOT_DIR=$env:CONDA_PREFIX",
    "-DPython3_EXECUTABLE=$pythonPath",
    "-DPYTHON_INCLUDE_DIR=$pythonInclude",
    "-DPYTHON_INCLUDE_DIRS=$pythonInclude",
    "-DPYTHON_LIBRARY=$pythonLibDir",
    "-DPYTHON_DEBUG_LIBRARY=$pythonLibDir",
    "-DNUMPY_INCLUDE_DIR=$numpyInclude",
    "-DOCCT_INCLUDE_DIR=$occIncludeDir",
    "-DOCCT_LIBRARY_DIR=$occLibDir",
    "-DCMAKE_BUILD_TYPE=Release",
    "-DCMAKE_MAKE_PROGRAM=$ninjaPath",
    "-DCMAKE_PREFIX_PATH=$env:CONDA_PREFIX",
    "-DCMAKE_INSTALL_PREFIX=$env:CONDA_PREFIX",
    "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
    "-B", $buildDir,
    "-S", $sourceDir
)

# Run CMake configuration with debug output
Write-Host "`nRunning CMake configuration with debug output..."

# Convert paths to proper format
$cmakePath = $cmakePath.Replace('\', '/')
$buildDir = $buildDir.Replace('\', '/')
$sourceDir = $sourceDir.Replace('\', '/')

# Create the debug command line
$debugCmd = """$cmakePath"" -G ""Ninja"" --debug-find -DCMAKE_FIND_DEBUG_MODE=ON -B ""$buildDir"" -S ""$sourceDir"""
Write-Host "Debug command: $debugCmd"

# Run debug configuration
$debugOutput = cmd /c $debugCmd 2>&1
Write-Host "`nPackage detection output:"
$debugOutput | ForEach-Object { Write-Host $_ }

# Now run actual configuration
Write-Host "`nRunning main CMake configuration..."
Write-Host "CMake arguments:"
$cmakeArgs | ForEach-Object { Write-Host "  $_" }

# Create the main command line
$mainCmd = """$cmakePath"" $($cmakeArgs -join ' ')"
Write-Host "Main command: $mainCmd"

$cmakeOutput = cmd /c $mainCmd 2>&1
$cmakeSuccess = $LASTEXITCODE -eq 0

# Always show CMake output
Write-Host "`nCMake output:"
$cmakeOutput | ForEach-Object { Write-Host $_ }

if (-not $cmakeSuccess) {
    Write-Error "CMake configuration failed"
    exit 1
}

# Run build
Write-Host "`nBuilding with Ninja..."
& $ninjaPath -C $buildDir

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed"
    exit 1
}

Write-Host "`nBuild completed successfully!"
