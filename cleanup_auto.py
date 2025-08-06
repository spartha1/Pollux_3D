#!/usr/bin/env python3
"""
Script de limpieza automática de duplicados - Ejecuta directamente
"""

import json
from pathlib import Path

def clean_selected_duplicates():
    """Limpia duplicados seleccionados automáticamente"""
    # Cargar reporte
    reports_dir = Path(".")
    pattern = "audit_reports_*"
    report_dirs = [d for d in reports_dir.glob(pattern) if d.is_dir()]

    if not report_dirs:
        print("❌ No se encontraron reportes")
        return

    latest_dir = max(report_dirs, key=lambda x: x.stat().st_mtime)
    report_file = latest_dir / "consolidated_report.json"

    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)

    duplicate_data = report['system_audit']['duplicate_files']['by_content']

    print("🧹 LIMPIEZA AUTOMÁTICA DE DUPLICADOS")
    print("="*60)
    print(f"🔄 Procesando {len(duplicate_data)} grupos de duplicados...")

    removed_count = 0
    space_freed = 0
    errors = 0

    for hash_key, file_group in duplicate_data.items():
        if len(file_group) < 2:
            continue

        # Mantener el primer archivo, eliminar el resto
        files_to_remove = file_group[1:]

        print(f"\n📁 Grupo (hash: {hash_key[:8]}...): {len(file_group)} archivos")

        keep_file = file_group[0]['path']
        print(f"   ✅ Mantener: {keep_file}")

        for file_obj in files_to_remove:
            try:
                file_path = file_obj['path']
                file_obj_path = Path(file_path)

                if file_obj_path.exists():
                    file_size = file_obj_path.stat().st_size
                    file_obj_path.unlink()
                    print(f"   🗑️ Eliminado: {file_path} ({file_size:,} bytes)")
                    removed_count += 1
                    space_freed += file_size
                else:
                    print(f"   ⚠️ No existe: {file_path}")

            except Exception as e:
                print(f"   ❌ Error: {file_path} - {e}")
                errors += 1

        # Límite de seguridad: solo procesar los primeros 50 grupos
        if removed_count >= 50:
            print(f"\n⚠️ Límite de seguridad alcanzado (50 archivos eliminados)")
            break

    print("\n" + "="*60)
    print("📊 RESUMEN DE LIMPIEZA")
    print("="*60)
    print(f"📁 Archivos eliminados: {removed_count}")
    print(f"💾 Espacio liberado: {space_freed / (1024*1024):.2f} MB")
    print(f"❌ Errores: {errors}")
    print("="*60)

if __name__ == "__main__":
    clean_selected_duplicates()
