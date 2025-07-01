<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\FileUpload;

class CheckFile extends Command
{
    protected $signature = 'file:check {id : The file ID to check}';
    protected $description = 'Check file status and existence';

    public function handle()
    {
        $fileId = $this->argument('id');
        $file = FileUpload::find($fileId);

        if (!$file) {
            $this->error("File with ID {$fileId} not found");
            return 1;
        }

        $this->info("File Details:");
        $this->line("ID: {$file->id}");
        $this->line("Filename: {$file->filename}");
        $this->line("Original Name: {$file->original_filename}");
        $this->line("Storage Path: {$file->storage_path}");
        $this->line("Status: {$file->status}");
        $this->line("MIME Type: {$file->mime_type}");
        $this->line("File Size: {$file->file_size} bytes");
        $this->line("Created: {$file->created_at}");

        $fullPath = storage_path('app/' . $file->storage_path);
        $exists = file_exists($fullPath);
        $this->line("Full Path: {$fullPath}");
        $this->line("File Exists: " . ($exists ? 'Yes' : 'No'));

        if ($exists) {
            $actualSize = filesize($fullPath);
            $this->line("Actual File Size: {$actualSize} bytes");
        }

        // Check analysis result
        $analysisResult = $file->analysisResult;
        if ($analysisResult) {
            $this->info("Analysis Result:");
            $this->line("Status: {$analysisResult->status}");
            $this->line("Created: {$analysisResult->created_at}");
            if ($analysisResult->analysis_data) {
                $this->line("Analysis Data: " . json_encode($analysisResult->analysis_data, JSON_PRETTY_PRINT));
            }
        } else {
            $this->warn("No analysis result found");
        }

        return 0;
    }
}
