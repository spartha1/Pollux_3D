<?php
require 'vendor/autoload.php';
$app = require_once 'bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

// Create the missing preview record for file 57
$file57 = App\Models\FileUpload::find(57);
if ($file57) {
    $preview = $file57->previews()->create([
        'image_path' => 'previews/57/stl_2d_preview_f02985c0.png',
        'render_type' => '2d',
    ]);
    
    echo "Created preview record for file 57:" . PHP_EOL;
    echo "Preview ID: " . $preview->id . PHP_EOL;
    echo "Image Path: " . $preview->image_path . PHP_EOL;
    echo "Render Type: " . $preview->render_type . PHP_EOL;
} else {
    echo "File 57 not found" . PHP_EOL;
}
