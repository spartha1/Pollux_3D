<?php

require_once 'vendor/autoload.php';

use App\Models\FileUpload;
use Illuminate\Support\Facades\App;

$app = require_once 'bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

$file = FileUpload::find(28);

if ($file) {
    echo "ID: " . $file->id . "\n";
    echo "Archivo: " . $file->filename_original . "\n";
    echo "Status: " . $file->status . "\n";
    
    $analysisResult = $file->analysisResult;
    
    if ($analysisResult) {
        echo "Análisis encontrado:\n";
        
        $data = $analysisResult->analysis_data;
        
        if (isset($data['manufacturing'])) {
            echo "✅ Datos de fabricación presentes:\n";
            echo json_encode($data['manufacturing'], JSON_PRETTY_PRINT);
        } else {
            echo "❌ No se encontraron datos de fabricación.\n";
            echo "Datos disponibles:\n";
            echo json_encode(array_keys($data), JSON_PRETTY_PRINT);
        }
    } else {
        echo "❌ No se encontró resultado de análisis.\n";
    }
} else {
    echo "❌ No se encontró archivo con ID 28.\n";
}
