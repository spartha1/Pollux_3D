#!/usr/bin/env python3
"""
Preview Server Híbrido - Usa matplotlib para 2D y numpy-stl para STL
Evita problemas de VTK en Windows mientras mantiene funcionalidad completa
"""

import sys
import os
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import uuid

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("Starting Hybrid Preview Server (matplotlib + numpy-stl)...")

# Importar configuración de rutas
from path_config import config

# Verificar y crear directorios necesarios
print(f"Project root: {config.BASE_PATH}")
config.ensure_directories()

# Importar dependencias básicas
try:
    logger.info("Starting server initialization...")
    
    from PIL import Image, ImageDraw, ImageFont
    logger.info("PIL imported successfully")
    
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    logger.info("FastAPI and related imports successful")
    
    import numpy as np
    logger.info("NumPy imported successfully")
    
    # Matplotlib para 2D
    import matplotlib
    matplotlib.use('Agg')  # Backend sin GUI para Windows
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    logger.info("Matplotlib imported successfully - 2D/3D visualization supported")
    
    # numpy-stl para STL
    from stl import mesh
    logger.info("numpy-stl imported successfully - STL files supported")
    
    # PythonOCC para STEP
    try:
        from OCC.Core.STEPControl import STEPControl_Reader
        from OCC.Core.IFSelect import IFSelect_RetDone
        from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
        from OCC.Core.TopoDS import TopoDS_Shape
        from OCC.Core.BRep import BRep_Builder
        from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec
        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib_Add
        logger.info("PythonOCC imported successfully - STEP files supported")
        HAS_PYTHONOCC = True
    except ImportError as e:
        logger.warning(f"PythonOCC import failed - STEP files will not be supported: {e}")
        HAS_PYTHONOCC = False
    
    # PyVista (opcional, solo para funciones avanzadas)
    try:
        import pyvista as pv
        # Configurar para Windows
        pv.set_plot_theme("document")
        pv.global_theme.notebook = False
        logger.info("PyVista imported successfully - Advanced 3D features available")
        HAS_PYVISTA = True
    except ImportError as e:
        logger.warning(f"PyVista import failed - Using matplotlib fallback: {e}")
        HAS_PYVISTA = False
    
    # DXF support via ezdxf
    try:
        import ezdxf
        logger.info("ezdxf imported successfully - DXF files supported")
        HAS_DXF = True
    except ImportError as e:
        logger.warning(f"ezdxf import failed - DXF files will not be supported: {e}")
        HAS_DXF = False
    
    # EPS support via subprocess + ghostscript
    try:
        import subprocess
        # Verificar si ghostscript está disponible
        subprocess.run(['gs', '--version'], capture_output=True, check=True)
        logger.info("Ghostscript found - EPS files supported")
        HAS_EPS = True
    except (ImportError, subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning(f"Ghostscript not available - EPS files will not be supported: {e}")
        HAS_EPS = False
        
except ImportError as e:
    logger.error(f"Critical import failed: {e}")
    sys.exit(1)

# Configuración
class Config:
    def __init__(self):
        # Usar configuración de rutas importada
        self.HOST = config.HOST
        self.PORT = config.PORT
        self.UPLOADS_DIR = config.UPLOADS_DIR
        self.MODELS_DIR = config.MODELS_DIR
        self.TEMP_DIR = config.TEMP_DIR
        self.PREVIEWS_DIR = config.PREVIEWS_DIR
        self.PUBLIC_PREVIEWS = config.PUBLIC_PREVIEWS

server_config = Config()

# Modelos Pydantic
class PreviewRequest(BaseModel):
    file_path: str
    preview_type: str = "2d"
    width: int = 800
    height: int = 600
    file_id: Optional[str] = None  # Para compatibilidad con Laravel
    background_color: Optional[str] = "#FFFFFF"  # Para compatibilidad con Laravel
    file_type: Optional[str] = None  # Para compatibilidad con Laravel
    options: Optional[Dict[str, Any]] = None

# FastAPI app
app = FastAPI(
    title="Pollux 3D Hybrid Preview Server",
    description="Generate 2D/3D previews using matplotlib + numpy-stl",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Funciones de generación específicas por tipo de archivo

def generate_dxf_preview(file_path: str, width: int = 800, height: int = 600) -> str:
    """Generate preview for DXF file using ezdxf + matplotlib"""
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        fig, ax = plt.subplots(figsize=(width/100, height/100))
        ax.set_aspect('equal')
        ax.set_title('DXF Drawing Preview', fontweight='bold')
        
        # Procesar entidades básicas
        for entity in msp:
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                ax.plot([start.x, end.x], [start.y, end.y], 'b-', linewidth=1)
            elif entity.dxftype() == 'CIRCLE':
                center = entity.dxf.center
                radius = entity.dxf.radius
                circle = plt.Circle((center.x, center.y), radius, fill=False, color='blue', linewidth=1)
                ax.add_patch(circle)
            elif entity.dxftype() == 'ARC':
                # Implementación básica de arco
                center = entity.dxf.center
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                arc = plt.Circle((center.x, center.y), radius, fill=False, color='blue', linewidth=1)
                ax.add_patch(arc)
        
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        
        # Guardar
        preview_filename = f"dxf_preview_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(server_config.PREVIEWS_DIR, preview_filename)
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        return preview_filename
        
    except Exception as e:
        logger.error(f"Error generating DXF preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate DXF preview: {str(e)}")

def generate_step_preview(file_path: str, width: int = 800, height: int = 600) -> str:
    """Generate preview for STEP file using PythonOCC + matplotlib"""
    try:
        # Leer archivo STEP
        step_reader = STEPControl_Reader()
        status = step_reader.ReadFile(file_path)
        
        if status != IFSelect_RetDone:
            raise ValueError("Failed to read STEP file")
        
        step_reader.TransferRoots()
        shape = step_reader.OneShape()
        
        # Crear malla para visualización
        mesh_tool = BRepMesh_IncrementalMesh(shape, 0.1)
        mesh_tool.Perform()
        
        # Obtener bounding box
        bbox = Bnd_Box()
        brepbndlib_Add(shape, bbox)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
        
        # Crear visualización simple con matplotlib
        fig = plt.figure(figsize=(width/100, height/100))
        ax = fig.add_subplot(111, projection='3d')
        
        # Dibujar bounding box como representación básica
        ax.plot([xmin, xmax], [ymin, ymin], [zmin, zmin], 'b-', linewidth=2)
        ax.plot([xmin, xmax], [ymax, ymax], [zmax, zmax], 'b-', linewidth=2)
        ax.plot([xmin, xmin], [ymin, ymax], [zmin, zmin], 'b-', linewidth=2)
        ax.plot([xmax, xmax], [ymin, ymax], [zmax, zmax], 'b-', linewidth=2)
        
        ax.set_title('STEP Model Preview', fontweight='bold')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        
        # Guardar
        preview_filename = f"step_preview_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(server_config.PREVIEWS_DIR, preview_filename)
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        return preview_filename
        
    except Exception as e:
        logger.error(f"Error generating STEP preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate STEP preview: {str(e)}")

def generate_eps_preview(file_path: str, width: int = 800, height: int = 600) -> str:
    """Generate preview for EPS file using Ghostscript"""
    try:
        import subprocess
        
        # Crear archivo PNG temporal usando Ghostscript
        preview_filename = f"eps_preview_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(server_config.PREVIEWS_DIR, preview_filename)
        
        # Comando Ghostscript para convertir EPS a PNG
        gs_command = [
            'gs',
            '-dNOPAUSE',
            '-dBATCH',
            '-sDEVICE=png16m',
            f'-r100',  # resolución
            f'-dEPSCrop',
            f'-sOutputFile={output_path}',
            file_path
        ]
        
        result = subprocess.run(gs_command, capture_output=True, text=True, check=True)
        
        if not os.path.exists(output_path):
            raise ValueError("Ghostscript failed to generate output file")
            
        return preview_filename
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Ghostscript error: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Ghostscript failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Error generating EPS preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate EPS preview: {str(e)}")

def generate_2d_matplotlib_preview(file_path: str, width: int = 800, height: int = 600) -> str:
    """Generate 2D technical drawing using matplotlib"""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.stl':
            return generate_stl_2d_matplotlib(file_path, width, height)
        elif file_ext in ['.step', '.stp'] and HAS_PYTHONOCC:
            return generate_step_2d_matplotlib(file_path, width, height)
        else:
            raise ValueError(f"Unsupported file type for 2D preview: {file_ext}")
            
    except Exception as e:
        logger.error(f"Error generating 2D matplotlib preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate 2D preview: {str(e)}")

def generate_stl_2d_matplotlib(file_path: str, width: int, height: int) -> str:
    """Generate 2D technical drawing for STL using matplotlib"""
    
    # Cargar STL
    stl_mesh = mesh.Mesh.from_file(file_path)
    
    # Obtener vértices únicos
    vertices = stl_mesh.vectors.reshape(-1, 3)
    
    # Crear figura con múltiples vistas
    fig = plt.figure(figsize=(12, 8))
    fig.suptitle('STL Technical Drawing', fontsize=16, fontweight='bold')
    
    # Vista frontal (XY)
    ax1 = fig.add_subplot(221)
    ax1.scatter(vertices[:, 0], vertices[:, 1], s=0.1, c='blue', alpha=0.6)
    ax1.set_title('Front View (XY)')
    ax1.set_xlabel('X (mm)')
    ax1.set_ylabel('Y (mm)')
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')
    
    # Vista lateral (XZ)  
    ax2 = fig.add_subplot(222)
    ax2.scatter(vertices[:, 0], vertices[:, 2], s=0.1, c='red', alpha=0.6)
    ax2.set_title('Side View (XZ)')
    ax2.set_xlabel('X (mm)')
    ax2.set_ylabel('Z (mm)')
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')
    
    # Vista superior (YZ)
    ax3 = fig.add_subplot(223)
    ax3.scatter(vertices[:, 1], vertices[:, 2], s=0.1, c='green', alpha=0.6)
    ax3.set_title('Top View (YZ)')
    ax3.set_xlabel('Y (mm)')
    ax3.set_ylabel('Z (mm)')
    ax3.grid(True, alpha=0.3)
    ax3.set_aspect('equal')
    
    # Vista isométrica
    ax4 = fig.add_subplot(224, projection='3d')
    ax4.scatter(vertices[:, 0], vertices[:, 1], vertices[:, 2], s=0.1, c='purple', alpha=0.4)
    ax4.set_title('Isometric View')
    ax4.set_xlabel('X (mm)')
    ax4.set_ylabel('Y (mm)')
    ax4.set_zlabel('Z (mm)')
    
    # Ajustar diseño
    plt.tight_layout()
    
    # Guardar imagen
    preview_filename = f"stl_2d_preview_{uuid.uuid4().hex[:8]}.png"
    preview_path = os.path.join(server_config.PREVIEWS_DIR, preview_filename)
    
    plt.savefig(preview_path, dpi=100, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    logger.info(f"STL 2D preview generated: {preview_path}")
    return preview_filename

def generate_step_2d_matplotlib(file_path: str, width: int, height: int) -> str:
    """Generate 2D technical drawing for STEP using matplotlib"""
    
    if not HAS_PYTHONOCC:
        raise ValueError("PythonOCC not available for STEP processing")
    
    # Cargar STEP
    step_loader = STEPControl_Reader()
    status = step_loader.ReadFile(file_path)
    
    if status != IFSelect_RetDone:
        raise ValueError("Failed to read STEP file")
    
    step_loader.TransferRoots()
    shape = step_loader.OneShape()
    
    # Obtener bounding box
    bbox = Bnd_Box()
    brepbndlib_Add(shape, bbox)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    
    # Crear figura técnica
    fig = plt.figure(figsize=(12, 8))
    fig.suptitle('STEP Technical Drawing', fontsize=16, fontweight='bold')
    
    # Dibujar vistas proyectadas
    ax1 = fig.add_subplot(221)
    rect1 = plt.Rectangle((xmin, ymin), xmax-xmin, ymax-ymin, 
                         fill=False, edgecolor='blue', linewidth=2)
    ax1.add_patch(rect1)
    ax1.set_xlim(xmin-5, xmax+5)
    ax1.set_ylim(ymin-5, ymax+5)
    ax1.set_title('Front View (XY)')
    ax1.set_xlabel('X (mm)')
    ax1.set_ylabel('Y (mm)')
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')
    
    # Vista lateral
    ax2 = fig.add_subplot(222)
    rect2 = plt.Rectangle((xmin, zmin), xmax-xmin, zmax-zmin,
                         fill=False, edgecolor='red', linewidth=2)
    ax2.add_patch(rect2)
    ax2.set_xlim(xmin-5, xmax+5)
    ax2.set_ylim(zmin-5, zmax+5)
    ax2.set_title('Side View (XZ)')
    ax2.set_xlabel('X (mm)')
    ax2.set_ylabel('Z (mm)')
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')
    
    # Vista superior
    ax3 = fig.add_subplot(223)
    rect3 = plt.Rectangle((ymin, zmin), ymax-ymin, zmax-zmin,
                         fill=False, edgecolor='green', linewidth=2)
    ax3.add_patch(rect3)
    ax3.set_xlim(ymin-5, ymax+5)
    ax3.set_ylim(zmin-5, zmax+5)
    ax3.set_title('Top View (YZ)')
    ax3.set_xlabel('Y (mm)')
    ax3.set_ylabel('Z (mm)')
    ax3.grid(True, alpha=0.3)
    ax3.set_aspect('equal')
    
    # Información dimensional
    ax4 = fig.add_subplot(224)
    ax4.axis('off')
    dimensions_text = f"""
DIMENSIONS:
Width (X): {xmax-xmin:.2f} mm
Height (Y): {ymax-ymin:.2f} mm  
Depth (Z): {zmax-zmin:.2f} mm

VOLUME: {(xmax-xmin)*(ymax-ymin)*(zmax-zmin):.2f} mm³
"""
    ax4.text(0.1, 0.5, dimensions_text, fontsize=12, 
             verticalalignment='center', fontfamily='monospace')
    
    plt.tight_layout()
    
    # Guardar imagen
    preview_filename = f"step_2d_preview_{uuid.uuid4().hex[:8]}.png"
    preview_path = os.path.join(server_config.PREVIEWS_DIR, preview_filename)
    
    plt.savefig(preview_path, dpi=100, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    
    logger.info(f"STEP 2D preview generated: {preview_path}")
    return preview_filename

def generate_wireframe_matplotlib_preview(file_path: str, width: int = 800, height: int = 600) -> str:
    """Generate wireframe technical drawing using matplotlib"""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.stl':
            return generate_stl_wireframe_matplotlib(file_path, width, height)
        elif file_ext in ['.step', '.stp'] and HAS_PYTHONOCC:
            return generate_step_wireframe_matplotlib(file_path, width, height)
        else:
            raise ValueError(f"Unsupported file type for wireframe preview: {file_ext}")
            
    except Exception as e:
        logger.error(f"Error generating wireframe matplotlib preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate wireframe preview: {str(e)}")

def generate_stl_wireframe_matplotlib(file_path: str, width: int, height: int) -> str:
    """Generate wireframe technical drawing for STL using matplotlib"""
    
    # Cargar STL
    stl_mesh = mesh.Mesh.from_file(file_path)
    
    # Obtener vértices únicos y caras
    vertices = stl_mesh.vectors.reshape(-1, 3)
    faces = stl_mesh.vectors
    
    # Crear figura con múltiples vistas wireframe
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle('STL Wireframe View', fontsize=16, fontweight='bold')
    
    # Vista 3D principal wireframe
    ax1 = fig.add_subplot(221, projection='3d')
    
    # Dibujar wireframe de las caras
    for face in faces[::10]:  # Reducir densidad para mejor visualización
        # Conectar los vértices de cada cara triangular
        face_vertices = np.vstack([face, face[0]])  # Cerrar el triángulo
        ax1.plot(face_vertices[:, 0], face_vertices[:, 1], face_vertices[:, 2], 
                'b-', linewidth=0.5, alpha=0.7)
    
    ax1.set_title('3D Wireframe')
    ax1.set_xlabel('X (mm)')
    ax1.set_ylabel('Y (mm)')
    ax1.set_zlabel('Z (mm)')
    
    # Vista frontal wireframe (XY)
    ax2 = fig.add_subplot(222)
    for face in faces[::20]:  # Mayor reducción para vistas 2D
        face_2d = face[:, [0, 1]]  # Proyección XY
        face_2d = np.vstack([face_2d, face_2d[0]])  # Cerrar triángulo
        ax2.plot(face_2d[:, 0], face_2d[:, 1], 'r-', linewidth=0.3, alpha=0.6)
    
    ax2.set_title('Front Wireframe (XY)')
    ax2.set_xlabel('X (mm)')
    ax2.set_ylabel('Y (mm)')
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')
    
    # Vista lateral wireframe (XZ)
    ax3 = fig.add_subplot(223)
    for face in faces[::20]:
        face_2d = face[:, [0, 2]]  # Proyección XZ
        face_2d = np.vstack([face_2d, face_2d[0]])
        ax3.plot(face_2d[:, 0], face_2d[:, 1], 'g-', linewidth=0.3, alpha=0.6)
    
    ax3.set_title('Side Wireframe (XZ)')
    ax3.set_xlabel('X (mm)')
    ax3.set_ylabel('Z (mm)')
    ax3.grid(True, alpha=0.3)
    ax3.set_aspect('equal')
    
    # Vista superior wireframe (YZ)
    ax4 = fig.add_subplot(224)
    for face in faces[::20]:
        face_2d = face[:, [1, 2]]  # Proyección YZ
        face_2d = np.vstack([face_2d, face_2d[0]])
        ax4.plot(face_2d[:, 0], face_2d[:, 1], 'm-', linewidth=0.3, alpha=0.6)
    
    ax4.set_title('Top Wireframe (YZ)')
    ax4.set_xlabel('Y (mm)')
    ax4.set_ylabel('Z (mm)')
    ax4.grid(True, alpha=0.3)
    ax4.set_aspect('equal')
    
    # Ajustar diseño
    plt.tight_layout()
    
    # Guardar imagen
    preview_filename = f"stl_wireframe_preview_{uuid.uuid4().hex[:8]}.png"
    preview_path = os.path.join(server_config.PREVIEWS_DIR, preview_filename)
    
    plt.savefig(preview_path, dpi=120, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    logger.info(f"STL wireframe preview generated: {preview_path}")
    return preview_filename

def generate_step_wireframe_matplotlib(file_path: str, width: int, height: int) -> str:
    """Generate wireframe technical drawing for STEP using matplotlib"""
    
    if not HAS_PYTHONOCC:
        raise ValueError("PythonOCC not available for STEP processing")
    
    # Simple wireframe - para STEP completo necesitaríamos más procesamiento
    # Por ahora retornamos un placeholder
    preview_filename = f"step_wireframe_preview_{uuid.uuid4().hex[:8]}.png"
    preview_path = os.path.join(server_config.PREVIEWS_DIR, preview_filename)
    
    # Crear una imagen simple indicando que STEP wireframe no está completamente implementado
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.text(0.5, 0.5, 'STEP Wireframe Preview\n(Advanced feature in development)', 
            horizontalalignment='center', verticalalignment='center',
            fontsize=16, fontweight='bold')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title('STEP Wireframe Preview')
    
    plt.savefig(preview_path, dpi=100, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    
    logger.info(f"STEP wireframe preview generated: {preview_path}")
    return preview_filename

def generate_2d_wireframe_preview(file_path: str, width: int = 800, height: int = 600) -> str:
    """Generate 2D wireframe using existing wireframe function - eliminates redundancy"""
    # Reutilizar la función wireframe existente que ya genera vistas 2D ortográficas
    logger.info("Using existing wireframe function for 2D wireframe (eliminates redundancy)")
    return generate_wireframe_matplotlib_preview(file_path, width, height)

# Función eliminada: generate_stl_2d_wireframe era redundante
# La función generate_stl_wireframe_matplotlib ya genera vistas 2D ortográficas

# Función eliminada: generate_step_2d_wireframe era redundante  
# La función generate_step_wireframe_matplotlib ya maneja STEP wireframes

@app.get("/")
async def root():
    return {
        "message": "Pollux 3D Hybrid Preview Server",
        "version": "2.0",
        "capabilities": {
            "matplotlib_2d": True,
            "numpy_stl": True,
            "pythonocc_step": HAS_PYTHONOCC,
            "pyvista_advanced": HAS_PYVISTA
        }
    }

@app.post("/generate-preview")
async def generate_preview(request: PreviewRequest):
    """Generate preview for a file"""
    return await generate_preview_internal(request)

@app.post("/generate_preview")  # Compatibilidad con Laravel (guión bajo)
async def generate_preview_legacy(request: PreviewRequest):
    """Generate preview for a file (legacy endpoint)"""
    return await generate_preview_internal(request)

async def generate_preview_internal(request: PreviewRequest):
    """Internal preview generation logic"""
    try:
        # Convertir la ruta relativa de Laravel a ruta absoluta del sistema
        file_path = config.get_absolute_path(request.file_path)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        # Determinar tipo de archivo
        file_type = request.file_type or os.path.splitext(file_path)[1].lower().lstrip('.')
        
        # Generar preview según el tipo de archivo
        if file_type.lower() in ['stl']:
            if request.preview_type == "2d":
                preview_filename = generate_2d_matplotlib_preview(
                    file_path, request.width, request.height
                )
            elif request.preview_type == "wireframe":
                preview_filename = generate_wireframe_matplotlib_preview(
                    file_path, request.width, request.height
                )
            elif request.preview_type == "wireframe_2d":
                preview_filename = generate_2d_wireframe_preview(
                    file_path, request.width, request.height
                )
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported preview type: {request.preview_type}")
                
        elif file_type.lower() in ['dxf', 'dwg']:
            if not HAS_DXF:
                raise HTTPException(status_code=501, detail="DXF support not available - ezdxf not installed")
            preview_filename = generate_dxf_preview(file_path, request.width, request.height)
            
        elif file_type.lower() in ['step', 'stp']:
            if not HAS_PYTHONOCC:
                raise HTTPException(status_code=501, detail="STEP support not available - PythonOCC not installed")
            preview_filename = generate_step_preview(file_path, request.width, request.height)
            
        elif file_type.lower() in ['eps', 'ai']:
            if not HAS_EPS:
                raise HTTPException(status_code=501, detail="EPS support not available - Ghostscript not installed")
            preview_filename = generate_eps_preview(file_path, request.width, request.height)
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")
        
        # Read the generated image and convert to base64
        preview_path = os.path.join(server_config.PREVIEWS_DIR, preview_filename)
        if not os.path.exists(preview_path):
            raise HTTPException(status_code=500, detail="Generated preview file not found")
            
        import base64
        with open(preview_path, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Si tenemos file_id, copiar archivo a la estructura Laravel correcta
        final_preview_path = preview_path
        if request.file_id:
            # Usar configuración para obtener el directorio correcto
            laravel_preview_dir = config.get_laravel_preview_path(request.file_id)
            
            # Copiar archivo a la ubicación final
            final_preview_path = os.path.join(laravel_preview_dir, preview_filename)
            import shutil
            shutil.copy2(preview_path, final_preview_path)
            logger.info(f"Preview copied to Laravel structure: {final_preview_path}")
        
        # DON'T clean up the temp file - keep it for debugging
        # try:
        #     os.remove(preview_path)
        # except:
        #     pass
        
        return {
            "success": True,
            "image_data": img_data,
            "preview_filename": preview_filename,
            "preview_url": f"/storage/previews/{request.file_id}/{preview_filename}" if request.file_id else f"/preview/{preview_filename}",
            "final_path": final_preview_path,
            "generator": "matplotlib"
        }
        
    except Exception as e:
        import traceback
        error_details = f"Preview generation failed: {str(e)}\nTraceback: {traceback.format_exc()}"
        logger.error(error_details)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/preview/{filename}")
async def get_preview(filename: str):
    """Serve preview image"""
    preview_path = os.path.join(server_config.PREVIEWS_DIR, filename)
    if os.path.exists(preview_path):
        return FileResponse(preview_path)
    else:
        raise HTTPException(status_code=404, detail="Preview not found")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "dependencies": {
            "matplotlib": True,
            "numpy_stl": True,
            "pythonocc": HAS_PYTHONOCC,
            "pyvista": HAS_PYVISTA,
            "ezdxf": HAS_DXF,
            "ghostscript": HAS_EPS
        }
    }

if __name__ == "__main__":
    print(f"Starting server on {server_config.HOST}:{server_config.PORT}")
    uvicorn.run(app, host=server_config.HOST, port=server_config.PORT, log_level="info")
