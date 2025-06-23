# First, run this script from a clean PowerShell session
# Initialize Visual Studio environment
& "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64

# Activate conda base environment and install required tools
# Initialize Visual Studio environment
Write-Host "Initializing Visual Studio environment..."
$vsPath = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
& "${env:COMSPEC}" /c "`"$vsPath`" x64 && set" | foreach-object {
    if ($_ -match "=") {
        $v = $_.split("=")
        Set-Item -Force -Path "ENV:\$($v[0])" -Value "$($v[1])"
    }
}

# Find Miniconda/Anaconda installation
Write-Host "Looking for conda installation..."

# First, try to use CONDA_PREFIX if we're in an environment
$condaPath = $null
if ($env:CONDA_PREFIX) {
    $basePath = Split-Path (Split-Path $env:CONDA_PREFIX)
    $condaExePath = Join-Path $basePath "Scripts\conda.exe"
    if (Test-Path $condaExePath) {
        $condaPath = $basePath
        Write-Host "Found conda installation from CONDA_PREFIX at: $condaPath"
    }
}

# If not found through CONDA_PREFIX, check common locations
if (-not $condaPath) {
    $possiblePaths = @(
        (Join-Path $env:USERPROFILE "AppData\Local\miniconda3"),
        (Join-Path $env:USERPROFILE "AppData\Local\miniconda"),
        (Join-Path $env:USERPROFILE "miniconda3"),
        (Join-Path $env:USERPROFILE "Anaconda3"),
        (Join-Path ${env:ProgramFiles} "Miniconda3"),
        (Join-Path ${env:ProgramFiles} "Anaconda3")
    )

    foreach ($path in $possiblePaths) {
        $testPath = Join-Path $path "Scripts\conda.exe"
        if (Test-Path $testPath) {
            $condaPath = $path
            Write-Host "Found conda installation at: $condaPath"
            break
        }
    }
}

if (-not $condaPath) {
    Write-Host "Could not find Miniconda/Anaconda installation in common locations."
    Write-Host "Searched in:"
    $possiblePaths | ForEach-Object { Write-Host "  $_" }
    Write-Host "Please ensure Miniconda/Anaconda is installed and try again."
    exit 1
}

# Install required packages
Write-Host "Installing required packages..."
$condaExe = Join-Path $condaPath "Scripts\conda.exe"

if (Test-Path $condaExe) {
    # Install required packages in current environment
    if ($env:CONDA_DEFAULT_ENV) {
        Write-Host "Installing in environment: $env:CONDA_DEFAULT_ENV"

        # Add conda-forge channel if not already added
        Write-Host "Adding conda-forge channel..."
        & $condaExe config --add channels conda-forge
        & $condaExe config --set channel_priority strict

        # Clean any existing SWIG installation
        Write-Host "Removing existing SWIG installation..."
        & $condaExe remove -y -n $env:CONDA_DEFAULT_ENV swig
        & $condaExe clean -y --all

        # Install packages with explicit channel specification
        Write-Host "Installing packages from conda-forge..."
        & $condaExe install -y -c conda-forge -n $env:CONDA_DEFAULT_ENV cmake ninja "swig=4.2.1"

        # Verify installation
        $cmakeCheck = & $condaExe list -n $env:CONDA_DEFAULT_ENV cmake
        $ninjaCheck = & $condaExe list -n $env:CONDA_DEFAULT_ENV ninja
        $swigCheck = & $condaExe list -n $env:CONDA_DEFAULT_ENV swig

        # Verify SWIG version with extra diagnostics
        $swigPath = Join-Path $env:CONDA_PREFIX "Library\bin\swig.exe"
        Write-Host "`nChecking SWIG installation:"
        Write-Host "SWIG path: $swigPath"

        if (Test-Path $swigPath) {
            $swigOutput = & $swigPath -version
            Write-Host "SWIG version output:"
            $swigOutput | ForEach-Object { Write-Host "  $_" }

            $swigVersion = $swigOutput | Select-String "SWIG Version" | ForEach-Object { $_.ToString().Split(" ")[-1] }
            Write-Host "Parsed SWIG version: $swigVersion"

            if ($swigVersion -ne "4.2.1") {
                Write-Host "Error: Incorrect SWIG version. Required: 4.2.1, Found: $swigVersion"
                Write-Host "Please try reinstalling SWIG manually:"
                Write-Host "conda remove swig"
                Write-Host "conda clean --all"
                Write-Host "conda install -c conda-forge swig=4.2.1"
                exit 1
            }
            Write-Host "Found correct SWIG version: $swigVersion"
        } else {
            Write-Host "Error: SWIG executable not found at expected location"
            exit 1
        }

        if (-not ($cmakeCheck -match "cmake" -and $ninjaCheck -match "ninja" -and $swigCheck -match "swig")) {
            Write-Host "Failed to install required packages. Please try installing manually:"
            Write-Host "conda install -c conda-forge cmake ninja swig"
            exit 1
        }
    } else {
        Write-Host "Installing in base environment"
        & $condaExe install -y -c conda-forge cmake ninja
    }
} else {
    Write-Host "Conda executable not found at: $condaExe"
    exit 1
}

# Get the script's directory and create build directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $scriptDir "build"
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir
}
Set-Location $buildDir

# Run CMake configuration
Write-Host "Running CMake configuration..."

# Find tools in environment
if ($env:CONDA_PREFIX) {
    $envPath = $env:CONDA_PREFIX
} else {
    $envPath = Join-Path $condaPath "envs\pyoccenv"
}

$pythonPath = Join-Path $envPath "python.exe"

# Look for tools in multiple possible locations
$possibleToolPaths = @(
    (Join-Path $envPath "Scripts"),
    (Join-Path $envPath "Library\bin"),
    (Join-Path $envPath "bin")
)

Write-Host "Looking for tools in:"
$possibleToolPaths | ForEach-Object { Write-Host "  $_" }

# Find cmake, ninja, and swig
$cmakePath = $null
$ninjaPath = $null
$swigPath = $null

foreach ($toolPath in $possibleToolPaths) {
    $testCmakePath = Join-Path $toolPath "cmake.exe"
    $testNinjaPath = Join-Path $toolPath "ninja.exe"
    $testSwigPath = Join-Path $toolPath "swig.exe"

    if (Test-Path $testCmakePath) {
        $cmakePath = $testCmakePath
        Write-Host "Found cmake at: $cmakePath"
    }

    if (Test-Path $testNinjaPath) {
        $ninjaPath = $testNinjaPath
        Write-Host "Found ninja at: $ninjaPath"
    }

    if (Test-Path $testSwigPath) {
        $swigPath = $testSwigPath
        Write-Host "Found swig at: $swigPath"
    }
}

# Show conda package info
Write-Host "`nChecking conda package information..."
& $condaExe list -n $env:CONDA_DEFAULT_ENV cmake
& $condaExe list -n $env:CONDA_DEFAULT_ENV ninja
Write-Host "Python executable: $pythonPath"

if (-not $cmakePath) {
    Write-Host "CMake not found in any of the expected locations"
    Write-Host "Please ensure cmake is installed with: conda install -c conda-forge cmake"
    exit 1
}

if (-not $ninjaPath) {
    Write-Host "Ninja not found in any of the expected locations"
    Write-Host "Please ensure ninja is installed with: conda install -c conda-forge ninja"
    exit 1
}

if (-not $swigPath) {
    Write-Host "SWIG not found in any of the expected locations"
    Write-Host "Please ensure swig is installed with: conda install -c conda-forge swig"
    exit 1
}

Write-Host "`nVerifying tool versions before CMake:"
Write-Host "CMake version:"
& $cmakePath --version
Write-Host "`nNinja version:"
& $ninjaPath --version
Write-Host "`nSWIG version:"
& $swigPath -version
Write-Host "`nPython version:"
& $pythonPath --version

Write-Host "`nRunning CMake with:"
Write-Host "  CMake: $cmakePath"
Write-Host "  Ninja: $ninjaPath"
Write-Host "  Python: $pythonPath"
Write-Host "  SWIG: $swigPath"
Write-Host "  Source: $scriptDir`n"

# Clear CMake cache before configuration
Clear-CMakeCache -buildDir $buildDir

# Check for other SWIG installations that might interfere
Find-SwigInPath

Write-Host "`nConfiguring with CMake..."
$swigRoot = Split-Path (Get-Command swig.exe).Path -Parent
$swigShare = Join-Path (Split-Path $swigRoot -Parent) "share" "swig" "4.2.1"
$env:SWIG_LIB = $swigShare
$env:PATH = "$swigRoot;$env:PATH"

$cmakeArgs = @(
    "-G", "Ninja"
    "-DSWIG_EXECUTABLE=`"$swigRoot\swig.exe`""
    "-DSWIG_DIR=`"$swigShare`""
    "-DSWIG_USE_FILE=`"$swigShare\UseFile.cmake`""
    "-DSWIG_VERSION=4.2.1"
    "-DSWIG_INCLUDE_DIR=`"$swigShare`""
    "-DPYTHON_EXECUTABLE=`"$pythonExe`""
    "-DCMAKE_BUILD_TYPE=Release"
    "-B", $buildDir
    "-S", $sourceDir
)

Write-Host "Running CMake with arguments:"
$cmakeArgs | ForEach-Object { Write-Host "  $_" }

& $cmakeExe @cmakeArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "CMake configuration failed"
    exit 1
}

Write-Host "`nBuilding with Ninja..."
& $ninjaExe -C $buildDir

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed with exit code $LASTEXITCODE"
    exit 1
}

Write-Host "`nBuild completed successfully!"

function Clear-CMakeCache {
    param($buildDir)

    if (Test-Path "$buildDir\CMakeCache.txt") {
        Write-Host "Removing CMake cache..."
        Remove-Item -Force "$buildDir\CMakeCache.txt"
    }
    if (Test-Path "$buildDir\CMakeFiles") {
        Write-Host "Removing CMakeFiles directory..."
        Remove-Item -Force -Recurse "$buildDir\CMakeFiles"
    }
}

function Find-SwigInPath {
    Write-Host "`nChecking for other SWIG installations in PATH..."
    $pathDirs = $env:Path -split ";" | Where-Object { $_ }

    foreach ($dir in $pathDirs) {
        $swigPath = Join-Path $dir "swig.exe"
        if (Test-Path $swigPath) {
            Write-Host "Found SWIG at: $swigPath"
            if (Test-Path $swigPath) {
                $version = & $swigPath -version 2>&1 | Select-String "SWIG Version" | ForEach-Object { $_.ToString().Split(" ")[-1] }
                Write-Host "Version: $version"
            }
        }
    }
}
