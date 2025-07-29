<?php

require_once 'vendor/autoload.php';

use Illuminate\Support\Facades\Storage;
use Illuminate\Http\Client\Factory as Http;

// Bootstrap Laravel
$app = require_once 'bootstrap/app.php';
$app->make('Illuminate\Contracts\Console\Kernel')->bootstrap();

echo "=== Testing Laravel Controller Logic ===\n";

$fileId = 57; // VaccumBox _ 2.STL
$renderType = '2d';

echo "File ID: $fileId\n";
echo "Render Type: $renderType\n";

// Simulate the controller logic
echo "\n1. Testing preview service call...\n";

$previewServiceUrl = 'http://127.0.0.1:8052';
$filePath = 'C:\xampp\htdocs\laravel\Pollux_3D\c1bc34d4-df6e-4caa-900e-5a0d70b41c3c.STL';

$payload = [
    'file_path' => $filePath,
    'preview_type' => $renderType,
    'width' => 800,
    'height' => 600,
    'background_color' => '#FFFFFF',
    'file_type' => 'stl'
];

$response = \Illuminate\Support\Facades\Http::timeout(120)
    ->withHeaders([
        'Content-Type' => 'application/json',
        'Accept' => 'application/json'
    ])
    ->post($previewServiceUrl . '/generate_preview', $payload);

echo "Response Status: " . $response->status() . "\n";

if ($response->successful()) {
    $data = $response->json();
    echo "Response Keys: " . implode(', ', array_keys($data)) . "\n";
    
    $imageData = $data['image_data'] ?? null;
    echo "Image Data Exists: " . ($imageData ? 'YES' : 'NO') . "\n";
    echo "Image Data Length: " . ($imageData ? strlen($imageData) : 0) . " bytes\n";
    
    if ($imageData) {
        // Test Laravel Storage logic
        echo "\n2. Testing Laravel Storage logic...\n";
        
        // Generate filename like controller does
        if ($renderType === '2d') {
            $filename = 'stl_2d_preview_' . substr(md5($fileId . time()), 0, 8) . '.png';
        } elseif ($renderType === 'wireframe') {
            $filename = 'stl_wireframe_preview_' . substr(md5($fileId . time()), 0, 8) . '.png';
        } else {
            $filename = 'stl_' . $renderType . '_preview_' . substr(md5($fileId . time()), 0, 8) . '.png';
        }
        
        echo "Generated filename: $filename\n";
        
        // Save in the correct directory structure: storage/app/previews/
        $previewPath = 'previews/' . $filename;
        echo "Local storage path: $previewPath\n";
        
        try {
            $saved = Storage::disk('local')->put($previewPath, base64_decode($imageData));
            echo "Local storage save: " . ($saved ? 'SUCCESS' : 'FAILED') . "\n";
        } catch (Exception $e) {
            echo "Local storage error: " . $e->getMessage() . "\n";
        }
        
        // Create symlink path for public access: public/storage/previews/{id}/{filename}
        $publicPreviewPath = 'previews/' . $fileId . '/' . $filename;
        echo "Public storage path: $publicPreviewPath\n";
        
        // Ensure the public directory exists
        try {
            if (!Storage::disk('public')->exists('previews/' . $fileId)) {
                $dirCreated = Storage::disk('public')->makeDirectory('previews/' . $fileId);
                echo "Directory creation: " . ($dirCreated ? 'SUCCESS' : 'FAILED') . "\n";
            } else {
                echo "Directory already exists\n";
            }
        } catch (Exception $e) {
            echo "Directory creation error: " . $e->getMessage() . "\n";
        }
        
        // Copy to public storage for web access
        try {
            $publicSaved = Storage::disk('public')->put($publicPreviewPath, base64_decode($imageData));
            echo "Public storage save: " . ($publicSaved ? 'SUCCESS' : 'FAILED') . "\n";
            
            if ($publicSaved) {
                $fullPath = storage_path('app/public/' . $publicPreviewPath);
                echo "Full file path: $fullPath\n";
                echo "File exists: " . (file_exists($fullPath) ? 'YES' : 'NO') . "\n";
                if (file_exists($fullPath)) {
                    echo "File size: " . filesize($fullPath) . " bytes\n";
                }
            }
            
        } catch (Exception $e) {
            echo "Public storage error: " . $e->getMessage() . "\n";
        }
        
    } else {
        echo "❌ No image_data in response\n";
    }
    
} else {
    echo "❌ Preview service request failed\n";
    echo "Status: " . $response->status() . "\n";
    echo "Body: " . $response->body() . "\n";
}

echo "\n=== Test Complete ===\n";
