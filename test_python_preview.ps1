# Test directo al servidor Python de previews
$filePath = "C:\xampp\htdocs\laravel\Pollux_3D\storage\app\models\1\96313e44-cb5f-4416-83b5-1473198c2227.STL"
$payload = @{
    file_id = "60"
    file_path = $filePath
    preview_type = "2d"
    width = 800
    height = 600
    background_color = "#FFFFFF"
    file_type = "stl"
} | ConvertTo-Json

Write-Host "Testing Python preview server with payload:"
Write-Host $payload

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8052/generate_preview" -Method POST -Body $payload -ContentType "application/json"
    Write-Host "Success! Response keys:" $response.Keys
    if ($response.image_data) {
        Write-Host "Image data length:" $response.image_data.Length
    } else {
        Write-Host "No image_data in response"
        Write-Host "Full response:" ($response | ConvertTo-Json)
    }
} catch {
    Write-Host "Error:" $_.Exception.Message
    Write-Host "Response:" $_.Exception.Response
}
