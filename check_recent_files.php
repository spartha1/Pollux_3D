<?php
require_once 'vendor/autoload.php';
require_once 'bootstrap/app.php';

use App\Models\FileAnalysisResult;

$recent_files = FileAnalysisResult::orderBy('created_at', 'desc')->take(10)->get();
echo "Archivos recientes:\n";
foreach ($recent_files as $file) {
    $has_analysis = $file->analysis_data ? 'Sí' : 'No';
    $has_manufacturing = isset($file->analysis_data['manufacturing']) ? 'Sí' : 'No';
    echo "ID: {$file->id} | Nombre: {$file->filename} | Creado: {$file->created_at} | Tiene análisis: {$has_analysis} | Tiene manufacturing: {$has_manufacturing}\n";
}
