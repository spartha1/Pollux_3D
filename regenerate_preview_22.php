<?php
require_once __DIR__ . '/vendor/autoload.php';

use Illuminate\Support\Facades\Storage;
use App\Models\FileUpload;
use App\Models\FilePreview;

// Configurar Laravel
$app = require_once __DIR__ . '/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

echo "🚀 Regenerando preview para archivo 22...\n";

// Buscar el archivo
$file = FileUpload::find(22);
if (!$file) {
    echo "❌ No se encontró el archivo con ID 22\n";
    exit(1);
}

echo "📁 Archivo encontrado: " . $file->filename_original . "\n";
echo "📍 Ruta: " . $file->storage_path . "\n";

// Verificar que el archivo existe
$fullPath = storage_path('app/' . $file->storage_path);
if (!file_exists($fullPath)) {
    echo "❌ El archivo físico no existe: " . $fullPath . "\n";
    exit(1);
}

// Hacer petición al servidor de preview
$url = 'http://localhost:8051/generate-preview';
echo "🔄 Solicitando preview desde: " . $url . "\n";

$postData = json_encode([
    'file_path' => $file->filename_stored,
    'preview_type' => '2d',
    'width' => 1600,
    'height' => 1200,
    'format' => 'png'
]);

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
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
    echo "❌ Error en la petición HTTP: " . $httpCode . "\n";
    echo "Response: " . $response . "\n";
    exit(1);
}

// Decodificar la respuesta JSON
$data = json_decode($response, true);
if (!$data || !isset($data['preview_2d'])) {
    echo "❌ Respuesta inválida del servidor\n";
    echo "Response: " . $response . "\n";
    exit(1);
}

echo "✅ Preview recibido, tamaño: " . strlen($data['preview_2d']) . " bytes\n";

// Decodificar el base64
$imageData = base64_decode($data['preview_2d']);
if ($imageData === false) {
    echo "❌ Error decodificando base64\n";
    exit(1);
}

// Generar UUID para el archivo
$uuid = uniqid('preview_' . time() . '_');
$filename = $uuid . '.png';

// Crear directorio si no existe
$previewDir = 'public/previews/' . $file->id;
if (!Storage::exists($previewDir)) {
    Storage::makeDirectory($previewDir);
}

// Guardar la imagen
$imagePath = $previewDir . '/' . $filename;
if (!Storage::put($imagePath, $imageData)) {
    echo "❌ Error guardando la imagen\n";
    exit(1);
}

echo "💾 Imagen guardada en: " . $imagePath . "\n";

// Eliminar previews antiguos
FilePreview::where('file_upload_id', $file->id)->delete();

// Crear registro en base de datos
$preview = new FilePreview();
$preview->file_upload_id = $file->id;
$preview->render_type = '2d';
$preview->image_path = $imagePath;
$preview->generated_at = now();
$preview->save();

echo "✅ Preview generado exitosamente!\n";
echo "📊 ID del preview: " . $preview->id . "\n";
