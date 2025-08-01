<?php

require_once 'vendor/autoload.php';

use App\Models\FileUpload;
use App\Http\Controllers\FileAnalysisController;

// Initialize Laravel
$app = require_once 'bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

// Get the most recent STL file
$latestFile = FileUpload::where('extension', 'stl')
    ->orderBy('id', 'desc')
    ->first();

if (!$latestFile) {
    echo "No STL files found\n";
    exit(1);
}

echo "=== TESTING LATEST STL FILE ===\n";
echo "File ID: {$latestFile->id}\n";
echo "Filename: {$latestFile->filename_original}\n";
echo "Status: {$latestFile->status}\n";
echo "Storage path: {$latestFile->storage_path}\n";

// Check if file exists
$fullPath = storage_path('app/' . $latestFile->storage_path);
echo "File exists: " . (file_exists($fullPath) ? 'yes' : 'no') . "\n";

if (!file_exists($fullPath)) {
    echo "ERROR: File not found at {$fullPath}\n";
    exit(1);
}

// Check current analysis data
$currentAnalysis = $latestFile->analysisResult;
if ($currentAnalysis && $currentAnalysis->analysis_data) {
    echo "Current analysis data keys: " . implode(', ', array_keys($currentAnalysis->analysis_data)) . "\n";
    
    if (isset($currentAnalysis->analysis_data['manufacturing'])) {
        echo "✅ Manufacturing data already exists\n";
        $weightEstimates = $currentAnalysis->analysis_data['manufacturing']['weight_estimates'] ?? [];
        echo "Current weight estimates: " . count($weightEstimates) . " materials\n";
    } else {
        echo "❌ No manufacturing data yet\n";
    }
} else {
    echo "No analysis data yet\n";
}

echo "\n=== STARTING MANUFACTURING ANALYSIS ===\n";

// Create controller instance and analyze
$controller = new FileAnalysisController();
$response = $controller->analyze($latestFile);

// Check response
if ($response->getStatusCode() === 200) {
    echo "✅ Analysis completed successfully\n";
    
    // Reload file to get updated data
    $latestFile->load('analysisResult');
    $analysisResult = $latestFile->analysisResult;
    
    if ($analysisResult && $analysisResult->analysis_data) {
        $analysisData = $analysisResult->analysis_data;
        echo "\n=== ANALYSIS RESULTS ===\n";
        echo "Available data keys: " . implode(', ', array_keys($analysisData)) . "\n";
        
        // Check dimensions
        if (isset($analysisData['dimensions'])) {
            $dims = $analysisData['dimensions'];
            echo "Dimensions: {$dims['width']} x {$dims['height']} x {$dims['depth']} mm\n";
        }
        
        // Check volume
        if (isset($analysisData['volume'])) {
            echo "Volume: {$analysisData['volume']} mm³\n";
        }
        
        // Check manufacturing data
        if (isset($analysisData['manufacturing'])) {
            echo "\n✅ MANUFACTURING DATA FOUND!\n";
            $manufacturing = $analysisData['manufacturing'];
            
            echo "Manufacturing keys: " . implode(', ', array_keys($manufacturing)) . "\n";
            
            // Weight estimates
            if (isset($manufacturing['weight_estimates'])) {
                $weightEstimates = $manufacturing['weight_estimates'];
                echo "✅ Weight estimates: " . count($weightEstimates) . " materials\n";
                
                echo "\nMaterial weight estimates:\n";
                foreach ($weightEstimates as $material => $data) {
                    echo "  - {$data['name']}: {$data['weight_grams']}g ({$data['type']})\n";
                }
            } else {
                echo "❌ Weight estimates missing\n";
            }
            
            // Other manufacturing data
            if (isset($manufacturing['complexity'])) {
                echo "Complexity: {$manufacturing['complexity']['surface_complexity']} / {$manufacturing['complexity']['fabrication_difficulty']}\n";
            }
            
            if (isset($manufacturing['cutting_perimeters'])) {
                echo "Cutting perimeters: {$manufacturing['cutting_perimeters']}\n";
            }
            
        } else {
            echo "❌ Manufacturing data missing\n";
            echo "Available keys: " . implode(', ', array_keys($analysisData)) . "\n";
        }
        
    } else {
        echo "❌ No analysis result data\n";
    }
    
} else {
    echo "❌ Analysis failed with status: " . $response->getStatusCode() . "\n";
    echo "Response: " . $response->getContent() . "\n";
}

echo "\n=== TEST COMPLETED ===\n";
