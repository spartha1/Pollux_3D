<?php

/**
 * Script para generar archivos de configuración portables
 * Este script lee las variables de entorno y genera los archivos .bat
 * necesarios para que el proyecto funcione en cualquier servidor.
 * 
 * Uso: php generate_portable_config.php
 */

require_once __DIR__ . '/vendor/autoload.php';

use Dotenv\Dotenv;

class PortableConfigGenerator
{
    private $basePath;
    private $config = [];
    
    public function __construct()
    {
        $this->basePath = __DIR__;
        $this->loadEnvironment();
        $this->detectPaths();
    }
    
    private function loadEnvironment()
    {
        // Cargar archivo .env si existe
        if (file_exists($this->basePath . '/.env')) {
            $dotenv = Dotenv::createImmutable($this->basePath);
            $dotenv->load();
        }
    }
    
    private function detectPaths()
    {
        $isWindows = PHP_OS_FAMILY === 'Windows';
        
        // Detectar conda root
        $condaRoot = $_ENV['CONDA_ROOT'] ?? getenv('CONDA_ROOT') ?? $this->detectCondaRoot();
        
        // Detectar conda env
        $condaEnv = $_ENV['CONDA_ENV'] ?? getenv('CONDA_ENV') ?? 'pollux-preview-env';
        
        // Construir rutas
        if ($isWindows) {
            $condaPrefix = $condaRoot . '\\envs\\' . $condaEnv;
            $pythonExecutable = $condaPrefix . '\\python.exe';
        } else {
            $condaPrefix = $condaRoot . '/envs/' . $condaEnv;
            $pythonExecutable = $condaPrefix . '/bin/python';
        }
        
        $this->config = [
            'PROJECT_ROOT' => $this->basePath,
            'CONDA_ROOT' => $condaRoot,
            'CONDA_ENV' => $condaEnv,
            'CONDA_PREFIX' => $condaPrefix,
            'PYTHON_EXECUTABLE' => $pythonExecutable,
            'IS_WINDOWS' => $isWindows,
        ];
        
        echo "🔍 Configuración detectada:\n";
        foreach ($this->config as $key => $value) {
            if ($key !== 'IS_WINDOWS') {
                echo "   {$key}: {$value}\n";
            }
        }
        echo "\n";
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
        
        throw new Exception("No se pudo detectar la instalación de conda. Configure CONDA_ROOT en .env");
    }
    
    public function generateScripts()
    {
        echo "🚀 Generando scripts portables...\n\n";
        
        if ($this->config['IS_WINDOWS']) {
            $this->generateManufacturingAnalyzerBat();
            $this->generateCondaWrapperBat();
        } else {
            $this->generateManufacturingAnalyzerSh();
            $this->generateCondaWrapperSh();
        }
        
        echo "✅ Scripts generados exitosamente!\n";
        echo "📝 Los archivos antiguos se respaldaron con extensión .backup\n\n";
        echo "🔧 Para migrar a otro servidor:\n";
        echo "   1. Copie todo el proyecto\n";
        echo "   2. Configure las variables en .env\n";
        echo "   3. Ejecute: php generate_portable_config.php\n";
        echo "   4. Los scripts se regenerarán automáticamente\n";
    }
    
    private function generateManufacturingAnalyzerBat()
    {
        $template = file_get_contents($this->basePath . '/run_manufacturing_analyzer_template.bat');
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
        
        $outputFile = $this->basePath . '/run_manufacturing_analyzer.bat';
        $this->backupAndWrite($outputFile, $content);
        echo "✓ Generado: run_manufacturing_analyzer.bat\n";
    }
    
    private function generateCondaWrapperBat()
    {
        $template = file_get_contents($this->basePath . '/app/Services/FileAnalyzers/run_with_conda_template.bat');
        $content = str_replace([
            '{{CONDA_ROOT}}',
            '{{CONDA_ENV}}',
            '{{PYTHON_EXECUTABLE}}'
        ], [
            $this->config['CONDA_ROOT'],
            $this->config['CONDA_ENV'],
            $this->config['PYTHON_EXECUTABLE']
        ], $template);
        
        $outputFile = $this->basePath . '/app/Services/FileAnalyzers/run_with_conda.bat';
        $this->backupAndWrite($outputFile, $content);
        echo "✓ Generado: app/Services/FileAnalyzers/run_with_conda.bat\n";
    }
    
    private function generateManufacturingAnalyzerSh()
    {
        $content = <<<EOL
#!/bin/bash
# Script dedicado para ejecutar el analizador de manufactura con entorno conda
# Generado automáticamente por generate_portable_config.php

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
        
        $outputFile = $this->basePath . '/run_manufacturing_analyzer.sh';
        $this->backupAndWrite($outputFile, $content);
        chmod($outputFile, 0755);
        echo "✓ Generado: run_manufacturing_analyzer.sh\n";
    }
    
    private function generateCondaWrapperSh()
    {
        $content = <<<EOL
#!/bin/bash
# Wrapper de conda multiplataforma
# Generado automáticamente por generate_portable_config.php

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
        
        $outputFile = $this->basePath . '/app/Services/FileAnalyzers/run_with_conda.sh';
        $this->backupAndWrite($outputFile, $content);
        chmod($outputFile, 0755);
        echo "✓ Generado: app/Services/FileAnalyzers/run_with_conda.sh\n";
    }
    
    private function backupAndWrite($filepath, $content)
    {
        // Hacer backup del archivo existente
        if (file_exists($filepath)) {
            $backupPath = $filepath . '.backup.' . date('Y-m-d_H-i-s');
            copy($filepath, $backupPath);
        }
        
        // Escribir nuevo contenido
        file_put_contents($filepath, $content);
    }
    
    public function validateConfiguration()
    {
        echo "🔍 Validando configuración...\n";
        
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
            echo "✅ Configuración válida!\n\n";
            return true;
        } else {
            echo "❌ Errores encontrados:\n";
            foreach ($errors as $error) {
                echo "   • {$error}\n";
            }
            echo "\n";
            return false;
        }
    }
}

// Ejecutar el generador
try {
    $generator = new PortableConfigGenerator();
    
    if ($generator->validateConfiguration()) {
        $generator->generateScripts();
    } else {
        echo "🚫 No se pueden generar scripts debido a errores de configuración.\n";
        echo "💡 Verifique las variables de entorno y la instalación de conda.\n";
        exit(1);
    }
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
    exit(1);
}
