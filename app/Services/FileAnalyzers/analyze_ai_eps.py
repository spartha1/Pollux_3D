import sys, json, subprocess

def analyze(filepath):
    try:
        result = subprocess.run(['gs', '-dBATCH', '-dNOPAUSE', '-sDEVICE=bbox', filepath],
                                stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, timeout=15)

        bbox_lines = result.stderr.decode().splitlines()
        bbox_data = next((line for line in bbox_lines if line.startswith('%%BoundingBox:')), None)

        if bbox_data:
            _, x1, y1, x2, y2 = bbox_data.strip().split()
            dimensions = {
                "width": float(x2) - float(x1),
                "height": float(y2) - float(y1),
                "depth": 0
            }
        else:
            dimensions = None

        return {
            "dimensions": dimensions,
            "volume": None,
            "area": None,
            "layers": None,
            "metadata": {
                "bounding_box_raw": bbox_data
            },
            "analysis_time_ms": 1000
        }
    except Exception as e:
        raise Exception("Ghostscript error: " + str(e))

if __name__ == "__main__":
    path = sys.argv[1]
    print(json.dumps(analyze(path)))
