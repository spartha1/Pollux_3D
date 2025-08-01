<?php

require_once 'vendor/autoload.php';

use App\Models\FileUpload;

// Initialize Laravel
$app = require_once 'bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

echo "=== REAL-TIME FILE ANALYSIS MONITOR ===\n";

// Get current latest file ID
$currentLatest = FileUpload::max('id') ?? 0;
echo "Current latest file ID: {$currentLatest}\n";
echo "Waiting for new file upload...\n";
echo "👆 Please upload a new STL file now\n\n";

while (true) {
    $newLatest = FileUpload::max('id') ?? 0;
    
    if ($newLatest > $currentLatest) {
        $newFile = FileUpload::find($newLatest);
        echo "🆕 NEW FILE UPLOADED!\n";
        echo "ID: {$newFile->id}\n";
        echo "Name: {$newFile->filename_original}\n";
        echo "Extension: {$newFile->extension}\n";
        echo "Status: {$newFile->status}\n";
        echo "Time: " . $newFile->created_at->format('H:i:s') . "\n";
        
        if (strtolower($newFile->extension) === 'stl') {
            echo "\n✅ STL file detected!\n";
            echo "🔴 Now press the 'Analizar' button in the web interface!\n";
            echo "📊 Monitoring analysis progress...\n\n";
            
            // Monitor the analysis
            $startTime = time();
            $lastStatus = $newFile->status;
            
            while (time() - $startTime < 180) { // 3 minutes timeout
                sleep(3);
                $newFile->refresh();
                $newFile->load('analysisResult');
                
                if ($newFile->status !== $lastStatus) {
                    echo "[" . date('H:i:s') . "] Status: {$lastStatus} → {$newFile->status}\n";
                    $lastStatus = $newFile->status;
                    
                    if ($newFile->status === 'processing') {
                        echo "🔄 Analysis started! Manufacturing analyzer is running...\n";
                    } elseif ($newFile->status === 'analyzed') {
                        echo "✅ Analysis completed!\n";
                        
                        $analysis = $newFile->analysisResult;
                        if ($analysis && $analysis->analysis_data) {
                            $data = $analysis->analysis_data;
                            
                            if (isset($data['manufacturing'])) {
                                echo "✅ Manufacturing data: PRESENT\n";
                                
                                if (isset($data['manufacturing']['weight_estimates'])) {
                                    $count = count($data['manufacturing']['weight_estimates']);
                                    echo "✅ Weight estimates: {$count} materials\n";
                                    
                                    if ($count === 11) {
                                        echo "\n🎉 SUCCESS! FRONTEND BUTTON WORKS PERFECTLY!\n";
                                        echo "All 11 material weight estimates generated:\n";
                                        
                                        foreach ($data['manufacturing']['weight_estimates'] as $key => $mat) {
                                            echo "  - {$mat['name']}: {$mat['weight_grams']}g\n";
                                        }
                                        
                                        echo "\n🚀 The manufacturing analysis system is fully functional!\n";
                                        exit(0);
                                    } else {
                                        echo "❌ Expected 11 materials, got {$count}\n";
                                    }
                                } else {
                                    echo "❌ Weight estimates missing\n";
                                }
                            } else {
                                echo "❌ Manufacturing data missing\n";
                                echo "Available keys: " . implode(', ', array_keys($data)) . "\n";
                            }
                        } else {
                            echo "❌ No analysis data found\n";
                        }
                        
                        break;
                    } elseif ($newFile->status === 'error') {
                        echo "❌ Analysis failed!\n";
                        break;
                    }
                }
            }
            
            if (time() - $startTime >= 180) {
                echo "⏰ Analysis timeout - check manually\n";
            }
            
            break;
        } else {
            echo "ℹ️ Not an STL file, continuing to wait...\n";
        }
        
        $currentLatest = $newLatest;
    }
    
    sleep(2);
}
