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

def calculate_manufacturing_metrics(volume_cm3, area_cm2):
    """Calculate manufacturing metrics for different materials"""
    debug("Calculating manufacturing metrics...")
    
    # Material properties (density in g/cm³, cost per kg in USD)
    materials = {
        'aluminum': {'density': 2.7, 'cost_per_kg': 2.5, 'name': 'Aluminio', 'type': 'metal'},
        'steel': {'density': 7.85, 'cost_per_kg': 1.2, 'name': 'Acero', 'type': 'metal'},
        'stainless_steel': {'density': 8.0, 'cost_per_kg': 4.0, 'name': 'Acero Inoxidable', 'type': 'metal'},
        'copper': {'density': 8.96, 'cost_per_kg': 8.5, 'name': 'Cobre', 'type': 'metal'},
        'brass': {'density': 8.5, 'cost_per_kg': 6.0, 'name': 'Latón', 'type': 'metal'},
        'pla': {'density': 1.24, 'cost_per_kg': 25.0, 'name': 'PLA', 'type': 'plastic'},
        'abs': {'density': 1.05, 'cost_per_kg': 30.0, 'name': 'ABS', 'type': 'plastic'},
        'petg': {'density': 1.27, 'cost_per_kg': 35.0, 'name': 'PETG', 'type': 'plastic'},
        'nylon': {'density': 1.15, 'cost_per_kg': 45.0, 'name': 'Nylon', 'type': 'plastic'},
        'wood': {'density': 0.6, 'cost_per_kg': 3.0, 'name': 'Madera', 'type': 'composite'},
        'carbon_fiber': {'density': 1.6, 'cost_per_kg': 50.0, 'name': 'Fibra de Carbono', 'type': 'composite'}
    }
    
    weight_estimates = {}
    
    for material_id, props in materials.items():
        # Calculate weight in grams and kg
        weight_grams = volume_cm3 * props['density']
        weight_kg = weight_grams / 1000.0
        
        # Calculate estimated cost
        estimated_cost = weight_kg * props['cost_per_kg']
        
        weight_estimates[material_id] = {
            'name': props['name'],
            'type': props['type'],
            'weight_grams': round(weight_grams, 2),
            'weight_kg': round(weight_kg, 4),
            'density': props['density'],
            'estimated_cost_usd': round(estimated_cost, 2),
            'cost_per_kg': props['cost_per_kg']
        }
    
    # Basic manufacturing complexity analysis
    complexity_score = min(100, (volume_cm3 * 0.1) + (area_cm2 * 0.01))
    
    if complexity_score < 30:
        fabrication_difficulty = "Baja"
        surface_complexity = "Simple"
    elif complexity_score < 70:
        fabrication_difficulty = "Media"
        surface_complexity = "Moderada"
    else:
        fabrication_difficulty = "Alta"
        surface_complexity = "Compleja"
    
    manufacturing_data = {
        'cutting_perimeters': int(area_cm2 / 10),  # Estimate based on surface area
        'cutting_length_mm': round(area_cm2 * 2, 2),  # Approximate cutting length
        'bend_orientations': 2,  # Default estimate
        'holes_detected': 0,  # Would need more complex geometry analysis
        'work_planes': {
            'xy_faces': 1,
            'xz_faces': 1, 
            'yz_faces': 1,
            'dominant_plane': 'xy'
        },
        'complexity': {
            'surface_complexity': surface_complexity,
            'fabrication_difficulty': fabrication_difficulty
        },
        'material_efficiency': round(min(95.0, 85.0 + (10.0 / (1 + complexity_score/50))), 2),
        'weight_estimates': weight_estimates
    }
    
    debug(f"Generated manufacturing data for {len(weight_estimates)} materials")
    return manufacturing_data

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
        
        # Calculate manufacturing metrics
        volume_cm3 = volume  # Volume is already in cm³
        area_cm2 = total_area  # Area is already in cm²
        manufacturing_data = calculate_manufacturing_metrics(volume_cm3, area_cm2)
        
        # Prepare result
        result = {
            "dimensions": {
                "width": float(stats['dimensions'][0]),
                "height": float(stats['dimensions'][1]),
                "depth": float(stats['dimensions'][2])
            },
            "volume": float(volume),
            "area": float(total_area),
            "manufacturing": manufacturing_data,
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
