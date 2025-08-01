<?php

require_once 'vendor/autoload.php';

use App\Models\FileUpload;

// Initialize Laravel
$app = require_once 'bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

echo "=== MONITORING NEW FILE UPLOADS ===\n";
echo "Waiting for new file uploads...\n";
echo "Press Ctrl+C to stop monitoring.\n\n";

$lastFileId = FileUpload::max('id') ?? 0;
echo "Last file ID: {$lastFileId}\n";

while (true) {
    // Check for new files
    $newFiles = FileUpload::where('id', '>', $lastFileId)->orderBy('id')->get();
    
    foreach ($newFiles as $file) {
        echo "\n🆕 NEW FILE DETECTED!\n";
        echo "ID: {$file->id}\n";
        echo "Filename: {$file->filename_original}\n";
        echo "Extension: {$file->extension}\n";
        echo "Status: {$file->status}\n";
        echo "Time: " . $file->created_at->format('H:i:s') . "\n";
        
        if (strtolower($file->extension) === 'stl') {
            echo "✅ STL file detected - ready for manufacturing analysis\n";
            echo "💡 Now click the 'Analizar' button in the frontend!\n";
            
            // Monitor this file for status changes
            $this->monitorFileAnalysis($file);
        }
        
        $lastFileId = $file->id;
    }
    
    sleep(2); // Check every 2 seconds
}

function monitorFileAnalysis($file) {
    echo "\n📊 MONITORING FILE ANALYSIS: {$file->filename_original}\n";
    echo "Waiting for analysis to start...\n";
    
    $maxWaitTime = 300; // 5 minutes
    $startTime = time();
    
    while ((time() - $startTime) < $maxWaitTime) {
        $file->refresh();
        $file->load('analysisResult');
        
        static $lastStatus = null;
        if ($file->status !== $lastStatus) {
            echo "[" . date('H:i:s') . "] Status changed: {$lastStatus} → {$file->status}\n";
            $lastStatus = $file->status;
            
            if ($file->status === 'processing') {
                echo "🔄 Analysis started!\n";
            } elseif ($file->status === 'analyzed') {
                echo "✅ Analysis completed!\n";
                
                $analysisResult = $file->analysisResult;
                if ($analysisResult && $analysisResult->analysis_data) {
                    $data = $analysisResult->analysis_data;
                    
                    echo "\n📋 ANALYSIS RESULTS:\n";
                    echo "Available keys: " . implode(', ', array_keys($data)) . "\n";
                    
                    if (isset($data['manufacturing'])) {
                        echo "✅ Manufacturing data: YES\n";
                        $manufacturing = $data['manufacturing'];
                        
                        if (isset($manufacturing['weight_estimates'])) {
                            $weightCount = count($manufacturing['weight_estimates']);
                            echo "✅ Weight estimates: {$weightCount} materials\n";
                            
                            if ($weightCount === 11) {
                                echo "🎉 SUCCESS! All 11 weight estimates generated!\n";
                                
                                // Show material list
                                echo "\nMaterials analyzed:\n";
                                foreach ($manufacturing['weight_estimates'] as $key => $material) {
                                    echo "  - {$material['name']}: {$material['weight_grams']}g\n";
                                }
                                
                                echo "\n🎯 MANUFACTURING ANALYSIS SUCCESSFUL!\n";
                                echo "The frontend button is working correctly.\n";
                                return true;
                            } else {
                                echo "❌ Expected 11 materials, got {$weightCount}\n";
                            }
                        } else {
                            echo "❌ Weight estimates missing\n";
                        }
                    } else {
                        echo "❌ Manufacturing data missing\n";
                        echo "Available keys: " . implode(', ', array_keys($data)) . "\n";
                    }
                } else {
                    echo "❌ No analysis result data\n";
                }
                
                return false;
            } elseif ($file->status === 'error') {
                echo "❌ Analysis failed!\n";
                return false;
            }
        }
        
        sleep(2);
    }
    
    echo "⏰ Monitoring timeout reached\n";
    return false;
}
