# First, run this script from a clean PowerShell session
# Initialize Visual Studio environment
& "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64

# Activate conda base environment and install required tools
& $env:USERPROFILE\AppData\Local\miniconda3\Scripts\activate.bat
conda install -y -n base cmake ninja
conda activate pyoccenv

# Create and move to build directory
$buildDir = "c:\xampp\htdocs\laravel\PolluxwWeb\pythonocc-core-master\build"
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir
}
Set-Location $buildDir

# Run CMake configuration
cmake .. -G "Ninja" -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE="$env:USERPROFILE\AppData\Local\miniconda3\envs\pyoccenv\python.exe"

# If CMake succeeds, run Ninja
if ($LASTEXITCODE -eq 0) {
    ninja
}
