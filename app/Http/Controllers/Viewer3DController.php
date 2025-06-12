<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use App\Models\FileUpload;
use Inertia\Inertia;

class Viewer3DController extends Controller
{
    public function show(FileUpload $fileUpload)
    {
        return Inertia::render('Viewer3D', [
            'fileUpload' => $fileUpload
        ]);
    }
}
