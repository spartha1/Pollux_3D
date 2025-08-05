#!/usr/bin/env python3
import sys
import json
import time
import os
import ezdxf
from ezdxf.tools.standards import linetypes

def debug(msg):
    """Print debug messages to stderr"""
    print(msg, file=sys.stderr, flush=True)

def calculate_manufacturing_metrics_2d(area_cm2, perimeter_mm, entity_counts):
    """Calculate manufacturing metrics for 2D CAD files (cutting, engraving, etc.)"""
    debug("Calculating 2D manufacturing metrics...")
    
    # Material properties for 2D cutting/engraving (thickness assumed 3mm)
    thickness_mm = 3.0  # Standard sheet thickness
    volume_cm3 = (area_cm2 * thickness_mm) / 10.0  # Convert mm to cm
    
    # Material properties (density in g/cm³, cost per m² for sheets)
    materials = {
        'aluminum_sheet': {'density': 2.7, 'cost_per_m2': 25.0, 'name': 'Lámina de Aluminio', 'type': 'metal', 'thickness_mm': 3.0},
        'steel_sheet': {'density': 7.85, 'cost_per_m2': 15.0, 'name': 'Lámina de Acero', 'type': 'metal', 'thickness_mm': 3.0},
        'stainless_sheet': {'density': 8.0, 'cost_per_m2': 45.0, 'name': 'Lámina de Acero Inoxidable', 'type': 'metal', 'thickness_mm': 3.0},
        'copper_sheet': {'density': 8.96, 'cost_per_m2': 85.0, 'name': 'Lámina de Cobre', 'type': 'metal', 'thickness_mm': 3.0},
        'acrylic_sheet': {'density': 1.18, 'cost_per_m2': 35.0, 'name': 'Acrílico', 'type': 'plastic', 'thickness_mm': 3.0},
        'wood_sheet': {'density': 0.6, 'cost_per_m2': 12.0, 'name': 'Madera Contrachapada', 'type': 'wood', 'thickness_mm': 3.0},
        'cardboard': {'density': 0.7, 'cost_per_m2': 2.0, 'name': 'Cartón', 'type': 'paper', 'thickness_mm': 3.0},
        'foam_core': {'density': 0.3, 'cost_per_m2': 8.0, 'name': 'Foam Core', 'type': 'foam', 'thickness_mm': 5.0},
        'vinyl': {'density': 1.3, 'cost_per_m2': 15.0, 'name': 'Vinilo', 'type': 'plastic', 'thickness_mm': 0.1},
        'fabric': {'density': 0.8, 'cost_per_m2': 20.0, 'name': 'Tela', 'type': 'textile', 'thickness_mm': 1.0},
        'leather': {'density': 0.9, 'cost_per_m2': 80.0, 'name': 'Cuero', 'type': 'leather', 'thickness_mm': 2.0}
    }
    
    weight_estimates = {}
    area_m2 = area_cm2 / 10000.0  # Convert cm² to m²
    
    for material_id, props in materials.items():
        # Calculate volume with material-specific thickness
        material_volume_cm3 = (area_cm2 * props['thickness_mm']) / 10.0
        
        # Calculate weight in grams and kg
        weight_grams = material_volume_cm3 * props['density']
        weight_kg = weight_grams / 1000.0
        
        # Calculate estimated cost based on area
        estimated_cost = area_m2 * props['cost_per_m2']
        
        weight_estimates[material_id] = {
            'name': props['name'],
            'type': props['type'],
            'weight_grams': round(weight_grams, 2),
            'weight_kg': round(weight_kg, 4),
            'density': props['density'],
            'thickness_mm': props['thickness_mm'],
            'estimated_cost_usd': round(estimated_cost, 2),
            'cost_per_m2': props['cost_per_m2']
        }
    
    # Calculate cutting complexity based on entities
    line_entities = entity_counts.get('LINE', 0) + entity_counts.get('POLYLINE', 0) + entity_counts.get('LWPOLYLINE', 0)
    curve_entities = entity_counts.get('CIRCLE', 0) + entity_counts.get('ARC', 0) + entity_counts.get('ELLIPSE', 0)
    total_cut_entities = line_entities + curve_entities
    
    # Estimate cutting time and complexity
    if total_cut_entities < 10:
        cutting_complexity = "Simple"
        estimated_cutting_time_min = 5
    elif total_cut_entities < 50:
        cutting_complexity = "Moderada"
        estimated_cutting_time_min = 15
    else:
        cutting_complexity = "Compleja"
        estimated_cutting_time_min = 30
    
    manufacturing_data = {
        'cutting_method': 'laser_cutting',  # Assumed for DXF/DWG
        'cutting_perimeter_mm': round(perimeter_mm, 2),
        'cutting_area_cm2': round(area_cm2, 2),
        'estimated_cutting_time_min': estimated_cutting_time_min,
        'cutting_complexity': cutting_complexity,
        'line_entities': line_entities,
        'curve_entities': curve_entities,
        'total_entities': sum(entity_counts.values()),
        'fabrication_method': {
            'primary': 'laser_cutting',
            'secondary': 'cnc_routing',
            'finishing': 'edge_smoothing'
        },
        'material_efficiency': round(min(95.0, 90.0 - (total_cut_entities * 0.5)), 2),
        'weight_estimates': weight_estimates
    }
    
    debug(f"Generated 2D manufacturing data for {len(weight_estimates)} materials")
    return manufacturing_data

def calculate_perimeter(msp):
    """Calculate approximate perimeter from DXF entities"""
    total_perimeter = 0.0
    
    for entity in msp:
        entity_type = entity.dxftype()
        
        try:
            if entity_type == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                length = ((end.x - start.x)**2 + (end.y - start.y)**2 + (end.z - start.z)**2)**0.5
                total_perimeter += length
                
            elif entity_type == 'CIRCLE':
                radius = entity.dxf.radius
                circumference = 2 * 3.14159 * radius
                total_perimeter += circumference
                
            elif entity_type == 'ARC':
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                if end_angle < start_angle:
                    end_angle += 360
                arc_angle = end_angle - start_angle
                arc_length = (arc_angle / 360.0) * 2 * 3.14159 * radius
                total_perimeter += arc_length
                
            elif entity_type in ['POLYLINE', 'LWPOLYLINE']:
                # For polylines, approximate by summing vertex distances
                if hasattr(entity, 'vertices'):
                    vertices = list(entity.vertices)
                    for i in range(len(vertices) - 1):
                        v1 = vertices[i]
                        v2 = vertices[i + 1]
                        length = ((v2.dxf.location.x - v1.dxf.location.x)**2 + 
                                (v2.dxf.location.y - v1.dxf.location.y)**2)**0.5
                        total_perimeter += length
                        
        except Exception as e:
            debug(f"Error calculating perimeter for {entity_type}: {e}")
            continue
    
    return total_perimeter

def analyze_dxf_complete(filepath):
    """Complete analysis of DXF/DWG files with manufacturing data"""
    debug(f"Analyzing file: {filepath}")
    start_time = time.time()

    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        debug("Loading DXF file...")
        doc = ezdxf.readfile(filepath)
        debug("DXF file loaded successfully")

        msp = doc.modelspace()
        debug("Accessing modelspace...")

        # Get bounding box
        ext = msp.bbox()
        if ext and ext.has_data:
            dimensions = {
                "width": ext.size.x,
                "height": ext.size.y,
                "depth": ext.size.z if hasattr(ext.size, 'z') else 0
            }
            # Calculate area (assuming 2D)
            area_cm2 = (ext.size.x / 10.0) * (ext.size.y / 10.0)  # Convert mm to cm
            debug(f"Calculated dimensions: {dimensions}")
        else:
            dimensions = {"width": 0, "height": 0, "depth": 0}
            area_cm2 = 0
            debug("No bounding box data available")

        # Count entities by type
        entity_counts = {}
        total_entities = 0
        for entity in msp:
            dxftype = entity.dxftype()
            entity_counts[dxftype] = entity_counts.get(dxftype, 0) + 1
            total_entities += 1

        debug(f"Found {total_entities} total entities")

        # Calculate perimeter
        perimeter_mm = calculate_perimeter(msp)
        debug(f"Calculated perimeter: {perimeter_mm} mm")

        # Calculate manufacturing metrics
        manufacturing_data = calculate_manufacturing_metrics_2d(area_cm2, perimeter_mm, entity_counts)

        # Get file info
        file_size = os.path.getsize(filepath)

        # Collect metadata
        metadata = {
            "dxf_version": doc.dxfversion,
            "encoding": doc.encoding,
            "layers": len(doc.layers),
            "linetypes": len(doc.linetypes),
            "blocks": len(doc.blocks),
            "entities": total_entities,
            "entity_types": entity_counts,
            "file_size_kb": round(file_size / 1024, 2),
            "perimeter_mm": round(perimeter_mm, 2)
        }

        # Calculate analysis time
        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "dimensions": dimensions,
            "volume": None,  # Not applicable for 2D DXF
            "area": round(area_cm2, 2),
            "manufacturing": manufacturing_data,
            "metadata": metadata,
            "analysis_time_ms": elapsed_ms
        }

    except ezdxf.DXFError as e:
        debug(f"DXF parsing error: {str(e)}")
        raise
    except Exception as e:
        debug(f"Unexpected error: {str(e)}")
        raise

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: analyze_dxf_dwg_complete.py <filepath>"}))
        sys.exit(1)

    try:
        result = analyze_dxf_complete(sys.argv[1])
        print(json.dumps(result))
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
