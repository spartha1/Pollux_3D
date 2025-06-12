#!/usr/bin/env python3
import sys
import json
import time

try:
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib_Add
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
    OCC_AVAILABLE = True
except ImportError:
    OCC_AVAILABLE = False

def analyze_step(filepath):
    """Analiza un archivo STEP y devuelve dimensiones, volumen, área y topología."""
    if not OCC_AVAILABLE:
        raise ImportError(
            "PythonOCC no está instalado. Instálalo con:\n"
            "conda install -c conda-forge pythonocc-core\n"
            "o consulta: https://github.com/tpaviot/pythonocc-core"
        )

    t0 = time.time()

    # Leer STEP
    reader = STEPControl_Reader()
    status = reader.ReadFile(filepath)
    if status != IFSelect_RetDone:
        raise RuntimeError(f"Error al leer STEP ({status})")

    reader.TransferRoot()
    shape = reader.OneShape()

    # Bounding box
    bbox = Bnd_Box()
    brepbndlib_Add(shape, bbox)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    dims = {
        "width": round(xmax - xmin, 3),
        "height": round(ymax - ymin, 3),
        "depth": round(zmax - zmin, 3),
    }

    # Propiedades de volumen
    vp = GProp_GProps()
    brepgprop_VolumeProperties(shape, vp)
    volume = round(vp.Mass(), 3)

    # Propiedades de superficie
    sp = GProp_GProps()
    brepgprop_SurfaceProperties(shape, sp)
    area = round(sp.Mass(), 3)

    # Conteo de caras, aristas, vértices
    counts = {"faces": 0, "edges": 0, "vertices": 0}
    for explorer, key in [
        (TopAbs_FACE, "faces"),
        (TopAbs_EDGE, "edges"),
        (TopAbs_VERTEX, "vertices")
    ]:
        exp = TopExp_Explorer(shape, explorer)
        while exp.More():
            counts[key] += 1
            exp.Next()

    # Centro de masa
    com = vp.CentreOfMass()
    center_of_mass = {"x": round(com.X(), 3), "y": round(com.Y(), 3), "z": round(com.Z(), 3)}

    elapsed_ms = int((time.time() - t0) * 1000)

    return {
        "dimensions": dims,
        "volume": volume,
        "area": area,
        "metadata": {
            **counts,
            "center_of_mass": center_of_mass
        },
        "analysis_time_ms": elapsed_ms
    }

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Uso: analyze_step.py <ruta_al_archivo.step>"}))
        sys.exit(1)

    path = sys.argv[1]
    try:
        result = analyze_step(path)
        print(json.dumps(result))
    except ImportError as e:
        error_info = {
            "error": str(e),
            "type": "dependency_error"
        }
        print(json.dumps(error_info))
        sys.exit(1)
    except Exception as e:
        import traceback
        error_info = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_info))
        sys.exit(1)

if __name__ == "__main__":
    main()
