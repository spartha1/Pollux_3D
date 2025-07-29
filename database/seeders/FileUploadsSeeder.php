<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\User;
use App\Models\FileUpload;
use App\Models\FileAnalysisResult;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

class FileUploadsSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        // Create a test user if it doesn't exist
        $user = User::firstOrCreate(
            ['email' => 'test@pollux3d.com'],
            [
                'name' => 'Test User',
                'password' => bcrypt('password123'),
                'email_verified_at' => now(),
            ]
        );

        // Sample files data
        $sampleFiles = [
            [
                'filename_original' => 'sample_cube.stl',
                'extension' => 'stl',
                'mime_type' => 'application/octet-stream',
                'description' => 'Cubo 3D simple en formato STL',
                'analyzer' => 'STL',
            ],
            [
                'filename_original' => 'sample_drawing.dxf',
                'extension' => 'dxf',
                'mime_type' => 'application/dxf',
                'description' => 'Dibujo 2D técnico con rectángulo y círculo',
                'analyzer' => 'DXF/DWG',
            ],
            [
                'filename_original' => 'sample_part.step',
                'extension' => 'step',
                'mime_type' => 'application/step',
                'description' => 'Pieza 3D CAD en formato STEP',
                'analyzer' => 'STEP',
            ],
            [
                'filename_original' => 'sample_vector.eps',
                'extension' => 'eps',
                'mime_type' => 'application/postscript',
                'description' => 'Gráfico vectorial en formato EPS',
                'analyzer' => 'AI/EPS',
            ],
        ];

        foreach ($sampleFiles as $fileData) {
            $uuid = Str::uuid()->toString();
            $filename_stored = $uuid . '.' . $fileData['extension'];
            
            // Source path in sample_files
            $sourcePath = storage_path('app/sample_files/' . $fileData['filename_original']);
            
            // Destination path following the models/{user_id}/{uuid}.ext pattern
            $destinationDir = "models/{$user->id}";
            $destinationPath = "{$destinationDir}/{$filename_stored}";
            
            // Create destination directory if it doesn't exist
            Storage::disk('local')->makeDirectory($destinationDir);
            
            // Copy sample file to destination
            if (file_exists($sourcePath)) {
                Storage::disk('local')->put($destinationPath, file_get_contents($sourcePath));
                $fileSize = filesize($sourcePath);
            } else {
                $this->command->warn("Sample file not found: {$sourcePath}");
                continue;
            }

            // Create FileUpload record
            $fileUpload = FileUpload::create([
                'uuid' => $uuid,
                'user_id' => $user->id,
                'filename_original' => $fileData['filename_original'],
                'filename_stored' => $filename_stored,
                'extension' => $fileData['extension'],
                'mime_type' => $fileData['mime_type'],
                'size' => $fileSize,
                'status' => 'processed', // Set as processed to show complete examples
                'path' => $destinationPath,
                'storage_disk' => 'local',
                'uploaded_at' => now(),
                'processed_at' => now(),
            ]);

            // Create sample analysis results based on file type
            $this->createSampleAnalysisResult($fileUpload, $fileData);

            $this->command->info("Created sample file: {$fileData['filename_original']} (ID: {$fileUpload->id})");
        }
    }

    /**
     * Create sample analysis results for each file type
     */
    private function createSampleAnalysisResult(FileUpload $fileUpload, array $fileData): void
    {
        $analysisData = [];
        $metadata = [];

        switch ($fileData['extension']) {
            case 'stl':
                $analysisData = [
                    'dimensions' => ['width' => 10.0, 'height' => 10.0, 'depth' => 5.0],
                    'volume' => 500.0,
                    'area' => 350.0,
                    'analysis_time_ms' => 245,
                ];
                $metadata = [
                    'triangles' => 12,
                    'faces' => 12,
                    'edges' => 36,
                    'vertices' => 24,
                    'format' => 'ASCII',
                    'center_of_mass' => ['x' => 5.0, 'y' => 5.0, 'z' => 2.5],
                    'bbox_min' => ['x' => 0.0, 'y' => 0.0, 'z' => 0.0],
                    'bbox_max' => ['x' => 10.0, 'y' => 10.0, 'z' => 5.0],
                    'file_size_bytes' => filesize(storage_path('app/sample_files/sample_cube.stl')),
                ];
                break;

            case 'dxf':
                $analysisData = [
                    'dimensions' => ['width' => 100.0, 'height' => 50.0, 'depth' => 0.0],
                    'volume' => null,
                    'area' => 5000.0,
                    'analysis_time_ms' => 156,
                ];
                $metadata = [
                    'dxf_version' => 'AC1014',
                    'encoding' => 'UTF-8',
                    'layers' => 1,
                    'linetypes' => 1,
                    'blocks' => 0,
                    'entities' => 5,
                    'entity_types' => ['LINE' => 4, 'CIRCLE' => 1],
                    'file_size_kb' => round(filesize(storage_path('app/sample_files/sample_drawing.dxf')) / 1024, 2),
                ];
                break;

            case 'step':
                $analysisData = [
                    'dimensions' => ['width' => 10.0, 'height' => 10.0, 'depth' => 5.0],
                    'volume' => 500.0,
                    'area' => 350.0,
                    'analysis_time_ms' => 892,
                ];
                $metadata = [
                    'faces' => 6,
                    'edges' => 12,
                    'vertices' => 8,
                    'center_of_mass' => ['x' => 5.0, 'y' => 5.0, 'z' => 2.5],
                    'file_size_kb' => round(filesize(storage_path('app/sample_files/sample_part.step')) / 1024, 2),
                ];
                break;

            case 'eps':
                $analysisData = [
                    'dimensions' => ['width' => 200.0, 'height' => 150.0, 'depth' => 0.0],
                    'volume' => null,
                    'area' => 30000.0,
                    'analysis_time_ms' => 67,
                ];
                $metadata = [
                    'bounding_box_raw' => '%%BoundingBox: 0 0 200 150',
                    'file_size_kb' => round(filesize(storage_path('app/sample_files/sample_vector.eps')) / 1024, 2),
                    'file_type' => 'EPS',
                ];
                break;
        }

        // Add manufacturing data for 3D files
        if (in_array($fileData['extension'], ['stl', 'step'])) {
            $analysisData['manufacturing'] = [
                'cutting_perimeters' => 24,
                'cutting_length_mm' => 120.0,
                'bend_orientations' => 3,
                'holes_detected' => 0,
                'work_planes' => [
                    'xy_faces' => 2,
                    'xz_faces' => 2,
                    'yz_faces' => 2,
                    'dominant_plane' => 'XY',
                ],
                'complexity' => [
                    'surface_complexity' => 'Low',
                    'fabrication_difficulty' => 'Simple',
                ],
                'material_efficiency' => 85.5,
            ];
        }

        FileAnalysisResult::create([
            'file_upload_id' => $fileUpload->id,
            'analyzer_type' => $fileData['analyzer'],
            'analysis_data' => $analysisData,
            'dimensions' => $analysisData['dimensions'] ?? null,
            'volume' => $analysisData['volume'] ?? null,
            'area' => $analysisData['area'] ?? null,
            'metadata' => $metadata,
            'analysis_time_ms' => $analysisData['analysis_time_ms'] ?? null,
        ]);
    }
}
