@echo off
rem Resumable whole-article generation (gen13b_guard.py) in GPU-lock passes of at most 1.8 hours,
rem 2 minutes apart so umwelt can take a turn.
rem Usage: gen_loop.cmd ADAPTER PROMPTS OUT SEED NAME   (each pass logs to C:\hgpu\NAME_pass.log)
cd /d C:\hgpu
set PY=C:\hgpu\.venv\Scripts\python.exe
set PYTHONUTF8=1
set HF_HUB_DISABLE_PROGRESS_BARS=1
:pass
echo [%date% %time%] pass %5
call gpu_job.cmd %PY% gen13b_guard.py --adapter %1 --prompts %2 --out %3 --seed %4 --hours 1.8 > %5_pass.log 2>&1
type %5_pass.log
findstr /c:"GEN_OK" %5_pass.log >nul && goto done
findstr /c:"HOURS_UP" %5_pass.log >nul || (echo FAILED & exit /b 1)
timeout /t 120 /nobreak >nul
goto pass
:done
echo [%date% %time%] DONE %5
timeout /t 120 /nobreak >nul
