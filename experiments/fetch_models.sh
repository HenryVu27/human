#!/bin/zsh
# Downloads and converts the local models. Re-runnable: hf skips finished files.
set -e
cd "$(dirname "$0")/.."
uv run hf download mlx-community/Qwen3.5-4B-MLX-4bit >/dev/null
echo "done: 4B instruct 4bit"
uv run hf download mlx-community/Qwen3.5-9B-MLX-4bit >/dev/null
echo "done: 9B instruct 4bit"
if [ ! -d models/qwen3.5-9b-base-4bit ]; then
  uv run hf download Qwen/Qwen3.5-9B-Base >/dev/null
  echo "done: 9B base bf16 download"
  uv run python -m mlx_lm convert --hf-path Qwen/Qwen3.5-9B-Base --mlx-path models/qwen3.5-9b-base-4bit -q --q-bits 4
  echo "done: 9B base converted"
fi
