"""Whole-article generation on the Windows GPU with the Guard, the PC twin of experiments/gen_mlx.py.

OLMo-2-13B (4-bit NF4) with one PEFT adapter, the Mac's sampling (temperature 0.8, top_p 0.95,
repetition penalty 1.05, stop at EOS or max_new_tokens) and the same Guard file (guard.py next to
this one), built as gen_mlx builds it: names and numbers from the allowed text and the prompt,
quotes if the allowed text has any. Writes gen_mlx's row format and skips ids already written, so a
run can stop at --hours (one GPU-lock acquisition) and the next run resumes.

Usage: python gen13b_guard.py --adapter out_essaypool/lora-13b-v1 --prompts p.jsonl --out g.jsonl --seed 0 [--hours 1.8] [--stop-file f]
"""

import argparse
import json
import os
import time

import torch

from guard import QUOTES, Guard, TorchGuard, allowed_specifics

MODEL = "allenai/OLMo-2-1124-13B"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--common", default="common.json")
    ap.add_argument("--hours", type=float, default=1.8)
    ap.add_argument("--stop-file", help="stop before the next prompt once this file exists")
    a = ap.parse_args()
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, LogitsProcessorList

    start = time.time()
    done = {json.loads(line)["id"] for line in open(a.out, encoding="utf-8")} if os.path.exists(a.out) else set()
    rows = [r for r in map(json.loads, open(a.prompts, encoding="utf-8")) if r["id"] not in done]
    tok = AutoTokenizer.from_pretrained(MODEL)
    base = AutoModelForCausalLM.from_pretrained(
        MODEL, device_map={"": 0}, attn_implementation="sdpa", dtype=torch.bfloat16,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                               bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16))
    model = PeftModel.from_pretrained(base, a.adapter).eval()
    common = set(json.load(open(a.common, encoding="utf-8")))
    for r in rows:
        if time.time() - start > a.hours * 3600:
            print("HOURS_UP", flush=True)
            return
        if a.stop_file and os.path.exists(a.stop_file):
            print("STOPPED", flush=True)
            return
        t0 = time.time()
        guard = Guard(tok, allowed_specifics(r["allowed_text"], r["prompt"]), common,
                      allow_quotes=any(q in r["allowed_text"] for q in QUOTES))
        ids = tok(r["prompt"], return_tensors="pt").input_ids.to("cuda")
        torch.manual_seed(a.seed)
        with torch.no_grad():
            out = model.generate(ids, attention_mask=torch.ones_like(ids), do_sample=True, temperature=0.8, top_p=0.95,
                                 repetition_penalty=1.05, max_new_tokens=r["max_new_tokens"],
                                 logits_processor=LogitsProcessorList([TorchGuard(guard)]),
                                 eos_token_id=tok.eos_token_id, pad_token_id=tok.eos_token_id)[0, ids.shape[1]:].tolist()
        cut = out.index(tok.eos_token_id) if tok.eos_token_id in out else len(out)
        text = tok.decode(out[:cut], skip_special_tokens=True).split("\nFacts:")[0].split("\nNotes:")[0].strip()
        g = {"id": r["id"], "seed": a.seed, "text": text, "words": len(text.split()), "new_tokens": cut,
             "hit_eos": cut < len(out), "machine": "pc"}
        with open(a.out, "a", encoding="utf-8") as f:
            f.write(json.dumps(g) + "\n")
        print(r["id"], g["words"], g["hit_eos"], f"{cut / (time.time() - t0):.1f} tok/s", flush=True)
    print("GEN_OK", flush=True)


if __name__ == "__main__":
    main()
