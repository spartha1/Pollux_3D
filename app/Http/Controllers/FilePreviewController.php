<?php

namespace App\Http\Controllers;

use App\Models\FileUpload;
use App\Models\FilePreview;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Illuminate\Foundation\Auth\Access\AuthorizesRequests;

class FilePreviewController extends Controller
{
    use AuthorizesRequests;
    /**
     * Generate previews for a file upload.
     */
    public function generate(FileUpload $fileUpload, Request $request)
    {
        $this->authorize('update', $fileUpload);

        $request->validate([
            'render_type' => 'in:2d,wireframe,3d'
        ]);

        $renderType = $request->input('render_type', '2d');

        // Check if preview already exists
        $existingPreview = $fileUpload->previews()
            ->where('render_type', $renderType)
            ->first();

        if ($existingPreview) {
            return response()->json([
                'message' => 'Preview already exists',
                'preview' => $existingPreview
            ]);
        }

        // Verify file exists before generating preview
        if (!Storage::disk($fileUpload->disk)->exists($fileUpload->storage_path)) {
            return response()->json([
                'message' => 'File not found',
                'error' => 'The requested file does not exist'
            ], 404);
        }

        // Call preview generation service
        $preview = $this->generatePreview($fileUpload, $renderType);

        return response()->json([
            'message' => 'Preview generated successfully',
            'preview' => $preview
        ]);
    }

    /**
     * Get all previews for a file upload.
     */
    public function index(FileUpload $fileUpload)
    {
        $this->authorize('view', $fileUpload);

        $previews = $fileUpload->previews()->get();

        return response()->json([
            'file_id' => $fileUpload->id,
            'previews' => $previews
        ]);
    }

    /**
     * Show a specific preview image.
     */
    public function show(FileUpload $fileUpload, FilePreview $preview)
    {
        $this->authorize('view', $fileUpload);

        // Ensure preview belongs to the file
        if ($preview->file_upload_id !== $fileUpload->id) {
            abort(404);
        }

        $path = Storage::disk('public')->path($preview->image_path);

        if (!file_exists($path)) {
            abort(404);
        }

        return response()->file($path);
    }

    /**
     * Delete a preview.
     */
    public function destroy(FileUpload $fileUpload, FilePreview $preview)
    {
        $this->authorize('update', $fileUpload);

        // Ensure preview belongs to the file
        if ($preview->file_upload_id !== $fileUpload->id) {
            abort(404);
        }

        // Delete physical file
        Storage::disk('public')->delete($preview->image_path);

        // Delete record
        $preview->delete();

        return response()->json([
            'message' => 'Preview deleted successfully'
        ]);
    }

    /**
     * Generate preview using Python service.
     */
    private function generatePreview(FileUpload $fileUpload, string $renderType)
    {
        try {
            // Get preview service URL from config (default to localhost:8051)
            $previewServiceUrl = config('services.preview.url', 'http://localhost:8051');

            // Get the absolute file path
            $filePath = Storage::disk($fileUpload->disk)->path($fileUpload->storage_path);

            // Prepare request payload matching FastAPI schema
            $payload = [
                'file_path' => $filePath,
                'preview_type' => $renderType,
                'width' => 800,
                'height' => 600,
                'format' => 'png'
            ];

            $response = Http::timeout(120)->post($previewServiceUrl . '/generate-preview', $payload);

            if ($response->successful()) {
                $data = $response->json();

                // Get the image data from the correct field
                $imageData = $data['preview_2d'] ?? null;
                
                if (!$imageData) {
                    throw new \Exception('No image data received from preview service');
                }

                // Save preview image
                $previewPath = 'previews/' . $fileUpload->id . '/' . Str::uuid() . '.png';
                Storage::disk('public')->put($previewPath, base64_decode($imageData));

                // Create preview record
                return $fileUpload->previews()->create([
                    'image_path' => $previewPath,
                    'render_type' => $renderType,
                ]);
            } else {
                throw new \Exception('Preview service returned error: ' . $response->body());
            }
        } catch (\Exception $e) {
            // Log error
            $fileUpload->errors()->create([
                'error_message' => 'Preview generation failed: ' . $e->getMessage(),
                'stack_trace' => $e->getTraceAsString(),
            ]);

            throw $e;
        }
    }
}
