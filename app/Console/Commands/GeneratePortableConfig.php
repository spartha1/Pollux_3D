<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\File;

class GeneratePortableConfig extends Command
{
    protected $signature = 'config:portable {--validate : Solo validar la configuración sin generar archivos}';
    protected $description = 'Genera archivos de configuración portables para migración de servidor';

    private $config = [];
    
    public function handle()
    {
        $this->info('🚀 Generador de Configuración Portable - Pollux 3D');
        $this->info('================================================');
        
        $this->detectPaths();
        
        if ($this->option('validate')) {
            return $this->validateConfiguration();
        }
        
        if ($this->validateConfiguration()) {
            $this->generateScripts();
            $this->info('✅ ¡Scripts generados exitosamente!');
            $this->warn('📝 Los archivos antiguos se respaldaron con extensión .backup');
            $this->info('');
            $this->info('🔧 Para migrar a otro servidor:');
            $this->info('   1. Copie todo el proyecto');
            $this->info('   2. Configure las variables en .env');
            $this->info('   3. Ejecute: php artisan config:portable');
            $this->info('   4. Los scripts se regenerarán automáticamente');
        }
        
        return 0;
    }
    
    private function detectPaths()
    {
        $isWindows = PHP_OS_FAMILY === 'Windows';
        
        // Detectar conda root
        $condaRoot = config('services.python.conda_root') ?? $this->detectCondaRoot();
        
        // Detectar conda env
        $condaEnv = config('services.python.conda_env', 'pollux-preview-env');
        
        // Construir rutas
        if ($isWindows) {
            $condaPrefix = $condaRoot . '\\envs\\' . $condaEnv;
            $pythonExecutable = $condaPrefix . '\\python.exe';
        } else {
            $condaPrefix = $condaRoot . '/envs/' . $condaEnv;
            $pythonExecutable = $condaPrefix . '/bin/python';
        }
        
        $this->config = [
            'PROJECT_ROOT' => base_path(),
            'CONDA_ROOT' => $condaRoot,
            'CONDA_ENV' => $condaEnv,
            'CONDA_PREFIX' => $condaPrefix,
            'PYTHON_EXECUTABLE' => $pythonExecutable,
            'IS_WINDOWS' => $isWindows,
        ];
        
        $this->info('🔍 Configuración detectada:');
        foreach ($this->config as $key => $value) {
            if ($key !== 'IS_WINDOWS') {
                $this->line("   {$key}: {$value}");
            }
        }
        $this->info('');
    }
    
    private function detectCondaRoot()
    {
        $isWindows = PHP_OS_FAMILY === 'Windows';
        
        // Intentar detectar desde CONDA_PREFIX
        $condaPrefix = getenv('CONDA_PREFIX');
        if ($condaPrefix) {
            // Extraer root path desde prefix
            if ($isWindows) {
                $parts = explode('\\envs\\', $condaPrefix);
            } else {
                $parts = explode('/envs/', $condaPrefix);
            }
            if (count($parts) > 1) {
                return $parts[0];
            }
        }
        
        // Rutas comunes por OS
        $username = getenv('USERNAME') ?: getenv('USER');
        if ($isWindows) {
            $commonPaths = [
                "C:\\Users\\{$username}\\miniconda3",
                "C:\\Users\\{$username}\\anaconda3",
                "C:\\miniconda3",
                "C:\\anaconda3",
            ];
        } else {
            $commonPaths = [
                "/home/{$username}/miniconda3",
                "/home/{$username}/anaconda3",
                "/opt/miniconda3",
                "/opt/anaconda3",
            ];
        }
        
        foreach ($commonPaths as $path) {
            if (is_dir($path)) {
                return $path;
            }
        }
        
        throw new \Exception("No se pudo detectar la instalación de conda. Configure CONDA_ROOT en .env");
    }
    
    private function validateConfiguration()
    {
        $this->info('🔍 Validando configuración...');
        
        $errors = [];
        
        // Verificar que existe conda root
        if (!is_dir($this->config['CONDA_ROOT'])) {
            $errors[] = "CONDA_ROOT no existe: {$this->config['CONDA_ROOT']}";
        }
        
        // Verificar que existe el environment
        if (!is_dir($this->config['CONDA_PREFIX'])) {
            $errors[] = "Conda environment no existe: {$this->config['CONDA_PREFIX']}";
        }
        
        // Verificar que existe python
        if (!file_exists($this->config['PYTHON_EXECUTABLE'])) {
            $errors[] = "Python executable no existe: {$this->config['PYTHON_EXECUTABLE']}";
        }
        
        if (empty($errors)) {
            $this->info('✅ Configuración válida!');
            $this->info('');
            return true;
        } else {
            $this->error('❌ Errores encontrados:');
            foreach ($errors as $error) {
                $this->line("   • {$error}");
            }
            $this->info('');
            return false;
        }
    }
    
    private function generateScripts()
    {
        $this->info('🚀 Generando scripts portables...');
        $this->info('');
        
        if ($this->config['IS_WINDOWS']) {
            $this->generateManufacturingAnalyzerBat();
            $this->generateCondaWrapperBat();
        } else {
            $this->generateManufacturingAnalyzerSh();
            $this->generateCondaWrapperSh();
        }
    }
    
    private function generateManufacturingAnalyzerBat()
    {
        $templatePath = base_path('run_manufacturing_analyzer_template.bat');
        if (!file_exists($templatePath)) {
            $this->error("Template no encontrado: {$templatePath}");
            return;
        }
        
        $template = File::get($templatePath);
        $content = str_replace([
            '{{CONDA_PREFIX}}',
            '{{CONDA_ENV}}',
            '{{PROJECT_ROOT}}',
            '{{PYTHON_EXECUTABLE}}'
        ], [
            $this->config['CONDA_PREFIX'],
            $this->config['CONDA_ENV'],
            $this->config['PROJECT_ROOT'],
            $this->config['PYTHON_EXECUTABLE']
        ], $template);
        
        $outputFile = base_path('run_manufacturing_analyzer.bat');
        $this->backupAndWrite($outputFile, $content);
        $this->line('✓ Generado: run_manufacturing_analyzer.bat');
    }
    
    private function generateCondaWrapperBat()
    {
        $templatePath = app_path('Services/FileAnalyzers/run_with_conda_template.bat');
        if (!file_exists($templatePath)) {
            $this->error("Template no encontrado: {$templatePath}");
            return;
        }
        
        $template = File::get($templatePath);
        $content = str_replace([
            '{{CONDA_ROOT}}',
            '{{CONDA_ENV}}',
            '{{PYTHON_EXECUTABLE}}'
        ], [
            $this->config['CONDA_ROOT'],
            $this->config['CONDA_ENV'],
            $this->config['PYTHON_EXECUTABLE']
        ], $template);
        
        $outputFile = app_path('Services/FileAnalyzers/run_with_conda.bat');
        $this->backupAndWrite($outputFile, $content);
        $this->line('✓ Generado: app/Services/FileAnalyzers/run_with_conda.bat');
    }
    
    private function generateManufacturingAnalyzerSh()
    {
        $content = <<<EOL
#!/bin/bash
# Script dedicado para ejecutar el analizador de manufactura con entorno conda
# Generado automáticamente por php artisan config:portable

# Configurar las variables de entorno de conda
export CONDA_PREFIX="{$this->config['CONDA_PREFIX']}"
export CONDA_DEFAULT_ENV="{$this->config['CONDA_ENV']}"
export PATH="\$CONDA_PREFIX/bin:\$PATH"

# Deshabilitar randomización de hash de Python
export PYTHONHASHSEED=0

# Cambiar al directorio del proyecto
cd "{$this->config['PROJECT_ROOT']}"

# Ejecutar el analizador usando Python del entorno conda
"{$this->config['PYTHON_EXECUTABLE']}" "app/Services/FileAnalyzers/analyze_stl_manufacturing.py" "\$1"
EOL;
        
        $outputFile = base_path('run_manufacturing_analyzer.sh');
        $this->backupAndWrite($outputFile, $content);
        chmod($outputFile, 0755);
        $this->line('✓ Generado: run_manufacturing_analyzer.sh');
    }
    
    private function generateCondaWrapperSh()
    {
        $content = <<<EOL
#!/bin/bash
# Wrapper de conda multiplataforma
# Generado automáticamente por php artisan config:portable

# Set conda environment paths from configuration
export CONDA_ROOT="{$this->config['CONDA_ROOT']}"
export CONDA_ENV="{$this->config['CONDA_ENV']}"
export CONDA_PREFIX="{$this->config['CONDA_PREFIX']}"

# Set PATH to include conda directories
export PATH="\$CONDA_PREFIX/bin:\$CONDA_ROOT/bin:\$PATH"

# Set conda environment variables
export CONDA_DEFAULT_ENV="\$CONDA_ENV"
export PYTHONHASHSEED=0

# Verify Python exists
if [ ! -f "{$this->config['PYTHON_EXECUTABLE']}" ]; then
    echo "ERROR: Python not found at {$this->config['PYTHON_EXECUTABLE']}"
    exit 1
fi

# Run the Python script directly
"{$this->config['PYTHON_EXECUTABLE']}" "\$@"
EOL;
        
        $outputFile = app_path('Services/FileAnalyzers/run_with_conda.sh');
        $this->backupAndWrite($outputFile, $content);
        chmod($outputFile, 0755);
        $this->line('✓ Generado: app/Services/FileAnalyzers/run_with_conda.sh');
    }
    
    private function backupAndWrite($filepath, $content)
    {
        // Hacer backup del archivo existente
        if (file_exists($filepath)) {
            $backupPath = $filepath . '.backup.' . date('Y-m-d_H-i-s');
            File::copy($filepath, $backupPath);
        }
        
        // Escribir nuevo contenido
        File::put($filepath, $content);
    }
}
