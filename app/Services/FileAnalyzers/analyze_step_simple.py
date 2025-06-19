#!/usr/bin/env python3
"""
Analizador simple de STEP sin PythonOCC.
Extrae información básica del archivo STEP.
"""
import sys
import json
import time
import os
import re
import traceback

def debug(msg):
    """Print debug messages to stderr"""
    print(msg, file=sys.stderr, flush=True)

def analyze_step_simple(filepath):
    """Análisis básico de archivo STEP sin PythonOCC."""
    debug(f"Analyzing STEP file: {filepath}")
    t0 = time.time()

    try:
        # Verificar que el archivo existe
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        # Leer archivo con diferentes encodings
        content = ""
        tried_encodings = []
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            tried_encodings.append(encoding)
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                debug(f"Successfully read file with {encoding} encoding")
                break
            except UnicodeError:
                continue

        if not content:
            raise ValueError(f"Could not read file with any encoding. Tried: {', '.join(tried_encodings)}")

        # Información básica
        metadata = {}
        debug("Analyzing file content...")

        # Buscar información del header
        header_match = re.search(r'HEADER;(.*?)ENDSEC;', content, re.DOTALL | re.IGNORECASE)
        if header_match:
            header_content = header_match.group(1)
            debug("Found HEADER section")

            # Extract header information with patterns
            header_patterns = {
                'file_name': [
                    r"FILE_NAME\s*\(\s*'([^']+)'",
                    r'FILE_NAME\s*\(\s*"([^"]+)"'
                ],
                'description': [
                    r"FILE_DESCRIPTION\s*\(\s*\(\s*'([^']+)'",
                    r'FILE_DESCRIPTION\s*\(\s*\(\s*"([^"]+)"'
                ],
                'schema': [
                    r"FILE_SCHEMA\s*\(\s*\(\s*'([^']+)'",
                    r'FILE_SCHEMA\s*\(\s*\(\s*"([^"]+)"'
                ]
            }

            for key, patterns in header_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, header_content, re.IGNORECASE)
                    if match:
                        metadata[key] = match.group(1)
                        debug(f"Found {key}: {match.group(1)}")
                        break

        # Buscar la sección DATA
        debug("Searching for DATA section...")
        data_content = ""
        data_patterns = [
            r'DATA;(.*?)ENDSEC;',
            r'DATA;(.*?)ENDSEC\s*;',
            r'DATA\s*;(.*?)ENDSEC',
            r'DATA;(.*)$'
        ]

        for pattern in data_patterns:
            data_match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if data_match:
                data_content = data_match.group(1)
                debug("Found DATA section")
                break

        # Si no encontramos DATA section, usar todo el contenido después del header
        if not data_content:
            debug("No DATA section found, using full content")
            if header_match:
                data_content = content[header_match.end():]
            else:
                data_content = content

        # Contar entidades
        debug("Counting entities...")
        entities = {
            'faces': 0, 'edges': 0, 'vertices': 0,
            'surfaces': 0, 'curves': 0, 'shells': 0,
            'solids': 0, 'points': 0
        }

        entity_patterns = {
            'faces': [r'#\d+\s*=\s*(ADVANCED_FACE|FACE_BOUND|FACE_SURFACE)'],
            'edges': [r'#\d+\s*=\s*(EDGE_CURVE|EDGE_LOOP|ORIENTED_EDGE)'],
            'vertices': [r'#\d+\s*=\s*(VERTEX_POINT|VERTEX_LOOP)'],
            'surfaces': [r'#\d+\s*=\s*(PLANE|CYLINDRICAL_SURFACE|CONICAL_SURFACE|SURFACE)'],
            'curves': [r'#\d+\s*=\s*(LINE|CIRCLE|ELLIPSE|B_SPLINE_CURVE)'],
            'shells': [r'#\d+\s*=\s*(CLOSED_SHELL|OPEN_SHELL)'],
            'solids': [r'#\d+\s*=\s*(MANIFOLD_SOLID_BREP|BREP_WITH_VOIDS)'],
            'points': [r'#\d+\s*=\s*CARTESIAN_POINT']
        }

        for entity_type, patterns in entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, data_content, re.IGNORECASE)
                entities[entity_type] += len(matches)
                debug(f"Found {len(matches)} {entity_type}")

        # Buscar puntos para calcular dimensiones
        debug("Calculating dimensions...")
        points = []
        point_pattern = r'CARTESIAN_POINT\s*\([^)]*\(\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*\)'

        for match in re.finditer(point_pattern, data_content, re.IGNORECASE):
            try:
                x, y, z = map(float, match.groups())
                points.append((x, y, z))
            except (ValueError, TypeError):
                continue

        dimensions = {"width": 0, "height": 0, "depth": 0}
        if points:
            x_coords, y_coords, z_coords = zip(*points)
            dimensions = {
                "width": max(x_coords) - min(x_coords),
                "height": max(y_coords) - min(y_coords),
                "depth": max(z_coords) - min(z_coords)
            }
            debug(f"Calculated dimensions: {dimensions}")

        # File metadata
        file_size = os.path.getsize(filepath)
        total_entities = sum(entities.values())

        metadata.update({
            **entities,
            "file_size_kb": round(file_size / 1024, 2),
            "total_entities": total_entities,
            "total_points": len(points),
            "analysis_complete": True
        })

        elapsed_ms = int((time.time() - t0) * 1000)
        debug(f"Analysis completed in {elapsed_ms}ms")

        return {
            "dimensions": dimensions,
            "volume": None,  # Requires geometry engine
            "area": None,    # Requires geometry engine
            "metadata": metadata,
            "analysis_time_ms": elapsed_ms
        }

    except Exception as e:
        debug(f"Error analyzing STEP file: {str(e)}")
        raise

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: analyze_step_simple.py <filepath>"}))
        sys.exit(1)

    try:
        result = analyze_step_simple(sys.argv[1])
        print(json.dumps(result))
    except Exception as e:
        error_info = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_info))
        sys.exit(1)

if __name__ == "__main__":
    main()
