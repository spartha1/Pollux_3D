#!/usr/bin/env python3
"""
Script para mejorar el análisis de volumen en archivos STL
Detecta y repara problemas comunes de geometría
"""

import sys
import json
import numpy as np
from pathlib import Path

def analyze_stl_volume_issues(file_path):
    """Analizar problemas de volumen en archivos STL"""
    print(f"🔍 Analizando problemas de volumen en: {file_path}")
    
    try:
        # Leer el archivo STL
        with open(file_path, 'rb') as f:
            # Saltar header (80 bytes)
            f.read(80)
            
            # Leer número de triángulos
            num_triangles_data = f.read(4)
            num_triangles = int.from_bytes(num_triangles_data, byteorder='little')
            
            print(f"📊 Triángulos en el archivo: {num_triangles}")
            
            # Leer todos los triángulos
            triangles = []
            for i in range(num_triangles):
                # Leer normal (12 bytes) - saltamos
                f.read(12)
                
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
            print(f"✅ Triángulos procesados: {len(triangles)}")
            
            # Análisis de problemas de volumen
            issues = []
            
            # 1. Verificar si hay triángulos degenerados
            degenerate_count = 0
            for i, triangle in enumerate(triangles):
                v1, v2, v3 = triangle
                
                # Calcular área del triángulo
                edge1 = v2 - v1
                edge2 = v3 - v1
                cross = np.cross(edge1, edge2)
                area = 0.5 * np.linalg.norm(cross)
                
                if area < 1e-10:
                    degenerate_count += 1
            
            if degenerate_count > 0:
                issues.append(f"Triángulos degenerados: {degenerate_count}")
                print(f"⚠️ Triángulos degenerados encontrados: {degenerate_count}")
            
            # 2. Verificar orientación de normales
            inconsistent_normals = 0
            for i, triangle in enumerate(triangles):
                v1, v2, v3 = triangle
                
                # Calcular normal del triángulo
                edge1 = v2 - v1
                edge2 = v3 - v1
                normal = np.cross(edge1, edge2)
                
                # Normalizar
                if np.linalg.norm(normal) > 0:
                    normal = normal / np.linalg.norm(normal)
                    
                    # Verificar si apunta hacia afuera (método simple)
                    center = (v1 + v2 + v3) / 3
                    
                    # Si el modelo está centrado en el origen, las normales deberían apuntar hacia afuera
                    if np.dot(normal, center) < 0:
                        inconsistent_normals += 1
            
            if inconsistent_normals > len(triangles) * 0.1:  # Más del 10%
                issues.append(f"Normales inconsistentes: {inconsistent_normals}")
                print(f"⚠️ Normales inconsistentes: {inconsistent_normals}")
            
            # 3. Verificar si es un modelo cerrado (watertight)
            # Crear un conjunto de aristas
            edges = set()
            for triangle in triangles:
                for i in range(3):
                    v1 = tuple(triangle[i])
                    v2 = tuple(triangle[(i + 1) % 3])
                    
                    # Ordenar vértices para crear arista consistente
                    edge = tuple(sorted([v1, v2]))
                    
                    if edge in edges:
                        edges.remove(edge)  # Arista compartida
                    else:
                        edges.add(edge)
            
            open_edges = len(edges)
            if open_edges > 0:
                issues.append(f"Aristas abiertas: {open_edges}")
                print(f"⚠️ Modelo no cerrado - Aristas abiertas: {open_edges}")
            else:
                print("✅ Modelo cerrado (watertight)")
            
            # 4. Calcular volumen usando método de divergencia
            volume = 0.0
            for triangle in triangles:
                v1, v2, v3 = triangle
                
                # Volumen usando el método de divergencia
                volume += np.dot(v1, np.cross(v2, v3)) / 6.0
            
            volume = abs(volume)
            
            # Resultados
            results = {
                "original_volume": volume,
                "triangles_analyzed": len(triangles),
                "issues_found": issues,
                "is_watertight": open_edges == 0,
                "degenerate_triangles": degenerate_count,
                "inconsistent_normals": inconsistent_normals,
                "open_edges": open_edges,
                "volume_calculation_method": "divergence_theorem"
            }
            
            # Determinar si el volumen es válido
            if volume < 1e-10:
                results["volume_status"] = "invalid_too_small"
                results["recommended_action"] = "repair_geometry"
            elif not results["is_watertight"]:
                results["volume_status"] = "invalid_not_watertight"
                results["recommended_action"] = "close_holes"
            elif degenerate_count > 0:
                results["volume_status"] = "questionable_degenerate_triangles"
                results["recommended_action"] = "remove_degenerate_triangles"
            else:
                results["volume_status"] = "valid"
                results["recommended_action"] = "none"
            
            print(f"\n📋 RESUMEN DEL ANÁLISIS:")
            print(f"   Volumen calculado: {volume:.6f}")
            print(f"   Estado: {results['volume_status']}")
            print(f"   Recomendación: {results['recommended_action']}")
            print(f"   Problemas: {len(issues)}")
            
            return results
            
    except Exception as e:
        print(f"❌ Error en análisis: {e}")
        return {"error": str(e)}

def main():
    if len(sys.argv) != 2:
        print("Uso: python analyze_volume_issues.py <archivo.stl>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"❌ Archivo no encontrado: {file_path}")
        sys.exit(1)
    
    results = analyze_stl_volume_issues(file_path)
    
    print(f"\n🔍 ANÁLISIS COMPLETO:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
