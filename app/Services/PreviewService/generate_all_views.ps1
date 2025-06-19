#!/usr/bin/env pwsh
# Configure error handling to stop on any error
$ErrorActionPreference = "Stop"

$viewTypes = @("2d", "wireframe", "3d")
$results = @()

foreach ($viewType in $viewTypes) {
    Write-Host "`n=== Generating $viewType view ===" -ForegroundColor Cyan
    $env:RENDER_TYPE = $viewType
    
    try {
        & .\test_preview.ps1
        $results += @{
            type = $viewType
            status = "Success"
            file = "preview_test_$viewType.png"
        }
    }
    catch {
        $results += @{
            type = $viewType
            status = "Failed"
            error = $_.Exception.Message
        }
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor Yellow
foreach ($result in $results) {
    $status = if ($result.status -eq "Success") { "[OK]" } else { "[FAILED]" }
    $color = if ($result.status -eq "Success") { "Green" } else { "Red" }
    Write-Host "$status $($result.type): $($result.status)" -ForegroundColor $color
    if ($result.status -eq "Failed") {
        Write-Host "  Error: $($result.error)" -ForegroundColor Red
    }
    else {
        Write-Host "  File: $($result.file)" -ForegroundColor Gray
    }
}
}
