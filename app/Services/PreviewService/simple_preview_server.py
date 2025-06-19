print("Starting imports...")
try:
    from fastapi import FastAPI, HTTPException
    print("FastAPI imported")
    from pydantic import BaseModel
    print("Pydantic imported")
    import uvicorn
    print("Uvicorn imported")
    import os
    import base64
    import io
    from PIL import Image, ImageDraw, ImageFont
    print("All imports completed successfully")
except Exception as e:
    print(f"Import error: {str(e)}")
    import traceback
    print(traceback.format_exc())
    input("Press Enter to continue...")

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

    # Create a test image that's easy to see
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
