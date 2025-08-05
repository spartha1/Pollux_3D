# 🐧 Guía Completa de Migración a Linux - Pollux 3D

## ❌ **NO es suficiente solo ejecutar `./build.sh`**

Para migrar correctamente a Linux, necesitas seguir este proceso completo:

## 🚀 **Opción 1: Configuración Automática (Recomendada)**

### 📥 **Paso 1: Copiar archivos al servidor Linux**
```bash
# Copiar proyecto completo (incluye setup-linux.sh)
scp -r pollux3d/ user@server:/var/www/pollux3d/
# O clonar desde git
git clone tu-repo.git /var/www/pollux3d

cd /var/www/pollux3d
```

### 🔧 **Paso 2: Ejecutar configuración automática**
```bash
# Hacer ejecutable
chmod +x setup-linux.sh

# Ejecutar configuración automática
./setup-linux.sh
```

**¡Esto instalará automáticamente TODO lo necesario!**

### ⚡ **Paso 3: Configurar proyecto específico**
```bash
# Reiniciar terminal o recargar bash
source ~/.bashrc

# Activar entorno conda
conda activate pollux-preview-env

# Configurar .env
cp .env.linux.example .env
nano .env  # Editar con tus configuraciones

# AHORA SÍ ejecutar build
chmod +x build.sh
export NODE_ENV=production
./build.sh
```

## 🛠️ **Opción 2: Configuración Manual**

### 📋 **Paso 1: Instalar dependencias del sistema**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y curl wget git unzip software-properties-common

# Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# PHP 8.2
sudo add-apt-repository ppa:ondrej/php -y
sudo apt update
sudo apt install -y php8.2 php8.2-fpm php8.2-mysql php8.2-xml \
    php8.2-curl php8.2-zip php8.2-mbstring php8.2-gd php8.2-bcmath

# Composer
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer

# Ghostscript para análisis AI/EPS
sudo apt install -y ghostscript

# Nginx (opcional)
sudo apt install -y nginx

# MySQL (opcional) 
sudo apt install -y mysql-server
```

### 📋 **Paso 2: Instalar Miniconda**
```bash
cd /tmp
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3

# Inicializar conda
$HOME/miniconda3/bin/conda init bash
source ~/.bashrc
```

### 📋 **Paso 3: Crear entorno Python**
```bash
# Crear entorno
conda create -n pollux-preview-env python=3.9 -y

# Activar entorno
conda activate pollux-preview-env

# Instalar dependencias Python
pip install numpy stl-numpy pythonocc-core pyvista matplotlib
```

### 📋 **Paso 4: Configurar el proyecto**
```bash
cd /var/www/pollux3d

# Copiar y editar .env
cp .env.linux.example .env
nano .env
```

**Ejemplo de .env para Linux:**
```ini
# Configuración para Linux
CONDA_ROOT=/home/username/miniconda3
CONDA_ENV=pollux-preview-env
PYTHON_EXECUTABLE=/home/username/miniconda3/envs/pollux-preview-env/bin/python

# O mejor, usar variables del sistema
# CONDA_ROOT=${HOME}/miniconda3
# PYTHON_EXECUTABLE=${CONDA_PREFIX}/bin/python

PROJECT_ROOT=/var/www/pollux3d
```

### 📋 **Paso 5: Ejecutar build**
```bash
# Activar entorno conda
conda activate pollux-preview-env

# Hacer ejecutable y ejecutar
chmod +x build.sh
export NODE_ENV=production
./build.sh
```

## 🔍 **Lo que hace `./build.sh` internamente:**

1. ✅ **Verifica prerrequisitos** (Node.js, PHP, Composer, Conda)
2. ✅ **Limpia** instalaciones anteriores
3. ✅ **Instala** dependencias PHP y Node.js
4. ✅ **Genera** configuración portable automática
5. ✅ **Compila** assets frontend optimizados
6. ✅ **Optimiza** Laravel para producción
7. ✅ **Configura** permisos
8. ✅ **Valida** el resultado

## 📊 **Comparación de Opciones:**

| Opción | Tiempo | Dificultad | Automatización |
|--------|--------|------------|----------------|
| **setup-linux.sh** | ~15 min | Muy Fácil | 95% automático |
| **Manual** | ~45 min | Intermedio | Manual |
| **Solo build.sh** | ❌ Falla | ❌ No funciona | Sin prerrequisitos |

## ✅ **Resumen: Proceso Correcto**

### **Para migración completa:**
```bash
# 1. Copiar proyecto
scp -r pollux3d/ user@server:/var/www/pollux3d/

# 2. Configurar servidor automáticamente
cd /var/www/pollux3d
chmod +x setup-linux.sh
./setup-linux.sh

# 3. Configurar proyecto específico
source ~/.bashrc
conda activate pollux-preview-env
cp .env.linux.example .env
nano .env  # Editar configuraciones

# 4. AHORA SÍ, ejecutar build
chmod +x build.sh
export NODE_ENV=production
./build.sh
```

## 🚨 **Errores Comunes y Soluciones**

### ❌ **Error: "Node.js not found"**
```bash
# Instalar Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### ❌ **Error: "Composer not found"**
```bash
# Instalar Composer
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer
```

### ❌ **Error: "Python executable not found"**
```bash
# Verificar configuración conda
conda activate pollux-preview-env
echo $CONDA_PREFIX
# Actualizar .env con la ruta correcta
```

### ❌ **Error: "Permission denied"**
```bash
# Hacer ejecutables los scripts
chmod +x build.sh setup-linux.sh
chmod +x *.sh

# Configurar permisos de storage
sudo chown -R www-data:www-data storage bootstrap/cache
sudo chmod -R 775 storage bootstrap/cache
```

## 🎯 **Respuesta Final**

### ❌ **NO:** Solo `./build.sh` no es suficiente
### ✅ **SÍ:** Necesitas configurar el servidor primero

**La forma más fácil:**
```bash
./setup-linux.sh   # Configura todo automáticamente
# Luego editar .env
./build.sh          # AHORA SÍ funciona perfectamente
```

**¡Con esto tendrás Pollux 3D funcionando en Linux en ~15 minutos!** 🚀
