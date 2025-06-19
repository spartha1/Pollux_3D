#!/usr/bin/env python3
import sys
import json
import time
import os
import numpy as np
import struct
import traceback

def debug(msg):
    """Print debug messages to stderr"""
    print(msg, file=sys.stderr, flush=True)

def read_binary_stl(filepath):
    """Read a binary STL file."""
    with open(filepath, 'rb') as f:
        # Skip header
        f.seek(80)
        # Read number of triangles
        count = struct.unpack('I', f.read(4))[0]

        # Each triangle is 50 bytes: normal(3*4), vertices(9*4), attribute(2)
        data = np.frombuffer(f.read(count * 50), dtype=np.uint8)
        triangles = data.view(dtype=np.float32).reshape((-1, 12))[:, 3:12]
        return triangles.reshape((-1, 3, 3))

def read_ascii_stl(filepath):
    """Read an ASCII STL file."""
    vertices = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if 'vertex' in line.lower():
                    nums = line.strip().split()[1:]
                    vertices.extend([float(n) for n in nums])
    except UnicodeDecodeError:
        return None

    if not vertices:
        return None

    return np.array(vertices).reshape((-1, 3, 3))

def analyze_stl(filepath):
    """Analyze STL file and return dimensions, volume, and area."""
    debug(f"Analyzing STL file: {filepath}")
    t0 = time.time()

    try:
        # Try binary first
        try:
            triangles = read_binary_stl(filepath)
            file_format = "BINARY"
            debug("Successfully read binary STL")
        except Exception as e:
            debug(f"Binary read failed: {str(e)}, trying ASCII")
            triangles = read_ascii_stl(filepath)
            if triangles is None:
                raise ValueError("Could not read STL file in either binary or ASCII format")
            file_format = "ASCII"
            debug("Successfully read ASCII STL")

        # Calculate bounding box and dimensions
        vertices = triangles.reshape(-1, 3)
        min_corner = np.min(vertices, axis=0)
        max_corner = np.max(vertices, axis=0)
        dimensions = max_corner - min_corner

        # Calculate areas
        vectors = np.diff(triangles, axis=1)
        cross_products = np.cross(vectors[:, 0], vectors[:, 1])
        areas = 0.5 * np.sqrt(np.sum(cross_products**2, axis=1))
        total_area = float(np.sum(areas))

        # Calculate volume (approximate for watertight meshes)
        centroids = np.mean(triangles, axis=1)
        signed_volumes = np.sum(cross_products * centroids, axis=1) / 6.0
        volume = float(abs(np.sum(signed_volumes)))

        # Get unique vertices for topology information
        unique_vertices = np.unique(vertices.round(decimals=6), axis=0)
        vertex_count = len(unique_vertices)

        # Count unique edges
        edges = set()
        for tri in triangles:
            for i in range(3):
                v1 = tuple(np.round(tri[i], decimals=6))
                v2 = tuple(np.round(tri[(i + 1) % 3], decimals=6))
                edge = tuple(sorted([v1, v2]))
                edges.add(edge)
        edge_count = len(edges)

        # Create result dictionary
        dims = {
            "width": float(dimensions[0]),
            "height": float(dimensions[1]),
            "depth": float(dimensions[2])
        }

        # Calculate center of mass (using weighted average of triangle centers)
        centroids = np.mean(triangles, axis=1)
        if total_area > 0:
            center_of_mass = np.average(centroids, weights=areas, axis=0)
        else:
            center_of_mass = np.mean(centroids, axis=0)

        metadata = {
            "triangles": int(len(triangles)),
            "faces": int(len(triangles)),
            "edges": edge_count,
            "vertices": vertex_count,
            "center_of_mass": {
                "x": float(center_of_mass[0]),
                "y": float(center_of_mass[1]),
                "z": float(center_of_mass[2])
            },
            "bbox_min": {
                "x": float(min_corner[0]),
                "y": float(min_corner[1]),
                "z": float(min_corner[2])
            },
            "bbox_max": {
                "x": float(max_corner[0]),
                "y": float(max_corner[1]),
                "z": float(max_corner[2])
            },
            "format": file_format
        }

        elapsed_ms = int((time.time() - t0) * 1000)

        return {
            "dimensions": dims,
            "volume": volume,
            "area": total_area,
            "metadata": metadata,
            "analysis_time_ms": elapsed_ms
        }

    except Exception as e:
        debug(f"Error analyzing STL: {str(e)}")
        raise

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Please provide an STL file path"}))
        sys.exit(1)

    path = sys.argv[1]
    try:
        result = analyze_stl(path)
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
