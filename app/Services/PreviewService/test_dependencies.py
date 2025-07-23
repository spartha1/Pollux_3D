#!/usr/bin/env python3
"""
Script para verificar dependencias del sistema Pollux 3D
"""

def test_dependency(name, import_statement):
    try:
        exec(import_statement)
        print(f"✅ {name}: DISPONIBLE")
        return True
    except ImportError as e:
        print(f"❌ {name}: NO DISPONIBLE - {e}")
        return False
    except Exception as e:
        print(f"⚠️ {name}: ERROR - {e}")
        return False

print("=== AUDITORÍA DE DEPENDENCIAS POLLUX 3D ===\n")

# Dependencias básicas
print("1. DEPENDENCIAS BÁSICAS:")
test_dependency("Python PIL", "from PIL import Image")
test_dependency("NumPy", "import numpy")
test_dependency("FastAPI", "from fastapi import FastAPI")
test_dependency("Uvicorn", "import uvicorn")

print("\n2. DEPENDENCIAS 3D:")
test_dependency("PythonOCC", "from OCC.Core.STEPControl import STEPControl_Reader")
test_dependency("numpy-stl", "from stl import mesh")

print("\n3. DEPENDENCIAS OPCIONALES:")
test_dependency("PyVista", "import pyvista")
test_dependency("ezdxf", "import ezdxf")

print("\n4. DEPENDENCIAS EXTERNAS:")
# Verificar Ghostscript para archivos AI/EPS
try:
    import subprocess
    gs_path = r"C:\Program Files\gs\gs10.05.1\bin\gswin64c.exe"
    result = subprocess.run([gs_path, '--version'], capture_output=True, text=True, timeout=5)
    print(f"✅ Ghostscript: DISPONIBLE - {result.stdout.strip()}")
except FileNotFoundError:
    print("❌ Ghostscript: NO ENCONTRADO - Instalar desde https://www.ghostscript.com/download/gsdnld.html")
except Exception as e:
    print(f"⚠️ Ghostscript: ERROR - {e}")

print("\n5. VERIFICACIÓN DE VERSIONES:")
try:
    import numpy as np
    print(f"NumPy: {np.__version__}")
except:
    print("NumPy: No disponible")

try:
    from PIL import Image
    print(f"PIL: {Image.__version__}")
except:
    print("PIL: No disponible")

try:
    from OCC.Core import STEPControl
    print("PythonOCC: Disponible")
except:
    print("PythonOCC: No disponible")

print("\n=== FIN DE AUDITORÍA ===")
