<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use App\Models\FileUpload;
use Inertia\Inertia;

class Viewer3DController extends Controller
{
    public function show(FileUpload $fileUpload)
    {
        // Get all preview types for the file
        $previews = $fileUpload->previews()
            ->whereIn('render_type', ['2d', 'wireframe', '3d'])
            ->get()
            ->keyBy('render_type');

        $fileUpload->makeVisible(['storage_path']);

        return Inertia::render('Viewer3D', [
            'fileUpload' => $fileUpload,
            'previews' => $previews,
            'viewTypes' => [
                [
                    'id' => '2d',
                    'name' => '2D View',
                    'description' => 'Flat projection view of the model'
                ],
                [
                    'id' => 'wireframe',
                    'name' => 'Wireframe',
                    'description' => 'Wire frame structure view'
                ],
                [
                    'id' => '3d',
                    'name' => '3D View',
                    'description' => 'Full 3D rendered view'
                ]
            ]
        ]);
    }
}
