#!/usr/bin/env python3
"""
Analizador simple de STEP sin PythonOCC.
Extrae información básica del archivo STEP.
"""
import sys
import json
import re
import time
import os

def analyze_step_simple(filepath):
    """Análisis básico de archivo STEP sin PythonOCC."""
    t0 = time.time()

    # Verificar que el archivo existe
    if not os.path.exists(filepath):
        return {
            "error": f"File not found: {filepath}",
            "dimensions": {"width": 0, "height": 0, "depth": 0},
            "volume": 0,
            "area": 0,
            "metadata": {}
        }

    # Leer archivo con diferentes encodings
    content = ""
    for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
        try:
            with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
                break
        except:
            continue

    if not content:
        return {
            "error": "Could not read file with any encoding",
            "dimensions": {"width": 0, "height": 0, "depth": 0},
            "volume": 0,
            "area": 0,
            "metadata": {}
        }

    # Información básica
    metadata = {}

    # Buscar información del header
    header_match = re.search(r'HEADER;(.*?)ENDSEC;', content, re.DOTALL | re.IGNORECASE)
    if header_match:
        header_content = header_match.group(1)

        # Nombre del archivo
        name_patterns = [
            r"FILE_NAME\s*\(\s*'([^']+)'",
            r'FILE_NAME\s*\(\s*"([^"]+)"',
            r"FILE_NAME\s*\('[^']*',\s*'([^']+)'"
        ]
        for pattern in name_patterns:
            name_match = re.search(pattern, header_content, re.IGNORECASE)
            if name_match:
                metadata['file_name'] = name_match.group(1)
                break

        # Descripción
        desc_patterns = [
            r"FILE_DESCRIPTION\s*\(\s*\(\s*'([^']+)'",
            r'FILE_DESCRIPTION\s*\(\s*\(\s*"([^"]+)"'
        ]
        for pattern in desc_patterns:
            desc_match = re.search(pattern, header_content, re.IGNORECASE)
            if desc_match:
                metadata['description'] = desc_match.group(1)
                break

        # Schema
        schema_patterns = [
            r"FILE_SCHEMA\s*\(\s*\(\s*'([^']+)'",
            r'FILE_SCHEMA\s*\(\s*\(\s*"([^"]+)"'
        ]
        for pattern in schema_patterns:
            schema_match = re.search(pattern, header_content, re.IGNORECASE)
            if schema_match:
                metadata['schema'] = schema_match.group(1)
                break

    # Buscar la sección DATA - más flexible
    data_content = ""
    data_patterns = [
        r'DATA;(.*?)ENDSEC;',
        r'DATA;(.*?)ENDSEC\s*;',
        r'DATA\s*;(.*?)ENDSEC',
        r'DATA;(.*)$'  # Si no hay ENDSEC
    ]

    for pattern in data_patterns:
        data_match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if data_match:
            data_content = data_match.group(1)
            break

    # Si no encontramos DATA section, buscar entidades directamente
    if not data_content:
        # Buscar patrones de entidades STEP (#número = ...)
        entity_pattern = r'#\d+\s*=\s*[A-Z_]+'
        if re.search(entity_pattern, content):
            # Usar todo el contenido después del header
            if header_match:
                data_content = content[header_match.end():]
            else:
                data_content = content

    # Contar diferentes tipos de entidades STEP
    entities = {
        'faces': 0,
        'edges': 0,
        'vertices': 0,
        'surfaces': 0,
        'curves': 0,
        'shells': 0,
        'solids': 0,
        'points': 0
    }

    # Patrones mejorados y más flexibles
    entity_patterns = {
        'faces': [
            r'#\d+\s*=\s*ADVANCED_FACE',
            r'#\d+\s*=\s*FACE_BOUND',
            r'#\d+\s*=\s*FACE_OUTER_BOUND',
            r'#\d+\s*=\s*FACE_SURFACE',
            r'#\d+\s*=\s*ORIENTED_FACE',
            r'#\d+\s*=\s*FACE\s*\('
        ],
        'edges': [
            r'#\d+\s*=\s*EDGE_CURVE',
            r'#\d+\s*=\s*EDGE_LOOP',
            r'#\d+\s*=\s*ORIENTED_EDGE',
            r'#\d+\s*=\s*SEAM_EDGE',
            r'#\d+\s*=\s*SUBEDGE',
            r'#\d+\s*=\s*EDGE\s*\('
        ],
        'vertices': [
            r'#\d+\s*=\s*VERTEX_POINT',
            r'#\d+\s*=\s*VERTEX_LOOP',
            r'#\d+\s*=\s*VERTEX_SHELL',
            r'#\d+\s*=\s*VERTEX\s*\('
        ],
        'surfaces': [
            r'#\d+\s*=\s*PLANE\s*\(',
            r'#\d+\s*=\s*CYLINDRICAL_SURFACE',
            r'#\d+\s*=\s*CONICAL_SURFACE',
            r'#\d+\s*=\s*SPHERICAL_SURFACE',
            r'#\d+\s*=\s*TOROIDAL_SURFACE',
            r'#\d+\s*=\s*SURFACE_OF_REVOLUTION',
            r'#\d+\s*=\s*SURFACE_OF_LINEAR_EXTRUSION',
            r'#\d+\s*=\s*B_SPLINE_SURFACE',
            r'#\d+\s*=\s*BOUNDED_SURFACE',
            r'#\d+\s*=\s*ELEMENTARY_SURFACE',
            r'#\d+\s*=\s*SURFACE\s*\('
        ],
        'curves': [
            r'#\d+\s*=\s*LINE\s*\(',
            r'#\d+\s*=\s*CIRCLE\s*\(',
            r'#\d+\s*=\s*ELLIPSE\s*\(',
            r'#\d+\s*=\s*PARABOLA\s*\(',
            r'#\d+\s*=\s*HYPERBOLA\s*\(',
            r'#\d+\s*=\s*POLYLINE\s*\(',
            r'#\d+\s*=\s*B_SPLINE_CURVE',
            r'#\d+\s*=\s*BEZIER_CURVE',
            r'#\d+\s*=\s*TRIMMED_CURVE',
            r'#\d+\s*=\s*COMPOSITE_CURVE',
            r'#\d+\s*=\s*CURVE\s*\('
        ],
        'shells': [
            r'#\d+\s*=\s*CLOSED_SHELL',
            r'#\d+\s*=\s*OPEN_SHELL',
            r'#\d+\s*=\s*ORIENTED_CLOSED_SHELL',
            r'#\d+\s*=\s*ORIENTED_OPEN_SHELL',
            r'#\d+\s*=\s*SHELL\s*\('
        ],
        'solids': [
            r'#\d+\s*=\s*MANIFOLD_SOLID_BREP',
            r'#\d+\s*=\s*BREP_WITH_VOIDS',
            r'#\d+\s*=\s*FACETED_BREP',
            r'#\d+\s*=\s*ADVANCED_BREP_SHAPE_REPRESENTATION',
            r'#\d+\s*=\s*SOLID\s*\('
        ],
        'points': [
            r'#\d+\s*=\s*CARTESIAN_POINT'
        ]
    }

    # Usar el contenido completo si no encontramos data_content
    search_content = data_content if data_content else content

    # Contar entidades
    for entity_type, patterns in entity_patterns.items():
        for pattern in patterns:
            matches = re.findall(pattern, search_content, re.IGNORECASE | re.MULTILINE)
            entities[entity_type] += len(matches)

    # Buscar y analizar puntos cartesianos para estimar dimensiones
    point_patterns = [
        # Formato estándar: CARTESIAN_POINT('name',(x,y,z))
        r'CARTESIAN_POINT\s*\(\s*\'[^\']*\'\s*,\s*\(\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*\)\s*\)',
        # Formato sin nombre: CARTESIAN_POINT((x,y,z))
        r'CARTESIAN_POINT\s*\(\s*\(\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*\)\s*\)',
        # Formato alternativo con espacios
        r'CARTESIAN_POINT\s*\(\s*\'[^\']*\'\s*,\s*\(\s*([-\d.eE+]+)\s+,\s+([-\d.eE+]+)\s+,\s+([-\d.eE+]+)\s*\)\s*\)'
    ]

    points = []
    for pattern in point_patterns:
        matches = re.findall(pattern, search_content, re.IGNORECASE)
        points.extend(matches)

    dimensions = {"width": 0, "height": 0, "depth": 0}
    bbox_info = {}

    if points:
        try:
            x_coords = [float(p[0]) for p in points if p[0]]
            y_coords = [float(p[1]) for p in points if p[1]]
            z_coords = [float(p[2]) for p in points if p[2]]

            if x_coords and y_coords and z_coords:
                dimensions = {
                    "width": round(max(x_coords) - min(x_coords), 3),
                    "height": round(max(y_coords) - min(y_coords), 3),
                    "depth": round(max(z_coords) - min(z_coords), 3)
                }

                bbox_info = {
                    "point_count": len(points),
                    "bbox_min": {
                        "x": round(min(x_coords), 3),
                        "y": round(min(y_coords), 3),
                        "z": round(min(z_coords), 3)
                    },
                    "bbox_max": {
                        "x": round(max(x_coords), 3),
                        "y": round(max(y_coords), 3),
                        "z": round(max(z_coords), 3)
                    }
                }
        except (ValueError, IndexError) as e:
            metadata['coordinate_parse_error'] = str(e)

    # Contar todas las entidades (líneas que empiezan con #número)
    all_entities_pattern = r'#\d+\s*='
    all_entities = re.findall(all_entities_pattern, search_content, re.MULTILINE)
    total_entities = len(all_entities)

    # Si no encontramos entidades en data_content, buscar en todo el archivo
    if total_entities == 0:
        all_entities = re.findall(all_entities_pattern, content, re.MULTILINE)
        total_entities = len(all_entities)

    # Analizar tipos de entidades más comunes
    entity_types = {}
    entity_type_pattern = r'#\d+\s*=\s*([A-Z_]+[A-Z0-9_]*)\s*\('
    entity_matches = re.finditer(entity_type_pattern, search_content, re.IGNORECASE)

    for match in entity_matches:
        entity_type = match.group(1).upper()
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

    # Si no encontramos tipos en data_content, buscar en todo el archivo
    if not entity_types:
        entity_matches = re.finditer(entity_type_pattern, content, re.IGNORECASE)
        for match in entity_matches:
            entity_type = match.group(1).upper()
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

    # Top 15 tipos de entidades
    top_entities = sorted(entity_types.items(), key=lambda x: x[1], reverse=True)[:15]

    # Información del archivo
    file_size = os.path.getsize(filepath)

    elapsed_ms = int((time.time() - t0) * 1000)

    # Compilar metadata
    metadata.update({
        **entities,
        "file_size_kb": round(file_size / 1024, 2),
        "total_entities": total_entities,
        "entity_types": dict(top_entities) if top_entities else {},
        **bbox_info,
        "analysis_complete": False
    })

    # Mensajes de advertencia más específicos
    if total_entities == 0:
        metadata["warning"] = "No se encontraron entidades STEP en el archivo. El archivo podría estar vacío, corrupto o usar un formato no reconocido."
        # Agregar información de depuración
        metadata["debug_info"] = {
            "file_size_bytes": file_size,
            "content_length": len(content),
            "has_header": bool(header_match),
            "has_data_section": bool(data_content),
            "first_100_chars": content[:100] if content else ""
        }
    else:
        metadata["warning"] = f"Análisis limitado sin PythonOCC. Se encontraron {total_entities} entidades STEP."

    return {
        "dimensions": dimensions,
        "volume": 0,  # No se puede calcular sin geometría real
        "area": 0,    # No se puede calcular sin geometría real
        "metadata": metadata,
        "analysis_time_ms": elapsed_ms
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No file path provided"}))
        sys.exit(1)

    filepath = sys.argv[1]
    result = analyze_step_simple(filepath)
    print(json.dumps(result))
