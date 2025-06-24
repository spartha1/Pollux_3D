# Debug CMake problems
Write-Host "`nRunning CMake with debug output..."

& $cmakePath $cmakeArgs --trace-expand 2>&1 | Tee-Object -Variable cmakeOutput

Write-Host "`nFull CMake output:"
$cmakeOutput | ForEach-Object { Write-Host $_ }
