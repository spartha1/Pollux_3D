import sys
from preview_env import verify_conda_env, verify_imports

# Verificar entorno conda
python_path = verify_conda_env()
print(f"Using correct Python: {python_path}\n")

# Verificar todas las importaciones básicas
results = verify_imports()
print("\nOCC Base Status:")
occ_info = results["occ"]
if occ_info["status"]:
    print("✓ Base OCC package imported")
    print(f"OCC location: {occ_info['path']}")
    print(f"OCC version: {occ_info['version']}\n")
else:
    print("✗ OCC import failed\n")
    sys.exit(1)

# Verificar componentes específicos de OCC
print("Checking OCC Components:")
try:
    from OCC.Core.STEPControl import STEPControl_Reader
    print("✓ STEPControl_Reader imported")

    from OCC.Core.IFSelect import IFSelect_RetDone
    print("✓ IFSelect_RetDone imported")

    from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
    print("✓ BRepMesh_IncrementalMesh imported")

    print("\nAll critical OCC components imported successfully!")
except ImportError as e:
    print(f"✗ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Other Error: {e}")
    sys.exit(1)
