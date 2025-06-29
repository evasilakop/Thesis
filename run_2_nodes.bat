@echo off
REM Set your working directory and environment name
SET WORKDIR=C:\Users\eleni\Documents\GitHub\Thesis
SET NUM_NODES=4
SET ENV=xbtest

REM Node 0
start "" /D "%WORKDIR%" cmd.exe /K "CALL C:\Users\eleni\anaconda3\Scripts\activate.bat %ENV% && python main.py -i 0 -v video0.mp4 -n %NUM_NODES%"

REM Node 1
start "" /D "%WORKDIR%" cmd.exe /K "CALL C:\Users\eleni\anaconda3\Scripts\activate.bat %ENV% && python main.py -i 1 -v video1.mp4 -n %NUM_NODES%"

echo All nodes launched!