@echo off
rem B26 on the Windows box: train the 13B voice writer on the essay corpus (data_essaypool).
rem Generation runs on the Mac. Logs to C:\hgpu\b26.log.
cd /d C:\hgpu
set PY=C:\hgpu\.venv\Scripts\python.exe
set PYTHONUTF8=1
set HF_HUB_DISABLE_PROGRESS_BARS=1
if not exist out_essaypool mkdir out_essaypool
echo [%date% %time%] train
call gpu_job.cmd %PY% train13b.py --data data_essaypool --out out_essaypool || exit /b 1
echo [%date% %time%] ALL_DONE
