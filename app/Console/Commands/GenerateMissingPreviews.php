<?php

namespace App\Console\Commands;

use App\Models\FileUpload;
use App\Models\FilePreview;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Symfony\Component\Process\Process;

class GenerateMissingPreviews extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'previews:generate-missing {--file-id= : Specific file ID to process} {--type= : Specific preview type (2d, wireframe, 3d)}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Generate missing 2D and wireframe previews for uploaded files';

    /**
     * Execute the console command.
     */
    public function handle()
    {
        $this->info('🚀 Starting preview generation...');

        // Get files to process
        $query = FileUpload::with('previews');

        if ($fileId = $this->option('file-id')) {
            $query->where('id', $fileId);
        } else {
            // Only process STL files that don't have all preview types
            $query->where('extension', 'stl')
                  ->where('status', 'uploaded');
        }

        $files = $query->get();

        if ($files->isEmpty()) {
            $this->warn('❌ No files found to process.');
            return;
        }

        $this->info("📁 Found {$files->count()} files to process");

        $viewTypes = $this->option('type') ? [$this->option('type')] : ['2d', 'wireframe'];

        $successCount = 0;
        $errorCount = 0;

        foreach ($files as $file) {
            $this->line("📄 Processing: {$file->filename_original}");

            // Check which previews are missing
            $existingPreviews = $file->previews->pluck('render_type')->toArray();
            $missingTypes = array_diff($viewTypes, $existingPreviews);

            if (empty($missingTypes)) {
                $this->info("  ✅ All previews already exist");
                continue;
            }

            foreach ($missingTypes as $type) {
                $this->line("  🎨 Generating {$type} preview...");

                try {
                    // Call the preview generation service directly
                    $preview = $this->generatePreviewDirect($file, $type);

                    if ($preview) {
                        $this->info("    ✅ {$type} preview generated successfully");
                        $successCount++;
                    } else {
                        $this->error("    ❌ Failed to generate {$type} preview");
                        $errorCount++;
                    }

                } catch (\Exception $e) {
                    $this->error("    ❌ Error generating {$type} preview: {$e->getMessage()}");
                    Log::error("Preview generation failed", [
                        'file_id' => $file->id,
                        'type' => $type,
                        'error' => $e->getMessage()
                    ]);
                    $errorCount++;
                }
            }
        }

        $this->newLine();
        $this->info("🎉 Preview generation completed!");
        $this->info("✅ Success: {$successCount}");
        if ($errorCount > 0) {
            $this->error("❌ Errors: {$errorCount}");
        }

        return $errorCount === 0 ? 0 : 1;
    }

    /**
     * Generate preview directly without going through controller authorization
     */
    private function generatePreviewDirect($fileUpload, $renderType)
    {
        try {
            // Check if preview already exists
            $existingPreview = $fileUpload->previews()
                ->where('render_type', $renderType)
                ->first();

            if ($existingPreview) {
                $this->info("    ✅ Preview already exists");
                return $existingPreview;
            }

            // Get the absolute file path
            $filePath = Storage::disk($fileUpload->disk)->path($fileUpload->storage_path);

            if (!file_exists($filePath)) {
                throw new \Exception("File not found: {$filePath}");
            }

            // Generate preview based on type
            if ($renderType === '2d' || $renderType === 'wireframe') {
                return $this->generateImagePreview($fileUpload, $renderType, $filePath);
            } else {
                // For 3D previews, we might use a different approach
                $this->line("    📝 3D preview generation not implemented yet");
                return null;
            }

        } catch (\Exception $e) {
            Log::error("Direct preview generation failed", [
                'file_id' => $fileUpload->id,
                'type' => $renderType,
                'error' => $e->getMessage()
            ]);
            throw $e;
        }
    }

    /**
     * Generate 2D or wireframe preview image using Python script
     */
    private function generateImagePreview($fileUpload, $renderType, $filePath)
    {
        // Use the Python script for generating actual images
        $scriptPath = app_path('Services/FileAnalyzers/generate_preview_images.py');

        if (!file_exists($scriptPath)) {
            throw new \Exception("Preview generation script not found: {$scriptPath}");
        }

        // Create output directory if it doesn't exist
        $outputDir = storage_path('app/public/previews');
        if (!is_dir($outputDir)) {
            Storage::disk('public')->makeDirectory('previews');
        }

        // Generate unique filename for the preview image
        $filename = "preview_{$fileUpload->id}_{$renderType}_" . time() . ".png";
        $outputPath = $outputDir . DIRECTORY_SEPARATOR . $filename;
        $relativePath = "previews/{$filename}";

        // Normalize paths for Windows
        $scriptPath = str_replace('/', DIRECTORY_SEPARATOR, $scriptPath);
        $filePath = str_replace('/', DIRECTORY_SEPARATOR, $filePath);
        $outputPath = str_replace('/', DIRECTORY_SEPARATOR, $outputPath);

        $this->line("    🐍 Running Python script...");
        $this->line("    📁 Script: {$scriptPath}");
        $this->line("    📄 Input: {$filePath}");
        $this->line("    🖼️ Output: {$outputPath}");

        // Build the conda command properly for Windows
        $condaCommand = [
            'conda', 'run', '-n', 'pollux', 'python',
            $scriptPath,
            $filePath,
            $outputPath,
            $renderType,
            '800',
            '600'
        ];

        // Run the preview generation script
        $process = new Process($condaCommand);
        $process->setTimeout(60); // Increased timeout for image generation
        $process->run();

        $this->line("    📤 Command output: " . $process->getOutput());
        if ($process->getErrorOutput()) {
            $this->line("    ⚠️ Command errors: " . $process->getErrorOutput());
        }

        if (!$process->isSuccessful()) {
            throw new \Exception("Preview generation failed. Exit code: " . $process->getExitCode() . ". Error: " . $process->getErrorOutput());
        }

        // Parse the JSON output from the script
        $output = trim($process->getOutput());
        if (empty($output)) {
            throw new \Exception("No output from preview generation script");
        }

        $result = json_decode($output, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            $this->line("    ⚠️ Non-JSON output: {$output}");
            // If it's not JSON, assume success if file exists
            if (file_exists($outputPath)) {
                $result = ['success' => true];
            } else {
                throw new \Exception("Preview generation failed: Invalid JSON output");
            }
        }

        if (!$result || !$result['success']) {
            throw new \Exception("Preview generation failed: " . ($result['error'] ?? 'Unknown error'));
        }

        // Verify the image file was created
        if (!file_exists($outputPath)) {
            throw new \Exception("Preview image file was not created at: {$outputPath}");
        }

        // Create database record for the preview
        $preview = FilePreview::create([
            'file_upload_id' => $fileUpload->id,
            'image_path' => $relativePath,
            'render_type' => $renderType,
            'generated_at' => now()
        ]);

        $this->line("    📸 Image saved: {$relativePath}");
        return $preview;
    }
}
