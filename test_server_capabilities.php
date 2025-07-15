<?php
echo "🔍 Probando capacidades del servidor actual...\n";

$postData = json_encode([
    'file_path' => 'c1bc34d4-df6e-4caa-900e-5a0d70b41c3c.STL',
    'preview_type' => 'both',
    'width' => 800,
    'height' => 600,
    'format' => 'png'
]);

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'http://localhost:8051/generate-preview');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

echo "HTTP Code: $httpCode\n";
echo "Response: $response\n";

if ($httpCode === 200) {
    $data = json_decode($response, true);
    if ($data) {
        echo "\n📊 Capacidades detectadas:\n";
        echo "- preview_2d: " . (isset($data['preview_2d']) ? "✅ Sí" : "❌ No") . "\n";
        echo "- preview_3d: " . (isset($data['preview_3d']) ? "✅ Sí" : "❌ No") . "\n";
        echo "- success: " . ($data['success'] ? "✅ Sí" : "❌ No") . "\n";
    }
}
?>
