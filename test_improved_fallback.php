<?php

echo "🧪 TESTING IMPROVED FALLBACK ANALYZER\n";
echo "=====================================\n";

// Test with the exact same file that failed before
$filePath = "storage\\app\\models\\1\\65fd5754-0307-4a91-8ad2-e74aa413519b.STL";
$fallbackScript = "app\\Services\\FileAnalyzers\\analyze_stl_no_numpy.py";

echo "File: {$filePath}\n";
echo "Script: {$fallbackScript}\n\n";

require_once 'vendor/autoload.php';
use Symfony\Component\Process\Process;

// Test with regular Python (like Laravel fallback does)
$process = new Process([
    'python',
    $fallbackScript,
    $filePath
]);

$process->setEnv(['PYTHONHASHSEED' => '0']);
$process->setTimeout(30);

echo "🚀 Executing improved fallback analyzer...\n";

$start = microtime(true);
$process->run();
$duration = microtime(true) - $start;

echo "⏱️ Duration: " . round($duration, 2) . "s\n";
echo "🔄 Exit code: " . $process->getExitCode() . "\n";
echo "📊 Output length: " . strlen($process->getOutput()) . " chars\n";
echo "🚨 Error length: " . strlen($process->getErrorOutput()) . " chars\n\n";

if ($process->isSuccessful()) {
    $output = $process->getOutput();
    $result = json_decode($output, true);
    
    if (json_last_error() === JSON_ERROR_NONE) {
        echo "✅ FALLBACK SUCCESS!\n";
        
        if (isset($result['manufacturing']['weight_estimates'])) {
            $materials = array_keys($result['manufacturing']['weight_estimates']);
            echo "⚖️ Materials (" . count($materials) . "): " . implode(', ', $materials) . "\n";
            echo "🎉 ¡FALLBACK ahora tiene datos de manufacturing!\n";
            
            // Show a sample material
            $firstMaterial = reset($result['manufacturing']['weight_estimates']);
            echo "📊 Sample material: {$firstMaterial['name']}\n";
            echo "   Weight: {$firstMaterial['weight_grams']}g ({$firstMaterial['weight_kg']}kg)\n";
            echo "   Cost: \${$firstMaterial['estimated_cost_usd']}\n";
        } else {
            echo "❌ No manufacturing data in fallback result\n";
            echo "Available keys: " . implode(', ', array_keys($result)) . "\n";
        }
        
        // Check basic data
        if (isset($result['dimensions'], $result['volume'], $result['area'])) {
            echo "✅ Basic geometry data present\n";
        }
        
    } else {
        echo "❌ Invalid JSON from fallback\n";
        echo "Raw output: " . substr($output, 0, 500) . "...\n";
    }
} else {
    echo "❌ FALLBACK FAILED - Exit code: " . $process->getExitCode() . "\n";
    echo "Error: " . $process->getErrorOutput() . "\n";
    echo "Output: " . $process->getOutput() . "\n";
}
