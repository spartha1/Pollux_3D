# Use user's documents folder instead of C: root
$userDocs = [Environment]::GetFolderPath('MyDocuments')
$swigDir = Join-Path $userDocs "swig-4.2.1"
$swigZip = Join-Path $userDocs "swig-4.2.1.zip"
$envFile = Join-Path $userDocs "swig-env.txt"

# Remove existing SWIG
Write-Output "Removing existing SWIG..."
conda remove -y swig
conda clean -a -y

# Create directory if it doesn't exist
if (-not (Test-Path $swigDir)) {
    New-Item -ItemType Directory -Path $swigDir -Force | Out-Null
}

# Download SWIG 4.2.1
Write-Output "Downloading SWIG 4.2.1..."
$swigUrl = "https://downloads.sourceforge.net/project/swig/swigwin/swigwin-4.2.1/swigwin-4.2.1.zip"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $swigUrl -OutFile $swigZip

Write-Output "Extracting SWIG..."
if (Test-Path $swigDir) {
    Remove-Item -Path $swigDir -Recurse -Force
}
Expand-Archive -Path $swigZip -DestinationPath $userDocs -Force

# Rename the extracted directory if needed
$extractedDir = Join-Path $userDocs "swigwin-4.2.1"
if (Test-Path $extractedDir) {
    Move-Item -Path $extractedDir -Destination $swigDir -Force
}

# Set environment variables
$env:SWIG_EXECUTABLE = Join-Path $swigDir "swig.exe"
$env:SWIG_DIR = $swigDir
$env:SWIG_LIB = $swigDir
$env:PATH = "$swigDir;$env:PATH"

Write-Output "SWIG installation:"
Write-Output "Executable: $env:SWIG_EXECUTABLE"
Write-Output "Directory: $env:SWIG_DIR"
Write-Output "Library: $env:SWIG_LIB"

# Test SWIG
Write-Output "`nTesting SWIG:"
& $env:SWIG_EXECUTABLE -version

# Write environment variables to a file for CMake
@"
SWIG_EXECUTABLE=$env:SWIG_EXECUTABLE
SWIG_DIR=$env:SWIG_DIR
SWIG_LIB=$env:SWIG_LIB
"@ | Out-File -FilePath $envFile

Write-Output "`nEnvironment variables written to: $envFile"

# Clean up zip file
if (Test-Path $swigZip) {
    Remove-Item -Path $swigZip -Force
}

# Update the main rebuild script with these paths
$rebuildScript = Join-Path $PSScriptRoot "rebuild_occ.ps1"
if (Test-Path $rebuildScript) {
    Write-Output "`nUpdating rebuild script with SWIG paths..."
    $content = Get-Content $rebuildScript -Raw
    $content = $content -replace '(?s)(\$swigRoot = .+?)(\r?\n\s*\$cmakeArgs)', @"
# Use manually installed SWIG
`$env:SWIG_EXECUTABLE = '$($env:SWIG_EXECUTABLE.Replace('\','\\'))'
`$env:SWIG_DIR = '$($env:SWIG_DIR.Replace('\','\\'))'
`$env:SWIG_LIB = '$($env:SWIG_LIB.Replace('\','\\'))'
`$env:PATH = '$($swigDir.Replace('\','\\'));$env:PATH'

`$swigRoot = Split-Path `$env:SWIG_EXECUTABLE -Parent
`$swigShare = `$env:SWIG_DIR`$2
"@
    $content | Set-Content $rebuildScript -Force
}
