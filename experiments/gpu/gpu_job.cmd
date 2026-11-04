@echo off
rem Run one GPU command under C:\gpu-lock, the lock shared with umwelt on this PC.
rem Usage: gpu_job.cmd <command and args>. Waits for the lock, releases it even if the command fails.
:lock
mkdir C:\gpu-lock 2>nul || (timeout /t 60 /nobreak >nul & goto lock)
echo humanizer %* (%date% %time%) > C:\gpu-lock\owner
%*
set RC=%errorlevel%
rmdir /s /q C:\gpu-lock
exit /b %RC%
