function Initialize-Conda {
    # Buscar la ubicación de Conda en las rutas comunes
    $possibleCondaPaths = @(
        "C:\ProgramData\miniconda3",
        "C:\ProgramData\Anaconda3",
        "$env:USERPROFILE\miniconda3",
        "$env:USERPROFILE\Anaconda3"
    )

    $condaPath = $null
    foreach ($path in $possibleCondaPaths) {
        if (Test-Path $path) {
            $condaPath = $path
            break
        }
    }

    if ($condaPath) {
        Write-Host "Found Conda installation at: $condaPath" -ForegroundColor Green
        
        # Inicializar Conda para PowerShell
        $initScript = Join-Path $condaPath "shell\condabin\conda-hook.ps1"
        if (Test-Path $initScript) {
            . $initScript
        }
        
        # Agregar Conda al PATH
        $env:PATH = "$condaPath;$condaPath\Scripts;$condaPath\Library\bin;$env:PATH"
        
        return $true
    } else {
        Write-Host "Error: Could not find Conda installation" -ForegroundColor Red
        return $false
    }
}

# Inicializar Conda
Initialize-Conda
