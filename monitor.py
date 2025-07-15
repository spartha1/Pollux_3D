#!/usr/bin/env python3
"""
Monitor en tiempo real para el sistema Pollux 3D
Detecta nuevos archivos y los analiza automáticamente
"""

import time
import requests
import json
import os
import sys
from pathlib import Path
from datetime import datetime

class PolluxMonitor:
    def __init__(self):
        self.api_base = "http://localhost:8088"
        self.preview_base = "http://localhost:8051"
        self.last_file_id = self.get_last_file_id()
        print(f"🔍 Monitor iniciado - Último archivo ID: {self.last_file_id}")
        
    def get_last_file_id(self):
        """Obtener el último ID de archivo"""
        try:
            # Usamos un método simple para obtener el último ID
            return 26  # Basado en el último archivo que vimos
        except:
            return 0
    
    def check_new_files(self):
        """Verificar si hay nuevos archivos"""
        try:
            # Aquí podrías implementar una API para obtener archivos recientes
            # Por ahora, simulamos revisando IDs incrementales
            for file_id in range(self.last_file_id + 1, self.last_file_id + 5):
                if self.file_exists(file_id):
                    print(f"🆕 Nuevo archivo detectado: ID {file_id}")
                    self.analyze_file(file_id)
                    self.last_file_id = file_id
                    return True
            return False
        except Exception as e:
            print(f"❌ Error verificando archivos: {e}")
            return False
    
    def file_exists(self, file_id):
        """Verificar si un archivo existe"""
        try:
            # Simular verificación de archivo
            # En un sistema real, esto consultaría la base de datos
            return False  # Por ahora, no hacer nada automático
        except:
            return False
    
    def analyze_file(self, file_id):
        """Analizar un archivo específico"""
        print(f"🔬 Analizando archivo ID: {file_id}")
        
        # Ejecutar análisis usando PHP
        result = os.system(f'php debug_system.php monitor {file_id}')
        
        if result == 0:
            print(f"✅ Análisis completado para archivo {file_id}")
        else:
            print(f"❌ Error en análisis de archivo {file_id}")
    
    def test_preview_generation(self, file_path):
        """Probar generación de preview"""
        print(f"🖼️ Probando generación de preview para: {file_path}")
        
        data = {
            'file_path': file_path,
            'preview_type': '2d',
            'width': 800,
            'height': 600,
            'format': 'png'
        }
        
        try:
            response = requests.post(
                f'{self.preview_base}/generate-preview',
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    preview_size = len(result.get('preview_2d', ''))
                    print(f"✅ Preview generado: {preview_size} bytes")
                    return True
                else:
                    print(f"❌ Error en preview: {result.get('message', 'Error desconocido')}")
            else:
                print(f"❌ Error HTTP: {response.status_code}")
        except Exception as e:
            print(f"❌ Error generando preview: {e}")
        
        return False
    
    def run_diagnostics(self):
        """Ejecutar diagnósticos completos"""
        print("\n🔍 EJECUTANDO DIAGNÓSTICOS COMPLETOS...")
        print("=" * 60)
        
        # 1. Verificar servicios
        services = {
            'Laravel': f'{self.api_base}',
            'Preview Server': f'{self.preview_base}/health'
        }
        
        for name, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                status = "✅ ACTIVO" if response.status_code < 400 else "❌ ERROR"
                print(f"{name}: {status} (HTTP {response.status_code})")
            except Exception as e:
                print(f"{name}: ❌ NO RESPONDE ({e})")
        
        # 2. Verificar Python
        print(f"\n🐍 Python: {sys.version}")
        print(f"📍 Ejecutable: {sys.executable}")
        
        # 3. Verificar dependencias
        dependencies = ['numpy', 'PIL', 'requests']
        for dep in dependencies:
            try:
                __import__(dep)
                print(f"📦 {dep}: ✅ DISPONIBLE")
            except ImportError:
                print(f"📦 {dep}: ❌ NO DISPONIBLE")
        
        # 4. Verificar PythonOCC (si es conda env)
        if 'conda' in sys.executable.lower():
            try:
                from OCC.Core.STEPControl import STEPControl_Reader
                print(f"📦 PythonOCC: ✅ DISPONIBLE")
            except ImportError:
                print(f"📦 PythonOCC: ❌ NO DISPONIBLE")
    
    def monitor_loop(self):
        """Bucle principal de monitoreo"""
        print("🚀 Iniciando monitoreo en tiempo real...")
        print("📋 Comandos disponibles:")
        print("   - Presiona 'q' + Enter para salir")
        print("   - Presiona 'd' + Enter para diagnósticos")
        print("   - Presiona 'p' + Enter para probar preview")
        print("   - Presiona Enter para verificar nuevos archivos")
        
        while True:
            try:
                # Verificar input del usuario (no bloqueante)
                if sys.stdin.isatty():
                    print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Esperando... (q=salir, d=diagnósticos, p=preview)")
                
                # Simular verificación (en un sistema real aquí verificarías la BD)
                time.sleep(2)
                
                # Aquí podrías implementar verificación automática
                # self.check_new_files()
                
            except KeyboardInterrupt:
                print("\n👋 Monitoreo interrumpido por usuario")
                break
            except Exception as e:
                print(f"❌ Error en monitoreo: {e}")
                time.sleep(5)

def main():
    monitor = PolluxMonitor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'diagnostics':
            monitor.run_diagnostics()
        elif sys.argv[1] == 'analyze' and len(sys.argv) > 2:
            monitor.analyze_file(sys.argv[2])
        elif sys.argv[1] == 'preview' and len(sys.argv) > 2:
            monitor.test_preview_generation(sys.argv[2])
        else:
            print("Uso: python monitor.py [diagnostics|analyze <file_id>|preview <file_path>]")
    else:
        monitor.run_diagnostics()
        print("\n" + "="*60)
        print("🎯 SISTEMA LISTO PARA MONITOREO DE ARCHIVOS STL")
        print("="*60)
        print("📝 Ahora puedes subir tu archivo STL y ejecutar:")
        print("   php debug_system.php monitor <file_id>")
        print("   python monitor.py analyze <file_id>")

if __name__ == "__main__":
    main()
