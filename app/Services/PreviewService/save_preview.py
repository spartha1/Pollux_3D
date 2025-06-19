import base64
import sys
from PIL import Image
import io
import os

# Configurar la salida para que no se bufferee
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Nombre del archivo de salida
output_file = "preview_test.png"

try:
    print("Leyendo imagen base64...")
    # Lee la imagen base64 desde la entrada estándar
    import json

    # Leer la entrada línea por línea para encontrar el base64
    base64_data = ""
    for line in sys.stdin:
        if "image_data" in line:
            # Intentar extraer directamente el valor de image_data
            base64_data = line.strip()
            break

    print(f"Datos leídos: {base64_data[:50]}...")  # Mostrar los primeros 50 caracteres

    # Si no encontramos datos, salir
    if not base64_data:
        raise ValueError("No se encontraron datos base64 en la entrada")

    print("Decodificando datos base64...")
    # Decodificar base64 a bytes
    image_data = base64.b64decode(base64_data)

    print("Creando imagen...")
    # Crear imagen desde bytes
    image = Image.open(io.BytesIO(image_data))

    print(f"Guardando imagen como {output_file}...")
    # Guardar imagen
    image.save(output_file)

    print(f"¡Imagen guardada! Dimensiones: {image.size}")

    # Intentar abrir la imagen
    print("Abriendo imagen...")
    image.show()

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    print(traceback.format_exc())

input("Presiona Enter para continuar...")
