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
import subprocess
import json

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
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_VERTEX
    from OCC.Core.BRep import BRep_Tool
    from OCC.Core.TopLoc import TopLoc_Location
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib_Add  # Nombre alternativo
    import numpy as np
    from PIL import Image
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    STEP_SUPPORT = True
except ImportError as e:
    try:
        # Intentar imports más básicos
        from OCC.Core.STEPControl import STEPControl_Reader
        from OCC.Core.IFSelect import IFSelect_RetDone
        import numpy as np
        from PIL import Image
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        STEP_SUPPORT = True
    except ImportError as e2:
        logger.warning(f"PythonOCC no está instalado. La vista previa de STEP/STP será limitada. Error: {e2}")
        STEP_SUPPORT = False

# Intentar importar numpy-stl para STL
try:
    from stl import mesh
    STL_SUPPORT = True
except ImportError:
    logger.warning("numpy-stl no está instalado. La vista previa de STL será limitada.")
    STL_SUPPORT = False

app = FastAPI()

def call_external_step_analyzer(file_path: str) -> dict:
    """Llama al analizador STEP externo mejorado para obtener información diagnóstica."""
    try:
        # Ruta al analizador externo
        analyzer_path = Path(__file__).parent.parent / "FileAnalyzers" / "analyze_step.py"
        conda_script = Path(__file__).parent.parent / "FileAnalyzers" / "run_with_conda.sh"

        # Comando para ejecutar el analizador
        cmd = [str(conda_script), str(analyzer_path), file_path]

        # Ejecutar el analizador
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # 30 segundos de timeout
        )

        # Parsear la respuesta JSON
        if result.stdout:
            analysis_data = json.loads(result.stdout)
            logger.info(f"External analyzer returned: {analysis_data.get('status', 'unknown')}")
            return analysis_data
        else:
            logger.warning("External analyzer returned no output")
            return {"error": "Analyzer returned no output", "stderr": result.stderr}

    except subprocess.TimeoutExpired:
        logger.error("External analyzer timed out")
        return {"error": "Analysis timed out", "timeout": True}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse analyzer output: {e}")
        return {"error": f"Invalid JSON response: {e}", "stdout": result.stdout if 'result' in locals() else None}
    except Exception as e:
        logger.error(f"Failed to call external analyzer: {e}")
        return {"error": f"Analyzer execution failed: {e}"}

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

    error_details = None
    try:
        # Leer archivo STEP
        reader = STEPControl_Reader()
        status = reader.ReadFile(file_path)
        if status != IFSelect_RetDone:
            raise Exception(f"Error al leer archivo STEP: {status}")

        # Transferir a shape
        nb_roots = reader.TransferRoot()
        if nb_roots == 0:
            raise Exception("El archivo STEP no contiene geometría transferible")

        shape = reader.OneShape()

        # Verificar que el shape es válido
        if shape is None:
            raise Exception("El archivo STEP no pudo ser procesado. Archivo corrupto o formato inválido.")

        if shape.IsNull():
            raise Exception("Archivo STEP incompatible con PythonOCC")

        # Si llegamos aquí, el análisis básico fue exitoso, continuar con la generación de preview
        # Crear figura para matplotlib
        fig = plt.figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111, projection='3d')

        # Intentar extraer vértices básicos del shape para una visualización simple
        vertices = []

        # Explorar todas las caras del shape sin mesh
        exp = TopExp_Explorer(shape, TopAbs_FACE)

        # Como fallback, crear una representación básica del bounding box
        # Simplificar aún más - usar dimensiones genéricas si no podemos obtener el bbox real
        try:
            bbox = Bnd_Box()
            brepbndlib_Add(shape, bbox)
            xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
        except:
            # Fallback: usar dimensiones genéricas
            xmin, ymin, zmin = -10, -10, -10
            xmax, ymax, zmax = 10, 10, 10

        # Crear una representación wireframe del bounding box
        box_vertices = [
            [xmin, ymin, zmin], [xmax, ymin, zmin], [xmax, ymax, zmin], [xmin, ymax, zmin],  # base
            [xmin, ymin, zmax], [xmax, ymin, zmax], [xmax, ymax, zmax], [xmin, ymax, zmax]   # top
        ]

        # Dibujar el wireframe del bounding box
        box_edges = [
            (0,1), (1,2), (2,3), (3,0),  # base
            (4,5), (5,6), (6,7), (7,4),  # top
            (0,4), (1,5), (2,6), (3,7)   # vertical
        ]

        for edge in box_edges:
            v1, v2 = box_vertices[edge[0]], box_vertices[edge[1]]
            ax.plot([v1[0], v2[0]], [v1[1], v2[1]], [v1[2], v2[2]], 'b-', linewidth=2)

        # Añadir algunos puntos para indicar que es una representación del modelo
        center = [(xmin+xmax)/2, (ymin+ymax)/2, (zmin+zmax)/2]
        ax.scatter(*center, color='red', s=50, label='Center')

        # Configurar vista
        ax.set_xlim([xmin, xmax])
        ax.set_ylim([ymin, ymax])
        ax.set_zlim([zmin, zmax])

        # Configurar perspectiva según tipo de render
        if render_type == '2d':
            ax.view_init(elev=0, azim=0)  # Vista frontal
            ax.set_title('STEP File - 2D View (Bounding Box)')
        elif render_type == 'wireframe' or render_type == 'wireframe_2d':
            ax.view_init(elev=30, azim=45)  # Vista isométrica
            ax.set_title('STEP File - Wireframe View (Bounding Box)')
        else:  # 3d
            ax.view_init(elev=20, azim=45)  # Vista 3D
            ax.set_title('STEP File - 3D View (Bounding Box)')

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')

        # Convertir a imagen
        canvas = FigureCanvasAgg(fig)
        canvas.draw()

        # Obtener imagen como array
        buf = canvas.buffer_rgba()
        img_array = np.asarray(buf)

        # Convertir a PIL Image
        pil_image = Image.fromarray(img_array)

        # Convertir a PNG en memoria
        import io
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        plt.close(fig)  # Limpiar memoria

        return base64.b64encode(img_bytes.getvalue()).decode()

    except Exception as e:
        logger.error(f"Error generando vista previa STEP: {str(e)}")

        # Intentar usar el analizador externo para obtener información diagnóstica detallada
        try:
            logger.info("Calling external analyzer for detailed diagnostics...")
            analysis_result = call_external_step_analyzer(file_path)

            # El nuevo analizador siempre devuelve información útil, incluso en casos de "error"
            status = analysis_result.get("status", "unknown")

            # Estados que contienen información útil aunque no se pueda generar vista 3D
            informative_states = [
                "transfer_error_with_fallback",
                "shape_error_with_fallback",
                "read_error_with_fallback",
                "error_with_fallback",
                "fallback_only",
                "partial_success_with_fallback"
            ]

            if status in informative_states:
                # Tenemos información diagnóstica detallada - crear respuesta informativa
                detailed_info = {
                    "error": analysis_result.get("error", "No se pudo generar vista 3D"),
                    "status": status,
                    "diagnostic_info": {
                        "step_metadata": analysis_result.get("step_metadata", {}),
                        "coordinate_bounds": analysis_result.get("coordinate_bounds", {}),
                        "structure_analysis": analysis_result.get("structure_analysis", {}),
                        "step_entities": analysis_result.get("step_entities", {}),
                        "content_summary": analysis_result.get("content_summary", {}),
                        "total_step_entities": analysis_result.get("total_step_entities", 0),
                        "file_complexity": analysis_result.get("structure_analysis", {}).get("file_complexity", "unknown")
                    },
                    "suggestions": analysis_result.get("suggestions", []),
                    "analysis_time_ms": analysis_result.get("analysis_time_ms", 0),
                    "message": "Archivo STEP válido con información detallada disponible - vista 3D no generada",
                    "file_readable": True,
                    "information_extracted": True,
                    "analysis_type": "comprehensive_diagnostic"
                }
                logger.info(f"Returning comprehensive diagnostic info for {status}")
                raise HTTPException(200, json.dumps(detailed_info))

            elif "error" in analysis_result:
                # Error sin información útil
                error_msg = analysis_result["error"]

                # Si hay información de fallback, crear un error detallado
                if "fallback_analysis" in analysis_result:
                    fallback = analysis_result["fallback_analysis"]
                    detailed_error = {
                        "error": error_msg,
                        "fallback_analysis": fallback,
                        "diagnostic_available": True,
                        "analysis_type": "external_analyzer",
                        "original_error": str(e)
                    }
                    logger.info("Raising detailed error with fallback analysis")
                    raise HTTPException(500, json.dumps(detailed_error))
                else:
                    # Sin información de fallback, pero aún más detallado que el error original
                    detailed_error = {
                        "error": error_msg,
                        "diagnostic_available": False,
                        "analysis_type": "external_analyzer",
                        "original_error": str(e)
                    }
                    raise HTTPException(500, json.dumps(detailed_error))
            else:
                # El analizador externo tuvo éxito en el análisis pero falló la generación de imagen
                # Esto significa que el archivo es válido pero tenemos un problema de visualización
                detailed_error = {
                    "error": f"El archivo STEP es válido pero no se pudo generar la vista previa: {str(e)}",
                    "file_valid": True,
                    "analysis_successful": True,
                    "analysis_result": analysis_result,
                    "visualization_error": str(e),
                    "diagnostic_available": True
                }
                raise HTTPException(500, json.dumps(detailed_error))

        except HTTPException:
            # Re-raise HTTPException para mantener el código de estado
            raise
        except Exception as analyzer_error:
            logger.error(f"External analyzer also failed: {analyzer_error}")
            # Si el analizador externo también falla, usar el error original
            fallback_error = {
                "error": f"Error generando vista previa: {str(e)}",
                "analyzer_error": str(analyzer_error),
                "diagnostic_available": False,
                "original_error": str(e)
            }
            raise HTTPException(500, json.dumps(fallback_error))

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
            "success": True,
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
