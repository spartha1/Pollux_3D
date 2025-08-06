#!/usr/bin/env python3
"""
Basic Preview Server for STL files
Minimal version for immediate functionality
"""

import os
import sys
import base64
import io
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="STL Preview Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PreviewRequest(BaseModel):
    file_id: str
    file_path: str
    preview_type: str = "2d"
    width: int = 800
    height: int = 600
    background_color: str = "#FFFFFF"
    file_type: str = "stl"

class PreviewResponse(BaseModel):
    success: bool
    message: str
    image_data: Optional[str] = None

def generate_stl_preview(file_path: str, preview_type: str = "2d", width: int = 800, height: int = 600) -> str:
    """Generate a preview image from STL file using matplotlib."""
    try:
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        import numpy as np
        from stl import mesh

        # Convert relative path to absolute if needed
        if not os.path.isabs(file_path):
            # Assume file is relative to Laravel storage/app
            base_path = Path(__file__).parent.parent.parent.parent
            storage_path = base_path / "storage" / "app" / file_path
            file_path = str(storage_path)

        logger.info(f"Loading STL file: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"STL file not found: {file_path}")

        # Load STL file
        stl_mesh = mesh.Mesh.from_file(file_path)

        # Create figure and axis
        fig = plt.figure(figsize=(width/100, height/100))

        if preview_type in ["3d", "wireframe"]:
            ax = fig.add_subplot(111, projection='3d')

            # Get the mesh vectors
            vectors = stl_mesh.vectors

            if preview_type == "wireframe":
                # Create wireframe by plotting edges
                for triangle in vectors:
                    # Plot each edge of the triangle
                    x = [triangle[0][0], triangle[1][0]]
                    y = [triangle[0][1], triangle[1][1]]
                    z = [triangle[0][2], triangle[1][2]]
                    ax.plot3D(x, y, z, 'b-', alpha=0.6, linewidth=0.5)

                    x = [triangle[1][0], triangle[2][0]]
                    y = [triangle[1][1], triangle[2][1]]
                    z = [triangle[1][2], triangle[2][2]]
                    ax.plot3D(x, y, z, 'b-', alpha=0.6, linewidth=0.5)

                    x = [triangle[2][0], triangle[0][0]]
                    y = [triangle[2][1], triangle[0][1]]
                    z = [triangle[2][2], triangle[0][2]]
                    ax.plot3D(x, y, z, 'b-', alpha=0.6, linewidth=0.5)
            else:
                # 3D solid view
                # Create a collection of 3D polygons
                from mpl_toolkits.mplot3d.art3d import Poly3DCollection

                poly3d = Poly3DCollection(vectors, alpha=0.7, facecolor='lightblue', edgecolor='black')
                ax.add_collection3d(poly3d)

            # Set equal aspect ratio
            max_range = np.array([
                vectors[:,:,0].max() - vectors[:,:,0].min(),
                vectors[:,:,1].max() - vectors[:,:,1].min(),
                vectors[:,:,2].max() - vectors[:,:,2].min()
            ]).max() / 2.0

            mid_x = (vectors[:,:,0].max() + vectors[:,:,0].min()) * 0.5
            mid_y = (vectors[:,:,1].max() + vectors[:,:,1].min()) * 0.5
            mid_z = (vectors[:,:,2].max() + vectors[:,:,2].min()) * 0.5

            ax.set_xlim(mid_x - max_range, mid_x + max_range)
            ax.set_ylim(mid_y - max_range, mid_y + max_range)
            ax.set_zlim(mid_z - max_range, mid_z + max_range)

        else:
            # 2D projection (top view)
            ax = fig.add_subplot(111)

            vectors = stl_mesh.vectors

            # Project to XY plane (top view)
            for triangle in vectors:
                x_coords = [triangle[0][0], triangle[1][0], triangle[2][0], triangle[0][0]]
                y_coords = [triangle[0][1], triangle[1][1], triangle[2][1], triangle[0][1]]
                ax.plot(x_coords, y_coords, 'b-', alpha=0.3, linewidth=0.5)

            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)

        ax.set_title(f'STL Preview - {preview_type.upper()}')

        # Save to BytesIO
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        buffer.seek(0)

        # Convert to base64
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        plt.close(fig)
        logger.info(f"Successfully generated {preview_type} preview")

        return image_data

    except Exception as e:
        logger.error(f"Error generating STL preview: {str(e)}")
        raise

@app.get("/")
async def root():
    return {"message": "STL Preview Service is running", "status": "ok"}

@app.post("/generate_preview", response_model=PreviewResponse)
async def generate_preview(request: PreviewRequest):
    """Generate a preview image for an STL file."""
    try:
        logger.info(f"Generating preview for file: {request.file_path}, type: {request.preview_type}")

        # Handle wireframe_2d as wireframe
        preview_type = request.preview_type
        if preview_type == "wireframe_2d":
            preview_type = "wireframe"

        image_data = generate_stl_preview(
            file_path=request.file_path,
            preview_type=preview_type,
            width=request.width,
            height=request.height
        )

        return PreviewResponse(
            success=True,
            message="Preview generated successfully",
            image_data=image_data
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting STL Preview Server on port 8052...")
    uvicorn.run(app, host="0.0.0.0", port=8052, log_level="info")
