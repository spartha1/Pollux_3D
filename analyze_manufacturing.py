#!/usr/bin/env python3
"""
Analizador de fabricación para Pollux 3D
Convierte problemas geométricos en métricas de fabricación útiles
"""

import sys
import json
import numpy as np
from pathlib import Path
from collections import defaultdict
import math

def analyze_manufacturing_features(file_path):
    """Analizar características de fabricación en archivos STL"""
    print(f"🏭 Analizando características de fabricación en: {file_path}")
    
    try:
        # Leer el archivo STL
        with open(file_path, 'rb') as f:
            # Saltar header (80 bytes)
            f.read(80)
            
            # Leer número de triángulos
            num_triangles_data = f.read(4)
            num_triangles = int.from_bytes(num_triangles_data, byteorder='little')
            
            print(f"📊 Procesando {num_triangles} triángulos...")
            
            # Leer todos los triángulos
            triangles = []
            normals = []
            
            for i in range(num_triangles):
                # Leer normal (12 bytes)
                normal_data = f.read(12)
                normal = np.frombuffer(normal_data, dtype=np.float32)
                normals.append(normal)
                
                # Leer 3 vértices (36 bytes total)
                triangle = []
                for j in range(3):
                    vertex_data = f.read(12)
                    if len(vertex_data) == 12:
                        x, y, z = np.frombuffer(vertex_data, dtype=np.float32)
                        triangle.append([x, y, z])
                
                if len(triangle) == 3:
                    triangles.append(triangle)
                
                # Leer attribute byte count (2 bytes) - saltamos
                f.read(2)
            
            triangles = np.array(triangles)
            normals = np.array(normals)
            
            # 1. ANÁLISIS DE PERÍMETROS DE CORTE
            print("🔍 Analizando perímetros de corte...")
            edge_count = defaultdict(int)
            edges = []
            
            for triangle in triangles:
                for i in range(3):
                    v1 = tuple(triangle[i])
                    v2 = tuple(triangle[(i + 1) % 3])
                    
                    # Crear arista ordenada
                    edge = tuple(sorted([v1, v2]))
                    edge_count[edge] += 1
                    edges.append(edge)
            
            # Aristas abiertas (aparecen solo una vez) = perímetros de corte
            open_edges = [edge for edge, count in edge_count.items() if count == 1]
            cutting_perimeters = len(open_edges)
            
            # 2. ANÁLISIS DE ORIENTACIONES DE DOBLECES
            print("🔍 Analizando orientaciones de dobleces...")
            normal_groups = defaultdict(list)
            
            for i, normal in enumerate(normals):
                # Normalizar
                if np.linalg.norm(normal) > 0:
                    normal = normal / np.linalg.norm(normal)
                    
                    # Agrupar por orientación (redondeado para tolerancia)
                    key = tuple(np.round(normal, 3))
                    normal_groups[key].append(i)
            
            # Contar orientaciones principales
            major_orientations = len([group for group in normal_groups.values() if len(group) > 10])
            
            # 3. ANÁLISIS DE PLANOS DE TRABAJO
            print("🔍 Analizando planos de trabajo...")
            plane_normals = []
            
            for normal in normals:
                if np.linalg.norm(normal) > 0:
                    normalized = normal / np.linalg.norm(normal)
                    
                    # Determinar plano principal (XY, XZ, YZ)
                    abs_normal = np.abs(normalized)
                    max_component = np.argmax(abs_normal)
                    
                    if abs_normal[max_component] > 0.9:  # Principalmente en un eje
                        plane_normals.append(max_component)
            
            # Contar planos de trabajo
            xy_faces = plane_normals.count(2)  # Normal en Z
            xz_faces = plane_normals.count(1)  # Normal en Y
            yz_faces = plane_normals.count(0)  # Normal en X
            
            # 4. ANÁLISIS DE AGUJEROS Y CARACTERÍSTICAS
            print("🔍 Detectando agujeros y características...")
            
            # Detectar agujeros circulares aproximados
            holes_detected = 0
            hole_diameters = []
            
            # Agrupar aristas abiertas por proximidad
            hole_clusters = []
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
                        
                    # Calcular distancia promedio entre aristas
                    dist = min(
                        np.linalg.norm(np.array(edge[0]) - np.array(other_edge[0])),
                        np.linalg.norm(np.array(edge[0]) - np.array(other_edge[1])),
                        np.linalg.norm(np.array(edge[1]) - np.array(other_edge[0])),
                        np.linalg.norm(np.array(edge[1]) - np.array(other_edge[1]))
                    )
                    
                    if dist < 5.0:  # Tolerance de 5mm
                        cluster.append(other_edge)
                        processed_edges.add(other_edge)
                
                if len(cluster) > 3:  # Potencial agujero
                    hole_clusters.append(cluster)
            
            holes_detected = len(hole_clusters)
            
            # 5. CALCULAR VOLUMEN DE MATERIAL
            print("🔍 Calculando volumen de material...")
            
            # Método de divergencia para volumen
            volume = 0.0
            for triangle in triangles:
                v1, v2, v3 = triangle
                volume += np.dot(v1, np.cross(v2, v3)) / 6.0
            
            material_volume = abs(volume)
            
            # 6. ANÁLISIS DE DIMENSIONES Y BOUNDING BOX
            all_vertices = triangles.reshape(-1, 3)
            bbox_min = np.min(all_vertices, axis=0)
            bbox_max = np.max(all_vertices, axis=0)
            dimensions = bbox_max - bbox_min
            
            # 7. CALCULAR MÉTRICAS DE FABRICACIÓN
            total_surface_area = 0
            for triangle in triangles:
                v1, v2, v3 = triangle
                edge1 = v2 - v1
                edge2 = v3 - v1
                cross = np.cross(edge1, edge2)
                area = 0.5 * np.linalg.norm(cross)
                total_surface_area += area
            
            # Calcular perímetro total de corte
            cutting_perimeter_length = 0
            for edge in open_edges:
                length = np.linalg.norm(np.array(edge[1]) - np.array(edge[0]))
                cutting_perimeter_length += length
            
            # RESULTADOS PARA FABRICACIÓN
            manufacturing_info = {
                "fabrication_analysis": {
                    "cutting_perimeters": int(cutting_perimeters),
                    "cutting_perimeter_length_mm": float(cutting_perimeter_length),
                    "bend_orientations": int(major_orientations),
                    "holes_detected": int(holes_detected),
                    "work_planes": {
                        "xy_faces": int(xy_faces),
                        "xz_faces": int(xz_faces),
                        "yz_faces": int(yz_faces),
                        "dominant_plane": "XY" if xy_faces > max(xz_faces, yz_faces) else "XZ" if xz_faces > yz_faces else "YZ"
                    }
                },
                "material_info": {
                    "material_volume_mm3": float(material_volume),
                    "surface_area_mm2": float(total_surface_area),
                    "dimensions_mm": {
                        "width": float(dimensions[0]),
                        "height": float(dimensions[1]),
                        "depth": float(dimensions[2])
                    },
                    "bounding_box": {
                        "min": [float(x) for x in bbox_min],
                        "max": [float(x) for x in bbox_max]
                    }
                },
                "manufacturing_complexity": {
                    "triangle_count": int(len(triangles)),
                    "vertex_count": int(len(all_vertices)),
                    "surface_complexity": "High" if len(triangles) > 5000 else "Medium" if len(triangles) > 1000 else "Low",
                    "fabrication_difficulty": "Complex" if cutting_perimeters > 50 else "Medium" if cutting_perimeters > 10 else "Simple"
                },
                "recommendations": {
                    "cutting_operations": int(cutting_perimeters),
                    "drilling_operations": int(holes_detected),
                    "bending_operations": int(major_orientations),
                    "material_efficiency": float(round((material_volume / (dimensions[0] * dimensions[1] * dimensions[2])) * 100, 1)) if np.prod(dimensions) > 0 else 0.0
                }
            }
            
            print(f"\n📋 ANÁLISIS DE FABRICACIÓN COMPLETADO:")
            print(f"   Perímetros de corte: {cutting_perimeters}")
            print(f"   Longitud de corte: {cutting_perimeter_length:.2f} mm")
            print(f"   Agujeros detectados: {holes_detected}")
            print(f"   Orientaciones de dobleces: {major_orientations}")
            print(f"   Volumen de material: {material_volume:.2f} mm³")
            print(f"   Plano dominante: {manufacturing_info['fabrication_analysis']['work_planes']['dominant_plane']}")
            
            return manufacturing_info
            
    except Exception as e:
        print(f"❌ Error en análisis de fabricación: {e}")
        return {"error": str(e)}

def main():
    if len(sys.argv) != 2:
        print("Uso: python analyze_manufacturing.py <archivo.stl>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"❌ Archivo no encontrado: {file_path}")
        sys.exit(1)
    
    results = analyze_manufacturing_features(file_path)
    
    print(f"\n📊 REPORTE DE FABRICACIÓN:")
    print("=" * 60)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
