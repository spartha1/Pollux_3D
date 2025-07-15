<?php
require_once __DIR__ . '/vendor/autoload.php';

use Illuminate\Support\Facades\Storage;
use App\Models\FileUpload;
use App\Models\FilePreview;

// Configurar Laravel
$app = require_once __DIR__ . '/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

echo "🚀 Generando TODOS los tipos de preview para archivo 27...\n";

// Buscar el archivo
$file = FileUpload::find(27);
if (!$file) {
    echo "❌ No se encontró el archivo con ID 27\n";
    exit(1);
}

echo "📁 Archivo: " . $file->filename_original . "\n";

// Tipos de preview a generar
$previewTypes = [
    '2d' => 'Vista CAD Técnica 2D',
    '3d' => 'Vista 3D',
    'wireframe' => 'Vista Wireframe',
    'both' => 'Vista 2D + 3D'
];

foreach ($previewTypes as $type => $description) {
    echo "\n🔄 Generando $description...\n";
    
    $postData = json_encode([
        'file_path' => $file->filename_stored,
        'preview_type' => $type,
        'width' => 1600,
        'height' => 1200,
        'format' => 'png'
    ]);
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, 'http://localhost:8051/generate-preview');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($postData)
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode !== 200) {
        echo "❌ Error en $description: HTTP $httpCode\n";
        continue;
    }
    
    $data = json_decode($response, true);
    if (!$data || !$data['success']) {
        echo "❌ Error en $description: Respuesta inválida\n";
        continue;
    }
    
    // Guardar preview_2d si existe
    if (isset($data['preview_2d']) && $data['preview_2d']) {
        $imageData = base64_decode($data['preview_2d']);
        $filename = 'preview_2d_' . $type . '_' . time() . '.png';
        $imagePath = 'public/previews/' . $file->id . '/' . $filename;
        
        if (!Storage::exists('public/previews/' . $file->id)) {
            Storage::makeDirectory('public/previews/' . $file->id);
        }
        
        Storage::put($imagePath, $imageData);
        echo "✅ Vista 2D guardada: " . strlen($data['preview_2d']) . " bytes\n";
    }
    
    // Guardar preview_3d si existe
    if (isset($data['preview_3d']) && $data['preview_3d']) {
        $imageData = base64_decode($data['preview_3d']);
        $filename = 'preview_3d_' . $type . '_' . time() . '.png';
        $imagePath = 'public/previews/' . $file->id . '/' . $filename;
        
        Storage::put($imagePath, $imageData);
        echo "✅ Vista 3D guardada: " . strlen($data['preview_3d']) . " bytes\n";
    }
}

echo "\n🎉 Proceso completado - Todas las vistas han sido generadas!\n";
?>
