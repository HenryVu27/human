@echo off
rem B30 on the Windows box: train the 13B rewriter (AI post to the essay) on data_rewritepool, B17's recipe,
rem max length 3,584 tokens. Generation runs on the Mac (and PC, by amendment). Logs to C:\hgpu\b30.log.
cd /d C:\hgpu
set PY=C:\hgpu\.venv\Scripts\python.exe
set PYTHONUTF8=1
set HF_HUB_DISABLE_PROGRESS_BARS=1
if not exist out_rewritepool mkdir out_rewritepool
echo [%date% %time%] train
call gpu_job.cmd %PY% train13b.py --data data_rewritepool --out out_rewritepool --max-len 3584 || exit /b 1
echo [%date% %time%] ALL_DONE
