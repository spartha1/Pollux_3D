<?php

namespace App\Http\Controllers;

use App\Models\FileUpload;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use Illuminate\Foundation\Auth\Access\AuthorizesRequests;
use Inertia\Inertia;

class FileUploadController extends Controller
{
    use AuthorizesRequests;
    /**
     * Display a listing of the user's file uploads.
     */
    public function index(Request $request)
    {
        $perPage = $request->get('per_page', 30); // Permitir personalizar, por defecto 30
        $perPage = in_array($perPage, [20, 30, 50, 100]) ? $perPage : 30; // Limitar opciones válidas
        
        $files = $request->user()->fileUploads()
            ->with(['analysisResult', 'previews'])
            ->latest()
            ->paginate($perPage);

        return Inertia::render('3d/index', [
            'files' => $files
        ]);
    }

    /**
     * Show the form for uploading a new file.
     */
    public function create()
    {
        return view('files.create');
    }

    /**
     * Store a newly uploaded file.
     */
    public function store(Request $request)
    {
        $request->validate([
            'file' => 'required|file|max:102400', // 100MB max
        ]);

        $file = $request->file('file');
        $extension = strtoupper($file->getClientOriginalExtension());
        $originalName = $file->getClientOriginalName();
        $storedName = Str::uuid() . '.' . $extension;

        // Store file in models directory under user's ID
        $relativePath = 'models/' . $request->user()->id;

        // Ensure the directory exists
        Storage::disk('local')->makeDirectory($relativePath);

        try {
            // Store the file with binary mode
            $path = $file->storeAs($relativePath, $storedName, [
                'disk' => 'local',
                'visibility' => 'private'
            ]);

            if (!$path) {
                Log::error('Failed to store file', [
                    'original_name' => $originalName,
                    'stored_name' => $storedName,
                    'path' => $relativePath
                ]);
                return back()->with('error', 'Failed to store file. Please try again.');
            }

            // Double check the file exists and is readable
            if (!Storage::disk('local')->exists($path)) {
                Log::error('File verification failed', [
                    'path' => $path,
                    'full_path' => Storage::disk('local')->path($path)
                ]);
                return back()->with('error', 'File upload failed verification. Please try again.');
            }

            // Verify file contents
            $fullPath = Storage::disk('local')->path($path);
            if (!file_exists($fullPath) || filesize($fullPath) === 0) {
                Log::error('File is empty or not accessible', [
                    'path' => $path,
                    'full_path' => $fullPath,
                    'exists' => file_exists($fullPath),
                    'size' => file_exists($fullPath) ? filesize($fullPath) : 'N/A'
                ]);
                return back()->with('error', 'File upload failed: empty or inaccessible file.');
            }

            // Log success
            Log::info('File stored successfully', [
                'original_name' => $originalName,
                'stored_name' => $storedName,
                'path' => $path,
                'full_path' => $fullPath,
                'size' => filesize($fullPath)
            ]);

            $fileUpload = $request->user()->fileUploads()->create([
                'uuid' => Str::uuid(),
                'filename_original' => $originalName,
                'filename_stored' => $storedName,
                'extension' => $extension,
                'mime_type' => $file->getMimeType(),
                'size' => $file->getSize(),
                'storage_path' => $path,
                'disk' => 'local',
                'status' => 'uploaded',
                'uploaded_at' => now(),
            ]);

            return redirect()->route('3d.show', ['fileUpload' => $fileUpload->id])
                ->with('success', 'File uploaded successfully. Processing will begin shortly.');

        } catch (\Exception $e) {
            Log::error('File upload failed', [
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
                'original_name' => $originalName,
                'stored_name' => $storedName
            ]);
            return back()->with('error', 'File upload failed: ' . $e->getMessage());
        }
    }

    /**
     * Display the specified file upload.
     */
    public function show(FileUpload $fileUpload)
    {
        $this->authorize('view', $fileUpload);

        $fileUpload->load(['analysisResult', 'previews', 'errors']);

        // Prepare metadata for the view
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

        // Prepare file data for the view
        $fileData = [
            'id' => $fileUpload->id,
            'filename_original' => $fileUpload->filename_original,
            'filename_stored' => $fileUpload->filename_stored,
            'extension' => $fileUpload->extension,
            'mime_type' => $fileUpload->mime_type,
            'size' => $fileUpload->size,
            'status' => $fileUpload->status,
            'created_at' => $fileUpload->created_at->format('Y-m-d H:i:s'),
            'uploadedAt' => $fileUpload->uploaded_at ? $fileUpload->uploaded_at->format('Y-m-d H:i:s') : null,
            'processedAt' => $fileUpload->processed_at ? $fileUpload->processed_at->format('Y-m-d H:i:s') : null,
            'processed_at' => $fileUpload->processed_at ? $fileUpload->processed_at->format('Y-m-d H:i:s') : null,
            'analysis_result' => $fileUpload->analysisResult ? $fileUpload->analysisResult->analysis_data : null,
            'errors' => $fileUpload->errors->map(function ($error) {
                return [
                    'error_message' => $error->error_message,
                    'stack_trace' => $error->stack_trace,
                ];
            }),
            'disk' => $fileUpload->disk,
            'storage_path' => $fileUpload->storage_path,
            'metadata' => $metadata,
        ];

        return Inertia::render('3d/show', [
            'fileUpload' => $fileData
        ]);
    }

    /**
     * Download the original file.
     */
    public function download(FileUpload $fileUpload)
    {
        $this->authorize('view', $fileUpload);

        $path = Storage::disk('local')->path($fileUpload->storage_path);

        if (!file_exists($path)) {
            abort(404, 'File not found');
        }

        return response()->file($path, [
            'Content-Type' => $fileUpload->mime_type,
            'Content-Disposition' => 'inline; filename="' . $fileUpload->filename_original . '"'
        ]);
    }

    /**
     * Remove the specified file upload.
     */
    public function destroy(FileUpload $fileUpload)
    {
        $this->authorize('delete', $fileUpload);

        // Delete physical file
        Storage::disk($fileUpload->disk)->delete($fileUpload->storage_path);

        // Delete previews
        foreach ($fileUpload->previews as $preview) {
            Storage::disk('public')->delete($preview->image_path);
        }

        // Delete record (cascades to related tables)
        $fileUpload->delete();

        return redirect()->route('3d.index')
            ->with('success', 'File deleted successfully.');
    }

    /**
     * Serve the STL file for 3D viewer.
     */
    public function serveFile(FileUpload $fileUpload)
    {
        $this->authorize('view', $fileUpload);

        $filePath = Storage::disk($fileUpload->disk)->path($fileUpload->storage_path);

        if (!file_exists($filePath)) {
            abort(404);
        }

        return response()->file($filePath, [
            'Content-Type' => $fileUpload->mime_type ?: 'application/octet-stream',
            'Access-Control-Allow-Origin' => '*', // Para permitir acceso desde el visor 3D
        ]);
    }
}
