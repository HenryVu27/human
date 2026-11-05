@echo off
rem B7 on the Windows box: retrain the 13B adapter on partial fact pools (data_pool). Generation runs on the Mac.
rem Logs to C:\hgpu\b7.log. gpu_job.cmd waits for C:\gpu-lock, which umwelt shares.
cd /d C:\hgpu
set PY=C:\hgpu\.venv\Scripts\python.exe
set PYTHONUTF8=1
set HF_HUB_DISABLE_PROGRESS_BARS=1
if not exist out_pool mkdir out_pool
echo [%date% %time%] train
call gpu_job.cmd %PY% train13b.py --data data_pool --out out_pool || exit /b 1
echo [%date% %time%] ALL_DONE
