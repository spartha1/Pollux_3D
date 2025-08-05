# 🚀 Guía de Migración a Servidor - Pollux 3D

Esta guía explica cómo migrar el proyecto Pollux 3D de un entorno de desarrollo local a un servidor de producción, eliminando todas las dependencias de rutas absolutas.

## 📋 Resumen de Cambios Realizados

### ✅ Archivos Configurados para Portabilidad

1. **Configuración Laravel**
   - `.env` - Variables de entorno configurables
   - `.env.example` - Template con ejemplos para diferentes OS
   - `config/services.php` - Configuración multiplataforma
   - `app/Http/Controllers/FileAnalysisController.php` - Detección automática de rutas

2. **Scripts de Sistema**
   - `generate_portable_config.php` - Generador automático de configuración
   - `app/Console/Commands/GeneratePortableConfig.php` - Comando Artisan integrado
   - Templates para archivos .bat/.sh portables

3. **Analizadores Python**
   - `app/Services/FileAnalyzers/portable_config.py` - Sistema de configuración Python
   - Scripts de análisis actualizados para usar configuración portable

## 🔧 Proceso de Migración

### Paso 1: Preparar el Servidor Destino

1. **Instalar Dependencias Base**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip nginx php8.2-fpm php8.2-mysql composer
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip nginx php-fpm php-mysql composer
   ```

2. **Instalar Miniconda/Anaconda**
   ```bash
   # Linux
   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
   bash Miniconda3-latest-Linux-x86_64.sh
   
   # Crear el entorno conda
   conda create -n pollux-preview-env python=3.9
   conda activate pollux-preview-env
   pip install numpy stl-numpy pythonocc-core pyvista
   ```

3. **Instalar Ghostscript (para análisis AI/EPS)**
   ```bash
   # Ubuntu/Debian
   sudo apt install ghostscript
   
   # CentOS/RHEL
   sudo yum install ghostscript
   ```

### Paso 2: Configurar Variables de Entorno

1. **Copiar el proyecto al servidor**
   ```bash
   # Ejemplo: copiar a /var/www/pollux3d
   sudo mkdir -p /var/www/pollux3d
   sudo chown -R $USER:$USER /var/www/pollux3d
   ```

2. **Configurar archivo .env**
   ```bash
   cd /var/www/pollux3d
   cp .env.example .env
   ```

3. **Editar .env para el servidor Linux**
   ```ini
   # Base de datos
   DB_HOST=localhost
   DB_DATABASE=pollux_3d
   DB_USERNAME=pollux_user
   DB_PASSWORD=secure_password
   
   # Python/Conda Configuration para Linux
   CONDA_ROOT=/home/username/miniconda3
   CONDA_ENV=pollux-preview-env
   PYTHON_EXECUTABLE=/home/username/miniconda3/envs/pollux-preview-env/bin/python
   
   # O usar variables del sistema (recomendado)
   CONDA_ROOT=${CONDA_ROOT_PATH}
   PYTHON_EXECUTABLE=${CONDA_PREFIX}/bin/python
   
   # Rutas del proyecto
   PROJECT_ROOT=/var/www/pollux3d
   STORAGE_PATH=/var/www/pollux3d/storage
   ANALYZER_PATH=/var/www/pollux3d/app/Services/FileAnalyzers
   ```

### Paso 3: Generar Configuración Portable

1. **Ejecutar el comando de generación**
   ```bash
   # Validar configuración primero
   php artisan config:portable --validate
   
   # Generar scripts portables
   php artisan config:portable
   ```

2. **Verificar archivos generados**
   - `run_manufacturing_analyzer.sh` (Linux)
   - `app/Services/FileAnalyzers/run_with_conda.sh` (Linux)

### Paso 4: Configurar Permisos

```bash
# Dar permisos a los scripts
chmod +x run_manufacturing_analyzer.sh
chmod +x app/Services/FileAnalyzers/run_with_conda.sh

# Configurar permisos de storage
sudo chown -R www-data:www-data storage/
sudo chmod -R 775 storage/
```

### Paso 5: Instalar Dependencias Laravel

```bash
# Instalar dependencias PHP
composer install --no-dev --optimize-autoloader

# Generar key de aplicación
php artisan key:generate

# Ejecutar migraciones
php artisan migrate --force

# Optimizar para producción
php artisan config:cache
php artisan route:cache
php artisan view:cache
```

## 🛠️ Variables de Entorno Importantes

### Para Windows (Desarrollo)
```ini
CONDA_ROOT=C:\Users\Username\miniconda3
CONDA_ENV=pollux-preview-env
PYTHON_EXECUTABLE=C:\Users\Username\miniconda3\envs\pollux-preview-env\python.exe
```

### Para Linux (Producción)
```ini
CONDA_ROOT=/home/username/miniconda3
CONDA_ENV=pollux-preview-env
PYTHON_EXECUTABLE=/home/username/miniconda3/envs/pollux-preview-env/bin/python
```

### Usando Variables del Sistema (Recomendado)
```ini
CONDA_ROOT=${CONDA_ROOT_PATH}
PYTHON_EXECUTABLE=${CONDA_PREFIX}/bin/python
PROJECT_ROOT=${PWD}
```

## 🔍 Verificación Post-Migración

1. **Probar configuración Python**
   ```bash
   php artisan config:portable --validate
   ```

2. **Probar análisis de archivos**
   ```bash
   # Probar analizador STL
   ./run_manufacturing_analyzer.sh storage/app/test.stl
   
   # Probar analizador AI/EPS
   ./app/Services/FileAnalyzers/run_with_conda.sh app/Services/FileAnalyzers/analyze_ai_eps.py storage/app/test.ai
   ```

3. **Verificar logs**
   ```bash
   tail -f storage/logs/laravel.log
   ```

## 🚨 Solución de Problemas Comunes

### Error: "Python executable not found"
```bash
# Verificar que conda esté activado
conda activate pollux-preview-env
echo $CONDA_PREFIX

# Actualizar .env con la ruta correcta
PYTHON_EXECUTABLE=$CONDA_PREFIX/bin/python
```

### Error: "Ghostscript not found"
```bash
# Verificar instalación
which gs
gs --version

# Si no está instalado
sudo apt install ghostscript  # Ubuntu/Debian
sudo yum install ghostscript  # CentOS/RHEL
```

### Error: "Permission denied"
```bash
# Verificar permisos de scripts
ls -la *.sh
chmod +x *.sh

# Verificar permisos de storage
sudo chown -R www-data:www-data storage/
sudo chmod -R 775 storage/
```

## 📁 Estructura de Archivos Post-Migración

```
pollux3d/
├── .env                              # Configuración específica del servidor
├── generate_portable_config.php     # Generador standalone
├── run_manufacturing_analyzer.sh    # Script Linux generado
├── run_manufacturing_analyzer.bat   # Script Windows (backup)
├── app/
│   ├── Console/Commands/
│   │   └── GeneratePortableConfig.php
│   └── Services/FileAnalyzers/
│       ├── portable_config.py       # Config Python portable
│       ├── run_with_conda.sh       # Wrapper Linux generado
│       └── run_with_conda.bat      # Wrapper Windows (backup)
└── config/
    └── services.php                 # Config Laravel multiplataforma
```

## ✅ Checklist de Migración

- [ ] Servidor configurado con PHP, Python, Conda
- [ ] Ghostscript instalado (para AI/EPS)
- [ ] Variables de entorno configuradas en .env
- [ ] Scripts generados con `php artisan config:portable`
- [ ] Permisos configurados correctamente
- [ ] Dependencias Laravel instaladas
- [ ] Base de datos migrada
- [ ] Configuración validada con `--validate`
- [ ] Pruebas de análisis funcionando
- [ ] Logs sin errores

## 🔄 Mantenimiento

Para futuras migraciones o cambios de servidor:

1. Actualizar variables en `.env`
2. Ejecutar `php artisan config:portable`
3. Verificar con `php artisan config:portable --validate`
4. Probar funcionalidad crítica

¡El proyecto ahora es completamente portable y listo para producción! 🎉
