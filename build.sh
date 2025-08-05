#!/bin/bash
# 🚀 Script de Build y Deployment para Pollux 3D
# Este script automatiza todo el proceso de preparación para producción

set -e  # Salir si hay errores

echo "🚀 POLLUX 3D - BUILD & DEPLOYMENT SCRIPT"
echo "========================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
PROJECT_NAME="Pollux 3D"
BUILD_START_TIME=$(date)

echo -e "${BLUE}📋 Iniciando build para ${PROJECT_NAME}...${NC}"
echo -e "${BLUE}🕐 Hora de inicio: ${BUILD_START_TIME}${NC}"
echo ""

# Función para imprimir pasos
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

# 1. Verificar prerrequisitos
print_step "1. Verificando prerrequisitos..."

# Verificar Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js no está instalado. Instale Node.js primero."
fi
NODE_VERSION=$(node -v)
print_success "Node.js detectado: $NODE_VERSION"

# Verificar npm
if ! command -v npm &> /dev/null; then
    print_error "npm no está instalado."
fi
NPM_VERSION=$(npm -v)
print_success "npm detectado: $NPM_VERSION"

# Verificar PHP
if ! command -v php &> /dev/null; then
    print_error "PHP no está instalado."
fi
PHP_VERSION=$(php -v | head -n 1)
print_success "PHP detectado: $PHP_VERSION"

# Verificar Composer
if ! command -v composer &> /dev/null; then
    print_error "Composer no está instalado."
fi
COMPOSER_VERSION=$(composer -V | head -n 1)
print_success "Composer detectado: $COMPOSER_VERSION"

echo ""

# 2. Limpiar instalaciones anteriores
print_step "2. Limpiando instalaciones anteriores..."
if [ -d "node_modules" ]; then
    rm -rf node_modules
    print_success "node_modules eliminado"
fi

if [ -d "vendor" ]; then
    rm -rf vendor
    print_success "vendor eliminado"
fi

# Limpiar caché de Laravel
if [ -f "artisan" ]; then
    php artisan cache:clear || true
    php artisan config:clear || true
    php artisan route:clear || true
    php artisan view:clear || true
    print_success "Caché de Laravel limpiado"
fi

echo ""

# 3. Instalar dependencias PHP
print_step "3. Instalando dependencias PHP..."
if [ "$NODE_ENV" = "production" ]; then
    composer install --no-dev --optimize-autoloader --no-interaction
    print_success "Dependencias PHP instaladas (producción)"
else
    composer install --optimize-autoloader --no-interaction
    print_success "Dependencias PHP instaladas (desarrollo)"
fi

echo ""

# 4. Instalar dependencias Node.js
print_step "4. Instalando dependencias Node.js..."
npm ci
print_success "Dependencias Node.js instaladas"

echo ""

# 5. Generar configuración portable
print_step "5. Generando configuración portable..."
if [ -f "artisan" ]; then
    php artisan config:portable --validate
    if [ $? -eq 0 ]; then
        php artisan config:portable
        print_success "Configuración portable generada"
    else
        print_error "Error en configuración portable. Verifique .env"
    fi
else
    print_error "Archivo artisan no encontrado"
fi

echo ""

# 6. Build de assets frontend
print_step "6. Building assets frontend..."
if [ "$NODE_ENV" = "production" ]; then
    npm run build
    print_success "Assets compilados para producción"
else
    npm run build
    print_success "Assets compilados"
fi

echo ""

# 7. Configuración Laravel para producción
if [ "$NODE_ENV" = "production" ]; then
    print_step "7. Optimizando Laravel para producción..."
    
    # Generar key si no existe
    if ! grep -q "APP_KEY=base64:" .env; then
        php artisan key:generate --force
        print_success "APP_KEY generada"
    fi
    
    # Cachear configuración
    php artisan config:cache
    print_success "Configuración cacheada"
    
    # Cachear rutas
    php artisan route:cache
    print_success "Rutas cacheadas"
    
    # Cachear vistas
    php artisan view:cache
    print_success "Vistas cacheadas"
    
    echo ""
fi

# 8. Verificar permisos
print_step "8. Configurando permisos..."
if [ -d "storage" ]; then
    chmod -R 775 storage
    print_success "Permisos de storage configurados"
fi

if [ -d "bootstrap/cache" ]; then
    chmod -R 775 bootstrap/cache
    print_success "Permisos de bootstrap/cache configurados"
fi

# Scripts ejecutables
chmod +x *.sh 2>/dev/null || true
find . -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true
print_success "Scripts marcados como ejecutables"

echo ""

# 9. Ejecutar migraciones si es necesario
if [ "$RUN_MIGRATIONS" = "true" ]; then
    print_step "9. Ejecutando migraciones de base de datos..."
    php artisan migrate --force
    print_success "Migraciones ejecutadas"
    echo ""
fi

# 10. Verificar build
print_step "10. Verificando build..."

# Verificar que los assets fueron compilados
if [ -d "public/build" ]; then
    MANIFEST_FILE="public/build/manifest.json"
    if [ -f "$MANIFEST_FILE" ]; then
        print_success "Assets compilados correctamente"
    else
        print_error "Manifest de Vite no encontrado"
    fi
else
    print_error "Directorio public/build no encontrado"
fi

# Verificar configuración portable
if [ -f "run_manufacturing_analyzer.sh" ] || [ -f "run_manufacturing_analyzer.bat" ]; then
    print_success "Scripts portables generados"
else
    print_error "Scripts portables no generados"
fi

echo ""

# Resumen final
BUILD_END_TIME=$(date)
echo -e "${GREEN}🎉 BUILD COMPLETADO EXITOSAMENTE${NC}"
echo "========================================"
echo -e "${BLUE}📊 Resumen del Build:${NC}"
echo -e "   • Proyecto: ${PROJECT_NAME}"
echo -e "   • Inicio: ${BUILD_START_TIME}"
echo -e "   • Fin: ${BUILD_END_TIME}"
echo -e "   • Node.js: ${NODE_VERSION}"
echo -e "   • PHP: ${PHP_VERSION}"
echo -e "   • Entorno: ${NODE_ENV:-development}"
echo ""
echo -e "${GREEN}✅ El proyecto está listo para deployment${NC}"

if [ "$NODE_ENV" = "production" ]; then
    echo ""
    echo -e "${YELLOW}🚨 RECORDATORIOS PARA PRODUCCIÓN:${NC}"
    echo "   • Configurar servidor web (nginx/apache)"
    echo "   • Configurar base de datos"
    echo "   • Configurar variables de entorno en .env"
    echo "   • Configurar permisos de directorio"
    echo "   • Configurar SSL/HTTPS"
    echo "   • Configurar backup de base de datos"
fi
