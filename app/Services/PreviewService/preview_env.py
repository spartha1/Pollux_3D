"""
Environment configuration for preview service
"""
import sys
import os
from pathlib import Path

def verify_conda_env():
    """Verify that we're running in the correct conda environment"""
    expected_env = "pollux-preview-env"
    python_path = Path(sys.executable)

    # Verificar si estamos en el entorno correcto
    conda_prefix = os.environ.get("CONDA_PREFIX", "")
    current_env = os.environ.get("CONDA_DEFAULT_ENV", "")

    if current_env != expected_env or expected_env not in conda_prefix:
        print(f"Error: This script must be run using Python from the '{expected_env}' conda environment")
        print(f"Current Python: {sys.executable}")
        print(f"Current environment: {current_env}")
        print(f"Conda prefix: {conda_prefix}")
        print(f"Please use the appropriate batch script to run this script")
        sys.exit(1)

    return python_path

def verify_imports():
    """Verify all required imports are available"""
    results = {
        "python": {"status": True, "path": sys.executable, "version": sys.version},
        "occ": {"status": False, "path": None, "version": None},
        "pyvista": {"status": False, "version": None},
        "vtk": {"status": False, "version": None},
        "numpy": {"status": False, "version": None},
        "pillow": {"status": False, "version": None},
        "fastapi": {"status": False, "version": None}
    }

    # Verify OCC
    try:
        import OCC
        results["occ"].update({
            "status": True,
            "path": OCC.__file__,
            "version": getattr(OCC, "__version__", "unknown")
        })
    except ImportError as e:
        print(f"Error importing OCC: {e}")

    # Verify PyVista
    try:
        import pyvista as pv
        results["pyvista"].update({
            "status": True,
            "version": pv.__version__
        })
    except ImportError as e:
        print(f"Error importing PyVista: {e}")

    # Verify VTK
    try:
        import vtk
        results["vtk"].update({
            "status": True,
            "version": vtk.vtkVersion().GetVTKVersion()
        })
    except ImportError as e:
        print(f"Error importing VTK: {e}")

    # Verify NumPy
    try:
        import numpy as np
        results["numpy"].update({
            "status": True,
            "version": np.__version__
        })
    except ImportError as e:
        print(f"Error importing NumPy: {e}")

    # Verify Pillow
    try:
        from PIL import Image
        import PIL
        results["pillow"].update({
            "status": True,
            "version": PIL.__version__
        })
    except ImportError as e:
        print(f"Error importing Pillow: {e}")

    # Verify FastAPI
    try:
        import fastapi
        results["fastapi"].update({
            "status": True,
            "version": fastapi.__version__
        })
    except ImportError as e:
        print(f"Error importing FastAPI: {e}")

    return results

if __name__ == "__main__":
    python_path = verify_conda_env()
    print(f"Using Python from: {python_path}")

    print("\nVerifying imports:")
    results = verify_imports()
    for name, info in results.items():
        status = "✓" if info["status"] else "✗"
        version = info.get("version", "N/A")
        path = info.get("path", "N/A")
        print(f"{status} {name}: version={version}, path={path}")
