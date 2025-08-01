<?php

$fileInfo = "File ID 23 Info:
ID: 23
Extension: STL
Storage Path: models/1/65fd5754-0307-4a91-8ad2-e74aa413519b.STL
Full Path: storage/app/models/1/65fd5754-0307-4a91-8ad2-e74aa413519b.STL";

echo $fileInfo . "\n";

// Test the exact command that Laravel uses for ID 23
$relativePath = str_replace('/', '\\', 'models/1/65fd5754-0307-4a91-8ad2-e74aa413519b.STL');
$filePathForCmd = "storage\\app\\{$relativePath}";
echo "Batch command path: " . $filePathForCmd . "\n";
echo "File exists: " . (file_exists($filePathForCmd) ? 'YES' : 'NO') . "\n";

// Now test the batch script with the exact same parameters Laravel uses
echo "\n🧪 TESTING BATCH SCRIPT WITH EXACT LARAVEL PARAMETERS\n";
echo "===============================================\n";

$batchScript = 'run_manufacturing_analyzer.bat';
echo "Batch script: {$batchScript}\n";
echo "File path: {$filePathForCmd}\n\n";

echo "🚀 Executing: {$batchScript} {$filePathForCmd}\n";

require_once 'vendor/autoload.php';
use Symfony\Component\Process\Process;

$process = new Process([$batchScript, $filePathForCmd]);
$process->setWorkingDirectory(__DIR__);
$process->setTimeout(120);

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
        echo "✅ SUCCESS!\n";
        
        if (isset($result['manufacturing']['weight_estimates'])) {
            $materials = array_keys($result['manufacturing']['weight_estimates']);
            echo "⚖️ Materials (" . count($materials) . "): " . implode(', ', $materials) . "\n";
            echo "🎉 Manufacturing data generated successfully!\n";
        } else {
            echo "❌ No manufacturing data in result\n";
            echo "Available keys: " . implode(', ', array_keys($result)) . "\n";
        }
    } else {
        echo "❌ Invalid JSON output\n";
        echo "Raw output: " . substr($output, 0, 500) . "...\n";
    }
} else {
    echo "❌ FAILED - Exit code: " . $process->getExitCode() . "\n";
    echo "Error: " . $process->getErrorOutput() . "\n";
    echo "Output: " . $process->getOutput() . "\n";
}
