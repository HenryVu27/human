"""Forced-prefix continuation with loop protection (phase 2, P2d; rules in experiments/p2d_bakeoff.py).

As gen_fp.py (B30 adapter, 4-bit NF4 OLMo-2-13B, Guard, T 0.8, top-p 0.95, repetition penalty 1.05; prompt for section
k: "Draft:\n{draft k-1}\n{draft k}\n\nRewrite:\n{chosen output k-1}"), with these changes:
- generation stops early when loops.trailing_loop fires (checked every 32 new tokens);
- max new tokens 2.4 x the section's words + 64, within the 4,096 window;
- seeds 0 and 1 are sampled; seeds 2 and 3 only if neither is clean. Clean: stopped by itself (EOS), not loops.is_loop,
  passes form.check_form (new code at most 0), and 0.5 to 1.6 times the section's words. The pick is the clean
  candidate copying least from the section (rule "eligible");
- with no clean candidate, each candidate is cut (loops.cut_loop, then to its last complete sentence) and the
  form-passing cut of at least half the section's words that copies least is taken (rule "cut"); otherwise the longest
  non-looping cut (rule "short"), which may be empty;
- a looped text is never carried forward: the prefix is the chosen text after cutting; an empty prefix restarts the
  prompt as for k = 0, with draft k alone.

Usage: python gen_fp2.py --adapter out_rewritepool/lora-13b-v1 --posts posts.jsonl --out out.jsonl [--hours 1.8]
Output rows: {"doc", "sections": [{k, chosen, rule, tried, candidates: [{seed, text, words, hit_eos, form_ok, copied,
loop, raw_words}]}]}. Posts already in --out are skipped.
"""

import argparse
import json
import os
import time

import torch

from copying import copied_share
from form import check_form
from guard import QUOTES, Guard, TorchGuard, allowed_specifics
from loops import cut_loop, is_loop, last_sentence, overlap_share, trailing_loop

MODEL = "allenai/OLMo-2-1124-13B"
CONTEXT = 4096


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--posts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--common", default="common.json")
    ap.add_argument("--hours", type=float, default=1.8)
    ap.add_argument("--limit", type=int, default=0, help="stop after this many posts (smoke test)")
    ap.add_argument("--independent", action="store_true", help="P2e: each section alone, no prefix (B30's own shape)")
    ap.add_argument("--max-overlap", type=float, default=1.0, help="P2e: reject a candidate sharing more than this "
                    "share of its word 4-grams with the post's earlier chosen sections")
    a = ap.parse_args()
    from peft import PeftModel
    from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, LogitsProcessorList,
                              StoppingCriteria, StoppingCriteriaList)

    start = time.time()
    done = {json.loads(x)["doc"] for x in open(a.out, encoding="utf-8")} if os.path.exists(a.out) else set()
    posts = [p for p in map(json.loads, open(a.posts, encoding="utf-8")) if p["doc"] not in done]
    if a.limit:
        posts = posts[:a.limit]
    tok = AutoTokenizer.from_pretrained(MODEL)
    base = AutoModelForCausalLM.from_pretrained(
        MODEL, device_map={"": 0}, attn_implementation="sdpa", dtype=torch.bfloat16,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                               bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16))
    model = PeftModel.from_pretrained(base, a.adapter).eval()
    common = set(json.load(open(a.common, encoding="utf-8")))

    class LoopStop(StoppingCriteria):
        def __init__(self, plen):
            self.plen = plen

        def __call__(self, ids, scores, **kw):
            n = ids.shape[1] - self.plen
            stop = n >= 64 and n % 32 == 0 and trailing_loop(tok.decode(ids[0, self.plen:], skip_special_tokens=True))
            return torch.full((ids.shape[0],), stop, dtype=torch.bool, device=ids.device)

    def sample(prompt, allowed, sec, k, seed, enc, max_new):
        guard = Guard(tok, allowed_specifics(allowed, prompt), common, allow_quotes=any(q in allowed for q in QUOTES))
        torch.manual_seed(seed * 100003 + k)
        with torch.no_grad():
            g = model.generate(**enc, do_sample=True, temperature=0.8, top_p=0.95, repetition_penalty=1.05,
                               max_new_tokens=max_new, logits_processor=LogitsProcessorList([TorchGuard(guard)]),
                               stopping_criteria=StoppingCriteriaList([LoopStop(enc["input_ids"].shape[1])]),
                               eos_token_id=tok.eos_token_id, pad_token_id=tok.pad_token_id or tok.eos_token_id)
        ids = g[0, enc["input_ids"].shape[1]:].tolist()
        cut = ids.index(tok.eos_token_id) if tok.eos_token_id in ids else len(ids)
        text = tok.decode(ids[:cut], skip_special_tokens=True)
        text = text.split("\nDraft:")[0].split("\nFacts:")[0].split("\nNotes:")[0].strip()
        form = check_form(text, sec, later_section=k > 0, max_new_code=0)
        return {"seed": seed, "text": text, "words": len(text.split()), "raw_words": len(text.split()),
                "hit_eos": cut < len(ids), "form_ok": form["ok"], "copied": copied_share(text, sec),
                "loop": is_loop(text)}

    for p in posts:
        if time.time() - start > a.hours * 3600:
            print("HOURS_UP", flush=True)
            return
        prev_out, out_secs = "", []
        for k, sec in enumerate(p["sections"]):
            n = len(sec.split())
            if a.independent:
                prev_out = ""
            draft = (p["sections"][k - 1] + "\n" + sec) if k and prev_out else sec
            prompt = f"Draft:\n{draft}\n\nRewrite:\n" + (prev_out + "\n" if prev_out else "")
            earlier = " ".join(s["_text"] for s in out_secs)
            enc = tok(prompt, return_tensors="pt").to("cuda")
            room = CONTEXT - enc["input_ids"].shape[1] - 8
            max_new = max(64, min(int(n * 2.4) + 64, room))
            allowed = draft + "\n" + prev_out
            clean = lambda c: (c["hit_eos"] and not c["loop"] and c["form_ok"] and 0.5 * n <= c["words"] <= 1.6 * n
                               and overlap_share(c["text"], earlier) <= a.max_overlap)
            cands = []
            for seed in (0, 1, 2, 3):
                if seed == 2 and any(clean(c) for c in cands):
                    break
                cands.append(sample(prompt, allowed, sec, k, seed, enc, max_new))
            ok = [c for c in cands if clean(c)]
            if ok:
                chosen, rule = min(ok, key=lambda c: c["copied"]), "eligible"
            else:
                for c in cands:  # keep only the sound part of each try
                    t = cut_loop(c["text"]) if c["loop"] or not c["hit_eos"] else c["text"]
                    t = last_sentence(t) if not c["hit_eos"] or c["loop"] else t
                    t = "" if is_loop(t) else t
                    form = check_form(t, sec, later_section=k > 0, max_new_code=0) if t else {"ok": False}
                    c.update(text=t, words=len(t.split()), form_ok=form["ok"], copied=copied_share(t, sec) if t else 0.0)
                cut_ok = [c for c in cands if c["form_ok"] and c["words"] >= 0.5 * n
                          and overlap_share(c["text"], earlier) <= a.max_overlap]
                if cut_ok:
                    chosen, rule = min(cut_ok, key=lambda c: c["copied"]), "cut"
                else:
                    pool = [c for c in cands if overlap_share(c["text"], earlier) <= a.max_overlap] or cands
                    chosen, rule = max(pool, key=lambda c: c["words"]), "short"
            out_secs.append({"k": k, "chosen": chosen["seed"], "rule": rule, "tried": len(cands), "candidates": cands,
                             "_text": chosen["text"]})
            prev_out = chosen["text"]
        with open(a.out, "a", encoding="utf-8") as f:
            f.write(json.dumps({"doc": p["doc"], "sections": [{k2: v for k2, v in s.items() if k2 != "_text"}
                                                              for s in out_secs]}) + "\n")
        rules = [s["rule"] for s in out_secs]
        print(f"done {p['doc']} ({len(out_secs)} sections; eligible {rules.count('eligible')}, cut {rules.count('cut')}, "
              f"short {rules.count('short')}) {time.time() - start:.0f}s", flush=True)
    print("GEN_OK", flush=True)


if __name__ == "__main__":
    main()
