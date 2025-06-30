#!/usr/bin/env python3
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
from fastapi.security import APIKeyHeader
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel

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
    from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
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

async def get_api_key(api_key_header: Optional[str] = Depends(api_key_header)) -> Optional[str]:
    """Validate API key if we're in production"""
    if Config.is_production():
        if not api_key_header or api_key_header != os.getenv("API_KEY"):
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )
    return api_key_header



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

class FileMetadata(BaseModel):
    """Modelo para metadatos del archivo"""
    file_size: int
    dimensions: Optional[dict] = None
    vertex_count: Optional[int] = None
    face_count: Optional[int] = None
    bounds: Optional[dict] = None
    units: Optional[str] = None
    created_at: Optional[str] = None
    software: Optional[str] = None
    analysis_time: Optional[float] = None

class PreviewResponse(BaseModel):
    """Response model for preview generation"""
    file_id: str
    preview_type: str
    image_data: str
    status: str
    message: str = ""
    metadata: Optional[FileMetadata] = None
    processing_time: float = 0.0
    cached: bool = False

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    version: str = "1.0.0"
    timestamp: str
    request_count: int
    python_version: str
    step_support: bool
    stl_support: bool
    dxf_support: bool
    uptime: float
    temp_files: int
    memory_usage: float
    cpu_percent: float
    disk_usage: float
    environment: str
    start_time: str
    service_uptime: float

start_time = time.time()

@app.middleware("http")
async def count_requests(request: Request, call_next):
    """Count the number of requests made to the server"""
    if not hasattr(request.app.state, "request_count"):
        request.app.state.request_count = 0
    request.app.state.request_count += 1
    response = await call_next(request)
    return response



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

def analyze_file(file_path: Path, file_type: str) -> FileMetadata:
    """Analizar archivo y extraer metadatos"""
    stats = file_path.stat()
    metadata = {
        "file_size": stats.st_size,
        "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat()
    }

    try:
        if file_type.lower() == "stl":
            # Análisis STL con numpy-stl
            from stl import mesh
            mesh_data = mesh.Mesh.from_file(str(file_path))
            metadata.update({
                "vertex_count": len(mesh_data.vectors),
                "face_count": len(mesh_data.vectors),
                "bounds": {
                    "min": mesh_data.min_.tolist(),
                    "max": mesh_data.max_.tolist()
                }
            })
        elif file_type.lower() == "step":
            # Análisis STEP con pythonOCC
            reader = STEPControl_Reader()
            status = reader.ReadFile(str(file_path))
            if status == IFSelect_RetDone:
                reader.TransferRoots()
                shape = reader.OneShape()
                bbox = Bnd_Box()
                brepbndlib_Add(shape, bbox)
                xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
                metadata.update({
                    "bounds": {
                        "min": [xmin, ymin, zmin],
                        "max": [xmax, ymax, zmax]
                    }
                })
    except Exception as e:
        logger.warning(f"Error analyzing file {file_path}: {e}")

    return FileMetadata(**metadata)

def render_preview(
    file_path: Path,
    preview_type: str,
    width: int,
    height: int,
    background_color: str = "#FFFFFF"
) -> Image.Image:
    """Renderizar vista previa usando PyVista"""
    plotter = pv.Plotter(off_screen=True, window_size=[width, height])

    try:
        # Cargar geometría
        if file_path.suffix.lower() == ".stl":
            mesh = pv.read(str(file_path))
        elif file_path.suffix.lower() in [".step", ".stp"]:
            # Convertir STEP a malla usando OCC
            reader = STEPControl_Reader()
            status = reader.ReadFile(str(file_path))
            if status != IFSelect_RetDone:
                raise ValueError("Error reading STEP file")

            reader.TransferRoots()
            shape = reader.OneShape()

            # Crear malla para visualización
            mesh_maker = BRepMesh_IncrementalMesh(shape, 0.1)
            mesh_maker.Perform()

            # Convertir a formato PyVista
            mesh = wrap(shape)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        # Configurar visualización según el tipo
        bg_color = background_color.lstrip('#')
        bg_rgb = tuple(int(bg_color[i:i+2], 16) / 255 for i in (0, 2, 4))
        plotter.set_background(*bg_rgb)

        if preview_type == "wireframe":
            plotter.add_mesh(mesh, style='wireframe', color='black', line_width=2)
        elif preview_type == "2d":
            # Vista 2D desde arriba
            plotter.add_mesh(mesh, color='lightgray', show_edges=True)
            plotter.view_xy()  # Vista superior
        else:  # "3d"
            plotter.add_mesh(mesh, color='white', show_edges=True)
            plotter.add_shadow_plane()
            plotter.enable_shadows()

        # Ajustar cámara
        plotter.camera_position = 'iso'
        plotter.camera.zoom(1.2)

        # Renderizar
        img_array = plotter.screenshot()
        plotter.close()

        return Image.fromarray(img_array)
    except Exception as e:
        logger.error(f"Error rendering preview: {e}")
        raise

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

        # Analizar archivo y extraer metadatos
        start_time = time.time()
        metadata = analyze_file(file_path, request.file_type)

        # Generar vista previa
        try:
            image = render_preview(
                file_path,
                request.preview_type,
                request.width,
                request.height,
                request.background_color
            )
        except Exception as e:
            logger.exception("Error generating preview")
            # Generar imagen de error
            image = Image.new('RGB', (request.width, request.height), request.background_color)
            draw = ImageDraw.Draw(image)
            draw.text((10, 10), f"Error: {str(e)}", fill="black")
            metadata = None

        # Save preview and encode for response
        preview_path = save_preview(image, request.file_id, request.preview_type)
        image_data = encode_image(image)

        # Schedule cleanup in background
        background_tasks.add_task(lambda: Path(preview_path).unlink(missing_ok=True))

        processing_time = time.time() - start_time

        return PreviewResponse(
            file_id=request.file_id,
            preview_type=request.preview_type,
            image_data=image_data,
            status="success",
            metadata=metadata,
            processing_time=processing_time,
            cached=False
        )

    except Exception as e:
        logger.exception("Error generating preview")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
@limiter.limit("60/minute")
async def health_check(request: Request, api_key: Optional[str] = Depends(get_api_key)):
    """
    Health check endpoint that returns service status and capabilities
    """
    import psutil
    import platform

    # Ensure request counter exists
    if not hasattr(app.state, "request_count"):
        app.state.request_count = 0

    # Count temp files
    temp_files = len(list(Path(config.TEMP_DIR).glob('*')))

    # Get system information
    process = psutil.Process()
    disk = psutil.disk_usage('/')

    # Format start time
    process_start = datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
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
        start_time=process_start,
        service_uptime=time.time() - start_time,
        request_count=app.state.request_count
    )

@app.post("/preview", response_model=PreviewResponse)
@limiter.limit("20/minute")
async def preview_endpoint(
    request: PreviewRequest,
    background_tasks: BackgroundTasks,
    api_key: Optional[str] = Depends(get_api_key)
):
    """Alias para /generate_preview para mantener consistencia de APIs"""
    return await generate_preview(request, background_tasks, api_key)

@app.get("/api/health", response_model=HealthResponse)
@limiter.limit("60/minute")
async def health_alias(request: Request, api_key: Optional[str] = Depends(get_api_key)):
    """Alias para /health con prefijo /api para consistencia"""
    return await health_check(request, api_key)

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
