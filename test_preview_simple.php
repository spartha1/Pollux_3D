<?php

require 'vendor/autoload.php';

$app = require_once 'bootstrap/app.php';
$app->make('Illuminate\Contracts\Console\Kernel')->bootstrap();

use App\Models\FileUpload;

echo "Looking for valid files with complete data:\n";
$files = FileUpload::whereNotNull('uuid')
    ->whereNotNull('path')
    ->whereNotNull('storage_disk')
    ->orderBy('id', 'desc')
    ->limit(5)
    ->get();

if ($files->count() > 0) {
    foreach ($files as $file) {
        echo "ID: {$file->id} | File: {$file->filename_original} | UUID: {$file->uuid}\n";
        echo "  Path: {$file->path}\n";
        echo "  Storage: {$file->storage_disk}\n";
        
        $fullPath = storage_path('app/' . $file->path);
        echo "  File exists: " . (file_exists($fullPath) ? 'Yes' : 'No') . "\n";
        echo "  ---\n";
    }
} else {
    echo "No valid files found. Let's check what files exist:\n";
    $allFiles = FileUpload::orderBy('id', 'desc')->limit(10)->get();
    foreach ($allFiles as $file) {
        echo "ID: {$file->id} | File: {$file->filename_original}\n";
        echo "  UUID: '{$file->uuid}' | Path: '{$file->path}' | Storage: '{$file->storage_disk}'\n";
        echo "  ---\n";
    }
}

echo "\nDone.\n";
