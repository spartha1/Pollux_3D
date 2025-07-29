import base64
import os

# Datos base64 del preview generado anteriormente (recortado para brevedad)
base64_data = """iVBORw0KGgoAAAANSUhEUgAABEYAAAOGCAYAAAB+VpbQAAAAOXRFWHRTb2Z0d2FyZQBNYXRwbG90bGliIHZlcnNpb24zLjkuMiwgaHR0cHM6Ly9tYXRwbG90bGliLm9yZy8hTI83AAAACXBIWXMAAA9hAAAPYQGoP6dpAAEAAElEQVR4nOzdSZBs2V3n+/8594zIe++t2Zps7N07+4rnnnsOY8wxMAYjjNE="  # Truncated for brevity

# Crear directorio si no existe
preview_dir = r"c:\xampp\htdocs\laravel\Pollux_3D\public\storage\previews\58"
os.makedirs(preview_dir, exist_ok=True)

# Decodificar y guardar la imagen
try:
    # Decodificar base64
    image_data = base64.b64decode(base64_data)
    
    # Guardar archivo
    preview_path = os.path.join(preview_dir, "stl_2d_preview_f0f90935.png")
    with open(preview_path, 'wb') as f:
        f.write(image_data)
    
    print(f"Preview guardado exitosamente en: {preview_path}")
    print(f"Tamaño del archivo: {len(image_data)} bytes")
    
except Exception as e:
    print(f"Error al guardar preview: {e}")
