import os
from pathlib import Path

# Detectar el entorno (desarrollo o producción)
IS_PRODUCTION = os.getenv('APP_ENV') == 'production'

# Configuración base
class Config:
    # Directorio base del proyecto
    BASE_DIR = Path(__file__).parent.parent.parent.absolute()

    # Configuración del entorno Python
    if IS_PRODUCTION:
        # En producción, usar rutas del sistema
        PYTHON_EXECUTABLE = '/usr/bin/python3'  # Ajustar según el servidor
        CONDA_ENV_PATH = '/opt/conda/envs/pollux-preview-env'  # Ajustar según el servidor
    else:
        # En desarrollo, usar rutas locales
        PYTHON_EXECUTABLE = r'C:\Users\Leinad\miniconda3\envs\pollux-preview-env\python.exe'
        CONDA_ENV_PATH = r'C:\Users\Leinad\miniconda3\envs\pollux-preview-env'

    # Rutas de archivos y directorios
    UPLOAD_DIR = BASE_DIR / 'storage' / 'app' / 'uploads'
    TEMP_DIR = BASE_DIR / 'storage' / 'app' / 'temp'
    PREVIEW_DIR = BASE_DIR / 'storage' / 'app' / 'previews'

    # Configuración del servidor
    HOST = '0.0.0.0' if IS_PRODUCTION else '127.0.0.1'
    PORT = int(os.getenv('PREVIEW_SERVER_PORT', 8000))

    # Configuración de logging
    LOG_DIR = BASE_DIR / 'storage' / 'logs'
    LOG_FILE = LOG_DIR / 'preview_service.log'

    # Asegurarse de que existan los directorios necesarios
    @classmethod
    def setup(cls):
        for directory in [cls.UPLOAD_DIR, cls.TEMP_DIR, cls.PREVIEW_DIR, cls.LOG_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

        return cls

# Inicializar configuración
config = Config.setup()
