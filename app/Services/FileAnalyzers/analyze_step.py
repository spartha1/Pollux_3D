#!/usr/bin/env python3
import sys
import json
import time
import os
import re
from datetime import datetime
from collections import defaultdict

try:
    # Importaciones principales de PythonOCC
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_RetVoid, IFSelect_RetError, IFSelect_RetFail, IFSelect_RetStop
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib_Add
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
    from OCC.Core.TopoDS import topods_Face, topods_Edge, topods_Vertex
    from OCC.Core.TCollection import TCollection_AsciiString
    from OCC.Core.Interface import Interface_Static

    # Importaciones opcionales - no críticas para funcionamiento básico
    try:
        from OCC.Core.STEPConstruct import STEPConstruct_UnitContext
    except ImportError:
        STEPConstruct_UnitContext = None

    try:
        from OCC.Core.StepRepr import StepRepr_RepresentationItem
    except ImportError:
        StepRepr_RepresentationItem = None

    try:
        from OCC.Core.StepBasic import StepBasic_ProductDefinition
    except ImportError:
        StepBasic_ProductDefinition = None

    # Intentar importar módulos para análisis de ensamblajes
    try:
        from OCC.Core.XSControl import XSControl_WorkSession
        from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
        from OCC.Core.TDF import TDF_Label, TDF_LabelSequence
        from OCC.Core.TDocStd import TDocStd_Document
        from OCC.Core.XCAFApp import XCAFApp_Application
        from OCC.Core.XCAFDoc import (XCAFDoc_DocumentTool, XCAFDoc_ShapeTool,
                                     XCAFDoc_ColorTool, XCAFDoc_AssemblyItemRef)
        XCAF_AVAILABLE = True
    except ImportError:
        XCAF_AVAILABLE = False

    OCC_AVAILABLE = True
except ImportError as e:
    print(f"Debug: PythonOCC import failed: {e}", file=sys.stderr)
    OCC_AVAILABLE = False
    XCAF_AVAILABLE = False

# ======================================================================
# FUNCIONES AUXILIARES MEJORADAS
# ======================================================================

def get_file_diagnostic_info(filepath):
    """Obtiene información diagnóstica detallada del archivo."""
    if not os.path.exists(filepath):
        return {"error": "Archivo no encontrado", "exists": False}

    try:
        stat = os.stat(filepath)
        size_mb = round(stat.st_size / (1024 * 1024), 2)
        modified_date = datetime.fromtimestamp(stat.st_mtime).isoformat()
        created_date = datetime.fromtimestamp(stat.st_ctime).isoformat()
        file_ext = os.path.splitext(filepath)[1].lower()

        # Detección de tipo de archivo
        file_type = "Desconocido"
        magic_bytes = None
        with open(filepath, 'rb') as f:
            header = f.read(100)
            magic_bytes = header.hex()

            if header.startswith(b"ISO-10303-21"):
                file_type = "STEP (ISO-10303-21)"
            elif header.startswith(b"HEADER;"):
                file_type = "STEP (Formato antiguo)"
            elif b"SOLIDWORKS" in header:
                file_type = "Posible archivo SOLIDWORKS"

        # Intento de detección de codificación
        encodings = ['utf-8', 'latin-1', 'ascii']
        first_lines = []
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc, errors='ignore') as f:
                    first_lines = [f.readline().strip() for _ in range(8)]
                    encoding_info = enc
                    break
            except:
                continue
        else:
            encoding_info = "No detectable"
            first_lines = ["<Error al leer el archivo>"]

        return {
            "file_size_mb": size_mb,
            "file_type": file_type,
            "file_extension": file_ext,
            "magic_bytes": magic_bytes,
            "encoding": encoding_info,
            "first_lines": first_lines,
            "modified_date": modified_date,
            "created_date": created_date,
            "absolute_path": os.path.abspath(filepath),
            "exists": True
        }
    except Exception as e:
        return {
            "error": f"Error en diagnóstico: {str(e)}",
            "exists": True
        }

def get_step_status_description(status):
    """Convierte el código de estado de lectura STEP a descripción legible."""
    status_map = {
        IFSelect_RetDone: "Lectura exitosa",
        IFSelect_RetVoid: "Archivo vacío o sin contenido válido",
        IFSelect_RetError: "Error en la estructura del archivo",
        IFSelect_RetFail: "Fallo en el procesamiento",
        IFSelect_RetStop: "Proceso interrumpido"
    }
    return status_map.get(status, f"Estado desconocido: {status}")

def get_compatibility_suggestions(error_type, filepath):
    """Proporciona sugerencias específicas basadas en el tipo de error."""
    diagnostic = get_file_diagnostic_info(filepath)

    suggestions = {
        "read_error": [
            "Verifica que el archivo no esté corrupto",
            "Asegúrate de que sea un archivo STEP válido (.step o .stp)",
            "Intenta abrir el archivo en SOLIDWORKS o visor CAD para verificar integridad",
            "Reexporta el archivo desde SOLIDWORKS con configuración 'STEP AP214'"
        ],
        "transfer_error": [
            "El archivo puede contener geometría no estándar específica de SOLIDWORKS",
            "Exporta desde SOLIDWORKS con 'Scheme: AP214 IS' para mejor compatibilidad",
            "Desactiva 'Exportar caras de soldadura' en opciones de exportación",
            "Prueba exportar como STEP AP203 si persisten los problemas"
        ],
        "null_shape": [
            "Geometría incompatible con PythonOCC - común en archivos SOLIDWORKS complejos",
            "Posibles causas: superficies de soldadura, geometría paramétrica avanzada",
            "Soluciones: simplificar geometría en SOLIDWORKS antes de exportar",
            "Exportar como 'Ensamblaje como pieza única' para reducir complejidad"
        ],
        "assembly_error": [
            "No se pudo extraer estructura de ensamblaje",
            "SOLIDWORKS puede exportar metadata específica que no sigue estándares",
            "Intenta exportar con 'Incluir todos los componentes' activado",
            "Verifica que el ensamblaje no contenga componentes corruptos"
        ]
    }

    base_suggestions = suggestions.get(error_type, ["Error no clasificado"])

    # Sugerencias basadas en diagnóstico
    if diagnostic.get("file_size_mb", 0) > 50:
        base_suggestions.append("¡Archivo muy grande (>50MB)! Simplifica el ensamblaje en SOLIDWORKS")

    if "SOLIDWORKS" in diagnostic.get("file_type", ""):
        base_suggestions.append("Detectado archivo SOLIDWORKS: Usa configuración de exportación 'STEP AP214 IS'")

    if diagnostic.get("file_extension") not in ['.stp', '.step']:
        base_suggestions.append(f"Extensión inusual: {diagnostic.get('file_extension')} - ¿Es realmente un archivo STEP?")

    return base_suggestions

def extract_step_metadata(filepath):
    """Extrae metadatos específicos de SOLIDWORKS del header STEP."""
    metadata = {
        "solidworks_info": {},
        "general": {}
    }

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(100000)  # Leer solo los primeros 100KB para eficiencia

        # Patrones específicos de SOLIDWORKS
        sw_patterns = {
            "sw_version": r"SOLIDWORKS\s+(\d{4})",
            "sw_partno": r"Part_Number\s*\(\s*'([^']+)",
            "sw_rev": r"Revision_Number\s*\(\s*'([^']+)",
            "sw_author": r"Author\s*\(\s*'([^']+)",
            "sw_created": r"Created\s*\(\s*'([^']+)",
            "sw_modified": r"Modified\s*\(\s*'([^']+)",
            "sw_material": r"Material\s*\(\s*'([^']+)"
        }

        for key, pattern in sw_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                metadata["solidworks_info"][key] = match.group(1)

        # Metadatos generales STEP
        general_patterns = {
            "file_description": r"FILE_DESCRIPTION\s*\(\s*\(\s*'([^']+)",
            "file_name": r"FILE_NAME\s*\(\s*'([^']+)",
            "file_schema": r"FILE_SCHEMA\s*\(\s*\(\s*'([^']+)",
            "timestamp": r"'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})'",
            "units": r"LENGTH_UNIT\s*\(\s*\.\w+\s*,\s*\(*\s*([^\)]+)\s*\)"
        }

        for key, pattern in general_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                metadata["general"][key] = matches[0] if isinstance(matches[0], str) else matches

        # Extraer nombres de componentes
        component_names = re.findall(r"#\d+\s*=\s*PRODUCT\s*\(\s*'([^']+)", content)
        if component_names:
            metadata["components"] = component_names

        # Extraer materiales
        material_names = re.findall(r"MATERIAL\s*\(\s*'([^']+)", content)
        if material_names:
            metadata["materials"] = list(set(material_names))

        # Detectar si es ensamblaje
        if "ASSEMBLY" in content.upper() or "ASM" in metadata.get("general", {}).get("file_name", "").upper():
            metadata["assembly"] = True
            metadata["assembly_components"] = len(component_names) if component_names else 0

    except Exception as e:
        metadata["error"] = f"Error al extraer metadatos: {str(e)}"

    return metadata

def extract_coordinate_bounds(filepath):
    """Extrae los límites de coordenadas con detección de unidades."""
    bounds = {
        'x': {'min': None, 'max': None},
        'y': {'min': None, 'max': None},
        'z': {'min': None, 'max': None},
        'units': 'mm'
    }

    unit_conversion = {
        'meter': 1000,
        'millimeter': 1,
        'inch': 25.4,
        'foot': 304.8
    }

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(200000)  # Limitar lectura para eficiencia

        # Detectar unidades
        unit_match = re.search(r"LENGTH_UNIT\s*\(.*?NAMED_UNIT\(\s*\(\s*SI_UNIT\s*\)\s*\.\s*(\w+)", content)
        if unit_match:
            unit_name = unit_match.group(1).lower()
            bounds['units'] = unit_name
            conversion = unit_conversion.get(unit_name, 1)
        else:
            conversion = 1

        # Buscar puntos cartesianos
        cartesian_points = re.findall(
            r'CARTESIAN_POINT\s*\(\s*\'[^\']*\'\s*,\s*\(\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*\)',
            content
        )

        if cartesian_points:
            # Convertir y escalar coordenadas
            scaled_points = []
            for point in cartesian_points:
                try:
                    scaled_points.append(tuple(float(coord) * conversion for coord in point))
                except:
                    continue

            if scaled_points:
                x_coords = [p[0] for p in scaled_points]
                y_coords = [p[1] for p in scaled_points]
                z_coords = [p[2] for p in scaled_points]

                bounds['x'] = {'min': round(min(x_coords), 3), 'max': round(max(x_coords), 3)}
                bounds['y'] = {'min': round(min(y_coords), 3), 'max': round(max(y_coords), 3)}
                bounds['z'] = {'min': round(min(z_coords), 3), 'max': round(max(z_coords), 3)}

                bounds['approximate_dimensions'] = {
                    'width': round(bounds['x']['max'] - bounds['x']['min'], 3),
                    'height': round(bounds['y']['max'] - bounds['y']['min'], 3),
                    'depth': round(bounds['z']['max'] - bounds['z']['min'], 3)
                }
                bounds['coordinate_points_analyzed'] = len(scaled_points)

    except Exception as e:
        bounds['error'] = str(e)

    return bounds

def analyze_step_structure(filepath):
    """Analiza la estructura del archivo STEP para identificar ensamblajes y componentes."""
    structure = {
        "is_assembly": False,
        "components": [],
        "weldment_features": [],
        "metadata": {}
    }

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(500000)  # Limitar lectura para eficiencia

        # Detectar si es ensamblaje
        assembly_flags = [
            "NEXT_ASSEMBLY_USAGE_OCCURRENCE",
            "PRODUCT_DEFINITION_CONTEXT",
            "APPLICATION_CONTEXT('assembly"
        ]

        if any(flag in content for flag in assembly_flags):
            structure["is_assembly"] = True

        # Extraer componentes
        component_matches = re.findall(
            r"#(\d+)\s*=\s*PRODUCT\s*\(\s*'([^']+)",
            content
        )

        if component_matches:
            for comp_id, comp_name in component_matches:
                structure["components"].append({
                    "id": comp_id,
                    "name": comp_name
                })

        # Detectar características de weldment
        weldment_flags = [
            "WELDMENT_ASSEMBLY",
            "WELD_BEAD",
            "WELD_FILLET",
            "WELD_GROOVE"
        ]

        for flag in weldment_flags:
            if flag in content:
                count = content.count(flag)
                structure["weldment_features"].append({
                    "feature": flag,
                    "count": count
                })

        # Contar entidades relevantes
        entity_counts = {}
        entities = [
            'CARTESIAN_POINT', 'ADVANCED_FACE', 'CLOSED_SHELL',
            'MANIFOLD_SOLID_BREP', 'PRODUCT', 'NEXT_ASSEMBLY_USAGE_OCCURRENCE',
            'WELD_', 'CUT_'
        ]

        for entity in entities:
            count = content.count(entity)
            if count > 0:
                entity_counts[entity] = count

        structure["entity_counts"] = entity_counts

        # Detectar materiales
        material_matches = re.findall(r"MATERIAL\s*\(\s*'([^']+)", content)
        if material_matches:
            structure["materials"] = list(set(material_matches))

    except Exception as e:
        structure["error"] = str(e)

    return structure

def extract_weldment_info(filepath):
    """Extrae información específica de weldment de archivos SOLIDWORKS."""
    weldment_info = {
        "weldment_detected": False,
        "weld_beads": 0,
        "weld_fillets": 0,
        "weld_grooves": 0,
        "members": [],
        "gussets": 0,
        "end_caps": 0
    }

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(1000000)  # Leer hasta 1MB para buscar características

        # Detectar tipos de soldadura
        weldment_info["weld_beads"] = content.count("WELD_BEAD")
        weldment_info["weld_fillets"] = content.count("WELD_FILLET")
        weldment_info["weld_grooves"] = content.count("WELD_GROOVE")

        # Detectar miembros estructurales
        member_matches = re.findall(
            r"STRUCTURAL_PROFILE\s*\(\s*'([^']+)",
            content
        )

        if member_matches:
            weldment_info["members"] = list(set(member_matches))

        # Detectar otras características
        weldment_info["gussets"] = content.count("GUSSET")
        weldment_info["end_caps"] = content.count("END_CAP")
        weldment_info["trim_extend"] = content.count("TRIM_EXTEND")

        # Determinar si es weldment
        if (weldment_info["weld_beads"] > 0 or
            weldment_info["weld_fillets"] > 0 or
            len(weldment_info["members"]) > 0):
            weldment_info["weldment_detected"] = True

    except Exception as e:
        weldment_info["error"] = str(e)

    return weldment_info

def extract_assembly_structure(filepath):
    """Intenta extraer la estructura jerárquica del ensamblaje."""
    assembly_structure = {
        "root_components": [],
        "total_parts": 0,
        "subassemblies": 0,
        "success": False
    }

    if not XCAF_AVAILABLE:
        assembly_structure["error"] = "XCAF no disponible para análisis de ensamblajes"
        return assembly_structure

    try:
        # Configurar aplicación XCAF
        app = XCAFApp_Application.GetApplication().GetObject()
        doc = TDocStd_Document("STEP-Assembly")
        app.NewDocument("MDTV-XCAF", doc)

        # Leer archivo STEP
        reader = STEPCAFControl_Reader()
        reader.SetColorMode(True)
        reader.SetLayerMode(True)
        reader.SetNameMode(True)

        status = reader.ReadFile(filepath)
        if status != IFSelect_RetDone:
            assembly_structure["error"] = f"Error al leer archivo: {get_step_status_description(status)}"
            return assembly_structure

        if not reader.Transfer(doc):
            assembly_structure["error"] = "Error en transferencia de datos"
            return assembly_structure

        # Obtener herramienta de formas
        shape_tool = XCAFDoc_DocumentTool.ShapeTool(doc.Main())
        root_label = shape_tool.GetObject().Label()

        # Recorrer estructura jerárquica
        def traverse_label(label, path=""):
            components = []

            # Obtener subcomponentes
            child_labels = TDF_LabelSequence()
            shape_tool.GetSubShapes(label, child_labels)

            for i in range(1, child_labels.Length() + 1):
                child_label = child_labels.Value(i)
                child_path = f"{path}/{i}"

                # Obtener nombre
                name = TCollection_AsciiString()
                if shape_tool.GetName(child_label, name):
                    comp_name = name.ToString()
                else:
                    comp_name = f"Componente_{child_path.replace('/', '_')}"

                # Determinar tipo
                comp_type = "part"
                if shape_tool.IsAssembly(child_label):
                    comp_type = "assembly"
                    assembly_structure["subassemblies"] += 1
                elif shape_tool.IsReference(child_label):
                    comp_type = "reference"

                # Obtener forma
                shape = shape_tool.GetShape(child_label)
                shape_type = "unknown"
                if not shape.IsNull():
                    if shape.ShapeType() == 1:  # VERTEX
                        shape_type = "vertex"
                    elif shape.ShapeType() == 2:  # EDGE
                        shape_type = "edge"
                    elif shape.ShapeType() == 3:  # WIRE
                        shape_type = "wire"
                    elif shape.ShapeType() == 4:  # FACE
                        shape_type = "face"
                    elif shape.ShapeType() == 5:  # SHELL
                        shape_type = "shell"
                    elif shape.ShapeType() == 6:  # SOLID
                        shape_type = "solid"
                    elif shape.ShapeType() == 7:  # COMPSOLID
                        shape_type = "compsolid"
                    elif shape.ShapeType() == 8:  # COMPOUND
                        shape_type = "compound"

                # Crear componente
                component = {
                    "name": comp_name,
                    "type": comp_type,
                    "shape_type": shape_type,
                    "path": child_path,
                    "children": []
                }

                # Si es ensamblaje, recorrer hijos
                if comp_type == "assembly":
                    component["children"] = traverse_label(child_label, child_path)

                components.append(component)
                assembly_structure["total_parts"] += 1

            return components

        # Recorrer desde raíz
        assembly_structure["root_components"] = traverse_label(root_label)
        assembly_structure["success"] = True

    except Exception as e:
        assembly_structure["error"] = f"Error en análisis de ensamblaje: {str(e)}"

    return assembly_structure

def compute_shape_properties(shape):
    """Calcula propiedades geométricas para una forma dada."""
    props = {
        "bounding_box": {},
        "volume": 0,
        "area": 0,
        "topology": {"faces": 0, "edges": 0, "vertices": 0},
        "center_of_mass": {}
    }

    try:
        # Bounding box
        bbox = Bnd_Box()
        brepbndlib_Add(shape, bbox)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
        props["bounding_box"] = {
            "xmin": round(xmin, 3),
            "ymin": round(ymin, 3),
            "zmin": round(zmin, 3),
            "xmax": round(xmax, 3),
            "ymax": round(ymax, 3),
            "zmax": round(zmax, 3),
            "width": round(xmax - xmin, 3),
            "height": round(ymax - ymin, 3),
            "depth": round(zmax - zmin, 3)
        }

        # Propiedades de volumen
        vp = GProp_GProps()
        brepgprop_VolumeProperties(shape, vp)
        props["volume"] = round(vp.Mass(), 3)

        # Propiedades de superficie
        sp = GProp_GProps()
        brepgprop_SurfaceProperties(shape, sp)
        props["area"] = round(sp.Mass(), 3)

        # Centro de masa
        com = vp.CentreOfMass()
        props["center_of_mass"] = {
            "x": round(com.X(), 3),
            "y": round(com.Y(), 3),
            "z": round(com.Z(), 3)
        }

        # Conteo topológico
        for explorer, key in [
            (TopAbs_FACE, "faces"),
            (TopAbs_EDGE, "edges"),
            (TopAbs_VERTEX, "vertices")
        ]:
            exp = TopExp_Explorer(shape, explorer)
            count = 0
            while exp.More():
                count += 1
                exp.Next()
            props["topology"][key] = count

    except Exception as e:
        props["error"] = f"Error en cálculo: {str(e)}"

    return props

# ======================================================================
# FUNCIÓN PRINCIPAL MEJORADA
# ======================================================================

def analyze_step(filepath):
    """Analiza un archivo STEP con soporte para ensamblajes SOLIDWORKS y weldments."""
    t0 = time.time()
    diagnostic_info = get_file_diagnostic_info(filepath)
    result = {
        "file_info": diagnostic_info,
        "metadata": extract_step_metadata(filepath),
        "weldment_info": extract_weldment_info(filepath),
        "structure_info": analyze_step_structure(filepath),
        "coordinate_bounds": extract_coordinate_bounds(filepath),
        "solidworks_specific": {},
        "status": "success",
        "analysis_time_ms": 0
    }

    # Verificar disponibilidad de PythonOCC
    if not OCC_AVAILABLE:
        result.update({
            "status": "dependency_error",
            "error": "PythonOCC no disponible",
            "suggestions": [
                "Instalar con: conda install -c conda-forge pythonocc-core",
                "Para SOLIDWORKS, asegúrese de usar STEP AP214"
            ],
            "analysis_complete": True  # Tenemos análisis sin geometría
        })
        result["analysis_time_ms"] = int((time.time() - t0) * 1000)
        return result

    # Análisis geométrico principal
    try:
        # Leer archivo STEP
        reader = STEPControl_Reader()
        status = reader.ReadFile(filepath)

        if status != IFSelect_RetDone:
            # PythonOCC no puede leer el archivo - devolver información parcial
            result.update({
                "status": "read_error_with_analysis",
                "error": f"PythonOCC no puede leer archivo: {get_step_status_description(status)}",
                "read_status_code": status,
                "suggestions": get_compatibility_suggestions("read_error", filepath),
                "analysis_complete": True,
                "geometric_analysis": False
            })
            result["analysis_time_ms"] = int((time.time() - t0) * 1000)
            return result

        # Transferir geometría
        nb_roots = reader.TransferRoot()
        if nb_roots == 0:
            # Archivo válido pero geometría no transferible - común en archivos complejos
            result.update({
                "status": "transfer_error_with_analysis",
                "error": f"Archivo STEP válido pero geometría no transferible con PythonOCC (raíces: {nb_roots})",
                "read_status": "success",
                "transfer_roots": nb_roots,
                "suggestions": get_compatibility_suggestions("transfer_error", filepath),
                "analysis_complete": True,
                "geometric_analysis": False,
                "file_validity": "valid_step_file"
            })
            result["analysis_time_ms"] = int((time.time() - t0) * 1000)
            return result

        shape = reader.OneShape()

        if shape is None or shape.IsNull():
            # Forma nula pero información ya extraída
            result.update({
                "status": "null_shape_with_analysis",
                "error": "Geometría incompatible con PythonOCC pero archivo analizado completamente",
                "read_status": "success",
                "transfer_roots": nb_roots,
                "shape_valid": False,
                "suggestions": get_compatibility_suggestions("null_shape", filepath),
                "analysis_complete": True,
                "geometric_analysis": False,
                "file_validity": "valid_step_file"
            })
            result["analysis_time_ms"] = int((time.time() - t0) * 1000)
            return result

        # ¡Éxito completo! Calcular propiedades geométricas
        geometric_props = compute_shape_properties(shape)
        result["geometric_properties"] = geometric_props
        result.update({
            "geometric_analysis": True,
            "shape_valid": True,
            "read_status": "success",
            "transfer_roots": nb_roots
        })

        # Extraer estructura de ensamblaje si está disponible
        if XCAF_AVAILABLE and result.get("structure_info", {}).get("is_assembly", False):
            try:
                assembly_structure = extract_assembly_structure(filepath)
                result["assembly_structure"] = assembly_structure

                if not assembly_structure.get("success", False):
                    result["assembly_warning"] = "Estructura de ensamblaje parcial"
            except Exception as e:
                result["assembly_error"] = f"Error en análisis de ensamblaje: {str(e)}"

        # Información específica de SOLIDWORKS
        if "solidworks" in result["metadata"].get("general", {}).get("file_name", "").lower():
            result["solidworks_specific"] = {
                "export_options": {
                    "suggested": "STEP AP214 IS",
                    "avoid": "STEP AP203"
                },
                "weldment_handling": {
                    "tip": "Exporte weldments como 'Multicuerpo' para mejor compatibilidad",
                    "common_issues": [
                        "Las caras de soldadura pueden causar errores de transferencia",
                        "Los miembros estructurales complejos pueden requerir simplificación"
                    ]
                }
            }

    except Exception as e:
        result.update({
            "status": "processing_error_with_analysis",
            "error": f"Error en procesamiento geométrico: {str(e)}",
            "suggestions": [
                "El archivo puede contener características específicas de SOLIDWORKS",
                "Intente exportar con diferentes opciones de STEP",
                "Simplifique la geometría compleja antes de exportar"
            ],
            "analysis_complete": True,
            "geometric_analysis": False
        })

    # Tiempo total de análisis
    result["analysis_time_ms"] = int((time.time() - t0) * 1000)
    return result

# ======================================================================
# EJECUCIÓN PRINCIPAL
# ======================================================================

def main():
    if len(sys.argv) != 2:
        print(json.dumps({
            "error": "Uso: analyze_step.py <ruta_al_archivo.step>",
            "suggested_usage": "python analyze_step.py 'tu_archivo.step' > resultado.json"
        }))
        sys.exit(1)

    path = sys.argv[1]
    try:
        result = analyze_step(path)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Código de salida basado en resultado
        status = result.get("status", "error")

        # Estados que proporcionan análisis completo y son considerados "exitosos"
        successful_states = [
            "success",
            "read_error_with_analysis",
            "transfer_error_with_analysis",
            "null_shape_with_analysis",
            "processing_error_with_analysis"
        ]

        # Verificar si tenemos análisis completo exitoso
        analysis_complete = result.get("analysis_complete", False)
        has_valuable_data = any([
            result.get("metadata", {}).get("solidworks_info"),
            result.get("coordinate_bounds", {}).get("coordinate_points_analyzed", 0) > 0,
            result.get("structure_info", {}).get("components"),
            result.get("weldment_info", {}).get("weldment_detected", False)
        ])

        # Si tenemos análisis completo con datos valiosos, es un éxito
        if status in successful_states or (analysis_complete and has_valuable_data):
            sys.exit(0)  # Éxito - información valiosa extraída
        elif status == "dependency_error" and not OCC_AVAILABLE:
            sys.exit(2)  # Error real de dependencias
        else:
            sys.exit(1)  # Error real

    except Exception as e:
        error_info = {
            "error": str(e),
            "type": "critical_error",
            "timestamp": datetime.now().isoformat(),
            "message": "Error crítico durante el análisis"
        }
        print(json.dumps(error_info, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
