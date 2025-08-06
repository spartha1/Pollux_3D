#!/usr/bin/env python3
# Script de prueba para verificar el procesamiento de archivos STEP

import requests
import json
import base64
import os

def test_step_processing():
    print("🧪 PROBANDO PROCESAMIENTO DE ARCHIVOS STEP")
    print("==========================================")

    # URL del servidor
    server_url = "http://localhost:8052"

    # Archivo STEP de prueba
    step_file = "/home/jerardo/Documents/Pollux3d/Pollux_3D/pythonocc-core-master/test/test_io/as1-oc-214.stp"

    if not os.path.exists(step_file):
        step_file = "/home/jerardo/Documents/Pollux3d/Pollux_3D/tests/test.step"

    if not os.path.exists(step_file):
        print("❌ No se encontró archivo STEP de prueba")
        return False

    print(f"📁 Usando archivo: {step_file}")

    # Probar diferentes tipos de render
    render_types = ['2d', 'wireframe', '3d']

    for render_type in render_types:
        print(f"\n🔄 Probando render tipo: {render_type}")

        try:
            # Preparar payload
            payload = {
                'file_id': 'test_001',
                'file_path': step_file,
                'render_type': render_type
            }

            # Hacer request
            response = requests.post(
                f"{server_url}/generate_preview",
                json=payload,
                timeout=30
            )

            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('image_data'):
                    print(f"   ✅ {render_type}: Imagen generada correctamente")
                    print(f"   📏 Tamaño imagen: {len(data['image_data'])} caracteres base64")

                    # Guardar imagen para verificación
                    img_data = base64.b64decode(data['image_data'])
                    with open(f"test_step_{render_type}.png", "wb") as f:
                        f.write(img_data)
                    print(f"   💾 Imagen guardada: test_step_{render_type}.png")
                else:
                    print(f"   ❌ {render_type}: Respuesta sin imagen")
                    print(f"   📄 Respuesta: {data}")
            else:
                print(f"   ❌ {render_type}: Error HTTP {response.status_code}")
                print(f"   📄 Error: {response.text}")

        except Exception as e:
            print(f"   ❌ {render_type}: Excepción - {e}")

    print("\n🎉 Prueba completada")
    return True

if __name__ == "__main__":
    test_step_processing()
