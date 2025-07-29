<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\FileUpload;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;

class GenerateAllPreviews extends Command
{
    protected $signature = 'previews:generate-all';
    protected $description = 'Generate previews for all processed files';

    public function handle()
    {
        $files = FileUpload::where('status', 'processed')->get();
        
        $this->info("Generando previews para {$files->count()} archivos...");
        
        foreach ($files as $file) {
            $this->info("Procesando ID {$file->id}: {$file->filename_original}");
            
            $filePath = storage_path('app/' . $file->path);
            $outputDir = public_path("storage/previews/{$file->id}");
            
            // Crear directorio de salida si no existe
            if (!file_exists($outputDir)) {
                mkdir($outputDir, 0755, true);
            }
            
            try {
                // Intentar primero con el servidor híbrido (puerto 8052)
                $hybridResponse = $this->tryGeneratePreview($file, $filePath, $outputDir, 8052);
                
                if ($hybridResponse['success']) {
                    $this->info("✅ Preview generado para ID {$file->id} (servidor híbrido)");
                    continue;
                }
                
                // Si falla, intentar con servidor simple (puerto 8051)
                $this->warn("⚠️  Servidor híbrido falló para ID {$file->id}, intentando servidor simple...");
                $simpleResponse = $this->tryGeneratePreview($file, $filePath, $outputDir, 8051);
                
                if ($simpleResponse['success']) {
                    $this->info("✅ Preview generado para ID {$file->id} (servidor simple)");
                } else {
                    $this->error("❌ Ambos servidores fallaron para ID {$file->id}");
                    $this->error("   Híbrido: " . $hybridResponse['error']);
                    $this->error("   Simple: " . $simpleResponse['error']);
                }
                
            } catch (\Exception $e) {
                $this->error("❌ Excepción para ID {$file->id}: " . $e->getMessage());
            }
        }
        
        $this->info("¡Proceso completado!");
    }
    
    /**
     * Intentar generar preview con un servidor específico
     */
    private function tryGeneratePreview($file, $filePath, $outputDir, $port)
    {
        try {
            $response = Http::timeout(30)->post("http://127.0.0.1:{$port}/generate_preview", [
                'file_id' => (string)$file->id,
                'file_path' => $filePath,
                'file_type' => $file->extension,
                'output_dir' => $outputDir
            ]);
            
            return [
                'success' => $response->successful(),
                'error' => $response->successful() ? null : $response->body()
            ];
            
        } catch (\Exception $e) {
            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }
}
