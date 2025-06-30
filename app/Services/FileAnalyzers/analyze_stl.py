#!/usr/bin/env python3
import os
os.environ['PYTHONHASHSEED'] = '0'  # Disable hash randomization

import sys
import json
import time
import numpy as np
import struct
import traceback
from pathlib import Path

def debug(msg):
    """Print debug messages to stderr"""
    print(msg, file=sys.stderr, flush=True)

def read_binary_stl(filepath):
    """Read a binary STL file."""
    try:
        with open(filepath, 'rb') as f:
            # Read and save header
            header = f.read(80)
            # Check if it might be ASCII by looking for 'solid' at start
            if header.startswith(b'solid '):
                return None, None

            # Read number of triangles
            count = struct.unpack('I', f.read(4))[0]

            # Validate triangle count
            file_size = Path(filepath).stat().st_size
            expected_size = 84 + (50 * count)  # Header + count + triangles
            if file_size != expected_size:
                debug(f"File size mismatch: expected {expected_size}, got {file_size}")
                if count > 1000000:  # Unreasonable number of triangles
                    return None, None

            # Each triangle is 50 bytes: normal(3*4), vertices(9*4), attribute(2)
            data = np.frombuffer(f.read(count * 50), dtype=np.uint8)
            triangles = data.view(dtype=np.float32).reshape((-1, 12))[:, 3:12]
            return triangles.reshape((-1, 3, 3)), "binary"
    except Exception as e:
        debug(f"Binary read error: {str(e)}")
        return None, None

def read_ascii_stl(filepath):
    """Read an ASCII STL file."""
    vertices = []
    normal_count = 0
    vertex_count = 0
    facet_count = 0
    try:
        with open(filepath, 'r') as f:
            in_facet = False
            for line in f:
                line = line.strip().lower()
                if 'facet normal' in line:
                    in_facet = True
                    normal_count += 1
                elif 'vertex' in line:
                    if not in_facet:
                        continue
                    nums = line.split()[1:]
                    if len(nums) != 3:
                        continue
                    try:
                        coords = [float(n) for n in nums]
                        vertices.extend(coords)
                        vertex_count += 1
                    except ValueError:
                        continue
                elif 'endfacet' in line:
                    if in_facet and vertex_count % 3 == 0:
                        facet_count += 1
                    in_facet = False

            if facet_count > 0 and vertex_count == facet_count * 3:
                return np.array(vertices).reshape((-1, 3, 3)), "ascii"

            return None, None

    except Exception as e:
        debug(f"ASCII read error: {str(e)}")
        return None, None

def analyze_stl(filepath):
    """Analyze STL file and return dimensions, volume, and area."""
    debug(f"Analyzing STL file: {filepath}")
    t0 = time.time()

    try:
        # Try binary first
        triangles, format_type = read_binary_stl(filepath)
        if triangles is None:
            triangles, format_type = read_ascii_stl(filepath)
            if triangles is None:
                raise ValueError("Could not read STL file in either binary or ASCII format. The file may be corrupted or in an unsupported format.")

        debug(f"Successfully read {format_type.upper()} STL")

        # Validate mesh data
        if len(triangles) == 0:
            raise ValueError("Invalid STL file: No geometry found")

        # Calculate bounding box and dimensions
        vertices = triangles.reshape(-1, 3)
        min_corner = np.min(vertices, axis=0)
        max_corner = np.max(vertices, axis=0)
        dimensions = max_corner - min_corner

        # Calculate areas and validate triangles
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

        # Count edges and analyze mesh topology
        edges = {}
        for i, tri in enumerate(triangles):
            for j in range(3):
                v1 = tuple(np.round(tri[j], decimals=6))
                v2 = tuple(np.round(tri[(j + 1) % 3], decimals=6))
                edge = tuple(sorted([v1, v2]))
                if edge in edges:
                    edges[edge].append(i)
                else:
                    edges[edge] = [i]

        # Analyze mesh quality
        edge_count = len(edges)
        manifold_edges = sum(1 for edge_faces in edges.values() if len(edge_faces) == 2)
        non_manifold_edges = sum(1 for edge_faces in edges.values() if len(edge_faces) > 2)
        boundary_edges = sum(1 for edge_faces in edges.values() if len(edge_faces) == 1)

        # Create result dictionary
        dims = {
            "width": float(dimensions[0]),
            "height": float(dimensions[1]),
            "depth": float(dimensions[2])
        }

        result = {
            "format": format_type.upper(),
            "dimensions": dims,
            "bounding_box": {
                "min": [float(x) for x in min_corner],
                "max": [float(x) for x in max_corner]
            },
            "area": round(total_area, 6),
            "volume": round(volume, 6),
            "topology": {
                "triangles": len(triangles),
                "vertices": vertex_count,
                "edges": edge_count
            },
            "quality": {
                "is_watertight": boundary_edges == 0,
                "is_manifold": non_manifold_edges == 0,
                "boundary_edges": boundary_edges,
                "non_manifold_edges": non_manifold_edges,
                "manifold_edges": manifold_edges
            },
            "processing_time": round(time.time() - t0, 3)
        }

        return result

    except Exception as e:
        debug(f"Error in analyze_stl: {str(e)}")
        debug(traceback.format_exc())
        raise

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_stl.py <stl_file>", file=sys.stderr)
        sys.exit(1)

    try:
        result = analyze_stl(sys.argv[1])
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), file=sys.stderr)
        sys.exit(1)
