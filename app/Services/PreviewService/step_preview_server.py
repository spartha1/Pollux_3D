#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import base64
import io
from PIL import Image

# PythonOCC imports
try:
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Display.SimpleGui import init_display
    from OCC.Core.V3d import V3d_SpotLight
    from OCC.Core.Quantity import Quantity_Color, Quantity_NOC_WHITE, Quantity_TOC_RGB
    from OCC.Core.BRepTools import breptools_Clean
    from OCC.Core.AIS import AIS_WireFrame, AIS_Shaded
    OCC_AVAILABLE = True
except ImportError as e:
    print(f"PythonOCC import error: {e}")
    OCC_AVAILABLE = False

app = FastAPI()

class PreviewRequest(BaseModel):
    file_id: str
    file_path: str
    render_type: str = '2d'

def load_step_file(filepath):
    """Load a STEP file and return the shape."""
    reader = STEPControl_Reader()
    status = reader.ReadFile(filepath)

    if status != IFSelect_RetDone:
        raise RuntimeError(f"Error reading STEP file: {status}")

    reader.TransferRoot()
    return reader.OneShape()

def setup_display(width=800, height=600):
    """Initialize the display with white background."""
    display, start_display, add_menu, add_function_to_menu = init_display(
        size=(width, height)
    )
    display.View.SetBackgroundColor(Quantity_Color(1, 1, 1, Quantity_TOC_RGB))
    return display

def capture_view(display, shape, render_type):
    """Capture a view of the shape based on render_type."""
    display.EraseAll()

    # Clean the shape
    breptools_Clean(shape)

    if render_type == 'wireframe':
        # Wireframe view
        display.DisplayShape(shape, update=True, transparency=0.0,
                           mode=AIS_WireFrame)
    elif render_type == '2d':
        # 2D view (top view)
        display.DisplayShape(shape, update=False)
        display.View_Top()
        display.FitAll()
    else:  # '3d'
        # Full 3D rendered view
        display.DisplayShape(shape, update=False, mode=AIS_Shaded)
        display.View_Iso()

    # Add lighting
    light = V3d_SpotLight()
    display.View.SetLightOn(light)

    # Update and fit
    display.FitAll()

    # Capture the view
    return display.View.Capture()

@app.post("/preview")
async def generate_preview(request: PreviewRequest):
    """Generate preview for STEP files with different render types."""
    if not OCC_AVAILABLE:
        raise HTTPException(500, "PythonOCC not available")

    if not os.path.exists(request.file_path):
        raise HTTPException(404, f"File not found: {request.file_path}")

    try:
        # Load the STEP file
        shape = load_step_file(request.file_path)

        # Setup display
        display = setup_display()

        # Capture view based on render type
        image = capture_view(display, shape, request.render_type)

        # Convert to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return {
            "file_id": request.file_id,
            "image_data": image_base64,
            "render_type": request.render_type
        }

    except Exception as e:
        raise HTTPException(500, f"Error generating preview: {str(e)}")

if __name__ == "__main__":
    print("Starting STEP preview server on http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)
