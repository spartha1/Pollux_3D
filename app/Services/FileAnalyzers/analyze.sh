#!/bin/bash

# Cargar Conda en el contexto de bash
source /home/jerardo/miniconda3/etc/profile.d/conda.sh

# Activar el entorno
conda activate occ310

# Ejecutar el análisis Python con el archivo como argumento
python /home/jerardo/Documents/PolluxWeb/PolluxwWeb/app/Services/FileAnalyzers/main.py "$1"
