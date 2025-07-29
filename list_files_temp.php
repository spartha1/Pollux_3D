<?php
require_once 'vendor/autoload.php';

$app = require_once 'bootstrap/app.php';
$app->make('Illuminate\Contracts\Console\Kernel')->bootstrap();

use App\Models\FileUpload;

echo "Archivos en la base de datos:\n";
foreach(FileUpload::all() as $f) {
    echo "ID: {$f->id} - {$f->filename_original} ({$f->extension})\n";
}
