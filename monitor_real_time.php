<?php

// Monitor en tiempo real para el siguiente archivo
echo "🔍 MONITOR TIEMPO REAL - PREPARADO\n";
echo "===================================\n";
echo "Timestamp: " . date('Y-m-d H:i:s') . "\n\n";

echo "📋 INSTRUCCIONES:\n";
echo "1. Deja este script ejecutándose\n";
echo "2. Sube un archivo STL desde el frontend\n";
echo "3. Presiona el botón 'Analizar'\n";
echo "4. Este script capturará EXACTAMENTE lo que pasa\n\n";

echo "🚀 Monitoreando logs...\n";
echo "========================\n";

$logFile = 'storage/logs/laravel.log';
$lastPosition = file_exists($logFile) ? filesize($logFile) : 0;
$iteration = 0;

while (true) {
    if (file_exists($logFile)) {
        $currentSize = filesize($logFile);
        
        if ($currentSize > $lastPosition) {
            $handle = fopen($logFile, 'r');
            fseek($handle, $lastPosition);
            
            while (($line = fgets($handle)) !== false) {
                $line = trim($line);
                
                // Filtrar solo logs relevantes al proceso de análisis
                if (strpos($line, 'Manufacturing') !== false || 
                    strpos($line, 'STL file detected') !== false ||
                    strpos($line, 'batch script') !== false ||
                    strpos($line, 'run_manufacturing_analyzer') !== false ||
                    strpos($line, 'FileAnalysisController') !== false ||
                    strpos($line, 'Exit code') !== false ||
                    strpos($line, 'ERROR') !== false) {
                    
                    echo "[" . date('H:i:s') . "] " . $line . "\n";
                }
            }
            
            fclose($handle);
            $lastPosition = $currentSize;
        }
    }
    
    $iteration++;
    if ($iteration % 30 === 0) {
        echo "[" . date('H:i:s') . "] ⏰ Esperando actividad... (presiona Ctrl+C para salir)\n";
    }
    
    sleep(1);
}
