#!/bin/bash

# Instalar dependencias para análisis de archivos

echo "📦 Instalando dependencias para análisis de archivos..."

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Instalar numpy-stl para archivos STL
pip install numpy-stl

# Instalar PythonOCC para archivos STEP/STP
# Nota: PythonOCC requiere conda, alternativamente usar opencascade
echo "⚠️  Para archivos STEP/STP se requiere PythonOCC."
echo "Instalación con conda:"
echo "  conda install -c conda-forge pythonocc-core"
echo ""
echo "O usar la alternativa con pip:"
echo "  pip install opencascade"

# Para archivos DXF/DWG
pip install ezdxf

# Para archivos AI/EPS
pip install pillow

echo "✅ Instalación completada"
