<?php

// Prueba simple del script batch sin usar Eloquent
echo "🧪 PRUEBA DIRECTA DEL SCRIPT BATCH\n";
echo "==================================\n";

// Usar el mismo archivo que se probó antes
$filePathForCmd = "storage\\app\\models\\1\\0ffea33d-0de3-44d2-86c4-242c6973e7df.STL";
$batchScript = __DIR__ . '/run_manufacturing_analyzer.bat';

echo "🔧 Configuración:\n";
echo "Script batch: {$batchScript}\n";
echo "Archivo: {$filePathForCmd}\n\n";

echo "🚀 Ejecutando análisis usando Symfony Process...\n";

require_once __DIR__ . '/vendor/autoload.php';
use Symfony\Component\Process\Process;

$process = new Process([$batchScript, $filePathForCmd]);
$process->setWorkingDirectory(__DIR__);
$process->setTimeout(120);

$start = microtime(true);
$process->run();
$duration = microtime(true) - $start;

echo "⏱️ Tiempo: " . round($duration, 2) . "s\n";
echo "🔄 Exit code: " . $process->getExitCode() . "\n";
echo "📊 Output length: " . strlen($process->getOutput()) . " chars\n";
echo "🚨 Error length: " . strlen($process->getErrorOutput()) . " chars\n\n";

if ($process->isSuccessful()) {
    $output = $process->getOutput();
    $result = json_decode($output, true);
    
    if (json_last_error() === JSON_ERROR_NONE) {
        echo "✅ ANÁLISIS EXITOSO!\n";
        
        if (isset($result['manufacturing']['weight_estimates'])) {
            $materials = array_keys($result['manufacturing']['weight_estimates']);
            echo "⚖️ Materiales (" . count($materials) . "): " . implode(', ', $materials) . "\n";
            
            if (count($materials) >= 11) {
                echo "🎉 ¡PERFECTO! Los 11 materiales se generaron correctamente\n";
            } else {
                echo "⚠️ Solo " . count($materials) . " materiales (esperados: 11)\n";
            }
        } else {
            echo "❌ No hay weight_estimates\n";
        }
    } else {
        echo "❌ Error JSON: " . json_last_error_msg() . "\n";
    }
} else {
    echo "❌ FALLÓ!\n";
    echo "Error: " . $process->getErrorOutput() . "\n";
}

echo "\n=== LISTO PARA FRONTEND ===\n";
