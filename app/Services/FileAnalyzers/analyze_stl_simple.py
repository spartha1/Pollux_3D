#!/usr/bin/env python3
import sys
import json
import time
import struct
import traceback
import numpy as np
from pathlib import Path

def debug(msg):
    """Print debug messages to stderr"""
    print(msg, file=sys.stderr, flush=True)

def read_binary_stl(filepath):
    """Read an STL file in binary format"""
    with open(filepath, 'rb') as f:
        # Skip header
        f.seek(80)

        # Read number of triangles
        num_triangles = struct.unpack('<I', f.read(4))[0]

        # Each triangle is 50 bytes: 12 floats (3 vertices + normal) + 2 padding bytes
        data = np.frombuffer(f.read(num_triangles * 50), dtype=np.uint8)

        # Reshape and get vertices (skip normal and padding)
        vertices = np.zeros((num_triangles * 3, 3))
        for i in range(num_triangles):
            base = i * 50 + 12  # Skip normal vector
            for j in range(3):
                vertex_base = base + j * 12
                vertices[i * 3 + j] = struct.unpack('<fff', data[vertex_base:vertex_base + 12])

        return vertices

def read_ascii_stl(filepath):
    """Read an STL file in ASCII format"""
    vertices = []
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 4 and parts[0] == 'vertex':
                try:
                    vertex = [float(x) for x in parts[1:]]
                    vertices.append(vertex)
                except ValueError:
                    continue
    return np.array(vertices)

def analyze_stl(filepath):
    """Analyze an STL file and return dimensions, volume, and topology"""
    debug(f"Analyzing STL file: {filepath}")
    start_time = time.time()

    try:
        # Try binary first
        try:
            vertices = read_binary_stl(filepath)
            file_format = "BINARY"
            debug("Successfully read binary STL")
        except:
            # If binary fails, try ASCII
            vertices = read_ascii_stl(filepath)
            file_format = "ASCII"
            debug("Successfully read ASCII STL")

        if len(vertices) == 0:
            raise ValueError("No vertices found in STL file")

        debug(f"Found {len(vertices)} vertices")

        # Calculate dimensions
        min_coords = np.min(vertices, axis=0)
        max_coords = np.max(vertices, axis=0)
        dimensions = max_coords - min_coords
        debug(f"Dimensions: {dimensions}")

        # Calculate other metrics
        num_vertices = len(vertices)
        num_triangles = num_vertices // 3
        num_edges = num_triangles * 3
        debug(f"Counted {num_triangles} triangles")

        # Reshape vertices into triangles
        triangles = vertices.reshape(-1, 3, 3)

        # Calculate areas
        v0 = triangles[:, 1] - triangles[:, 0]
        v1 = triangles[:, 2] - triangles[:, 0]
        areas = 0.5 * np.linalg.norm(np.cross(v0, v1), axis=1)
        total_area = float(np.sum(areas))
        debug(f"Total surface area: {total_area}")

        # Calculate volume (may be 0 for 2D shapes)
        v2 = triangles[:, 2] - triangles[:, 1]
        cross_products = np.cross(v1, v2)
        volumes = np.abs(np.sum(v0 * cross_products, axis=1)) / 6
        total_volume = float(np.sum(volumes))
        debug(f"Total volume: {total_volume}")

        # Calculate center (using weighted average of triangle centers)
        triangle_centers = np.mean(triangles, axis=1)
        if total_area > 0:
            # Weight by triangle areas for better accuracy
            center_of_mass = np.average(triangle_centers, weights=areas, axis=0)
        else:
            # Fallback to simple average if areas are zero
            center_of_mass = np.mean(triangle_centers, axis=0)
        debug(f"Center of mass: {center_of_mass}")

        # Create result dictionary
        analysis_time_ms = int((time.time() - start_time) * 1000)

        result = {
            "dimensions": {
                "width": float(dimensions[0]),
                "height": float(dimensions[1]),
                "depth": float(dimensions[2])
            },
            "volume": total_volume,
            "area": total_area,
            "analysis_time_ms": analysis_time_ms,
            "metadata": {
                "triangles": int(num_triangles),
                "faces": int(num_triangles),
                "edges": int(num_edges),
                "vertices": int(num_vertices),
                "vertex_count": int(num_vertices),
                "face_count": int(num_triangles),
                "center_of_mass": {
                    "x": float(center_of_mass[0]),
                    "y": float(center_of_mass[1]),
                    "z": float(center_of_mass[2])
                },
                "bbox_min": {
                    "x": float(min_coords[0]),
                    "y": float(min_coords[1]),
                    "z": float(min_coords[2])
                },
                "bbox_max": {
                    "x": float(max_coords[0]),
                    "y": float(max_coords[1]),
                    "z": float(max_coords[2])
                },
                "format": file_format,
                "file_size_bytes": Path(filepath).stat().st_size if Path(filepath).exists() else 0
            }
        }

        debug("Analysis complete")
        return result

    except Exception as e:
        debug(f"Error analyzing STL: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Please provide an STL file path"}))
        sys.exit(1)

    try:
        result = analyze_stl(sys.argv[1])
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "traceback": traceback.format_exc() if 'traceback' in sys.modules else None
        }))
        sys.exit(1)
