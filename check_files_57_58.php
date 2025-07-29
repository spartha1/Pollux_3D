<?php
require 'vendor/autoload.php';
$app = require_once 'bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

$file58 = App\Models\FileUpload::find(58);
$file57 = App\Models\FileUpload::find(57);

echo "FILE ID 58:" . PHP_EOL;
if($file58) {
    echo "ID: " . $file58->id . PHP_EOL;
    echo "Original Name: " . ($file58->original_filename ?? 'NULL') . PHP_EOL;
    echo "Storage Path: " . $file58->storage_path . PHP_EOL;
    echo "Disk: " . $file58->disk . PHP_EOL;
    echo "Full Path: " . storage_path('app/' . $file58->storage_path) . PHP_EOL;
    echo "File exists: " . (file_exists(storage_path('app/' . $file58->storage_path)) ? 'YES' : 'NO') . PHP_EOL;
} else {
    echo "File 58 not found" . PHP_EOL;
}

echo PHP_EOL . "FILE ID 57:" . PHP_EOL;
if($file57) {
    echo "ID: " . $file57->id . PHP_EOL;
    echo "Original Name: " . ($file57->original_filename ?? 'NULL') . PHP_EOL;
    echo "Storage Path: " . $file57->storage_path . PHP_EOL;
    echo "Disk: " . $file57->disk . PHP_EOL;
    echo "Full Path: " . storage_path('app/' . $file57->storage_path) . PHP_EOL;
    echo "File exists: " . (file_exists(storage_path('app/' . $file57->storage_path)) ? 'YES' : 'NO') . PHP_EOL;
} else {
    echo "File 57 not found" . PHP_EOL;
}
