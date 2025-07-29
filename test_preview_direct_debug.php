<?php

require_once 'vendor/autoload.php';

use Illuminate\Http\Client\Factory as Http;
use Illuminate\Support\Facades\Storage;

// Simular la configuración de Laravel
$_ENV['APP_URL'] = 'http://localhost:8088';

echo "=== Testing Preview Generation Debug ===\n";

$fileId = 57; // VaccumBox _ 2.STL
$renderType = '2d';

echo "File ID: $fileId\n";
echo "Render Type: $renderType\n";

// 1. Test preview service directly
echo "\n1. Testing preview service directly...\n";

$previewServiceUrl = 'http://127.0.0.1:8052';
$filePath = 'C:\xampp\htdocs\laravel\Pollux_3D\c1bc34d4-df6e-4caa-900e-5a0d70b41c3c.STL';

$payload = [
    'file_path' => $filePath,
    'preview_type' => $renderType,
    'width' => 800,
    'height' => 600
];

echo "Payload: " . json_encode($payload, JSON_PRETTY_PRINT) . "\n";

$http = new Http();
$response = $http->timeout(120)->post($previewServiceUrl . '/generate-preview', $payload);

echo "Response Status: " . $response->status() . "\n";
echo "Response Headers: " . json_encode($response->headers(), JSON_PRETTY_PRINT) . "\n";

if ($response->successful()) {
    $data = $response->json();
    echo "Response Keys: " . implode(', ', array_keys($data)) . "\n";
    
    if (isset($data['image_data'])) {
        $imageDataLength = strlen($data['image_data']);
        echo "Image Data Length: $imageDataLength bytes\n";
        echo "Image Data Preview (first 100 chars): " . substr($data['image_data'], 0, 100) . "\n";
        
        // Test base64 decoding
        $decodedData = base64_decode($data['image_data']);
        echo "Decoded Data Length: " . strlen($decodedData) . " bytes\n";
        
        // Test saving file
        $testFilename = "test_preview_debug_$renderType.png";
        $testPath = "c:/xampp/htdocs/laravel/Pollux_3D/public/storage/previews/$testFilename";
        
        if (file_put_contents($testPath, $decodedData)) {
            echo "✅ Successfully saved test file: $testPath\n";
            echo "File size: " . filesize($testPath) . " bytes\n";
        } else {
            echo "❌ Failed to save test file: $testPath\n";
        }
        
    } else {
        echo "❌ No image_data in response\n";
        echo "Full Response: " . json_encode($data, JSON_PRETTY_PRINT) . "\n";
    }
} else {
    echo "❌ Preview service request failed\n";
    echo "Response Body: " . $response->body() . "\n";
}

echo "\n=== Test Complete ===\n";
