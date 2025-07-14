#!/usr/bin/env python3
"""
Generador de archivos STL de prueba para verificar el análisis de metadatos.
"""

import numpy as np
import os
import struct

def create_cube_stl(size=10.0, filename="test_cube.stl"):
    """
    Crear un cubo STL simple para pruebas.
    
    Args:
        size: Tamaño del cubo (default: 10.0)
        filename: Nombre del archivo STL (default: "test_cube.stl")
    """
    # Definir vértices del cubo
    vertices = np.array([
        # Cara frontal (z=0)
        [0, 0, 0], [size, 0, 0], [size, size, 0],
        [0, 0, 0], [size, size, 0], [0, size, 0],
        
        # Cara trasera (z=size)
        [0, 0, size], [size, size, size], [size, 0, size],
        [0, 0, size], [0, size, size], [size, size, size],
        
        # Cara izquierda (x=0)
        [0, 0, 0], [0, size, 0], [0, size, size],
        [0, 0, 0], [0, size, size], [0, 0, size],
        
        # Cara derecha (x=size)
        [size, 0, 0], [size, size, size], [size, size, 0],
        [size, 0, 0], [size, 0, size], [size, size, size],
        
        # Cara inferior (y=0)
        [0, 0, 0], [0, 0, size], [size, 0, size],
        [0, 0, 0], [size, 0, size], [size, 0, 0],
        
        # Cara superior (y=size)
        [0, size, 0], [size, size, size], [0, size, size],
        [0, size, 0], [size, size, 0], [size, size, size],
    ])
    
    # Calcular normales para cada triángulo
    triangles = vertices.reshape(-1, 3, 3)
    normals = []
    
    for triangle in triangles:
        # Calcular normal usando producto cruzado
        v1 = triangle[1] - triangle[0]
        v2 = triangle[2] - triangle[0]
        normal = np.cross(v1, v2)
        # Normalizar
        normal = normal / np.linalg.norm(normal)
        normals.append(normal)
    
    normals = np.array(normals)
    
    # Escribir archivo STL binario
    with open(filename, 'wb') as f:
        # Header (80 bytes)
        header = f"Generated test cube {size}x{size}x{size}".encode('ascii')
        header = header[:80].ljust(80, b'\0')
        f.write(header)
        
        # Número de triángulos
        num_triangles = len(triangles)
        f.write(struct.pack('<I', num_triangles))
        
        # Escribir cada triángulo
        for i, triangle in enumerate(triangles):
            # Normal (3 floats)
            f.write(struct.pack('<fff', *normals[i]))
            
            # Vértices (9 floats)
            for vertex in triangle:
                f.write(struct.pack('<fff', *vertex))
            
            # Attribute byte count (2 bytes)
            f.write(struct.pack('<H', 0))
    
    print(f"Archivo STL creado: {filename}")
    print(f"Dimensiones: {size} x {size} x {size}")
    print(f"Triángulos: {num_triangles}")
    print(f"Volumen esperado: {size**3}")
    print(f"Área esperada: {6 * size**2}")
    
    return filename

def create_pyramid_stl(base_size=10.0, height=8.0, filename="test_pyramid.stl"):
    """
    Crear una pirámide STL para pruebas.
    
    Args:
        base_size: Tamaño de la base (default: 10.0)
        height: Altura de la pirámide (default: 8.0)
        filename: Nombre del archivo STL (default: "test_pyramid.stl")
    """
    # Vértices de la pirámide
    vertices = np.array([
        # Base (4 triángulos)
        [0, 0, 0], [base_size, 0, 0], [base_size, base_size, 0],
        [0, 0, 0], [base_size, base_size, 0], [0, base_size, 0],
        
        # Caras laterales (4 triángulos)
        # Cara frontal
        [0, 0, 0], [base_size/2, base_size/2, height], [base_size, 0, 0],
        # Cara derecha
        [base_size, 0, 0], [base_size/2, base_size/2, height], [base_size, base_size, 0],
        # Cara trasera
        [base_size, base_size, 0], [base_size/2, base_size/2, height], [0, base_size, 0],
        # Cara izquierda
        [0, base_size, 0], [base_size/2, base_size/2, height], [0, 0, 0],
    ])
    
    # Calcular normales
    triangles = vertices.reshape(-1, 3, 3)
    normals = []
    
    for triangle in triangles:
        v1 = triangle[1] - triangle[0]
        v2 = triangle[2] - triangle[0]
        normal = np.cross(v1, v2)
        if np.linalg.norm(normal) > 0:
            normal = normal / np.linalg.norm(normal)
        normals.append(normal)
    
    normals = np.array(normals)
    
    # Escribir archivo STL binario
    with open(filename, 'wb') as f:
        # Header
        header = f"Generated test pyramid {base_size}x{base_size}x{height}".encode('ascii')
        header = header[:80].ljust(80, b'\0')
        f.write(header)
        
        # Número de triángulos
        num_triangles = len(triangles)
        f.write(struct.pack('<I', num_triangles))
        
        # Escribir triángulos
        for i, triangle in enumerate(triangles):
            # Normal
            f.write(struct.pack('<fff', *normals[i]))
            
            # Vértices
            for vertex in triangle:
                f.write(struct.pack('<fff', *vertex))
            
            # Attribute byte count
            f.write(struct.pack('<H', 0))
    
    expected_volume = (base_size * base_size * height) / 3
    print(f"Archivo STL creado: {filename}")
    print(f"Dimensiones base: {base_size} x {base_size}")
    print(f"Altura: {height}")
    print(f"Triángulos: {num_triangles}")
    print(f"Volumen esperado: {expected_volume:.2f}")
    
    return filename

def main():
    """Crear archivos STL de prueba."""
    print("Generando archivos STL de prueba...")
    
    # Crear directorio de pruebas si no existe
    test_dir = "test_stl_files"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    # Crear cubo
    cube_file = os.path.join(test_dir, "test_cube.stl")
    create_cube_stl(10.0, cube_file)
    
    print()
    
    # Crear pirámide
    pyramid_file = os.path.join(test_dir, "test_pyramid.stl")
    create_pyramid_stl(10.0, 8.0, pyramid_file)
    
    print(f"\nArchivos creados en: {test_dir}")
    print("Puedes usar estos archivos para probar el análisis STL.")

if __name__ == "__main__":
    main()
