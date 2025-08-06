#!/bin/bash
# Script wrapper para ejecutar Python con el entorno conda de Pollux 3D
# Equivalente en Linux del run_with_conda.bat

set -e

# Función para detectar y activar conda
detect_and_activate_conda() {
    # Intenta diferentes ubicaciones de conda
    if command -v conda &> /dev/null; then
        # Conda ya está en PATH
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
        echo "ERROR: No se pudo encontrar conda"
        return 1
    fi
}

# Activar entorno conda
if ! detect_and_activate_conda; then
    echo "ERROR: No se pudo activar el entorno pollux-preview-env"
    exit 1
fi

# Verificar que Python existe y el entorno está activo
if [ "$CONDA_DEFAULT_ENV" != "pollux-preview-env" ]; then
    echo "ERROR: El entorno pollux-preview-env no está activo"
    exit 1
fi

# Verificar que Python funciona
if ! python -c "import sys" 2>/dev/null; then
    echo "ERROR: Python no está funcionando correctamente en el entorno"
    exit 1
fi

# Ejecutar el script Python con todos los argumentos pasados
exec python "$@"
