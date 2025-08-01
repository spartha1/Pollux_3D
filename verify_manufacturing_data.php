<?php

require_once __DIR__ . '/vendor/autoload.php';

// Configurar Laravel
$app = require_once __DIR__ . '/bootstrap/app.php';
$app->make('Illuminate\Contracts\Console\Kernel')->bootstrap();

use App\Models\FileUpload;

echo "🔍 VERIFICACIÓN DE DATOS DE MANUFACTURA\n";
echo "=======================================\n";

$fileId = 20;
$fileUpload = FileUpload::with('analysisResult')->find($fileId);

if (!$fileUpload) {
    echo "❌ Archivo no encontrado\n";
    exit(1);
}

echo "📁 Archivo: {$fileUpload->filename_original}\n";
echo "🆔 ID: {$fileUpload->id}\n";
echo "📊 Estado: {$fileUpload->status}\n\n";

if ($fileUpload->analysisResult) {
    $analysisData = $fileUpload->analysisResult->analysis_data;
    
    echo "✅ Análisis encontrado\n";
    echo "🔧 Claves disponibles: " . implode(', ', array_keys($analysisData)) . "\n\n";
    
    if (isset($analysisData['manufacturing'])) {
        echo "🏭 ¡DATOS DE MANUFACTURA ENCONTRADOS!\n";
        
        $manufacturing = $analysisData['manufacturing'];
        echo "🔧 Claves de manufactura: " . implode(', ', array_keys($manufacturing)) . "\n";
        
        if (isset($manufacturing['weight_estimates'])) {
            $materials = array_keys($manufacturing['weight_estimates']);
            echo "⚖️ Materiales disponibles (" . count($materials) . "):\n";
            
            foreach ($materials as $material) {
                $data = $manufacturing['weight_estimates'][$material];
                echo "   • {$data['name']} ({$data['type']}): {$data['weight_grams']}g\n";
            }
            
            if (count($materials) >= 11) {
                echo "\n🎉 ¡PERFECTO! Los 11 materiales están almacenados en la base de datos\n";
                echo "✅ El frontend debería mostrar todos los datos de manufactura\n";
            } else {
                echo "\n⚠️ Solo " . count($materials) . " materiales encontrados\n";
            }
        } else {
            echo "❌ No se encontraron weight_estimates\n";
        }
        
        // Mostrar otros datos de manufactura
        echo "\n📈 Otros datos de manufactura:\n";
        echo "   • Perímetros de corte: " . ($manufacturing['cutting_perimeters'] ?? 'N/A') . "\n";
        echo "   • Longitud de corte: " . ($manufacturing['cutting_length_mm'] ?? 'N/A') . " mm\n";
        echo "   • Hoyos detectados: " . ($manufacturing['holes_detected'] ?? 'N/A') . "\n";
        echo "   • Eficiencia de material: " . ($manufacturing['material_efficiency'] ?? 'N/A') . "%\n";
        
    } else {
        echo "❌ No se encontraron datos de manufactura\n";
    }
    
} else {
    echo "❌ No se encontró análisis\n";
}

echo "\n=== ESTADO FINAL ===\n";
echo "El archivo ID 20 " . (isset($analysisData['manufacturing']) ? "TIENE" : "NO TIENE") . " datos de manufactura\n";
