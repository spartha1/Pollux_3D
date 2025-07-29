<?php

$url = 'http://127.0.0.1:8052/generate_preview';
$data = [
    'file_id' => '1',
    'file_path' => 'models/1/c1bc34d4-df6e-4caa-900e-5a0d70b41c3c.STL',
    'preview_type' => '2d',
    'width' => 800,
    'height' => 600,
    'background_color' => '#FFFFFF',
    'file_type' => 'STL'
];

$payload = json_encode($data);

echo "Testing preview endpoint...\n";
echo "URL: $url\n";
echo "Payload: $payload\n\n";

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'Content-Length: ' . strlen($payload)
]);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);

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
