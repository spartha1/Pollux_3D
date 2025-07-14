Write-Host "Verifying all services..." -ForegroundColor Yellow

# Función para verificar si un puerto está en uso
function Test-Port {
    param($port)
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("localhost", $port)
        $tcp.Close()
        return $true
    } catch {
        return $false
    }
}

# Función para verificar si un proceso está corriendo
function Test-Process {
    param($name, $args = $null)
    $processes = Get-Process -Name $name -ErrorAction SilentlyContinue
    if ($args) {
        return ($processes | Where-Object { $_.CommandLine -like "*$args*" }).Count -gt 0
    }
    return $processes.Count -gt 0
}

# Cargar configuración del entorno
$configScript = Join-Path $PSScriptRoot "config\environment.ps1"
if (-not (Test-Path $configScript)) {
    Write-Host "Error: environment.ps1 not found at: $configScript" -ForegroundColor Red
    exit 1
}

Write-Host "`nInitializing environment..." -ForegroundColor Cyan
$env = . $configScript
Initialize-Environment

# Verificar servicios uno por uno
$errors = 0

# 1. Verificar Laravel (puerto 8088)
Write-Host "`nVerifying Laravel server (port 8088)..." -ForegroundColor Cyan
if (Test-Port 8088) {
    Write-Host "✓ Laravel server is running" -ForegroundColor Green
} else {
    Write-Host "✗ Laravel server is not running" -ForegroundColor Red
    $errors++
}

# 2. Verificar Vite dev server
Write-Host "`nVerifying Vite dev server..." -ForegroundColor Cyan
if (Test-Process "node" "vite") {
    Write-Host "✓ Vite dev server is running" -ForegroundColor Green
} else {
    Write-Host "✗ Vite dev server is not running" -ForegroundColor Red
    $errors++
}

# 3. Verificar Laravel Queue Worker
Write-Host "`nVerifying Laravel Queue Worker..." -ForegroundColor Cyan
if (Test-Process "php" "artisan queue:listen") {
    Write-Host "✓ Laravel Queue Worker is running" -ForegroundColor Green
} else {
    Write-Host "✗ Laravel Queue Worker is not running" -ForegroundColor Red
    $errors++
}

# 4. Verificar Preview Service (Python)
Write-Host "`nVerifying Preview Service..." -ForegroundColor Cyan
if (Test-Process "python" "simple_preview_server.py") {
    Write-Host "✓ Preview Service is running" -ForegroundColor Green
} else {
    Write-Host "✗ Preview Service is not running" -ForegroundColor Red
    $errors++
}

# Resumen
Write-Host "`n=== Service Check Summary ===" -ForegroundColor Yellow
if ($errors -eq 0) {
    Write-Host "All services are running correctly!" -ForegroundColor Green
    Write-Host "`nYou can access:" -ForegroundColor Cyan
    Write-Host "- Laravel app: http://localhost:8088" -ForegroundColor White
    Write-Host "- Vite dev server: http://localhost:5173" -ForegroundColor White
} else {
    Write-Host "Some services are not running ($errors issues found)" -ForegroundColor Red
    Write-Host "`nTo start all services, run:" -ForegroundColor Yellow
    Write-Host "npm run dev:all" -ForegroundColor White
}
