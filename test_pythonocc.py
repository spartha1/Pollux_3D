#!/usr/bin/env python3
"""
Script de prueba para verificar PythonOCC
"""

def test_pythonocc():
    """Test all PythonOCC components"""
    print("🧪 Testing PythonOCC Components...")
    
    try:
        # Test 1: Basic imports
        print("\n1. Testing basic imports...")
        from OCC.Core.STEPControl import STEPControl_Reader
        from OCC.Core.IFSelect import IFSelect_RetDone
        from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
        from OCC.Core.TopoDS import TopoDS_Shape
        from OCC.Core.BRep import BRep_Builder
        from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec
        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib_Add
        print("   ✅ All imports successful")
        
        # Test 2: Create a STEP reader
        print("\n2. Testing STEP reader creation...")
        step_reader = STEPControl_Reader()
        print("   ✅ STEP reader created successfully")
        
        # Test 3: Test geometry creation
        print("\n3. Testing geometry creation...")
        point = gp_Pnt(0, 0, 0)
        direction = gp_Dir(1, 0, 0)
        vector = gp_Vec(1, 1, 1)
        print(f"   ✅ Created point: ({point.X()}, {point.Y()}, {point.Z()})")
        print(f"   ✅ Created direction: ({direction.X()}, {direction.Y()}, {direction.Z()})")
        print(f"   ✅ Created vector: ({vector.X()}, {vector.Y()}, {vector.Z()})")
        
        # Test 4: Test bounding box
        print("\n4. Testing bounding box...")
        bbox = Bnd_Box()
        print("   ✅ Bounding box created successfully")
        
        print("\n🎉 All PythonOCC tests passed!")
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    import sys
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    success = test_pythonocc()
    
    if success:
        print("\n✅ PythonOCC is ready for STEP/STP file analysis!")
        sys.exit(0)
    else:
        print("\n❌ PythonOCC is not working correctly")
        sys.exit(1)
