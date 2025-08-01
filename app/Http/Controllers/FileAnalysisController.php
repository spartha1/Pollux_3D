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

        // Allow re-analysis for any status when not running in console
        if ($fileUpload->status === 'processing') {
            return back()->with('error', 'File is currently being processed. Please wait.');
        }

        // Update status
        $fileUpload->update(['status' => 'processing']);

        try {
            $filePath = storage_path('app/' . $fileUpload->storage_path);
            $extension = strtolower(pathinfo($filePath, PATHINFO_EXTENSION));

            // Get the Python executable path - try multiple methods for flexibility
            $pythonPath = $this->getPythonExecutablePath();

            if (!$pythonPath || !file_exists($pythonPath)) {
                throw new \Exception("Python executable not found. Tried paths: " . implode(', ', $this->getAllPossiblePythonPaths()));
            }

            // Select the appropriate analyzer based on file extension
            if ($extension === 'stl') {
                // FORCE manufacturing analyzer for ALL STL files - no exceptions
                $analyzerScript = app_path('Services/FileAnalyzers/analyze_stl_manufacturing.py');
                Log::info('STL file detected - FORCING manufacturing analyzer', [
                    'forced_script' => $analyzerScript,
                    'file_id' => $fileUpload->id,
                    'original_filename' => $fileUpload->filename_original
                ]);
            } else {
                $analyzerScript = match($extension) {
                    'step', 'stp' => app_path('Services/FileAnalyzers/analyze_step_simple.py'),
                    'dxf', 'dwg' => app_path('Services/FileAnalyzers/analyze_dxf_dwg.py'),
                    'eps', 'ai' => app_path('Services/FileAnalyzers/analyze_ai_eps.py'),
                    default => throw new \Exception("Unsupported file type: {$extension}")
                };
            }

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

            // For STL files, ALWAYS use direct Python execution with manufacturing analyzer
            if ($extension === 'stl') {
                Log::info('STL file detected - forcing manufacturing analyzer', [
                    'file_id' => $fileUpload->id,
                    'python_path' => $pythonPath,
                    'script' => $analyzerScript,
                    'file_path' => $filePath
                ]);
                
                // Use the dedicated batch script for manufacturing analysis
                $batchScript = base_path('run_manufacturing_analyzer.bat');
                $relativePath = str_replace('/', '\\', $fileUpload->storage_path);
                $filePathForCmd = "storage\\app\\{$relativePath}";
                
                Log::info("Using dedicated batch script for manufacturing analyzer", [
                    'batch_script' => $batchScript,
                    'file_path' => $filePathForCmd,
                    'file_id' => $fileUpload->id
                ]);
                
                $process = new Process([$batchScript, $filePathForCmd]);
                $process->setWorkingDirectory(base_path());
                $process->setTimeout(120); // 2 minutes for manufacturing analysis
                $process->run();
                
                Log::info('Manufacturing analyzer execution completed', [
                    'exit_code' => $process->getExitCode(),
                    'successful' => $process->isSuccessful(),
                    'output_length' => strlen($process->getOutput()),
                    'error_length' => strlen($process->getErrorOutput())
                ]);
                
                if (!$process->isSuccessful()) {
                    Log::error('Manufacturing analyzer failed - detailed error', [
                        'exit_code' => $process->getExitCode(),
                        'command' => $process->getCommandLine(),
                        'output' => $process->getOutput(),
                        'error' => $process->getErrorOutput(),
                        'working_directory' => $process->getWorkingDirectory()
                    ]);
                    
                    // Only use fallback if manufacturing analyzer completely failed
                    $fallbackScript = app_path('Services/FileAnalyzers/analyze_stl_no_numpy.py');
                    if (file_exists($fallbackScript)) {
                        Log::warning('Attempting fallback analyzer (manufacturing metrics will be missing)', [
                            'fallback_script' => $fallbackScript
                        ]);
                        
                        $fallbackProcess = new Process([
                            $pythonPath,
                            $fallbackScript,
                            $filePath
                        ]);
                        
                        $fallbackProcess->setEnv(['PYTHONHASHSEED' => '0']);
                        $fallbackProcess->setTimeout(30);
                        $fallbackProcess->run();
                        
                        if ($fallbackProcess->isSuccessful()) {
                            $output = $fallbackProcess->getOutput();
                            Log::warning('Fallback analysis succeeded - manufacturing metrics missing', [
                                'output_preview' => substr($output, 0, 200) . '...'
                            ]);
                        } else {
                            Log::error('Both analyzers failed', [
                                'manufacturing_error' => $process->getErrorOutput(),
                                'fallback_error' => $fallbackProcess->getErrorOutput()
                            ]);
                            throw new \Exception('Both manufacturing and fallback analyzers failed. Manufacturing: ' . $process->getErrorOutput() . ' | Fallback: ' . $fallbackProcess->getErrorOutput());
                        }
                    } else {
                        throw new \Exception('Manufacturing analyzer failed and no fallback available: ' . $process->getErrorOutput());
                    }
                } else {
                    $output = $process->getOutput();
                    
                    Log::info('Raw manufacturing analyzer output', [
                        'raw_output_length' => strlen($output),
                        'raw_output_preview' => substr($output, 0, 500),
                        'contains_manufacturing_raw' => strpos($output, 'manufacturing') !== false
                    ]);
                    
                    // Clean the output to extract only JSON
                    $cleanOutput = $this->extractJsonFromOutput($output);
                    
                    Log::info('Cleaned manufacturing analyzer output', [
                        'clean_output_length' => strlen($cleanOutput),
                        'clean_output_preview' => substr($cleanOutput, 0, 500),
                        'contains_manufacturing_clean' => strpos($cleanOutput, 'manufacturing') !== false
                    ]);
                    
                    // Use the cleaned output
                    $output = $cleanOutput;
                    
                    Log::info('Manufacturing analyzer succeeded', [
                        'output_preview' => substr($output, 0, 200) . '...',
                        'contains_manufacturing' => strpos($output, 'manufacturing') !== false,
                        'contains_weight_estimates' => strpos($output, 'weight_estimates') !== false
                    ]);
                }
            } else {
                // For non-STL files, use the conda wrapper
                $wrapperScript = app_path('Services/FileAnalyzers/run_with_conda.bat');
                $process = new Process([
                    $wrapperScript,
                    $analyzerScript,
                    $filePath
                ]);

                $process->setEnv([
                    'PYTHONHASHSEED' => '0'
                ]);

                $timeout = 30;
                $process->setTimeout($timeout);
                $process->run();

                if (!$process->isSuccessful()) {
                    throw new \Exception('Analysis failed: ' . $process->getErrorOutput());
                } else {
                    $output = $process->getOutput();
                }
            }
            $result = json_decode($output, true);

            if (json_last_error() !== JSON_ERROR_NONE) {
                throw new \Exception('Invalid analyzer output - JSON decode error: ' . json_last_error_msg() . '. Output preview: ' . substr($output, 0, 500));
            }

            // For STL files, validate that manufacturing data is present
            if ($extension === 'stl') {
                $hasManufacturing = isset($result['manufacturing']);
                $hasWeightEstimates = isset($result['manufacturing']['weight_estimates']);
                
                Log::info('STL analysis result validation', [
                    'has_manufacturing' => $hasManufacturing,
                    'has_weight_estimates' => $hasWeightEstimates,
                    'manufacturing_keys' => $hasManufacturing ? array_keys($result['manufacturing']) : [],
                    'result_keys' => array_keys($result)
                ]);
                
                if (!$hasManufacturing) {
                    Log::warning('STL analysis completed but manufacturing data missing', [
                        'available_keys' => array_keys($result),
                        'analyzer_used' => basename($analyzerScript),
                        'output_preview' => substr($output, 0, 300)
                    ]);
                    
                    // This suggests the fallback analyzer was used instead
                    // Log this as a potential issue for monitoring
                    Log::warning('Manufacturing data missing - fallback analyzer may have been used');
                }
                
                // Validate manufacturing data structure if present
                if ($hasManufacturing) {
                    $requiredKeys = ['cutting_perimeters', 'work_planes', 'complexity', 'weight_estimates'];
                    $missingKeys = [];
                    
                    foreach ($requiredKeys as $key) {
                        if (!isset($result['manufacturing'][$key])) {
                            $missingKeys[] = $key;
                        }
                    }
                    
                    if (!empty($missingKeys)) {
                        Log::warning('Manufacturing data incomplete', [
                            'missing_keys' => $missingKeys,
                            'available_keys' => array_keys($result['manufacturing'])
                        ]);
                    } else {
                        Log::info('✅ Manufacturing data validation passed - all required keys present');
                    }
                }
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
        // Skip authorization when running from CLI (Artisan commands)
        if (!app()->runningInConsole()) {
            $this->authorize('update', $fileUpload);
        }

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

    /**
     * Get Python executable path using multiple detection methods
     */
    private function getPythonExecutablePath()
    {
        $possiblePaths = $this->getAllPossiblePythonPaths();
        
        foreach ($possiblePaths as $path) {
            if ($path && file_exists($path)) {
                Log::info('Found Python executable', ['path' => $path]);
                return $path;
            }
        }
        
        return null;
    }

    /**
     * Get all possible Python executable paths for different environments
     */
    private function getAllPossiblePythonPaths()
    {
        $paths = [];
        
        // 1. From Laravel config (current method)
        $configPath = config('services.python.executable');
        if ($configPath) {
            $paths[] = $configPath;
        }
        
        // 2. From CONDA_PREFIX environment variable (most reliable in conda environments)
        $condaPrefix = getenv('CONDA_PREFIX');
        if ($condaPrefix) {
            $paths[] = $condaPrefix . DIRECTORY_SEPARATOR . 'python.exe';
        }
        
        // 3. Try current conda environment from PATH
        $pythonFromPath = $this->findPythonInPath();
        if ($pythonFromPath) {
            $paths[] = $pythonFromPath;
        }
        
        // 4. Common conda installation paths
        $username = getenv('USERNAME') ?: getenv('USER');
        if ($username) {
            $commonPaths = [
                "C:\\Users\\{$username}\\miniconda3\\envs\\pollux-preview-env\\python.exe",
                "C:\\Users\\{$username}\\anaconda3\\envs\\pollux-preview-env\\python.exe",
                "C:\\miniconda3\\envs\\pollux-preview-env\\python.exe",
                "C:\\anaconda3\\envs\\pollux-preview-env\\python.exe",
            ];
            $paths = array_merge($paths, $commonPaths);
        }
        
        // 5. System Python as last resort
        $paths[] = 'python';
        $paths[] = 'python.exe';
        
        return array_filter(array_unique($paths));
    }

    /**
     * Find Python executable in system PATH
     */
    private function findPythonInPath()
    {
        // Try to find python in PATH
        $process = new Process(['where', 'python']);
        $process->run();
        
        if ($process->isSuccessful()) {
            $output = trim($process->getOutput());
            $lines = explode("\n", $output);
            
            // Return the first python found that contains 'pollux-preview-env'
            foreach ($lines as $line) {
                $line = trim($line);
                if (strpos($line, 'pollux-preview-env') !== false) {
                    return $line;
                }
            }
            
            // If no conda env found, return the first python
            return $lines[0] ?? null;
        }
        
        return null;
    }
    
    /**
     * Extract clean JSON from mixed output that might contain PowerShell messages
     */
    private function extractJsonFromOutput($output)
    {
        // Look for the first opening brace and last closing brace
        $firstBrace = strpos($output, '{');
        $lastBrace = strrpos($output, '}');
        
        if ($firstBrace !== false && $lastBrace !== false && $lastBrace > $firstBrace) {
            $jsonPart = substr($output, $firstBrace, $lastBrace - $firstBrace + 1);
            
            // Test if this is valid JSON
            $decoded = json_decode($jsonPart, true);
            if (json_last_error() === JSON_ERROR_NONE) {
                return $jsonPart;
            }
        }
        
        // If extraction failed, return original output
        return $output;
    }
}
