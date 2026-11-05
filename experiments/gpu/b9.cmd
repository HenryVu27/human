@echo off
rem B9 on the Windows box: dose-response generation with the B4 facts adapter (out_facts), in two
rem separate GPU-lock acquisitions so umwelt can take a turn in between. Logs to C:\hgpu\b9.log.
cd /d C:\hgpu
set PY=C:\hgpu\.venv\Scripts\python.exe
set PYTHONUTF8=1
set HF_HUB_DISABLE_PROGRESS_BARS=1
echo [%date% %time%] chunk 1
call gpu_job.cmd %PY% gen13b.py --data data_facts --out out_facts --prompts b9_prompts_1.jsonl --name b9_gen_1 --seeds 0 --no-base || exit /b 1
echo [%date% %time%] chunk 2
call gpu_job.cmd %PY% gen13b.py --data data_facts --out out_facts --prompts b9_prompts_2.jsonl --name b9_gen_2 --seeds 0 --no-base || exit /b 1
echo [%date% %time%] ALL_DONE
