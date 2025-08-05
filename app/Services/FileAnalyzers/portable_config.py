#!/usr/bin/env python3
"""
Sistema de configuración portable para analizadores Python
Detecta automáticamente rutas del sistema y herramientas
"""

import os
import sys
import platform
from pathlib import Path
import shutil

class PortablePythonConfig:
    """Configuración portable para analizadores Python"""
    
    def __init__(self):
        self.is_windows = platform.system() == 'Windows'
        self.project_root = self._detect_project_root()
        self.ghostscript_path = self._detect_ghostscript()
        
    def _detect_project_root(self):
        """Detectar la raíz del proyecto Laravel"""
        current_path = Path(__file__).parent
        
        # Buscar hacia arriba hasta encontrar composer.json
        while current_path != current_path.parent:
            if (current_path / 'composer.json').exists():
                return str(current_path)
            current_path = current_path.parent
            
        # Si no encuentra composer.json, usar directorio actual
        return str(Path.cwd())
    
    def _detect_ghostscript(self):
        """Detectar la instalación de Ghostscript"""
        if self.is_windows:
            # Posibles ubicaciones de Ghostscript en Windows
            possible_paths = [
                r"C:\Program Files\gs\gs*\bin\gswin64c.exe",
                r"C:\Program Files (x86)\gs\gs*\bin\gswin32c.exe",
            ]
            
            import glob
            for pattern in possible_paths:
                matches = glob.glob(pattern)
                if matches:
                    # Tomar la versión más reciente
                    return max(matches)
            
            # Buscar en PATH
            gs_exe = shutil.which('gswin64c.exe') or shutil.which('gswin32c.exe')
            if gs_exe:
                return gs_exe
                
        else:
            # Linux/Mac
            gs_exe = shutil.which('gs')
            if gs_exe:
                return gs_exe
        
        return None
    
    def get_storage_path(self, relative_path=""):
        """Obtener ruta de storage del proyecto"""
        storage_path = Path(self.project_root) / "storage" / "app"
        if relative_path:
            storage_path = storage_path / relative_path
        return str(storage_path)
    
    def get_temp_path(self):
        """Obtener directorio temporal del sistema"""
        if self.is_windows:
            return os.environ.get('TEMP', r'C:\temp')
        else:
            return '/tmp'
    
    def to_dict(self):
        """Exportar configuración como diccionario"""
        return {
            'is_windows': self.is_windows,
            'project_root': self.project_root,
            'ghostscript_path': self.ghostscript_path,
            'storage_path': self.get_storage_path(),
            'temp_path': self.get_temp_path(),
        }

# Instancia global de configuración
config = PortablePythonConfig()

def get_config():
    """Obtener instancia de configuración"""
    return config

if __name__ == "__main__":
    # Test de configuración
    print("🔧 Configuración Portable Python - Pollux 3D")
    print("=" * 50)
    
    config_dict = config.to_dict()
    for key, value in config_dict.items():
        print(f"{key}: {value}")
    
    print("\n✅ Configuración cargada exitosamente")
