# 🔍 Sistema de Auditoría y Limpieza Pollux 3D

Este conjunto de herramientas te permite auditar tu sistema Pollux 3D para identificar archivos duplicados, scripts problemáticos, y limpiar automáticamente tu proyecto.

## 📋 Herramientas Incluidas

### 1. `master_audit.py` - Auditoría Completa
El script principal que ejecuta una auditoría completa del sistema.

### 2. `audit_system.py` - Auditoría de Archivos
Analiza archivos duplicados, scripts de build, configuraciones, etc.

### 3. `test_functionality.py` - Pruebas Funcionales
Verifica que los scripts tengan sintaxis válida y las dependencias estén instaladas.

### 4. `cleanup_system.py` - Limpieza Automática
Limpia archivos duplicados y problemáticos basándose en los resultados de la auditoría.

## 🚀 Uso Rápido

### Auditoría Completa (Recomendado)
```bash
# Ejecutar auditoría completa
python master_audit.py

# O especificar un directorio
python master_audit.py /ruta/a/tu/proyecto
```

### Solo Auditoría de Sistema
```bash
python audit_system.py
```

### Solo Pruebas Funcionales
```bash
python test_functionality.py
```

### Limpieza del Sistema
```bash
# Simulación (recomendado primero)
python cleanup_system.py --dry-run

# Limpieza real (¡CUIDADO!)
python cleanup_system.py --execute

# Usar reporte específico
python cleanup_system.py --report audit_reports_*/consolidated_report.json --dry-run
```

## 📊 Qué Analiza la Auditoría

### 🔄 Archivos Duplicados
- Detecta archivos idénticos por contenido (hash MD5)
- Identifica patrones sospechosos (rebuild*.ps1, check_*.php, etc.)
- Recomienda qué archivos mantener

### 🔧 Scripts de Build
- Analiza todos los scripts PowerShell (.ps1)
- Verifica sintaxis y funcionalidad
- Identifica scripts vacíos o problemáticos
- Cuenta funciones y dependencias

### 🐘 Scripts PHP
- Verifica sintaxis PHP
- Identifica scripts de debugging duplicados
- Analiza estructura y funcionalidad

### ⚙️ Archivos de Configuración
- Valida JSON (package.json, composer.json, etc.)
- Verifica archivos YAML/YML
- Detecta configuraciones duplicadas o vacías

### 📁 Archivos Grandes
- Identifica archivos >10MB
- Sugiere archivos que podrían eliminarse
- Calcula espacio ocupado

### 📋 Dependencias del Sistema
- Verifica Python, PHP, Node.js, npm, composer, conda
- Detecta herramientas faltantes
- Muestra versiones instaladas

## 📈 Puntuación de Salud

El sistema calcula una puntuación de 0-100 basada en:
- **Archivos duplicados**: -2 puntos por grupo de duplicados
- **Dependencias faltantes**: -5 puntos por dependencia
- **Errores de sintaxis**: -3 puntos por archivo con errores
- **Scripts problemáticos**: -2 puntos por script vacío/con errores

### Categorías de Salud
- **90-100**: 🟢 Excelente
- **75-89**: 🟡 Bueno
- **60-74**: 🟠 Aceptable
- **40-59**: 🔴 Problemático
- **0-39**: 🚨 Crítico

## 🧹 Operaciones de Limpieza

### Automáticas (con --execute)
- **duplicates**: Elimina archivos duplicados (mantiene el más reciente)
- **empty**: Elimina archivos vacíos
- **backups**: Elimina archivos .bak, .backup, *_old*, etc.
- **problematic**: Elimina scripts vacíos o con errores graves
- **redundant**: Elimina scripts de build redundantes

### Operaciones Específicas
```bash
# Solo limpiar duplicados
python cleanup_system.py --operations duplicates --dry-run

# Limpiar solo archivos vacíos y backups
python cleanup_system.py --operations empty backups --execute
```

## 📄 Reportes Generados

### Archivos JSON
- `system_audit.json`: Análisis detallado del sistema
- `functional_tests.json`: Resultados de pruebas funcionales
- `consolidated_report.json`: Reporte combinado
- `cleanup_log_*.json`: Log de operaciones de limpieza

### Reporte HTML
- `report.html`: Reporte visual completo con gráficos y resumen

## ⚠️ Precauciones de Seguridad

### Backup Automático
- El sistema crea backups antes de eliminar archivos
- Los backups se guardan en `cleanup_backup_TIMESTAMP/`
- **SIEMPRE** ejecuta `--dry-run` primero

### Archivos Protegidos
El sistema NO elimina:
- Archivos en `.git/`, `node_modules/`, `__pycache__/`
- Archivos especiales como `.gitkeep`, `__init__.py`
- Archivos del sistema o de configuración crítica

## 🔧 Ejemplos de Uso

### Auditoría Inicial
```bash
# 1. Ejecutar auditoría completa
python master_audit.py

# 2. Revisar el reporte HTML generado
# 3. Si la puntuación es <80, considerar limpieza
```

### Limpieza Segura
```bash
# 1. Simular limpieza primero
python cleanup_system.py --dry-run

# 2. Revisar qué se eliminaría
# 3. Si está conforme, ejecutar limpieza real
python cleanup_system.py --execute

# 4. Verificar que todo funciona correctamente
# 5. Si hay problemas, restaurar desde backup
```

### Análisis Específico
```bash
# Solo verificar duplicados
python audit_system.py

# Solo probar funcionalidad de scripts
python test_functionality.py

# Solo limpiar archivos obvios (backups, vacíos)
python cleanup_system.py --operations backups empty --execute
```

## 🎯 Recomendaciones de Uso

### Primera Vez
1. **Hacer backup completo** de tu proyecto
2. Ejecutar `python master_audit.py`
3. Revisar el reporte HTML generado
4. Si hay muchos duplicados, ejecutar limpieza con `--dry-run`
5. Solo usar `--execute` cuando estés seguro

### Mantenimiento Regular
- Ejecutar auditoría mensualmente
- Limpiar archivos evidentes (backups, vacíos) semanalmente
- Revisar scripts redundantes cada trimestre

### Antes de Deployment
- Ejecutar auditoría completa
- Asegurar puntuación >75
- Limpiar archivos innecesarios
- Verificar que todas las dependencias estén instaladas

## 🆘 Solución de Problemas

### Error: "No se puede importar módulo"
```bash
# Asegúrate de estar en el directorio correcto
cd /ruta/a/tu/proyecto/Pollux_3D
python master_audit.py
```

### Error: "Dependencia no encontrada"
```bash
# Instalar dependencias faltantes
# Para PowerShell: Instalar PowerShell Core
# Para PHP: sudo apt install php-cli (Linux) o instalar PHP (Windows)
```

### Recuperar archivos eliminados por error
```bash
# Los backups están en cleanup_backup_*/
# Copiar archivos de vuelta desde el backup
cp -r cleanup_backup_*/path/to/file /path/to/original/location
```

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs de error en los archivos JSON
2. Ejecuta siempre `--dry-run` antes de `--execute`
3. Mantén backups de archivos importantes
4. El reporte HTML contiene información detallada para debugging

---

**⚠️ IMPORTANTE**: Siempre haz backup de tu proyecto antes de ejecutar operaciones de limpieza con `--execute`.
