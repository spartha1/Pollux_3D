#!/usr/bin/env python3
"""
Preview generator for STL files
Generates 2D and wireframe previews
"""

import sys
import json
import numpy as np
import struct
import time
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

        vertices = []
        for i in range(num_triangles):
            # Skip normal vector (12 bytes)
            f.read(12)

            # Read 3 vertices (9 floats = 36 bytes)
            for j in range(3):
                x, y, z = struct.unpack('<fff', f.read(12))
                vertices.append([x, y, z])

            # Skip attribute byte count (2 bytes)
            f.read(2)

        return np.array(vertices)

def read_ascii_stl(filepath):
    """Read an STL file in ASCII format"""
    vertices = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('vertex'):
                coords = line.split()[1:4]
                vertices.append([float(x) for x in coords])
    return np.array(vertices)

def generate_2d_projection(vertices, view='top'):
    """Generate 2D projection coordinates"""
    if len(vertices) == 0:
        return []

    # Different projection views
    if view == 'top':
        # XY projection (looking down Z-axis)
        coords = vertices[:, [0, 1]]
    elif view == 'front':
        # XZ projection (looking down Y-axis)
        coords = vertices[:, [0, 2]]
    elif view == 'side':
        # YZ projection (looking down X-axis)
        coords = vertices[:, [1, 2]]
    else:
        coords = vertices[:, [0, 1]]  # Default to top view

    return coords.tolist()

def generate_wireframe_data(vertices):
    """Generate wireframe edge data"""
    if len(vertices) == 0:
        return []

    # Group vertices into triangles
    triangles = vertices.reshape(-1, 3, 3)
    edges = []

    for triangle in triangles:
        # Add the 3 edges of each triangle
        edges.extend([
            [triangle[0].tolist(), triangle[1].tolist()],
            [triangle[1].tolist(), triangle[2].tolist()],
            [triangle[2].tolist(), triangle[0].tolist()]
        ])

    return edges

def generate_previews(filepath):
    """Generate preview data for STL file"""
    debug(f"Generating previews for: {filepath}")
    start_time = time.time()

    try:
        # Try binary first
        try:
            vertices = read_binary_stl(filepath)
            file_format = "binary"
        except:
            vertices = read_ascii_stl(filepath)
            file_format = "ascii"

        if len(vertices) == 0:
            raise ValueError("No vertices found in STL file")

        debug(f"Found {len(vertices)} vertices in {file_format} format")

        # Calculate basic dimensions
        min_coords = np.min(vertices, axis=0)
        max_coords = np.max(vertices, axis=0)
        dimensions = max_coords - min_coords
        center = (min_coords + max_coords) / 2

        # Generate different view data
        previews = {
            "2d": {
                "top_view": generate_2d_projection(vertices, 'top'),
                "front_view": generate_2d_projection(vertices, 'front'),
                "side_view": generate_2d_projection(vertices, 'side'),
                "dimensions_2d": {
                    "width": float(dimensions[0]),
                    "height": float(dimensions[1]),
                    "depth": float(dimensions[2])
                }
            },
            "wireframe": {
                "edges": generate_wireframe_data(vertices),
                "center": center.tolist(),
                "bounds": {
                    "min": min_coords.tolist(),
                    "max": max_coords.tolist()
                }
            },
            "3d": {
                "vertices": vertices.tolist(),
                "triangles": len(vertices) // 3,
                "center": center.tolist(),
                "bounds": {
                    "min": min_coords.tolist(),
                    "max": max_coords.tolist()
                }
            },
            "metadata": {
                "vertex_count": len(vertices),
                "triangle_count": len(vertices) // 3,
                "file_format": file_format,
                "dimensions": {
                    "width": float(dimensions[0]),
                    "height": float(dimensions[1]),
                    "depth": float(dimensions[2])
                },
                "center_of_mass": {
                    "x": float(center[0]),
                    "y": float(center[1]),
                    "z": float(center[2])
                },
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
        }

        return previews

    except Exception as e:
        debug(f"Error generating previews: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Please provide an STL file path"}))
        sys.exit(1)

    # Get command line arguments
    file_path = sys.argv[1]
    preview_type = sys.argv[2] if len(sys.argv) > 2 else 'all'

    try:
        result = generate_previews(file_path)

        # If specific type requested, filter the result
        if preview_type != 'all' and preview_type in result:
            filtered_result = {
                preview_type: result[preview_type],
                'metadata': result.get('metadata', {})
            }
            print(json.dumps(filtered_result, indent=2))
        else:
            print(json.dumps(result, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
