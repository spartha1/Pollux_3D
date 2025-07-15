<?php
// Test preview generation
require __DIR__ . '/vendor/autoload.php';

use Illuminate\Support\Facades\Http;

// Test the preview service directly
$payload = [
    'file_path' => 'C:/xampp/htdocs/laravel/Pollux_3D/storage/app/models/1/0c200c23-4c21-4883-a256-add3b7e61b39.STL',
    'preview_type' => '2d',
    'width' => 800,
    'height' => 600,
    'format' => 'png'
];

echo "Testing preview service...\n";

try {
    $response = Http::timeout(30)->post('http://127.0.0.1:8051/generate-preview', $payload);
    
    if ($response->successful()) {
        $data = $response->json();
        echo "✓ Preview generated successfully!\n";
        echo "File: " . $data['file_info']['filename'] . "\n";
        echo "Size: " . $data['file_info']['size'] . " bytes\n";
        echo "Image data length: " . strlen($data['preview_2d']) . " characters\n";
        echo "Success: " . ($data['success'] ? 'true' : 'false') . "\n";
    } else {
        echo "✗ Preview service error: " . $response->body() . "\n";
    }
} catch (Exception $e) {
    echo "✗ Exception: " . $e->getMessage() . "\n";
}
