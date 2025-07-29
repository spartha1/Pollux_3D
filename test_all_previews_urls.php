<?php

echo "=== PRUEBA COMPLETA DE VISTAS PREVIAS ===\n\n";

// IDs de archivos del seeder (1-4) y tipos de vista previa
$fileIds = [1, 2, 3, 4];
$previewTypes = ['2d', 'wireframe', '3d'];

echo "🚀 Probando vistas previas para archivos del seeder:\n\n";

foreach ($fileIds as $fileId) {
    echo "📁 Archivo ID: $fileId\n";
    
    foreach ($previewTypes as $type) {
        $url = "http://127.0.0.1:8088/3d/{$fileId}/preview?type={$type}";
        echo "  🔍 $type: $url\n";
        
        // Test básico de conectividad
        $headers = @get_headers($url);
        if ($headers && strpos($headers[0], '200') !== false) {
            echo "    ✅ Responde correctamente\n";
        } elseif ($headers && strpos($headers[0], '302') !== false) {
            echo "    ↗️ Redirección (normal)\n";
        } else {
            echo "    ❌ Error o no responde\n";
        }
    }
    echo "\n";
}

echo "═══════════════════════════════════════════════════════\n";
echo "🎯 URLs de prueba directa:\n\n";

foreach ($fileIds as $fileId) {
    echo "Archivo $fileId:\n";
    echo "  2D:        http://127.0.0.1:8088/3d/{$fileId}/preview?type=2d\n";
    echo "  Wireframe: http://127.0.0.1:8088/3d/{$fileId}/preview?type=wireframe\n";
    echo "  3D:        http://127.0.0.1:8088/3d/{$fileId}/preview?type=3d\n\n";
}

echo "🌐 Interfaz principal: http://127.0.0.1:8088\n";
echo "🔧 Servidor Python: http://127.0.0.1:8052/health\n";
echo "📊 Documentación API: http://127.0.0.1:8052/docs\n";

echo "\n" . str_repeat("=", 50) . "\n";
