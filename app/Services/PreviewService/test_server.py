from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import base64
import io
from PIL import Image, ImageDraw, ImageFont

app = FastAPI()

class PreviewRequest(BaseModel):
    file_id: str
    file_path: str
    render_type: str = '2d'

@app.post("/preview")
async def generate_preview(request: PreviewRequest):
    """Generate preview for 3D files"""
    if not os.path.exists(request.file_path):
        raise HTTPException(404, f"File not found: {request.file_path}")

    # Crear una imagen de prueba
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)

    # Dibujar un rectángulo azul
    draw.rectangle([100, 100, 700, 500], outline='blue', width=5)

    # Dibujar diagonales rojas
    draw.line([100, 100, 700, 500], fill='red', width=2)
    draw.line([100, 500, 700, 100], fill='red', width=2)

    # Círculos verdes en las esquinas
    radius = 20
    for x, y in [(100, 100), (700, 100), (100, 500), (700, 500)]:
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], outline='green', width=3)

    # Texto simple en la parte superior e inferior
    draw.text((350, 50), "TEST PREVIEW", fill='black')
    draw.text((350, 550), f"Mode: {request.render_type}", fill='blue')

    # Convertir a base64
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    return {
        "file_id": request.file_id,
        "image_data": base64.b64encode(img_byte_arr).decode(),
        "render_type": request.render_type
    }

if __name__ == "__main__":
    print("Starting preview server on http://localhost:8088")
    print("Press Ctrl+C to stop the server")

    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8088,
        log_level="info",
        access_log=True,
        workers=1
    )
    server = uvicorn.Server(config)
    server.run()
