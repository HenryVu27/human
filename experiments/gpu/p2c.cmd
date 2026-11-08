@echo off
rem P2c forced-prefix generation (experiments/p2c_bakeoff.py), resumable, in GPU-lock passes of at most 1.8 hours,
rem 2 minutes apart so umwelt can take a turn. Logs to C:\hgpu\p2c_pass.log; ALL_DONE at the end.
cd /d C:\hgpu
set PY=C:\hgpu\.venv\Scripts\python.exe
set PYTHONUTF8=1
set HF_HUB_DISABLE_PROGRESS_BARS=1
:pass
echo [%date% %time%] pass p2c
call gpu_job.cmd %PY% gen_fp.py --adapter out_rewritepool/lora-13b-v1 --posts p2c_posts.jsonl --out p2c_gen.jsonl --seeds 0,1 --hours 1.8 > p2c_pass.log 2>&1
type p2c_pass.log
findstr /c:"GEN_OK" p2c_pass.log >nul && goto done
findstr /c:"HOURS_UP" p2c_pass.log >nul || (echo FAILED & exit /b 1)
timeout /t 120 /nobreak >nul
goto pass
:done
echo [%date% %time%] ALL_DONE p2c
