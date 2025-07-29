<?php

require_once 'vendor/autoload.php';

$app = require_once 'bootstrap/app.php';
$app->make('Illuminate\Contracts\Http\Kernel');

use App\Models\FileUpload;
use App\Models\FileAnalysisResult;

echo "=== ARCHIVOS DE PRUEBA CREADOS ===\n\n";

$files = FileUpload::with('analysisResults')->get();

foreach ($files as $file) {
    echo "ID: {$file->id}\n";
    echo "UUID: {$file->uuid}\n";
    echo "Archivo: {$file->filename_original}\n";
    echo "Extensión: {$file->extension}\n";
    echo "Path: {$file->path}\n";
    echo "Storage Disk: {$file->storage_disk}\n";
    echo "Status: {$file->status}\n";
    echo "User ID: {$file->user_id}\n";
    echo "Tamaño: {$file->size} bytes\n";
    
    if ($file->analysisResults->count() > 0) {
        $analysis = $file->analysisResults->first();
        echo "Análisis: ✓ ({$analysis->analyzer_type})\n";
        if ($analysis->dimensions) {
            $dims = $analysis->dimensions;
            echo "Dimensiones: {$dims['width']}x{$dims['height']}x{$dims['depth']}\n";
        }
        if ($analysis->volume) {
            echo "Volumen: {$analysis->volume}\n";
        }
        if ($analysis->area) {
            echo "Área: {$analysis->area}\n";
        }
    } else {
        echo "Análisis: ✗\n";
    }
    
    // Verificar si el archivo físico existe
    $fullPath = storage_path('app/' . $file->path);
    echo "Archivo físico: " . (file_exists($fullPath) ? "✓ Existe" : "✗ No existe") . "\n";
    
    echo "------------------------\n\n";
}

echo "Total de archivos: " . $files->count() . "\n";
