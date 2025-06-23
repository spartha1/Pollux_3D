# Get conda environment info
$condaPrefix = $env:CONDA_PREFIX
if (-not $condaPrefix) {
    $condaPrefix = "C:\Users\Leinad\miniconda3"
}

Write-Output "Installing SWIG..."
& conda install -y -c conda-forge "swig=4.2.1" --force-reinstall

$swigPath = Join-Path $condaPrefix "Library\bin\swig.exe"
$swigRoot = Split-Path $swigPath -Parent
$swigShare = Join-Path $condaPrefix "Library\share\swig\4.2.1"

Write-Output "`nPaths:"
Write-Output "SWIG: $swigPath"
Write-Output "Share: $swigShare"

Write-Output "`nVersion:"
& $swigPath -version

Write-Output "`nFiles:"
Test-Path $swigPath
Test-Path $swigShare
