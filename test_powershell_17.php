<?php

require_once 'vendor/autoload.php';

use App\Models\FileUpload;
use App\Http\Controllers\FileAnalysisController;

// Initialize Laravel
$app = require_once 'bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

try {
    echo "=== TESTING POWERSHELL APPROACH FOR FILE ID 17 ===\n";
    
    // Get file
    $file = FileUpload::find(17);
    if (!$file) {
        echo "File ID 17 not found\n";
        exit(1);
    }
    
    echo "File found: {$file->filename_original}\n";
    
    // Check current analysis data using the correct relationship
    $currentAnalysis = $file->analysisResult;
    if ($currentAnalysis && $currentAnalysis->analysis_data) {
        echo "Current analysis data keys: " . implode(', ', array_keys($currentAnalysis->analysis_data)) . "\n";
    } else {
        echo "No current analysis data\n";
        echo "Analysis result exists: " . ($currentAnalysis ? 'yes' : 'no') . "\n";
        if ($currentAnalysis) {
            echo "Analysis data exists: " . ($currentAnalysis->analysis_data ? 'yes' : 'no') . "\n";
        }
    }
    
    // Create controller instance  
    $controller = new FileAnalysisController();
    
    echo "\n=== STARTING POWERSHELL-BASED ANALYSIS ===\n";
    
    // Call analyze method
    $response = $controller->analyze($file);
    
    // Check response
    if ($response->getStatusCode() === 200) {
        echo "✅ Analysis completed successfully\n";
        
        // Reload file to get updated data - use relationship load
        $file->load('analysisResult');
        $analysisResult = $file->analysisResult;
        
        echo "Analysis result after reload: " . ($analysisResult ? 'exists' : 'null') . "\n";
        
        if ($analysisResult) {
            echo "Analysis data after reload: " . ($analysisResult->analysis_data ? 'exists' : 'null') . "\n";
            
            if ($analysisResult->analysis_data) {
                $analysisData = $analysisResult->analysis_data;
                echo "\nUpdated analysis data keys: " . implode(', ', array_keys($analysisData)) . "\n";
                
                if (isset($analysisData['manufacturing'])) {
                    echo "✅ Manufacturing data found!\n";
                    echo "Manufacturing keys: " . implode(', ', array_keys($analysisData['manufacturing'])) . "\n";
                    
                    if (isset($analysisData['manufacturing']['weight_estimates'])) {
                        echo "✅ Weight estimates found! Materials: " . count($analysisData['manufacturing']['weight_estimates']) . "\n";
                        
                        // Show some material examples
                        $materials = array_keys($analysisData['manufacturing']['weight_estimates']);
                        echo "Material examples: " . implode(', ', array_slice($materials, 0, 3)) . "\n";
                    } else {
                        echo "❌ Weight estimates missing\n";
                    }
                } else {
                    echo "❌ Manufacturing data still missing\n";
                    echo "Available keys: " . implode(', ', array_keys($analysisData)) . "\n";
                }
            } else {
                echo "❌ Analysis data is null\n";
            }
        } else {
            echo "❌ No analysis result found\n";
        }
    } else {
        echo "❌ Analysis failed with status: " . $response->getStatusCode() . "\n";
        echo "Response: " . $response->getContent() . "\n";
    }
    
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
    echo "Stack trace:\n" . $e->getTraceAsString() . "\n";
}
