#!/usr/bin/env python3
"""
Script de limpieza automática para el sistema Pollux 3D
Utiliza los resultados de la auditoría para limpiar archivos duplicados y problemáticos
"""

import json
import shutil
import os
from pathlib import Path
from datetime import datetime
import argparse

class SystemCleaner:
    def __init__(self, root_path, audit_report_path=None, dry_run=True):
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        self.backup_dir = None
        self.report = None
        self.cleanup_log = {
            'timestamp': datetime.now().isoformat(),
            'actions_taken': [],
            'files_removed': [],
            'space_freed': 0,
            'errors': []
        }

        if audit_report_path:
            self.load_audit_report(audit_report_path)

    def load_audit_report(self, report_path):
        """Carga el reporte de auditoría"""
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                self.report = json.load(f)
            print(f"✅ Reporte de auditoría cargado: {report_path}")
        except Exception as e:
            print(f"❌ Error cargando reporte: {e}")
            self.report = None

    def create_backup_dir(self):
        """Crea directorio de backup antes de la limpieza"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.root_path / f"cleanup_backup_{timestamp}"

        if not self.dry_run:
            self.backup_dir.mkdir(exist_ok=True)
            print(f"📁 Directorio de backup creado: {self.backup_dir}")
        else:
            print(f"📁 [DRY RUN] Se crearía directorio de backup: {self.backup_dir}")

    def backup_file(self, file_path):
        """Hace backup de un archivo antes de eliminarlo"""
        if self.dry_run:
            print(f"📋 [DRY RUN] Se haría backup de: {file_path}")
            return True

        try:
            relative_path = file_path.relative_to(self.root_path)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            self.cleanup_log['errors'].append(f"Error backup {file_path}: {e}")
            return False

    def remove_file(self, file_path, reason):
        """Elimina un archivo con backup"""
        file_size = 0
        try:
            file_size = file_path.stat().st_size
        except:
            pass

        if self.backup_file(file_path):
            if not self.dry_run:
                try:
                    file_path.unlink()
                    self.cleanup_log['files_removed'].append(str(file_path))
                    self.cleanup_log['space_freed'] += file_size
                    print(f"🗑️  Eliminado: {file_path} ({reason})")
                except Exception as e:
                    self.cleanup_log['errors'].append(f"Error eliminando {file_path}: {e}")
            else:
                print(f"🗑️  [DRY RUN] Se eliminaría: {file_path} ({reason})")
                self.cleanup_log['space_freed'] += file_size

    def clean_duplicate_files(self):
        """Limpia archivos duplicados basándose en el reporte de auditoría"""
        if not self.report or 'system_audit' not in self.report:
            print("⚠️ No hay reporte de auditoría disponible para limpiar duplicados")
            return

        print("\n🔄 Limpiando archivos duplicados...")
        duplicates = self.report['system_audit'].get('duplicate_files', {}).get('by_content', {})

        for file_hash, file_list in duplicates.items():
            if len(file_list) <= 1:
                continue

            # Ordenar por fecha de modificación (mantener el más reciente)
            sorted_files = sorted(file_list, key=lambda x: x['modified'], reverse=True)
            files_to_keep = [sorted_files[0]]  # Mantener el más reciente
            files_to_remove = sorted_files[1:]  # Eliminar los demás

            print(f"\n📁 Grupo de duplicados (hash: {file_hash[:8]}...):")
            print(f"   ✅ Mantener: {files_to_keep[0]['path']}")

            for file_info in files_to_remove:
                file_path = Path(file_info['path'])
                if file_path.exists():
                    self.remove_file(file_path, "archivo duplicado")

    def clean_empty_files(self):
        """Elimina archivos vacíos"""
        print("\n📄 Limpiando archivos vacíos...")

        # Buscar archivos vacíos
        for file_path in self.root_path.rglob('*'):
            if file_path.is_file():
                try:
                    if file_path.stat().st_size == 0:
                        # Verificar que no sea un archivo especial (como .gitkeep)
                        if file_path.name not in ['.gitkeep', '.gitignore', '__init__.py']:
                            self.remove_file(file_path, "archivo vacío")
                except Exception:
                    pass

    def clean_backup_files(self):
        """Elimina archivos de backup evidentes"""
        print("\n💾 Limpiando archivos de backup...")

        backup_patterns = [
            '*.bak',
            '*.backup',
            '*~',
            '*.tmp',
            '*_backup*',
            '*_old*',
            '*.orig'
        ]

        for pattern in backup_patterns:
            for file_path in self.root_path.rglob(pattern):
                if file_path.is_file():
                    self.remove_file(file_path, f"archivo de backup ({pattern})")

    def clean_problematic_scripts(self):
        """Limpia scripts problemáticos basándose en el reporte"""
        if not self.report or 'system_audit' not in self.report:
            print("⚠️ No hay reporte disponible para limpiar scripts problemáticos")
            return

        print("\n🔧 Limpiando scripts problemáticos...")

        # Limpiar scripts de build problemáticos
        build_scripts = self.report['system_audit'].get('build_scripts', {})
        for script_path, analysis in build_scripts.items():
            if analysis.get('status') == 'empty' and analysis.get('lines', 0) == 0:
                file_path = Path(script_path)
                if file_path.exists():
                    self.remove_file(file_path, "script vacío")

        # Limpiar scripts PHP problemáticos
        php_scripts = self.report['system_audit'].get('php_scripts', {})
        for script_path, analysis in php_scripts.items():
            if analysis.get('status') == 'empty' and analysis.get('lines', 0) == 0:
                file_path = Path(script_path)
                if file_path.exists():
                    self.remove_file(file_path, "script PHP vacío")

    def clean_redundant_build_scripts(self):
        """Identifica y sugiere limpieza de scripts de build redundantes"""
        if not self.report or 'system_audit' not in self.report:
            return

        print("\n🔧 Analizando scripts de build redundantes...")

        build_scripts = self.report['system_audit'].get('build_scripts', {})

        # Agrupar scripts por tipo/propósito
        rebuild_scripts = []
        setup_scripts = []

        for script_path, analysis in build_scripts.items():
            script_name = Path(script_path).name.lower()
            if 'rebuild' in script_name:
                rebuild_scripts.append((script_path, analysis))
            elif 'setup' in script_name:
                setup_scripts.append((script_path, analysis))

        # Sugerir limpieza de rebuilds redundantes
        if len(rebuild_scripts) > 3:
            print(f"📋 Se encontraron {len(rebuild_scripts)} scripts de rebuild:")

            # Mantener los que parecen más funcionales
            functional_rebuilds = [s for s in rebuild_scripts if s[1].get('status') == 'functional']
            non_functional = [s for s in rebuild_scripts if s[1].get('status') != 'functional']

            for script_path, analysis in non_functional:
                if analysis.get('lines', 0) < 10 or analysis.get('status') in ['empty', 'error']:
                    file_path = Path(script_path)
                    if file_path.exists():
                        self.remove_file(file_path, "script de rebuild redundante/problemático")

    def clean_large_unnecessary_files(self):
        """Identifica archivos grandes que podrían ser innecesarios"""
        if not self.report or 'system_audit' not in self.report:
            return

        print("\n📁 Analizando archivos grandes...")

        large_files = self.report['system_audit'].get('large_files', [])

        for file_info in large_files:
            file_path = Path(file_info['path'])
            if not file_path.exists():
                continue

            size_mb = file_info['size_mb']
            extension = file_info.get('extension', '').lower()

            # Archivos que típicamente pueden ser eliminados si son muy grandes
            if extension in ['.log', '.tmp', '.cache'] and size_mb > 50:
                self.remove_file(file_path, f"archivo temporal grande ({size_mb}MB)")
            elif extension in ['.zip', '.tar', '.gz'] and size_mb > 100:
                # Solo sugerir, no eliminar automáticamente
                print(f"💡 Archivo grande encontrado: {file_path} ({size_mb}MB) - revisar manualmente")

    def generate_suggestions(self):
        """Genera sugerencias adicionales basadas en el análisis"""
        suggestions = []

        if self.report:
            # Sugerir consolidación de scripts
            build_count = len(self.report['system_audit'].get('build_scripts', {}))
            if build_count > 5:
                suggestions.append(f"Considerar consolidar {build_count} scripts de build en uno principal")

            # Sugerir actualización de dependencias
            deps = self.report.get('functional_tests', {}).get('dependencies', {})
            missing = [dep for dep, info in deps.items() if info.get('status') == 'not_found']
            if missing:
                suggestions.append(f"Instalar dependencias faltantes: {', '.join(missing)}")

        return suggestions

    def run_cleanup(self, operations=None):
        """Ejecuta la limpieza completa o operaciones específicas"""
        if operations is None:
            operations = ['duplicates', 'empty', 'backups', 'problematic', 'redundant']

        print(f"🧹 Iniciando limpieza del sistema...")
        print(f"📂 Directorio: {self.root_path}")
        print(f"🎯 Modo: {'DRY RUN (simulación)' if self.dry_run else 'EJECUCIÓN REAL'}")
        print("-" * 60)

        self.create_backup_dir()

        # Ejecutar operaciones de limpieza
        if 'duplicates' in operations:
            self.clean_duplicate_files()

        if 'empty' in operations:
            self.clean_empty_files()

        if 'backups' in operations:
            self.clean_backup_files()

        if 'problematic' in operations:
            self.clean_problematic_scripts()

        if 'redundant' in operations:
            self.clean_redundant_build_scripts()

        if 'large' in operations:
            self.clean_large_unnecessary_files()

        # Generar sugerencias
        suggestions = self.generate_suggestions()

        # Mostrar resumen
        self.print_cleanup_summary(suggestions)

        # Guardar log
        self.save_cleanup_log()

        return self.cleanup_log

    def print_cleanup_summary(self, suggestions):
        """Imprime resumen de la limpieza"""
        print("\n" + "="*60)
        print("🧹 RESUMEN DE LIMPIEZA")
        print("="*60)

        files_removed = len(self.cleanup_log['files_removed'])
        space_freed_mb = self.cleanup_log['space_freed'] / (1024 * 1024)
        errors = len(self.cleanup_log['errors'])

        print(f"📁 Archivos {'que se eliminarían' if self.dry_run else 'eliminados'}: {files_removed}")
        print(f"💾 Espacio {'que se liberaría' if self.dry_run else 'liberado'}: {space_freed_mb:.2f} MB")
        print(f"❌ Errores: {errors}")

        if errors > 0:
            print("\n⚠️ ERRORES ENCONTRADOS:")
            for error in self.cleanup_log['errors']:
                print(f"   • {error}")

        if suggestions:
            print("\n💡 SUGERENCIAS ADICIONALES:")
            for suggestion in suggestions:
                print(f"   • {suggestion}")

        if not self.dry_run and self.backup_dir:
            print(f"\n📁 Backup disponible en: {self.backup_dir}")

        print("\n" + "="*60)

    def save_cleanup_log(self):
        """Guarda el log de limpieza"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.root_path / f"cleanup_log_{timestamp}.json"

        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.cleanup_log, f, indent=2, ensure_ascii=False)
            print(f"📄 Log de limpieza guardado: {log_file}")
        except Exception as e:
            print(f"❌ Error guardando log: {e}")

def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description="Limpieza automática del sistema Pollux 3D")
    parser.add_argument("--path", default=".", help="Directorio a limpiar (default: directorio actual)")
    parser.add_argument("--report", help="Archivo de reporte de auditoría JSON")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Ejecutar en modo simulación (default)")
    parser.add_argument("--execute", action="store_true",
                       help="Ejecutar limpieza real (anula --dry-run)")
    parser.add_argument("--operations", nargs="+",
                       choices=['duplicates', 'empty', 'backups', 'problematic', 'redundant', 'large'],
                       help="Operaciones específicas a ejecutar")

    args = parser.parse_args()

    # Determinar modo de ejecución
    dry_run = not args.execute

    # Buscar reporte automáticamente si no se especifica
    root_path = Path(args.path)
    report_path = args.report

    if not report_path:
        # Buscar reportes recientes
        report_dirs = list(root_path.glob("audit_reports_*"))
        if report_dirs:
            latest_dir = max(report_dirs, key=lambda x: x.stat().st_mtime)
            potential_report = latest_dir / "consolidated_report.json"
            if potential_report.exists():
                report_path = potential_report
                print(f"📄 Usando reporte encontrado: {report_path}")

    # Crear y ejecutar limpiador
    cleaner = SystemCleaner(root_path, report_path, dry_run)

    if dry_run:
        print("⚠️ MODO SIMULACIÓN - No se eliminarán archivos realmente")
        print("   Use --execute para ejecutar la limpieza real")
    else:
        print("🚨 MODO EJECUCIÓN REAL - Los archivos se eliminarán")
        response = input("¿Está seguro de que desea continuar? (sí/no): ")
        if response.lower() not in ['sí', 'si', 'yes', 'y']:
            print("❌ Limpieza cancelada")
            return

    # Ejecutar limpieza
    cleaner.run_cleanup(args.operations)

if __name__ == "__main__":
    main()
