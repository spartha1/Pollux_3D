# Read SWIG environment from file
$envVars = Get-Content "C:\swig-env.txt" | ConvertFrom-StringData

# Create minimal CMake project
$cmakeScript = @"
cmake_minimum_required(VERSION 3.10)
project(swig_test)

find_package(SWIG 4.2.1 REQUIRED)
message(STATUS "SWIG version: \${SWIG_VERSION}")
message(STATUS "SWIG executable: \${SWIG_EXECUTABLE}")
message(STATUS "SWIG dir: \${SWIG_DIR}")
"@

$testDir = "C:\swig-test"
if (-not (Test-Path $testDir)) {
    New-Item -ItemType Directory -Path $testDir
}

$cmakeScript | Out-File -FilePath "$testDir\CMakeLists.txt"

# Run CMake
Write-Output "Running CMake test..."
Push-Location $testDir
& cmake . `
    -DSWIG_EXECUTABLE="$($envVars.SWIG_EXECUTABLE)" `
    -DSWIG_DIR="$($envVars.SWIG_DIR)" `
    -DSWIG_LIB="$($envVars.SWIG_LIB)"
Pop-Location

Write-Output "`nTest complete"
