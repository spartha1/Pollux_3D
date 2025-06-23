print("Starting imports...")

# System imports
import os
import sys
import base64
import io
import logging
from pathlib import Path

# Image processing - try first as it's essential
try:
    from PIL import Image, ImageDraw, ImageFont
    print("PIL imported successfully")
except ImportError as e:
    print(f"Failed to import PIL: {e}")
    sys.exit(1)

# API imports
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    print("FastAPI and related imports successful")
except ImportError as e:
    print(f"Failed to import FastAPI dependencies: {e}")
    sys.exit(1)

# 3D processing imports
STEP_SUPPORT = False
STL_SUPPORT = False
DXF_SUPPORT = False

try:
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.Visualization import Display3d
    STEP_SUPPORT = True
    print("OCC.Core imported successfully - STEP files supported")
except ImportError as e:
    print(f"Warning: OCC.Core import failed - STEP files will not be supported: {e}")

try:
    import numpy as np
    import vtk
    import pyvista as pv
    STL_SUPPORT = True
    print("PyVista imported successfully - STL files supported")
except ImportError as e:
    print(f"Warning: PyVista import failed - STL files will not be supported: {e}")

print("Import phase completed")

app = FastAPI(
    title="PolluxWeb Preview Service",
    description="API service for generating 2D, wireframe, and 3D previews of CAD files",
    version="1.0.0",
    docs_url="/",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class PreviewRequest(BaseModel):
    """
    Request model for generating previews

    Attributes:
        file_id: Unique identifier for the file
        file_path: Absolute path to the file on the server
        render_type: Type of preview to generate ('2d', 'wireframe', or '3d')
    """
    file_id: str
    file_path: str
    render_type: str = '2d'

@app.get("/health")
async def health_check():
    """Check if the preview service is running and healthy"""
    supported_formats = []
    if STEP_SUPPORT:
        supported_formats.extend([".step", ".stp"])
    if STL_SUPPORT:
        supported_formats.append(".stl")
    if DXF_SUPPORT:
        supported_formats.extend([".dxf", ".dwg"])

    return {
        "status": "healthy",
        "supported_formats": supported_formats,
        "supported_renders": ["2d", "wireframe", "3d"],
        "features": {
            "step_support": STEP_SUPPORT,
            "stl_support": STL_SUPPORT,
            "dxf_support": DXF_SUPPORT
        }
    }

@app.get("/supported-formats")
async def supported_formats():
    """Get list of supported file formats"""
    return {
        "formats": {
            "step": {
                "extensions": [".step", ".stp"],
                "description": "STEP 3D CAD files"
            },
            "stl": {
                "extensions": [".stl"],
                "description": "STL 3D mesh files"
            },
            "dxf": {
                "extensions": [".dxf", ".dwg"],
                "description": "AutoCAD DXF/DWG files"
            }
        }
    }

def process_step_file(file_path: str, render_type: str) -> Image.Image:
    """Process STEP file and generate preview"""
    reader = STEPControl_Reader()
    status = reader.ReadFile(file_path)

    if status != IFSelect_RetDone:
        raise HTTPException(500, "Failed to read STEP file")

    reader.TransferRoot()
    shape = reader.OneShape()

    # Create a PyVista plotter
    plotter = pv.Plotter(off_screen=True, window_size=(800, 600))

    if render_type == '2d':
        # Top view
        plotter.camera_position = 'xy'
        plotter.camera.zoom(1.2)
    elif render_type == 'wireframe':
        plotter.camera.zoom(1.2)
        plotter.enable_wireframe()
    else:  # 3d view
        plotter.camera_position = 'iso'
        plotter.enable_shadows()

    # Add the shape to the plotter
    # Convert OCC shape to VTK
    vtk_shape = shape.ToVTK()
    plotter.add_mesh(vtk_shape, color='blue', show_edges=render_type == 'wireframe')

    # Render and get image
    plotter.show(auto_close=False)
    img_array = plotter.screenshot(transparent_background=False)
    plotter.close()

    # Convert numpy array to PIL Image
    return Image.fromarray(img_array)

def process_stl_file(file_path: str, render_type: str) -> Image.Image:
    """Process STL file and generate preview"""
    # Read the STL file
    mesh = pv.read(file_path)

    # Create a PyVista plotter
    plotter = pv.Plotter(off_screen=True, window_size=(800, 600))

    if render_type == '2d':
        plotter.camera_position = 'xy'
        plotter.camera.zoom(1.2)
    elif render_type == 'wireframe':
        plotter.camera.zoom(1.2)
        plotter.enable_wireframe()
    else:  # 3d view
        plotter.camera_position = 'iso'
        plotter.enable_shadows()

    # Add the mesh to the scene
    plotter.add_mesh(mesh, color='blue', show_edges=render_type == 'wireframe')

    # Render and get image
    plotter.show(auto_close=False)
    img_array = plotter.screenshot(transparent_background=False)
    plotter.close()

    # Convert numpy array to PIL Image
    return Image.fromarray(img_array)

@app.post("/preview")
async def generate_preview(request: PreviewRequest):
    """Generate preview for 3D files"""
    if not os.path.exists(request.file_path):
        raise HTTPException(404, f"File not found: {request.file_path}")

    # Get file extension
    file_ext = Path(request.file_path).suffix.lower()

    try:
        if file_ext == '.step' or file_ext == '.stp':
            img = process_step_file(request.file_path, request.render_type)
        elif file_ext == '.stl':
            img = process_stl_file(request.file_path, request.render_type)
        else:
            raise HTTPException(400, f"Unsupported file type: {file_ext}")
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        # Create error image
        img = Image.new('RGB', (800, 600), color='white')

    # Draw on the image to make it clear it's working
    draw = ImageDraw.Draw(img)

    # Draw a rectangle
    draw.rectangle([100, 100, 700, 500], outline='blue', width=5)

    # Draw text
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    draw.text((400, 300), "TEST PREVIEW",
              fill='black', font=font, anchor="mm")
    draw.text((400, 350), f"Type: {request.render_type}",
              fill='blue', font=font, anchor="mm")

    # Save to memory buffer
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # Ensure we're using UTF-8 encoding
    image_data = base64.b64encode(img_byte_arr).decode('utf-8')

    return {
        "file_id": request.file_id,
        "image_data": image_data,
        "render_type": request.render_type
    }

if __name__ == "__main__":
    print("Starting preview server on http://127.0.0.1:8088")
    uvicorn.run(app, host="127.0.0.1", port=8088, log_level="info")
