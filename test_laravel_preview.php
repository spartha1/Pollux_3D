<?php

use Illuminate\Http\Request;

// Simple test to trigger preview generation
$url = 'http://127.0.0.1:8088/3d/1/preview';
$data = ['render_type' => '2d'];

echo "Testing Laravel preview endpoint...\n";
echo "URL: $url\n";
echo "Data: " . json_encode($data) . "\n\n";

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/x-www-form-urlencoded',
    'X-Requested-With: XMLHttpRequest'
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

echo "HTTP Code: $httpCode\n";
echo "Error: $error\n";
echo "Response: $response\n";

if ($response) {
    $decoded = json_decode($response, true);
    if ($decoded) {
        echo "\nDecoded response:\n";
        print_r($decoded);
    }
}
