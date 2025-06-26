import os
from pathlib import Path

# Configuración base
class Config:
    # Directorio base del proyecto
    BASE_DIR = Path(__file__).parent.parent.parent.absolute()

    @classmethod
    def is_production(cls):
        """Detectar si estamos en entorno de producción"""
        return os.getenv('APP_ENV') == 'production'

    @classmethod
    def get_python_paths(cls):
        """Obtener las rutas de Python según el entorno"""
        if cls.is_production():
            return {
                'executable': '/usr/bin/python3',  # Ajustar según el servidor
                'conda_env': '/opt/conda/envs/pollux-preview-env'  # Ajustar según el servidor
            }
        else:
            return {
                'executable': r'C:\Users\Leinad\miniconda3\envs\pollux-preview-env\python.exe',
                'conda_env': r'C:\Users\Leinad\miniconda3\envs\pollux-preview-env'
            }

    # Configuración del entorno Python
    paths = get_python_paths()
    PYTHON_EXECUTABLE = paths['executable']
    CONDA_ENV_PATH = paths['conda_env']

    # Rutas de archivos y directorios
    UPLOAD_DIR = BASE_DIR / 'storage' / 'app' / 'uploads'
    TEMP_DIR = BASE_DIR / 'storage' / 'app' / 'temp'
    PREVIEW_DIR = BASE_DIR / 'storage' / 'app' / 'previews'

    # Configuración del servidor
    @classmethod
    def get_host(cls):
        """Obtener el host según el entorno"""
        return '0.0.0.0' if cls.is_production() else '127.0.0.1'

    HOST = get_host()
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
