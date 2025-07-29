<?php

require_once 'vendor/autoload.php';
require_once 'bootstrap/app.php';

use App\Models\FileUpload;

echo "=== ARCHIVO ID 57 ===" . PHP_EOL;
$file57 = FileUpload::find(57);
if ($file57) {
    echo "File path in DB: " . $file57->file_path . PHP_EOL;
    echo "Full expected path: " . storage_path('app/' . $file57->file_path) . PHP_EOL;
    echo "File exists at expected path: " . (file_exists(storage_path('app/' . $file57->file_path)) ? 'YES' : 'NO') . PHP_EOL;
} else {
    echo "File 57 not found in DB" . PHP_EOL;
}

echo PHP_EOL . "=== ARCHIVO ID 58 ===" . PHP_EOL;
$file58 = FileUpload::find(58);
if ($file58) {
    echo "File path in DB: " . $file58->file_path . PHP_EOL;
    echo "Full expected path: " . storage_path('app/' . $file58->file_path) . PHP_EOL;
    echo "File exists at expected path: " . (file_exists(storage_path('app/' . $file58->file_path)) ? 'YES' : 'NO') . PHP_EOL;
} else {
    echo "File 58 not found in DB" . PHP_EOL;
}

echo PHP_EOL . "=== ROOT DIRECTORY CHECK ===" . PHP_EOL;
echo "File exists at root: " . (file_exists('C:\xampp\htdocs\laravel\Pollux_3D\c1bc34d4-df6e-4caa-900e-5a0d70b41c3c.STL') ? 'YES' : 'NO') . PHP_EOL;
