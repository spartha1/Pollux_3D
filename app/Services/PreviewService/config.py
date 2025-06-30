import os
from pathlib import Path

class Config:
    """Configuration class for the preview service"""
    # Rutas base
    BASE_DIR = Path(__file__).parent.parent.parent.absolute()

    # Valores por defecto (se actualizarán en initialize())
    HOST = None
    PORT = None
    PYTHON_EXECUTABLE = None
    CONDA_ENV_PATH = None

    # Directorios (se crearán en setup())
    UPLOAD_DIR = None
    TEMP_DIR = None
    PREVIEW_DIR = None
    LOG_DIR = None
    LOG_FILE = None

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

    @classmethod
    def get_host(cls):
        """Obtener el host según el entorno"""
        return '0.0.0.0' if cls.is_production() else '127.0.0.1'

    @classmethod
    def get_port(cls):
        """Obtener el puerto según el entorno y configuración"""
        default_port = 8050
        env_port = os.getenv('PREVIEW_SERVER_PORT')
        if env_port:
            try:
                return int(env_port)
            except ValueError:
                print(f"Warning: Invalid port number {env_port}, using default {default_port}")
        return default_port

    @classmethod
    def setup(cls):
        """Configurar directorios y permisos necesarios"""
        directories = {
            'uploads': cls.UPLOAD_DIR,
            'temp': cls.TEMP_DIR,
            'previews': cls.PREVIEW_DIR,
            'logs': cls.LOG_DIR
        }

        for name, directory in directories.items():
            try:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"[OK] Directory '{name}' verified: {directory}")
            except Exception as e:
                print(f"[ERROR] Error creating '{name}' directory: {e}")
                raise
        return cls

    @classmethod
    def initialize(cls):
        """Initialize configuration"""
        # Configurar rutas base
        cls.UPLOAD_DIR = cls.BASE_DIR / 'storage' / 'app' / 'uploads'
        cls.TEMP_DIR = cls.BASE_DIR / 'storage' / 'app' / 'temp'
        cls.PREVIEW_DIR = cls.BASE_DIR / 'storage' / 'app' / 'previews'
        cls.LOG_DIR = cls.BASE_DIR / 'storage' / 'logs'
        cls.LOG_FILE = cls.LOG_DIR / 'preview_service.log'

        # Configurar Python y entorno
        paths = cls.get_python_paths()
        cls.PYTHON_EXECUTABLE = paths['executable']
        cls.CONDA_ENV_PATH = paths['conda_env']

        # Configurar servidor
        cls.HOST = cls.get_host()
        cls.PORT = cls.get_port()

        # Configurar directorios
        cls.setup()

        return cls

    @staticmethod
    def _cleanup_temp_files(temp_dir: Path, max_age_hours: int = 24):
        """Limpiar archivos temporales más antiguos que max_age_hours"""
        import time
        current_time = time.time()

        try:
            for file_path in temp_dir.glob('*'):
                if file_path.is_file():
                    file_age_hours = (current_time - file_path.stat().st_mtime) / 3600
                    if file_age_hours > max_age_hours:
                        file_path.unlink(missing_ok=True)
        except Exception as e:
            print(f"Warning: Error cleaning temp files: {e}")

# Inicializar la configuración
config = Config.initialize()
