<?php

require_once 'vendor/autoload.php';

use App\Models\FileUpload;
use Illuminate\Support\Facades\App;

$app = require_once 'bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

$files = FileUpload::orderBy('created_at', 'desc')->limit(5)->get();

echo "Últimos 5 archivos subidos:\n";
foreach($files as $file) {
    echo "ID: " . $file->id . " - " . $file->filename_original . " - " . $file->status . "\n";
}
