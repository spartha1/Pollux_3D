print("Starting Simple Preview Server...")

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

# System imports
import base64
import io
import logging
from pathlib import Path

# Import configuration
try:
    from config import config
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

# Image processing - try first as it's essential
try:
    from PIL import Image, ImageDraw, ImageFont
    logger.info("PIL imported successfully")
except ImportError as e:
    logger.critical(f"Failed to import PIL: {e}")
    sys.exit(1)

# API imports
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
    logger.info("FastAPI and related imports successful")
except ImportError as e:
    logger.critical(f"Failed to import FastAPI dependencies: {e}")
    sys.exit(1)

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
    STEP_SUPPORT = False

# Visualization support via VTK/PyVista
try:
    import vtk
    import pyvista as pv
    from pyvista import wrap
    STL_SUPPORT = True
    logger.info("PyVista imported successfully - STL files and visualization supported")
except ImportError as e:
    logger.warning(f"PyVista/VTK import failed - STL files and visualization will be limited: {e}")
    STL_SUPPORT = False

logger.info("Import phase completed")

# Create and configure FastAPI app
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
    allow_origins=["*"] if not config.IS_PRODUCTION else ["https://polluxweb.com"],  # Ajustar en producción
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class PreviewRequest(BaseModel):
    """Request model for generating previews"""
    file_id: str = Field(..., description="Unique identifier for the file")
    file_path: str = Field(..., description="Path to the file relative to the upload directory")
    preview_type: str = Field(..., description="Type of preview to generate (2d, wireframe, or 3d)")
    width: int = Field(800, description="Width of the preview image")
    height: int = Field(600, description="Height of the preview image")
    background_color: str = Field("#FFFFFF", description="Background color in hex format")
    file_type: str = Field(..., description="Type of the file (step, stl, dxf)")

class PreviewResponse(BaseModel):
    """Response model for preview generation"""
    file_id: str
    preview_type: str
    image_data: str
    status: str
    message: str = ""

def validate_file_type(file_type: str) -> bool:
    """Validate if the file type is supported with current imports"""
    if file_type.lower() == "step" and not STEP_SUPPORT:
        return False
    if file_type.lower() == "stl" and not STL_SUPPORT:
        return False
    if file_type.lower() == "dxf" and not DXF_SUPPORT:
        return False
    return True

def get_absolute_file_path(file_path: str) -> Path:
    """Convert relative file path to absolute path and validate"""
    abs_path = config.UPLOAD_DIR / file_path
    if not abs_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not abs_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    return abs_path

def save_preview(image: Image.Image, file_id: str, preview_type: str) -> str:
    """Save preview image and return its path"""
    preview_path = config.PREVIEW_DIR / f"{file_id}_{preview_type}.png"
    image.save(preview_path)
    return str(preview_path)

def encode_image(image: Image.Image) -> str:
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

@app.post("/generate_preview", response_model=PreviewResponse)
async def generate_preview(request: PreviewRequest, background_tasks: BackgroundTasks):
    """
    Generate a preview image for a CAD file
    """
    try:
        logger.info(f"Processing preview request for file ID: {request.file_id}")

        # Validate file type support
        if not validate_file_type(request.file_type):
            raise HTTPException(
                status_code=400,
                detail=f"File type {request.file_type} is not supported with current imports"
            )

        # Get and validate file path
        try:
            file_path = get_absolute_file_path(request.file_path)
        except (FileNotFoundError, ValueError) as e:
            raise HTTPException(status_code=404, detail=str(e))

        # Generate preview based on type
        if request.preview_type == "2d":
            # Implement 2D preview generation
            pass
        elif request.preview_type == "wireframe":
            # Implement wireframe preview generation
            pass
        elif request.preview_type == "3d":
            # Implement 3D preview generation
            pass
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid preview type: {request.preview_type}"
            )

        # TODO: Implement actual preview generation logic here
        # For now, return a placeholder image
        image = Image.new('RGB', (request.width, request.height), request.background_color)
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), f"Preview for {request.file_id}", fill="black")

        # Save preview and encode for response
        preview_path = save_preview(image, request.file_id, request.preview_type)
        image_data = encode_image(image)

        # Schedule cleanup in background
        background_tasks.add_task(lambda: Path(preview_path).unlink(missing_ok=True))

        return PreviewResponse(
            file_id=request.file_id,
            preview_type=request.preview_type,
            image_data=image_data,
            status="success"
        )

    except Exception as e:
        logger.exception("Error generating preview")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Preview service starting up...")
    # Ensure required directories exist
    config.setup()
    logger.info(f"Service initialized. STEP support: {STEP_SUPPORT}, STL support: {STL_SUPPORT}")

if __name__ == "__main__":
    logger.info(f"Starting preview service on {config.HOST}:{config.PORT}")
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level="info"
    )
