#!/usr/bin/env python3
"""
Script de prueba funcional para verificar qué scripts del sistema funcionan
"""

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

class FunctionalTester:
    def __init__(self, root_path):
        self.root_path = Path(root_path)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'test_results': {},
            'summary': {},
            'recommendations': []
        }

    def test_powershell_script(self, script_path):
        """Prueba si un script PowerShell tiene sintaxis válida"""
        try:
            # Verificar sintaxis sin ejecutar
            cmd = ['powershell', '-NoProfile', '-Command', f'Get-Content "{script_path}" | Out-Null']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                # Verificar que el archivo no esté vacío
                with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                    if not content:
                        return {'status': 'empty', 'message': 'Archivo vacío'}
                    elif len(content.splitlines()) < 3:
                        return {'status': 'minimal', 'message': 'Script muy corto'}
                    else:
                        return {'status': 'syntax_ok', 'message': 'Sintaxis válida'}
            else:
                return {'status': 'syntax_error', 'message': result.stderr.strip()}
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Timeout verificando sintaxis'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def test_php_script(self, script_path):
        """Prueba si un script PHP tiene sintaxis válida"""
        try:
            # Verificar sintaxis PHP
            cmd = ['php', '-l', str(script_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                    if not content:
                        return {'status': 'empty', 'message': 'Archivo vacío'}
                    elif '<?php' not in content:
                        return {'status': 'invalid', 'message': 'No es un archivo PHP válido'}
                    else:
                        return {'status': 'syntax_ok', 'message': 'Sintaxis válida'}
            else:
                return {'status': 'syntax_error', 'message': result.stderr.strip()}
        except FileNotFoundError:
            return {'status': 'no_php', 'message': 'PHP no instalado o no encontrado'}
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Timeout verificando sintaxis'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def test_batch_script(self, script_path):
        """Prueba básica para scripts batch/cmd"""
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
                if not content:
                    return {'status': 'empty', 'message': 'Archivo vacío'}
                elif '@echo off' in content.lower() or 'echo' in content.lower():
                    return {'status': 'likely_ok', 'message': 'Parece un script batch válido'}
                else:
                    return {'status': 'questionable', 'message': 'No parece un script batch estándar'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def test_json_file(self, file_path):
        """Prueba si un archivo JSON es válido"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return {'status': 'valid_json', 'message': 'JSON válido'}
        except json.JSONDecodeError as e:
            return {'status': 'invalid_json', 'message': f'JSON inválido: {e}'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def check_dependencies(self):
        """Verifica dependencias del sistema"""
        dependencies = {
            'python': ['python', '--version'],
            'php': ['php', '--version'],
            'powershell': ['powershell', '-Command', 'echo "test"'],
            'node': ['node', '--version'],
            'npm': ['npm', '--version'],
            'composer': ['composer', '--version'],
            'conda': ['conda', '--version']
        }

        dep_results = {}
        for dep, cmd in dependencies.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0]
                    dep_results[dep] = {'status': 'available', 'version': version}
                else:
                    dep_results[dep] = {'status': 'error', 'message': result.stderr.strip()}
            except FileNotFoundError:
                dep_results[dep] = {'status': 'not_found', 'message': 'No instalado'}
            except subprocess.TimeoutExpired:
                dep_results[dep] = {'status': 'timeout', 'message': 'Timeout'}
            except Exception as e:
                dep_results[dep] = {'status': 'error', 'message': str(e)}

        return dep_results

    def run_tests(self):
        """Ejecuta todas las pruebas"""
        print("🧪 Iniciando pruebas funcionales...")

        # Verificar dependencias
        print("📋 Verificando dependencias del sistema...")
        self.results['dependencies'] = self.check_dependencies()

        # Encontrar y probar scripts
        test_patterns = {
            '**/*.ps1': self.test_powershell_script,
            '**/*.php': self.test_php_script,
            '**/*.bat': self.test_batch_script,
            '**/*.cmd': self.test_batch_script,
            '**/package.json': self.test_json_file,
            '**/composer.json': self.test_json_file
        }

        total_files = 0
        for pattern, test_func in test_patterns.items():
            print(f"🔍 Probando archivos: {pattern}")
            files = list(self.root_path.glob(pattern))

            for file_path in files:
                # Filtrar archivos en directorios que queremos ignorar
                if any(ignore in str(file_path) for ignore in ['node_modules', '.git', '__pycache__', 'vendor', 'cleanup_backup_', 'audit_reports_']):
                    continue

                result = test_func(file_path)
                self.results['test_results'][str(file_path)] = {
                    'type': pattern.split('.')[-1],
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    **result
                }
                total_files += 1

        print(f"✅ Probados {total_files} archivos")

        # Generar resumen
        self.generate_summary()
        return self.results

    def generate_summary(self):
        """Genera resumen de los resultados"""
        status_counts = {}
        by_type = {}

        for file_path, result in self.results['test_results'].items():
            status = result['status']
            file_type = result['type']

            # Contar por status
            status_counts[status] = status_counts.get(status, 0) + 1

            # Contar por tipo
            if file_type not in by_type:
                by_type[file_type] = {}
            by_type[file_type][status] = by_type[file_type].get(status, 0) + 1

        self.results['summary'] = {
            'total_files': len(self.results['test_results']),
            'by_status': status_counts,
            'by_type': by_type
        }

        # Generar recomendaciones
        self.generate_test_recommendations()

    def generate_test_recommendations(self):
        """Genera recomendaciones basadas en las pruebas"""
        recommendations = []

        # Verificar dependencias faltantes
        missing_deps = [dep for dep, info in self.results['dependencies'].items()
                       if info['status'] == 'not_found']
        if missing_deps:
            recommendations.append({
                'priority': 'high',
                'category': 'dependencies',
                'title': 'Dependencias faltantes',
                'description': f"Faltan dependencias: {', '.join(missing_deps)}",
                'action': 'Instalar dependencias faltantes para el funcionamiento completo'
            })

        # Verificar archivos con errores de sintaxis
        syntax_errors = [path for path, result in self.results['test_results'].items()
                        if result['status'] == 'syntax_error']
        if syntax_errors:
            recommendations.append({
                'priority': 'medium',
                'category': 'syntax',
                'title': 'Errores de sintaxis',
                'description': f"Se encontraron {len(syntax_errors)} archivos con errores de sintaxis",
                'action': 'Revisar y corregir errores de sintaxis en los archivos'
            })

        # Verificar archivos vacíos
        empty_files = [path for path, result in self.results['test_results'].items()
                      if result['status'] == 'empty']
        if empty_files:
            recommendations.append({
                'priority': 'low',
                'category': 'cleanup',
                'title': 'Archivos vacíos',
                'description': f"Se encontraron {len(empty_files)} archivos vacíos",
                'action': 'Considerar eliminar archivos vacíos innecesarios'
            })

        self.results['recommendations'] = recommendations

    def print_summary(self):
        """Imprime resumen de las pruebas"""
        print("\n" + "="*60)
        print("🧪 RESUMEN DE PRUEBAS FUNCIONALES")
        print("="*60)

        # Dependencias
        print("📋 DEPENDENCIAS:")
        for dep, info in self.results['dependencies'].items():
            status_icon = "✅" if info['status'] == 'available' else "❌"
            version_info = f" ({info.get('version', 'N/A')})" if info['status'] == 'available' else ""
            print(f"  {status_icon} {dep.upper()}{version_info}")

        # Resumen por estado
        print(f"\n📊 RESUMEN POR ESTADO:")
        for status, count in self.results['summary']['by_status'].items():
            icon = {
                'syntax_ok': '✅',
                'valid_json': '✅',
                'likely_ok': '✅',
                'syntax_error': '❌',
                'invalid_json': '❌',
                'empty': '⚠️',
                'minimal': '⚠️',
                'error': '❌'
            }.get(status, '❓')
            print(f"  {icon} {status}: {count}")

        # Resumen por tipo
        print(f"\n📁 RESUMEN POR TIPO DE ARCHIVO:")
        for file_type, statuses in self.results['summary']['by_type'].items():
            total = sum(statuses.values())
            ok_count = sum(count for status, count in statuses.items()
                          if status in ['syntax_ok', 'valid_json', 'likely_ok'])
            print(f"  📄 {file_type.upper()}: {ok_count}/{total} OK")

        # Recomendaciones
        if self.results['recommendations']:
            print(f"\n💡 RECOMENDACIONES:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"  {i}. [{rec['priority'].upper()}] {rec['title']}")
                print(f"     → {rec['action']}")

        print("\n" + "="*60)

    def save_results(self, output_file='test_results.json'):
        """Guarda los resultados en un archivo"""
        output_path = self.root_path / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"💾 Resultados guardados en: {output_path}")
        return output_path

def main():
    """Función principal"""
    root_dir = Path(__file__).parent

    print("🧪 PROBADOR FUNCIONAL - POLLUX 3D")
    print("="*60)

    tester = FunctionalTester(root_dir)
    results = tester.run_tests()

    # Mostrar resumen
    tester.print_summary()

    # Guardar resultados
    tester.save_results()

    return results

if __name__ == "__main__":
    main()
