# Simple SWIG installation script using 7-Zip
$ErrorActionPreference = "Stop"

# Use current directory
$scriptDir = $PSScriptRoot
$swigDir = Join-Path $scriptDir "swig-4.2.1"
$swigZip = Join-Path $scriptDir "swig-4.2.1.zip"

Write-Output "Installing SWIG 4.2.1..."
Write-Output "Script directory: $scriptDir"

# Download SWIG if needed
if (-not (Test-Path $swigZip)) {
    Write-Output "Downloading SWIG..."
    $swigUrl = "https://downloads.sourceforge.net/project/swig/swigwin/swigwin-4.2.1/swigwin-4.2.1.zip"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $swigUrl -OutFile $swigZip
    Write-Output "Download complete"
}

# Extract using PowerShell commands
Write-Output "Extracting SWIG..."
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($swigZip, $scriptDir, $true)

    # Rename directory
    $extractedDir = Join-Path $scriptDir "swigwin-4.2.1"
    if (Test-Path $extractedDir) {
        if (Test-Path $swigDir) {
            Remove-Item -Path $swigDir -Recurse -Force
        }
        Move-Item -Path $extractedDir -Destination $swigDir -Force
    }
} catch {
    Write-Output "Error extracting: $_"
    exit 1
}

# Verify installation
$swigExe = Join-Path $swigDir "swig.exe"
if (-not (Test-Path $swigExe)) {
    Write-Output "ERROR: SWIG executable not found at $swigExe"
    exit 1
}

Write-Output "`nTesting SWIG..."
& $swigExe -version

# Set environment variables
$env:SWIG_EXECUTABLE = $swigExe
$env:SWIG_DIR = $swigDir
$env:SWIG_LIB = $swigDir
$env:PATH = "$swigDir;$env:PATH"

Write-Output "`nSWIG environment:"
Write-Output "SWIG_EXECUTABLE=$env:SWIG_EXECUTABLE"
Write-Output "SWIG_DIR=$env:SWIG_DIR"
Write-Output "SWIG_LIB=$env:SWIG_LIB"

# Clean up
Remove-Item -Path $swigZip -Force

Write-Output "`nSWIG installation complete"
