#!/usr/bin/env python3
"""
Limpieza de carpetas SWIG innecesarias
"""

import shutil
from pathlib import Path
import os

def cleanup_swig_folders():
    """Elimina carpetas SWIG duplicadas e innecesarias"""

    base_path = Path("pythonocc-core-master")

    # Carpetas a eliminar
    folders_to_remove = [
        base_path / "swig-4.2.1",           # Solo includes, incompleta
        base_path / "build-swig",           # Todo el directorio build-swig (duplicado)
    ]

    # Carpeta funcional a mantener
    keep_folder = base_path / "swigwin-4.2.1"

    print("🧹 LIMPIEZA DE CARPETAS SWIG")
    print("="*60)

    # Verificar carpeta a mantener
    if keep_folder.exists():
        swig_exe = keep_folder / "swig.exe"
        if swig_exe.exists():
            print(f"✅ Manteniendo: {keep_folder} (funcional)")
        else:
            print(f"⚠️  ADVERTENCIA: {keep_folder} no tiene swig.exe")
    else:
        print(f"❌ ERROR: Carpeta principal {keep_folder} no existe!")
        return

    total_freed = 0

    print("\n🗑️  Eliminando carpetas innecesarias:")

    for folder in folders_to_remove:
        if folder.exists():
            # Calcular tamaño antes de eliminar
            folder_size = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())
            size_mb = folder_size / (1024*1024)

            try:
                print(f"   🗑️  Eliminando: {folder} ({size_mb:.1f} MB)")
                shutil.rmtree(folder)
                total_freed += folder_size
                print(f"   ✅ Eliminado exitosamente")
            except Exception as e:
                print(f"   ❌ Error eliminando {folder}: {e}")
        else:
            print(f"   ⚠️  No existe: {folder}")

    print("\n" + "="*60)
    print("📊 RESUMEN DE LIMPIEZA")
    print("="*60)
    print(f"💾 Espacio liberado: {total_freed / (1024*1024):.1f} MB")
    print(f"📁 Carpeta funcional mantenida: {keep_folder}")
    print("✅ Limpieza SWIG completada")

def main():
    cleanup_swig_folders()

if __name__ == "__main__":
    main()
