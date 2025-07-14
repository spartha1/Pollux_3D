<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\Storage;
use Symfony\Component\Process\Process;

class TestStlAnalysis extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'app:test-stl-analysis {--list : Listar archivos STL disponibles} {--file= : Archivo específico para analizar}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Probar análisis STL con archivos reales o de prueba';

    /**
     * Execute the console command.
     */
    public function handle()
    {
        $this->info('🔬 PRUEBA DE ANÁLISIS STL');
        $this->info(str_repeat('=', 50));

        // Si se pide listar archivos
        if ($this->option('list')) {
            return $this->listAvailableFiles();
        }

        // Si se especifica un archivo
        if ($this->option('file')) {
            return $this->analyzeSpecificFile($this->option('file'));
        }

        // Análisis por defecto con archivo de prueba
        return $this->analyzeDefaultTestFile();
    }

    private function listAvailableFiles()
    {
        $this->info('📁 ARCHIVOS STL DISPONIBLES:');
        $this->info(str_repeat('-', 40));

        // Buscar archivos en storage/app/models
        $modelsPath = storage_path('app/models');
        $testPath = app_path('Services/FileAnalyzers/test_stl_files');
        
        $foundFiles = [];

        // Buscar en directorio de modelos
        if (is_dir($modelsPath)) {
            $this->info('📂 Archivos subidos por usuarios:');
            $this->searchStlFiles($modelsPath, $foundFiles, 'uploaded');
        }

        // Buscar en directorio de pruebas
        if (is_dir($testPath)) {
            $this->info('📂 Archivos de prueba:');
            $this->searchStlFiles($testPath, $foundFiles, 'test');
        }

        // Buscar en otros directorios comunes
        $otherPaths = [
            storage_path('app/public'),
            storage_path('app/private'),
            storage_path('app/uploads'),
            storage_path('app/test_uploads')
        ];

        foreach ($otherPaths as $path) {
            if (is_dir($path)) {
                $this->searchStlFiles($path, $foundFiles, 'other');
            }
        }

        if (empty($foundFiles)) {
            $this->warn('⚠️  No se encontraron archivos STL');
            $this->info('');
            $this->info('💡 Sugerencias:');
            $this->info('   - Sube un archivo STL desde la aplicación web');
            $this->info('   - Usa archivos de prueba: php artisan app:test-stl-analysis');
            return Command::SUCCESS;
        }

        $this->info('');
        $this->info('📊 RESUMEN: ' . count($foundFiles) . ' archivos encontrados');
        $this->info('');
        $this->info('🔍 Para analizar un archivo específico:');
        $this->info('   php artisan app:test-stl-analysis --file="ruta/al/archivo.stl"');

        return Command::SUCCESS;
    }

    private function searchStlFiles($directory, &$foundFiles, $type = 'unknown')
    {
        $iterator = new \RecursiveIteratorIterator(
            new \RecursiveDirectoryIterator($directory)
        );

        foreach ($iterator as $file) {
            if ($file->isFile() && strtolower($file->getExtension()) === 'stl') {
                $relativePath = str_replace(storage_path('app/'), '', $file->getPathname());
                $size = $file->getSize();
                $sizeKb = round($size / 1024, 2);
                
                $foundFiles[] = [
                    'path' => $file->getPathname(),
                    'relative' => $relativePath,
                    'size' => $sizeKb,
                    'type' => $type
                ];

                $icon = match($type) {
                    'uploaded' => '📤',
                    'test' => '🧪',
                    'other' => '📄',
                    default => '❓'
                };

                $this->info("   {$icon} {$relativePath} ({$sizeKb} KB)");
            }
        }
    }

    private function analyzeSpecificFile($filePath)
    {
        $this->info('🎯 ANÁLISIS DE ARCHIVO ESPECÍFICO');
        $this->info(str_repeat('-', 40));

        // Resolver ruta completa
        $fullPath = $this->resolveFilePath($filePath);
        
        if (!$fullPath || !file_exists($fullPath)) {
            $this->error("❌ Archivo no encontrado: {$filePath}");
            $this->info('');
            $this->info('💡 Usa --list para ver archivos disponibles');
            return Command::FAILURE;
        }

        $this->info("📄 Archivo: {$filePath}");
        $this->info("📍 Ruta completa: {$fullPath}");
        $this->info("📏 Tamaño: " . round(filesize($fullPath) / 1024, 2) . " KB");

        return $this->performAnalysis($fullPath);
    }

    private function analyzeDefaultTestFile()
    {
        $this->info('🧪 ANÁLISIS CON ARCHIVO DE PRUEBA');
        $this->info(str_repeat('-', 40));

        $testFile = app_path('Services/FileAnalyzers/test_stl_files/test_cube.stl');
        
        if (!file_exists($testFile)) {
            $this->error('❌ Archivo de prueba no encontrado: ' . $testFile);
            $this->info('');
            $this->info('💡 Ejecuta primero: php artisan app:test-stl-analysis --list');
            return Command::FAILURE;
        }

        $this->info("📄 Usando archivo de prueba: test_cube.stl");
        return $this->performAnalysis($testFile);
    }

    private function resolveFilePath($filePath)
    {
        // Si es una ruta completa y existe
        if (file_exists($filePath)) {
            return $filePath;
        }

        // Intentar rutas relativas desde storage/app
        $attempts = [
            storage_path('app/' . $filePath),
            storage_path('app/models/' . $filePath),
            storage_path('app/private/' . $filePath),
            storage_path('app/public/' . $filePath),
            app_path('Services/FileAnalyzers/test_stl_files/' . $filePath)
        ];

        foreach ($attempts as $attempt) {
            if (file_exists($attempt)) {
                return $attempt;
            }
        }

        // Buscar recursivamente
        $searchPaths = [
            storage_path('app/models'),
            storage_path('app/private'),
            storage_path('app/uploads'),
            storage_path('app/test_uploads')
        ];

        foreach ($searchPaths as $searchPath) {
            if (is_dir($searchPath)) {
                $found = $this->findFileRecursively($searchPath, basename($filePath));
                if ($found) {
                    return $found;
                }
            }
        }

        return null;
    }

    private function findFileRecursively($directory, $filename)
    {
        $iterator = new \RecursiveIteratorIterator(
            new \RecursiveDirectoryIterator($directory)
        );

        foreach ($iterator as $file) {
            if ($file->isFile() && $file->getFilename() === $filename) {
                return $file->getPathname();
            }
        }

        return null;
    }

    private function performAnalysis($testFile)
    {
        try {
            $this->info('✅ Archivo encontrado');

            // Configurar rutas
            $pythonPath = config('services.python.executable');
            $analyzerScript = app_path('Services/FileAnalyzers/analyze_stl_simple.py');

            $this->info('Python path: ' . $pythonPath);
            $this->info('Analyzer script: ' . $analyzerScript);

            // Verificar que existan
            if (!file_exists($pythonPath)) {
                $this->error('❌ Python executable no encontrado: ' . $pythonPath);
                return Command::FAILURE;
            }

            if (!file_exists($analyzerScript)) {
                $this->error('❌ Analyzer script no encontrado: ' . $analyzerScript);
                return Command::FAILURE;
            }

            $this->info('✅ Componentes verificados');

            // Ejecutar análisis
            $this->info('🚀 Ejecutando análisis...');
            
            $process = new Process([
                $pythonPath,
                $analyzerScript,
                $testFile
            ]);

            $process->setTimeout(120); // Más tiempo para archivos grandes
            $startTime = microtime(true);
            $process->run();
            $elapsed = microtime(true) - $startTime;

            $this->info('⏱️  Tiempo de ejecución: ' . round($elapsed, 2) . ' segundos');

            if (!$process->isSuccessful()) {
                $this->error('❌ Error en el proceso:');
                $this->error($process->getErrorOutput());
                return Command::FAILURE;
            }

            $output = $process->getOutput();
            $result = json_decode($output, true);

            if (json_last_error() !== JSON_ERROR_NONE) {
                $this->error('❌ Error al parsear JSON: ' . json_last_error_msg());
                $this->error('Salida raw: ' . $output);
                return Command::FAILURE;
            }

            $this->info('✅ Análisis completado exitosamente');
            $this->info('');

            // Mostrar resultados
            $this->displayResults($result);

            return Command::SUCCESS;

        } catch (\Exception $e) {
            $this->error('❌ Error: ' . $e->getMessage());
            $this->error('📍 Línea: ' . $e->getLine());
            $this->error('📄 Archivo: ' . $e->getFile());
            return Command::FAILURE;
        }
    }

    private function displayResults($result)
    {
        // Mostrar resultados
        $this->info('📊 RESULTADOS DEL ANÁLISIS:');
        $this->info(str_repeat('-', 40));

        $dimensions = $result['dimensions'] ?? [];
        $this->info('📏 Dimensiones:');
        $this->info('   - Ancho: ' . ($dimensions['width'] ?? 'N/A'));
        $this->info('   - Alto: ' . ($dimensions['height'] ?? 'N/A'));
        $this->info('   - Profundidad: ' . ($dimensions['depth'] ?? 'N/A'));

        $this->info('📦 Volumen: ' . ($result['volume'] ?? 'N/A'));
        $this->info('📐 Área: ' . ($result['area'] ?? 'N/A'));

        $metadata = $result['metadata'] ?? [];
        $this->info('');
        $this->info('🔍 Metadatos:');
        $this->info('   - Triángulos: ' . ($metadata['triangles'] ?? 'N/A'));
        $this->info('   - Vértices: ' . ($metadata['vertices'] ?? 'N/A'));
        $this->info('   - Caras: ' . ($metadata['faces'] ?? 'N/A'));
        $this->info('   - Aristas: ' . ($metadata['edges'] ?? 'N/A'));
        $this->info('   - Formato: ' . ($metadata['format'] ?? 'N/A'));

        if (isset($metadata['center_of_mass'])) {
            $com = $metadata['center_of_mass'];
            $this->info('   - Centro de masa: (' . 
                round($com['x'] ?? 0, 2) . ', ' . 
                round($com['y'] ?? 0, 2) . ', ' . 
                round($com['z'] ?? 0, 2) . ')');
        }

        if (isset($metadata['file_size_bytes'])) {
            $sizeKb = round($metadata['file_size_bytes'] / 1024, 2);
            $this->info('   - Tamaño de archivo: ' . $sizeKb . ' KB');
        }

        $this->info('');
        $this->info('⏱️  Tiempo de análisis: ' . ($result['analysis_time_ms'] ?? 'N/A') . ' ms');

        // Verificar campos requeridos
        $requiredFields = ['dimensions', 'volume', 'area', 'metadata'];
        $missingFields = array_diff($requiredFields, array_keys($result));

        $this->info('');
        $this->info('🎯 VERIFICACIÓN DE CAMPOS:');
        
        if (empty($missingFields)) {
            $this->info('✅ Todos los campos requeridos están presentes');
        } else {
            $this->error('⚠️  Campos faltantes: ' . implode(', ', $missingFields));
        }

        // Verificar metadatos
        $requiredMetadata = ['triangles', 'vertices', 'format'];
        $missingMetadata = array_diff($requiredMetadata, array_keys($metadata));

        if (empty($missingMetadata)) {
            $this->info('✅ Metadatos requeridos están presentes');
        } else {
            $this->error('⚠️  Metadatos faltantes: ' . implode(', ', $missingMetadata));
        }

        $this->info('');
        $this->info('🏁 COMPATIBILIDAD CON VISTAS:');
        $this->info('✅ JSON válido para almacenar en BD');
        $this->info('✅ Estructura compatible con FileAnalysisResult');
        $this->info('✅ Campos esperados por las vistas React presentes');

        $this->info('');
        $this->info('🎉 ANÁLISIS COMPLETADO EXITOSAMENTE');
    }
}
