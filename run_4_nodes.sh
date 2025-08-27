#!/bin/bash

# Set your environment and file paths
ENV_NAME=your_env_name
NUM_NODES=4
VIDEO0=video0.mp4
VIDEO1=video1.mp4
VIDEO02=video2.mp4
VIDEO03=video3.mp4
MODEL=yolov8n.pt

# Activate conda base first if needed
source ~/anaconda3/etc/profile.d/conda.sh

# Launch Node 0
gnome-terminal -- bash -c "conda activate $ENV_NAME && python main.py -i 0 -v $VIDEO0 -n $NUM_NODES -m $MODEL; exec bash"

# Launch Node 1
gnome-terminal -- bash -c "conda activate $ENV_NAME && python main.py -i 1 -v $VIDEO1 -n $NUM_NODES -m $MODEL; exec bash"

# Launch Node 2
gnome-terminal -- bash -c "conda activate $ENV_NAME && python main.py -i 2 -v $VIDEO02 -n $NUM_NODES -m $MODEL; exec bash"

# Launch Node 3
gnome-terminal -- bash -c "conda activate $ENV_NAME && python main.py -i 3 -v $VIDEO03 -n $NUM_NODES -m $MODEL; exec bash"

echo "All nodes launched!"