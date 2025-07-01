#!/usr/bin/env python3
"""
STL Preview Image Generator
Generates 2D and wireframe preview images for STL files
"""

import sys
import json
import numpy as np
import struct
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
import io
import base64
from PIL import Image

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

def generate_2d_image(vertices, output_path, width=800, height=600, view='top'):
    """Generate 2D projection image"""
    debug(f"Generating 2D {view} view image...")

    # Create projection based on view
    if view == 'top':
        # XY projection (looking down Z-axis)
        coords = vertices[:, [0, 1]]
        xlabel, ylabel = 'X', 'Y'
    elif view == 'front':
        # XZ projection (looking down Y-axis)
        coords = vertices[:, [0, 2]]
        xlabel, ylabel = 'X', 'Z'
    elif view == 'side':
        # YZ projection (looking down X-axis)
        coords = vertices[:, [1, 2]]
        xlabel, ylabel = 'Y', 'Z'
    else:
        coords = vertices[:, [0, 1]]  # Default to top view
        xlabel, ylabel = 'X', 'Y'

    # Create figure
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)

    # Plot points
    ax.scatter(coords[:, 0], coords[:, 1], s=0.5, c='#0066cc', alpha=0.6)

    # Set equal aspect ratio and labels
    ax.set_aspect('equal')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f'2D {view.capitalize()} View')

    # Remove margins and set background
    ax.margins(0.05)
    fig.patch.set_facecolor('white')

    # Save image
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

    debug(f"2D {view} view saved to: {output_path}")

def generate_wireframe_image(vertices, output_path, width=800, height=600):
    """Generate wireframe image"""
    debug("Generating wireframe image...")

    # Reshape vertices into triangles
    triangles = vertices.reshape(-1, 3, 3)

    # Create figure with 3D projection
    fig = plt.figure(figsize=(width/100, height/100), dpi=100)
    ax = fig.add_subplot(111, projection='3d')

    # Plot wireframe
    for triangle in triangles:
        # Plot the 3 edges of each triangle
        for i in range(3):
            start = triangle[i]
            end = triangle[(i + 1) % 3]
            ax.plot([start[0], end[0]], [start[1], end[1]], [start[2], end[2]],
                   'b-', linewidth=0.5, alpha=0.7)

    # Set labels and title
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Wireframe View')

    # Set equal aspect ratio
    max_range = np.array([vertices[:, 0].max()-vertices[:, 0].min(),
                         vertices[:, 1].max()-vertices[:, 1].min(),
                         vertices[:, 2].max()-vertices[:, 2].min()]).max() / 2.0
    mid_x = (vertices[:, 0].max()+vertices[:, 0].min()) * 0.5
    mid_y = (vertices[:, 1].max()+vertices[:, 1].min()) * 0.5
    mid_z = (vertices[:, 2].max()+vertices[:, 2].min()) * 0.5

    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

    # Set background color
    fig.patch.set_facecolor('white')

    # Save image
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

    debug(f"Wireframe image saved to: {output_path}")

def generate_preview_image(filepath, output_path, preview_type='2d', **kwargs):
    """Generate preview image for STL file"""
    debug(f"Generating {preview_type} preview for: {filepath}")
    start_time = time.time()

    try:
        # Read STL file
        try:
            vertices = read_binary_stl(filepath)
            file_format = "binary"
        except:
            vertices = read_ascii_stl(filepath)
            file_format = "ascii"

        if len(vertices) == 0:
            raise ValueError("No vertices found in STL file")

        debug(f"Found {len(vertices)} vertices in {file_format} format")

        # Generate image based on type
        if preview_type == '2d':
            view = kwargs.get('view', 'top')
            generate_2d_image(vertices, output_path,
                            width=kwargs.get('width', 800),
                            height=kwargs.get('height', 600),
                            view=view)
        elif preview_type == 'wireframe':
            generate_wireframe_image(vertices, output_path,
                                   width=kwargs.get('width', 800),
                                   height=kwargs.get('height', 600))
        else:
            raise ValueError(f"Unsupported preview type: {preview_type}")

        processing_time = int((time.time() - start_time) * 1000)

        # Return success result
        result = {
            "success": True,
            "output_path": str(output_path),
            "preview_type": preview_type,
            "processing_time_ms": processing_time,
            "file_format": file_format,
            "vertex_count": len(vertices)
        }

        return result

    except Exception as e:
        debug(f"Error generating preview: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(json.dumps({
            "error": "Usage: python generate_preview_images.py <stl_file> <output_path> <preview_type> [width] [height]"
        }))
        sys.exit(1)

    # Get command line arguments
    stl_file = sys.argv[1]
    output_path = sys.argv[2]
    preview_type = sys.argv[3]
    width = int(sys.argv[4]) if len(sys.argv) > 4 else 800
    height = int(sys.argv[5]) if len(sys.argv) > 5 else 600

    # Generate preview
    result = generate_preview_image(
        stl_file,
        output_path,
        preview_type,
        width=width,
        height=height
    )

    # Output result as JSON
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result.get("success", False) else 1)
