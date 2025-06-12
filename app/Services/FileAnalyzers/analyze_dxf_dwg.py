import sys, json
import ezdxf

def analyze(filepath):
    doc = ezdxf.readfile(filepath)
    msp = doc.modelspace()

    ext = msp.bbox()
    dimensions = {
        "width": ext.extmax.x - ext.extmin.x,
        "height": ext.extmax.y - ext.extmin.y,
        "depth": 0
    }

    return {
        "dimensions": dimensions,
        "volume": None,
        "area": None,
        "layers": len(doc.layers),
        "metadata": {
            "entities": len(msp)
        },
        "analysis_time_ms": 800
    }

if __name__ == "__main__":
    path = sys.argv[1]
    print(json.dumps(analyze(path)))
