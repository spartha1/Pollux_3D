@echo off
REM 🚀 Script de Build y Deployment para Pollux 3D (Windows)
REM Este script automatiza todo el proceso de preparación para producción

setlocal EnableDelayedExpansion
set "PROJECT_NAME=Pollux 3D"
set "BUILD_START_TIME=%date% %time%"

echo 🚀 POLLUX 3D - BUILD ^& DEPLOYMENT SCRIPT
echo ========================================
echo 📋 Iniciando build para %PROJECT_NAME%...
echo 🕐 Hora de inicio: %BUILD_START_TIME%
echo.

REM Función para imprimir pasos
set "STEP_COUNT=0"

:print_step
set /a STEP_COUNT+=1
echo ▶️  %~1
goto :eof

:print_success
echo ✅ %~1
goto :eof

:print_error
echo ❌ %~1
pause
exit /b 1

REM 1. Verificar prerrequisitos
call :print_step "1. Verificando prerrequisitos..."

REM Verificar Node.js
node -v >nul 2>&1
if %errorlevel% neq 0 (
    call :print_error "Node.js no está instalado. Instale Node.js primero."
)
for /f "tokens=*" %%i in ('node -v') do set "NODE_VERSION=%%i"
call :print_success "Node.js detectado: %NODE_VERSION%"

REM Verificar npm
npm -v >nul 2>&1
if %errorlevel% neq 0 (
    call :print_error "npm no está instalado."
)
for /f "tokens=*" %%i in ('npm -v') do set "NPM_VERSION=%%i"
call :print_success "npm detectado: %NPM_VERSION%"

REM Verificar PHP
php -v >nul 2>&1
if %errorlevel% neq 0 (
    call :print_error "PHP no está instalado."
)
for /f "tokens=1-3" %%i in ('php -v') do (
    set "PHP_VERSION=%%i %%j %%k"
    goto :php_done
)
:php_done
call :print_success "PHP detectado: %PHP_VERSION%"

REM Verificar Composer
composer -V >nul 2>&1
if %errorlevel% neq 0 (
    call :print_error "Composer no está instalado."
)
for /f "tokens=1-2" %%i in ('composer -V') do (
    set "COMPOSER_VERSION=%%i %%j"
    goto :composer_done
)
:composer_done
call :print_success "Composer detectado: %COMPOSER_VERSION%"

echo.

REM 2. Limpiar instalaciones anteriores
call :print_step "2. Limpiando instalaciones anteriores..."
if exist "node_modules" (
    rmdir /s /q "node_modules"
    call :print_success "node_modules eliminado"
)

if exist "vendor" (
    rmdir /s /q "vendor"
    call :print_success "vendor eliminado"
)

REM Limpiar caché de Laravel
if exist "artisan" (
    php artisan cache:clear >nul 2>&1
    php artisan config:clear >nul 2>&1
    php artisan route:clear >nul 2>&1
    php artisan view:clear >nul 2>&1
    call :print_success "Caché de Laravel limpiado"
)

echo.

REM 3. Instalar dependencias PHP
call :print_step "3. Instalando dependencias PHP..."
if "%NODE_ENV%"=="production" (
    composer install --no-dev --optimize-autoloader --no-interaction
    call :print_success "Dependencias PHP instaladas (producción)"
) else (
    composer install --optimize-autoloader --no-interaction
    call :print_success "Dependencias PHP instaladas (desarrollo)"
)

echo.

REM 4. Instalar dependencias Node.js
call :print_step "4. Instalando dependencias Node.js..."
npm ci
if %errorlevel% neq 0 (
    call :print_error "Error instalando dependencias Node.js"
)
call :print_success "Dependencias Node.js instaladas"

echo.

REM 5. Generar configuración portable
call :print_step "5. Generando configuración portable..."
if exist "artisan" (
    php artisan config:portable --validate
    if !errorlevel! equ 0 (
        php artisan config:portable
        call :print_success "Configuración portable generada"
    ) else (
        call :print_error "Error en configuración portable. Verifique .env"
    )
) else (
    call :print_error "Archivo artisan no encontrado"
)

echo.

REM 6. Build de assets frontend
call :print_step "6. Building assets frontend..."
if "%NODE_ENV%"=="production" (
    npm run build
    if !errorlevel! neq 0 (
        call :print_error "Error en build de producción"
    )
    call :print_success "Assets compilados para producción"
) else (
    npm run build
    if !errorlevel! neq 0 (
        call :print_error "Error en build"
    )
    call :print_success "Assets compilados"
)

echo.

REM 7. Configuración Laravel para producción
if "%NODE_ENV%"=="production" (
    call :print_step "7. Optimizando Laravel para producción..."
    
    REM Generar key si no existe
    findstr /C:"APP_KEY=base64:" .env >nul 2>&1
    if !errorlevel! neq 0 (
        php artisan key:generate --force
        call :print_success "APP_KEY generada"
    )
    
    REM Cachear configuración
    php artisan config:cache
    call :print_success "Configuración cacheada"
    
    REM Cachear rutas
    php artisan route:cache
    call :print_success "Rutas cacheadas"
    
    REM Cachear vistas
    php artisan view:cache
    call :print_success "Vistas cacheadas"
    
    echo.
)

REM 8. Verificar permisos (Windows - limitado)
call :print_step "8. Configurando permisos..."
if exist "storage" (
    call :print_success "Directorio storage verificado"
)

if exist "bootstrap\cache" (
    call :print_success "Directorio bootstrap\cache verificado"
)

echo.

REM 9. Ejecutar migraciones si es necesario
if "%RUN_MIGRATIONS%"=="true" (
    call :print_step "9. Ejecutando migraciones de base de datos..."
    php artisan migrate --force
    call :print_success "Migraciones ejecutadas"
    echo.
)

REM 10. Verificar build
call :print_step "10. Verificando build..."

REM Verificar que los assets fueron compilados
if exist "public\build" (
    if exist "public\build\manifest.json" (
        call :print_success "Assets compilados correctamente"
    ) else (
        call :print_error "Manifest de Vite no encontrado"
    )
) else (
    call :print_error "Directorio public\build no encontrado"
)

REM Verificar configuración portable
if exist "run_manufacturing_analyzer.bat" (
    call :print_success "Scripts portables generados"
) else (
    call :print_error "Scripts portables no generados"
)

echo.

REM Resumen final
set "BUILD_END_TIME=%date% %time%"
echo 🎉 BUILD COMPLETADO EXITOSAMENTE
echo ========================================
echo 📊 Resumen del Build:
echo    • Proyecto: %PROJECT_NAME%
echo    • Inicio: %BUILD_START_TIME%
echo    • Fin: %BUILD_END_TIME%
echo    • Node.js: %NODE_VERSION%
echo    • PHP: %PHP_VERSION%
echo    • Entorno: %NODE_ENV%
echo.
echo ✅ El proyecto está listo para deployment

if "%NODE_ENV%"=="production" (
    echo.
    echo 🚨 RECORDATORIOS PARA PRODUCCIÓN:
    echo    • Configurar servidor web ^(IIS/Apache^)
    echo    • Configurar base de datos
    echo    • Configurar variables de entorno en .env
    echo    • Configurar permisos de directorio
    echo    • Configurar SSL/HTTPS
    echo    • Configurar backup de base de datos
)

echo.
echo Presione cualquier tecla para continuar...
pause >nul
