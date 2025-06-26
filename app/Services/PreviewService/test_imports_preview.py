print("Verificando importaciones para el servidor de previsualización...")

# Importar y verificar el entorno
from preview_env import verify_conda_env, verify_imports

# Verificar entorno conda
python_path = verify_conda_env()
print(f"Using correct Python: {python_path}\n")

# Verificar todas las importaciones
results = verify_imports()
print("\nResultados de la verificación:")
for name, info in results.items():
    status = "✓" if info["status"] else "✗"
    version = info.get("version", "N/A")
    path = info.get("path", "N/A")
    print(f"{status} {name}: version={version}, path={path}")

# 2. Verificar PIL
try:
    from PIL import Image, ImageDraw, ImageFont
    print("✓ PIL (Pillow): OK")
except ImportError as e:
    print(f"✗ Error en PIL: {e}")

# 3. Verificar FastAPI
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    print("✓ FastAPI y dependencias: OK")
except ImportError as e:
    print(f"✗ Error en FastAPI: {e}")

# 4. Verificar NumPy
try:
    import numpy as np
    print(f"✓ NumPy {np.__version__}: OK")
except ImportError as e:
    print(f"✗ Error en NumPy: {e}")

# 5. Verificar PythonOCC
try:
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
    from OCC.Core.TopoDS import TopoDS_Shape
    from OCC.Core.BRep import BRep_Builder
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib_Add
    print("✓ PythonOCC (OCC.Core): OK")
except ImportError as e:
    print(f"✗ Error en PythonOCC: {e}")

# 6. Verificar VTK/PyVista
try:
    import vtk
    print(f"✓ VTK {vtk.vtkVersion().GetVTKVersion()}: OK")
except ImportError as e:
    print(f"✗ Error en VTK: {e}")

try:
    import pyvista as pv
    print(f"✓ PyVista {pv.__version__}: OK")
except ImportError as e:
    print(f"✗ Error en PyVista: {e}")

print("\nVerificación de importaciones completada.")
