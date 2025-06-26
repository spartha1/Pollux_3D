#!/bin/bash

# Activar el entorno conda si existe
if [ -d "/opt/conda/envs/pollux-preview-env" ]; then
    source /opt/conda/etc/profile.d/conda.sh
    conda activate pollux-preview-env
fi

# Configurar variables de entorno
export APP_ENV=production
export PREVIEW_SERVER_PORT=8000

# Iniciar el servidor
echo "Starting Preview Service..."
python app/Services/PreviewService/preview_server.py
