#!/usr/bin/env python3
"""
Verificación de componentes instalados para análisis completo de metadatos
"""

import sys
import os
import importlib
import json
from pathlib import Path

def check_component(module_name, description, required=True):
    """
    Verificar si un componente está instalado
    """
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'Unknown')
        status = "✅ INSTALADO"
        return {
            'name': module_name,
            'description': description,
            'status': 'installed',
            'version': version,
            'required': required,
            'symbol': '✅'
        }
    except ImportError:
        status = "❌ NO INSTALADO" if required else "⚠️  OPCIONAL"
        return {
            'name': module_name,
            'description': description,
            'status': 'missing' if required else 'optional',
            'version': None,
            'required': required,
            'symbol': '❌' if required else '⚠️'
        }

def check_python_version():
    """
    Verificar versión de Python
    """
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Versión de Python compatible")
        return True
    else:
        print("❌ Versión de Python no compatible (requiere Python 3.8+)")
        return False

def analyze_components_for_stl():
    """
    Analizar componentes para análisis STL
    """
    print("\n📊 ANÁLISIS DE COMPONENTES PARA STL")
    print("=" * 50)
    
    # Componentes básicos para STL
    components = [
        ('numpy', 'Cálculos numéricos para geometría y matrices', True),
        ('struct', 'Lectura de archivos binarios STL', True),
        ('json', 'Serialización de resultados', True),
        ('pathlib', 'Manipulación de rutas de archivos', True),
        ('time', 'Medición de tiempos de análisis', True),
        ('traceback', 'Manejo de errores detallado', True),
        ('codecs', 'Manejo de encodings para STL ASCII', True),
        ('scipy', 'Cálculos avanzados de geometría', False),
        ('matplotlib', 'Visualización de geometría', False),
        ('trimesh', 'Análisis avanzado de mallas', False),
        ('open3d', 'Procesamiento de nubes de puntos', False),
        ('vtk', 'Visualización 3D avanzada', False),
        ('pyvista', 'Interfaz simplificada para VTK', False),
    ]
    
    results = []
    for name, desc, required in components:
        result = check_component(name, desc, required)
        results.append(result)
        print(f"{result['symbol']} {result['name']:<12} - {result['description']}")
        if result['version'] and result['version'] != 'Unknown':
            print(f"{'':16} Versión: {result['version']}")
    
    return results

def analyze_components_for_step():
    """
    Analizar componentes para análisis STEP
    """
    print("\n⚙️  ANÁLISIS DE COMPONENTES PARA STEP")
    print("=" * 50)
    
    components = [
        ('pythonocc-core', 'Análisis completo STEP/BREP', False),
        ('OCC', 'OpenCASCADE bindings', False),
        ('FreeCAD', 'Análisis CAD alternativo', False),
        ('ezdxf', 'Análisis de archivos DXF', False),
        ('re', 'Análisis de texto STEP', True),
        ('os', 'Operaciones del sistema', True),
    ]
    
    results = []
    for name, desc, required in components:
        result = check_component(name, desc, required)
        results.append(result)
        print(f"{result['symbol']} {result['name']:<15} - {result['description']}")
        if result['version'] and result['version'] != 'Unknown':
            print(f"{'':19} Versión: {result['version']}")
    
    return results

def analyze_components_for_other_formats():
    """
    Analizar componentes para otros formatos
    """
    print("\n🎨 ANÁLISIS DE COMPONENTES PARA OTROS FORMATOS")
    print("=" * 50)
    
    components = [
        ('ezdxf', 'Análisis de archivos DXF/DWG', False),
        ('subprocess', 'Ejecución de Ghostscript para AI/EPS', True),
        ('Pillow', 'Procesamiento de imágenes', False),
        ('reportlab', 'Análisis de PDF', False),
        ('cairosvg', 'Procesamiento de SVG', False),
    ]
    
    results = []
    for name, desc, required in components:
        result = check_component(name, desc, required)
        results.append(result)
        print(f"{result['symbol']} {result['name']:<12} - {result['description']}")
        if result['version'] and result['version'] != 'Unknown':
            print(f"{'':16} Versión: {result['version']}")
    
    return results

def evaluate_completeness(all_results):
    """
    Evaluar qué tan completo está el sistema
    """
    print("\n🎯 EVALUACIÓN DE COMPLETITUD")
    print("=" * 50)
    
    required_installed = sum(1 for r in all_results if r['required'] and r['status'] == 'installed')
    required_total = sum(1 for r in all_results if r['required'])
    
    optional_installed = sum(1 for r in all_results if not r['required'] and r['status'] == 'installed')
    optional_total = sum(1 for r in all_results if not r['required'])
    
    print(f"📋 Componentes requeridos: {required_installed}/{required_total}")
    print(f"📋 Componentes opcionales: {optional_installed}/{optional_total}")
    
    # Capacidades específicas
    print(f"\n🔧 CAPACIDADES DISPONIBLES:")
    
    # STL
    stl_basic = any(r['name'] == 'numpy' and r['status'] == 'installed' for r in all_results)
    print(f"{'✅' if stl_basic else '❌'} Análisis STL básico (dimensiones, área, volumen)")
    
    # STEP
    step_advanced = any(r['name'] == 'pythonocc-core' and r['status'] == 'installed' for r in all_results)
    step_basic = any(r['name'] == 're' and r['status'] == 'installed' for r in all_results)
    print(f"{'✅' if step_advanced else '⚠️'} Análisis STEP {'avanzado' if step_advanced else 'básico'}")
    
    # DXF/DWG
    dxf_support = any(r['name'] == 'ezdxf' and r['status'] == 'installed' for r in all_results)
    print(f"{'✅' if dxf_support else '❌'} Análisis DXF/DWG")
    
    # AI/EPS
    ai_support = any(r['name'] == 'subprocess' and r['status'] == 'installed' for r in all_results)
    print(f"{'✅' if ai_support else '❌'} Análisis AI/EPS (requiere Ghostscript)")
    
    # Visualización
    viz_support = any(r['name'] in ['vtk', 'pyvista'] and r['status'] == 'installed' for r in all_results)
    print(f"{'✅' if viz_support else '❌'} Generación de previsualizaciones")
    
    # Calcular puntuación general
    basic_score = (required_installed / required_total) * 100 if required_total > 0 else 0
    advanced_score = (optional_installed / optional_total) * 100 if optional_total > 0 else 0
    
    print(f"\n📊 PUNTUACIÓN:")
    print(f"   - Funcionalidad básica: {basic_score:.1f}%")
    print(f"   - Funcionalidad avanzada: {advanced_score:.1f}%")
    
    return {
        'basic_score': basic_score,
        'advanced_score': advanced_score,
        'required_installed': required_installed,
        'required_total': required_total,
        'optional_installed': optional_installed,
        'optional_total': optional_total,
        'capabilities': {
            'stl_basic': stl_basic,
            'step_advanced': step_advanced,
            'step_basic': step_basic,
            'dxf_support': dxf_support,
            'ai_support': ai_support,
            'viz_support': viz_support
        }
    }

def generate_recommendations(evaluation):
    """
    Generar recomendaciones basadas en la evaluación
    """
    print(f"\n💡 RECOMENDACIONES")
    print("=" * 50)
    
    capabilities = evaluation['capabilities']
    
    if evaluation['basic_score'] < 100:
        print("🔴 CRÍTICO: Instalar componentes básicos faltantes")
        print("   - Ejecutar: pip install numpy")
    
    if not capabilities['step_advanced']:
        print("🟡 MEJORAR: Para análisis STEP completo:")
        print("   - Ejecutar: conda install -c conda-forge pythonocc-core")
    
    if not capabilities['dxf_support']:
        print("🟡 MEJORAR: Para análisis DXF/DWG:")
        print("   - Ejecutar: pip install ezdxf")
    
    if not capabilities['viz_support']:
        print("🟡 MEJORAR: Para previsualización:")
        print("   - Ejecutar: conda install -c conda-forge vtk pyvista")
    
    if evaluation['basic_score'] >= 100:
        print("✅ EXCELENTE: Todos los componentes básicos están instalados")
        print("   El sistema puede analizar archivos STL completamente")
    
    if evaluation['advanced_score'] >= 50:
        print("✅ BUENO: Muchos componentes opcionales están disponibles")
    
    print(f"\n🎯 RESUMEN:")
    if evaluation['basic_score'] >= 100:
        print("✅ El sistema está listo para análisis de metadatos STL")
    else:
        print("❌ El sistema necesita componentes básicos para funcionar")
    
    return evaluation

def main():
    """
    Función principal
    """
    print("🔍 VERIFICACIÓN DE COMPONENTES PARA ANÁLISIS DE METADATOS")
    print("=" * 60)
    
    # Verificar Python
    if not check_python_version():
        return
    
    # Analizar componentes
    all_results = []
    all_results.extend(analyze_components_for_stl())
    all_results.extend(analyze_components_for_step())
    all_results.extend(analyze_components_for_other_formats())
    
    # Evaluar completitud
    evaluation = evaluate_completeness(all_results)
    
    # Generar recomendaciones
    generate_recommendations(evaluation)
    
    # Guardar reporte
    report = {
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'components': all_results,
        'evaluation': evaluation
    }
    
    with open('components_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Reporte guardado en: components_report.json")

if __name__ == "__main__":
    main()
