#!/bin/bash

# Set your environment and file paths
ENV_NAME=your_env_name
NUM_NODES=2
VIDEO0=video0.mp4
VIDEO1=video1.mp4
MODEL=yolov8n.pt

# Activate conda base first if needed
source ~/anaconda3/etc/profile.d/conda.sh

# Launch Node 0
gnome-terminal -- bash -c "conda activate $ENV_NAME && python main.py -i 0 -v $VIDEO0 -n $NUM_NODES -m $MODEL; exec bash"

# Launch Node 1
gnome-terminal -- bash -c "conda activate $ENV_NAME && python main.py -i 1 -v $VIDEO1 -n $NUM_NODES -m $MODEL; exec bash"

# Wait for a few seconds to ensure both nodes are launched
sleep 5

echo "All nodes launched!"