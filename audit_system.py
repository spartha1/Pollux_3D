#!/usr/bin/env python3
"""
Sistema de Auditoría para Pollux 3D
Identifica archivos duplicados, scripts funcionales y genera un reporte completo
"""

import os
import hashlib
import json
import subprocess
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

class SystemAuditor:
    def __init__(self, root_path):
        self.root_path = Path(root_path)
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'root_path': str(root_path),
            'duplicate_files': {},
            'script_analysis': {},
            'build_scripts': {},
            'php_scripts': {},
            'config_files': {},
            'large_files': [],
            'issues': [],
            'recommendations': []
        }

    def calculate_file_hash(self, file_path):
        """Calcula hash MD5 de un archivo"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            return None

    def find_duplicate_files(self):
        """Encuentra archivos duplicados por contenido"""
        print("🔍 Buscando archivos duplicados...")

        file_hashes = defaultdict(list)
        duplicate_patterns = defaultdict(list)

        # Patrones de archivos que típicamente son duplicados
        suspicious_patterns = [
            r'rebuild.*\.ps1$',
            r'check_.*\.php$',
            r'build.*\.(bat|cmd|ps1)$',
            r'setup.*\.(bat|cmd|ps1)$',
            r'install.*\.ps1$',
            r'.*_backup.*',
            r'.*\.bak$',
            r'.*_new\d*\.',
            r'.*_fixed\.',
            r'.*_final\.'
        ]

        for root, dirs, files in os.walk(self.root_path):
            # Ignorar directorios comunes que contienen archivos temporales
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'build', 'dist']
                      and not d.startswith('cleanup_backup_')
                      and not d.startswith('audit_reports_')]

            for file in files:
                file_path = Path(root) / file

                # Agrupar por patrones sospechosos
                for pattern in suspicious_patterns:
                    if re.search(pattern, file, re.IGNORECASE):
                        duplicate_patterns[pattern].append(str(file_path))

                # Solo procesar archivos menores a 50MB para evitar archivos binarios grandes
                try:
                    if file_path.stat().st_size < 50 * 1024 * 1024:
                        file_hash = self.calculate_file_hash(file_path)
                        if file_hash:
                            file_hashes[file_hash].append({
                                'path': str(file_path),
                                'size': file_path.stat().st_size,
                                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })
                except Exception as e:
                    self.report['issues'].append(f"Error procesando {file_path}: {e}")

        # Filtrar solo archivos que aparecen más de una vez
        self.report['duplicate_files']['by_content'] = {
            hash_val: files for hash_val, files in file_hashes.items()
            if len(files) > 1
        }

        self.report['duplicate_files']['by_pattern'] = {
            pattern: files for pattern, files in duplicate_patterns.items()
            if len(files) > 1
        }

        return len(self.report['duplicate_files']['by_content'])

    def analyze_build_scripts(self):
        """Analiza scripts de build y su funcionalidad"""
        print("🔧 Analizando scripts de build...")

        build_scripts = []
        for pattern in ['**/*.ps1', '**/*.bat', '**/*.cmd', '**/*.sh']:
            build_scripts.extend(self.root_path.glob(pattern))

        for script in build_scripts:
            if any(keyword in script.name.lower() for keyword in ['build', 'rebuild', 'setup', 'install']):
                analysis = self.analyze_script(script)
                self.report['build_scripts'][str(script)] = analysis

    def analyze_php_scripts(self):
        """Analiza scripts PHP"""
        print("🐘 Analizando scripts PHP...")

        php_scripts = list(self.root_path.glob('**/*.php'))

        for script in php_scripts:
            if 'check_' in script.name or 'debug_' in script.name:
                analysis = self.analyze_script(script)
                self.report['php_scripts'][str(script)] = analysis

    def analyze_script(self, script_path):
        """Analiza un script individual"""
        analysis = {
            'name': script_path.name,
            'size': script_path.stat().st_size,
            'modified': datetime.fromtimestamp(script_path.stat().st_mtime).isoformat(),
            'lines': 0,
            'functions': [],
            'dependencies': [],
            'issues': [],
            'status': 'unknown'
        }

        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                analysis['lines'] = len(content.splitlines())

                # Buscar funciones (PowerShell)
                if script_path.suffix == '.ps1':
                    functions = re.findall(r'function\s+([a-zA-Z_][a-zA-Z0-9_-]*)', content, re.IGNORECASE)
                    analysis['functions'] = functions

                    # Buscar dependencias de conda/python
                    deps = re.findall(r'conda\s+install.*?([a-zA-Z_][a-zA-Z0-9_-]*)', content)
                    analysis['dependencies'].extend(deps)

                    # Verificar si parece funcional
                    if 'ErrorActionPreference' in content and 'Write-Host' in content:
                        analysis['status'] = 'functional'
                    elif content.strip() == '':
                        analysis['status'] = 'empty'
                        analysis['issues'].append('Archivo vacío')

                # Buscar funciones (PHP)
                elif script_path.suffix == '.php':
                    functions = re.findall(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
                    analysis['functions'] = functions

                    if '<?php' in content:
                        analysis['status'] = 'functional'
                    elif content.strip() == '':
                        analysis['status'] = 'empty'
                        analysis['issues'].append('Archivo vacío')

                # Verificar sintaxis básica
                if analysis['lines'] < 5 and analysis['status'] != 'empty':
                    analysis['issues'].append('Script muy corto, posible fragmento')

        except Exception as e:
            analysis['issues'].append(f"Error leyendo archivo: {e}")
            analysis['status'] = 'error'

        return analysis

    def find_large_files(self, min_size_mb=10):
        """Encuentra archivos grandes que podrían ser innecesarios"""
        print(f"📁 Buscando archivos mayores a {min_size_mb}MB...")

        for root, dirs, files in os.walk(self.root_path):
            for file in files:
                file_path = Path(root) / file
                try:
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    if size_mb > min_size_mb:
                        self.report['large_files'].append({
                            'path': str(file_path),
                            'size_mb': round(size_mb, 2),
                            'extension': file_path.suffix,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
                except Exception:
                    pass

    def analyze_config_files(self):
        """Analiza archivos de configuración"""
        print("⚙️ Analizando archivos de configuración...")

        config_patterns = ['**/*.json', '**/*.yml', '**/*.yaml', '**/*.env', '**/*.ini', '**/*.config']

        for pattern in config_patterns:
            for config_file in self.root_path.glob(pattern):
                if config_file.name in ['package.json', 'composer.json', 'environment.yml', '.env']:
                    analysis = {
                        'path': str(config_file),
                        'size': config_file.stat().st_size,
                        'modified': datetime.fromtimestamp(config_file.stat().st_mtime).isoformat(),
                        'status': 'found'
                    }

                    # Verificar si es válido
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if config_file.suffix == '.json':
                                json.loads(content)
                                analysis['status'] = 'valid_json'
                            elif content.strip():
                                analysis['status'] = 'valid'
                            else:
                                analysis['status'] = 'empty'
                    except Exception as e:
                        analysis['status'] = 'invalid'
                        analysis['error'] = str(e)

                    self.report['config_files'][config_file.name] = analysis

    def generate_recommendations(self):
        """Genera recomendaciones basadas en el análisis"""
        print("💡 Generando recomendaciones...")

        # Recomendaciones para archivos duplicados
        if self.report['duplicate_files']['by_content']:
            self.report['recommendations'].append({
                'category': 'duplicates',
                'priority': 'high',
                'title': 'Archivos duplicados encontrados',
                'description': f"Se encontraron {len(self.report['duplicate_files']['by_content'])} grupos de archivos duplicados",
                'action': 'Revisar y eliminar archivos duplicados innecesarios'
            })

        # Recomendaciones para scripts múltiples
        rebuild_scripts = [k for k in self.report['build_scripts'].keys() if 'rebuild' in k.lower()]
        if len(rebuild_scripts) > 3:
            self.report['recommendations'].append({
                'category': 'scripts',
                'priority': 'medium',
                'title': 'Múltiples scripts de rebuild',
                'description': f"Se encontraron {len(rebuild_scripts)} scripts de rebuild",
                'action': 'Consolidar en un script principal funcional'
            })

        # Recomendaciones para archivos grandes
        if self.report['large_files']:
            total_size = sum(f['size_mb'] for f in self.report['large_files'])
            self.report['recommendations'].append({
                'category': 'storage',
                'priority': 'medium',
                'title': 'Archivos grandes detectados',
                'description': f"Archivos grandes ocupan {total_size:.1f}MB de espacio",
                'action': 'Revisar si los archivos grandes son necesarios'
            })

        # Recomendaciones para scripts vacíos o con errores
        problematic_scripts = []
        for script_dict in [self.report['build_scripts'], self.report['php_scripts']]:
            for path, analysis in script_dict.items():
                if analysis['status'] in ['empty', 'error'] or analysis['issues']:
                    problematic_scripts.append(path)

        if problematic_scripts:
            self.report['recommendations'].append({
                'category': 'cleanup',
                'priority': 'low',
                'title': 'Scripts problemáticos',
                'description': f"Se encontraron {len(problematic_scripts)} scripts con problemas",
                'action': 'Limpiar o reparar scripts problemáticos'
            })

    def run_audit(self):
        """Ejecuta la auditoría completa"""
        print("🔍 Iniciando auditoría del sistema Pollux 3D...")
        print(f"📂 Directorio base: {self.root_path}")
        print("-" * 60)

        try:
            self.find_duplicate_files()
            self.analyze_build_scripts()
            self.analyze_php_scripts()
            self.find_large_files()
            self.analyze_config_files()
            self.generate_recommendations()

            print("-" * 60)
            print("✅ Auditoría completada")

        except Exception as e:
            print(f"❌ Error durante la auditoría: {e}")
            self.report['issues'].append(f"Error general: {e}")

        return self.report

    def save_report(self, output_file='audit_report.json'):
        """Guarda el reporte en un archivo JSON"""
        output_path = self.root_path / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        print(f"📄 Reporte guardado en: {output_path}")
        return output_path

    def print_summary(self):
        """Imprime un resumen del reporte"""
        print("\n" + "="*60)
        print("📊 RESUMEN DE AUDITORÍA")
        print("="*60)

        # Duplicados
        dup_content = len(self.report['duplicate_files']['by_content'])
        dup_pattern = len(self.report['duplicate_files']['by_pattern'])
        print(f"🔄 Archivos duplicados por contenido: {dup_content}")
        print(f"🔄 Patrones de archivos sospechosos: {dup_pattern}")

        # Scripts
        build_scripts = len(self.report['build_scripts'])
        php_scripts = len(self.report['php_scripts'])
        print(f"🔧 Scripts de build analizados: {build_scripts}")
        print(f"🐘 Scripts PHP analizados: {php_scripts}")

        # Archivos grandes
        large_files = len(self.report['large_files'])
        if large_files > 0:
            total_size = sum(f['size_mb'] for f in self.report['large_files'])
            print(f"📁 Archivos grandes (>10MB): {large_files} ({total_size:.1f}MB total)")

        # Recomendaciones
        recommendations = len(self.report['recommendations'])
        print(f"💡 Recomendaciones generadas: {recommendations}")

        if self.report['recommendations']:
            print("\n🎯 RECOMENDACIONES PRINCIPALES:")
            for i, rec in enumerate(self.report['recommendations'][:3], 1):
                print(f"{i}. [{rec['priority'].upper()}] {rec['title']}")
                print(f"   → {rec['action']}")

        print("\n" + "="*60)

def main():
    """Función principal"""
    # Obtener el directorio actual o usar el proporcionado
    root_dir = Path(__file__).parent

    print("🚀 AUDITOR DEL SISTEMA POLLUX 3D")
    print("="*60)

    auditor = SystemAuditor(root_dir)
    report = auditor.run_audit()

    # Guardar reporte
    report_file = auditor.save_report()

    # Mostrar resumen
    auditor.print_summary()

    # Generar reporte HTML simplificado
    generate_html_report(report, report_file.parent / 'audit_report.html')

    return report

def generate_html_report(report, output_file):
    """Genera un reporte HTML más legible"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Auditoría Pollux 3D - {report['timestamp']}</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; }}
            .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; }}
            .duplicate {{ background: #ffe6e6; }}
            .recommendation {{ background: #e6ffe6; }}
            .high-priority {{ border-left-color: #e74c3c; }}
            .medium-priority {{ border-left-color: #f39c12; }}
            .low-priority {{ border-left-color: #27ae60; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 Auditoría del Sistema Pollux 3D</h1>
            <p>Generado el: {report['timestamp']}</p>
            <p>Directorio: {report['root_path']}</p>
        </div>

        <div class="section recommendation">
            <h2>💡 Recomendaciones Principales</h2>
    """

    for rec in report['recommendations']:
        priority_class = f"{rec['priority']}-priority"
        html_content += f"""
            <div class="section {priority_class}">
                <h3>[{rec['priority'].upper()}] {rec['title']}</h3>
                <p><strong>Descripción:</strong> {rec['description']}</p>
                <p><strong>Acción:</strong> {rec['action']}</p>
            </div>
        """

    html_content += """
        </div>

        <div class="section duplicate">
            <h2>🔄 Archivos Duplicados</h2>
    """

    if report['duplicate_files']['by_content']:
        html_content += "<h3>Por Contenido Idéntico:</h3><table><tr><th>Hash</th><th>Archivos</th><th>Tamaño</th></tr>"
        for hash_val, files in report['duplicate_files']['by_content'].items():
            file_list = "<br>".join([f['path'] for f in files])
            size = files[0]['size']
            html_content += f"<tr><td>{hash_val[:8]}...</td><td>{file_list}</td><td>{size} bytes</td></tr>"
        html_content += "</table>"

    if report['duplicate_files']['by_pattern']:
        html_content += "<h3>Por Patrones Sospechosos:</h3><table><tr><th>Patrón</th><th>Archivos</th></tr>"
        for pattern, files in report['duplicate_files']['by_pattern'].items():
            file_list = "<br>".join(files)
            html_content += f"<tr><td>{pattern}</td><td>{file_list}</td></tr>"
        html_content += "</table>"

    html_content += """
        </div>

        <div class="section">
            <h2>🔧 Scripts de Build</h2>
            <table>
                <tr><th>Script</th><th>Estado</th><th>Líneas</th><th>Funciones</th><th>Problemas</th></tr>
    """

    for path, analysis in report['build_scripts'].items():
        functions = ", ".join(analysis['functions'][:3])
        if len(analysis['functions']) > 3:
            functions += f" (+{len(analysis['functions'])-3} más)"
        issues = "; ".join(analysis['issues']) if analysis['issues'] else "Ninguno"

        html_content += f"""
                <tr>
                    <td>{Path(path).name}</td>
                    <td>{analysis['status']}</td>
                    <td>{analysis['lines']}</td>
                    <td>{functions}</td>
                    <td>{issues}</td>
                </tr>
        """

    html_content += """
            </table>
        </div>
    </body>
    </html>
    """

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"📄 Reporte HTML guardado en: {output_file}")

if __name__ == "__main__":
    main()
