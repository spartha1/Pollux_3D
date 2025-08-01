<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\FileUpload;

class DebugFileData extends Command
{
    protected $signature = 'debug:file-data {id}';
    protected $description = 'Debug what data is being sent to frontend for a file';

    public function handle()
    {
        $fileId = $this->argument('id');
        $fileUpload = FileUpload::find($fileId);

        if (!$fileUpload) {
            $this->error("File with ID {$fileId} not found");
            return 1;
        }

        $this->info("=== RAW DATABASE DATA ===");
        if ($fileUpload->analysisResult) {
            $this->line("Analysis Data JSON:");
            $this->line(json_encode($fileUpload->analysisResult->analysis_data, JSON_PRETTY_PRINT));
        } else {
            $this->warn("No analysis result found");
        }

        $this->info("\n=== WHAT FRONTEND RECEIVES ===");
        
        // Simulate the same logic as FileUploadController::show()
        $metadata = [
            'dimensions' => null,
            'vertices' => 0,
            'faces' => 0,
            'triangles' => 0,
            'volume' => null,
            'area' => null,
            'fileSize' => $fileUpload->size,
            'uploadDate' => optional($fileUpload->uploaded_at)->format('Y-m-d H:i:s'),
            'processDate' => optional($fileUpload->processed_at)->format('Y-m-d H:i:s'),
            'analysisTime' => null,
        ];

        if ($fileUpload->analysisResult) {
            $analysisData = $fileUpload->analysisResult->analysis_data;
            $metadata = array_merge($metadata, [
                'dimensions' => $analysisData['dimensions'] ?? null,
                'vertices' => $analysisData['metadata']['vertices'] ?? 0,
                'faces' => $analysisData['metadata']['faces'] ?? 0,
                'triangles' => $analysisData['metadata']['triangles'] ?? 0,
                'volume' => $analysisData['volume'] ?? null,
                'area' => $analysisData['area'] ?? null,
                'analysisTime' => $analysisData['analysis_time_ms'] ?? null,
            ]);
        }

        $fileData = [
            'id' => $fileUpload->id,
            'filename_original' => $fileUpload->filename_original,
            'analysis_result' => $fileUpload->analysisResult ? $fileUpload->analysisResult->analysis_data : null,
            'metadata' => $metadata,
        ];

        $this->line("Frontend fileUpload.analysis_result:");
        $this->line(json_encode($fileData['analysis_result'], JSON_PRETTY_PRINT));

        $this->info("\n=== MANUFACTURING DATA CHECK ===");
        if (isset($fileData['analysis_result']['manufacturing'])) {
            $this->info("✅ Manufacturing data EXISTS");
            $this->line("Manufacturing data:");
            $this->line(json_encode($fileData['analysis_result']['manufacturing'], JSON_PRETTY_PRINT));
        } else {
            $this->error("❌ Manufacturing data MISSING");
        }

        return 0;
    }
}
