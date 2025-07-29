<?php
require_once 'vendor/autoload.php';

$app = require_once 'bootstrap/app.php';
$app->make('Illuminate\Contracts\Console\Kernel')->bootstrap();

use App\Models\FileUpload;

echo "Archivos específicos con sus paths:\n";
foreach(FileUpload::whereIn('id', [1,2,3,4,5,6,7,8])->get() as $f) {
    echo "ID: {$f->id} - {$f->filename_original} -> {$f->path}\n";
}
