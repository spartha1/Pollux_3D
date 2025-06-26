import sys
print(f"Python executable: {sys.executable}\n")

print("Testing OCC imports...")
try:
    import OCC
    print("✓ Base OCC package imported")
    print(f"OCC location: {OCC.__file__}\n")

    from OCC.Core.STEPControl import STEPControl_Reader
    print("✓ STEPControl_Reader imported")

    from OCC.Core.IFSelect import IFSelect_RetDone
    print("✓ IFSelect_RetDone imported")

    from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
    print("✓ BRepMesh_IncrementalMesh imported")

    print("\nAll critical OCC components imported successfully!")
except ImportError as e:
    print(f"✗ Import Error: {e}")
except Exception as e:
    print(f"✗ Other Error: {e}")
