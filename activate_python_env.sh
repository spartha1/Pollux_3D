#!/bin/bash
# Script portable para activar el entorno Python de Pollux 3D

# Función para detectar conda
detect_and_activate_conda() {
    # Inicializar conda shell hooks primero
    if command -v conda &> /dev/null; then
        eval "$(conda shell.bash hook)" 2>/dev/null || true
        conda activate pollux-preview-env
        return 0
    elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
        conda activate pollux-preview-env
        return 0
    elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
        conda activate pollux-preview-env
        return 0
    elif [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
        source "/opt/conda/etc/profile.d/conda.sh"
        conda activate pollux-preview-env
        return 0
    else
        echo "❌ No se pudo encontrar conda"
        return 1
    fi
}

# Exportar función para uso en otros scripts
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    # Script está siendo sourced
    detect_and_activate_conda
else
    # Script está siendo ejecutado
    echo "🐍 Activando entorno Python de Pollux 3D..."
    detect_and_activate_conda
    if [ $? -eq 0 ]; then
        echo "✅ Entorno activado correctamente"
        # Mantener shell abierto si se ejecuta directamente
        exec "$SHELL"
    else
        echo "❌ Error al activar el entorno"
        exit 1
    fi
fi
