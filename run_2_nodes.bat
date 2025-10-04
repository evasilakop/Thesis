@echo off
REM Adjust to point directly to your env’s Python
SET PYTHON=C:\Users\User\.conda\envs\thesis\python.exe

start "" /D "%WORKDIR%src" %PYTHON% -m main -i 0 -v ..\videos\video0.mp4 -n 4 -g
start "" /D "%WORKDIR%src" %PYTHON% -m main -i 1 -v ..\videos\video1.mp4 -n 4