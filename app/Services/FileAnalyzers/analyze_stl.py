import sys, json
from stl import mesh

def analyze(filepath):
    model = mesh.Mesh.from_file(filepath)
    dimensions = {
        "x": float(model.x.max() - model.x.min()),
        "y": float(model.y.max() - model.y.min()),
        "z": float(model.z.max() - model.z.min())
    }
    volume = float(model.get_mass_properties()[0])
    return {
        "dimensions": dimensions,
        "volume": volume,
        "metadata": {
            "triangles": int(len(model))
        },
        "analysis_time_ms": 1000
    }

if __name__ == "__main__":
    filepath = sys.argv[1]
    print(json.dumps(analyze(filepath)))
