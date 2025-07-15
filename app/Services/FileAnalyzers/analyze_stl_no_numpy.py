#!/usr/bin/env python3
import sys
import json
import time
import struct
import traceback
import os
from pathlib import Path

def debug(msg):
    """Print debug messages to stderr"""
    print(msg, file=sys.stderr, flush=True)

def read_binary_stl(filepath):
    """Read an STL file in binary format"""
    try:
        with open(filepath, 'rb') as f:
            # Skip the 80-byte header
            header = f.read(80)
            
            # Read the number of triangles
            triangle_count_data = f.read(4)
            if len(triangle_count_data) != 4:
                raise ValueError("Invalid STL file: cannot read triangle count")
            
            triangle_count = struct.unpack('<I', triangle_count_data)[0]
            debug(f"Triangle count: {triangle_count}")
            
            vertices = []
            
            # Read each triangle
            for i in range(triangle_count):
                # Normal vector (12 bytes, 3 floats) - skip for now
                normal = f.read(12)
                
                # Three vertices (36 bytes, 9 floats)
                vertex_data = f.read(36)
                if len(vertex_data) != 36:
                    raise ValueError(f"Invalid STL file: incomplete vertex data for triangle {i}")
                
                # Unpack the 9 floats (3 vertices * 3 coordinates)
                coords = struct.unpack('<9f', vertex_data)
                
                # Add the three vertices
                vertices.extend([
                    [coords[0], coords[1], coords[2]],  # Vertex 1
                    [coords[3], coords[4], coords[5]],  # Vertex 2
                    [coords[6], coords[7], coords[8]]   # Vertex 3
                ])
                
                # Skip attribute byte count (2 bytes)
                f.read(2)
            
            return vertices
    except Exception as e:
        debug(f"Error reading binary STL: {e}")
        raise

def read_ascii_stl(filepath):
    """Read an STL file in ASCII format"""
    try:
        vertices = []
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('vertex'):
                    coords = line.split()[1:4]
                    vertex = [float(x) for x in coords]
                    vertices.append(vertex)
        return vertices
    except Exception as e:
        debug(f"Error reading ASCII STL: {e}")
        raise

def calculate_basic_stats(vertices):
    """Calculate basic statistics without numpy"""
    if not vertices:
        return None
    
    # Convert to simple list of coordinates
    x_coords = [v[0] for v in vertices]
    y_coords = [v[1] for v in vertices]
    z_coords = [v[2] for v in vertices]
    
    # Calculate min/max for dimensions
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    min_z, max_z = min(z_coords), max(z_coords)
    
    # Calculate dimensions
    width = max_x - min_x
    height = max_y - min_y
    depth = max_z - min_z
    
    # Calculate center of mass (average of all vertices)
    center_x = sum(x_coords) / len(x_coords)
    center_y = sum(y_coords) / len(y_coords)
    center_z = sum(z_coords) / len(z_coords)
    
    return {
        'dimensions': [width, height, depth],
        'bbox_min': [min_x, min_y, min_z],
        'bbox_max': [max_x, max_y, max_z],
        'center_of_mass': [center_x, center_y, center_z]
    }

def calculate_triangle_area(v1, v2, v3):
    """Calculate area of a triangle using cross product"""
    # Vector from v1 to v2
    a = [v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]]
    # Vector from v1 to v3  
    b = [v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]]
    
    # Cross product
    cross = [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    ]
    
    # Magnitude of cross product
    magnitude = (cross[0]**2 + cross[1]**2 + cross[2]**2) ** 0.5
    
    # Area is half the magnitude
    return magnitude / 2.0

def analyze_stl(filepath):
    """Analyze an STL file and return metadata"""
    start_time = time.time()
    
    try:
        debug(f"Analyzing STL file: {filepath}")
        
        # Try binary format first
        try:
            vertices = read_binary_stl(filepath)
            debug("Successfully read binary STL")
            file_format = "BINARY"
        except:
            # If binary fails, try ASCII
            vertices = read_ascii_stl(filepath)
            debug("Successfully read ASCII STL")
            file_format = "ASCII"
        
        debug(f"Found {len(vertices)} vertices")
        
        # Calculate basic statistics
        stats = calculate_basic_stats(vertices)
        if not stats:
            raise ValueError("No vertices found in STL file")
        
        debug(f"Dimensions: {stats['dimensions']}")
        
        # Count triangles (every 3 vertices = 1 triangle)
        triangle_count = len(vertices) // 3
        debug(f"Counted {triangle_count} triangles")
        
        # Calculate total surface area
        total_area = 0.0
        for i in range(0, len(vertices), 3):
            if i + 2 < len(vertices):
                area = calculate_triangle_area(vertices[i], vertices[i+1], vertices[i+2])
                total_area += area
        
        debug(f"Total surface area: {total_area}")
        
        # For STL files, volume calculation requires watertight mesh
        # We'll set it to 0 for now as it requires complex algorithms
        volume = 0.0
        debug(f"Total volume: {volume}")
        
        debug(f"Center of mass: {stats['center_of_mass']}")
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        # Calculate analysis time
        analysis_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        
        debug("Analysis complete")
        
        # Prepare result
        result = {
            "dimensions": {
                "width": float(stats['dimensions'][0]),
                "height": float(stats['dimensions'][1]),
                "depth": float(stats['dimensions'][2])
            },
            "volume": float(volume),
            "area": float(total_area),
            "analysis_time_ms": analysis_time,
            "metadata": {
                "triangles": triangle_count,
                "faces": triangle_count,
                "edges": len(vertices),
                "vertices": len(vertices),
                "vertex_count": len(vertices),
                "face_count": triangle_count,
                "center_of_mass": {
                    "x": float(stats['center_of_mass'][0]),
                    "y": float(stats['center_of_mass'][1]),
                    "z": float(stats['center_of_mass'][2])
                },
                "bbox_min": {
                    "x": float(stats['bbox_min'][0]),
                    "y": float(stats['bbox_min'][1]),
                    "z": float(stats['bbox_min'][2])
                },
                "bbox_max": {
                    "x": float(stats['bbox_max'][0]),
                    "y": float(stats['bbox_max'][1]),
                    "z": float(stats['bbox_max'][2])
                },
                "format": file_format,
                "file_size_bytes": file_size
            }
        }
        
        return result
        
    except Exception as e:
        debug(f"Error analyzing STL: {e}")
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python analyze_stl_no_numpy.py <stl_file>"}))
        sys.exit(1)
    
    filepath = sys.argv[1]
    result = analyze_stl(filepath)
    print(json.dumps(result, indent=None))
