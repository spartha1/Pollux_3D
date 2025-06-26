# Add CUDA support if available
$cudaPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0"
if (Test-Path $cudaPath) {
    Write-Host "Found CUDA installation at $cudaPath"
    $env:CUDA_PATH = $cudaPath
    $env:PATH = "$cudaPath\bin;$cudaPath\libnvvp;$env:PATH"
    $env:INCLUDE = "$cudaPath\include;$env:INCLUDE"
    $env:LIB = "$cudaPath\lib\x64;$env:LIB"
}

# Set up SWIG paths to use local installation in the project directory
$swigDir = Join-Path $PSScriptRoot "swigwin-4.2.1"
$swigExe = Join-Path $swigDir "swig.exe"
$swigLibDir = Join-Path $swigDir "Lib"

# Check for existing SWIG installation in the project directory
if (Test-Path $swigDir) {
    Write-Host "Found existing SWIG installation at $swigDir"
    if (Test-Path $swigExe) {
        Write-Host "Found SWIG executable"
        try {
            $swigVersion = & $swigExe -version
            Write-Host "Detected SWIG version: $swigVersion"

            # Verify SWIG library files exist
            $requiredFiles = @("swig.swg", "python.swg", "typemaps.i")
            $missingFiles = $false
            foreach ($file in $requiredFiles) {
                if (-not (Test-Path (Join-Path $swigLibDir $file))) {
                    $missingFiles = $true
                    Write-Host "Missing required SWIG file: $file"
                }
            }

            if (-not $missingFiles -and $swigVersion -match "SWIG Version 4.2.1") {
                Write-Host "Found complete SWIG 4.2.1 installation, using local version"
                $env:SWIG_EXECUTABLE = $swigExe
                $env:SWIG_DIR = $swigDir
                $env:SWIG_LIB = $swigLibDir
                return
            }
        } catch {
            Write-Host "Existing SWIG installation appears to be incomplete"
        }
    }
}

# Verify SWIG exists or download it
if (-not (Test-Path $swigDir)) {
    Write-Host "SWIG not found. Downloading SWIG 4.2.1..."
    $swigZip = Join-Path $env:TEMP "swigwin-4.2.1.zip"
    $swigUrls = @(
        "https://github.com/swig/swigwin/releases/download/v4.2.1/swigwin-4.2.1.zip",
        "https://versaweb.dl.sourceforge.net/project/swig/swigwin/swigwin-4.2.1/swigwin-4.2.1.zip",
        "https://downloads.sourceforge.net/project/swig/swigwin/swigwin-4.2.1/swigwin-4.2.1.zip"
    )

    $downloaded = $false
    foreach ($url in $swigUrls) {
        try {
            Write-Host "Attempting to download SWIG from $url"
            $webClient = New-Object System.Net.WebClient
            $webClient.DownloadFile($url, $swigZip)

            if (Test-Path $swigZip) {
                $downloaded = $true
                Write-Host "Successfully downloaded SWIG"
                break
            }
        } catch {
            Write-Host "Failed to download from $url, trying next mirror..."
            continue
        }
    }

    if (-not $downloaded) {
        Write-Error "Failed to download SWIG from any mirror"
        exit 1
    }

    try {
        Write-Host "Extracting SWIG..."
        if (-not (Test-Path $PSScriptRoot)) {
            New-Item -ItemType Directory -Path $PSScriptRoot -Force | Out-Null
        }

        # Remove existing SWIG directory if it exists
        if (Test-Path $swigDir) {
            Write-Host "Removing existing SWIG installation..."
            Remove-Item -Path $swigDir -Recurse -Force
        }

        Add-Type -AssemblyName System.IO.Compression.FileSystem
        Write-Host "Extracting to $PSScriptRoot"
        [System.IO.Compression.ZipFile]::ExtractToDirectory($swigZip, $PSScriptRoot)
        Remove-Item $swigZip -Force

        if (-not (Test-Path $swigDir)) {
            Write-Error "SWIG directory not found after extraction"
            exit 1
        }
        Write-Host "Successfully extracted SWIG to $swigDir"
    } catch {
        Write-Error "Failed to extract SWIG: $_"
        exit 1
    }
}

# Verify SWIG installation
if (-not (Test-Path $swigExe)) {
    Write-Error "SWIG executable not found at $swigExe after installation"
    exit 1
}

Write-Host "Using SWIG from: $swigExe"
try {
    $swigVersion = & $swigExe -version
    Write-Host "SWIG version: $swigVersion"
} catch {
    Write-Error "Failed to get SWIG version: $_"
    exit 1
}

# Set environment variables for SWIG
$env:SWIG_EXECUTABLE = $swigExe
$env:SWIG_DIR = $swigDir
$env:SWIG_LIB = $swigLibDir

# Find Visual Studio installation
$vswhereUrl = "https://github.com/microsoft/vswhere/releases/download/3.1.7/vswhere.exe"
$vswhereExe = Join-Path $env:TEMP "vswhere.exe"
Invoke-WebRequest -Uri $vswhereUrl -OutFile $vswhereExe -UseBasicParsing

# Run vswhere to find VS installation path
$vsPath = & $vswhereExe -latest -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vsPath) {
    Write-Error "Visual Studio with C++ tools not found"
    exit 1
}

Write-Host "Found Visual Studio at: $vsPath"

# Find Windows SDK
$sdkPath = "C:\Program Files (x86)\Windows Kits\10"
$sdkVer = (Get-ChildItem -Path "$sdkPath\Include" -Directory | Sort-Object Name -Descending | Select-Object -First 1).Name

# Find latest MSVC tools version
$vcToolsPath = Get-ChildItem -Path "$vsPath\VC\Tools\MSVC" | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName

# Set up Visual C++ environment variables manually
$vcToolsPath = Join-Path $vsPath "VC\Tools\MSVC\14.44.35211"
$sdkLibPath = Join-Path $sdkPath "Lib\$sdkVer"

# Add Visual C++ and Windows SDK paths to LIB
$env:LIB = @(
    "$vcToolsPath\ATLMFC\lib\x64",
    "$vcToolsPath\lib\x64",
    "$sdkLibPath\ucrt\x64",
    "$sdkLibPath\um\x64"
) -join ";"

# Add Visual C++ and Windows SDK paths to INCLUDE
$env:INCLUDE = @(
    "$vcToolsPath\ATLMFC\include",
    "$vcToolsPath\include",
    "$sdkPath\include\$sdkVer\ucrt",
    "$sdkPath\include\$sdkVer\shared",
    "$sdkPath\include\$sdkVer\um",
    "$sdkPath\include\$sdkVer\winrt",
    "$sdkPath\include\$sdkVer\cppwinrt"
) -join ";"

# Add Visual C++ and Windows SDK paths to Path
$env:Path = @(
    "$vcToolsPath\bin\HostX64\x64",
    "$sdkPath\bin\$sdkVer\x64",
    $env:Path
) -join ";"

Write-Host "Environment variables set:"
Write-Host "LIB: $env:LIB"
Write-Host "INCLUDE: $env:INCLUDE"

Write-Host "Current directory: $(Get-Location)"
Write-Host "PATH: $env:Path"
Write-Host "INCLUDE: $env:INCLUDE"
Write-Host "LIB: $env:LIB"

Write-Host "Cleaning build directory..."
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
New-Item -ItemType Directory -Path "build" | Out-Null
Set-Location "build"

Write-Host "Configuring CMake..."
# Get the correct Python paths
$pythonDir = "C:\Users\Leinad\miniconda3\envs\pythonocc-env"
$pythonExe = Join-Path $pythonDir "python.exe"
$pythonInclude = Join-Path $pythonDir "include"
$pythonLibs = Join-Path $pythonDir "libs"

# Set up paths for the existing SWIG installation
$swigDir = Join-Path $PSScriptRoot "swigwin-4.2.1"
$swigExe = Join-Path $swigDir "swig.exe"
$swigLibDir = Join-Path $swigDir "Lib"
$swigPythonDir = Join-Path $swigLibDir "python"

# Verify SWIG executable exists
if (-not (Test-Path $swigExe)) {
    Write-Error "SWIG executable not found at $swigExe. Please ensure SWIG is properly installed in the project directory."
    exit 1
}

Write-Host "Found SWIG installation at: $swigDir"

# Ensure directories exist
if (-not (Test-Path $swigLibDir)) {
    New-Item -ItemType Directory -Path $swigLibDir | Out-Null
}
if (-not (Test-Path $swigPythonDir)) {
    New-Item -ItemType Directory -Path $swigPythonDir | Out-Null
}

# Verify SWIG library files exist
Write-Host "Verifying SWIG library files..."
$requiredFiles = @(
    @{Path = "swig.swg"; Dir = "" },
    @{Path = "python/python.swg"; Dir = "" },
    @{Path = "typemaps.i"; Dir = "" },
    @{Path = "std/std_common.i"; Dir = "std" },
    @{Path = "std/std_string.i"; Dir = "std" },
    @{Path = "std/std_vector.i"; Dir = "std" }
)

foreach ($file in $requiredFiles) {
    $filePath = Join-Path $swigLibDir $file.Path
    Write-Host "Checking for $filePath..."
    if (-not (Test-Path $filePath)) {
        Write-Error "Required SWIG file not found: $($file.Path) in $swigLibDir"
        exit 1
    } else {
        Write-Host "Found $($file.Path)"
    }
}

Write-Host "All required SWIG files found"

# Set SWIG environment variables
$env:SWIG_LIB = $swigLibDir
$env:SWIG_DIR = $swigDir
$env:SWIG_EXECUTABLE = $swigExe
Write-Host "Setting SWIG environment variables:"
Write-Host "SWIG_LIB = $env:SWIG_LIB"
Write-Host "SWIG_DIR = $env:SWIG_DIR"
Write-Host "SWIG_EXECUTABLE = $env:SWIG_EXECUTABLE"

Write-Host "SWIG version:"
& $swigExe -version

Write-Host "Python paths:"
Write-Host "Executable: $pythonExe"
Write-Host "Include: $pythonInclude"
Write-Host "Libraries: $pythonLibs"
Write-Host "SWIG paths:"
Write-Host "Directory: $swigDir"
Write-Host "Executable: $swigExe"
Write-Host "Library: $swigLibDir"

# Ensure we're in the root directory
Set-Location $PSScriptRoot

Write-Host "Cleaning build directory..."
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
New-Item -ItemType Directory -Path "build" | Out-Null
Set-Location "build"

Write-Host "Configuring CMake..."

# Set environment variables for SWIG
$env:SWIG_EXECUTABLE = $swigExe
$env:SWIG_DIR = $swigDir
$env:SWIG_LIB = $swigLibDir
$env:PATH = "$swigDir;$env:PATH"

Write-Host "SWIG environment variables:"
Write-Host "SWIG_EXECUTABLE: $env:SWIG_EXECUTABLE"
Write-Host "SWIG_DIR: $env:SWIG_DIR"
Write-Host "SWIG_LIB: $env:SWIG_LIB"

# Add OpenCASCADE include directory to INCLUDE path
$condaPrefix = "C:\Users\Leinad\miniconda3\envs\pythonocc-env\Library"
$opencascadeInclude = Join-Path $condaPrefix "include"

Write-Host "Searching for OpenCASCADE headers in: $opencascadeInclude"
if (-not (Test-Path $opencascadeInclude)) {
    Write-Error "OpenCASCADE include directory not found at $opencascadeInclude"
    exit 1
}

# Search for math_VectorBase.hxx in possible locations
$possiblePaths = @(
    "$opencascadeInclude\opencascade\math_VectorBase.hxx",
    "$opencascadeInclude\math_VectorBase.hxx",
    "$opencascadeInclude\occt\math_VectorBase.hxx"
)

$mathHeader = $null
foreach ($path in $possiblePaths) {
    Write-Host "Checking for math_VectorBase.hxx at: $path"
    if (Test-Path $path) {
        $mathHeader = $path
        $opencascadeInclude = Split-Path -Parent $path
        Write-Host "Found math_VectorBase.hxx at: $path"
        break
    }
}

if (-not $mathHeader) {
    Write-Error "Could not find math_VectorBase.hxx in any of the expected locations"
    exit 1
}

$env:INCLUDE = "$opencascadeInclude;$env:INCLUDE"
if (-not (Test-Path $mathHeader)) {
    Write-Error "Required OpenCASCADE header 'math_VectorBase.hxx' not found at $mathHeader"
    exit 1
}

Write-Host "OpenCASCADE headers found at: $opencascadeInclude"

cmake .. -G "Visual Studio 17 2022" -A x64 `
    -DCMAKE_BUILD_TYPE=Release `
    -DCMAKE_MSVC_RUNTIME_LIBRARY="MultiThreadedDLL" `
    -DPYTHON_EXECUTABLE="$pythonExe" `
    -DPYTHON_INCLUDE_DIR="$pythonInclude" `
    -DPYTHON_LIBRARY="$pythonLibs\python310.lib" `
    -DOpenCASCADE_DIR="$condaPrefix\lib\cmake\opencascade" `
    -DSWIG_EXECUTABLE="$swigExe" `
    -DSWIG_DIR="$swigDir" `
    -DSWIG_LIB="$swigLibDir" `
    -DSWIG_VERSION="4.2.1" `
    -DCMAKE_PREFIX_PATH="C:\Users\Leinad\miniconda3\envs\pythonocc-env\Library" `
    -DCMAKE_INSTALL_PREFIX="C:\Users\Leinad\miniconda3\envs\pythonocc-env\Lib\site-packages" `
    -DCMAKE_INCLUDE_PATH="$opencascadeInclude" `
    -DINCLUDE_DIRECTORIES="$opencascadeInclude"

Write-Host "Building with Visual Studio..."
cmake --build . --config Release
