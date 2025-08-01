<?php

// Prueba específica para el archivo ID 20 con el script batch mejorado
echo "🧪 PRUEBA SCRIPT BATCH - ARCHIVO ID 20\n";
echo "=====================================\n";

// Usar el archivo específico que falló
$filePathForCmd = "storage\\app\\models\\1\\631c6fce-96f6-4581-82a0-d49dea9cdfc9.STL";
$batchScript = __DIR__ . '/run_manufacturing_analyzer.bat';

echo "📁 Archivo: {$filePathForCmd}\n";
echo "🔧 Script: {$batchScript}\n\n";

require_once __DIR__ . '/vendor/autoload.php';
use Symfony\Component\Process\Process;

echo "🚀 Ejecutando desde PHP...\n";

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
        echo "✅ ¡ANÁLISIS EXITOSO!\n";
        
        if (isset($result['manufacturing']['weight_estimates'])) {
            $materials = array_keys($result['manufacturing']['weight_estimates']);
            echo "⚖️ Materiales (" . count($materials) . "): " . implode(', ', $materials) . "\n";
            
            if (count($materials) >= 11) {
                echo "🎉 ¡PERFECTO! Los 11 materiales generados correctamente\n";
                echo "🔧 El script batch está funcionando desde PHP\n";
                echo "✅ Listo para usarse en el frontend\n";
            } else {
                echo "⚠️ Solo " . count($materials) . " materiales\n";
            }
        } else {
            echo "❌ No hay weight_estimates\n";
        }
    } else {
        echo "❌ Error JSON: " . json_last_error_msg() . "\n";
        echo "Output: " . substr($output, 0, 200) . "...\n";
    }
} else {
    echo "❌ FALLÓ!\n";
    echo "Exit code: " . $process->getExitCode() . "\n";
    echo "Error: " . $process->getErrorOutput() . "\n";
    echo "Output: " . $process->getOutput() . "\n";
}

echo "\n=== RESULTADO FINAL ===\n";
