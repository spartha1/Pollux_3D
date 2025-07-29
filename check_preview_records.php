<?php
require 'vendor/autoload.php';
$app = require_once 'bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

echo "PREVIEW RECORDS IN DATABASE:" . PHP_EOL;

// Check previews for file 57
$previews57 = App\Models\FilePreview::where('file_upload_id', 57)->get();
echo "File 57 previews: " . $previews57->count() . PHP_EOL;
foreach($previews57 as $preview) {
    echo "  - ID: {$preview->id}, Type: {$preview->render_type}, Path: {$preview->image_path}" . PHP_EOL;
}

// Check previews for file 58  
$previews58 = App\Models\FilePreview::where('file_upload_id', 58)->get();
echo "File 58 previews: " . $previews58->count() . PHP_EOL;
foreach($previews58 as $preview) {
    echo "  - ID: {$preview->id}, Type: {$preview->render_type}, Path: {$preview->image_path}" . PHP_EOL;
}

// Check previews for file 59 (the one we were testing)
$previews59 = App\Models\FilePreview::where('file_upload_id', 59)->get();
echo "File 59 previews: " . $previews59->count() . PHP_EOL;
foreach($previews59 as $preview) {
    echo "  - ID: {$preview->id}, Type: {$preview->render_type}, Path: {$preview->image_path}" . PHP_EOL;
}
