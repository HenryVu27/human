@echo off
rem P2d forced-prefix generation with loop protection (experiments/p2d_bakeoff.py), resumable, in GPU-lock passes of
rem at most 1.8 hours, 2 minutes apart so umwelt can take a turn. ALL_DONE or FAILED at the end of p2d_run.log.
cd /d C:\hgpu
set PY=C:\hgpu\.venv\Scripts\python.exe
set PYTHONUTF8=1
set HF_HUB_DISABLE_PROGRESS_BARS=1
:pass
echo [%date% %time%] pass p2d
call gpu_job.cmd %PY% gen_fp2.py --adapter out_rewritepool/lora-13b-v1 --posts p2c_posts.jsonl --out p2d_gen.jsonl --hours 1.8 > p2d_pass.log 2>&1
type p2d_pass.log
findstr /c:"GEN_OK" p2d_pass.log >nul && goto done
findstr /c:"HOURS_UP" p2d_pass.log >nul || (echo FAILED & exit /b 1)
timeout /t 120 /nobreak >nul
goto pass
:done
echo [%date% %time%] ALL_DONE p2d
