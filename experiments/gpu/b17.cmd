@echo off
rem B17 on the Windows box: train the 13B pool writer on first-person technical blog posts (data_techpool).
rem Generation runs on the Mac. Logs to C:\hgpu\b17.log.
cd /d C:\hgpu
set PY=C:\hgpu\.venv\Scripts\python.exe
set PYTHONUTF8=1
set HF_HUB_DISABLE_PROGRESS_BARS=1
if not exist out_techpool mkdir out_techpool
echo [%date% %time%] train
call gpu_job.cmd %PY% train13b.py --data data_techpool --out out_techpool || exit /b 1
echo [%date% %time%] ALL_DONE
