#!/usr/bin/env bash

# Adjust to point directly to your env’s Python
PYTHON="$HOME/.conda/envs/thesis/bin/python"
WORKDIR="/path/to/your/project"    # set this to the root of your repo

# Move into the src directory
cd "$WORKDIR/src" || {
  echo "ERROR: Cannot cd into $WORKDIR/src"
  exit 1
}

# Four parallel jobs, first one with -g
"$PYTHON" -m main -i 0 -v "../videos/video0.mp4" -n 4 -g &
"$PYTHON" -m main -i 1 -v "../videos/video1.mp4" -n 4 &
"$PYTHON" -m main -i 2 -v "../videos/video2.mp4" -n 4 &
"$PYTHON" -m main -i 3 -v "../videos/video3.mp4" -n 4 &

# Wait for all background jobs to finish
wait
echo "All processing done."