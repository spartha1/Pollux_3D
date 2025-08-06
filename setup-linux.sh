#!/bin/bash
# 🐧 Script de Configuración Automática para Linux - Pollux 3D
# Este script configura automáticamente un servidor Linux para ejecutar Pollux 3D

set -e

echo "🐧 POLLUX 3D - CONFIGURACIÓN AUTOMÁTICA LINUX"
echo "============================================="

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
    exit 1
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Detectar distribución de Linux
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    else
        print_error "No se pudo detectar la distribución de Linux"
    fi
}

# Función para Ubuntu/Debian
setup_ubuntu_debian() {
    print_step "Configurando para Ubuntu/Debian..."
    
    # Actualizar sistema
    sudo apt update && sudo apt upgrade -y
    
    # Instalar dependencias base
    sudo apt install -y curl wget git unzip software-properties-common
    
    # Instalar Node.js 18.x
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
    
    # Instalar PHP 8.2
    sudo add-apt-repository ppa:ondrej/php -y
    sudo apt update
    sudo apt install -y php8.2 php8.2-fpm php8.2-mysql php8.2-xml php8.2-curl php8.2-zip php8.2-mbstring php8.2-gd php8.2-bcmath
    
    # Instalar Composer
    curl -sS https://getcomposer.org/installer | php
    sudo mv composer.phar /usr/local/bin/composer
    
    # Instalar Ghostscript
    sudo apt install -y ghostscript
    
    # Instalar nginx (opcional)
    read -p "¿Instalar nginx? (y/n): " install_nginx
    if [[ $install_nginx == "y" ]]; then
        sudo apt install -y nginx
        print_success "nginx instalado"
    fi
    
    # Instalar MySQL (opcional)
    read -p "¿Instalar MySQL? (y/n): " install_mysql
    if [[ $install_mysql == "y" ]]; then
        sudo apt install -y mysql-server
        print_success "MySQL instalado"
    fi
}

# Función para CentOS/RHEL
setup_centos_rhel() {
    print_step "Configurando para CentOS/RHEL..."
    
    # Actualizar sistema
    sudo yum update -y
    
    # Instalar dependencias base
    sudo yum install -y curl wget git unzip
    
    # Instalar Node.js
    curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
    sudo yum install -y nodejs
    
    # Instalar PHP
    sudo yum install -y php php-fpm php-mysql php-xml php-curl php-zip php-mbstring php-gd php-bcmath
    
    # Instalar Composer
    curl -sS https://getcomposer.org/installer | php
    sudo mv composer.phar /usr/local/bin/composer
    
    # Instalar Ghostscript
    sudo yum install -y ghostscript
}

# Instalar Miniconda
install_miniconda() {
    print_step "Instalando Miniconda..."
    
    if command -v conda &> /dev/null; then
        print_info "Conda ya está instalado"
        return 0
    fi
    
    cd /tmp
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
    
    # Inicializar conda
    $HOME/miniconda3/bin/conda init bash
    
    # Recargar shell
    source ~/.bashrc
    
    print_success "Miniconda instalado"
}

# Crear entorno conda
setup_conda_env() {
    print_step "Configurando entorno conda..."
    
    # Activar conda
    source $HOME/miniconda3/bin/activate
    
    # Crear entorno
    conda create -n pollux-preview-env python=3.9 -y
    
    # Activar entorno
    conda activate pollux-preview-env
    
    # Instalar dependencias Python
    pip install numpy stl-numpy pythonocc-core pyvista matplotlib
    
    print_success "Entorno conda configurado"
}

# Configurar permisos
setup_permissions() {
    print_step "Configurando permisos..."
    
    # Crear grupo www-data si no existe
    if ! getent group www-data > /dev/null 2>&1; then
        sudo groupadd www-data
    fi
    
    # Agregar usuario actual al grupo www-data
    sudo usermod -a -G www-data $USER
    
    print_success "Permisos configurados"
}

# Función principal
main() {
    echo -e "${BLUE}🚀 Iniciando configuración automática...${NC}"
    echo ""
    
    # Detectar distribución
    detect_distro
    print_info "Distribución detectada: $DISTRO $VERSION"
    
    # Configurar según distribución
    case $DISTRO in
        ubuntu|debian)
            setup_ubuntu_debian
            ;;
        centos|rhel|fedora)
            setup_centos_rhel
            ;;
        *)
            print_error "Distribución no soportada: $DISTRO"
            ;;
    esac
    
    # Instalar Miniconda
    install_miniconda
    
    # Configurar entorno conda
    setup_conda_env
    
    # Configurar permisos
    setup_permissions
    
    echo ""
    echo -e "${GREEN}🎉 CONFIGURACIÓN COMPLETADA${NC}"
    echo "================================"
    echo -e "${BLUE}📋 Resumen de lo instalado:${NC}"
    echo "   • Node.js: $(node -v)"
    echo "   • npm: $(npm -v)"
    echo "   • PHP: $(php -v | head -n 1 | cut -d' ' -f2)"
    echo "   • Composer: $(composer -V | cut -d' ' -f3)"
    echo "   • Conda: $(conda -V)"
    echo "   • Ghostscript: $(gs --version)"
    echo ""
    echo -e "${YELLOW}🔄 PRÓXIMOS PASOS:${NC}"
    echo "   1. Reinicie la terminal o ejecute: source ~/.bashrc"
    echo "   2. Active el entorno conda: conda activate pollux-preview-env"
    echo "   3. Configure el archivo .env del proyecto"
    echo "   4. Ejecute el build: ./build.sh"
    echo ""
    echo -e "${GREEN}✅ El servidor está listo para Pollux 3D${NC}"
}

# Verificar si se ejecuta como root
if [[ $EUID -eq 0 ]]; then
   print_error "No ejecute este script como root (sudo). Ejecute como usuario normal."
fi

# Ejecutar función principal
main "$@"
