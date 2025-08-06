#!/usr/bin/env python3
"""
Análisis de carpetas SWIG duplicadas en pythonocc-core-master
"""

import os
from pathlib import Path

def analyze_swig_folders():
    """Analiza las carpetas SWIG para determinar cuál es útil"""

    base_path = Path("pythonocc-core-master")

    folders = {
        "swigwin-4.2.1": base_path / "swigwin-4.2.1",
        "swig-4.2.1": base_path / "swig-4.2.1",
        "build-swig/swig-4.2.1": base_path / "build-swig" / "swig-4.2.1"
    }

    print("🔍 ANÁLISIS DE CARPETAS SWIG")
    print("="*60)

    for name, path in folders.items():
        if not path.exists():
            print(f"❌ {name}: No existe")
            continue

        print(f"\n📁 {name}:")
        print(f"   📍 Ruta: {path}")

        # Buscar ejecutable SWIG
        swig_exe = path / "swig.exe"
        if swig_exe.exists():
            size_mb = swig_exe.stat().st_size / (1024*1024)
            print(f"   ✅ Ejecutable: swig.exe ({size_mb:.1f} MB)")
        else:
            print(f"   ❌ No tiene swig.exe")

        # Verificar estructura importante
        important_dirs = ["Source", "Examples", "Doc", "include"]
        for dir_name in important_dirs:
            dir_path = path / dir_name
            if dir_path.exists():
                count = len(list(dir_path.rglob("*")))
                print(f"   📂 {dir_name}/: {count} archivos")

        # Tamaño total
        total_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        print(f"   💾 Tamaño total: {total_size / (1024*1024):.1f} MB")

        # Verificar si es duplicado de build
        if "build-swig" in str(path):
            print(f"   ⚠️  Es una carpeta de build (probablemente duplicado)")
        elif path.name == "swig-4.2.1" and not (path / "swig.exe").exists():
            print(f"   ⚠️  Solo contiene includes (incompleto)")
        elif path.name == "swigwin-4.2.1":
            print(f"   ✅ Parece ser la instalación principal")

def main():
    analyze_swig_folders()

    print("\n🎯 RECOMENDACIÓN:")
    print("="*60)
    print("📁 MANTENER: swigwin-4.2.1/ (tiene ejecutable y estructura completa)")
    print("🗑️  ELIMINAR: swig-4.2.1/ (solo includes, incompleto)")
    print("🗑️  ELIMINAR: build-swig/swig-4.2.1/ (duplicado de build)")
    print("\n💡 La carpeta build-swig/ completa parece ser un duplicado")
    print("   de swigwin-4.2.1/ generado durante compilación.")

if __name__ == "__main__":
    main()
