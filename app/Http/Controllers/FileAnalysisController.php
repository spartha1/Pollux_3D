<?php

namespace App\Http\Controllers;

use App\Models\FileUpload;
use App\Models\FileAnalysisResult;
use Illuminate\Http\Request;
use Illuminate\Foundation\Auth\Access\AuthorizesRequests;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;
use Illuminate\Support\Facades\Log;

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

        // Call Python analysis service
        $this->callAnalysisService($fileUpload);

        return back()->with('success', 'File analysis has been queued.');
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

    /**
     * Call the Python analysis service.
     */
    private function callAnalysisService(FileUpload $fileUpload)
    {
        try {
            $filePath = storage_path('app/' . $fileUpload->storage_path);

            $process = new Process([
                '/home/jerardo/miniconda3/envs/occ310/bin/python',
                base_path('app/Services/FileAnalyzers/main.py'),
                $filePath
            ]);

            $process->setTimeout(300); // 5 minutos
            $process->run();

            if (!$process->isSuccessful()) {
                throw new ProcessFailedException($process);
            }

            $data = json_decode($process->getOutput(), true);
            Log::info('📦 Datos recibidos del análisis:', $data);

            // Guardar resultados en DB
            $fileUpload->analysisResult()->create([
                'dimensions' => $data['dimensions'] ?? null,
                'volume' => $data['volume'] ?? null,
                'area' => $data['area'] ?? null,
                'layers' => $data['layers'] ?? null,
                'metadata' => $data['metadata'] ?? null,
                'analysis_time_ms' => $data['analysis_time_ms'] ?? null,
            ]);

            $fileUpload->update([
                'status' => 'processed',
                'processed_at' => now(),
            ]);
        } catch (\Exception $e) {
            $fileUpload->errors()->create([
                'error_message' => $e->getMessage(),
                'stack_trace' => $e->getTraceAsString(),
            ]);

            $fileUpload->update(['status' => 'failed']);
        }
    }
}
