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

# Verificar directorios
required_dirs = {
    'uploads': r'C:\xampp\htdocs\laravel\Pollux_3D\app\storage\app\uploads',
    'temp': r'C:\xampp\htdocs\laravel\Pollux_3D\app\storage\app\temp',
    'previews': r'C:\xampp\htdocs\laravel\Pollux_3D\app\storage\app\previews',
    'logs': r'C:\xampp\htdocs\laravel\Pollux_3D\app\storage\logs'
}

for name, path in required_dirs.items():
    if os.path.exists(path):
        print(f"[OK] Directory '{name}' verified: {path}")
    else:
        os.makedirs(path, exist_ok=True)
        print(f"[CREATED] Directory '{name}' created: {path}")

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
        
except ImportError as e:
    logger.error(f"Critical import failed: {e}")
    sys.exit(1)

# Configuración
class Config:
    HOST = "127.0.0.1"
    PORT = 8052  # Puerto diferente para evitar conflictos
    UPLOADS_DIR = required_dirs['uploads']
    TEMP_DIR = required_dirs['temp'] 
    PREVIEWS_DIR = required_dirs['previews']

config = Config()

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
    preview_path = os.path.join(config.PREVIEWS_DIR, preview_filename)
    
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
    preview_path = os.path.join(config.PREVIEWS_DIR, preview_filename)
    
    plt.savefig(preview_path, dpi=100, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    
    logger.info(f"STEP 2D preview generated: {preview_path}")
    return preview_filename

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
        file_path = request.file_path
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Generar preview según el tipo
        if request.preview_type == "2d":
            preview_filename = generate_2d_matplotlib_preview(
                file_path, request.width, request.height
            )
        else:
            raise HTTPException(status_code=400, detail="Only 2D previews supported currently")
        
        return {
            "success": True,
            "preview_filename": preview_filename,
            "preview_url": f"/preview/{preview_filename}",
            "generator": "matplotlib"
        }
        
    except Exception as e:
        logger.error(f"Preview generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/preview/{filename}")
async def get_preview(filename: str):
    """Serve preview image"""
    preview_path = os.path.join(config.PREVIEWS_DIR, filename)
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
            "pyvista": HAS_PYVISTA
        }
    }

if __name__ == "__main__":
    print(f"Starting server on {config.HOST}:{config.PORT}")
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
