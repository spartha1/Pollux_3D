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

    @classmethod
    def get_port(cls):
        """Obtener el puerto según el entorno y configuración"""
        default_port = 8000
        env_port = os.getenv('PREVIEW_SERVER_PORT')
        if env_port:
            try:
                return int(env_port)
            except ValueError:
                print(f"Warning: Invalid port number {env_port}, using default {default_port}")
                return default_port
        return default_port

    HOST = get_host()
    PORT = get_port()

    # Configuración de logging
    LOG_DIR = BASE_DIR / 'storage' / 'logs'
    LOG_FILE = LOG_DIR / 'preview_service.log'

    # Asegurarse de que existan los directorios necesarios
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
                # Crear directorio si no existe
                directory.mkdir(parents=True, exist_ok=True)

                # Verificar permisos
                if not os.access(directory, os.W_OK):
                    raise PermissionError(f"No write access to '{name}' directory")

                # Limpiar archivos temporales antiguos si es el directorio temp
                if name == 'temp':
                    cls._cleanup_temp_files(directory)

                print(f"✓ Directory '{name}' verified and accessible: {directory}")
            except Exception as e:
                print(f"✗ Error with '{name}' directory: {e}")
                raise

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

# Inicializar configuración
config = Config.setup()
