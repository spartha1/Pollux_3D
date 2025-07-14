#!/usr/bin/env python3
"""
Script para probar el análisis de archivos STL y verificar que todos los metadatos se generen correctamente.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

def run_test_analysis(file_path, analyzer_script):
    """
    Ejecutar análisis y mostrar resultados.
    
    Args:
        file_path: Ruta al archivo STL
        analyzer_script: Script analizador a usar
    """
    print(f"\n{'='*60}")
    print(f"Probando: {os.path.basename(file_path)}")
    print(f"Analizador: {analyzer_script}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"❌ Error: Archivo no encontrado: {file_path}")
        return False
    
    script_path = os.path.join(os.path.dirname(__file__), analyzer_script)
    if not os.path.exists(script_path):
        print(f"❌ Error: Script analizador no encontrado: {script_path}")
        return False
    
    try:
        # Ejecutar análisis
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, script_path, file_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"Tiempo de ejecución: {elapsed_time:.2f} segundos")
        print(f"Código de salida: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ Análisis completado exitosamente")
            
            # Parsear y mostrar resultados
            try:
                data = json.loads(result.stdout)
                print("\n📊 RESULTADOS DEL ANÁLISIS:")
                print("-" * 40)
                
                # Dimensiones
                if 'dimensions' in data:
                    dims = data['dimensions']
                    print(f"📏 Dimensiones:")
                    print(f"   - Ancho: {dims.get('width', 'N/A')}")
                    print(f"   - Alto: {dims.get('height', 'N/A')}")
                    print(f"   - Profundidad: {dims.get('depth', 'N/A')}")
                
                # Volumen y área
                if 'volume' in data:
                    print(f"📦 Volumen: {data['volume']}")
                if 'area' in data:
                    print(f"📐 Área: {data['area']}")
                
                # Metadatos
                if 'metadata' in data:
                    meta = data['metadata']
                    print(f"\n🔍 Metadatos:")
                    print(f"   - Triángulos: {meta.get('triangles', 'N/A')}")
                    print(f"   - Vértices: {meta.get('vertices', 'N/A')}")
                    print(f"   - Caras: {meta.get('faces', 'N/A')}")
                    print(f"   - Aristas: {meta.get('edges', 'N/A')}")
                    print(f"   - Formato: {meta.get('format', 'N/A')}")
                    
                    if 'center_of_mass' in meta:
                        com = meta['center_of_mass']
                        print(f"   - Centro de masa: ({com.get('x', 0):.2f}, {com.get('y', 0):.2f}, {com.get('z', 0):.2f})")
                    
                    if 'file_size_bytes' in meta:
                        size_kb = meta['file_size_bytes'] / 1024
                        print(f"   - Tamaño de archivo: {size_kb:.2f} KB")
                
                # Tiempo de análisis
                if 'analysis_time_ms' in data:
                    print(f"\n⏱️  Tiempo de análisis: {data['analysis_time_ms']} ms")
                
                print("\n" + "="*60)
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ Error al parsear JSON: {e}")
                print(f"Salida raw: {result.stdout}")
                return False
                
        else:
            print(f"❌ Error en análisis (código {result.returncode})")
            if result.stderr:
                print(f"Error stderr: {result.stderr}")
            if result.stdout:
                print(f"Salida stdout: {result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout: El análisis tardó más de 60 segundos")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_main_analyzer(file_path):
    """
    Probar el analizador principal main.py
    """
    print(f"\n{'='*60}")
    print(f"Probando main.py con: {os.path.basename(file_path)}")
    print(f"{'='*60}")
    
    main_script = os.path.join(os.path.dirname(__file__), "main.py")
    if not os.path.exists(main_script):
        print(f"❌ Error: main.py no encontrado: {main_script}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, main_script, file_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(f"Código de salida: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ main.py completado exitosamente")
            try:
                data = json.loads(result.stdout)
                print("📊 Resultado JSON válido")
                print(f"Claves encontradas: {list(data.keys())}")
                return True
            except json.JSONDecodeError:
                print("❌ JSON inválido desde main.py")
                print(f"Salida: {result.stdout}")
                return False
        else:
            print(f"❌ Error en main.py")
            print(f"stderr: {result.stderr}")
            print(f"stdout: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando main.py: {e}")
        return False

def main():
    """
    Función principal para probar el análisis STL.
    """
    print("🔧 PRUEBAS DE ANÁLISIS STL")
    print("=" * 60)
    
    # Generar archivos de prueba primero
    print("📝 Generando archivos de prueba...")
    try:
        from generate_test_stl import create_cube_stl, create_pyramid_stl
        
        test_dir = "test_stl_files"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
        
        # Crear archivos de prueba
        cube_file = os.path.join(test_dir, "test_cube.stl")
        pyramid_file = os.path.join(test_dir, "test_pyramid.stl")
        
        create_cube_stl(10.0, cube_file)
        create_pyramid_stl(10.0, 8.0, pyramid_file)
        
        print(f"✅ Archivos de prueba creados en: {test_dir}")
        
    except Exception as e:
        print(f"❌ Error generando archivos de prueba: {e}")
        print("Continuando con archivos existentes...")
        
        # Buscar archivos STL existentes
        cube_file = None
        pyramid_file = None
        
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith('.stl'):
                    if 'cube' in file.lower():
                        cube_file = os.path.join(root, file)
                    elif 'pyramid' in file.lower():
                        pyramid_file = os.path.join(root, file)
    
    # Lista de archivos para probar
    test_files = []
    if cube_file and os.path.exists(cube_file):
        test_files.append(cube_file)
    if pyramid_file and os.path.exists(pyramid_file):
        test_files.append(pyramid_file)
    
    if not test_files:
        print("❌ No se encontraron archivos STL para probar")
        return
    
    # Probar con diferentes analizadores
    analyzers = [
        "analyze_stl_simple.py",
        "analyze_stl.py"
    ]
    
    results = []
    
    for file_path in test_files:
        for analyzer in analyzers:
            success = run_test_analysis(file_path, analyzer)
            results.append({
                'file': os.path.basename(file_path),
                'analyzer': analyzer,
                'success': success
            })
    
    # Probar main.py
    for file_path in test_files:
        success = test_main_analyzer(file_path)
        results.append({
            'file': os.path.basename(file_path),
            'analyzer': 'main.py',
            'success': success
        })
    
    # Resumen de resultados
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"Pruebas exitosas: {success_count}/{total_count}")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['file']} + {result['analyzer']}")
    
    if success_count == total_count:
        print("\n🎉 ¡Todas las pruebas pasaron!")
    else:
        print(f"\n⚠️  {total_count - success_count} pruebas fallaron")
    
    # Verificar componentes instalados
    print("\n" + "="*60)
    print("🔍 VERIFICACIÓN DE COMPONENTES")
    print("="*60)
    
    required_modules = ['numpy', 'json', 'struct', 'traceback']
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} - Instalado")
        except ImportError:
            print(f"❌ {module} - No instalado")
    
    print("\n🏁 Pruebas completadas")

if __name__ == "__main__":
    main()
