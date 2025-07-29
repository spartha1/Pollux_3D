<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\FileUpload;
use App\Http\Controllers\FileAnalysisController;

class AnalyzeFile extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'file:analyze {id : The file upload ID to analyze}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Analyze a specific file and generate metadata';

    /**
     * Execute the console command.
     */
    public function handle()
    {
        $fileId = $this->argument('id');

        $this->info("Looking for file with ID: {$fileId}");

        $file = FileUpload::find($fileId);

        if (!$file) {
            $this->error("File with ID {$fileId} not found");
            return 1;
        }

        // Ensure we have a single FileUpload model
        if (!($file instanceof FileUpload)) {
            $this->error("Expected FileUpload model, got: " . get_class($file));
            return 1;
        }

        $this->info("File found:");
        $this->info("- ID: {$file->id}");
        $this->info("- Filename: {$file->filename_original}");
        $this->info("- Path: {$file->storage_path}");
        $this->info("- Status: {$file->status}");

        $fullPath = storage_path('app/' . $file->storage_path);
        $fileExists = file_exists($fullPath);
        $this->info("- File exists: " . ($fileExists ? 'Yes' : 'No'));

        if (!$fileExists) {
            $this->error("File does not exist on disk at: {$fullPath}");
            return 1;
        }

        // Check if analysis already exists
        if ($file->analysisResult) {
            $this->warn("Analysis already exists for this file");
            $this->info("Current analysis data: " . json_encode($file->analysisResult->analysis_data, JSON_PRETTY_PRINT));

            if (!$this->confirm('Do you want to re-analyze this file?')) {
                return 0;
            }
        }

        $this->info("Starting analysis...");

        try {
            // Create controller instance
            $controller = new FileAnalysisController();

            // Call the analyze method (only pass the FileUpload model)
            $response = $controller->analyze($file);

            if ($response->getStatusCode() === 200) {
                $this->info("Analysis completed successfully!");

                // Refresh the file model to get updated analysis result
                $file->refresh();
                if ($file->analysisResult) {
                    $this->info("Analysis data:");
                    $this->line(json_encode($file->analysisResult->analysis_data, JSON_PRETTY_PRINT));
                }
            } else {
                $this->error("Analysis failed with status: " . $response->getStatusCode());
                $this->error("Response: " . $response->getContent());
                return 1;
            }

        } catch (\Exception $e) {
            $this->error("Analysis failed with exception: " . $e->getMessage());
            $this->error("Stack trace: " . $e->getTraceAsString());
            return 1;
        }

        return 0;
    }
}
