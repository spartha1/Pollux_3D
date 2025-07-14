# Configuración del entorno
$script:ENV = @{
    # Rutas base
    ProjectRoot = $PSScriptRoot | Split-Path -Parent
    CondaName = "pollux-preview-env"
    PythonVersion = "3.10"
}

function Find-CondaInstallation {
    $possiblePaths = @(
        "$env:USERPROFILE\miniconda3",
        "$env:USERPROFILE\anaconda3",
        "${env:ProgramFiles}\miniconda3",
        "${env:ProgramFiles}\anaconda3",
        "${env:ProgramFiles(x86)}\miniconda3",
        "${env:ProgramFiles(x86)}\anaconda3"
    )

    foreach ($path in $possiblePaths) {
        if (Test-Path "$path\Scripts\conda.exe") {
            return $path
        }
    }
    return $null
}

function Test-CommandAvailable {
    param (
        [string]$Command
    )
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Initialize-Environment {
    $requirements = @(
        @{
            Name = "PHP"
            Test = { Test-CommandAvailable "php" }
            Message = "PHP is required. Please install PHP and add it to your PATH"
            Required = $true
        },
        @{
            Name = "Node.js"
            Test = { Test-CommandAvailable "node" }
            Message = "Node.js is required. Please install Node.js from https://nodejs.org/"
            Required = $true
        },
        @{
            Name = "npm"
            Test = { Test-CommandAvailable "npm" }
            Message = "npm is required. It should be installed with Node.js"
            Required = $true
        },
        @{
            Name = "Composer"
            Test = { Test-CommandAvailable "composer" }
            Message = "Composer is required. Please install from https://getcomposer.org/"
            Required = $true
        }
    )

    $allGood = $true
    Write-Host "`nChecking system requirements..." -ForegroundColor Yellow

    foreach ($req in $requirements) {
        Write-Host "Checking $($req.Name)... " -NoNewline
        if (& $req.Test) {
            Write-Host "✓" -ForegroundColor Green
        } else {
            Write-Host "✗" -ForegroundColor Red
            Write-Host "  $($req.Message)" -ForegroundColor Yellow
            if ($req.Required) {
                $allGood = $false
            }
        }
    }

    # Verificar Conda
    Write-Host "`nChecking Conda installation... " -NoNewline
    $condaBase = Find-CondaInstallation
    if ($condaBase) {
        Write-Host "✓" -ForegroundColor Green
        Write-Host "  Found at: $condaBase"
        $ENV.CondaBase = $condaBase
        $ENV.CondaScripts = "$condaBase\Scripts"
        $ENV.PythonPath = "$condaBase\envs\$($ENV.CondaName)\python.exe"
    } else {
        Write-Host "✗" -ForegroundColor Red
        Write-Host "  Miniconda/Anaconda not found. Please install from https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Yellow
        $allGood = $false
    }

    # Verificar si el entorno Conda existe
    if ($condaBase) {
        Write-Host "`nChecking Conda environment... " -NoNewline
        $envExists = Test-Path "$condaBase\envs\$($ENV.CondaName)"
        if ($envExists) {
            Write-Host "✓" -ForegroundColor Green
            Write-Host "  Environment '$($ENV.CondaName)' found"
        } else {
            Write-Host "✗" -ForegroundColor Red
            Write-Host "  Environment '$($ENV.CondaName)' not found. Please run 'npm run verify:env' to create it" -ForegroundColor Yellow
            $allGood = $false
        }
    }

    if (-not $allGood) {
        Write-Host "`n❌ Some required components are missing. Please install them and try again." -ForegroundColor Red
        exit 1
    }

    Write-Host "`n✅ All system requirements are met!" -ForegroundColor Green
    return $ENV
}

# Exportar funciones y variables
Export-ModuleMember -Function Initialize-Environment
Export-ModuleMember -Variable ENV
