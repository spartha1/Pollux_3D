#!/usr/bin/env python3
import sys
import json
import time
import os
import ezdxf
from ezdxf.tools.standards import linetypes

def debug(msg):
    """Print debug messages to stderr"""
    print(msg, file=sys.stderr, flush=True)

def analyze_dxf(filepath):
    """Analyze DXF/DWG files using ezdxf"""
    debug(f"Analyzing file: {filepath}")
    start_time = time.time()

    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        debug("Loading DXF file...")
        doc = ezdxf.readfile(filepath)
        debug("DXF file loaded successfully")

        msp = doc.modelspace()
        debug("Accessing modelspace...")

        # Get bounding box
        ext = msp.bbox()
        if ext and ext.has_data:
            dimensions = {
                "width": ext.size.x,
                "height": ext.size.y,
                "depth": ext.size.z if hasattr(ext.size, 'z') else 0
            }
            debug(f"Calculated dimensions: {dimensions}")
        else:
            dimensions = {"width": 0, "height": 0, "depth": 0}
            debug("No bounding box data available")

        # Count entities by type
        entity_counts = {}
        total_entities = 0
        for entity in msp:
            dxftype = entity.dxftype()
            entity_counts[dxftype] = entity_counts.get(dxftype, 0) + 1
            total_entities += 1

        debug(f"Found {total_entities} total entities")

        # Get file info
        file_size = os.path.getsize(filepath)

        # Collect metadata
        metadata = {
            "dxf_version": doc.dxfversion,
            "encoding": doc.encoding,
            "layers": len(doc.layers),
            "linetypes": len(doc.linetypes),
            "blocks": len(doc.blocks),
            "entities": total_entities,
            "entity_types": entity_counts,
            "file_size_kb": round(file_size / 1024, 2)
        }

        # Calculate analysis time
        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "dimensions": dimensions,
            "volume": None,  # Not applicable for DXF
            "area": None,    # Would require additional calculation
            "metadata": metadata,
            "analysis_time_ms": elapsed_ms
        }

    except ezdxf.DXFError as e:
        debug(f"DXF parsing error: {str(e)}")
        raise
    except Exception as e:
        debug(f"Unexpected error: {str(e)}")
        raise

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: analyze_dxf_dwg.py <filepath>"}))
        sys.exit(1)

    try:
        result = analyze_dxf(sys.argv[1])
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
