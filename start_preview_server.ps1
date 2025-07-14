# Activar el entorno conda
conda activate pollux-preview-env

# Iniciar el servidor de vista previa
$env:PYTHONPATH = "$PWD"
uvicorn preview_service:app --host localhost --port 8000 --reload
