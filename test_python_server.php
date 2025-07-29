<?php

echo "=== PRUEBA DIRECTA DEL SERVIDOR DE PYTHON ===\n\n";

// Datos para la prueba
$testData = [
    'file_path' => 'C:\xampp\htdocs\laravel\Pollux_3D\storage\app\models\1\514e7da0-19e0-430f-8cf6-fce36535178b.stl',
    'preview_type' => '2d',
    'width' => 800,
    'height' => 600
];

$url = 'http://127.0.0.1:8052/generate-preview';

echo "🔍 URL: $url\n";
echo "📝 Datos enviados:\n";
print_r($testData);

// Crear contexto HTTP
$context = stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' => 'Content-Type: application/json',
        'content' => json_encode($testData)
    ]
]);

echo "\n🚀 Enviando solicitud...\n";

// Realizar solicitud
$result = file_get_contents($url, false, $context);

if ($result === false) {
    echo "❌ Error: No se pudo conectar al servidor de Python\n";
    echo "Verificar que el servidor esté ejecutándose en puerto 8052\n";
} else {
    echo "✅ Respuesta recibida:\n";
    echo $result . "\n";
    
    // Intentar decodificar JSON
    $response = json_decode($result, true);
    if ($response) {
        echo "\n📊 Respuesta decodificada:\n";
        print_r($response);
        
        if (isset($response['preview_path'])) {
            echo "\n🖼️ Imagen generada en: " . $response['preview_path'] . "\n";
            
            // Verificar si el archivo existe
            $fullPath = $response['preview_path'];
            if (file_exists($fullPath)) {
                echo "✅ Archivo de imagen existe\n";
                echo "📏 Tamaño: " . number_format(filesize($fullPath)) . " bytes\n";
            } else {
                echo "❌ Archivo de imagen no encontrado\n";
            }
        }
    }
}

echo "\n" . str_repeat("=", 50) . "\n";
