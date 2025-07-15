<?php
/**
 * Script de verificación de analizadores de archivos
 * Pollux 3D - Sistema de análisis multi-formato
 */

echo "=== VERIFICACIÓN DE ANALIZADORES POLLUX 3D ===\n\n";

// Configuración de rutas
$analyzersPath = __DIR__ . '/app/Services/FileAnalyzers/';
$pythonPath = 'python'; // Ajustar según configuración

// Lista de analizadores y sus dependencias
$analyzers = [
    'STL (Simple)' => [
        'file' => 'analyze_stl_simple.py',
        'dependencies' => ['numpy', 'PIL'],
        'extensions' => ['.stl']
    ],
    'STL (No NumPy)' => [
        'file' => 'analyze_stl_no_numpy.py',
        'dependencies' => ['PIL'],
        'extensions' => ['.stl']
    ],
    'STEP/STP' => [
        'file' => 'analyze_step_simple.py',
        'dependencies' => ['OCC.Core'],
        'extensions' => ['.step', '.stp']
    ],
    'DXF/DWG' => [
        'file' => 'analyze_dxf_dwg.py',
        'dependencies' => ['ezdxf'],
        'extensions' => ['.dxf', '.dwg']
    ],
    'AI/EPS' => [
        'file' => 'analyze_ai_eps.py',
        'dependencies' => ['subprocess (Ghostscript)'],
        'extensions' => ['.ai', '.eps']
    ]
];

echo "Verificando analizadores disponibles...\n";
echo str_repeat("-", 70) . "\n";

foreach ($analyzers as $name => $config) {
    $filePath = $analyzersPath . $config['file'];
    $exists = file_exists($filePath);
    
    echo sprintf("%-20s | %-30s | %s\n", 
        $name, 
        implode(', ', $config['extensions']), 
        $exists ? "✅ ENCONTRADO" : "❌ NO ENCONTRADO"
    );
}

echo "\n" . str_repeat("-", 70) . "\n";
echo "Verificando dependencias de Python...\n";
echo str_repeat("-", 70) . "\n";

// Verificar dependencias
$pythonDependencies = [
    'numpy' => 'import numpy; print("NumPy version:", numpy.__version__)',
    'PIL' => 'import PIL; print("PIL version:", PIL.__version__)',
    'ezdxf' => 'import ezdxf; print("ezdxf version:", ezdxf.__version__)',
    'OCC.Core' => 'from OCC.Core.STEPControl import STEPControl_Reader; print("PythonOCC: OK")'
];

foreach ($pythonDependencies as $package => $testCode) {
    $command = $pythonPath . ' -c "' . $testCode . '"';
    $output = [];
    $returnCode = 0;
    
    exec($command . ' 2>&1', $output, $returnCode);
    
    $status = ($returnCode === 0) ? "✅ DISPONIBLE" : "❌ NO DISPONIBLE";
    $result = ($returnCode === 0) ? implode(' ', $output) : "Error: " . implode(' ', $output);
    
    echo sprintf("%-15s | %-20s | %s\n", $package, $status, $result);
}

echo "\n" . str_repeat("-", 70) . "\n";
echo "Verificando Ghostscript...\n";
echo str_repeat("-", 70) . "\n";

// Verificar Ghostscript
$gsPath = 'C:\Program Files\gs\gs10.05.1\bin\gswin64c.exe';
$gsExists = file_exists($gsPath);

if ($gsExists) {
    $command = '"' . $gsPath . '" --version';
    $output = [];
    $returnCode = 0;
    
    exec($command . ' 2>&1', $output, $returnCode);
    
    if ($returnCode === 0) {
        echo "Ghostscript      | ✅ DISPONIBLE     | Version: " . trim(implode(' ', $output)) . "\n";
    } else {
        echo "Ghostscript      | ⚠️ ERROR          | No se pudo ejecutar\n";
    }
} else {
    echo "Ghostscript      | ❌ NO ENCONTRADO  | Ruta: " . $gsPath . "\n";
}

echo "\n" . str_repeat("-", 70) . "\n";
echo "Verificando configuración del controlador...\n";
echo str_repeat("-", 70) . "\n";

// Verificar configuración del controlador
$controllerPath = __DIR__ . '/app/Http/Controllers/FileAnalysisController.php';
if (file_exists($controllerPath)) {
    $controllerContent = file_get_contents($controllerPath);
    
    // Extraer extensiones soportadas
    preg_match_all("/'(\w+)'\s*=>/", $controllerContent, $matches);
    $supportedExts = $matches[1] ?? [];
    
    echo "Controlador      | ✅ ENCONTRADO     | Extensiones: " . implode(', ', $supportedExts) . "\n";
} else {
    echo "Controlador      | ❌ NO ENCONTRADO  | Ruta: " . $controllerPath . "\n";
}

echo "\n" . str_repeat("-", 70) . "\n";
echo "Verificando frontend...\n";
echo str_repeat("-", 70) . "\n";

// Verificar frontend
$frontendPath = __DIR__ . '/resources/js/pages/3d/upload.tsx';
if (file_exists($frontendPath)) {
    $frontendContent = file_get_contents($frontendPath);
    
    // Extraer tipos aceptados
    preg_match('/accept="([^"]+)"/', $frontendContent, $matches);
    $acceptedTypes = $matches[1] ?? 'No encontrado';
    
    echo "Frontend Upload  | ✅ ENCONTRADO     | Tipos: " . $acceptedTypes . "\n";
} else {
    echo "Frontend Upload  | ❌ NO ENCONTRADO  | Ruta: " . $frontendPath . "\n";
}

echo "\n" . str_repeat("=", 70) . "\n";
echo "RESUMEN DE COMPATIBILIDAD:\n";
echo str_repeat("=", 70) . "\n";

// Resumen final
$totalAnalyzers = count($analyzers);
$workingAnalyzers = 0;

foreach ($analyzers as $name => $config) {
    $filePath = $analyzersPath . $config['file'];
    if (file_exists($filePath)) {
        $workingAnalyzers++;
        
        // Verificar dependencias específicas
        $depsOk = true;
        foreach ($config['dependencies'] as $dep) {
            if ($dep === 'OCC.Core' && !isset($pythonDependencies['OCC.Core'])) {
                $depsOk = false;
            }
        }
        
        $status = $depsOk ? "✅ OPERATIVO" : "⚠️ REQUIERE DEPS";
        echo sprintf("%-20s | %s\n", $name, $status);
    } else {
        echo sprintf("%-20s | ❌ NO DISPONIBLE\n", $name);
    }
}

echo "\nEstado general: " . $workingAnalyzers . "/" . $totalAnalyzers . " analizadores disponibles\n";
echo "Fecha de verificación: " . date('Y-m-d H:i:s') . "\n";
echo str_repeat("=", 70) . "\n";
