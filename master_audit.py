#!/usr/bin/env python3
"""
Script principal de auditoría completa del sistema Pollux 3D
Combina auditoría de archivos duplicados y pruebas funcionales
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Agregar el directorio actual al path para importar nuestros módulos
sys.path.insert(0, str(Path(__file__).parent))

from audit_system import SystemAuditor
from test_functionality import FunctionalTester

class MasterAuditor:
    def __init__(self, root_path):
        self.root_path = Path(root_path)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_complete_audit(self):
        """Ejecuta auditoría completa del sistema"""
        print("🚀 AUDITORÍA COMPLETA DEL SISTEMA POLLUX 3D")
        print("="*80)
        print(f"📂 Directorio: {self.root_path}")
        print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        # 1. Auditoría de sistema (duplicados, análisis de archivos)
        print("\n🔍 FASE 1: AUDITORÍA DEL SISTEMA")
        print("-"*50)
        system_auditor = SystemAuditor(self.root_path)
        system_report = system_auditor.run_audit()
        system_auditor.print_summary()

        # 2. Pruebas funcionales
        print("\n🧪 FASE 2: PRUEBAS FUNCIONALES")
        print("-"*50)
        functional_tester = FunctionalTester(self.root_path)
        functional_report = functional_tester.run_tests()
        functional_tester.print_summary()

        # 3. Generar reporte consolidado
        print("\n📊 FASE 3: REPORTE CONSOLIDADO")
        print("-"*50)
        consolidated_report = self.create_consolidated_report(system_report, functional_report)

        # 4. Guardar reportes
        self.save_reports(system_report, functional_report, consolidated_report)

        # 5. Mostrar resumen final
        self.print_final_summary(consolidated_report)

        return consolidated_report

    def create_consolidated_report(self, system_report, functional_report):
        """Crea un reporte consolidado combinando ambas auditorías"""
        consolidated = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'root_path': str(self.root_path),
                'audit_type': 'complete_system_audit',
                'version': '1.0'
            },
            'executive_summary': {},
            'system_audit': system_report,
            'functional_tests': functional_report,
            'consolidated_recommendations': [],
            'action_plan': {},
            'health_score': {}
        }

        # Generar resumen ejecutivo
        consolidated['executive_summary'] = self.generate_executive_summary(system_report, functional_report)

        # Consolidar recomendaciones
        consolidated['consolidated_recommendations'] = self.consolidate_recommendations(
            system_report.get('recommendations', []),
            functional_report.get('recommendations', [])
        )

        # Generar plan de acción
        consolidated['action_plan'] = self.generate_action_plan(consolidated['consolidated_recommendations'])

        # Calcular score de salud del sistema
        consolidated['health_score'] = self.calculate_health_score(system_report, functional_report)

        return consolidated

    def generate_executive_summary(self, system_report, functional_report):
        """Genera un resumen ejecutivo del estado del sistema"""
        summary = {
            'overall_status': 'unknown',
            'critical_issues': 0,
            'warnings': 0,
            'info_items': 0,
            'key_findings': []
        }

        # Analizar duplicados
        duplicate_groups = len(system_report.get('duplicate_files', {}).get('by_content', {}))
        if duplicate_groups > 10:
            summary['critical_issues'] += 1
            summary['key_findings'].append(f"Encontrados {duplicate_groups} grupos de archivos duplicados")
        elif duplicate_groups > 0:
            summary['warnings'] += 1
            summary['key_findings'].append(f"Algunos archivos duplicados encontrados ({duplicate_groups})")

        # Analizar scripts de build
        build_scripts = len(system_report.get('build_scripts', {}))
        working_scripts = sum(1 for script in system_report.get('build_scripts', {}).values()
                             if script.get('status') == 'functional')

        if build_scripts > 0:
            if working_scripts / build_scripts < 0.5:
                summary['critical_issues'] += 1
                summary['key_findings'].append(f"Solo {working_scripts}/{build_scripts} scripts de build parecen funcionales")
            elif working_scripts / build_scripts < 0.8:
                summary['warnings'] += 1
                summary['key_findings'].append(f"Algunos scripts de build pueden tener problemas")

        # Analizar dependencias
        deps = functional_report.get('dependencies', {})
        missing_deps = [dep for dep, info in deps.items() if info.get('status') == 'not_found']

        if missing_deps:
            if len(missing_deps) > 3:
                summary['critical_issues'] += 1
            else:
                summary['warnings'] += 1
            summary['key_findings'].append(f"Dependencias faltantes: {', '.join(missing_deps)}")

        # Analizar errores de sintaxis
        syntax_errors = sum(1 for result in functional_report.get('test_results', {}).values()
                           if result.get('status') == 'syntax_error')
        if syntax_errors > 0:
            summary['warnings'] += 1
            summary['key_findings'].append(f"{syntax_errors} archivos con errores de sintaxis")

        # Determinar estado general
        if summary['critical_issues'] > 0:
            summary['overall_status'] = 'critical'
        elif summary['warnings'] > 2:
            summary['overall_status'] = 'warning'
        elif summary['warnings'] > 0:
            summary['overall_status'] = 'caution'
        else:
            summary['overall_status'] = 'good'

        return summary

    def consolidate_recommendations(self, system_recs, functional_recs):
        """Consolida recomendaciones de ambas auditorías"""
        all_recs = []

        # Agregar recomendaciones del sistema con prefijo
        for rec in system_recs:
            rec['source'] = 'system_audit'
            all_recs.append(rec)

        # Agregar recomendaciones funcionales con prefijo
        for rec in functional_recs:
            rec['source'] = 'functional_test'
            all_recs.append(rec)

        # Ordenar por prioridad
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        all_recs.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))

        return all_recs

    def generate_action_plan(self, recommendations):
        """Genera un plan de acción basado en las recomendaciones"""
        plan = {
            'immediate_actions': [],
            'short_term_actions': [],
            'long_term_actions': [],
            'estimated_time': {}
        }

        for rec in recommendations:
            priority = rec.get('priority', 'low')
            action_item = {
                'title': rec.get('title', 'Sin título'),
                'action': rec.get('action', 'Sin acción definida'),
                'category': rec.get('category', 'general'),
                'source': rec.get('source', 'unknown')
            }

            if priority == 'high':
                plan['immediate_actions'].append(action_item)
            elif priority == 'medium':
                plan['short_term_actions'].append(action_item)
            else:
                plan['long_term_actions'].append(action_item)

        # Estimar tiempos
        plan['estimated_time'] = {
            'immediate': f"{len(plan['immediate_actions'])} * 30min = {len(plan['immediate_actions']) * 0.5}h",
            'short_term': f"{len(plan['short_term_actions'])} * 1h = {len(plan['short_term_actions'])}h",
            'long_term': f"{len(plan['long_term_actions'])} * 2h = {len(plan['long_term_actions']) * 2}h"
        }

        return plan

    def calculate_health_score(self, system_report, functional_report):
        """Calcula un score de salud del sistema (0-100)"""
        score = 100
        deductions = {
            'reasons': [],
            'total_deducted': 0
        }

        # Penalizar por duplicados
        duplicate_groups = len(system_report.get('duplicate_files', {}).get('by_content', {}))
        if duplicate_groups > 0:
            deduction = min(duplicate_groups * 2, 20)  # Máximo 20 puntos
            score -= deduction
            deductions['reasons'].append(f"Archivos duplicados: -{deduction}")
            deductions['total_deducted'] += deduction

        # Penalizar por dependencias faltantes
        missing_deps = sum(1 for info in functional_report.get('dependencies', {}).values()
                          if info.get('status') == 'not_found')
        if missing_deps > 0:
            deduction = missing_deps * 5  # 5 puntos por dependencia
            score -= deduction
            deductions['reasons'].append(f"Dependencias faltantes: -{deduction}")
            deductions['total_deducted'] += deduction

        # Penalizar por errores de sintaxis
        syntax_errors = sum(1 for result in functional_report.get('test_results', {}).values()
                           if result.get('status') == 'syntax_error')
        if syntax_errors > 0:
            deduction = min(syntax_errors * 3, 15)  # Máximo 15 puntos
            score -= deduction
            deductions['reasons'].append(f"Errores de sintaxis: -{deduction}")
            deductions['total_deducted'] += deduction

        # Penalizar por archivos problemáticos
        problematic = sum(1 for analysis in system_report.get('build_scripts', {}).values()
                         if analysis.get('status') in ['empty', 'error'])
        if problematic > 0:
            deduction = min(problematic * 2, 10)  # Máximo 10 puntos
            score -= deduction
            deductions['reasons'].append(f"Scripts problemáticos: -{deduction}")
            deductions['total_deducted'] += deduction

        return {
            'score': max(score, 0),  # No permitir scores negativos
            'category': self.categorize_health_score(max(score, 0)),
            'deductions': deductions
        }

    def categorize_health_score(self, score):
        """Categoriza el score de salud"""
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'fair'
        elif score >= 40:
            return 'poor'
        else:
            return 'critical'

    def save_reports(self, system_report, functional_report, consolidated_report):
        """Guarda todos los reportes"""
        output_dir = self.root_path / f'audit_reports_{self.timestamp}'
        output_dir.mkdir(exist_ok=True)

        # Guardar reporte del sistema
        with open(output_dir / 'system_audit.json', 'w', encoding='utf-8') as f:
            json.dump(system_report, f, indent=2, ensure_ascii=False)

        # Guardar reporte funcional
        with open(output_dir / 'functional_tests.json', 'w', encoding='utf-8') as f:
            json.dump(functional_report, f, indent=2, ensure_ascii=False)

        # Guardar reporte consolidado
        with open(output_dir / 'consolidated_report.json', 'w', encoding='utf-8') as f:
            json.dump(consolidated_report, f, indent=2, ensure_ascii=False)

        # Generar reporte HTML
        self.generate_html_report(consolidated_report, output_dir / 'report.html')

        print(f"📁 Reportes guardados en: {output_dir}")
        return output_dir

    def generate_html_report(self, report, output_file):
        """Genera un reporte HTML comprensivo"""
        health_score = report['health_score']['score']
        health_category = report['health_score']['category']
        overall_status = report['executive_summary']['overall_status']

        # Mapear colores por categoría
        health_colors = {
            'excellent': '#27ae60',
            'good': '#2ecc71',
            'fair': '#f39c12',
            'poor': '#e67e22',
            'critical': '#e74c3c'
        }

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Auditoría Completa - Pollux 3D</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; margin: -30px -30px 30px -30px; border-radius: 10px 10px 0 0; }}
                .health-score {{ text-align: center; margin: 20px 0; }}
                .score-circle {{ width: 120px; height: 120px; border-radius: 50%; margin: 0 auto; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; font-weight: bold; background: {health_colors.get(health_category, '#95a5a6')}; }}
                .section {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .critical {{ border-left: 5px solid #e74c3c; background: #fdf2f2; }}
                .warning {{ border-left: 5px solid #f39c12; background: #fefbf3; }}
                .success {{ border-left: 5px solid #27ae60; background: #f2f8f5; }}
                .info {{ border-left: 5px solid #3498db; background: #f2f8fc; }}
                .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
                .card {{ background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }}
                .recommendation {{ margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .high-priority {{ background: #ffe6e6; border-left: 4px solid #e74c3c; }}
                .medium-priority {{ background: #fff3e0; border-left: 4px solid #f39c12; }}
                .low-priority {{ background: #e8f5e8; border-left: 4px solid #27ae60; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; font-weight: 600; }}
                .metric {{ text-align: center; }}
                .metric-value {{ font-size: 2em; font-weight: bold; color: #2c3e50; }}
                .metric-label {{ color: #7f8c8d; }}
                .progress-bar {{ width: 100%; height: 20px; background: #ecf0f1; border-radius: 10px; overflow: hidden; }}
                .progress-fill {{ height: 100%; background: linear-gradient(90deg, #e74c3c 0%, #f39c12 40%, #27ae60 100%); transition: width 0.3s; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 Auditoría Completa del Sistema Pollux 3D</h1>
                    <p>Generado el: {report['metadata']['timestamp']}</p>
                    <p>Directorio auditado: {report['metadata']['root_path']}</p>
                </div>

                <div class="health-score">
                    <h2>Puntuación de Salud del Sistema</h2>
                    <div class="score-circle">
                        {health_score}/100
                    </div>
                    <h3>Estado: {health_category.upper()}</h3>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {health_score}%;"></div>
                    </div>
                </div>

                <div class="grid">
                    <div class="card">
                        <h3>📊 Métricas Clave</h3>
                        <div class="metric">
                            <div class="metric-value">{len(report['system_audit'].get('duplicate_files', {}).get('by_content', {}))}</div>
                            <div class="metric-label">Grupos de Duplicados</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{len(report['system_audit'].get('build_scripts', {}))}</div>
                            <div class="metric-label">Scripts de Build</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{report['functional_tests'].get('summary', {}).get('total_files', 0)}</div>
                            <div class="metric-label">Archivos Probados</div>
                        </div>
                    </div>

                    <div class="card">
                        <h3>🎯 Resumen Ejecutivo</h3>
                        <p><strong>Estado General:</strong> {overall_status.upper()}</p>
                        <p><strong>Problemas Críticos:</strong> {report['executive_summary']['critical_issues']}</p>
                        <p><strong>Advertencias:</strong> {report['executive_summary']['warnings']}</p>
                        <ul>
        """

        for finding in report['executive_summary']['key_findings']:
            html_content += f"<li>{finding}</li>"

        html_content += """
                        </ul>
                    </div>
                </div>

                <div class="section">
                    <h2>💡 Plan de Acción Recomendado</h2>

                    <h3>🚨 Acciones Inmediatas (Alta Prioridad)</h3>
        """

        for action in report['action_plan']['immediate_actions']:
            html_content += f"""
                    <div class="recommendation high-priority">
                        <strong>{action['title']}</strong><br>
                        <em>Acción:</em> {action['action']}<br>
                        <small>Fuente: {action['source']} | Categoría: {action['category']}</small>
                    </div>
            """

        html_content += """
                    <h3>⚠️ Acciones a Corto Plazo (Prioridad Media)</h3>
        """

        for action in report['action_plan']['short_term_actions']:
            html_content += f"""
                    <div class="recommendation medium-priority">
                        <strong>{action['title']}</strong><br>
                        <em>Acción:</em> {action['action']}<br>
                        <small>Fuente: {action['source']} | Categoría: {action['category']}</small>
                    </div>
            """

        html_content += """
                    <h3>📋 Acciones a Largo Plazo (Prioridad Baja)</h3>
        """

        for action in report['action_plan']['long_term_actions']:
            html_content += f"""
                    <div class="recommendation low-priority">
                        <strong>{action['title']}</strong><br>
                        <em>Acción:</em> {action['action']}<br>
                        <small>Fuente: {action['source']} | Categoría: {action['category']}</small>
                    </div>
            """

        html_content += f"""
                </div>

                <div class="section info">
                    <h2>⏱️ Estimación de Tiempo</h2>
                    <ul>
                        <li><strong>Inmediato:</strong> {report['action_plan']['estimated_time']['immediate']}</li>
                        <li><strong>Corto plazo:</strong> {report['action_plan']['estimated_time']['short_term']}</li>
                        <li><strong>Largo plazo:</strong> {report['action_plan']['estimated_time']['long_term']}</li>
                    </ul>
                </div>

                <div class="section">
                    <h2>🔍 Detalles de la Puntuación</h2>
                    <p><strong>Puntuación base:</strong> 100 puntos</p>
                    <p><strong>Deducciones totales:</strong> -{report['health_score']['deductions']['total_deducted']} puntos</p>
                    <ul>
        """

        for reason in report['health_score']['deductions']['reasons']:
            html_content += f"<li>{reason}</li>"

        html_content += f"""
                    </ul>
                    <p><strong>Puntuación final:</strong> {health_score}/100 ({health_category})</p>
                </div>

                <div class="section">
                    <h2>📋 Dependencias del Sistema</h2>
                    <table>
                        <tr><th>Dependencia</th><th>Estado</th><th>Versión</th></tr>
        """

        for dep, info in report['functional_tests'].get('dependencies', {}).items():
            status_icon = "✅" if info['status'] == 'available' else "❌"
            version = info.get('version', info.get('message', 'N/A'))
            html_content += f"<tr><td>{dep}</td><td>{status_icon} {info['status']}</td><td>{version}</td></tr>"

        html_content += """
                    </table>
                </div>

                <div class="section">
                    <p style="text-align: center; color: #7f8c8d; margin-top: 30px;">
                        Reporte generado automáticamente por el Sistema de Auditoría Pollux 3D<br>
                        Para más detalles, consulte los archivos JSON incluidos en esta carpeta.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"📄 Reporte HTML generado: {output_file}")

    def print_final_summary(self, report):
        """Imprime resumen final de la auditoría"""
        print("\n" + "="*80)
        print("🏁 RESUMEN FINAL DE AUDITORÍA")
        print("="*80)

        health_score = report['health_score']['score']
        health_category = report['health_score']['category']

        # Mostrar puntuación de salud
        print(f"\n🎯 PUNTUACIÓN DE SALUD DEL SISTEMA: {health_score}/100 ({health_category.upper()})")

        if health_score >= 90:
            print("🟢 ¡Excelente! El sistema está en muy buen estado")
        elif health_score >= 75:
            print("🟡 Buen estado general, algunas mejoras menores recomendadas")
        elif health_score >= 60:
            print("🟠 Estado aceptable, se requieren algunas correcciones")
        elif health_score >= 40:
            print("🔴 El sistema tiene problemas que requieren atención")
        else:
            print("🚨 Estado crítico, se requiere intervención inmediata")

        # Mostrar plan de acción resumido
        immediate = len(report['action_plan']['immediate_actions'])
        short_term = len(report['action_plan']['short_term_actions'])
        long_term = len(report['action_plan']['long_term_actions'])

        print(f"\n📋 PLAN DE ACCIÓN:")
        print(f"   🚨 Acciones inmediatas: {immediate}")
        print(f"   ⚠️  Acciones corto plazo: {short_term}")
        print(f"   📋 Acciones largo plazo: {long_term}")

        # Mostrar próximos pasos
        print(f"\n🚀 PRÓXIMOS PASOS RECOMENDADOS:")
        if immediate > 0:
            print("   1. Revisar y ejecutar acciones inmediatas (alta prioridad)")
        if short_term > 0:
            print("   2. Planificar acciones de corto plazo")
        print("   3. Consultar el reporte HTML detallado")
        print("   4. Ejecutar auditoría periódicamente")

        print("\n" + "="*80)

def main():
    """Función principal"""
    # Determinar directorio de trabajo
    if len(sys.argv) > 1:
        root_dir = Path(sys.argv[1])
    else:
        root_dir = Path(__file__).parent

    if not root_dir.exists():
        print(f"❌ Error: El directorio {root_dir} no existe")
        return 1

    # Ejecutar auditoría completa
    master_auditor = MasterAuditor(root_dir)
    try:
        report = master_auditor.run_complete_audit()
        return 0
    except KeyboardInterrupt:
        print("\n❌ Auditoría cancelada por el usuario")
        return 1
    except Exception as e:
        print(f"❌ Error durante la auditoría: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
