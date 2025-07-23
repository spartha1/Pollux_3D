#!/usr/bin/env python3
"""
Test específico para PyVista y VTK
"""

def test_pyvista_detailed():
    print("=== TEST DETALLADO PYVISTA/VTK ===\n")
    
    try:
        print("1. Importando PyVista básico...")
        import pyvista as pv
        print("✅ PyVista importado correctamente")
        print(f"   Versión PyVista: {pv.__version__}")
        
        print("\n2. Verificando configuración...")
        print(f"   Backend de plotting: {pv.global_theme.notebook}")
        
        print("\n3. Probando creación de mesh simple...")
        # Crear un mesh simple sin VTK complejo
        mesh = pv.Sphere()
        print(f"✅ Mesh creado: {mesh.n_points} puntos, {mesh.n_cells} células")
        
        print("\n4. Probando renderizado off-screen...")
        # Configurar para renderizado sin pantalla
        pv.start_xvfb()  # Para sistemas sin display
        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(mesh)
        
        # Intentar generar imagen
        plotter.show(screenshot=True)
        print("✅ Renderizado off-screen exitoso")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Error durante pruebas: {e}")
        
        # Intentar diagnóstico más específico
        try:
            print("\n5. Diagnóstico VTK...")
            import vtk
            print(f"   VTK importado correctamente")
            print(f"   Versión VTK: {vtk.vtkVersion.GetVTKVersion()}")
            
            # Probar componentes específicos
            print("   Probando vtkSphereSource...")
            sphere = vtk.vtkSphereSource()
            sphere.Update()
            print("✅ vtkSphereSource funciona")
            
        except Exception as vtk_error:
            print(f"❌ Error específico VTK: {vtk_error}")
        
        return False

def test_alternative_3d_libraries():
    print("\n=== PRUEBA BIBLIOTECAS 3D ALTERNATIVAS ===\n")
    
    alternatives = [
        ("matplotlib 3D", "from mpl_toolkits.mplot3d import Axes3D; import matplotlib.pyplot as plt"),
        ("plotly", "import plotly.graph_objects as go"),
        ("mayavi", "from mayavi import mlab"),
    ]
    
    working_alternatives = []
    
    for name, import_statement in alternatives:
        try:
            exec(import_statement)
            print(f"✅ {name}: DISPONIBLE")
            working_alternatives.append(name)
        except ImportError as e:
            print(f"❌ {name}: NO DISPONIBLE - {e}")
        except Exception as e:
            print(f"⚠️ {name}: ERROR - {e}")
    
    return working_alternatives

if __name__ == "__main__":
    pyvista_works = test_pyvista_detailed()
    alternatives = test_alternative_3d_libraries()
    
    print(f"\n=== RESUMEN ===")
    print(f"PyVista/VTK: {'✅ FUNCIONA' if pyvista_works else '❌ PROBLEMAS'}")
    print(f"Alternativas disponibles: {', '.join(alternatives) if alternatives else 'Ninguna'}")
    
    if not pyvista_works and not alternatives:
        print("\n🚨 RECOMENDACIÓN: Instalar matplotlib para visualización 3D básica")
        print("   Comando: conda install matplotlib")
