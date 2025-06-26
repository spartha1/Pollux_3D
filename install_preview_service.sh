#!/bin/bash

# Verificar si conda está instalado
if ! command -v conda &> /dev/null; then
    echo "Instalando Miniconda..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p /opt/conda
    rm miniconda.sh
fi

# Agregar conda a PATH
export PATH="/opt/conda/bin:$PATH"

# Crear el entorno
conda env create -f environment.yml

# Activar el entorno
source /opt/conda/etc/profile.d/conda.sh
conda activate pollux-preview-env

# Crear directorios necesarios
mkdir -p storage/app/{uploads,temp,previews}
mkdir -p storage/logs

# Configurar permisos
chmod -R 775 storage
chown -R www-data:www-data storage

# Instalar supervisor para manejar el proceso
apt-get update
apt-get install -y supervisor

# Configurar supervisor
cat > /etc/supervisor/conf.d/preview-service.conf << EOL
[program:preview-service]
directory=/var/www/polluxweb
command=/opt/conda/envs/pollux-preview-env/bin/python app/Services/PreviewService/preview_server.py
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/preview-service.err.log
stdout_logfile=/var/log/preview-service.out.log
environment=APP_ENV="production",PREVIEW_SERVER_PORT="8000"
EOL

# Reiniciar supervisor
supervisorctl reread
supervisorctl update
