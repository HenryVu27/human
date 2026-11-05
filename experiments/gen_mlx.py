"""Generate from a prompts file with a local MLX model and adapter, the Mac twin of gpu/gen13b.py.

Same sampling: temperature 0.8, top_p 0.95, repetition penalty 1.05, stop at EOS or max_new_tokens.
With --guard, rows that carry "allowed_text" (the draft) get the Guard: names, numbers and quotes
may only be ones that text contains. Rows are appended as they finish and finished ids are skipped on restart, so a stopped run resumes.

Usage: uv run python experiments/gen_mlx.py PROMPTS OUT [--model DIR] [--adapter DIR] [--seed 0]
"""

import argparse
import json
from pathlib import Path

import mlx.core as mx
from mlx_lm import stream_generate
from mlx_lm.sample_utils import make_logits_processors, make_sampler

from humanizer import ROOT
from humanizer.llm import load_mlx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompts")
    ap.add_argument("out")
    ap.add_argument("--model", default=str(ROOT / "models" / "olmo2-13b-base-4bit"))
    ap.add_argument("--adapter", default=str(ROOT / "models" / "lora-13b-facts-mlx"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--guard", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    done = {json.loads(line)["id"] for line in out.open()} if out.exists() else set()
    rows = [r for r in map(json.loads, open(a.prompts)) if r["id"] not in done]
    model, tok = load_mlx(a.model, a.adapter)
    if a.guard:
        from humanizer.pipeline.sectional import QUOTES, Guard, allowed_specifics, common_capitalized
        common = common_capitalized()
    for r in rows:
        procs = make_logits_processors(repetition_penalty=1.05)
        if a.guard:
            src = r["allowed_text"]
            procs.append(Guard(tok, allowed_specifics(src, r["prompt"]), common,
                               allow_quotes=any(q in src for q in QUOTES)))
        mx.random.seed(a.seed)
        text, last = "", None
        for last in stream_generate(model, tok, r["prompt"], max_tokens=r["max_new_tokens"],
                                    sampler=make_sampler(temp=0.8, top_p=0.95),
                                    logits_processors=procs,
                                    prefill_step_size=512, kv_bits=4, quantized_kv_start=0):
            text += last.text
        text = text.split("\nFacts:")[0].split("\nNotes:")[0].strip()
        g = {"id": r["id"], "seed": a.seed, "text": text, "words": len(text.split()),
             "new_tokens": last.generation_tokens, "hit_eos": last.finish_reason == "stop"}
        with out.open("a") as f:
            f.write(json.dumps(g) + "\n")
        print(r["id"], g["words"], g["hit_eos"], f"{last.generation_tps:.1f} tok/s", flush=True)
    print("GEN_OK", flush=True)


if __name__ == "__main__":
    main()
