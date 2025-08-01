<?php

require_once 'vendor/autoload.php';

use App\Models\FileUpload;

// Initialize Laravel
$app = require_once 'bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

$file = FileUpload::find(17);
if ($file) {
    echo "Storage path: " . $file->storage_path . "\n";
    echo "Full path: " . storage_path('app/' . $file->storage_path) . "\n";
    echo "File exists: " . (file_exists(storage_path('app/' . $file->storage_path)) ? 'yes' : 'no') . "\n";
    
    // Check the working command path
    $workingPath = 'storage\\app\\models\\1\\1f53da16-5c8d-45e7-97b4-f01b225c6329.STL';
    echo "Working path: " . $workingPath . "\n";
    echo "Working path exists: " . (file_exists($workingPath) ? 'yes' : 'no') . "\n";
} else {
    echo "File not found\n";
}
