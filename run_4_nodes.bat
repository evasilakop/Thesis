@echo off
REM Set your working directory and environment name
SET WORKDIR=C:\Users\eleni\Documents\GitHub\Thesis
SET ENV=xbtest

REM Node 0
start "" /D "%WORKDIR%" cmd.exe /K "CALL C:\Users\eleni\anaconda3\Scripts\activate.bat %ENV% && python main.py -i 0 -v video0.mp4 -n 4 -f 7"

REM Node 1
start "" /D "%WORKDIR%" cmd.exe /K "CALL C:\Users\eleni\anaconda3\Scripts\activate.bat %ENV% && python main.py -i 1 -v video1.mp4 -n 4 -f 7"

REM Launch node 2
start "" /D "%WORKDIR%" cmd.exe /K "CALL C:\Users\eleni\anaconda3\Scripts\activate.bat %ENV% && python main.py -i 2 -v video2.mp4 -n 4 -f 7 -g"

REM Launch node 3
start "" /D "%WORKDIR%" cmd.exe /K "CALL C:\Users\eleni\anaconda3\Scripts\activate.bat %ENV% && python main.py -i 3 -v video3.mp4 -n 4 -f 7"

echo All nodes launched!