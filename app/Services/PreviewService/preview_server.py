#!/usr/bin/env python3

# Verificar el entorno Python
import sys
import os
from pathlib import Path

expected_env = "pollux-preview-env"
python_path = Path(sys.executable)
if "miniconda3/envs/" + expected_env not in str(python_path):
    print(f"Error: This script must be run using Python from the '{expected_env}' conda environment")
    print(f"Current Python: {sys.executable}")
    print(f"Please use the start_preview_server.bat script to run the server")
    sys.exit(1)

print(f"Using Python from: {sys.executable}")

# Import configuration
try:
    from config import config
    print("Configuration loaded successfully")
except ImportError as e:
    print(f"Failed to import config: {e}")
    print("Please ensure config.py is in the same directory")
    sys.exit(1)

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator
import uvicorn
import base64
import tempfile
import numpy as np
from PIL import Image
import io
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.info("Starting Preview Server initialization...")

# Intentar importar PythonOCC para STEP/STP
try:
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec
    from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
    from OCC.Core.Graphic3d import Graphic3d_RenderingParams
    from OCC.Core.V3d import V3d_Viewer
    from OCC.Core.AIS import AIS_Shape
    import pyvista as pv
    STEP_SUPPORT = True
except ImportError as e:
    logger.warning(f"PythonOCC no está instalado. La vista previa de STEP/STP será limitada. Error: {e}")
    STEP_SUPPORT = False

# Intentar importar numpy-stl para STL
try:
    from stl import mesh
    STL_SUPPORT = True
except ImportError:
    logger.warning("numpy-stl no está instalado. La vista previa de STL será limitada.")
    STL_SUPPORT = False

app = FastAPI()

class PreviewRequest(BaseModel):
    file_id: str
    file_path: str
    render_type: str = '2d'  # '2d', 'wireframe', '3d'
    # Campos adicionales que Laravel puede enviar
    preview_type: str = None  # Alias para render_type
    width: int = 800
    height: int = 600
    background_color: str = "#FFFFFF"
    file_type: str = None
    output_dir: str = None  # Laravel envía este campo
    
    @model_validator(mode='before')
    @classmethod
    def validate_render_type(cls, data):
        # Si preview_type está presente, usar como render_type
        if isinstance(data, dict) and 'preview_type' in data and data['preview_type']:
            data['render_type'] = data['preview_type']
        return data

def generate_step_preview(file_path: str, render_type: str) -> str:
    """Generate preview for STEP/STP files"""
    if not STEP_SUPPORT:
        raise HTTPException(400, "PythonOCC no está instalado para vista previa STEP")

    try:
        # Leer archivo STEP
        reader = STEPControl_Reader()
        status = reader.ReadFile(file_path)
        if status != IFSelect_RetDone:
            raise Exception(f"Error al leer archivo STEP: {status}")

        # Transferir a shape
        reader.TransferRoot()
        shape = reader.OneShape()

        # Crear una malla para visualización
        mesh = BRepMesh_IncrementalMesh(shape, 0.1)
        mesh.Perform()

        # Convertir a formato PyVista para renderizado
        plotter = pv.Plotter(off_screen=True, window_size=[800, 600])

        if render_type == '3d':
            # Vista 3D con sombreado
            plotter.add_mesh(shape, color='white', show_edges=True)
            plotter.camera_position = 'iso'
            plotter.enable_shadows()
        else:
            # Vista wireframe
            plotter.add_mesh(shape, style='wireframe', color='black', line_width=2)
            plotter.camera_position = 'xy'  # Vista frontal para wireframe

        # Ajustar vista
        plotter.camera.zoom(1.2)

        # Renderizar y capturar
        image = plotter.screenshot()

        # Convertir a PNG y luego a base64
        img_bytes = io.BytesIO()
        pv.save_image(img_bytes, image, 'png')
        img_bytes.seek(0)

        return base64.b64encode(img_bytes.getvalue()).decode()

    except Exception as e:
        logger.error(f"Error generando vista previa STEP: {str(e)}")
        raise HTTPException(500, f"Error generando vista previa: {str(e)}")

def generate_stl_preview(file_path: str, render_type: str) -> str:
    """Generate preview for STL files"""
    if not STL_SUPPORT:
        raise HTTPException(400, "numpy-stl no está instalado para vista previa STL")

    try:
        # Leer STL
        mesh_data = mesh.Mesh.from_file(file_path)

        # Configurar visualización
        if render_type == '3d':
            # Usar PyVista o VTK para renderizado 3D
            import pyvista as pv
            pl = pv.Plotter(off_screen=True)
            pl.add_mesh(mesh_data, show_edges=True)
            pl.camera_position = 'iso'
            pl.window_size = [800, 600]

            # Renderizar y capturar
            img = pl.screenshot()

        else:
            # Vista 2D/wireframe simple
            vectors = mesh_data.vectors
            x = vectors[:,:,0].flatten()
            y = vectors[:,:,1].flatten()

            # Crear imagen 2D
            import matplotlib.pyplot as plt
            plt.figure(figsize=(8,6))
            plt.plot(x, y, 'b-', linewidth=0.5)
            plt.axis('equal')

            # Capturar plot
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            img = Image.open(buf)

        # Convertir a base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    except Exception as e:
        logger.error(f"Error generando vista previa STL: {str(e)}")
        raise HTTPException(500, f"Error generando vista previa: {str(e)}")

@app.post("/preview")
async def generate_preview(request: PreviewRequest, background_tasks: BackgroundTasks):
    """Generate preview for 3D files"""
    file_path = request.file_path
    
    # Si la ruta no es absoluta, asumir que es relativa al directorio storage/app de Laravel
    if not os.path.isabs(file_path):
        storage_path = config.BASE_DIR / 'storage' / 'app' / file_path
        file_path = str(storage_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(404, f"Archivo no encontrado: {file_path}")

    # Determinar tipo de archivo
    ext = Path(file_path).suffix.lower()

    try:
        if ext in ['.step', '.stp']:
            image_data = generate_step_preview(file_path, request.render_type)
        elif ext == '.stl':
            image_data = generate_stl_preview(file_path, request.render_type)
        else:
            raise HTTPException(400, f"Tipo de archivo no soportado: {ext}")

        return {
            "file_id": request.file_id,
            "image_data": image_data,
            "render_type": request.render_type
        }

    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        raise HTTPException(500, f"Error generating preview: {str(e)}")

# Alias para compatibilidad con Laravel (usa generate_preview en lugar de preview)
@app.post("/generate_preview")
async def generate_preview_alias(request: PreviewRequest, background_tasks: BackgroundTasks):
    """Generate preview for 3D files - Laravel compatibility endpoint"""
    return await generate_preview(request, background_tasks)

@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to list all available routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods)
            })
    return {"routes": routes}

if __name__ == "__main__":
    uvicorn.run(app, host=config.HOST, port=config.PORT)
