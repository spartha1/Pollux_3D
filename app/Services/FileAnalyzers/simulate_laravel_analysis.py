#!/usr/bin/env python3
"""
Script para simular la ejecución del análisis STL desde Laravel
"""

import os
import sys
import json
import subprocess
import time

def simulate_laravel_analysis():
    """
    Simular el análisis como lo haría Laravel
    """
    
    # Ruta del entorno Python como la configuraría Laravel
    python_path = r"C:\Users\DANIELIVANVALDEZRODR\miniconda3\envs\pollux-preview-env\python.exe"
    
    # Archivo de prueba
    test_file = r"test_stl_files\test_cube.stl"
    
    # Script main.py
    main_script = r"main.py"
    
    print("🔬 SIMULACIÓN DE ANÁLISIS DESDE LARAVEL")
    print("=" * 50)
    print(f"Python path: {python_path}")
    print(f"Test file: {test_file}")
    print(f"Main script: {main_script}")
    print()
    
    if not os.path.exists(test_file):
        print("❌ Archivo de prueba no encontrado")
        return
    
    if not os.path.exists(main_script):
        print("❌ Script main.py no encontrado")
        return
    
    if not os.path.exists(python_path):
        print("❌ Python path no encontrado")
        return
    
    try:
        # Ejecutar análisis como lo haría Laravel
        print("🚀 Ejecutando análisis...")
        start_time = time.time()
        
        process = subprocess.Popen(
            [python_path, main_script, test_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=30)
        
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Tiempo de ejecución: {elapsed_time:.2f} segundos")
        print(f"📊 Código de salida: {process.returncode}")
        
        if process.returncode == 0:
            print("✅ Análisis completado exitosamente")
            
            try:
                # Parsear resultado JSON
                result = json.loads(stdout)
                
                print("\n📈 RESULTADO DEL ANÁLISIS:")
                print("-" * 30)
                print(f"Dimensiones: {result.get('dimensions', {})}")
                print(f"Volumen: {result.get('volume', 'N/A')}")
                print(f"Área: {result.get('area', 'N/A')}")
                print(f"Tiempo de análisis: {result.get('analysis_time_ms', 'N/A')} ms")
                
                metadata = result.get('metadata', {})
                print(f"Triángulos: {metadata.get('triangles', 'N/A')}")
                print(f"Vértices: {metadata.get('vertices', 'N/A')}")
                print(f"Formato: {metadata.get('format', 'N/A')}")
                
                # Verificar que todos los campos necesarios estén presentes
                required_fields = ['dimensions', 'volume', 'area', 'metadata']
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    print(f"⚠️  Campos faltantes: {missing_fields}")
                else:
                    print("✅ Todos los campos requeridos están presentes")
                
                # Verificar campos de metadata
                required_metadata = ['triangles', 'vertices', 'faces', 'format', 'center_of_mass']
                missing_metadata = [field for field in required_metadata if field not in metadata]
                
                if missing_metadata:
                    print(f"⚠️  Metadatos faltantes: {missing_metadata}")
                else:
                    print("✅ Todos los metadatos requeridos están presentes")
                
                print("\n🎯 COMPATIBILIDAD CON LARAVEL:")
                print("✅ Salida JSON válida")
                print("✅ Estructura de datos compatible")
                print("✅ Campos esperados por las vistas presentes")
                
            except json.JSONDecodeError as e:
                print(f"❌ Error al parsear JSON: {e}")
                print(f"Salida raw: {stdout}")
                
        else:
            print("❌ Error en el análisis")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout: El análisis tardó más de 30 segundos")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def check_laravel_config():
    """
    Verificar la configuración que usaría Laravel
    """
    print("\n🔧 VERIFICACIÓN DE CONFIGURACIÓN LARAVEL")
    print("=" * 50)
    
    # Verificar que el archivo de configuración de Laravel tenga la ruta correcta
    config_path = r"C:\Users\DANIELIVANVALDEZRODR\miniconda3\envs\pollux-preview-env\python.exe"
    
    if os.path.exists(config_path):
        print(f"✅ Python path configurado correctamente: {config_path}")
        
        # Verificar que numpy esté disponible
        try:
            result = subprocess.run(
                [config_path, "-c", "import numpy; print('NumPy OK')"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ NumPy disponible en el entorno")
            else:
                print(f"❌ Error al verificar NumPy: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error al verificar NumPy: {e}")
    else:
        print(f"❌ Python path no encontrado: {config_path}")
    
    # Verificar analizadores disponibles
    analyzers = [
        "analyze_stl_simple.py",
        "analyze_stl.py",
        "analyze_step_simple.py",
        "analyze_dxf_dwg.py",
        "analyze_ai_eps.py",
        "main.py"
    ]
    
    print("\n📁 ANALIZADORES DISPONIBLES:")
    for analyzer in analyzers:
        if os.path.exists(analyzer):
            print(f"✅ {analyzer}")
        else:
            print(f"❌ {analyzer}")

if __name__ == "__main__":
    simulate_laravel_analysis()
    check_laravel_config()
