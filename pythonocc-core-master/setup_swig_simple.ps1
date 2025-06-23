# Simple SWIG setup script
$ErrorActionPreference = "Stop"
$scriptDir = $PSScriptRoot
$swigDir = Join-Path $scriptDir "swig-4.2.1"
$swigZip = Join-Path $scriptDir "swigwin.zip"

Write-Host "Setting up SWIG 4.2.1..."
Write-Host "Directory: $scriptDir"

# Download SWIG
Write-Host "`nDownloading SWIG..."
$url = "https://downloads.sourceforge.net/project/swig/swigwin/swigwin-4.2.1/swigwin-4.2.1.zip"
$webClient = New-Object System.Net.WebClient
$webClient.DownloadFile($url, $swigZip)

# Create temp directory
$tempDir = Join-Path $scriptDir "temp_swig"
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Extract using PowerShell
Write-Host "`nExtracting SWIG..."
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($swigZip, $tempDir)

# Move to final location
$extractedDir = (Get-ChildItem -Path $tempDir -Directory | Where-Object { $_.Name -like "*swig*" }).FullName
if (Test-Path $swigDir) {
    Remove-Item -Path $swigDir -Recurse -Force
}
Move-Item -Path $extractedDir -Destination $swigDir

# Clean up
Remove-Item -Path $swigZip -Force
Remove-Item -Path $tempDir -Recurse -Force

# Test SWIG
$swigExe = Join-Path $swigDir "swig.exe"
Write-Host "`nTesting SWIG at $swigExe"
if (Test-Path $swigExe) {
    & $swigExe -version
} else {
    Write-Host "ERROR: SWIG not found"
    exit 1
}

Write-Host "`nSetting environment variables..."
$env:SWIG_EXECUTABLE = $swigExe
$env:SWIG_DIR = $swigDir
$env:SWIG_LIB = $swigDir

Write-Host "SWIG setup complete"
