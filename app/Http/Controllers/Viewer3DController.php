<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use App\Models\FileUpload;
use Inertia\Inertia;
use Illuminate\Foundation\Auth\Access\AuthorizesRequests;

class Viewer3DController extends Controller
{
    use AuthorizesRequests;

    public function show(FileUpload $fileUpload)
    {
        $this->authorize('view', $fileUpload);

        // Get all preview types for the file
        $previews = $fileUpload->previews()
            ->whereIn('render_type', ['2d', 'wireframe', '3d'])
            ->get()
            ->keyBy('render_type');

        // Make sure storage_path is visible
        $fileUpload->makeVisible(['storage_path']);

        // Transform previews to array with proper type mapping
        $previewsData = $previews->map(function ($preview) {
            return [
                'id' => $preview->id,
                'file_upload_id' => $preview->file_upload_id,
                'render_type' => $preview->render_type,
                'image_path' => $preview->image_path,
                'created_at' => $preview->created_at?->format('Y-m-d H:i:s'),
            ];
        })->all();

        // Get analysis data if available
        $metadata = [
            'dimensions' => null,
            'vertices' => 0,
            'faces' => 0,
            'fileSize' => $fileUpload->size,
            'uploadDate' => $fileUpload->uploaded_at ? $fileUpload->uploaded_at->format('Y-m-d H:i:s') : null,
            'processDate' => $fileUpload->processed_at ? $fileUpload->processed_at->format('Y-m-d H:i:s') : null,
        ];

        if ($fileUpload->analysisResult) {
            $analysisData = $fileUpload->analysisResult->analysis_data;
            $metadata = array_merge($metadata, [
                'dimensions' => $analysisData['dimensions'] ?? null,
                'vertices' => $analysisData['vertex_count'] ?? 0,
                'faces' => $analysisData['face_count'] ?? 0,
            ]);
        }

        // Prepare file data
        $fileData = [
            'id' => $fileUpload->id,
            'filename_original' => $fileUpload->filename_original,
            'filename_stored' => $fileUpload->filename_stored,
            'extension' => $fileUpload->extension,
            'disk' => $fileUpload->disk,
            'storage_path' => $fileUpload->storage_path,
            'status' => $fileUpload->status,
            'uploadedAt' => $fileUpload->uploaded_at ? $fileUpload->uploaded_at->format('Y-m-d H:i:s') : null,
            'processedAt' => $fileUpload->processed_at ? $fileUpload->processed_at->format('Y-m-d H:i:s') : null,
            'size' => $fileUpload->size,
            'metadata' => $metadata
        ];

        return Inertia::render('Viewer3D', [
            'fileUpload' => $fileData,
            'previews' => $previewsData,
            'viewTypes' => [
                [
                    'id' => '3d',
                    'name' => '3D View',
                    'description' => 'Full 3D rendered view',
                ],
                [
                    'id' => 'wireframe',
                    'name' => 'Wireframe',
                    'description' => 'Wire frame structure view',
                ],
                [
                    'id' => '2d',
                    'name' => '2D View',
                    'description' => 'Flat projection view of the model',
                ]
            ]
        ]);
    }
}
