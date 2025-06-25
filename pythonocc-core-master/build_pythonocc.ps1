# Script to build pythonocc-core with proper Visual Studio environment
$ErrorActionPreference = "Stop"

Write-Host "Setting up build environment..."

# First, run the SWIG check script to ensure SWIG is properly configured
$swigCheckScript = Join-Path $PSScriptRoot "check_swig.ps1"
. $swigCheckScript

# Find Visual Studio installation using vswhere
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path $vswhere)) {
    Write-Error "Visual Studio Installer not found. Please install Visual Studio 2019 or newer with C++ development tools."
    exit 1
}

$vsPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vsPath) {
    Write-Error "Visual Studio with C++ tools not found. Please install Visual Studio 2019 or newer with C++ development tools."
    exit 1
}

# Import Visual Studio environment
$vcvarsall = Join-Path $vsPath "VC\Auxiliary\Build\vcvars64.bat"
if (-not (Test-Path $vcvarsall)) {
    Write-Error "Visual Studio environment setup script not found at: $vcvarsall"
    exit 1
}

Write-Host "Importing Visual Studio environment from: $vcvarsall"
$tempFile = [System.IO.Path]::GetTempFileName()
cmd /c """$vcvarsall"" amd64 && set > ""$tempFile"""
Get-Content $tempFile | ForEach-Object {
    if ($_ -match "^(.*?)=(.*)$") {
        $name = $matches[1]
        $value = $matches[2]
        Set-Item "env:$name" $value
    }
}
Remove-Item $tempFile

# Ensure we're in a conda environment
if (-not $env:CONDA_PREFIX) {
    Write-Error "No active conda environment detected. Please activate your conda environment first."
    exit 1
}

# Create and enter build directory
$buildDir = Join-Path $PSScriptRoot "build"
if (Test-Path $buildDir) {
    Write-Host "Cleaning existing build directory..."
    Remove-Item -Path $buildDir -Recurse -Force
}
New-Item -Path $buildDir -ItemType Directory -Force | Out-Null
Set-Location $buildDir

# Run CMake configuration
Write-Host "`nRunning CMake configuration..."
$cmakeArgs = @(
    "-G", "Ninja",
    "-DCMAKE_BUILD_TYPE=Release",
    "-DPYTHONOCC_WRAP_OCCT=TRUE",
    "-DSWIG_EXECUTABLE=$swigPath",
    "-DSWIG_DIR=$swigShare",
    "-DSWIG_LIB=$swigShare",
    "-DSWIG_LIBRARY_PATH=$swigShare",
    "-DPYTHON_EXECUTABLE=$env:CONDA_PREFIX\python.exe",
    "-DPython3_ROOT_DIR=$env:CONDA_PREFIX",
    "-DPYTHON_INCLUDE_DIR=$env:CONDA_PREFIX\include",
    "-DOCCT_INCLUDE_DIR=$env:CONDA_PREFIX\Library\include\opencascade",
    "-DOCCT_LIBRARY_DIR=$env:CONDA_PREFIX\Library\lib",
    "-DNUMPY_INCLUDE_DIR=$env:CONDA_PREFIX\Lib\site-packages\numpy\core\include",
    ".."
)

& cmake $cmakeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "CMake configuration failed"
    exit 1
}

# Run the build
Write-Host "`nRunning build with Ninja..."
& ninja
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed"
    exit 1
}

Write-Host "`nBuild completed successfully!"
