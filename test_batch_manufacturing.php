<?php

require_once __DIR__ . '/vendor/autoload.php';

use App\Models\FileUpload;

// Prueba del analizador de manufactura con script batch
$fileId = 19; // ID del archivo que subiste
$fileUpload = FileUpload::find($fileId);

if (!$fileUpload) {
    echo "❌ Archivo no encontrado\n";
    exit(1);
}

echo "🧪 PRUEBA DEL SCRIPT BATCH MANUFACTURING ANALYZER\n";
echo "================================\n";
echo "Archivo: {$fileUpload->filename_original}\n";
echo "ID: {$fileUpload->id}\n";
echo "Ruta: {$fileUpload->storage_path}\n\n";

// Simular el proceso que usará el frontend
$batchScript = __DIR__ . '/run_manufacturing_analyzer.bat';
$relativePath = str_replace('/', '\\', $fileUpload->storage_path);
$filePathForCmd = "storage\\app\\{$relativePath}";

echo "🔧 Configuración:\n";
echo "Script batch: {$batchScript}\n";
echo "Archivo para análisis: {$filePathForCmd}\n\n";

echo "🚀 Ejecutando análisis...\n";

// Ejecutar el proceso usando Symfony Process (como lo hace Laravel)
use Symfony\Component\Process\Process;

$process = new Process([$batchScript, $filePathForCmd]);
$process->setWorkingDirectory(__DIR__);
$process->setTimeout(120);
$start = microtime(true);
$process->run();
$duration = microtime(true) - $start;

echo "⏱️ Tiempo de ejecución: " . round($duration, 2) . " segundos\n";
echo "🔄 Código de salida: " . $process->getExitCode() . "\n";
echo "📊 Longitud de salida: " . strlen($process->getOutput()) . " caracteres\n";
echo "🚨 Longitud de error: " . strlen($process->getErrorOutput()) . " caracteres\n\n";

if ($process->isSuccessful()) {
    $output = $process->getOutput();
    $result = json_decode($output, true);
    
    if (json_last_error() === JSON_ERROR_NONE) {
        echo "✅ ANÁLISIS EXITOSO!\n";
        echo "📦 Claves disponibles: " . implode(', ', array_keys($result)) . "\n";
        
        if (isset($result['manufacturing'])) {
            echo "🏭 DATOS DE MANUFACTURA ENCONTRADOS!\n";
            
            if (isset($result['manufacturing']['weight_estimates'])) {
                $materials = array_keys($result['manufacturing']['weight_estimates']);
                echo "⚖️ Materiales disponibles (" . count($materials) . "): " . implode(', ', $materials) . "\n";
                
                if (count($materials) >= 11) {
                    echo "🎉 ¡ÉXITO! Se generaron los 11 materiales esperados\n";
                } else {
                    echo "⚠️ Solo se generaron " . count($materials) . " materiales (esperados: 11)\n";
                }
            } else {
                echo "❌ No se encontraron weight_estimates en manufacturing\n";
            }
        } else {
            echo "❌ No se encontraron datos de manufacturing\n";
        }
    } else {
        echo "❌ Error al decodificar JSON: " . json_last_error_msg() . "\n";
        echo "📝 Salida cruda (primeros 500 chars):\n";
        echo substr($output, 0, 500) . "\n";
    }
} else {
    echo "❌ ANÁLISIS FALLÓ!\n";
    echo "📝 Error:\n";
    echo $process->getErrorOutput() . "\n";
    echo "📝 Salida:\n";
    echo $process->getOutput() . "\n";
}

echo "\n=== FIN DE LA PRUEBA ===\n";
