<?php

require_once 'vendor/autoload.php';

use App\Models\FileUpload;
use Illuminate\Support\Facades\App;

$app = require_once 'bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

$fileUpload = FileUpload::find(1);

if ($fileUpload) {
    echo "Archivo: " . $fileUpload->filename_original . "\n";
    
    $analysisResult = $fileUpload->analysisResult;
    
    if ($analysisResult) {
        echo "Análisis encontrado:\n";
        
        $data = $analysisResult->analysis_data;
        
        echo "Datos completos:\n";
        echo json_encode($data, JSON_PRETTY_PRINT);
        
        if (isset($data['manufacturing'])) {
            echo "\n\nDatos de fabricación:\n";
            echo json_encode($data['manufacturing'], JSON_PRETTY_PRINT);
        } else {
            echo "\n\nNo se encontraron datos de fabricación.\n";
        }
    } else {
        echo "No se encontró resultado de análisis.\n";
    }
} else {
    echo "No se encontró archivo con ID 1.\n";
}
