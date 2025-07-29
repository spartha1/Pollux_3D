<?php
require 'vendor/autoload.php';
$app = require_once 'bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

$file = App\Models\FileUpload::find(59);
if($file) {
    echo "File ID: " . $file->id . PHP_EOL;
    echo "Original Name: " . $file->original_filename . PHP_EOL;
    echo "Storage Path: " . $file->storage_path . PHP_EOL;
    echo "Disk: " . $file->disk . PHP_EOL;
    echo "Full Path: " . storage_path('app/' . $file->storage_path) . PHP_EOL;
    echo "File exists: " . (file_exists(storage_path('app/' . $file->storage_path)) ? 'YES' : 'NO') . PHP_EOL;
} else {
    echo "File not found" . PHP_EOL;
}
