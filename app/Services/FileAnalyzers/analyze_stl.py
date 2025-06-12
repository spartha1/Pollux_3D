#!/usr/bin/env python3
import sys
import json
import time
import numpy as np

try:
    from stl import mesh
    STL_AVAILABLE = True
except ImportError:
    STL_AVAILABLE = False

def analyze_stl(filepath):
    """Analiza un archivo STL y devuelve dimensiones, volumen, área y topología."""
    if not STL_AVAILABLE:
        raise ImportError(
            "numpy-stl no está instalado. Instálalo con:\n"
            "pip install numpy-stl\n"
            "o consulta: https://github.com/WoLpH/numpy-stl"
        )

    t0 = time.time()

    # Leer STL
    model = mesh.Mesh.from_file(filepath)

    # Dimensiones y bounding box
    x_min, x_max = float(model.x.min()), float(model.x.max())
    y_min, y_max = float(model.y.min()), float(model.y.max())
    z_min, z_max = float(model.z.min()), float(model.z.max())

    dims = {
        "width": round(x_max - x_min, 3),
        "height": round(y_max - y_min, 3),
        "depth": round(z_max - z_min, 3),
    }

    # Propiedades de masa (volumen, centro de masa, inercia)
    volume, cog, inertia = model.get_mass_properties()
    volume = round(float(volume), 3)

    # Centro de masa
    center_of_mass = {
        "x": round(float(cog[0]), 3),
        "y": round(float(cog[1]), 3),
        "z": round(float(cog[2]), 3)
    }

    # Área superficial
    # Calcular el área de cada triángulo y sumar
    areas = []
    for i in range(len(model.vectors)):
        # Obtener los tres vértices del triángulo
        v0, v1, v2 = model.vectors[i]
        # Calcular vectores de las aristas
        edge1 = v1 - v0
        edge2 = v2 - v0
        # Producto cruz para obtener el área
        cross = np.cross(edge1, edge2)
        area = 0.5 * np.linalg.norm(cross)
        areas.append(area)

    total_area = round(float(sum(areas)), 3)

    # Contar vértices únicos y aristas
    # Extraer todos los vértices
    vertices = model.vectors.reshape(-1, 3)
    # Encontrar vértices únicos (con tolerancia)
    unique_vertices = np.unique(np.round(vertices, decimals=6), axis=0)
    vertex_count = len(unique_vertices)

    # Contar aristas únicas
    edges = set()
    for triangle in model.vectors:
        # Cada triángulo tiene 3 aristas
        for i in range(3):
            v1 = tuple(np.round(triangle[i], decimals=6))
            v2 = tuple(np.round(triangle[(i + 1) % 3], decimals=6))
            # Ordenar para evitar duplicados (v1,v2) y (v2,v1)
            edge = tuple(sorted([v1, v2]))
            edges.add(edge)

    edge_count = len(edges)

    # Metadata
    metadata = {
        "triangles": int(len(model)),
        "faces": int(len(model)),  # En STL, cada triángulo es una cara
        "edges": edge_count,
        "vertices": vertex_count,
        "center_of_mass": center_of_mass,
        "bbox_min": {"x": round(x_min, 3), "y": round(y_min, 3), "z": round(z_min, 3)},
        "bbox_max": {"x": round(x_max, 3), "y": round(y_max, 3), "z": round(z_max, 3)},
    }

    # Verificar si el modelo es ASCII o binario
    try:
        with open(filepath, 'rb') as f:
            header = f.read(5)
            is_ascii = header.startswith(b'solid')
            metadata["format"] = "ASCII" if is_ascii else "Binary"
    except:
        pass

    elapsed_ms = int((time.time() - t0) * 1000)

    return {
        "dimensions": dims,
        "volume": volume,
        "area": total_area,
        "metadata": metadata,
        "analysis_time_ms": elapsed_ms
    }

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Uso: analyze_stl.py <ruta_al_archivo.stl>"}))
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
