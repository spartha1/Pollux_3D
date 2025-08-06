#!/usr/bin/env python3
"""
Script de limpieza de duplicados - Versión no interactiva para pruebas
"""

import json
from pathlib import Path

def load_audit_report():
    """Busca y carga el reporte de auditoría más reciente"""
    reports_dir = Path(".")
    pattern = "audit_reports_*"

    # Buscar directorios de reportes
    report_dirs = [d for d in reports_dir.glob(pattern) if d.is_dir()]
    if not report_dirs:
        print("❌ No se encontraron reportes de auditoría")
        return None

    # Usar el más reciente
    latest_dir = max(report_dirs, key=lambda x: x.stat().st_mtime)
    report_file = latest_dir / "consolidated_report.json"
    print(f"📄 Usando reporte: {report_file}")

    if not report_file.exists():
        print("❌ No se encontró consolidated_report.json")
        return None

    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error cargando reporte: {e}")
        return None

def main():
    """Función principal"""
    print("🧹 ANÁLISIS DE DUPLICADOS")
    print("="*60)

    # Cargar reporte
    report = load_audit_report()
    if not report:
        return

    # Verificar estructura
    print("🔍 Analizando estructura del reporte...")

    if 'system_audit' in report:
        print("✅ Encontrada sección 'system_audit'")
        if 'duplicate_files' in report['system_audit']:
            print("✅ Encontrada sección 'duplicate_files'")
            if 'by_content' in report['system_audit']['duplicate_files']:
                duplicate_data = report['system_audit']['duplicate_files']['by_content']
                print(f"✅ Encontrados {len(duplicate_data)} grupos de duplicados")

                # Mostrar primeros 3 grupos como ejemplo
                count = 0
                for hash_key, file_group in duplicate_data.items():
                    if count >= 3:
                        break
                    print(f"\n📁 Grupo {count+1} (hash: {hash_key[:8]}...): {len(file_group)} archivos")
                    for i, file_obj in enumerate(file_group[:2]):  # Solo mostrar primeros 2
                        file_path = file_obj['path'] if isinstance(file_obj, dict) else file_obj
                        action = "✅ Mantener" if i == 0 else "🗑️ Duplicado"
                        print(f"   {action}: {file_path}")
                    if len(file_group) > 2:
                        print(f"   ... y {len(file_group)-2} más")
                    count += 1
            else:
                print("❌ No se encontró 'by_content' en duplicate_files")
        else:
            print("❌ No se encontró 'duplicate_files' en system_audit")
    else:
        print("❌ No se encontró 'system_audit' en el reporte")
        print("🔍 Claves disponibles en el reporte:")
        for key in report.keys():
            print(f"   - {key}")

if __name__ == "__main__":
    main()
