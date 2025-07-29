<?php

require_once 'vendor/autoload.php';

$app = require_once 'bootstrap/app.php';
$kernel = $app->make('Illuminate\Contracts\Http\Kernel');

use App\Models\FileUpload;

echo "=== PRUEBA DE VISTAS PREVIAS - ARCHIVOS DE MUESTRA ===\n\n";

// Obtener los últimos 4 archivos (que deberían ser nuestros samples)
$sampleFiles = FileUpload::orderBy('id', 'desc')->take(4)->get();

echo "Archivos de muestra encontrados: " . $sampleFiles->count() . "\n\n";

foreach ($sampleFiles as $file) {
    echo "═══════════════════════════════════════════════════════\n";
    echo "ID: {$file->id} | {$file->filename_original}\n";
    echo "UUID: {$file->uuid}\n";
    echo "Extensión: {$file->extension}\n";
    echo "Path: {$file->path}\n";
    echo "Status: {$file->status}\n";
    
    // Verificar archivo físico
    $fullPath = storage_path('app/' . $file->path);
    $exists = file_exists($fullPath);
    echo "Archivo físico: " . ($exists ? "✓ Existe" : "✗ No existe") . "\n";
    
    if ($exists) {
        echo "Tamaño: " . number_format(filesize($fullPath)) . " bytes\n";
    }
    
    // URLs de preview disponibles
    echo "\n🔍 URLs de Vista Previa:\n";
    echo "2D:        http://127.0.0.1:8088/3d/{$file->id}/preview?type=2d\n";
    echo "Wireframe: http://127.0.0.1:8088/3d/{$file->id}/preview?type=wireframe\n";
    echo "3D:        http://127.0.0.1:8088/3d/{$file->id}/preview?type=3d\n";
    
    // Análisis
    $analysis = $file->analysisResults->first();
    if ($analysis) {
        echo "\n📊 Análisis disponible: ✓ ({$analysis->analyzer_type})\n";
        if ($analysis->dimensions) {
            $dims = $analysis->dimensions;
            echo "Dimensiones: {$dims['width']} x {$dims['height']} x {$dims['depth']}\n";
        }
        if ($analysis->volume) {
            echo "Volumen: {$analysis->volume}\n";
        }
        if ($analysis->area) {
            echo "Área: {$analysis->area}\n";
        }
    } else {
        echo "\n📊 Análisis: ✗ No disponible\n";
    }
    
    echo "\n";
}

echo "═══════════════════════════════════════════════════════\n";
echo "🚀 Para probar las vistas previas:\n";
echo "1. Visita: http://127.0.0.1:8088\n";
echo "2. Ve a la lista de archivos\n";
echo "3. Haz clic en los botones de vista previa\n";
echo "4. O usa las URLs directas mostradas arriba\n\n";

echo "🔧 Servidor de Python ejecutándose en: http://127.0.0.1:8052\n";
echo "📁 Archivos almacenados en: storage/app/models/\n";
