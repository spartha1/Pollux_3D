<?php

require_once 'vendor/autoload.php';

use App\Models\FileUpload;
use Illuminate\Support\Facades\App;

$app = require_once 'bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

$file = FileUpload::where('filename_original', 'LIKE', '%RollerAxleHolder%')->latest()->first();

if ($file) {
    echo "ID: " . $file->id . "\n";
    echo "Archivo: " . $file->filename_original . "\n";
    echo "Status: " . $file->status . "\n";
    echo "Extension: " . $file->extension . "\n";
    
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
    echo "❌ No se encontró archivo RollerAxleHolder.\n";
}
