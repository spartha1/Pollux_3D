<?php

require_once 'vendor/autoload.php';
use App\Models\FileUpload;

$file = FileUpload::find(23);
if ($file) {
    echo "ID: " . $file->id . "\n";
    echo "Extension: " . $file->extension . "\n";
    echo "Storage Path: " . $file->storage_path . "\n";
    echo "Full Path: " . storage_path('app/' . $file->storage_path) . "\n";
    echo "File exists: " . (file_exists(storage_path('app/' . $file->storage_path)) ? 'YES' : 'NO') . "\n";
    
    // Show actual file path being passed to batch
    $relativePath = str_replace('/', '\\', $file->storage_path);
    $filePathForCmd = "storage\\app\\{$relativePath}";
    echo "Batch command path: " . $filePathForCmd . "\n";
    echo "Batch file exists: " . (file_exists($filePathForCmd) ? 'YES' : 'NO') . "\n";
} else {
    echo "File ID 23 not found\n";
}
