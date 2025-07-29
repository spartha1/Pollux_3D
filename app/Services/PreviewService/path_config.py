#!/usr/bin/env python3
"""
Configuración de rutas para el servidor de previews
Elimina rutas absolutas y usa configuración relativa
"""

import os
import json
from pathlib import Path

class PathConfig:
    def __init__(self):
        # Determinar la ruta base del proyecto
        self.project_root = self._find_project_root()
        
        # Cargar configuración desde JSON
        config_path = os.path.join(self.project_root, 'config', 'paths.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Configurar rutas base
        self._setup_paths()
    
    def _find_project_root(self):
        """Encuentra la raíz del proyecto Laravel buscando composer.json"""
        current_dir = Path(__file__).parent.absolute()
        
        # Buscar hacia arriba hasta encontrar composer.json
        while current_dir.parent != current_dir:
            composer_file = current_dir / 'composer.json'
            if composer_file.exists():
                return str(current_dir)
            current_dir = current_dir.parent
        
        # Fallback si no encuentra composer.json
        return str(Path(__file__).parent.parent.parent.absolute())
    
    def _setup_paths(self):
        """Configura todas las rutas basadas en la raíz del proyecto"""
        self.BASE_PATH = self.project_root
        
        # Rutas de storage
        self.STORAGE_APP = os.path.join(self.BASE_PATH, self.config['storage']['app'])
        self.UPLOADS_DIR = os.path.join(self.BASE_PATH, self.config['storage']['uploads'])
        self.MODELS_DIR = os.path.join(self.BASE_PATH, self.config['storage']['models'])
        self.TEMP_DIR = os.path.join(self.BASE_PATH, self.config['storage']['temp'])
        self.PREVIEWS_DIR = os.path.join(self.BASE_PATH, self.config['storage']['previews'])
        self.PUBLIC_STORAGE = os.path.join(self.BASE_PATH, self.config['storage']['public'])
        self.LOGS_DIR = os.path.join(self.BASE_PATH, self.config['storage']['logs'])
        
        # Rutas públicas
        self.PUBLIC_DIR = os.path.join(self.BASE_PATH, self.config['public']['storage'])
        self.PUBLIC_PREVIEWS = os.path.join(self.BASE_PATH, self.config['public']['previews'])
        
        # Configuración del servidor
        self.HOST = self.config['python_server']['host']
        self.PORT = self.config['python_server']['port']
    
    def ensure_directories(self):
        """Crea todos los directorios necesarios si no existen"""
        directories = [
            self.STORAGE_APP,
            self.UPLOADS_DIR,
            self.MODELS_DIR,
            self.TEMP_DIR,
            self.PREVIEWS_DIR,
            self.PUBLIC_STORAGE,
            self.LOGS_DIR,
            self.PUBLIC_DIR,
            self.PUBLIC_PREVIEWS
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"[OK] Directory ensured: {directory}")
    
    def get_absolute_path(self, relative_path):
        """Convierte una ruta relativa de Laravel a ruta absoluta del sistema"""
        if os.path.isabs(relative_path):
            # Si ya es absoluta, verificar que esté dentro del proyecto
            if relative_path.startswith(self.BASE_PATH):
                return relative_path
            else:
                raise ValueError(f"Absolute path outside project: {relative_path}")
        
        # Si es relativa, necesitamos agregarla correctamente
        # Laravel envía rutas como "models/1/archivo.STL" que deben ir a "storage/app/models/1/archivo.STL"
        if relative_path.startswith('models/'):
            # Es una ruta de modelos, agregarla a storage/app/
            full_path = os.path.join(self.STORAGE_APP, relative_path)
        elif relative_path.startswith('uploads/'):
            # Es una ruta de uploads, agregarla a storage/app/
            full_path = os.path.join(self.STORAGE_APP, relative_path)
        else:
            # Para otras rutas, usar la base del proyecto
            full_path = os.path.join(self.BASE_PATH, relative_path)
        
        return full_path
    
    def get_laravel_preview_path(self, file_id):
        """Obtiene la ruta donde Laravel espera las previews"""
        preview_dir = os.path.join(self.PUBLIC_PREVIEWS, str(file_id))
        os.makedirs(preview_dir, exist_ok=True)
        return preview_dir

# Instancia global de configuración
config = PathConfig()
