import sys, json, time
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX

def analyze(filepath):
    start_time = time.time()

    reader = STEPControl_Reader()
    status = reader.ReadFile(filepath)

    if status != IFSelect_RetDone:
        raise Exception("Failed to read STEP file")

    reader.TransferRoot()
    shape = reader.OneShape()

    # Calcular el bounding box
    bbox = Bnd_Box()
    brepbndlib_Add(shape, bbox)

    x_min, y_min, z_min, x_max, y_max, z_max = bbox.Get()

    dimensions = {
        "x": round(x_max - x_min, 3),
        "y": round(y_max - y_min, 3),
        "z": round(z_max - z_min, 3),
    }

    # Calcular volumen
    volume_props = GProp_GProps()
    brepgprop_VolumeProperties(shape, volume_props)
    volume = round(volume_props.Mass(), 3)

    # Calcular área superficial
    surface_props = GProp_GProps()
    brepgprop_SurfaceProperties(shape, surface_props)
    area = round(surface_props.Mass(), 3)

    # Contar elementos
    face_count = 0
    edge_count = 0
    vertex_count = 0

    face_explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while face_explorer.More():
        face_count += 1
        face_explorer.Next()

    edge_explorer = TopExp_Explorer(shape, TopAbs_EDGE)
    while edge_explorer.More():
        edge_count += 1
        edge_explorer.Next()

    vertex_explorer = TopExp_Explorer(shape, TopAbs_VERTEX)
    while vertex_explorer.More():
        vertex_count += 1
        vertex_explorer.Next()

    # Metadata
    metadata = {
        "faces": face_count,
        "edges": edge_count,
        "vertices": vertex_count,
        "center_of_mass": {
            "x": round(volume_props.CentreOfMass().X(), 3),
            "y": round(volume_props.CentreOfMass().Y(), 3),
            "z": round(volume_props.CentreOfMass().Z(), 3)
        }
    }

    elapsed_time = round((time.time() - start_time) * 1000)

    return {
        "dimensions": dimensions,
        "volume": volume,
        "area": area,
        "layers": None,
        "metadata": metadata,
        "analysis_time_ms": elapsed_time
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No file path provided"}))
        sys.exit(1)

    try:
        path = sys.argv[1]
        result = analyze(path)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
