@echo off
rem B28's remaining samples on the Windows box (amendment of 23:10 in experiments/b28_dose.py):
rem the rest of seed 0 (b28_gen_s0.jsonl holds both machines' rows, so those are skipped), then the
rem rest of seed 1 in reverse order.
cd /d C:\hgpu
if exist b28_s1.stop del b28_s1.stop
call gen_loop.cmd out_essaypool/lora-13b-v1 b28_prompts.jsonl b28_gen_s0.jsonl 0 b28s0 || exit /b 1
call gen_loop.cmd out_essaypool/lora-13b-v1 b28_prompts_rev.jsonl b28_gen_s1_pc.jsonl 1 b28s1r || exit /b 1
echo [%date% %time%] ALL_DONE
