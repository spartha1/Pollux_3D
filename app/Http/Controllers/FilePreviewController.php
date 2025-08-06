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
                'render_type' => $renderType  // Use 'render_type' not 'preview_type'
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
                $errorBody = $response->body();
                $errorMessage = 'Error del servidor de preview';

                // Intentar parsear respuesta JSON del analizador mejorado
                try {
                    // El errorBody puede contener JSON anidado del servidor Python
                    $errorData = json_decode($errorBody, true);

                    // Si hay un 'detail' que contiene JSON, parsearlo también
                    if (isset($errorData['detail']) && is_string($errorData['detail']) && strpos($errorData['detail'], '{') !== false) {
                        // Extraer JSON del detail
                        if (preg_match('/\{.*\}/', $errorData['detail'], $matches)) {
                            $nestedJson = json_decode($matches[0], true);
                            if (json_last_error() === JSON_ERROR_NONE) {
                                $errorData = $nestedJson;
                            }
                        }
                    }

                    if (json_last_error() === JSON_ERROR_NONE && isset($errorData['error'])) {

                        // Crear mensaje amigable para el usuario
                        $userMessage = "No se pudo generar la vista previa de este archivo STEP.";

                        // Priorizar información diagnóstica del nuevo sistema mejorado
                        if (isset($errorData['diagnostic_info']) && isset($errorData['analysis_type']) && $errorData['analysis_type'] === 'comprehensive_diagnostic') {
                            $diagnostic = $errorData['diagnostic_info'];

                            // Información del archivo STEP
                            $metadata = $diagnostic['step_metadata'] ?? [];
                            $structure = $diagnostic['structure_analysis'] ?? [];
                            $bounds = $diagnostic['coordinate_bounds'] ?? [];
                            $entities = $diagnostic['step_entities'] ?? [];
                            $totalEntities = $diagnostic['total_step_entities'] ?? 0;
                            $complexity = $diagnostic['file_complexity'] ?? 'unknown';

                            // Crear mensaje detallado basado en la información extraída
                            $userMessage = "✅ <strong>Archivo STEP válido</strong> - información detallada extraída:<br><br>";

                            // Información del archivo
                            if (!empty($metadata)) {
                                $userMessage .= "📄 <strong>Información del archivo:</strong><br>";
                                if (isset($metadata['description'])) {
                                    $userMessage .= "• Descripción: {$metadata['description']}<br>";
                                }
                                if (isset($metadata['schema'])) {
                                    $userMessage .= "• Schema: {$metadata['schema']}<br>";
                                }
                                if (isset($metadata['timestamp'])) {
                                    $userMessage .= "• Creado: {$metadata['timestamp']}<br>";
                                }
                                $userMessage .= "<br>";
                            }

                            // Dimensiones aproximadas
                            if (isset($bounds['approximate_dimensions'])) {
                                $dims = $bounds['approximate_dimensions'];
                                $userMessage .= "📐 <strong>Dimensiones aproximadas:</strong><br>";
                                $userMessage .= "• {$dims['width']} × {$dims['height']} × {$dims['depth']} mm<br>";
                                if (isset($bounds['coordinate_points_analyzed'])) {
                                    $userMessage .= "• Basado en {$bounds['coordinate_points_analyzed']} puntos analizados<br>";
                                }
                                $userMessage .= "<br>";
                            }

                            // Análisis de contenido
                            $userMessage .= "🔍 <strong>Contenido detectado:</strong><br>";
                            $userMessage .= "• Total entidades STEP: " . number_format($totalEntities) . "<br>";

                            if ($structure['has_basic_geometry'] ?? false) {
                                $geomCount = 0;
                                $geomTypes = [];
                                foreach (['cartesian_point', 'line', 'circle', 'b_spline_curve', 'surface'] as $type) {
                                    if (isset($entities[$type]) && $entities[$type] > 0) {
                                        $geomCount += $entities[$type];
                                        $geomTypes[] = str_replace('_', ' ', $type) . " ({$entities[$type]})";
                                    }
                                }
                                if ($geomCount > 0) {
                                    $userMessage .= "• Geometría: " . implode(', ', array_slice($geomTypes, 0, 3));
                                    if (count($geomTypes) > 3) $userMessage .= ' y más...';
                                    $userMessage .= "<br>";
                                }
                            }

                            if ($structure['has_topology'] ?? false) {
                                $topoCount = ($entities['advanced_face'] ?? 0) + ($entities['closed_shell'] ?? 0) + ($entities['manifold_solid_brep'] ?? 0);
                                if ($topoCount > 0) {
                                    $userMessage .= "• Topología: {$topoCount} elementos de superficie/sólido<br>";
                                }
                            }

                            if ($structure['has_product_structure'] ?? false) {
                                $prodCount = ($entities['product'] ?? 0);
                                if ($prodCount > 0) {
                                    $userMessage .= "• Productos: {$prodCount} elementos<br>";
                                }
                            }

                            $userMessage .= "• Complejidad: " . ucfirst($complexity) . "<br><br>";

                            // Por qué no se pudo generar la vista 3D
                            $userMessage .= "⚠️ <strong>Vista 3D no disponible:</strong><br>";
                            $userMessage .= "• El archivo contiene geometría válida pero incompatible con el motor PythonOCC<br>";
                            $userMessage .= "• Esto es común en archivos con superficies NURBS complejas o geometría paramétrica avanzada<br><br>";

                            // Sugerencias específicas
                            $userMessage .= "💡 <strong>Soluciones recomendadas:</strong><br>";
                            if ($complexity === 'high' || $totalEntities > 5000) {
                                $userMessage .= "• <strong>Simplificar geometría</strong>: Reduce la complejidad en tu software CAD<br>";
                                $userMessage .= "• <strong>Exportar a STL</strong>: Para visualización, usa formato STL que es más compatible<br>";
                            }
                            $userMessage .= "• <strong>Configuración STEP conservadora</strong>: Usa configuraciones más simples al exportar desde CAD<br>";
                            $userMessage .= "• <strong>Visor CAD externo</strong>: Usa un software CAD profesional para visualización completa<br>";

                        }
                        // Fallback al sistema anterior para compatibilidad
                        elseif (isset($errorData['fallback_analysis'])) {
                            $fallback = $errorData['fallback_analysis'];

                            // Verificar si el archivo es válido
                            if (isset($fallback['structure_analysis'])) {
                                $structure = $fallback['structure_analysis'];
                                $complexity = $structure['complexity_score'] ?? 0;
                                $hasGeometry = $structure['has_basic_geometry'] ?? false;
                                $hasTopology = $structure['has_topology'] ?? false;
                                $totalEntities = $fallback['total_step_entities'] ?? 0;

                                if ($hasGeometry && $hasTopology && $totalEntities > 1000) {
                                    $userMessage = "El archivo STEP es válido pero contiene geometría muy compleja ({$totalEntities} entidades) que no es compatible con el motor de visualización actual. ";
                                    $userMessage .= "Sugerencias: Simplifica la geometría en tu software CAD o considera convertir a un formato más simple como STL para visualización.";
                                } elseif ($hasGeometry) {
                                    $userMessage = "El archivo STEP es válido pero tiene problemas de compatibilidad con el motor de visualización. ";
                                    $userMessage .= "Intenta exportar el modelo con configuraciones STEP más conservadoras desde tu software CAD.";
                                } else {
                                    $userMessage = "El archivo STEP no contiene geometría compatible con el visualizador. ";
                                    $userMessage .= "Verifica que el archivo fue exportado correctamente desde tu software CAD.";
                                }
                            }

                            // Información adicional sobre el archivo
                            if (isset($fallback['file_info']['file_size_mb'])) {
                                $sizeMb = $fallback['file_info']['file_size_mb'];
                                if ($sizeMb > 50) {
                                    $userMessage .= " Nota: El archivo es muy grande ({$sizeMb} MB).";
                                }
                            }
                        } else {
                            // Sin información de fallback, mensaje genérico pero útil
                            $userMessage = "No se pudo procesar el archivo STEP. ";
                            if (strpos($errorData['error'], 'transferible') !== false) {
                                $userMessage .= "El archivo puede contener geometría no estándar o incompatible. ";
                                $userMessage .= "Intenta exportar el modelo con configuraciones STEP más simples desde tu software CAD.";
                            } elseif (strpos($errorData['error'], 'corrupto') !== false) {
                                $userMessage .= "El archivo puede estar dañado o corrupto. Verifica que el archivo fue guardado correctamente.";
                            } else {
                                $userMessage .= "Error técnico en el procesamiento. Contacta al soporte técnico si el problema persiste.";
                            }
                        }

                        $errorMessage = $userMessage;

                    } else {
                        // Fallback a lógica anterior si no se puede parsear JSON
                        if (strpos($errorBody, 'incompatible') !== false) {
                            $errorMessage = 'Este archivo STEP no es compatible con el motor de visualización. Puede contener geometría no soportada o haber sido generado por una versión de CAD incompatible.';
                        } elseif (strpos($errorBody, 'geometría válida') !== false || strpos($errorBody, 'vacío') !== false) {
                            $errorMessage = 'El archivo STEP no contiene geometría válida o está vacío.';
                        } elseif (strpos($errorBody, 'corrupto') !== false) {
                            $errorMessage = 'El archivo STEP parece estar corrupto o dañado.';
                        } else {
                            $errorMessage = 'Error generando vista previa. Contacta al soporte técnico si el problema persiste.';
                        }
                    }
                } catch (\Exception $parseError) {
                    Log::warning('Could not parse error response as JSON', [
                        'parse_error' => $parseError->getMessage(),
                        'raw_body' => $errorBody
                    ]);
                    $errorMessage = 'Error generando vista previa. Contacta al soporte técnico si el problema persiste.';
                }                Log::error('Preview service returned non-successful response', [
                    'status' => $response->status(),
                    'headers' => $response->headers(),
                    'body' => $errorBody,
                    'payload' => $payload,
                    'parsed_error' => $errorMessage
                ]);
                throw new \Exception($errorMessage);
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
