<?php

// Comparar paths Laravel vs nuestro script
echo "🔍 COMPARACIÓN DE PATHS\n";
echo "======================\n";

echo "PHP __DIR__: " . __DIR__ . "\n";

// Simular Laravel base_path()
$laravelBasePath = realpath(__DIR__);
echo "Laravel base_path(): " . $laravelBasePath . "\n";

echo "\n¿Son iguales?: " . (__DIR__ === $laravelBasePath ? "✅ SÍ" : "❌ NO") . "\n";

echo "\n🔧 SIMULANDO EXACTAMENTE LARAVEL\n";
echo "===============================\n";

$filePathForCmd = "storage\\app\\models\\1\\51ef900f-b335-4019-8343-9c3c15a1c026.STL";
$batchScript = $laravelBasePath . '/run_manufacturing_analyzer.bat'; // Como hace Laravel

echo "Script batch (método Laravel): {$batchScript}\n";
echo "Archivo: {$filePathForCmd}\n\n";

require_once __DIR__ . '/vendor/autoload.php';
use Symfony\Component\Process\Process;

$process = new Process([$batchScript, $filePathForCmd]);
$process->setWorkingDirectory($laravelBasePath); // Exacto como Laravel
$process->setTimeout(120);

$start = microtime(true);
$process->run();
$duration = microtime(true) - $start;

echo "⏱️ Tiempo: " . round($duration, 2) . "s\n";
echo "🔄 Exit code: " . $process->getExitCode() . "\n";

if ($process->isSuccessful()) {
    $output = $process->getOutput();
    $result = json_decode($output, true);
    
    if (json_last_error() === JSON_ERROR_NONE && isset($result['manufacturing']['weight_estimates'])) {
        $materials = array_keys($result['manufacturing']['weight_estimates']);
        echo "✅ ÉXITO: " . count($materials) . " materiales generados\n";
    } else {
        echo "❌ Sin datos de manufactura\n";
    }
} else {
    echo "❌ FALLÓ - Exit code: " . $process->getExitCode() . "\n";
    echo "Error: " . $process->getErrorOutput() . "\n";
}
