#!/usr/bin/env python3
import sys
import json
import subprocess
import os
import time
# Importar configuración portable
from portable_config import get_config

def debug(msg):
    """Print debug messages to stderr"""
    print(msg, file=sys.stderr, flush=True)

def analyze_ai_eps(filepath):
    """Analyze AI/EPS files using Ghostscript"""
    debug(f"Analyzing file: {filepath}")
    start_time = time.time()
    config = get_config()

    try:
        # Verificar que el archivo existe
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        # Verificar que Ghostscript está instalado usando configuración portable
        gs_path = config.ghostscript_path
        if not gs_path:
            raise RuntimeError("Ghostscript not found. Please install Ghostscript and make sure it's in your PATH")
            
        try:
            version = subprocess.run([gs_path, '--version'],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
            debug(f"Ghostscript version: {version.stdout.strip()}")
        except subprocess.SubprocessError:
            raise RuntimeError(f"Failed to run Ghostscript at: {gs_path}")

        # Ejecutar Ghostscript
        debug("Running Ghostscript analysis...")
        result = subprocess.run(
            [gs_path, '-dBATCH', '-dNOPAUSE', '-sDEVICE=bbox', filepath],
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            timeout=15,
            text=True  # Para manejar la salida como texto en lugar de bytes
        )

        bbox_lines = result.stderr.splitlines()
        debug(f"Ghostscript output lines: {len(bbox_lines)}")
        bbox_data = next((line for line in bbox_lines if line.startswith('%%BoundingBox:')), None)

        if bbox_data:
            debug(f"Found BoundingBox: {bbox_data}")
            parts = bbox_data.strip().split()
            if len(parts) == 5:  # %%BoundingBox: x1 y1 x2 y2
                _, x1, y1, x2, y2 = parts
                dimensions = {
                    "width": float(x2) - float(x1),
                    "height": float(y2) - float(y1),
                    "depth": 0
                }
            else:
                raise ValueError(f"Invalid BoundingBox format: {bbox_data}")
        else:
            raise ValueError("No BoundingBox information found in the file")

        # Información adicional del archivo
        file_size = os.path.getsize(filepath)
        file_type = os.path.splitext(filepath)[1].lower()

        metadata = {
            "bounding_box_raw": bbox_data,
            "file_size_kb": round(file_size / 1024, 2),
            "file_type": file_type[1:].upper(),  # Remove dot and convert to uppercase
            "gs_output_lines": len(bbox_lines)
        }

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "dimensions": dimensions,
            "volume": None,  # No aplicable para archivos 2D
            "area": dimensions["width"] * dimensions["height"] if dimensions else None,
            "layers": None,  # Requeriría análisis más profundo
            "metadata": metadata,
            "analysis_time_ms": elapsed_ms
        }

    except FileNotFoundError as e:
        debug(f"File error: {str(e)}")
        raise
    except subprocess.TimeoutExpired:
        debug("Ghostscript analysis timeout")
        raise RuntimeError("Ghostscript analysis timed out")
    except subprocess.SubprocessError as e:
        debug(f"Ghostscript process error: {str(e)}")
        raise RuntimeError(f"Ghostscript process error: {str(e)}")
    except Exception as e:
        debug(f"Unexpected error: {str(e)}")
        raise

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: analyze_ai_eps.py <filepath>"}))
        sys.exit(1)

    try:
        result = analyze_ai_eps(sys.argv[1])
        print(json.dumps(result))
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
