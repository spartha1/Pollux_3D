print("Starting Simple Preview Server...")

# Import environment verification module
import sys
import os
from pathlib import Path
from preview_env import verify_conda_env, verify_imports

# Verify conda environment
python_path = verify_conda_env()
print(f"Using Python from: {python_path}")

# System imports
import base64
import io
import logging
import time
from datetime import datetime

# Security imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import APIKeyHeader, Security
from typing import Optional

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

# Image processing - try first as it's essential
try:
    from PIL import Image, ImageDraw, ImageFont
    logger.info("PIL imported successfully")
except ImportError as e:
    logger.critical(f"Failed to import PIL: {e}")
    sys.exit(1)

# API imports
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security, Request
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

# Configurar rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar compresión GZip
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configurar autenticación API Key
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """Validate API key if we're in production"""
    if Config.is_production():
        if not api_key_header or api_key_header != os.getenv("API_KEY"):
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )
    return api_key_header

@app.middleware("http")
async def count_requests(request: Request, call_next):
    """Count the number of requests made to the server"""
    app.state.request_count = getattr(app.state, "request_count", 0) + 1
    response = await call_next(request)
    return response

# Configure CORS
CORS_ORIGINS = ["https://polluxweb.com"] if Config.is_production() else ["*"]
logger.info(f"Configuring CORS with origins: {CORS_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Rate limiting configuration
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )

app.add_middleware(GZipMiddleware)

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

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    version: str
    step_support: bool
    stl_support: bool
    dxf_support: bool
    uptime: float
    temp_files: int
    memory_usage: float
    cpu_percent: float
    disk_usage: float
    environment: str
    python_version: str
    start_time: str
    request_count: int = 0

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
@limiter.limit("20/minute")
async def generate_preview(
    request: PreviewRequest,
    background_tasks: BackgroundTasks,
    api_key: Optional[str] = Depends(get_api_key)
):
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

@app.get("/health", response_model=HealthResponse)
@limiter.limit("60/minute")
async def health_check(api_key: Optional[str] = Depends(get_api_key)):
    """
    Health check endpoint that returns service status and capabilities
    """
    import psutil
    import platform

    # Contar archivos temporales
    temp_files = len(list(Path(config.TEMP_DIR).glob('*')))

    # Obtener información del sistema
    process = psutil.Process()
    disk = psutil.disk_usage('/')

    # Formatear la hora de inicio
    start_time = datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        step_support=STEP_SUPPORT,
        stl_support=STL_SUPPORT,
        dxf_support=DXF_SUPPORT,
        uptime=time.time() - process.create_time(),
        temp_files=temp_files,
        memory_usage=process.memory_info().rss / 1024 / 1024,  # MB
        cpu_percent=process.cpu_percent(),
        disk_usage=disk.percent,
        environment="production" if Config.is_production() else "development",
        python_version=platform.python_version(),
        start_time=start_time,
        request_count=app.state.get("request_count", 0)
    )

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
