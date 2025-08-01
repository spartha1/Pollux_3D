<?php

require_once 'vendor/autoload.php';

use App\Models\FileUpload;
use App\Http\Controllers\FileAnalysisController;
use Illuminate\Http\Request;

// Initialize Laravel
$app = require_once 'bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

try {
    echo "=== TESTING FILE ANALYSIS FOR ID 16 ===\n";
    
    // Get file
    $file = FileUpload::find(16);
    if (!$file) {
        echo "File ID 16 not found\n";
        exit(1);
    }
    
    echo "File found: {$file->original_name}\n";
    echo "Current analysis data keys: " . implode(', ', array_keys($file->analysis_result ?? [])) . "\n";
    
    // Create controller instance
    $controller = new FileAnalysisController();
    
    echo "\n=== STARTING RE-ANALYSIS ===\n";
    
    // Call analyze method (only takes FileUpload)
    $response = $controller->analyze($file);
    
    // Check response
    if ($response->getStatusCode() === 200) {
        echo "✅ Analysis completed successfully\n";
        
        // Reload file to get updated data
        $file->refresh();
        $analysisData = $file->analysis_result;
        
        echo "\nUpdated analysis data keys: " . implode(', ', array_keys($analysisData ?? [])) . "\n";
        
        if (isset($analysisData['manufacturing'])) {
            echo "✅ Manufacturing data found!\n";
            echo "Manufacturing keys: " . implode(', ', array_keys($analysisData['manufacturing'])) . "\n";
            
            if (isset($analysisData['manufacturing']['weight_estimates'])) {
                echo "✅ Weight estimates found! Materials: " . count($analysisData['manufacturing']['weight_estimates']) . "\n";
            } else {
                echo "❌ Weight estimates missing\n";
            }
        } else {
            echo "❌ Manufacturing data still missing\n";
        }
    } else {
        echo "❌ Analysis failed with status: " . $response->getStatusCode() . "\n";
        echo "Response: " . $response->getContent() . "\n";
    }
    
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
    echo "Stack trace:\n" . $e->getTraceAsString() . "\n";
}
