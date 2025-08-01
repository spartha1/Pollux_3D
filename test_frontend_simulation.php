<?php

require_once 'vendor/autoload.php';

use App\Models\FileUpload;
use App\Http\Controllers\FileAnalysisController;

// Initialize Laravel
$app = require_once 'bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

// Get the most recent file
$latestFile = FileUpload::orderBy('id', 'desc')->first();

if (!$latestFile) {
    echo "No files found\n";
    exit(1);
}

echo "=== SIMULATING FRONTEND BUTTON CLICK ===\n";
echo "File ID: {$latestFile->id}\n";
echo "Filename: {$latestFile->filename_original}\n";
echo "Current Status: {$latestFile->status}\n";

// Check which route would be used by frontend
if ($latestFile->status === 'uploaded') {
    echo "Frontend would call: /3d/{$latestFile->id}/analyze (analyze method)\n";
} else if ($latestFile->status === 'processed' || $latestFile->status === 'analyzed') {
    echo "Frontend would call: /3d/{$latestFile->id}/reanalyze (reanalyze method)\n";
}

// Check if file has manufacturing data before
$currentAnalysis = $latestFile->analysisResult;
if ($currentAnalysis && $currentAnalysis->analysis_data) {
    $hasManufacturing = isset($currentAnalysis->analysis_data['manufacturing']);
    echo "Current manufacturing data: " . ($hasManufacturing ? 'YES' : 'NO') . "\n";
} else {
    echo "Current manufacturing data: NO (no analysis yet)\n";
}

echo "\n=== CALLING CONTROLLER METHOD DIRECTLY ===\n";

// Create controller and call the same method the frontend calls
$controller = new FileAnalysisController();

try {
    if ($latestFile->status === 'uploaded') {
        echo "Calling analyze() method...\n";
        $response = $controller->analyze($latestFile);
    } else {
        echo "Calling reanalyze() method...\n";
        $response = $controller->reanalyze($latestFile);
    }
    
    echo "Response status: " . $response->getStatusCode() . "\n";
    
    if ($response->getStatusCode() === 200) {
        echo "✅ Controller method completed successfully\n";
        
        // Wait a moment for the database to be updated
        sleep(1);
        
        // Check result after
        $latestFile->refresh();
        $latestFile->load('analysisResult');
        $updatedAnalysis = $latestFile->analysisResult;
        
        if ($updatedAnalysis && $updatedAnalysis->analysis_data) {
            $hasManufacturing = isset($updatedAnalysis->analysis_data['manufacturing']);
            echo "Manufacturing data after analysis: " . ($hasManufacturing ? 'YES' : 'NO') . "\n";
            
            if ($hasManufacturing) {
                $weightEstimates = $updatedAnalysis->analysis_data['manufacturing']['weight_estimates'] ?? [];
                echo "Weight estimates count: " . count($weightEstimates) . "\n";
                
                if (count($weightEstimates) > 0) {
                    echo "✅ SUCCESS! Manufacturing data was generated correctly.\n";
                } else {
                    echo "❌ Manufacturing section exists but weight estimates are empty\n";
                }
            } else {
                echo "❌ Manufacturing section missing from analysis data\n";
                echo "Available keys: " . implode(', ', array_keys($updatedAnalysis->analysis_data)) . "\n";
            }
        } else {
            echo "❌ No analysis result found after execution\n";
        }
    } else {
        echo "❌ Controller method failed\n";
        echo "Response content: " . $response->getContent() . "\n";
    }
    
} catch (Exception $e) {
    echo "❌ Exception occurred: " . $e->getMessage() . "\n";
    echo "Stack trace:\n" . $e->getTraceAsString() . "\n";
}

echo "\n=== COMPARISON COMPLETE ===\n";
