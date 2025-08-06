#!/bin/bash
# Script mejorado para iniciar el servidor de preview

cd "$(dirname "$0")"
PROJECT_ROOT="$(cd ../../.. && pwd)"

echo "🐍 Iniciando servidor de preview de Pollux 3D..."

# Cargar script de activación portable
if [ -f "$PROJECT_ROOT/activate_python_env.sh" ]; then
    source "$PROJECT_ROOT/activate_python_env.sh"
else
    echo "❌ Script de activación no encontrado"
    echo "Ejecute primero: ./setup_python_env.sh"
    exit 1
fi

# Verificar que el entorno está activo
if [ "$CONDA_DEFAULT_ENV" != "pollux-preview-env" ]; then
    echo "❌ El entorno pollux-preview-env no está activo"
    exit 1
fi

echo "✅ Entorno Python activo: $CONDA_DEFAULT_ENV"
echo "🚀 Iniciando servidor en puerto 8052..."

# Iniciar servidor
python preview_server.py

# Si el servidor se detiene, esperar entrada
echo "⏹️  Servidor detenido"
read -p "Presione Enter para continuar..."
