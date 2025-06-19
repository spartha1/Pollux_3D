<?php

namespace App\Http\Controllers;

use App\Models\FileUpload;
use App\Models\FileAnalysisResult;
use Illuminate\Http\Request;
use Illuminate\Foundation\Auth\Access\AuthorizesRequests;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;

class FileAnalysisController extends Controller
{
    use AuthorizesRequests;
    /**
     * Trigger analysis for a file upload.
     */
    public function analyze(FileUpload $fileUpload)
    {
        $this->authorize('update', $fileUpload);

        if ($fileUpload->status !== 'uploaded') {
            return back()->with('error', 'File is already being processed or has been processed.');
        }

        // Update status
        $fileUpload->update(['status' => 'processing']);

        try {
            // Get the absolute paths
            $analyzerPath = base_path('app/Services/FileAnalyzers');

            // Select the appropriate analyzer based on file extension
            $extension = strtolower($fileUpload->extension);
            $scriptName = match($extension) {
                'step', 'stp' => 'analyze_step_simple.py',
                'stl' => 'analyze_stl.py',
                'dxf', 'dwg' => 'analyze_dxf_dwg.py',
                'ai', 'eps' => 'analyze_ai_eps.py',
                default => throw new \Exception("Unsupported file type: $extension")
            };

            $scriptPath = $analyzerPath . DIRECTORY_SEPARATOR . $scriptName;

            // Get storage path and disk
            if (!$fileUpload->storage_path) {
                throw new \Exception("File storage path is missing");
            }

            $disk = Storage::disk($fileUpload->disk);

            // Log file path information for debugging
            Log::info('File paths:', [
                'storage_path' => $fileUpload->storage_path,
                'absolute_path' => $disk->path($fileUpload->storage_path),
                'exists' => $disk->exists($fileUpload->storage_path)
            ]);

            // Log all available information about the file
            Log::info('Analyzing file:', [
                'id' => $fileUpload->id,
                'original_name' => $fileUpload->filename_original,
                'stored_name' => $fileUpload->filename_stored,
                'extension' => $fileUpload->extension,
                'storage_path' => $fileUpload->storage_path,
                'disk' => $fileUpload->disk,
                'full_path' => Storage::disk($fileUpload->disk)->path($fileUpload->storage_path),
                'exists' => Storage::disk($fileUpload->disk)->exists($fileUpload->storage_path)
            ]);

            // Verify file exists before proceeding
            if (!$disk->exists($fileUpload->storage_path)) {
                throw new \Exception("File not found in storage: " . $fileUpload->storage_path);
            }

            // Get absolute path for the Python script
            $filePath = $disk->path($fileUpload->storage_path);

            // Set up clean environment
            $env = array_merge([
                'PYTHONIOENCODING' => 'utf-8',
                'PYTHONUNBUFFERED' => '1',
                'PYTHONDONTWRITEBYTECODE' => '1',
                'TEMP' => sys_get_temp_dir(),
                'TMP' => sys_get_temp_dir(),
            ], getenv());

            // Build the process
            // Try different Python paths in order of preference
            $pythonPath = null;

            // 1. Try conda environment if available
            if (isset($_SERVER['CONDA_PREFIX'])) {
                $condaPython = $_SERVER['CONDA_PREFIX'] . '\python.exe';
                if (file_exists($condaPython)) {
                    $pythonPath = $condaPython;
                }
            }

            // 2. Try venv in project directory
            if (!$pythonPath) {
                $venvPython = base_path('venv/Scripts/python.exe');
                if (file_exists($venvPython)) {
                    $pythonPath = $venvPython;
                }
            }

            // 3. Try system Python as last resort
            if (!$pythonPath) {
                // Try to find Python in PATH
                $process = new Process(['where', 'python']);
                $process->run();
                if ($process->isSuccessful()) {
                    $pythonPath = trim($process->getOutput());
                } else {
                    throw new \Exception('No se pudo encontrar un ejecutable de Python válido. Por favor, asegúrese de tener Python instalado.');
                }
            }

            Log::info('Using Python path: ' . $pythonPath);
            $process = new Process([$pythonPath, $scriptPath, $filePath]);
            $process->setWorkingDirectory($analyzerPath);
            $process->setEnv($env);
            $process->setTimeout(300);

            $startTime = microtime(true);
            $output = '';
            $errorOutput = '';

            // Capture both stdout and stderr
            $process->run(function ($type, $buffer) use (&$output, &$errorOutput) {
                if (Process::ERR === $type) {
                    Log::error('Analysis process error output: ' . $buffer);
                    $errorOutput .= $buffer;
                } else {
                    $output .= $buffer;
                }
            });

            // Log the total analysis time
            $analysisTime = (microtime(true) - $startTime) * 1000; // Convert to milliseconds

            if (!$process->isSuccessful()) {
                list($errorMessage, $errorContext) = $this->captureProcessError($process);
                Log::error('Analysis process failed', array_merge(
                    ['file_id' => $fileUpload->id],
                    $errorContext
                ));
                throw new \Exception("Analysis failed: " . $errorMessage);
            }

            // Try to parse the output as JSON
            $data = json_decode($output, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                // Log the raw output for debugging
                Log::error('Failed to parse analysis output as JSON', [
                    'output' => $output,
                    'json_error' => json_last_error_msg(),
                    'error_output' => $errorOutput
                ]);
                throw new \Exception("Invalid analysis output format: " . json_last_error_msg());
            }

            // Check for error in JSON
            if (isset($data['error'])) {
                throw new \Exception($data['error'] . (isset($data['traceback']) ? "\n" . $data['traceback'] : ''));
            }

            Log::info('📦 Analysis data received:', ['data' => $data]);

            // Normalize dimensions for compatibility with other analyzers
            $dimensions = $data['dimensions'] ?? null;
            if ($dimensions) {
                // Convert width/height/depth to x/y/z if needed
                if (isset($dimensions['width'], $dimensions['height'], $dimensions['depth'])) {
                    $dimensions['x'] = $dimensions['width'];
                    $dimensions['y'] = $dimensions['height'];
                    $dimensions['z'] = $dimensions['depth'];
                }
                // Ensure x/y/z exist
                if (!isset($dimensions['x'])) {
                    $dimensions['x'] = 0;
                    $dimensions['y'] = 0;
                    $dimensions['z'] = 0;
                }
            }

            // Save results to DB with analysis time
            $fileUpload->analysisResult()->create(array(
                'dimensions' => $dimensions,
                'volume' => $data['volume'] ?? null,
                'area' => $data['area'] ?? null,
                'layers' => $data['layers'] ?? null,
                'metadata' => $data['metadata'] ?? null,
                'analysis_time_ms' => $data['analysis_time_ms'] ?? round($analysisTime)
            ));

            $fileUpload->update([
                'status' => 'processed',
                'processed_at' => now(),
            ]);

        } catch (\Exception $e) {
            // Get process error context if available
            list($processError, $errorContext) = isset($process) ? $this->captureProcessError($process) : ['', []];

            // Build error message
            $errorMessage = $e->getMessage();
            if ($processError && !str_contains($errorMessage, $processError)) {
                $errorMessage .= "\n" . $processError;
            }

            // Log the error with full context
            Log::error('❌ Analysis failed', array_merge([
                'file_id' => $fileUpload->id,
                'error' => $errorMessage,
                'exception' => get_class($e),
            ], $errorContext));

            // Create error record
            $fileUpload->errors()->create([
                'error_message' => $errorMessage,
                'stack_trace' => $e->getTraceAsString()
            ]);

            // Update file status
            $fileUpload->update([
                'status' => 'failed',
                'processed_at' => now()
            ]);

            throw $e;
        }
    }

    /**
     * Get analysis results via API.
     */
    public function results(FileUpload $fileUpload)
    {
        $this->authorize('view', $fileUpload);

        $analysisResult = $fileUpload->analysisResult;

        if (!$analysisResult) {
            return response()->json([
                'message' => 'No analysis results available yet.'
            ], 404);
        }

        return response()->json([
            'file_id' => $fileUpload->id,
            'status' => $fileUpload->status,
            'results' => [
                'dimensions' => $analysisResult->dimensions,
                'volume' => $analysisResult->volume,
                'area' => $analysisResult->area,
                'layers' => $analysisResult->layers,
                'metadata' => $analysisResult->metadata,
                'analysis_time_ms' => $analysisResult->analysis_time_ms,
            ]
        ]);
    }

    /**
     * Re-analyze a file.
     */
    public function reanalyze(FileUpload $fileUpload)
    {
        $this->authorize('update', $fileUpload);

        // Delete existing results
        $fileUpload->analysisResult?->delete();
        $fileUpload->errors()->delete();

        // Reset status and trigger new analysis
        $fileUpload->update([
            'status' => 'uploaded',
            'processed_at' => null
        ]);

        return $this->analyze($fileUpload);
    }

    private function captureProcessError($process)
    {
        $errorContext = array();
        $errorMessage = '';

        if ($process instanceof Process) {
            $errorOutput = $process->getErrorOutput();
            $output = $process->getOutput();
            $exitCode = $process->getExitCode();

            if ($errorOutput) {
                $errorMessage .= "Error Output: " . $errorOutput;
                $errorContext['error_output'] = $errorOutput;
            }

            if ($output) {
                $errorContext['output'] = $output;
                if (!$errorMessage && $exitCode !== 0) {
                    $errorMessage .= "Process Output: " . $output;
                }
            }

            $errorContext['exit_code'] = $exitCode;
            $errorContext['command'] = $process->getCommandLine();
        }

        return array($errorMessage, $errorContext);
    }

    /**
     * Clean up the temporary directory and its contents
     */
    private function cleanupTempDirectory($dir)
    {
        if (!is_dir($dir)) {
            return;
        }

        $files = array_diff(scandir($dir), array('.', '..'));
        foreach ($files as $file) {
            $path = $dir . DIRECTORY_SEPARATOR . $file;
            if (is_dir($path)) {
                $this->cleanupTempDirectory($path);
            } else {
                @unlink($path);
            }
        }
        @rmdir($dir);

        Log::debug("🧹 Cleaned up temporary directory", ['directory' => $dir]);
    }
}
