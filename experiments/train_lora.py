"""Train the LoRA writer on data/lora (notes -> human article) with mlx-lm.

mlx-lm's completions format goes through the tokenizer's chat template, and a
base model has none. The fix is a sibling model directory whose template is
plain concatenation (notes, then article, then EOS), so prompt masking works and
no role tokens are ever trained. Weights are symlinked, not copied.

13B at 2,048 tokens ran out of Metal memory on 16 GB (2026-11-04); 7B is the local writer.
max-seq-length 2,560 covers 95% of pairs (dense notes plus article); longer ones are truncated.
"""

import argparse
import json
import subprocess
import sys

from humanizer import ROOT

TEMPLATE = "{% for m in messages %}{{ m['content'] }}{% if m['role'] == 'assistant' %}{{ eos_token }}{% endif %}{% endfor %}"


def notes_model(src: str) -> str:
    src_dir = (ROOT / src).resolve()
    dst = src_dir.with_name(src_dir.name + "-notes")
    dst.mkdir(exist_ok=True)
    for f in src_dir.iterdir():
        t = dst / f.name
        if f.name == "tokenizer_config.json":
            cfg = json.loads(f.read_text())
            cfg["chat_template"] = TEMPLATE
            t.write_text(json.dumps(cfg, indent=1))
        elif not t.exists():
            t.symlink_to(f)
    return str(dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/olmo2-7b-base-4bit")
    ap.add_argument("--name", default="lora-7b-v1")
    ap.add_argument("--iters", type=int, default=600)
    ap.add_argument("--data", default=str(ROOT / "data" / "lora"))
    a = ap.parse_args()
    out = ROOT / "models" / a.name
    cmd = [sys.executable, "-m", "mlx_lm", "lora", "--model", notes_model(a.model), "--train",
           "--data", a.data, "--mask-prompt", "--batch-size", "1", "--grad-accumulation-steps", "4",
           "--num-layers", "32", "--grad-checkpoint", "--max-seq-length", "2560",
           "--learning-rate", "1e-4", "--iters", str(a.iters), "--steps-per-report", "10",
           "--steps-per-eval", "100", "--val-batches", "30", "--save-every", "100",
           "--adapter-path", str(out)]
    print(" ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
