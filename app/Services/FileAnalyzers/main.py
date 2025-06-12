import sys
import os
import subprocess
import json
import traceback

# Mapa de extensiones a scripts
EXTENSION_MAP = {
    '.stl': 'analyze_stl.py',
    '.step': 'analyze_step.py',
    '.stp': 'analyze_step.py',
    '.dxf': 'analyze_dxf_dwg.py',
    '.dwg': 'analyze_dxf_dwg.py',
    '.ai':  'analyze_ai_eps.py',
    '.eps': 'analyze_ai_eps.py',
}

def get_extension(path):
    return os.path.splitext(path)[1].lower()

def main(file_path):
    ext = get_extension(file_path)

    if ext not in EXTENSION_MAP:
        print(json.dumps({"error": f"Unsupported file type: {ext}"}))
        return

    script = os.path.join(os.path.dirname(__file__), EXTENSION_MAP[ext])

    try:
        result = subprocess.run(
            ['python', script, file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )

        if result.returncode != 0:
            raise Exception(result.stderr.decode())

        print(result.stdout.decode())
    except Exception as e:
        print(json.dumps({
            "error": f"Failed to analyze file: {str(e)}",
            "traceback": traceback.format_exc()
        }))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing file path"}))
    else:
        main(sys.argv[1])
