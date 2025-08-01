#!/usr/bin/env python3
"""
Analizador STL con métricas de fabricación integradas
Para sistema Pollux 3D
"""

import sys
import json
import numpy as np
import time
from pathlib import Path
from collections import defaultdict

def calculate_weight_estimates(volume_mm3):
    """
    Calcular estimaciones de peso para diferentes materiales comunes en fabricación
    
    Args:
        volume_mm3: Volumen en mm³
    
    Returns:
        dict: Estimaciones de peso para diferentes materiales
    """
    if volume_mm3 <= 0:
        return {}
    
    # Convertir de mm³ a cm³ (dividir por 1000)
    volume_cm3 = volume_mm3 / 1000.0
    
    # Densidades de materiales comunes (g/cm³)
    material_densities = {
        # Metales
        "aluminum": {
            "density": 2.70,  # g/cm³
            "name": "Aluminio",
            "type": "Metal",
            "cost_per_kg": 2.0  # USD aproximado
        },
        "steel": {
            "density": 7.85,
            "name": "Acero",
            "type": "Metal",
            "cost_per_kg": 1.5
        },
        "stainless_steel": {
            "density": 8.0,
            "name": "Acero Inoxidable",
            "type": "Metal",
            "cost_per_kg": 4.0
        },
        "copper": {
            "density": 8.96,
            "name": "Cobre",
            "type": "Metal",
            "cost_per_kg": 8.0
        },
        "brass": {
            "density": 8.5,
            "name": "Latón",
            "type": "Metal",
            "cost_per_kg": 6.0
        },
        # Plásticos
        "pla": {
            "density": 1.25,
            "name": "PLA",
            "type": "Plástico",
            "cost_per_kg": 25.0
        },
        "abs": {
            "density": 1.05,
            "name": "ABS",
            "type": "Plástico",
            "cost_per_kg": 30.0
        },
        "petg": {
            "density": 1.27,
            "name": "PETG",
            "type": "Plástico",
            "cost_per_kg": 35.0
        },
        "nylon": {
            "density": 1.15,
            "name": "Nylon",
            "type": "Plástico",
            "cost_per_kg": 50.0
        },
        # Otros materiales
        "wood": {
            "density": 0.6,
            "name": "Madera (Pino)",
            "type": "Orgánico",
            "cost_per_kg": 3.0
        },
        "carbon_fiber": {
            "density": 1.6,
            "name": "Fibra de Carbono",
            "type": "Compuesto",
            "cost_per_kg": 200.0
        }
    }
    
    weight_estimates = {}
    
    for material_id, props in material_densities.items():
        weight_grams = volume_cm3 * props["density"]
        weight_kg = weight_grams / 1000.0
        estimated_cost = weight_kg * props["cost_per_kg"]
        
        weight_estimates[material_id] = {
            "name": props["name"],
            "type": props["type"],
            "weight_grams": round(weight_grams, 2),
            "weight_kg": round(weight_kg, 4),
            "density": props["density"],
            "estimated_cost_usd": round(estimated_cost, 2),
            "cost_per_kg": props["cost_per_kg"]
        }
    
    return weight_estimates

def analyze_stl_with_manufacturing(filepath):
    """Analizar archivo STL con métricas de fabricación"""
    debug_enabled = False
    
    def debug(msg):
        if debug_enabled:
            print(msg, file=sys.stderr, flush=True)
    
    debug(f"Analyzing STL file: {filepath}")
    start_time = time.time()
    
    try:
        if not Path(filepath).exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        debug("Reading STL file...")
        
        # Leer archivo STL
        with open(filepath, 'rb') as f:
            header = f.read(80)
            
            # Detectar formato
            is_ascii = False
            try:
                header_str = header.decode('ascii', errors='ignore').strip()
                if header_str.startswith('solid'):
                    f.seek(0)
                    sample = f.read(1024).decode('ascii', errors='ignore')
                    if 'vertex' in sample and 'facet' in sample:
                        is_ascii = True
            except:
                pass
            
            triangles = []
            vertices = []
            
            if is_ascii:
                debug("Processing ASCII STL")
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f_text:
                    content = f_text.read()
                    lines = content.split('\n')
                    current_triangle = []
                    
                    for line in lines:
                        line = line.strip()
                        if line.startswith('vertex'):
                            parts = line.split()
                            if len(parts) >= 4:
                                try:
                                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                                    vertex = [x, y, z]
                                    vertices.append(vertex)
                                    current_triangle.append(len(vertices) - 1)
                                    
                                    if len(current_triangle) == 3:
                                        triangles.append(current_triangle)
                                        current_triangle = []
                                except (ValueError, IndexError):
                                    continue
            else:
                debug("Processing Binary STL")
                f.seek(0)
                f.read(80)  # Skip header
                
                num_triangles_data = f.read(4)
                if len(num_triangles_data) == 4:
                    num_triangles = int.from_bytes(num_triangles_data, byteorder='little')
                    debug(f"Expected triangles: {num_triangles}")
                    
                    for i in range(num_triangles):
                        # Skip normal (12 bytes)
                        f.read(12)
                        
                        triangle_vertices = []
                        for j in range(3):
                            vertex_data = f.read(12)
                            if len(vertex_data) == 12:
                                x, y, z = np.frombuffer(vertex_data, dtype=np.float32)
                                vertex = [float(x), float(y), float(z)]
                                vertices.append(vertex)
                                triangle_vertices.append(len(vertices) - 1)
                        
                        if len(triangle_vertices) == 3:
                            triangles.append(triangle_vertices)
                        
                        # Skip attribute byte count (2 bytes)
                        f.read(2)
        
        debug(f"Successfully read STL: {len(triangles)} triangles, {len(vertices)} vertices")
        
        if not triangles:
            raise ValueError("No valid triangles found in STL file")
        
        vertices = np.array(vertices)
        
        # Calcular dimensiones
        bbox_min = np.min(vertices, axis=0)
        bbox_max = np.max(vertices, axis=0)
        dimensions = bbox_max - bbox_min
        
        # Calcular área superficial
        total_surface_area = 0
        for triangle in triangles:
            v1, v2, v3 = vertices[triangle[0]], vertices[triangle[1]], vertices[triangle[2]]
            edge1 = v2 - v1
            edge2 = v3 - v1
            cross = np.cross(edge1, edge2)
            area = 0.5 * np.linalg.norm(cross)
            total_surface_area += area
        
        # Calcular volumen
        volume = 0.0
        for triangle in triangles:
            v1, v2, v3 = vertices[triangle[0]], vertices[triangle[1]], vertices[triangle[2]]
            volume += np.dot(v1, np.cross(v2, v3)) / 6.0
        volume = abs(volume)
        
        # Calcular centro de masa
        center_of_mass = np.mean(vertices, axis=0)
        
        # --- ANÁLISIS DE FABRICACIÓN ---
        debug("Analyzing manufacturing features...")
        
        # 1. Análisis de aristas (perímetros de corte)
        edge_count = defaultdict(int)
        for triangle in triangles:
            for i in range(3):
                v1_idx, v2_idx = triangle[i], triangle[(i + 1) % 3]
                edge = tuple(sorted([v1_idx, v2_idx]))
                edge_count[edge] += 1
        
        open_edges = [edge for edge, count in edge_count.items() if count == 1]
        cutting_perimeters = len(open_edges)
        
        # Calcular longitud de corte
        cutting_perimeter_length = 0
        for edge in open_edges:
            v1, v2 = vertices[edge[0]], vertices[edge[1]]
            length = np.linalg.norm(v2 - v1)
            cutting_perimeter_length += length
        
        # 2. Análisis de orientaciones (normales)
        normal_groups = defaultdict(list)
        for triangle in triangles:
            v1, v2, v3 = vertices[triangle[0]], vertices[triangle[1]], vertices[triangle[2]]
            edge1 = v2 - v1
            edge2 = v3 - v1
            normal = np.cross(edge1, edge2)
            
            if np.linalg.norm(normal) > 0:
                normal = normal / np.linalg.norm(normal)
                key = tuple(np.round(normal, 2))
                normal_groups[key].append(triangle)
        
        major_orientations = len([group for group in normal_groups.values() if len(group) > 10])
        
        # 3. Análisis de planos de trabajo
        xy_faces = xz_faces = yz_faces = 0
        for triangle in triangles:
            v1, v2, v3 = vertices[triangle[0]], vertices[triangle[1]], vertices[triangle[2]]
            edge1 = v2 - v1
            edge2 = v3 - v1
            normal = np.cross(edge1, edge2)
            
            if np.linalg.norm(normal) > 0:
                normal = normal / np.linalg.norm(normal)
                abs_normal = np.abs(normal)
                max_component = np.argmax(abs_normal)
                
                if abs_normal[max_component] > 0.8:
                    if max_component == 2:  # Z normal -> XY plane
                        xy_faces += 1
                    elif max_component == 1:  # Y normal -> XZ plane
                        xz_faces += 1
                    else:  # X normal -> YZ plane
                        yz_faces += 1
        
        # 4. Detección de agujeros (clustering de aristas abiertas)
        holes_detected = 0
        if open_edges:
            processed_edges = set()
            for edge in open_edges:
                if edge in processed_edges:
                    continue
                
                cluster = [edge]
                processed_edges.add(edge)
                
                # Buscar aristas cercanas
                for other_edge in open_edges:
                    if other_edge in processed_edges:
                        continue
                    
                    # Calcular distancia mínima entre aristas
                    dist = min(
                        np.linalg.norm(vertices[edge[0]] - vertices[other_edge[0]]),
                        np.linalg.norm(vertices[edge[0]] - vertices[other_edge[1]]),
                        np.linalg.norm(vertices[edge[1]] - vertices[other_edge[0]]),
                        np.linalg.norm(vertices[edge[1]] - vertices[other_edge[1]])
                    )
                    
                    if dist < 3.0:  # Tolerance de 3mm
                        cluster.append(other_edge)
                        processed_edges.add(other_edge)
                
                if len(cluster) >= 3:
                    holes_detected += 1
        
        # Tiempo de análisis
        analysis_time = int((time.time() - start_time) * 1000)
        
        # Determinar plano dominante
        dominant_plane = "XY" if xy_faces > max(xz_faces, yz_faces) else "XZ" if xz_faces > yz_faces else "YZ"
        
        # Resultado final
        result = {
            "dimensions": {
                "width": float(dimensions[0]),
                "height": float(dimensions[1]), 
                "depth": float(dimensions[2])
            },
            "volume": float(volume),
            "area": float(total_surface_area),
            "analysis_time_ms": analysis_time,
            "metadata": {
                "triangles": len(triangles),
                "faces": len(triangles),
                "edges": len(vertices) * 3,  # Aproximado
                "vertices": len(vertices),
                "vertex_count": len(vertices),
                "face_count": len(triangles),
                "center_of_mass": {
                    "x": float(center_of_mass[0]),
                    "y": float(center_of_mass[1]),
                    "z": float(center_of_mass[2])
                },
                "bbox_min": {
                    "x": float(bbox_min[0]),
                    "y": float(bbox_min[1]),
                    "z": float(bbox_min[2])
                },
                "bbox_max": {
                    "x": float(bbox_max[0]),
                    "y": float(bbox_max[1]),
                    "z": float(bbox_max[2])
                },
                "format": "ASCII" if is_ascii else "BINARY",
                "file_size_bytes": Path(filepath).stat().st_size
            },
            "manufacturing": {
                "cutting_perimeters": cutting_perimeters,
                "cutting_length_mm": float(cutting_perimeter_length),
                "bend_orientations": major_orientations,
                "holes_detected": holes_detected,
                "work_planes": {
                    "xy_faces": xy_faces,
                    "xz_faces": xz_faces,
                    "yz_faces": yz_faces,
                    "dominant_plane": dominant_plane
                },
                "complexity": {
                    "surface_complexity": "High" if len(triangles) > 5000 else "Medium" if len(triangles) > 1000 else "Low",
                    "fabrication_difficulty": "Complex" if cutting_perimeters > 50 else "Medium" if cutting_perimeters > 10 else "Simple"
                },
                "material_efficiency": float(round((volume / (dimensions[0] * dimensions[1] * dimensions[2])) * 100, 1)) if np.prod(dimensions) > 0 else 0.0,
                "weight_estimates": calculate_weight_estimates(volume)
            }
        }
        
        debug("Analysis complete")
        return result
        
    except Exception as e:
        debug(f"Error in analysis: {e}")
        return {
            "error": str(e),
            "analysis_time_ms": int((time.time() - start_time) * 1000)
        }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No file path provided"}))
        sys.exit(1)
    
    filepath = sys.argv[1]
    result = analyze_stl_with_manufacturing(filepath)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
