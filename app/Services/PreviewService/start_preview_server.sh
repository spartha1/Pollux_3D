#!/bin/bash

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate pollux-preview-env

# Start preview server
python preview_server.py

# If server stops, wait for input
read -p "Press enter to continue"
