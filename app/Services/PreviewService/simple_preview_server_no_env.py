#!/usr/bin/env python3
"""
Simple Preview Server - No Environment Verification
Direct execution version for development
"""
print("Starting Simple Preview Server (No Env Check)...")

# System imports
import sys
import os
import base64
import io
import logging
import time
import struct
from datetime import datetime
from pathlib import Path

# Import configuration
try:
    from config import config, Config
    print("Configuration loaded successfully")
except ImportError as e:
    print(f"Failed to import config: {e}")
    print("Please ensure config.py is in the same directory")
    sys.exit(1)

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting server initialization...")

# Essential imports
try:
    from PIL import Image, ImageDraw, ImageFont
    logger.info("PIL imported successfully")
except ImportError as e:
    logger.critical(f"Failed to import PIL: {e}")
    sys.exit(1)

# API imports
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
    logger.info("FastAPI and related imports successful")
except ImportError as e:
    logger.critical(f"Failed to import FastAPI dependencies: {e}")
    sys.exit(1)

# Security imports
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.security import APIKeyHeader
    from typing import Optional
    logger.info("Security imports successful")
except ImportError as e:
    logger.warning(f"Some security imports failed: {e}")

# 3D processing capability flags
STEP_SUPPORT = False
STL_SUPPORT = False
DXF_SUPPORT = False

# Core numerical processing
try:
    import numpy as np
    logger.info("NumPy imported successfully")
except ImportError as e:
    logger.critical(f"Warning: NumPy import failed - This will affect all 3D processing: {e}")
    sys.exit(1)

# STEP file support via PythonOCC
try:
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
    from OCC.Core.TopoDS import TopoDS_Shape
    from OCC.Core.BRep import BRep_Builder
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib_Add
    STEP_SUPPORT = True
    logger.info("OCC.Core imported successfully - STEP files supported")
except ImportError as e:
    logger.warning(f"OCC.Core import failed - STEP files will not be supported: {e}")

# STL file support
try:
    from stl import mesh
    STL_SUPPORT = True
    logger.info("numpy-stl imported successfully - STL files supported")
except ImportError as e:
    logger.warning(f"numpy-stl import failed - STL files will use basic support: {e}")

# DXF file support
try:
    import ezdxf
    DXF_SUPPORT = True
    logger.info("ezdxf imported successfully - DXF files supported")
except ImportError as e:
    logger.warning(f"ezdxf import failed - DXF files will not be supported: {e}")

# Optional visualization support
try:
    import pyvista as pv
    import vtk
    logger.info("PyVista and VTK imported successfully")
except ImportError as e:
    logger.warning(f"PyVista/VTK import failed - Advanced 3D visualization will be limited: {e}")

# Create FastAPI app
app = FastAPI(
    title="Pollux 3D Preview Service",
    description="Generate 2D/3D previews for CAD files",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Request models
class PreviewRequest(BaseModel):
    file_path: str
    preview_type: str = Field(..., pattern="^(2d|3d|both|wireframe)$")
    width: int = Field(default=800, ge=100, le=2000)
    height: int = Field(default=600, ge=100, le=2000)
    format: str = Field(default="png", pattern="^(png|jpg|jpeg)$")

class PreviewResponse(BaseModel):
    success: bool
    message: str
    preview_2d: Optional[str] = None
    preview_3d: Optional[str] = None
    file_info: Optional[dict] = None

def get_file_info(file_path: str) -> dict:
    """Get basic file information"""
    try:
        path = Path(file_path)
        if not path.exists():
            return {"error": "File not found"}
        
        stat = path.stat()
        return {
            "filename": path.name,
            "size": stat.st_size,
            "extension": path.suffix.lower(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

def generate_2d_preview(file_path: str, width: int = 800, height: int = 600) -> str:
    """Generate professional CAD-style 2D technical drawing preview"""
    try:
        path = Path(file_path)
        ext = path.suffix.lower()
        
        # Create image with white background
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts
        try:
            font = ImageFont.truetype("arial.ttf", 12)
            title_font = ImageFont.truetype("arial.ttf", 14)
            dim_font = ImageFont.truetype("arial.ttf", 10)
        except:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            dim_font = ImageFont.load_default()
        
        # Draw title border and title
        draw.rectangle([10, 10, width-10, 50], outline='black', width=2)
        draw.text((20, 20), f"Technical Drawing: {path.name}", fill='black', font=title_font)
        draw.text((20, 35), f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill='gray', font=dim_font)
        
        if ext == '.stl':
            # Try to read STL file and generate professional technical drawing
            try:
                vertices = []
                triangles = []
                
                logger.info(f"Reading STL file: {file_path}")
                
                # Read STL file with improved error handling
                with open(file_path, 'rb') as f:
                    header = f.read(80)
                    
                    # More robust ASCII/Binary detection
                    is_ascii = False
                    try:
                        header_str = header.decode('ascii', errors='ignore').strip()
                        if header_str.startswith('solid') and not header_str.startswith('solid '):
                            # Check if file actually contains ASCII STL data
                            f.seek(0)
                            sample = f.read(1024).decode('ascii', errors='ignore')
                            if 'vertex' in sample and 'facet' in sample:
                                is_ascii = True
                    except:
                        pass
                    
                    if is_ascii:
                        logger.info("Processing as ASCII STL")
                        # ASCII STL with improved parsing
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f_text:
                                content = f_text.read()
                                
                                # Check if content looks valid
                                if content.count('vertex') < 3:
                                    logger.warning("ASCII STL appears corrupted, trying binary format")
                                    raise ValueError("Invalid ASCII STL format")
                                
                                lines = content.split('\n')
                                current_triangle = []
                                
                                for line in lines:
                                    line = line.strip()
                                    if line.startswith('vertex'):
                                        parts = line.split()
                                        if len(parts) >= 4:
                                            try:
                                                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                                                # Validate vertex coordinates
                                                if not (abs(x) < 1e6 and abs(y) < 1e6 and abs(z) < 1e6):
                                                    continue
                                                vertices.append((x, y, z))
                                                current_triangle.append(len(vertices) - 1)
                                                if len(current_triangle) == 3:
                                                    triangles.append(current_triangle)
                                                    current_triangle = []
                                            except (ValueError, IndexError):
                                                continue
                                
                                logger.info(f"ASCII STL: Found {len(vertices)} vertices, {len(triangles)} triangles")
                                
                        except Exception as e:
                            logger.warning(f"ASCII STL parsing failed: {e}, trying binary format")
                            is_ascii = False
                    
                    if not is_ascii:
                        logger.info("Processing as Binary STL")
                        # Binary STL with improved parsing
                        try:
                            f.seek(0)
                            f.read(80)  # Skip header
                            num_triangles_data = f.read(4)
                            
                            if len(num_triangles_data) == 4:
                                num_triangles = struct.unpack('<I', num_triangles_data)[0]
                                logger.info(f"Binary STL: Expected {num_triangles} triangles")
                                
                                # Validate triangle count
                                if num_triangles > 1000000:  # Sanity check
                                    logger.warning(f"Suspicious triangle count: {num_triangles}")
                                    raise ValueError("Invalid triangle count")
                                
                                for i in range(num_triangles):
                                    try:
                                        # Read normal vector (skip)
                                        normal_data = f.read(12)
                                        if len(normal_data) != 12:
                                            break
                                        
                                        triangle_indices = []
                                        for j in range(3):  # 3 vertices per triangle
                                            vertex_data = f.read(12)
                                            if len(vertex_data) == 12:
                                                x, y, z = struct.unpack('<fff', vertex_data)
                                                # Validate vertex coordinates
                                                if not (abs(x) < 1e6 and abs(y) < 1e6 and abs(z) < 1e6):
                                                    continue
                                                vertices.append((x, y, z))
                                                triangle_indices.append(len(vertices) - 1)
                                        
                                        if len(triangle_indices) == 3:
                                            triangles.append(triangle_indices)
                                        
                                        # Read attribute byte count
                                        attr_data = f.read(2)
                                        if len(attr_data) != 2:
                                            break
                                            
                                    except struct.error:
                                        break
                                
                                logger.info(f"Binary STL: Found {len(vertices)} vertices, {len(triangles)} triangles")
                            else:
                                logger.error("Invalid binary STL header")
                                
                        except Exception as e:
                            logger.error(f"Binary STL parsing failed: {e}")
                
                # Check if we successfully read vertices
                if len(vertices) > 0:
                    logger.info(f"Successfully read {len(vertices)} vertices")
                    
                    # Remove duplicate vertices for better visualization
                    unique_vertices = []
                    vertex_map = {}
                    for i, vertex in enumerate(vertices):
                        rounded = tuple(round(coord, 6) for coord in vertex)
                        if rounded not in vertex_map:
                            vertex_map[rounded] = len(unique_vertices)
                            unique_vertices.append(vertex)
                    
                    logger.info(f"Reduced to {len(unique_vertices)} unique vertices")
                    
                    # Calculate bounds
                    min_x = min(v[0] for v in unique_vertices)
                    max_x = max(v[0] for v in unique_vertices)
                    min_y = min(v[1] for v in unique_vertices)
                    max_y = max(v[1] for v in unique_vertices)
                    min_z = min(v[2] for v in unique_vertices)
                    max_z = max(v[2] for v in unique_vertices)
                    
                    logger.info(f"Bounds: X[{min_x:.2f}, {max_x:.2f}] Y[{min_y:.2f}, {max_y:.2f}] Z[{min_z:.2f}, {max_z:.2f}]")
                    
                    # Generate professional technical drawing
                    draw_technical_drawing(draw, unique_vertices, triangles, min_x, max_x, min_y, max_y, min_z, max_z, 
                                         width, height, font, dim_font)
                    
                else:
                    logger.warning("No vertices found in STL file")
                    # Enhanced fallback message
                    draw.text((50, 100), "STL file appears corrupted or invalid", fill='red', font=font)
                    draw.text((50, 120), f"File size: {os.path.getsize(file_path):,} bytes", fill='black', font=font)
                    draw.text((50, 140), "Using fallback representation", fill='gray', font=font)
                    draw_basic_3d_shape(draw, width, height)
                    
            except Exception as e:
                logger.warning(f"Error reading STL file: {e}")
                # Fallback to basic representation
                draw.text((50, 100), f"STL parsing failed: {str(e)[:50]}...", fill='red', font=font)
                draw_basic_3d_shape(draw, width, height)
        else:
            # Non-STL files
            draw.text((50, 100), f"File type: {ext}", fill='black', font=font)
            draw_basic_3d_shape(draw, width, height)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        logger.error(f"Error generating 2D preview: {e}")
        return None
        
        if ext == '.stl':
            # Try to read STL file and generate 2D projection
            try:
                vertices = []
                # First, try to determine if it's ASCII or binary STL
                with open(file_path, 'rb') as f:
                    header = f.read(80)
                    try:
                        # Check if it starts with 'solid' (ASCII STL)
                        if header.decode('ascii', errors='ignore').strip().startswith('solid'):
                            # ASCII STL
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                lines = content.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    if line.startswith('vertex'):
                                        parts = line.split()
                                        if len(parts) >= 4:
                                            try:
                                                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                                                vertices.append((x, y, z))
                                            except ValueError:
                                                continue
                        else:
                            # Binary STL
                            f.seek(0)
                            f.read(80)  # Skip header
                            num_triangles_data = f.read(4)
                            if len(num_triangles_data) == 4:
                                num_triangles = struct.unpack('<I', num_triangles_data)[0]
                                for _ in range(num_triangles):
                                    f.read(12)  # Skip normal vector
                                    for _ in range(3):  # 3 vertices per triangle
                                        vertex_data = f.read(12)
                                        if len(vertex_data) == 12:
                                            x, y, z = struct.unpack('<fff', vertex_data)
                                            vertices.append((x, y, z))
                                    f.read(2)  # Skip attribute byte count
                    except UnicodeDecodeError:
                        # Definitely binary STL
                        f.seek(0)
                        f.read(80)  # Skip header
                        num_triangles_data = f.read(4)
                        if len(num_triangles_data) == 4:
                            num_triangles = struct.unpack('<I', num_triangles_data)[0]
                            for _ in range(num_triangles):
                                f.read(12)  # Skip normal vector
                                for _ in range(3):  # 3 vertices per triangle
                                    vertex_data = f.read(12)
                                    if len(vertex_data) == 12:
                                        x, y, z = struct.unpack('<fff', vertex_data)
                                        vertices.append((x, y, z))
                                f.read(2)  # Skip attribute byte count
                
                if vertices:
                    # Calculate bounds
                    min_x = min(v[0] for v in vertices)
                    max_x = max(v[0] for v in vertices)
                    min_y = min(v[1] for v in vertices)
                    max_y = max(v[1] for v in vertices)
                    min_z = min(v[2] for v in vertices)
                    max_z = max(v[2] for v in vertices)
                    
                    # Draw multiple orthographic projections
                    margin = 60
                    proj_width = (width - 4 * margin) // 3
                    proj_height = height - 150
                    
                    # Front view (X-Z projection)
                    draw.text((margin, margin), "Front View (X-Z)", fill='black', font=font)
                    project_and_draw_points(draw, vertices, 0, 2, margin, margin + 30, proj_width, proj_height - 30, 
                                          min_x, max_x, min_z, max_z, 'blue')
                    
                    # Side view (Y-Z projection)  
                    draw.text((margin + proj_width + margin, margin), "Side View (Y-Z)", fill='black', font=font)
                    project_and_draw_points(draw, vertices, 1, 2, margin + proj_width + margin, margin + 30, 
                                          proj_width, proj_height - 30, min_y, max_y, min_z, max_z, 'red')
                    
                    # Top view (X-Y projection)
                    draw.text((margin + 2 * (proj_width + margin), margin), "Top View (X-Y)", fill='black', font=font)
                    project_and_draw_points(draw, vertices, 0, 1, margin + 2 * (proj_width + margin), margin + 30, 
                                          proj_width, proj_height - 30, min_x, max_x, min_y, max_y, 'green')
                    
                    # Draw dimensions info
                    dims_text = f"Dimensions: {max_x-min_x:.2f} x {max_y-min_y:.2f} x {max_z-min_z:.2f}"
                    draw.text((20, height - 40), dims_text, fill='black', font=font)
                    draw.text((20, height - 20), f"Vertices: {len(vertices)}", fill='black', font=font)
                    
                else:
                    # Fallback to basic representation
                    draw.text((50, 100), "Could not read STL vertices", fill='red', font=font)
                    draw_basic_3d_shape(draw, width, height)
                    
            except Exception as e:
                logger.warning(f"Error reading STL file: {e}")
                # Fallback to basic representation
                draw.text((50, 100), f"STL parsing failed: {str(e)[:50]}...", fill='red', font=font)
                draw_basic_3d_shape(draw, width, height)
        else:
            # Non-STL files
            draw.text((50, 100), f"File type: {ext}", fill='black', font=font)
            draw_basic_3d_shape(draw, width, height)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        logger.error(f"Error generating 2D preview: {e}")
        return None

def draw_technical_drawing(draw, vertices, triangles, min_x, max_x, min_y, max_y, min_z, max_z, 
                          width, height, font, dim_font):
    """Draw professional CAD-style technical drawing with multiple orthographic views"""
    
    # Layout parameters
    margin = 40
    top_margin = 70
    bottom_margin = 80
    spacing = 20
    
    # Calculate available space for views
    available_width = width - 2 * margin
    available_height = height - top_margin - bottom_margin
    
    # Layout: Front view (left), Side view (center), Top view (right)
    view_width = (available_width - 2 * spacing) // 3
    view_height = available_height - 60  # Leave space for labels
    
    # Position for each view
    front_x = margin
    side_x = margin + view_width + spacing
    top_x = margin + 2 * (view_width + spacing)
    view_y = top_margin + 30
    
    # Draw view frames with professional styling
    draw_view_frame(draw, front_x, view_y, view_width, view_height, "FRONT VIEW", font)
    draw_view_frame(draw, side_x, view_y, view_width, view_height, "SIDE VIEW", font)
    draw_view_frame(draw, top_x, view_y, view_width, view_height, "TOP VIEW", font)
    
    # Draw orthographic projections
    draw_orthographic_projection(draw, vertices, triangles, 0, 2, front_x, view_y, view_width, view_height, 
                                min_x, max_x, min_z, max_z, 'blue')
    draw_orthographic_projection(draw, vertices, triangles, 1, 2, side_x, view_y, view_width, view_height, 
                                min_y, max_y, min_z, max_z, 'red')
    draw_orthographic_projection(draw, vertices, triangles, 0, 1, top_x, view_y, view_width, view_height, 
                                min_x, max_x, min_y, max_y, 'green')
    
    # Draw dimensions and technical information
    draw_technical_dimensions(draw, min_x, max_x, min_y, max_y, min_z, max_z, 
                             front_x, side_x, top_x, view_y, view_width, view_height, dim_font)
    
    # Draw title block (bottom right)
    draw_title_block(draw, width, height, min_x, max_x, min_y, max_y, min_z, max_z, 
                    len(vertices), len(triangles), font, dim_font)

def draw_view_frame(draw, x, y, width, height, title, font):
    """Draw professional view frame with title"""
    # Main frame
    draw.rectangle([x, y, x + width, y + height], outline='black', width=2)
    
    # Title background
    title_height = 25
    draw.rectangle([x, y - title_height, x + width, y], fill='lightgray', outline='black', width=1)
    
    # Title text
    text_bbox = draw.textbbox((0, 0), title, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    title_x = x + (width - text_width) // 2
    draw.text((title_x, y - title_height + 5), title, fill='black', font=font)
    
    # Grid lines for professional look
    grid_spacing = 20
    for i in range(grid_spacing, width, grid_spacing):
        draw.line([x + i, y, x + i, y + height], fill='lightgray', width=1)
    for i in range(grid_spacing, height, grid_spacing):
        draw.line([x, y + i, x + width, y + i], fill='lightgray', width=1)

def draw_orthographic_projection(draw, vertices, triangles, axis1, axis2, x_offset, y_offset, 
                               width, height, min_val1, max_val1, min_val2, max_val2, color):
    """Draw orthographic projection with wireframe edges"""
    if max_val1 == min_val1 or max_val2 == min_val2:
        return
        
    # Add padding
    padding = 0.1
    range1 = max_val1 - min_val1
    range2 = max_val2 - min_val2
    min_val1 -= range1 * padding
    max_val1 += range1 * padding
    min_val2 -= range2 * padding
    max_val2 += range2 * padding
    
    # Draw visible edges
    edges_drawn = set()
    
    for triangle in triangles:
        if len(triangle) == 3:
            # Draw triangle edges
            for i in range(3):
                v1_idx = triangle[i]
                v2_idx = triangle[(i + 1) % 3]
                
                if v1_idx < len(vertices) and v2_idx < len(vertices):
                    # Create edge key (sorted to avoid duplicates)
                    edge_key = tuple(sorted([v1_idx, v2_idx]))
                    
                    if edge_key not in edges_drawn:
                        edges_drawn.add(edge_key)
                        
                        v1 = vertices[v1_idx]
                        v2 = vertices[v2_idx]
                        
                        # Project vertices to 2D
                        x1 = int(x_offset + (v1[axis1] - min_val1) / (max_val1 - min_val1) * width)
                        y1 = int(y_offset + height - (v1[axis2] - min_val2) / (max_val2 - min_val2) * height)
                        x2 = int(x_offset + (v2[axis1] - min_val1) / (max_val1 - min_val1) * width)
                        y2 = int(y_offset + height - (v2[axis2] - min_val2) / (max_val2 - min_val2) * height)
                        
                        # Draw edge
                        if (x_offset <= x1 <= x_offset + width and y_offset <= y1 <= y_offset + height and
                            x_offset <= x2 <= x_offset + width and y_offset <= y2 <= y_offset + height):
                            draw.line([x1, y1, x2, y2], fill=color, width=1)

def draw_technical_dimensions(draw, min_x, max_x, min_y, max_y, min_z, max_z, 
                            front_x, side_x, top_x, view_y, view_width, view_height, font):
    """Draw dimension lines and measurements"""
    
    # Calculate dimensions
    dim_x = max_x - min_x
    dim_y = max_y - min_y
    dim_z = max_z - min_z
    
    # Front view dimensions (X and Z)
    draw_dimension_line(draw, front_x, view_y + view_height + 10, 
                       front_x + view_width, view_y + view_height + 10, 
                       f"{dim_x:.2f}", font)
    draw_dimension_line(draw, front_x - 30, view_y, 
                       front_x - 30, view_y + view_height, 
                       f"{dim_z:.2f}", font, vertical=True)
    
    # Side view dimensions (Y and Z)
    draw_dimension_line(draw, side_x, view_y + view_height + 10, 
                       side_x + view_width, view_y + view_height + 10, 
                       f"{dim_y:.2f}", font)
    
    # Top view dimensions (X and Y)
    draw_dimension_line(draw, top_x, view_y + view_height + 10, 
                       top_x + view_width, view_y + view_height + 10, 
                       f"{dim_x:.2f}", font)
    draw_dimension_line(draw, top_x - 30, view_y, 
                       top_x - 30, view_y + view_height, 
                       f"{dim_y:.2f}", font, vertical=True)

def draw_dimension_line(draw, x1, y1, x2, y2, text, font, vertical=False):
    """Draw a professional dimension line with arrows and text"""
    # Main dimension line
    draw.line([x1, y1, x2, y2], fill='black', width=1)
    
    # Arrow heads
    arrow_size = 5
    if vertical:
        # Vertical arrows
        draw.polygon([x1, y1, x1-arrow_size, y1+arrow_size, x1+arrow_size, y1+arrow_size], fill='black')
        draw.polygon([x2, y2, x2-arrow_size, y2-arrow_size, x2+arrow_size, y2-arrow_size], fill='black')
        
        # Text (rotated effect by positioning)
        text_x = x1 - 25
        text_y = (y1 + y2) // 2 - 10
    else:
        # Horizontal arrows
        draw.polygon([x1, y1, x1+arrow_size, y1-arrow_size, x1+arrow_size, y1+arrow_size], fill='black')
        draw.polygon([x2, y2, x2-arrow_size, y2-arrow_size, x2-arrow_size, y2+arrow_size], fill='black')
        
        # Text
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (x1 + x2 - text_width) // 2
        text_y = y1 - 20
    
    # Draw text with background
    text_bbox = draw.textbbox((text_x, text_y), text, font=font)
    draw.rectangle([text_bbox[0]-2, text_bbox[1]-1, text_bbox[2]+2, text_bbox[3]+1], 
                  fill='white', outline='black', width=1)
    draw.text((text_x, text_y), text, fill='black', font=font)

def draw_title_block(draw, width, height, min_x, max_x, min_y, max_y, min_z, max_z, 
                    vertex_count, triangle_count, font, dim_font):
    """Draw professional title block"""
    block_width = 300
    block_height = 120
    block_x = width - block_width - 20
    block_y = height - block_height - 20
    
    # Main title block frame
    draw.rectangle([block_x, block_y, block_x + block_width, block_y + block_height], 
                  outline='black', width=2)
    
    # Header
    draw.rectangle([block_x, block_y, block_x + block_width, block_y + 25], 
                  fill='lightgray', outline='black', width=1)
    draw.text((block_x + 10, block_y + 5), "TECHNICAL SPECIFICATIONS", fill='black', font=font)
    
    # Content
    y_pos = block_y + 35
    line_height = 15
    
    specs = [
        f"Dimensions: {max_x-min_x:.2f} × {max_y-min_y:.2f} × {max_z-min_z:.2f}",
        f"Volume: {((max_x-min_x) * (max_y-min_y) * (max_z-min_z)):.2f} cubic units",
        f"Vertices: {vertex_count:,}",
        f"Triangles: {triangle_count:,}",
        f"Scale: 1:1",
        f"Date: {datetime.now().strftime('%Y-%m-%d')}"
    ]
    
    for spec in specs:
        draw.text((block_x + 10, y_pos), spec, fill='black', font=dim_font)
        y_pos += line_height

def project_and_draw_points(draw, vertices, axis1, axis2, x_offset, y_offset, width, height, 
                           min_val1, max_val1, min_val2, max_val2, color):
    """Legacy function - kept for compatibility"""
    if max_val1 == min_val1 or max_val2 == min_val2:
        return
        
    # Add padding
    padding = 0.1
    range1 = max_val1 - min_val1
    range2 = max_val2 - min_val2
    min_val1 -= range1 * padding
    max_val1 += range1 * padding
    min_val2 -= range2 * padding
    max_val2 += range2 * padding
    
    # Draw border
    draw.rectangle([x_offset, y_offset, x_offset + width, y_offset + height], outline='gray', width=1)
    
    # Sample vertices to avoid overcrowding
    step = max(1, len(vertices) // 2000)  # Limit to ~2000 points
    sampled_vertices = vertices[::step]
    
    # Project and draw points
    for vertex in sampled_vertices:
        val1 = vertex[axis1]
        val2 = vertex[axis2]
        
        # Map to screen coordinates
        x = int(x_offset + (val1 - min_val1) / (max_val1 - min_val1) * width)
        y = int(y_offset + height - (val2 - min_val2) / (max_val2 - min_val2) * height)
        
        # Draw point
        if 0 <= x - x_offset <= width and 0 <= y - y_offset <= height:
            draw.ellipse([x-1, y-1, x+1, y+1], fill=color)

def draw_basic_3d_shape(draw, width, height):
    """Draw a basic 3D shape as fallback"""
    # Draw a simple 3D-like shape representation
    draw.rectangle([100, 150, 300, 350], outline='blue', width=2)
    draw.rectangle([120, 130, 320, 330], outline='lightblue', width=2)
    draw.line([100, 150, 120, 130], fill='gray', width=1)
    draw.line([300, 150, 320, 130], fill='gray', width=1)
    draw.line([300, 350, 320, 330], fill='gray', width=1)
    draw.line([100, 350, 120, 330], fill='gray', width=1)

def generate_wireframe_preview(file_path: str, width: int = 800, height: int = 600) -> str:
    """Generate wireframe preview of the file"""
    try:
        # Create a wireframe-style preview
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw title
        title = Path(file_path).stem
        draw.text((20, 20), f"Wireframe Preview: {title}", fill='black')
        
        # Draw a wireframe-style representation
        # Draw multiple connected lines to simulate wireframe
        center_x, center_y = width // 2, height // 2
        
        # Draw a wireframe cube
        size = min(width, height) // 4
        
        # Front face
        draw.rectangle([center_x - size, center_y - size, center_x + size, center_y + size], outline='blue', width=2)
        
        # Back face (offset)
        offset = size // 3
        draw.rectangle([center_x - size + offset, center_y - size - offset, center_x + size + offset, center_y + size - offset], outline='lightblue', width=2)
        
        # Connect corners to create wireframe effect
        draw.line([center_x - size, center_y - size, center_x - size + offset, center_y - size - offset], fill='gray', width=1)
        draw.line([center_x + size, center_y - size, center_x + size + offset, center_y - size - offset], fill='gray', width=1)
        draw.line([center_x + size, center_y + size, center_x + size + offset, center_y + size - offset], fill='gray', width=1)
        draw.line([center_x - size, center_y + size, center_x - size + offset, center_y + size - offset], fill='gray', width=1)
        
        # Add some grid lines to enhance wireframe look
        for i in range(5):
            y = center_y - size + (i * size // 2)
            draw.line([center_x - size, y, center_x + size, y], fill='lightgray', width=1)
            draw.line([center_x - size + offset, y - offset, center_x + size + offset, y - offset], fill='lightgray', width=1)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        logger.error(f"Error generating wireframe preview: {e}")
        return None

def generate_3d_preview(file_path: str, width: int = 800, height: int = 600) -> str:
    """Generate 3D preview of the file"""
    try:
        # For now, return the same as 2D preview
        # TODO: Implement actual 3D rendering
        return generate_2d_preview(file_path, width, height)
    except Exception as e:
        logger.error(f"Error generating 3D preview: {e}")
        return None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Pollux 3D Preview Service",
        "version": "1.0.0",
        "status": "running",
        "capabilities": {
            "stl_support": STL_SUPPORT,
            "step_support": STEP_SUPPORT,
            "dxf_support": DXF_SUPPORT
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/generate-preview")
@limiter.limit("10/minute")
async def generate_preview(request: Request, preview_request: PreviewRequest):
    """Generate preview for a file"""
    try:
        file_path = preview_request.file_path
        logger.info(f"Generating preview for: {file_path}")
        
        # Validate file exists
        if not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file info
        file_info = get_file_info(file_path)
        
        # Generate previews based on request
        preview_2d = None
        preview_3d = None
        
        if preview_request.preview_type in ["2d", "both"]:
            preview_2d = generate_2d_preview(
                file_path, 
                preview_request.width, 
                preview_request.height
            )
        
        if preview_request.preview_type in ["3d", "both"]:
            preview_3d = generate_3d_preview(
                file_path, 
                preview_request.width, 
                preview_request.height
            )
            
        # Wireframe is handled as a variant of 2d preview
        if preview_request.preview_type == "wireframe":
            preview_2d = generate_wireframe_preview(
                file_path, 
                preview_request.width, 
                preview_request.height
            )
        
        return PreviewResponse(
            success=True,
            message="Preview generated successfully",
            preview_2d=preview_2d,
            preview_3d=preview_3d,
            file_info=file_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print(f"Starting server on {config.HOST}:{config.PORT}")
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
