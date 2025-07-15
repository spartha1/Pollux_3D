<?php
/**
 * Script de monitoreo y depuración del sistema Pollux 3D
 * Para detectar errores y mejoras en tiempo real
 */

require_once __DIR__ . '/vendor/autoload.php';

use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Log;
use App\Models\FileUpload;
use App\Models\FilePreview;

// Configurar Laravel
$app = require_once __DIR__ . '/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

echo "🔍 SISTEMA DE MONITOREO Y DEPURACIÓN - POLLUX 3D\n";
echo str_repeat("=", 60) . "\n";

function checkSystemStatus() {
    echo "\n📊 VERIFICANDO ESTADO DEL SISTEMA...\n";
    
    // 1. Verificar servicios
    echo "\n🔌 Verificando servicios:\n";
    $services = [
        'Laravel' => 'http://localhost:8088',
        'Vite' => 'http://localhost:5173',
        'Preview Server' => 'http://localhost:8051/health'
    ];
    
    foreach ($services as $name => $url) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        $status = ($httpCode >= 200 && $httpCode < 300) ? "✅ ACTIVO" : "❌ INACTIVO";
        echo "   $name: $status (HTTP $httpCode)\n";
    }
    
    // 2. Verificar Python environments
    echo "\n🐍 Verificando Python environments:\n";
    $pythonSystem = shell_exec('python --version 2>&1');
    $pythonConda = shell_exec('"C:\Users\\' . getenv('USERNAME') . '\miniconda3\envs\pollux-preview-env\python.exe" --version 2>&1');
    
    echo "   Sistema: " . trim($pythonSystem) . "\n";
    echo "   Conda: " . trim($pythonConda) . "\n";
    
    // 3. Verificar dependencias críticas
    echo "\n📦 Verificando dependencias críticas:\n";
    $dependencies = [
        'NumPy' => '"C:\Users\\' . getenv('USERNAME') . '\miniconda3\envs\pollux-preview-env\python.exe" -c "import numpy; print(numpy.__version__)"',
        'PythonOCC' => '"C:\Users\\' . getenv('USERNAME') . '\miniconda3\envs\pollux-preview-env\python.exe" -c "from OCC.Core.STEPControl import STEPControl_Reader; print(\'OK\')"',
        'ezdxf' => 'python -c "import ezdxf; print(ezdxf.__version__)"',
        'Ghostscript' => '"C:\Program Files\gs\gs10.05.1\bin\gswin64c.exe" --version'
    ];
    
    foreach ($dependencies as $name => $command) {
        $result = shell_exec($command . ' 2>&1');
        $status = $result ? "✅ " . trim($result) : "❌ ERROR";
        echo "   $name: $status\n";
    }
    
    // 4. Verificar espacio en disco
    echo "\n💾 Verificando espacio en disco:\n";
    $storageInfo = disk_free_space(storage_path());
    $storageFree = round($storageInfo / 1024 / 1024 / 1024, 2);
    echo "   Espacio libre: {$storageFree} GB\n";
    
    // 5. Verificar archivos recientes
    echo "\n📁 Archivos recientes:\n";
    $recentFiles = FileUpload::orderBy('created_at', 'desc')->take(5)->get();
    foreach ($recentFiles as $file) {
        echo "   ID: {$file->id} - {$file->filename_original} ({$file->created_at})\n";
    }
}

function monitorUpload($fileId) {
    echo "\n🔄 MONITOREANDO ARCHIVO ID: $fileId\n";
    echo str_repeat("-", 50) . "\n";
    
    // Buscar archivo
    $file = FileUpload::find($fileId);
    if (!$file) {
        echo "❌ No se encontró el archivo con ID $fileId\n";
        return;
    }
    
    echo "📄 Archivo: {$file->filename_original}\n";
    echo "📏 Tamaño: " . round($file->file_size / 1024, 2) . " KB\n";
    echo "🗂️ Tipo: {$file->file_type}\n";
    echo "📅 Subido: {$file->created_at}\n";
    
    // Verificar archivo físico
    $filePath = storage_path('app/' . $file->storage_path);
    if (!file_exists($filePath)) {
        echo "❌ ERROR: Archivo físico no encontrado: $filePath\n";
        return;
    }
    
    echo "✅ Archivo físico encontrado\n";
    
    // Verificar análisis
    echo "\n🔬 Verificando análisis...\n";
    $extension = strtolower(pathinfo($file->filename_original, PATHINFO_EXTENSION));
    
    // Seleccionar analizador
    $analyzerScript = match($extension) {
        'stl' => 'app/Services/FileAnalyzers/analyze_stl_simple.py',
        'step', 'stp' => 'app/Services/FileAnalyzers/analyze_step_simple.py',
        'dxf', 'dwg' => 'app/Services/FileAnalyzers/analyze_dxf_dwg.py',
        'eps', 'ai' => 'app/Services/FileAnalyzers/analyze_ai_eps.py',
        default => null
    };
    
    if (!$analyzerScript) {
        echo "❌ No hay analizador para la extensión: $extension\n";
        return;
    }
    
    echo "🔧 Analizador: $analyzerScript\n";
    
    // Ejecutar análisis manualmente
    $pythonPath = config('services.python.executable');
    $command = '"' . $pythonPath . '" "' . $analyzerScript . '" "' . $filePath . '"';
    
    echo "⚡ Ejecutando comando: $command\n";
    
    $startTime = microtime(true);
    $output = shell_exec($command . ' 2>&1');
    $endTime = microtime(true);
    $executionTime = round(($endTime - $startTime) * 1000, 2);
    
    echo "⏱️ Tiempo de ejecución: {$executionTime}ms\n";
    
    if ($output) {
        $result = json_decode($output, true);
        if ($result) {
            echo "✅ Análisis exitoso:\n";
            echo "   Dimensiones: " . json_encode($result['dimensions'] ?? 'N/A') . "\n";
            echo "   Volumen: " . ($result['volume'] ?? 'N/A') . "\n";
            echo "   Área: " . ($result['area'] ?? 'N/A') . "\n";
            echo "   Entidades: " . ($result['layers'] ?? $result['entities'] ?? 'N/A') . "\n";
        } else {
            echo "⚠️ Salida del análisis:\n";
            echo "   " . trim($output) . "\n";
        }
    } else {
        echo "❌ No se obtuvo salida del análisis\n";
    }
    
    // Verificar previews
    echo "\n🖼️ Verificando previews...\n";
    $previews = FilePreview::where('file_upload_id', $fileId)->get();
    
    if ($previews->isEmpty()) {
        echo "⚠️ No hay previews generados\n";
        
        // Intentar generar preview
        echo "🔄 Intentando generar preview...\n";
        $previewResult = generatePreview($file);
        echo $previewResult ? "✅ Preview generado\n" : "❌ Error generando preview\n";
    } else {
        echo "✅ Previews encontrados:\n";
        foreach ($previews as $preview) {
            echo "   Tipo: {$preview->preview_type} - Tamaño: " . strlen($preview->preview_data) . " bytes\n";
        }
    }
}

function generatePreview($file) {
    $postData = json_encode([
        'file_path' => $file->filename_stored,
        'preview_type' => '2d',
        'width' => 800,
        'height' => 600,
        'format' => 'png'
    ]);
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, 'http://localhost:8051/generate-preview');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($postData)
    ]);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode === 200) {
        $data = json_decode($response, true);
        return $data && $data['success'];
    }
    
    return false;
}

// Función principal
function main() {
    global $argv;
    
    if (isset($argv[1])) {
        if ($argv[1] === 'status') {
            checkSystemStatus();
        } elseif ($argv[1] === 'monitor' && isset($argv[2])) {
            checkSystemStatus();
            monitorUpload($argv[2]);
        } else {
            echo "Uso: php debug_system.php [status|monitor <file_id>]\n";
        }
    } else {
        echo "Modo interactivo - Verificando estado del sistema...\n";
        checkSystemStatus();
        
        echo "\n📝 Para monitorear un archivo específico:\n";
        echo "   php debug_system.php monitor <file_id>\n";
    }
}

main();
?>
