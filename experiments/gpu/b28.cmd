@echo off
rem B28 seed 0 on the Windows box: the voice writer (out_essaypool) writes whole articles with the Guard
rem (gen13b_guard.py, resumable). One GPU-lock acquisition per pass of at most 1.8 hours, 2 minutes
rem between passes so umwelt can take a turn. Logs to C:\hgpu\b28.log.
cd /d C:\hgpu
set PY=C:\hgpu\.venv\Scripts\python.exe
set PYTHONUTF8=1
set HF_HUB_DISABLE_PROGRESS_BARS=1
:pass
echo [%date% %time%] pass
call gpu_job.cmd %PY% gen13b_guard.py --adapter out_essaypool/lora-13b-v1 --prompts b28_prompts.jsonl --out b28_gen_s0.jsonl --seed 0 --hours 1.8 > b28_pass.log 2>&1
type b28_pass.log
findstr /c:"GEN_OK" b28_pass.log >nul && goto done
findstr /c:"HOURS_UP" b28_pass.log >nul || (echo FAILED & exit /b 1)
timeout /t 120 /nobreak >nul
goto pass
:done
echo [%date% %time%] ALL_DONE
