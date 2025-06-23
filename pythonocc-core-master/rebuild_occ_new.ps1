# Stop on first error
$ErrorActionPreference = "Stop"
$PSDefaultParameterValues['*:ErrorAction'] = 'Stop'

function Initialize-Build {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $buildDir = Join-Path $scriptDir "build"
    $sourceDir = $scriptDir

    # Create build directory if it doesn't exist
    if (-not (Test-Path $buildDir)) {
        New-Item -ItemType Directory -Path $buildDir | Out-Null
    }

    return @{
        BuildDir = $buildDir
        SourceDir = $sourceDir
    }
}

function Find-CondaInstallation {
    Write-Host "Looking for conda installation..."

    # First try CONDA_PREFIX
    if ($env:CONDA_PREFIX) {
        Write-Host "Found conda from CONDA_PREFIX at: $env:CONDA_PREFIX"
        return $env:CONDA_PREFIX
    }

    # Then try common locations
    $commonPaths = @(
        "$env:USERPROFILE\miniconda3",
        "$env:USERPROFILE\Anaconda3",
        "C:\ProgramData\miniconda3",
        "C:\ProgramData\Anaconda3"
    )

    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            Write-Host "Found conda installation at: $path"
            return $path
        }
    }

    throw "Could not find conda installation"
}

function Initialize-CondaEnv {
    param ($CondaPath)

    Write-Host "Installing required packages..."
    Write-Host "Installing in environment: base"

    # Add conda-forge channel
    Write-Host "Adding conda-forge channel..."
    & conda config --add channels conda-forge
    if ($LASTEXITCODE -ne 0) { throw "Failed to add conda-forge channel" }

    # Install required packages
    $packages = @("cmake", "ninja", "swig=4.2.1")
    foreach ($package in $packages) {
        Write-Host "Installing $package..."
        & conda install -y $package
        if ($LASTEXITCODE -ne 0) { throw "Failed to install $package" }
    }
}

function Get-BuildTools {
    # Find required tools
    $tools = @{
        CMake = (Get-Command cmake.exe -ErrorAction Stop).Source
        Ninja = (Get-Command ninja.exe -ErrorAction Stop).Source
        Swig = (Get-Command swig.exe -ErrorAction Stop).Source
        Python = (Get-Command python.exe -ErrorAction Stop).Source
    }

    Write-Host "Found tools:"
    $tools.GetEnumerator() | ForEach-Object {
        Write-Host "$($_.Key): $($_.Value)"
        if ($_.Key -eq "Swig") {
            $version = & $_.Value -version 2>&1 | Select-String "SWIG Version"
            Write-Host "SWIG Version: $version"
        }
    }

    return $tools
}

function Clear-CMakeCache {
    param($BuildDir)

    if (Test-Path "$BuildDir\CMakeCache.txt") {
        Write-Host "Removing CMake cache..."
        Remove-Item -Force "$BuildDir\CMakeCache.txt"
    }
    if (Test-Path "$BuildDir\CMakeFiles") {
        Write-Host "Removing CMakeFiles directory..."
        Remove-Item -Force -Recurse "$BuildDir\CMakeFiles"
    }
}

function Find-SwigInPath {
    Write-Host "`nChecking for other SWIG installations in PATH..."
    $pathDirs = $env:Path -split ";" | Where-Object { $_ }

    foreach ($dir in $pathDirs) {
        $swigPath = Join-Path $dir "swig.exe"
        if (Test-Path $swigPath) {
            Write-Host "Found SWIG at: $swigPath"
            $version = & $swigPath -version 2>&1 | Select-String "SWIG Version"
            Write-Host "Version: $version"
        }
    }
}

function Invoke-CMakeBuild {
    param(
        $BuildInfo,
        $Tools
    )

    Clear-CMakeCache -BuildDir $BuildInfo.BuildDir
    Find-SwigInPath

    Write-Host "`nConfiguring with CMake..."
    $swigRoot = Split-Path $Tools.Swig -Parent
    $swigShare = Join-Path (Split-Path $swigRoot -Parent) "share" "swig" "4.2.1"

    $env:SWIG_LIB = $swigShare
    $env:PATH = "$swigRoot;$env:PATH"

    $cmakeArgs = @(
        "-G", "Ninja"
        "-DSWIG_EXECUTABLE=`"$($Tools.Swig)`""
        "-DSWIG_DIR=`"$swigShare`""
        "-DSWIG_USE_FILE=`"$swigShare\UseFile.cmake`""
        "-DSWIG_VERSION=4.2.1"
        "-DSWIG_INCLUDE_DIR=`"$swigShare`""
        "-DPYTHON_EXECUTABLE=`"$($Tools.Python)`""
        "-DCMAKE_BUILD_TYPE=Release"
        "-B", "`"$($BuildInfo.BuildDir)`""
        "-S", "`"$($BuildInfo.SourceDir)`""
    )

    Write-Host "Running CMake with arguments:"
    $cmakeArgs | ForEach-Object { Write-Host "  $_" }

    & $Tools.CMake @cmakeArgs
    if ($LASTEXITCODE -ne 0) { throw "CMake configuration failed" }

    Write-Host "`nBuilding with Ninja..."
    & $Tools.Ninja -C $BuildInfo.BuildDir
    if ($LASTEXITCODE -ne 0) { throw "Build failed" }
}

try {
    # Main execution flow
    $buildInfo = Initialize-Build
    $condaPath = Find-CondaInstallation
    Initialize-CondaEnv -CondaPath $condaPath
    $tools = Get-BuildTools
    Invoke-CMakeBuild -BuildInfo $buildInfo -Tools $tools

    Write-Host "`nBuild completed successfully!"
} catch {
    Write-Error "Build failed: $_"
    Write-Error $_.ScriptStackTrace
    exit 1
}
