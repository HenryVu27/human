@echo off
rem B30 generation on the Windows box (amendment of 23:10 in experiments/b30_rewriter.py): seeds 0 and 1.
cd /d C:\hgpu
call gen_loop.cmd out_rewritepool/lora-13b-v1 b30_prompts.jsonl b30_gen_s0.jsonl 0 b30s0 || exit /b 1
call gen_loop.cmd out_rewritepool/lora-13b-v1 b30_prompts.jsonl b30_gen_s1.jsonl 1 b30s1 || exit /b 1
echo [%date% %time%] ALL_DONE
