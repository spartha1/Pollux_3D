<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\FileUpload;

class CheckFileStatus extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'app:check-file-status {filename?}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Verificar estado de análisis de archivos STL';

    /**
     * Execute the console command.
     */
    public function handle()
    {
        $filename = $this->argument('filename');
        
        if ($filename) {
            $this->checkSpecificFile($filename);
        } else {
            $this->checkAllFiles();
        }
    }

    private function checkSpecificFile($filename)
    {
        $this->info('🔍 VERIFICANDO ARCHIVO: ' . $filename);
        $this->info(str_repeat('=', 50));

        $file = FileUpload::with(['analysisResult', 'errors'])
            ->where('filename_stored', 'like', '%' . $filename . '%')
            ->first();

        if (!$file) {
            $this->error('❌ Archivo no encontrado en la base de datos');
            return;
        }

        $this->info('✅ Archivo encontrado:');
        $this->info('   - ID: ' . $file->id);
        $this->info('   - Nombre original: ' . $file->filename_original);
        $this->info('   - Nombre almacenado: ' . $file->filename_stored);
        $this->info('   - Extensión: ' . $file->extension);
        $this->info('   - Tamaño: ' . round($file->size / 1024, 2) . ' KB');
        $this->info('   - Estado: ' . $file->status);
        $this->info('   - Disco: ' . $file->disk);
        $this->info('   - Ruta: ' . $file->storage_path);

        if ($file->uploaded_at) {
            $this->info('   - Subido: ' . $file->uploaded_at->format('Y-m-d H:i:s'));
        }

        if ($file->processed_at) {
            $this->info('   - Procesado: ' . $file->processed_at->format('Y-m-d H:i:s'));
        }

        $this->info('');

        if ($file->analysisResult) {
            $this->info('✅ ANÁLISIS COMPLETADO:');
            $result = $file->analysisResult;
            $this->info('   - Tipo analizador: ' . $result->analyzer_type);
            $this->info('   - Tiempo de análisis: ' . ($result->analysis_time_ms ?? 'N/A') . ' ms');
            
            if ($result->dimensions) {
                $dims = $result->dimensions;
                $this->info('   - Dimensiones:');
                $this->info('     * Ancho: ' . ($dims['width'] ?? 'N/A'));
                $this->info('     * Alto: ' . ($dims['height'] ?? 'N/A'));
                $this->info('     * Profundidad: ' . ($dims['depth'] ?? 'N/A'));
            }

            if ($result->volume) {
                $this->info('   - Volumen: ' . $result->volume);
            }

            if ($result->area) {
                $this->info('   - Área: ' . $result->area);
            }

            if ($result->metadata) {
                $meta = $result->metadata;
                $this->info('   - Metadatos:');
                $this->info('     * Triángulos: ' . ($meta['triangles'] ?? 'N/A'));
                $this->info('     * Vértices: ' . ($meta['vertices'] ?? 'N/A'));
                $this->info('     * Formato: ' . ($meta['format'] ?? 'N/A'));
            }
        } else {
            $this->warn('⚠️  SIN ANÁLISIS - El archivo no ha sido analizado');
        }

        if ($file->errors && $file->errors->count() > 0) {
            $this->error('❌ ERRORES ENCONTRADOS:');
            foreach ($file->errors as $error) {
                $this->error('   - ' . $error->error_message);
            }
        } else {
            $this->info('✅ Sin errores registrados');
        }
    }

    private function checkAllFiles()
    {
        $this->info('📋 TODOS LOS ARCHIVOS SUBIDOS:');
        $this->info(str_repeat('=', 50));

        $files = FileUpload::with(['analysisResult', 'errors'])
            ->orderBy('created_at', 'desc')
            ->get();

        if ($files->isEmpty()) {
            $this->warn('⚠️  No hay archivos subidos');
            return;
        }

        foreach ($files as $file) {
            $status = match($file->status) {
                'uploaded' => '📤',
                'processing' => '⏳',
                'analyzed' => '✅',
                'error' => '❌',
                default => '❓'
            };

            $hasAnalysis = $file->analysisResult ? '📊' : '❌';
            $hasErrors = $file->errors && $file->errors->count() > 0 ? '⚠️' : '✅';

            $this->info("{$status} {$file->filename_original} ({$file->extension})");
            $this->info("   Estado: {$file->status} | Análisis: {$hasAnalysis} | Errores: {$hasErrors}");
            $this->info("   Tamaño: " . round($file->size / 1024, 2) . " KB");
            $this->info('');
        }

        $this->info('🎯 RESUMEN:');
        $total = $files->count();
        $analyzed = $files->where('analysisResult')->count();
        $errors = $files->filter(function($file) {
            return $file->errors && $file->errors->count() > 0;
        })->count();

        $this->info("   Total archivos: {$total}");
        $this->info("   Analizados: {$analyzed}");
        $this->info("   Con errores: {$errors}");
    }
}
