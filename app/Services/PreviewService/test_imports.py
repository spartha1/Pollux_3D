print("Verificando entorno y dependencias...\n")

# 1. Verificar Python y entorno
import sys
print(f"Python path: {sys.executable}\n")

# 2. Verificar PythonOCC
try:
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Display.SimpleGui import init_display
    from OCC.Core.V3d import V3d_SpotLight
    print("✓ PythonOCC (OCC.Core): OK")
except ImportError as e:
    print(f"✗ Error en PythonOCC: {e}")

# 3. Verificar PyVista
try:
    import pyvista as pv
    print(f"✓ PyVista {pv.__version__}: OK")
except ImportError as e:
    print(f"✗ Error en PyVista: {e}")

# 4. Verificar numpy-stl
try:
    from stl import mesh
    print("✓ numpy-stl: OK")
except ImportError as e:
    print(f"✗ Error en numpy-stl: {e}")

# 5. Verificar otras dependencias
try:
    import vtk
    print("✓ VTK: OK")
except ImportError as e:
    print(f"✗ Error en VTK: {e}")

try:
    from PIL import Image
    print("✓ Pillow: OK")
except ImportError as e:
    print(f"✗ Error en Pillow: {e}")

try:
    from fastapi import FastAPI
    print("✓ FastAPI: OK")
except ImportError as e:
    print(f"✗ Error en FastAPI: {e}")
