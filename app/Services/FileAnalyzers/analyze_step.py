import sys, json
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone

def analyze(filepath):
    reader = STEPControl_Reader()
    status = reader.ReadFile(filepath)
    if status != IFSelect_RetDone:
        raise Exception("Failed to read STEP file")
    reader.TransferRoot()
    shape = reader.OneShape()

    bbox = shape.BoundingBox()
    dimensions = {
        "width": bbox.XMax() - bbox.XMin(),
        "height": bbox.YMax() - bbox.YMin(),
        "depth": bbox.ZMax() - bbox.ZMin(),
    }

    return {
        "dimensions": dimensions,
        "volume": None,
        "area": None,
        "layers": None,
        "metadata": {},
        "analysis_time_ms": 2000
    }

if __name__ == "__main__":
    path = sys.argv[1]
    print(json.dumps(analyze(path)))
