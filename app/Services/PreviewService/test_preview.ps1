# Configure error handling to stop on any error
$ErrorActionPreference = "Stop"

# Get render type from environment or use default
$renderType = if ($env:RENDER_TYPE) { $env:RENDER_TYPE } else { '3d' }

# Configure request
$body = @{
    file_id = 'test'
    file_path = 'c:/xampp/htdocs/laravel/PolluxwWeb/tests/test.step'
    render_type = $renderType
}

Write-Host "Sending request to server..."
$response = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8088/preview' -ContentType 'application/json' -Body ($body | ConvertTo-Json)

Write-Host "Processing response..."
$base64Data = $response.image_data

# Create Python script with explicit UTF-8 encoding for reliable base64 handling
$pythonScript = @"
import base64
import io
from PIL import Image
import sys

try:
    # Use UTF-8 encoding for base64 data
    base64_data = '''$base64Data'''.encode('utf-8').decode('utf-8').strip()

    render_type = '''$($body.render_type)'''
    output_file = f'preview_test_{render_type}.png'
    
    image_data = base64.b64decode(base64_data)
    image = Image.open(io.BytesIO(image_data))
    image.save(output_file)
    print(f'Image saved as {output_file}')
    image.show()
except Exception as e:
    print(f'Error: {str(e)}', file=sys.stderr)
    sys.exit(1)
"@

# Get the current script directory for reliable file paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$processImagePath = Join-Path $scriptDir "process_image.py"

# Write the Python script with UTF-8 encoding
[System.IO.File]::WriteAllText($processImagePath, $pythonScript, [System.Text.Encoding]::UTF8)

Write-Host "Generating preview..."
python $processImagePath
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to process image"
    exit 1
}

Write-Host "Cleaning up..."
Remove-Item $processImagePath -ErrorAction SilentlyContinue

Write-Host "Process completed!"
