<?php

require_once 'vendor/autoload.php';

use App\Models\FileUpload;
use App\Models\FileError;
use Illuminate\Support\Facades\App;

$app = require_once 'bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

$file = FileUpload::find(31);

if ($file) {
    echo "=== ARCHIVO ID 28 ===\n";
    echo "Archivo: " . $file->filename_original . "\n";
    echo "Status: " . $file->status . "\n";
    echo "Extension: " . $file->extension . "\n";
    echo "Storage path: " . $file->storage_path . "\n";
    
    // Verificar si el archivo físico existe
    $fullPath = storage_path('app/' . $file->storage_path);
    echo "Archivo físico existe: " . (file_exists($fullPath) ? "✅ SÍ" : "❌ NO") . "\n";
    if (file_exists($fullPath)) {
        echo "Tamaño: " . filesize($fullPath) . " bytes\n";
    }
    
    // Verificar errores
    $errors = $file->errors;
    echo "\n=== ERRORES ===\n";
    if ($errors->count() > 0) {
        foreach ($errors as $error) {
            echo "Error: " . $error->error_message . "\n";
            echo "Fecha: " . $error->occurred_at . "\n";
            echo "---\n";
        }
    } else {
        echo "No hay errores registrados.\n";
    }
    
    // Verificar análisis
    $analysisResult = $file->analysisResult;
    echo "\n=== ANÁLISIS ===\n";
    if ($analysisResult) {
        $data = $analysisResult->analysis_data;
        echo "Analizador: " . $analysisResult->analyzer_type . "\n";
        echo "Datos disponibles: " . implode(', ', array_keys($data)) . "\n";
        
        if (isset($data['error'])) {
            echo "Error en análisis: " . $data['error'] . "\n";
        }
    } else {
        echo "No hay resultado de análisis.\n";
    }
} else {
    echo "❌ No se encontró archivo con ID 28.\n";
}
