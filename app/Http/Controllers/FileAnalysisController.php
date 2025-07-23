<?php

namespace App\Http\Controllers;

use App\Models\FileUpload;
use App\Models\FileAnalysisResult;
use App\Models\FileError;
use Illuminate\Http\Request;
use Symfony\Component\Process\Process;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Http;
use Illuminate\Foundation\Auth\Access\AuthorizesRequests;
use Inertia\Inertia;

class FileAnalysisController extends Controller
{
    use AuthorizesRequests;

    /**
     * Trigger analysis for a file upload.
     */
    public function analyze(FileUpload $fileUpload)
    {
        // Skip authorization when running from CLI (Artisan commands)
        if (!app()->runningInConsole()) {
            $this->authorize('update', $fileUpload);
        }

        if ($fileUpload->status !== 'uploaded') {
            // If running in console, continue anyway; otherwise return error
            if (!app()->runningInConsole()) {
                return back()->with('error', 'File is already being processed or has been processed.');
            }
        }

        // Update status
        $fileUpload->update(['status' => 'processing']);

        try {
            $filePath = storage_path('app/' . $fileUpload->storage_path);
            $extension = strtolower(pathinfo($filePath, PATHINFO_EXTENSION));

            // Get the Python executable path from the conda environment
            $pythonPath = config('services.python.executable');

            if (!file_exists($pythonPath)) {
                throw new \Exception("Python executable not found at: {$pythonPath}");
            }

            // Select the appropriate analyzer based on file extension
            $analyzerScript = match($extension) {
                'stl' => app_path('Services/FileAnalyzers/analyze_stl_manufacturing.py'),
                'step', 'stp' => app_path('Services/FileAnalyzers/analyze_step_simple.py'),
                'dxf', 'dwg' => app_path('Services/FileAnalyzers/analyze_dxf_dwg.py'),
                'eps', 'ai' => app_path('Services/FileAnalyzers/analyze_ai_eps.py'),
                default => throw new \Exception("Unsupported file type: {$extension}")
            };

            // For STL files, have a fallback analyzer without numpy
            $fallbackScript = null;
            if ($extension === 'stl') {
                $fallbackScript = app_path('Services/FileAnalyzers/analyze_stl_no_numpy.py');
            }

            // Check if analyzer exists
            if (!file_exists($analyzerScript)) {
                throw new \Exception("Analyzer not found for type: {$extension}");
            }

            Log::info('Starting analysis', [
                'python' => $pythonPath,
                'script' => $analyzerScript,
                'file' => $filePath
            ]);

            // Run analysis using conda wrapper to ensure proper environment
            $wrapperScript = app_path('Services/FileAnalyzers/run_with_conda.bat');
            $process = new Process([
                $wrapperScript,
                $analyzerScript,
                $filePath
            ]);

            // Set basic environment variables
            $process->setEnv([
                'PYTHONHASHSEED' => '0'
            ]);

            $process->setTimeout(30);
            $process->run();

            if (!$process->isSuccessful()) {
                Log::warning('Primary analysis failed, trying fallback', [
                    'output' => $process->getOutput(),
                    'error' => $process->getErrorOutput()
                ]);
                
                $output = null;
                $success = false;
                
                // Try fallback analyzer first (no numpy)
                if ($fallbackScript && file_exists($fallbackScript)) {
                    Log::info('Attempting fallback analysis (no numpy)', [
                        'fallback_script' => $fallbackScript
                    ]);
                    
                    $fallbackProcess = new Process([
                        $wrapperScript,
                        $fallbackScript,
                        $filePath
                    ]);
                    
                    $fallbackProcess->setEnv([
                        'PYTHONHASHSEED' => '0'
                    ]);
                    
                    $fallbackProcess->setTimeout(30);
                    $fallbackProcess->run();
                    
                    if ($fallbackProcess->isSuccessful()) {
                        $output = $fallbackProcess->getOutput();
                        $success = true;
                        Log::info('Fallback analysis (no numpy) succeeded');
                    } else {
                        Log::warning('Fallback analysis (no numpy) failed', [
                            'error' => $fallbackProcess->getErrorOutput()
                        ]);
                    }
                }
                
                // If fallback failed, try direct Python execution
                if (!$success && $fallbackScript && file_exists($fallbackScript)) {
                    Log::info('Attempting direct Python execution', [
                        'python_path' => $pythonPath,
                        'script' => $fallbackScript
                    ]);
                    
                    $directProcess = new Process([
                        $pythonPath,
                        $fallbackScript,
                        $filePath
                    ]);
                    
                    $directProcess->setEnv([
                        'PYTHONHASHSEED' => '0'
                    ]);
                    
                    $directProcess->setTimeout(30);
                    $directProcess->run();
                    
                    if ($directProcess->isSuccessful()) {
                        $output = $directProcess->getOutput();
                        $success = true;
                        Log::info('Direct Python execution succeeded');
                    } else {
                        Log::error('Direct Python execution failed', [
                            'error' => $directProcess->getErrorOutput()
                        ]);
                    }
                }
                
                if (!$success) {
                    Log::error('All analysis methods failed', [
                        'primary_error' => $process->getErrorOutput(),
                    ]);
                    throw new \Exception('Analysis failed: ' . $process->getErrorOutput());
                }
            } else {
                $output = $process->getOutput();
            }
            $result = json_decode($output, true);

            if (json_last_error() !== JSON_ERROR_NONE) {
                throw new \Exception('Invalid analyzer output: ' . json_last_error_msg());
            }

            // Store analysis result
            $analysisResult = $fileUpload->analysisResult;
            if ($analysisResult) {
                $analysisResult->update([
                    'analyzer_type' => $extension,
                    'analysis_data' => $result
                ]);
            } else {
                $analysisResult = new FileAnalysisResult([
                    'file_upload_id' => $fileUpload->id,
                    'analyzer_type' => $extension,
                    'analysis_data' => $result
                ]);
                $analysisResult->save();
            }

            // Update file status
            $fileUpload->update([
                'status' => 'analyzed',
                'processed_at' => now()
            ]);

            // Check for specific quality issues and create warnings
            if ($extension === 'stl' && isset($result['quality'])) {
                $quality = $result['quality'];

                if (!$quality['is_watertight']) {
                    FileError::create([
                        'file_upload_id' => $fileUpload->id,
                        'error_message' => 'The STL model is not watertight (has ' . $quality['boundary_edges'] . ' open edges)',
                        'stack_trace' => null,
                        'occurred_at' => now()
                    ]);
                }

                if (!$quality['is_manifold']) {
                    FileError::create([
                        'file_upload_id' => $fileUpload->id,
                        'error_message' => 'The STL model has non-manifold edges (' . $quality['non_manifold_edges'] . ' found)',
                        'stack_trace' => null,
                        'occurred_at' => now()
                    ]);
                }
            }

            // Return appropriate response based on context
            if (app()->runningInConsole()) {
                return response()->json([
                    'status' => 'success',
                    'data' => $result,
                    'metadata' => [
                        'processing_time' => $result['processing_time'] ?? null,
                        'analyzer_version' => '1.0',
                        'file_type' => $extension
                    ]
                ]);
            }

            // If request wants JSON, return it
            if (request()->expectsJson()) {
                return response()->json([
                    'status' => 'success',
                    'data' => $result,
                    'metadata' => [
                        'processing_time' => $result['processing_time'] ?? null,
                        'analyzer_version' => '1.0',
                        'file_type' => $extension
                    ]
                ]);
            }

            // Otherwise return Inertia response
            return back()->with('success', 'File analysis completed successfully.');

        } catch (\Exception $e) {
            // Log the error with full context
            Log::error('File analysis failed', [
                'file_id' => $fileUpload->id,
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);

            // Create an error record
            FileError::create([
                'file_upload_id' => $fileUpload->id,
                'error_message' => 'File analysis failed: ' . $e->getMessage(),
                'stack_trace' => $e->getTraceAsString(),
                'occurred_at' => now()
            ]);

            // Update file status
            $fileUpload->update([
                'status' => 'error',
                'processed_at' => now()
            ]);

            // Return appropriate response based on context
            if (app()->runningInConsole()) {
                return response()->json([
                    'status' => 'error',
                    'message' => $e->getMessage(),
                    'details' => [
                        'file_type' => $extension ?? 'unknown',
                        'analyzer' => basename($analyzerScript ?? 'unknown')
                    ]
                ], 422);
            }

            // If request wants JSON, return it
            if (request()->expectsJson()) {
                return response()->json([
                    'status' => 'error',
                    'message' => $e->getMessage(),
                    'details' => [
                        'file_type' => $extension ?? 'unknown',
                        'analyzer' => basename($analyzerScript ?? 'unknown')
                    ]
                ], 422);
            }

            // Otherwise return Inertia response
            return back()->with('error', 'Analysis failed: ' . $e->getMessage());
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
