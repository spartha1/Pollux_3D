#!/usr/bin/env python3
"""
Test de Integración Laravel - Servidor Híbrido
Verifica que Laravel puede comunicarse correctamente con el servidor híbrido
"""

import requests
import json
import os
import time

print("=== TEST DE INTEGRACIÓN LARAVEL ===")
print()

# Configuración
SERVER_URL = "http://localhost:8052"
STL_FILE = r"C:\xampp\htdocs\laravel\Pollux_3D\c1bc34d4-df6e-4caa-900e-5a0d70b41c3c.STL"
PREVIEWS_DIR = r"C:\xampp\htdocs\laravel\Pollux_3D\app\storage\app\previews"

def test_server_health():
    """Test 1: Verificar que el servidor esté respondiendo"""
    print("1. Verificando salud del servidor...")
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Servidor saludable")
            print(f"   ✅ Status: {data['status']}")
            for dep, status in data['dependencies'].items():
                status_icon = "✅" if status else "❌"
                print(f"   {status_icon} {dep}: {status}")
            return True
        else:
            print(f"   ❌ Error de salud: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error conectando al servidor: {e}")
        return False

def test_stl_file_exists():
    """Test 2: Verificar que el archivo STL existe"""
    print("\n2. Verificando archivo STL...")
    if os.path.exists(STL_FILE):
        size = os.path.getsize(STL_FILE)
        print(f"   ✅ Archivo STL encontrado: {STL_FILE}")
        print(f"   ✅ Tamaño: {size:,} bytes")
        return True
    else:
        print(f"   ❌ Archivo STL no encontrado: {STL_FILE}")
        return False

def test_preview_generation():
    """Test 3: Generar preview usando el endpoint Laravel-compatible"""
    print("\n3. Probando generación de preview (endpoint Laravel)...")
    try:
        # Datos que Laravel envía al servidor
        payload = {
            "file_path": STL_FILE,
            "preview_type": "2d",
            "width": 800,
            "height": 600,
            "file_id": "test_laravel_integration",
            "background_color": "#FFFFFF",
            "file_type": "stl"
        }
        
        # Usar el endpoint con guión bajo (Laravel compatible)
        response = requests.post(f"{SERVER_URL}/generate_preview", 
                               json=payload, 
                               timeout=30,
                               headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Preview generado exitosamente")
            print(f"   ✅ Archivo: {data['preview_filename']}")
            print(f"   ✅ URL: {data['preview_url']}")
            print(f"   ✅ Generador: {data['generator']}")
            
            # Verificar que la imagen se creó
            preview_path = os.path.join(PREVIEWS_DIR, data['preview_filename'])
            if os.path.exists(preview_path):
                size = os.path.getsize(preview_path)
                print(f"   ✅ Imagen verificada: {size:,} bytes")
                return True, data['preview_filename']
            else:
                print(f"   ❌ Imagen no encontrada en: {preview_path}")
                return False, None
        else:
            print(f"   ❌ Error generando preview: {response.status_code}")
            print(f"   ❌ Respuesta: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Error en generación: {e}")
        return False, None

def test_preview_access(filename):
    """Test 4: Verificar acceso a la imagen generada"""
    print("\n4. Probando acceso a imagen generada...")
    try:
        response = requests.get(f"{SERVER_URL}/preview/{filename}", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Imagen accesible vía HTTP")
            print(f"   ✅ Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"   ✅ Tamaño descargado: {len(response.content):,} bytes")
            return True
        else:
            print(f"   ❌ Error accediendo imagen: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error accediendo imagen: {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Salud del servidor
    if test_server_health():
        tests_passed += 1
    
    # Test 2: Archivo STL
    if test_stl_file_exists():
        tests_passed += 1
    
    # Test 3: Generación de preview
    success, filename = test_preview_generation()
    if success:
        tests_passed += 1
        
        # Test 4: Acceso a imagen (solo si se generó)
        if test_preview_access(filename):
            tests_passed += 1
    
    # Resultado final
    print(f"\n=== RESULTADO FINAL ===")
    print(f"Tests pasados: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 ¡INTEGRACIÓN LARAVEL EXITOSA!")
        print("✅ Las vistas 2D se están generando correctamente")
        print("✅ Laravel puede comunicarse con el servidor híbrido")
        print("✅ El problema original está RESUELTO")
    else:
        print("❌ Algunos tests fallaron")
        print("🔧 Revisar la configuración")
    
    print()

if __name__ == "__main__":
    main()
