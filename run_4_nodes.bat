@echo off
REM Launch 4 nodes for the project, each in a separate window

REM set the workdir where the batch file is located
SET WORKDIR=%~dp0
SET ENV=thesis


REM Node 0
start "" /D "%WORKDIR%src" cmd.exe /K "CALL C:\ProgramData\miniconda3\condabin\activate.bat %ENV% && python -m main -i 0 -v ..\videos\video0.mp4 -n 4 -g"
ping 127.0.0.1 -n 2 -w 500 > nul

REM Node 1
start "" /D "%WORKDIR%src" cmd.exe /K "CALL C:\ProgramData\miniconda3\condabin\activate.bat %ENV% && python -m main -i 1 -v ..\videos\video1.mp4 -n 4 "
ping 127.0.0.1 -n 2 -w 500 > nul

REM Node 2
start "" /D "%WORKDIR%src" cmd.exe /K "CALL C:\ProgramData\miniconda3\condabin\activate.bat %ENV% && python -m main -i 2 -v ..\videos\video2.mp4 -n 4 "
ping 127.0.0.1 -n 2 -w 500 > nul

REM Node 3
start "" /D "%WORKDIR%src" cmd.exe /K "CALL C:\ProgramData\miniconda3\condabin\activate.bat %ENV% && python -m main -i 3 -v ..\videos\video3.mp4 -n 4 "

echo All nodes launched!