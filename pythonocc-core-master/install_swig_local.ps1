# Use current directory instead of user documents
$scriptDir = $PSScriptRoot
$swigDir = Join-Path $scriptDir "swig-4.2.1"
$swigZip = Join-Path $scriptDir "swig-4.2.1.zip"
$envFile = Join-Path $scriptDir "swig-env.txt"

Write-Output "Paths:"
Write-Output "SWIG dir: $swigDir"
Write-Output "SWIG zip: $swigZip"
Write-Output "Env file: $envFile"

# Remove existing SWIG
Write-Output "`nRemoving existing SWIG..."
conda remove -y swig
conda clean -a -y

# Create directory if it doesn't exist
if (-not (Test-Path $swigDir)) {
    New-Item -ItemType Directory -Path $swigDir -Force | Out-Null
}

# Download SWIG 4.2.1
Write-Output "`nDownloading SWIG 4.2.1..."
$swigUrl = "https://downloads.sourceforge.net/project/swig/swigwin/swigwin-4.2.1/swigwin-4.2.1.zip"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $swigUrl -OutFile $swigZip

Write-Output "Extracting SWIG..."
if (Test-Path $swigDir) {
    Remove-Item -Path $swigDir -Recurse -Force
}
Expand-Archive -Path $swigZip -DestinationPath $scriptDir -Force

# Rename the extracted directory if needed
$extractedDir = Join-Path $scriptDir "swigwin-4.2.1"
if (Test-Path $extractedDir) {
    if (Test-Path $swigDir) {
        Remove-Item -Path $swigDir -Recurse -Force
    }
    Move-Item -Path $extractedDir -Destination $swigDir -Force
}

# Set environment variables
$env:SWIG_EXECUTABLE = Join-Path $swigDir "swig.exe"
$env:SWIG_DIR = $swigDir
$env:SWIG_LIB = $swigDir
$env:PATH = "$swigDir;$env:PATH"

Write-Output "`nSWIG installation:"
Write-Output "Executable: $env:SWIG_EXECUTABLE"
Write-Output "Directory: $env:SWIG_DIR"
Write-Output "Library: $env:SWIG_LIB"

# Test SWIG
Write-Output "`nTesting SWIG:"
if (Test-Path $env:SWIG_EXECUTABLE) {
    & $env:SWIG_EXECUTABLE -version
} else {
    Write-Output "ERROR: SWIG executable not found at $env:SWIG_EXECUTABLE"
    exit 1
}

# Write environment variables to a file for CMake
$envContent = @"
SWIG_EXECUTABLE=$($env:SWIG_EXECUTABLE.Replace('\','\\'))
SWIG_DIR=$($env:SWIG_DIR.Replace('\','\\'))
SWIG_LIB=$($env:SWIG_LIB.Replace('\','\\'))
"@
$envContent | Out-File -FilePath $envFile -Force

Write-Output "`nEnvironment variables written to: $envFile"

# Clean up zip file
if (Test-Path $swigZip) {
    Remove-Item -Path $swigZip -Force
}

# Update the rebuild script paths
$rebuildScript = Join-Path $scriptDir "rebuild_occ.ps1"
if (Test-Path $rebuildScript) {
    Write-Output "`nUpdating rebuild script..."
    # Read the file content
    $content = Get-Content $rebuildScript -Raw

    # Replace the CMake configuration section
    $content = $content -replace '(?s)(# Configure with CMake.+?)(\$cmakeArgs = @\()', @"
# Configure with CMake
Write-Host "`nConfiguring with CMake..."
`$env:SWIG_EXECUTABLE = '$($env:SWIG_EXECUTABLE.Replace('\','\\'))'
`$env:SWIG_DIR = '$($env:SWIG_DIR.Replace('\','\\'))'
`$env:SWIG_LIB = '$($env:SWIG_LIB.Replace('\','\\'))'
`$env:PATH = '$($swigDir.Replace('\','\\'));' + `$env:PATH

`$2
"@

    # Save the updated content
    $content | Set-Content $rebuildScript -Force
}
