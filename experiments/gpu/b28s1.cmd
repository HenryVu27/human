@echo off
rem B28 seed 1 on the Windows box, prompts in reverse order (the Mac takes them in order; amendment 22:41).
rem One GPU-lock acquisition per pass of at most 1.8 hours, 2 minutes between passes. The Mac creates
rem C:\hgpu\b28_s1.stop once every prompt has a seed-1 sample. Logs to C:\hgpu\b28s1.log.
cd /d C:\hgpu
set PY=C:\hgpu\.venv\Scripts\python.exe
set PYTHONUTF8=1
set HF_HUB_DISABLE_PROGRESS_BARS=1
:pass
if exist b28_s1.stop goto done
echo [%date% %time%] pass
call gpu_job.cmd %PY% gen13b_guard.py --adapter out_essaypool/lora-13b-v1 --prompts b28_prompts_rev.jsonl --out b28_gen_s1_pc.jsonl --seed 1 --hours 1.8 --stop-file b28_s1.stop > b28s1_pass.log 2>&1
type b28s1_pass.log
findstr /c:"GEN_OK" b28s1_pass.log >nul && goto done
findstr /c:"STOPPED" b28s1_pass.log >nul && goto done
findstr /c:"HOURS_UP" b28s1_pass.log >nul || (echo FAILED & exit /b 1)
timeout /t 120 /nobreak >nul
goto pass
:done
echo [%date% %time%] ALL_DONE
