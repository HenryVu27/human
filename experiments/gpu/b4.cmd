@echo off
rem B4 on the Windows box: retrain the 13B adapter on fact-only notes, then write the 20 test pieces.
rem Inputs in C:\hgpu\data_facts (train.jsonl, valid.jsonl, b4_prompts.jsonl). Logs to C:\hgpu\b4.log.
cd /d C:\hgpu
set PY=C:\hgpu\.venv\Scripts\python.exe
set PYTHONUTF8=1
set HF_HUB_DISABLE_PROGRESS_BARS=1
if not exist out_facts mkdir out_facts
echo [%date% %time%] train
call gpu_job.cmd %PY% train13b.py --data data_facts --out out_facts || exit /b 1
echo [%date% %time%] generate
call gpu_job.cmd %PY% gen13b.py --data data_facts --out out_facts --prompts b4_prompts.jsonl --name b4_generations --seeds 0 --no-base || exit /b 1
echo [%date% %time%] ALL_DONE
