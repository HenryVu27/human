"""Batched guarded generation with a PEFT adapter on a 4-bit base (transformers), the B30 path at scale.

Used by B36 (experiments/b36_transfer.py) to run B30's rewriter section by section. It reproduces
experiments/gpu/gen13b_guard.py's settings: OLMo-2-1124-13B in 4-bit NF4 (double quantization, bf16 compute), the
adapter in its trained PEFT form, temperature 0.8, top-p 0.95, repetition penalty 1.05, the Guard
(src/humanizer/pipeline/guard.py, identical to the PC's copy) built per prompt from its allowed text and prompt,
quotes allowed only if the allowed text has any, the same common-word list, and the same output trimming. Two
differences, both fixed before any B36 text exists: prompts run in batches (each row keeps its own Guard; prompts
are left-padded with the tokenizer's pad token, which is not EOS), and the seed is set once per batch, so a draw
differs from gen13b_guard's per-prompt seeding but comes from the same distribution.

  modal run experiments/modal/lf_rewrite_hf.py --prompts results/b36_prompts.jsonl --out results/b36_gen.jsonl --seeds 0,1

Input rows: {"id", "prompt", "allowed_text", "max_new_tokens"}. Output rows: {"id", "seed", "text", "words",
"new_tokens", "hit_eos", "machine"}. Rows already in --out are skipped, so a run can resume.
"""

from __future__ import annotations

import json
import pathlib

import modal

ROOT = pathlib.Path(__file__).resolve().parents[2] if modal.is_local() else pathlib.Path("/")
SP = ROOT / "experiments" / "modal" / "assets"  # common.json moved here from a session scratchpad (2026-11-06, attempt 2; same file)
app = modal.App("lf-rewrite-hf")
VOL = modal.Volume.from_name("b31-weights")
BASE = "/vol/models/allenai/OLMo-2-1124-13B/main"
IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("torch==2.11.0", "transformers==5.22.1", "peft==0.21.2", "bitsandbytes==0.50.2",
                    "accelerate==1.15.0", "safetensors", "numpy", extra_index_url="https://download.pytorch.org/whl/cu128")
    .env({"HF_HUB_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1", "PYTHONUTF8": "1"})
    .add_local_file(ROOT / "src" / "humanizer" / "pipeline" / "guard.py", "/w/guard.py")
    .add_local_file(SP / "common.json", "/w/common.json")
)


@app.function(image=IMAGE, volumes={"/vol": VOL}, gpu="L40S", cpu=4, memory=32768, timeout=4 * 3600)
def gen(rows: list[dict], seed: int, adapter: str, batch: int = 8) -> list[dict]:
    import subprocess
    import sys

    import torch

    sys.path.insert(0, "/w")
    from guard import QUOTES, Guard, allowed_specifics
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, LogitsProcessorList

    tok = AutoTokenizer.from_pretrained(BASE)
    tok.padding_side = "left"
    pad = tok.pad_token_id
    if pad is None or pad == tok.eos_token_id:
        raise RuntimeError(f"need a pad token distinct from EOS, got {pad}")
    base = AutoModelForCausalLM.from_pretrained(
        BASE, device_map={"": 0}, attn_implementation="sdpa", dtype=torch.bfloat16,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                               bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16))
    model = PeftModel.from_pretrained(base, f"/vol/adapters/{adapter}").eval()
    common = set(json.load(open("/w/common.json", encoding="utf-8")))
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True,
                         text=True).stdout.strip()

    class RowGuards:
        """TorchGuard with one Guard per batch row (each prompt has its own allowed names and numbers)."""

        def __init__(self, guards):
            self.guards = guards

        def __call__(self, input_ids, scores):
            import numpy as np

            masks = [g.mask(r[-24:].tolist(), scores.shape[-1]) for g, r in zip(self.guards, input_ids)]
            return scores.masked_fill(torch.as_tensor(np.stack(masks), device=scores.device), float("-inf"))

    rows = sorted(rows, key=lambda r: -r["max_new_tokens"])
    out = []

    def run(chunk, b0):
        guards = [Guard(tok, allowed_specifics(r["allowed_text"], r["prompt"]), common,
                        allow_quotes=any(q in r["allowed_text"] for q in QUOTES)) for r in chunk]
        enc = tok([r["prompt"] for r in chunk], return_tensors="pt", padding=True).to("cuda")
        torch.manual_seed(seed * 100003 + b0)
        with torch.no_grad():
            gen_ids = model.generate(**enc, do_sample=True, temperature=0.8, top_p=0.95, repetition_penalty=1.05,
                                     max_new_tokens=max(r["max_new_tokens"] for r in chunk),
                                     logits_processor=LogitsProcessorList([RowGuards(guards)]),
                                     eos_token_id=tok.eos_token_id, pad_token_id=pad)
        res = []
        for r, seq in zip(chunk, gen_ids[:, enc["input_ids"].shape[1]:].tolist()):
            seq = seq[: r["max_new_tokens"]]
            cut = seq.index(tok.eos_token_id) if tok.eos_token_id in seq else len(seq)
            text = tok.decode(seq[:cut], skip_special_tokens=True).split("\nFacts:")[0].split("\nNotes:")[0].strip()
            res.append({"id": r["id"], "seed": seed, "text": text, "words": len(text.split()), "new_tokens": cut,
                        "hit_eos": cut < len(seq), "machine": f"modal-{gpu}"})
        return res

    def run_safe(chunk, b0):  # on out-of-memory, halve the batch (added 2026-11-06 for B37; draws are unchanged in kind)
        try:
            return run(chunk, b0)
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if len(chunk) == 1:
                raise
            h = len(chunk) // 2
            return run_safe(chunk[:h], b0) + run_safe(chunk[h:], b0 + h)

    for b0 in range(0, len(rows), batch):
        out += run_safe(rows[b0:b0 + batch], b0)
        print(f"seed {seed}: {len(out)}/{len(rows)}", flush=True)
    return out


@app.local_entrypoint()
def main(prompts: str, out: str, seeds: str = "0,1", adapter: str = "b30-rewritepool", batch: int = 8,
         containers: int = 2):
    rows = [json.loads(line) for line in pathlib.Path(prompts).read_text().splitlines()]
    path = pathlib.Path(out)
    done = {(r["id"], r["seed"]) for r in map(json.loads, path.read_text().splitlines())} if path.exists() else set()
    jobs = []
    for s in map(int, seeds.split(",")):
        todo = [r for r in rows if (r["id"], s) not in done]
        k = max(1, containers // len(seeds.split(",")))
        for i in range(k):
            part = todo[i::k]
            if part:
                jobs.append((part, s, adapter, batch))
    print(f"{sum(len(j[0]) for j in jobs)} generations in {len(jobs)} containers", flush=True)
    for res in gen.starmap(jobs, order_outputs=False, return_exceptions=True):
        if isinstance(res, Exception):
            print("CONTAINER_ERROR", repr(res)[:800], flush=True)
            continue
        with path.open("a") as f:
            f.writelines(json.dumps(r) + "\n" for r in res)
        print(f"wrote {len(res)} rows", flush=True)
