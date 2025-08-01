<?php

// Prueba específica para el archivo ID 21 que falló
echo "🔍 PRUEBA ESPECÍFICA - ARCHIVO ID 21\n";
echo "===================================\n";

// Archivo exacto que falló
$filePathForCmd = "storage\\app\\models\\1\\51ef900f-b335-4019-8343-9c3c15a1c026.STL";
$batchScript = __DIR__ . '/run_manufacturing_analyzer.bat';

echo "🔧 Configuración:\n";
echo "Script batch: {$batchScript}\n";
echo "Archivo: {$filePathForCmd}\n\n";

echo "🚀 Ejecutando análisis usando Symfony Process (igual que Laravel)...\n";

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
            echo "🔍 Resultado disponible:\n";
            print_r(array_keys($result));
        }
    } else {
        echo "❌ Error JSON: " . json_last_error_msg() . "\n";
        echo "📝 Output recibido:\n";
        echo substr($output, 0, 500) . "...\n";
    }
} else {
    echo "❌ PROCESO FALLÓ!\n";
    echo "🚨 Exit code: " . $process->getExitCode() . "\n";
    echo "📤 Output: " . $process->getOutput() . "\n";
    echo "❗ Error: " . $process->getErrorOutput() . "\n";
    
    // Analizar el error específico
    $error = $process->getErrorOutput();
    if (strpos($error, 'Traceback') !== false) {
        echo "🐍 Error de Python detectado\n";
    }
    if (strpos($error, 'HashRandomization') !== false) {
        echo "🔧 Error de inicialización de Python - necesita PYTHONHASHSEED=0\n";
    }
}

echo "\n=== COMPARACIÓN DIRECTA ===\n";
echo "Desde consola funciona perfectamente\n";
echo "Desde PHP/Laravel falla - investigar contexto de ejecución\n";
