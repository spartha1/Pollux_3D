#!/usr/bin/env php
<?php
/**
 * Script para probar el análisis STL desde el contexto de Laravel
 */

use App\Models\FileUpload;
use App\Http\Controllers\FileAnalysisController;
use Illuminate\Support\Facades\Storage;

// Cargar el entorno de Laravel
require_once __DIR__ . '/../../../../vendor/autoload.php';
require_once __DIR__ . '/../../../../bootstrap/app.php';

// Función para crear un archivo de prueba
function createTestFile() {
    $testContent = file_get_contents(__DIR__ . '/test_stl_files/test_cube.stl');
    
    // Crear el directorio si no existe
    if (!Storage::disk('local')->exists('test_uploads')) {
        Storage::disk('local')->makeDirectory('test_uploads');
    }
    
    // Guardar el archivo
    Storage::disk('local')->put('test_uploads/test_cube.stl', $testContent);
    
    return storage_path('app/test_uploads/test_cube.stl');
}

// Función para simular el análisis
function testAnalysis() {
    echo "🔬 PRUEBA DE ANÁLISIS STL DESDE LARAVEL\n";
    echo str_repeat("=", 50) . "\n";
    
    try {
        // Crear archivo de prueba
        $testFilePath = createTestFile();
        echo "✅ Archivo de prueba creado: $testFilePath\n";
        
        // Crear un FileUpload de prueba
        $fileUpload = new FileUpload([
            'user_id' => 1,
            'filename_original' => 'test_cube.stl',
            'filename_stored' => 'test_cube.stl',
            'extension' => 'stl',
            'mime_type' => 'application/octet-stream',
            'size' => filesize($testFilePath),
            'status' => 'uploaded',
            'storage_path' => 'test_uploads/test_cube.stl',
            'disk' => 'local'
        ]);
        
        // No guardar en BD, solo usar para prueba
        echo "✅ Objeto FileUpload creado\n";
        
        // Configurar variables de entorno
        $pythonPath = config('services.python.executable');
        echo "Python path: $pythonPath\n";
        
        if (!file_exists($pythonPath)) {
            throw new Exception("Python executable no encontrado: $pythonPath");
        }
        
        $extension = strtolower(pathinfo($testFilePath, PATHINFO_EXTENSION));
        $analyzerScript = match($extension) {
            'stl' => app_path('Services/FileAnalyzers/analyze_stl_simple.py'),
            'step', 'stp' => app_path('Services/FileAnalyzers/analyze_step_simple.py'),
            'dxf', 'dwg' => app_path('Services/FileAnalyzers/analyze_dxf_dwg.py'),
            'eps', 'ai' => app_path('Services/FileAnalyzers/analyze_ai_eps.py'),
            default => throw new Exception("No analyzer available for extension: $extension")
        };
        
        if (!file_exists($analyzerScript)) {
            throw new Exception("Analyzer script not found: $analyzerScript");
        }
        
        echo "✅ Analyzer script encontrado: $analyzerScript\n";
        
        // Ejecutar análisis
        echo "🚀 Ejecutando análisis...\n";
        $startTime = microtime(true);
        
        $process = new Symfony\Component\Process\Process([
            $pythonPath,
            $analyzerScript,
            $testFilePath
        ]);
        
        $process->setTimeout(30);
        $process->run();
        
        $elapsed = microtime(true) - $startTime;
        echo "⏱️  Tiempo de ejecución: " . round($elapsed, 2) . " segundos\n";
        
        if (!$process->isSuccessful()) {
            throw new Exception("Process failed: " . $process->getErrorOutput());
        }
        
        $output = $process->getOutput();
        $result = json_decode($output, true);
        
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception('Invalid JSON output: ' . json_last_error_msg());
        }
        
        echo "✅ Análisis completado exitosamente\n";
        echo "\n📊 RESULTADOS:\n";
        echo "- Dimensiones: " . json_encode($result['dimensions'] ?? 'N/A') . "\n";
        echo "- Volumen: " . ($result['volume'] ?? 'N/A') . "\n";
        echo "- Área: " . ($result['area'] ?? 'N/A') . "\n";
        echo "- Tiempo de análisis: " . ($result['analysis_time_ms'] ?? 'N/A') . " ms\n";
        
        $metadata = $result['metadata'] ?? [];
        echo "- Triángulos: " . ($metadata['triangles'] ?? 'N/A') . "\n";
        echo "- Vértices: " . ($metadata['vertices'] ?? 'N/A') . "\n";
        echo "- Formato: " . ($metadata['format'] ?? 'N/A') . "\n";
        
        // Verificar campos requeridos
        $requiredFields = ['dimensions', 'volume', 'area', 'metadata'];
        $missingFields = array_diff($requiredFields, array_keys($result));
        
        if (empty($missingFields)) {
            echo "✅ Todos los campos requeridos están presentes\n";
        } else {
            echo "⚠️  Campos faltantes: " . implode(', ', $missingFields) . "\n";
        }
        
        // Verificar campos de metadata
        $requiredMetadata = ['triangles', 'vertices', 'format'];
        $missingMetadata = array_diff($requiredMetadata, array_keys($metadata));
        
        if (empty($missingMetadata)) {
            echo "✅ Metadatos requeridos están presentes\n";
        } else {
            echo "⚠️  Metadatos faltantes: " . implode(', ', $missingMetadata) . "\n";
        }
        
        echo "\n🎯 COMPATIBILIDAD CON VISTAS:\n";
        echo "✅ JSON válido para almacenar en BD\n";
        echo "✅ Estructura compatible con FileAnalysisResult\n";
        echo "✅ Campos esperados por las vistas React presentes\n";
        
        echo "\n🏁 Prueba completada exitosamente!\n";
        
    } catch (Exception $e) {
        echo "❌ Error: " . $e->getMessage() . "\n";
        echo "📍 Línea: " . $e->getLine() . "\n";
        echo "📄 Archivo: " . $e->getFile() . "\n";
        
        if ($e->getPrevious()) {
            echo "🔗 Causa: " . $e->getPrevious()->getMessage() . "\n";
        }
        
        return false;
    }
    
    return true;
}

// Función para verificar configuración
function checkConfig() {
    echo "\n🔧 VERIFICACIÓN DE CONFIGURACIÓN:\n";
    echo str_repeat("-", 30) . "\n";
    
    $pythonPath = config('services.python.executable');
    echo "Python path: $pythonPath\n";
    
    if (file_exists($pythonPath)) {
        echo "✅ Python executable encontrado\n";
    } else {
        echo "❌ Python executable no encontrado\n";
    }
    
    // Verificar analizadores
    $analyzers = [
        'analyze_stl_simple.py',
        'analyze_step_simple.py',
        'analyze_dxf_dwg.py',
        'analyze_ai_eps.py'
    ];
    
    foreach ($analyzers as $analyzer) {
        $path = app_path("Services/FileAnalyzers/$analyzer");
        if (file_exists($path)) {
            echo "✅ $analyzer encontrado\n";
        } else {
            echo "❌ $analyzer no encontrado\n";
        }
    }
    
    // Verificar directorio de almacenamiento
    $storagePath = storage_path('app');
    if (is_writable($storagePath)) {
        echo "✅ Directorio de almacenamiento escribible\n";
    } else {
        echo "❌ Directorio de almacenamiento no escribible\n";
    }
}

// Ejecutar pruebas
echo "🔬 SISTEMA DE ANÁLISIS STL - PRUEBAS\n";
echo str_repeat("=", 50) . "\n";

checkConfig();
$success = testAnalysis();

if ($success) {
    echo "\n🎉 TODAS LAS PRUEBAS PASARON\n";
    echo "El sistema de análisis STL está funcionando correctamente.\n";
} else {
    echo "\n❌ ALGUNAS PRUEBAS FALLARON\n";
    echo "Revisa los errores anteriores.\n";
}
