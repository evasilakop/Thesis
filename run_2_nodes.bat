@echo off
REM Edit these variables as needed:
set NUM_NODES=2
set VIDEO0=video0.mp4
set VIDEO1=video1.mp4
set MODEL=yolov8n.pt

REM Launch Node 0
start cmd /k "conda activate your_env_name && python main.py -i 0 -v %VIDEO0% -n %NUM_NODES% -m %MODEL%"

REM Launch Node 1
start cmd /k "conda activate your_env_name && python main.py -i 1 -v %VIDEO1% -n %NUM_NODES% -m %MODEL%"

REM Add more nodes as needed:
REM start cmd /k "conda activate your_env_name && python main.py -i 2 -v video2.mp4 -n %NUM_NODES% -m %MODEL%"
REM start cmd /k "conda activate your_env_name && python main.py -i 3 -v video3.mp4 -n %NUM_NODES% -m %MODEL%"

echo All nodes launched!