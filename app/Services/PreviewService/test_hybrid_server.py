#!/usr/bin/env python3
"""
Script para probar el servidor híbrido con archivos reales
"""
import requests
import json
import os

def test_hybrid_server():
    """Probar el servidor híbrido con archivos reales"""
    base_url = "http://127.0.0.1:8052"
    
    print("=== PRUEBA DEL SERVIDOR HÍBRIDO ===\n")
    
    # 1. Verificar que el servidor responde
    print("1. Verificando servidor...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Servidor respondiendo correctamente")
            print(f"   Versión: {data['version']}")
            print(f"   Capacidades: {data['capabilities']}")
        else:
            print(f"❌ Error del servidor: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        return False
    
    # 2. Verificar health check
    print("\n2. Verificando dependencias...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health = response.json()
            print("✅ Health check exitoso")
            for dep, status in health['dependencies'].items():
                status_icon = "✅" if status else "❌"
                print(f"   {status_icon} {dep}: {status}")
        else:
            print(f"❌ Health check falló: {response.status_code}")
    except Exception as e:
        print(f"❌ Error en health check: {e}")
    
    # 3. Probar generación de preview STL
    print("\n3. Probando generación de preview STL...")
    stl_file = r"C:\xampp\htdocs\laravel\Pollux_3D\c1bc34d4-df6e-4caa-900e-5a0d70b41c3c.STL"
    
    if not os.path.exists(stl_file):
        print(f"❌ Archivo STL no encontrado: {stl_file}")
        return False
    
    try:
        preview_request = {
            "file_path": stl_file,
            "preview_type": "2d",
            "width": 800,
            "height": 600
        }
        
        response = requests.post(f"{base_url}/generate-preview", 
                               json=preview_request,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Preview STL generado exitosamente")
            print(f"   Archivo: {result['preview_filename']}")
            print(f"   URL: {result['preview_url']}")
            print(f"   Generador: {result['generator']}")
            
            # Verificar que la imagen existe
            preview_path = f"C:\\xampp\\htdocs\\laravel\\Pollux_3D\\app\\storage\\app\\previews\\{result['preview_filename']}"
            if os.path.exists(preview_path):
                file_size = os.path.getsize(preview_path)
                print(f"   ✅ Imagen generada: {file_size} bytes")
                return True
            else:
                print(f"   ❌ Imagen no encontrada en: {preview_path}")
                return False
        else:
            print(f"❌ Error generando preview: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en request de preview: {e}")
        return False

if __name__ == "__main__":
    success = test_hybrid_server()
    if success:
        print("\n🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print("   El servidor híbrido está funcionando correctamente")
        print("   Las vistas 2D se están generando con matplotlib")
    else:
        print("\n❌ Algunas pruebas fallaron")
