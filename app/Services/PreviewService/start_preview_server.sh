#!/bin/bash

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate polluxw

# Start preview server
python simple_preview_server.py

# If server stops, wait for input
read -p "Press enter to continue"
