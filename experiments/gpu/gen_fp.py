"""Forced-prefix continuation with B30's rewriter, post by post (phase 2 step 3, P2c; rules in experiments/p2c_bakeoff.py).

For section k of a post the prompt is "Draft:\n{draft k-1}\n{draft k}\n\nRewrite:\n{chosen output k-1}" (k = 0: draft 0
alone), and the model continues it. This is B30's training shape: a draft, then a rewrite growing from its start. Each
section is sampled with every seed; the chosen continuation is the first, among those passing form.check_form against
draft k (non-English, new code at most 0, framing, headers, restarts for k > 0) with at least half of draft k's
words, that copies least from draft k in 8-word runs; if none passes, the longest. No prune, no cleanup, no deletion.
Settings as gen13b_guard.py (4-bit NF4 OLMo-2-13B, adapter, T 0.8, top-p 0.95, repetition penalty 1.05, the Guard
over the draft sections and the prefix); max new tokens 2.0 x words of draft k x 1.5 + 64, within the 4,096 window.

Usage: python gen_fp.py --adapter out_rewritepool/lora-13b-v1 --posts posts.jsonl --out out.jsonl --seeds 0,1 [--hours 1.8]
Input rows: {"doc", "sections": [draft section texts]}. Output rows: one per post, {"doc", "sections": [{k, chosen,
seed, candidates: [{seed, text, words, hit_eos, form_ok, copied}]}]}. Posts already in --out are skipped.
"""

import argparse
import json
import os
import time

import torch

from copying import copied_share
from form import check_form
from guard import QUOTES, Guard, TorchGuard, allowed_specifics

MODEL = "allenai/OLMo-2-1124-13B"
CONTEXT = 4096


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--posts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", default="0,1")
    ap.add_argument("--common", default="common.json")
    ap.add_argument("--hours", type=float, default=1.8)
    a = ap.parse_args()
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, LogitsProcessorList

    start = time.time()
    done = {json.loads(x)["doc"] for x in open(a.out, encoding="utf-8")} if os.path.exists(a.out) else set()
    posts = [p for p in map(json.loads, open(a.posts, encoding="utf-8")) if p["doc"] not in done]
    seeds = [int(s) for s in a.seeds.split(",")]
    tok = AutoTokenizer.from_pretrained(MODEL)
    base = AutoModelForCausalLM.from_pretrained(
        MODEL, device_map={"": 0}, attn_implementation="sdpa", dtype=torch.bfloat16,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                               bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16))
    model = PeftModel.from_pretrained(base, a.adapter).eval()
    common = set(json.load(open(a.common, encoding="utf-8")))
    for p in posts:
        if time.time() - start > a.hours * 3600:
            print("HOURS_UP", flush=True)
            return
        prev_out, out_secs = "", []
        for k, sec in enumerate(p["sections"]):
            draft = (p["sections"][k - 1] + "\n" + sec) if k else sec
            prompt = f"Draft:\n{draft}\n\nRewrite:\n" + (prev_out + "\n" if prev_out else "")
            enc = tok(prompt, return_tensors="pt").to("cuda")
            room = CONTEXT - enc["input_ids"].shape[1] - 8
            max_new = max(64, min(int(len(sec.split()) * 2.0 * 1.5) + 64, room))
            allowed = draft + "\n" + prev_out
            cands = []
            for s in seeds:
                guard = Guard(tok, allowed_specifics(allowed, prompt), common,
                              allow_quotes=any(q in allowed for q in QUOTES))
                torch.manual_seed(s * 100003 + k)
                with torch.no_grad():
                    g = model.generate(**enc, do_sample=True, temperature=0.8, top_p=0.95, repetition_penalty=1.05,
                                       max_new_tokens=max_new, logits_processor=LogitsProcessorList([TorchGuard(guard)]),
                                       eos_token_id=tok.eos_token_id, pad_token_id=tok.pad_token_id or tok.eos_token_id)
                ids = g[0, enc["input_ids"].shape[1]:].tolist()
                cut = ids.index(tok.eos_token_id) if tok.eos_token_id in ids else len(ids)
                text = tok.decode(ids[:cut], skip_special_tokens=True)
                text = text.split("\nDraft:")[0].split("\nFacts:")[0].split("\nNotes:")[0].strip()
                form = check_form(text, sec, later_section=k > 0, max_new_code=0)
                cands.append({"seed": s, "text": text, "words": len(text.split()), "hit_eos": cut < len(ids),
                              "form_ok": form["ok"], "copied": copied_share(text, sec)})
            ok = [c for c in cands if c["form_ok"] and c["words"] >= 0.5 * len(sec.split())]
            chosen = min(ok, key=lambda c: c["copied"]) if ok else max(cands, key=lambda c: c["words"])
            out_secs.append({"k": k, "chosen": chosen["seed"], "rule": "eligible" if ok else "longest",
                             "candidates": cands})
            prev_out = chosen["text"]
        with open(a.out, "a", encoding="utf-8") as f:
            f.write(json.dumps({"doc": p["doc"], "sections": out_secs}) + "\n")
        print(f"done {p['doc']} ({len(out_secs)} sections) {time.time() - start:.0f}s", flush=True)
    print("GEN_OK", flush=True)


if __name__ == "__main__":
    main()
