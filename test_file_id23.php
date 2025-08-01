<?php

// Probar exactamente el archivo ID 23 que falló desde Laravel
echo "🧪 PRUEBA ARCHIVO ID 23 QUE FALLÓ\n";
echo "=================================\n";

$filePathForCmd = "storage\\app\\models\\1\\65fd5754-0307-4a91-8ad2-e74aa413519b.STL";
$batchScript = __DIR__ . '/run_manufacturing_analyzer.bat';

echo "Script batch: {$batchScript}\n";
echo "Archivo: {$filePathForCmd}\n\n";

require_once __DIR__ . '/vendor/autoload.php';
use Symfony\Component\Process\Process;

echo "🚀 Ejecutando desde PHP (simulando Laravel)...\n";

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
        echo "Raw output: " . substr($output, 0, 500) . "...\n";
    }
} else {
    echo "❌ FALLÓ!\n";
    echo "Error: " . $process->getErrorOutput() . "\n";
}
