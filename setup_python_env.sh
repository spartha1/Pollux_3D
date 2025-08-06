#!/bin/bash
# 🐍 Script de Configuración del Entorno Python para Pollux 3D
# Este script configura automáticamente el entorno Python necesario para el procesamiento de archivos STEP/STL

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${YELLOW}▶️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo "🐍 POLLUX 3D - CONFIGURACIÓN DEL ENTORNO PYTHON"
echo "==============================================="

# Detectar si conda está instalado
detect_conda() {
    if command -v conda &> /dev/null; then
        print_success "Conda encontrado: $(which conda)"
        # Inicializar conda shell hooks si no están disponibles
        eval "$(conda shell.bash hook)" 2>/dev/null || true
        return 0
    elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        print_info "Conda encontrado en $HOME/miniconda3"
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
        return 0
    elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
        print_info "Anaconda encontrado en $HOME/anaconda3"
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
        return 0
    elif [ -f "/opt/conda/etc/profile.d/conda.sh" ]; then
        print_info "Conda encontrado en /opt/conda"
        source "/opt/conda/etc/profile.d/conda.sh"
        return 0
    else
        return 1
    fi
}

# Instalar conda si no existe
install_conda() {
    print_step "Conda no encontrado. Instalando Miniconda..."

    # Detectar arquitectura
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        CONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        CONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"
    else
        print_error "Arquitectura no soportada: $ARCH"
        exit 1
    fi

    # Descargar e instalar
    wget -q "$CONDA_URL" -O miniconda.sh
    bash miniconda.sh -b -p "$HOME/miniconda3"
    rm miniconda.sh

    # Activar conda
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda init bash

    print_success "Miniconda instalado correctamente"
}

# Crear entorno si no existe
create_environment() {
    print_step "Verificando entorno pollux-preview-env..."

    if conda env list | grep -q "pollux-preview-env"; then
        print_info "El entorno pollux-preview-env ya existe"
    else
        print_step "Creando entorno desde environment.yml..."
        conda env create -f environment.yml
        print_success "Entorno pollux-preview-env creado correctamente"
    fi
}

# Verificar dependencias
verify_dependencies() {
    print_step "Verificando dependencias en el entorno..."

    # Asegurar que conda está inicializado
    eval "$(conda shell.bash hook)" 2>/dev/null || true
    conda activate pollux-preview-env

    # Verificar PythonOCC
    if python -c "from OCC.Core.STEPControl import STEPControl_Reader" 2>/dev/null; then
        print_success "PythonOCC-Core instalado correctamente"
    else
        print_error "PythonOCC-Core no está instalado correctamente"
        exit 1
    fi

    # Verificar numpy-stl
    if python -c "from stl import mesh" 2>/dev/null; then
        print_success "numpy-stl instalado correctamente"
    else
        print_error "numpy-stl no está instalado correctamente"
        exit 1
    fi

    # Verificar PyVista
    if python -c "import pyvista as pv" 2>/dev/null; then
        print_success "PyVista instalado correctamente"
    else
        print_error "PyVista no está instalado correctamente"
        exit 1
    fi

    # Verificar FastAPI
    if python -c "import fastapi" 2>/dev/null; then
        print_success "FastAPI instalado correctamente"
    else
        print_error "FastAPI no está instalado correctamente"
        exit 1
    fi

    print_success "Todas las dependencias están instaladas correctamente"
}

# Crear script de activación portable
create_activation_script() {
    print_step "Creando script de activación portable..."

    cat > activate_python_env.sh << 'EOF'
#!/bin/bash
# Script portable para activar el entorno Python de Pollux 3D

# Función para detectar conda
detect_and_activate_conda() {
    if command -v conda &> /dev/null; then
        # Conda ya está en PATH
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
EOF

    chmod +x activate_python_env.sh
    print_success "Script de activación creado: activate_python_env.sh"
}

# Actualizar el script del servidor de preview
update_preview_server_script() {
    print_step "Actualizando script del servidor de preview..."

    cat > app/Services/PreviewService/start_preview_server.sh << 'EOF'
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
EOF

    chmod +x app/Services/PreviewService/start_preview_server.sh
    print_success "Script del servidor de preview actualizado"
}

# Ejecutar todas las funciones
main() {
    print_info "Iniciando configuración del entorno Python..."

    # Detectar o instalar conda
    if ! detect_conda; then
        install_conda
        # Reiniciar shell para cargar conda
        exec "$SHELL" "$0" --continue
    fi

    # Crear entorno
    create_environment

    # Verificar dependencias
    verify_dependencies

    # Crear scripts portables
    create_activation_script
    update_preview_server_script

    print_success "🎉 Configuración completada exitosamente!"
    print_info "Para activar el entorno manualmente: source ./activate_python_env.sh"
    print_info "Para iniciar el servidor: npm run dev:all"
}

# Verificar si es una continuación después de instalar conda
if [ "$1" = "--continue" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    create_environment
    verify_dependencies
    create_activation_script
    update_preview_server_script
    print_success "🎉 Configuración completada exitosamente!"
    exit 0
fi

main "$@"
