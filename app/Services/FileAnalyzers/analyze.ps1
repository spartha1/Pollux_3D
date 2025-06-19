# Create timestamp for log file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logFile = Join-Path $scriptDir "analyze_script_$timestamp.log"
$tempJson = Join-Path $env:TEMP "analysis_output_$timestamp.json"

# Start logging
Start-Transcript -Path $logFile -Append

try {
    Write-Output "Starting analysis process..."

    # Get input file path
    $inputFile = $args[0]
    if (-not $inputFile) {
        throw "No input file specified"
    }

    Write-Output "Input file: $inputFile"
    Write-Output "Working directory: $PWD"

    # Find conda in common locations
    $condaLocations = @(
        "C:\Users\Leinad\miniconda3\Scripts\conda.exe",
        "C:\Users\Leinad\miniconda3\condabin\conda.bat"
    )

    $condaPath = $null
    foreach ($loc in $condaLocations) {
        if (Test-Path $loc) {
            $condaPath = $loc
            $condaRoot = Split-Path -Parent (Split-Path -Parent $loc)
            break
        }
    }

    if (-not $condaPath) {
        throw "Conda not found in expected locations"
    }

    Write-Output "Found conda at: $condaPath"

    # Set up clean environment
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONUNBUFFERED = "1"
    $env:PYTHONDONTWRITEBYTECODE = "1"

    # Set up minimal PATH
    $cleanPath = @(
        "$condaRoot\Scripts",
        "$condaRoot\condabin",
        "$condaRoot\Library\bin",
        "C:\Windows\System32",
        "C:\Windows",
        "C:\Windows\System32\Wbem"
    ) -join ";"

    $env:PATH = $cleanPath
    Write-Output "Using PATH: $env:PATH"

    # Run the Python script
    Write-Output "Running Python analysis..."

    $pythonScript = Join-Path $scriptDir "main.py"
    & $condaPath run -n pollux python $pythonScript $inputFile > $tempJson 2>&1

    if ($LASTEXITCODE -ne 0) {
        $error = Get-Content $tempJson
        throw "Python script failed with code $LASTEXITCODE`nError: $error"
    }

    Write-Output "Analysis completed successfully"
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
finally {
    Stop-Transcript
}

# Output only the JSON result
if (Test-Path $tempJson) {
    Get-Content $tempJson
    Remove-Item $tempJson -Force
}
