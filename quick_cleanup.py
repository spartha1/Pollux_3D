#!/usr/bin/env python3
"""
Script de limpieza rápida y segura para casos de emergencia
Evita problemas de recursión y nombres largos
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def safe_cleanup():
    """Limpieza rápida y segura sin riesgo de recursión"""
    root_path = Path.cwd()

    print("🧹 Limpieza rápida de emergencia")
    print(f"📂 Directorio: {root_path}")
    print("-" * 50)

    cleaned_files = 0
    freed_space = 0

    # 1. Eliminar directorios de backup problemáticos
    print("🗑️ Eliminando directorios de backup problemáticos...")
    for item in root_path.iterdir():
        if item.is_dir() and item.name.startswith('cleanup_backup_'):
            try:
                size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                shutil.rmtree(item)
                print(f"   ✅ Eliminado: {item.name} ({size / (1024*1024):.1f}MB)")
                cleaned_files += 1
                freed_space += size
            except Exception as e:
                print(f"   ❌ Error eliminando {item.name}: {e}")

    # 2. Eliminar archivos vacíos evidentes
    print("\n📄 Eliminando archivos vacíos...")
    for pattern in ['*.ps1', '*.php', '*.bat', '*.cmd']:
        for file_path in root_path.glob(pattern):
            if file_path.is_file() and file_path.stat().st_size == 0:
                try:
                    file_path.unlink()
                    print(f"   ✅ Eliminado archivo vacío: {file_path.name}")
                    cleaned_files += 1
                except Exception as e:
                    print(f"   ❌ Error eliminando {file_path.name}: {e}")

    # 3. Eliminar archivos de backup evidentes
    print("\n💾 Eliminando archivos de backup...")
    backup_patterns = ['*.bak', '*.backup', '*~', '*.tmp', '*.orig']
    for pattern in backup_patterns:
        for file_path in root_path.rglob(pattern):
            # Evitar directorios problemáticos
            if any(part.startswith(('cleanup_backup_', 'audit_reports_', '.git'))
                   for part in file_path.parts):
                continue

            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    print(f"   ✅ Eliminado backup: {file_path.name}")
                    cleaned_files += 1
                    freed_space += size
                except Exception as e:
                    print(f"   ❌ Error eliminando {file_path.name}: {e}")

    # 4. Eliminar logs de cleanup muy grandes
    print("\n📋 Limpiando logs grandes...")
    for log_file in root_path.glob('cleanup_log_*.json'):
        if log_file.stat().st_size > 1024 * 1024:  # > 1MB
            try:
                size = log_file.stat().st_size
                log_file.unlink()
                print(f"   ✅ Eliminado log grande: {log_file.name} ({size / (1024*1024):.1f}MB)")
                cleaned_files += 1
                freed_space += size
            except Exception as e:
                print(f"   ❌ Error eliminando {log_file.name}: {e}")

    # Resumen
    print("\n" + "="*50)
    print("📊 RESUMEN DE LIMPIEZA RÁPIDA")
    print("="*50)
    print(f"🗑️ Archivos/directorios eliminados: {cleaned_files}")
    print(f"💾 Espacio liberado: {freed_space / (1024*1024):.1f}MB")
    print("✅ Sistema listo para auditoría completa")
    print("="*50)

if __name__ == "__main__":
    safe_cleanup()
