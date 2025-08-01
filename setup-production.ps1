# Production Setup Script for Pollux 3D Analysis System (Windows)
# This script configures the Python environment for production deployment

Write-Host "🚀 Setting up Pollux 3D for Production..." -ForegroundColor Green

function Detect-PythonEnv {
    Write-Host "🔍 Detecting Python environment..." -ForegroundColor Yellow
    
    # Check for conda
    try {
        $condaVersion = conda --version 2>$null
        if ($condaVersion) {
            Write-Host "✅ Conda found: $condaVersion" -ForegroundColor Green
            
            # Check if pollux-preview-env exists
            $envList = conda env list 2>$null
            if ($envList -match "pollux-preview-env") {
                Write-Host "✅ pollux-preview-env environment found" -ForegroundColor Green
                
                # Extract environment path
                $envLine = $envList | Select-String "pollux-preview-env"
                $envPath = ($envLine -split '\s+')[1]
                $script:PythonPath = Join-Path $envPath "python.exe"
                
                if (Test-Path $script:PythonPath) {
                    Write-Host "✅ Python executable found: $script:PythonPath" -ForegroundColor Green
                    return $true
                }
            }
            else {
                Write-Host "❌ pollux-preview-env not found. Please create it manually:" -ForegroundColor Red
                Write-Host "conda create -n pollux-preview-env python=3.9" -ForegroundColor Yellow
                Write-Host "conda activate pollux-preview-env" -ForegroundColor Yellow
                Write-Host "pip install -r requirements.txt" -ForegroundColor Yellow
                return $false
            }
        }
    }
    catch {
        Write-Host "⚠️ Conda not found, checking for system Python..." -ForegroundColor Yellow
    }
    
    # Check for system Python
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion) {
            $script:PythonPath = (Get-Command python).Source
            Write-Host "✅ System Python found: $pythonVersion at $script:PythonPath" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "❌ No Python installation found!" -ForegroundColor Red
        return $false
    }
    
    return $false
}

function Setup-EnvFile {
    Write-Host "⚙️ Configuring environment variables..." -ForegroundColor Yellow
    
    if (Test-Path ".env") {
        # Read current .env content
        $envContent = Get-Content ".env"
        
        # Remove old hardcoded paths
        $envContent = $envContent | Where-Object { $_ -notmatch "CONDA_ROOT=C:\\Users\\" }
        $envContent = $envContent | Where-Object { $_ -notmatch "PYTHON_EXECUTABLE.*Users" }
        
        # Add detected Python path if available
        if ($script:PythonPath) {
            $envContent += "PYTHON_EXECUTABLE=$($script:PythonPath -replace '\\', '\\\\')"
            Write-Host "✅ Python path configured: $script:PythonPath" -ForegroundColor Green
        }
        
        # Set production environment
        $envContent = $envContent -replace "APP_ENV=local", "APP_ENV=production"
        $envContent = $envContent -replace "APP_DEBUG=true", "APP_DEBUG=false"
        
        # Write back to file
        $envContent | Set-Content ".env"
        
        Write-Host "✅ Environment file configured for production" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "❌ .env file not found! Please copy .env.example to .env first." -ForegroundColor Red
        return $false
    }
}

function Install-Dependencies {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    
    # PHP dependencies
    try {
        composer install --optimize-autoloader --no-dev --no-interaction
        Write-Host "✅ PHP dependencies installed" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Composer install failed!" -ForegroundColor Red
        return $false
    }
    
    # Python dependencies
    if (Test-Path "requirements.txt" -and $script:PythonPath) {
        try {
            & $script:PythonPath -m pip install -r requirements.txt
            Write-Host "✅ Python dependencies installed" -ForegroundColor Green
        }
        catch {
            Write-Host "⚠️ Python dependencies installation failed" -ForegroundColor Yellow
        }
    }
    
    # Node.js dependencies
    try {
        if (Get-Command npm -ErrorAction SilentlyContinue) {
            npm ci --production
            npm run build
            Write-Host "✅ Frontend built for production" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "⚠️ Frontend build failed" -ForegroundColor Yellow
    }
    
    return $true
}

function Optimize-Laravel {
    Write-Host "⚡ Optimizing Laravel for production..." -ForegroundColor Yellow
    
    try {
        php artisan config:cache
        php artisan route:cache
        php artisan view:cache
        php artisan event:cache
        
        Write-Host "✅ Laravel optimized" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Laravel optimization failed!" -ForegroundColor Red
        return $false
    }
}

function Set-Permissions {
    Write-Host "🔐 Setting proper permissions..." -ForegroundColor Yellow
    
    # Windows doesn't need chmod, but we can check if directories are writable
    $paths = @("storage", "bootstrap\cache")
    
    foreach ($path in $paths) {
        if (Test-Path $path) {
            try {
                # Test write access
                $testFile = Join-Path $path "test_write_$(Get-Random).tmp"
                New-Item -Path $testFile -ItemType File -Force | Out-Null
                Remove-Item $testFile -Force
                Write-Host "✅ $path is writable" -ForegroundColor Green
            }
            catch {
                Write-Host "⚠️ $path may not be writable" -ForegroundColor Yellow
            }
        }
    }
}

# Main execution
function Main {
    if (Detect-PythonEnv) {
        if (Setup-EnvFile -and Install-Dependencies -and Optimize-Laravel) {
            Set-Permissions
            
            Write-Host "🎉 Production setup completed successfully!" -ForegroundColor Green
            Write-Host "📝 Python path: $($script:PythonPath)" -ForegroundColor Cyan
            Write-Host "🚀 Your application is ready for production deployment." -ForegroundColor Green
            
            # Show final configuration
            Write-Host "`n📋 Final Configuration:" -ForegroundColor Cyan
            Write-Host "- Environment: Production" -ForegroundColor Gray
            Write-Host "- Debug: Disabled" -ForegroundColor Gray
            Write-Host "- Python: Auto-detection enabled" -ForegroundColor Gray
            Write-Host "- Caches: Optimized" -ForegroundColor Gray
        }
        else {
            Write-Host "❌ Production setup failed during configuration." -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "❌ Production setup failed due to Python environment issues." -ForegroundColor Red
        Write-Host "Please ensure Python or Conda is properly installed." -ForegroundColor Yellow
        exit 1
    }
}

# Initialize variables
$script:PythonPath = $null

# Run main function
Main
