#!/usr/bin/env python3
"""
Script para probar todos los analizadores del sistema Pollux 3D
"""
import os
import sys
import json
import subprocess

def test_analyzer(name, script_path, test_args=None):
    """Probar un analizador específico"""
    print(f"\n=== PROBANDO {name} ===")
    
    if not os.path.exists(script_path):
        print(f"❌ Script no encontrado: {script_path}")
        return False
    
    try:
        if test_args:
            # Probar con argumentos específicos
            result = subprocess.run([sys.executable, script_path] + test_args, 
                                  capture_output=True, text=True, timeout=10)
        else:
            # Probar sin argumentos (debería mostrar usage)
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, timeout=10)
        
        print(f"Código de salida: {result.returncode}")
        print(f"Salida: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        
        # Para analyzadores, código 1 sin argumentos es normal (usage)
        if test_args is None and result.returncode == 1:
            return True
        elif test_args and result.returncode == 0:
            return True
        else:
            return result.returncode == 0
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout del analizador")
        return False
    except Exception as e:
        print(f"❌ Error ejecutando analizador: {e}")
        return False

def main():
    print("=== PRUEBA COMPLETA DE ANALIZADORES POLLUX 3D ===\n")
    
    # Lista de analizadores a probar
    analyzers = [
        ("STL Manufacturing", "analyze_stl_manufacturing.py"),
        ("STEP Simple", "analyze_step_simple.py"),
        ("DXF/DWG", "analyze_dxf_dwg.py"),
        ("AI/EPS", "analyze_ai_eps.py"),
    ]
    
    # Verificar archivos de ejemplo
    test_files = {
        "STL": "c1bc34d4-df6e-4caa-900e-5a0d70b41c3c.STL",  # Archivo que sabemos existe
    }
    
    results = {}
    
    # Probar cada analizador sin argumentos (verificar usage)
    for name, script in analyzers:
        results[name] = test_analyzer(name, script)
    
    # Probar con archivos reales si existen
    print("\n" + "="*50)
    print("PRUEBAS CON ARCHIVOS REALES")
    print("="*50)
    
    # Buscar archivo STL en el directorio raíz del proyecto
    stl_path = os.path.join("..", "..", "..", "c1bc34d4-df6e-4caa-900e-5a0d70b41c3c.STL")
    if os.path.exists(stl_path):
        print(f"\n✅ Archivo STL encontrado: {stl_path}")
        stl_result = test_analyzer("STL Manufacturing (con archivo)", 
                                 "analyze_stl_manufacturing.py", 
                                 [stl_path])
        results["STL con archivo"] = stl_result
    else:
        print(f"\n⚠️ Archivo STL no encontrado: {stl_path}")
    
    # Resumen final
    print("\n" + "="*50)
    print("RESUMEN DE RESULTADOS")
    print("="*50)
    
    for analyzer, success in results.items():
        status = "✅ FUNCIONA" if success else "❌ FALLA"
        print(f"{analyzer}: {status}")
    
    total_working = sum(results.values())
    total_tests = len(results)
    print(f"\nTotal: {total_working}/{total_tests} analizadores funcionando")
    
    return total_working == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
