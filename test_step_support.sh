#!/bin/bash
# Script de prueba para verificar que el procesamiento de archivos STEP funciona

echo "🧪 POLLUX 3D - PRUEBA DEL SISTEMA DE PREVIEW"
echo "============================================="

# Verificar que el servidor está ejecutándose
echo "📡 Verificando servidor de preview..."
if curl -s http://localhost:8052/debug/routes > /dev/null; then
    echo "✅ Servidor de preview está ejecutándose en puerto 8052"
else
    echo "❌ Servidor de preview no está disponible"
    echo "💡 Ejecute: cd app/Services/PreviewService && ./start_preview_server.sh"
    exit 1
fi

# Verificar dependencias Python
echo "🐍 Verificando dependencias Python..."
source ./activate_python_env.sh

python -c "
import sys
print(f'🐍 Usando Python: {sys.executable}')

try:
    from OCC.Core.STEPControl import STEPControl_Reader
    print('✅ PythonOCC-Core disponible - Soporte STEP habilitado')
except ImportError as e:
    print(f'❌ Error PythonOCC: {e}')
    sys.exit(1)

try:
    from stl import mesh
    print('✅ numpy-stl disponible - Soporte STL habilitado')
except ImportError as e:
    print(f'❌ Error numpy-stl: {e}')
    sys.exit(1)

try:
    import pyvista as pv
    print('✅ PyVista disponible - Renderizado 3D habilitado')
except ImportError as e:
    print(f'❌ Error PyVista: {e}')
    sys.exit(1)

try:
    import fastapi
    print('✅ FastAPI disponible - API REST habilitada')
except ImportError as e:
    print(f'❌ Error FastAPI: {e}')
    sys.exit(1)

print('🎉 Todas las dependencias están correctamente instaladas!')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SISTEMA LISTO PARA PROCESAR ARCHIVOS STEP"
    echo "============================================="
    echo "✅ Servidor de preview: http://localhost:8052"
    echo "✅ Entorno Python: pollux-preview-env"
    echo "✅ Dependencias: PythonOCC, PyVista, numpy-stl, FastAPI"
    echo ""
    echo "🚀 Para usar el sistema completo:"
    echo "   npm run dev:all"
    echo ""
    echo "📋 Tipos de archivo soportados:"
    echo "   • STL - Modelos 3D estándar"
    echo "   • STEP/STP - Archivos CAD industriales"
    echo "   • Tipos de render: 2d, wireframe, 3d"
else
    echo "❌ Error en la verificación de dependencias"
    exit 1
fi
