<?php

namespace App\Http\Controllers;

use App\Models\FileUpload;
use App\Models\FilePreview;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
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
        Log::info('🔥 PREVIEW DEBUG: Generation started', [
            'file_id' => $fileUpload->id,
            'user_id' => Auth::id() ?? 'unauthenticated',
            'request_data' => $request->all(),
            'file_path' => $fileUpload->storage_path,
            'file_disk' => $fileUpload->disk
        ]);

        try {
            // TODO: Temporary disable authorization for testing
            // $this->authorize('update', $fileUpload);

            $request->validate([
                'render_type' => 'in:2d,wireframe,wireframe_2d,3d'
            ]);

            $renderType = $request->input('render_type', '2d');

            Log::info('🔥 PREVIEW DEBUG: Validation passed', [
                'file_id' => $fileUpload->id,
                'render_type' => $renderType,
                'file_path' => $fileUpload->storage_path,
                'file_disk' => $fileUpload->disk
            ]);

        // Check if preview already exists and is valid
        $existingPreview = $fileUpload->previews()
            ->where('render_type', $renderType)
            ->first();

        // For wireframe_2d, also check if wireframe exists (since they generate similar views)
        if ($renderType === 'wireframe_2d') {
            $wireframePreview = $fileUpload->previews()
                ->where('render_type', 'wireframe')
                ->first();
            
            if ($wireframePreview && Storage::disk('public')->exists($wireframePreview->image_path)) {
                Log::info('Reusing existing wireframe preview for wireframe_2d request', [
                    'file_id' => $fileUpload->id,
                    'wireframe_preview_id' => $wireframePreview->id
                ]);
                
                // Create a new wireframe_2d record pointing to the same image
                $newPreview = $fileUpload->previews()->create([
                    'image_path' => $wireframePreview->image_path,
                    'render_type' => 'wireframe_2d',
                ]);
                
                return response()->json([
                    'message' => 'Preview reused from existing wireframe',
                    'preview' => $newPreview
                ]);
            }
        }

        if ($existingPreview && Storage::disk('public')->exists($existingPreview->image_path)) {
            Log::info('Existing preview found', [
                'file_id' => $fileUpload->id,
                'render_type' => $renderType,
                'preview_id' => $existingPreview->id
            ]);
            return response()->json([
                'message' => 'Preview already exists',
                'preview' => $existingPreview
            ]);
        }

        // If preview exists but file is missing, delete the record and regenerate
        if ($existingPreview) {
            Log::info('Deleting invalid existing preview', [
                'file_id' => $fileUpload->id,
                'render_type' => $renderType,
                'preview_id' => $existingPreview->id
            ]);
            $existingPreview->delete();
        }

        // Verify file exists before generating preview
        if (!Storage::disk($fileUpload->disk)->exists($fileUpload->storage_path)) {
            Log::error('Source file not found', [
                'file_id' => $fileUpload->id,
                'disk' => $fileUpload->disk,
                'storage_path' => $fileUpload->storage_path
            ]);
            return response()->json([
                'message' => 'File not found',
                'error' => 'The requested file does not exist'
            ], 404);
        }

        Log::info('Starting preview service call', [
            'file_id' => $fileUpload->id,
            'render_type' => $renderType
        ]);

        // Call preview generation service
        try {
            $preview = $this->generatePreview($fileUpload, $renderType);
            
            Log::info('Preview generation completed successfully', [
                'file_id' => $fileUpload->id,
                'render_type' => $renderType,
                'preview_id' => $preview->id
            ]);

            return response()->json([
                'message' => 'Preview generated successfully',
                'preview' => $preview
            ]);
        } catch (\Exception $e) {
            Log::error('🔥 PREVIEW DEBUG: Exception in inner try block', [
                'file_id' => $fileUpload->id,
                'render_type' => $renderType,
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return response()->json([
                'message' => 'Preview generation failed',
                'error' => $e->getMessage()
            ], 500);
        }
        } catch (\Exception $e) {
            Log::error('🔥 PREVIEW DEBUG: Exception in main try block', [
                'file_id' => $fileUpload->id,
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return response()->json([
                'message' => 'Preview generation failed',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get all previews for a file upload.
     */
    public function index(FileUpload $fileUpload)
    {
        // TODO: Temporary disable authorization for testing
        // $this->authorize('view', $fileUpload);

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
        // TODO: Temporary disable authorization for testing
        // $this->authorize('view', $fileUpload);

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
        // TODO: Temporary disable authorization for testing
        // $this->authorize('update', $fileUpload);

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
            // Get preview service URL from config (default to localhost:8052 - hybrid server)
            $previewServiceUrl = config('services.preview.url', 'http://localhost:8052');

            // Use relative path from Laravel storage - the Python server will handle absolute conversion
            $filePath = $fileUpload->storage_path;

            // Verify file exists using Laravel's Storage facade
            if (!Storage::disk($fileUpload->disk)->exists($fileUpload->storage_path)) {
                Log::error('File does not exist in Laravel storage', [
                    'file_id' => $fileUpload->id,
                    'disk' => $fileUpload->disk,
                    'storage_path' => $fileUpload->storage_path
                ]);
                throw new \Exception('File does not exist in storage: ' . $fileUpload->storage_path);
            }

            Log::info('🔥 PREVIEW DEBUG: About to call Python service with relative path', [
                'file_id' => $fileUpload->id,
                'disk' => $fileUpload->disk,
                'storage_path' => $fileUpload->storage_path,
                'relative_path' => $filePath,
                'render_type' => $renderType
            ]);

            // Prepare request payload matching FastAPI schema
            $payload = [
                'file_id' => (string) $fileUpload->id,
                'file_path' => $filePath, // Send relative path, Python will convert to absolute
                'preview_type' => $renderType,
                'width' => 800,
                'height' => 600,
                'background_color' => '#FFFFFF',
                'file_type' => $fileUpload->extension
            ];

            $response = Http::timeout(120)
                ->withHeaders([
                    'Content-Type' => 'application/json',
                    'Accept' => 'application/json'
                ])
                ->post($previewServiceUrl . '/generate_preview', $payload);

            // Log the full request and response for debugging
            Log::info('Preview service request', [
                'url' => $previewServiceUrl . '/generate_preview',
                'payload' => $payload,
                'response_status' => $response->status(),
                'response_headers' => $response->headers(),
                'response_size' => strlen($response->body())
            ]);

            if ($response->successful()) {
                $responseBody = $response->body();
                Log::info('Raw response body preview', [
                    'body_length' => strlen($responseBody),
                    'first_500_chars' => substr($responseBody, 0, 500),
                    'last_100_chars' => substr($responseBody, -100),
                    'response_headers' => $response->headers(),
                    'content_type' => $response->header('Content-Type')
                ]);
                
                try {
                    $data = $response->json();
                    Log::info('🔥 FULL RESPONSE DEBUG', [
                        'response_body_raw' => $responseBody,
                        'parsed_data' => $data,
                        'data_keys' => array_keys($data ?? []),
                        'response_successful' => $response->successful(),
                        'response_status' => $response->status()
                    ]);
                } catch (\Exception $jsonError) {
                    Log::error('JSON parse error', [
                        'error' => $jsonError->getMessage(),
                        'raw_body' => $responseBody,
                        'response_status' => $response->status(),
                        'response_headers' => $response->headers()
                    ]);
                    throw new \Exception('Failed to parse JSON response from preview service: ' . $jsonError->getMessage());
                }
                
                // Log the response structure for debugging
                Log::info('Preview service response structure', [
                    'response_keys' => array_keys($data ?? []),
                    'has_success' => isset($data['success']),
                    'success_value' => $data['success'] ?? null,
                    'has_image_data' => isset($data['image_data']),
                    'image_data_length' => isset($data['image_data']) ? strlen($data['image_data']) : 0,
                    'data_type' => gettype($data['image_data'] ?? null)
                ]);

                // Check if the Python server indicates success
                $isSuccess = ($data['success'] ?? false) == 1 || ($data['success'] ?? false) === true;
                
                if (!$isSuccess) {
                    Log::error('Python server reported failure', [
                        'response_data' => $data,
                        'success_field' => $data['success'] ?? 'not set'
                    ]);
                    throw new \Exception('Preview service reported failure: ' . ($data['message'] ?? 'Unknown error'));
                }

                // Get the image data from the correct field
                $imageData = $data['image_data'] ?? null;
                
                Log::info('Checking image data', [
                    'image_data_exists' => isset($data['image_data']),
                    'image_data_null' => is_null($imageData),
                    'image_data_type' => gettype($imageData),
                    'image_data_length' => is_string($imageData) ? strlen($imageData) : 0,
                    'raw_image_data_preview' => is_string($imageData) ? substr($imageData, 0, 100) : 'not string'
                ]);
                
                if (!isset($data['image_data']) || !is_string($imageData) || strlen($imageData) < 100) {
                    Log::error('No image data in response', [
                        'response_data' => $data,
                        'payload' => $payload,
                        'image_data_isset' => isset($data['image_data']),
                        'image_data_type' => gettype($imageData),
                        'image_data_length' => is_string($imageData) ? strlen($imageData) : 0
                    ]);
                    throw new \Exception('No image data received from preview service');
                }

                // Save preview image with correct naming convention
                if ($renderType === '2d') {
                    $filename = 'stl_2d_preview_' . substr(md5($fileUpload->id . time()), 0, 8) . '.png';
                } elseif ($renderType === 'wireframe') {
                    $filename = 'stl_wireframe_preview_' . substr(md5($fileUpload->id . time()), 0, 8) . '.png';
                } else {
                    $filename = 'stl_' . $renderType . '_preview_' . substr(md5($fileUpload->id . time()), 0, 8) . '.png';
                }
                
                // Save in the correct directory structure: storage/app/previews/
                $previewPath = 'previews/' . $filename;
                Storage::disk('local')->put($previewPath, base64_decode($imageData));
                
                // Create symlink path for public access: public/storage/previews/{id}/{filename}
                $publicPreviewPath = 'previews/' . $fileUpload->id . '/' . $filename;
                
                // Ensure the public directory exists
                if (!Storage::disk('public')->exists('previews/' . $fileUpload->id)) {
                    Storage::disk('public')->makeDirectory('previews/' . $fileUpload->id);
                }
                
                // Copy to public storage for web access
                Storage::disk('public')->put($publicPreviewPath, base64_decode($imageData));

                // Create preview record with public path
                return $fileUpload->previews()->create([
                    'image_path' => $publicPreviewPath,
                    'render_type' => $renderType,
                ]);
            } else {
                Log::error('Preview service returned non-successful response', [
                    'status' => $response->status(),
                    'headers' => $response->headers(),
                    'body' => $response->body(),
                    'payload' => $payload
                ]);
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
