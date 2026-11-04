"""Generate the 20 dev pieces with the 13B LoRA writer (seeds 0 and 1) and the plain base model (seed 0).

Same sampling as the MLX writer: temperature 0.8, top_p 0.95, repetition penalty 1.05, stop at EOS.
No grounding guard here (it is an MLX logits processor), so new names or numbers are not blocked.

Usage: python gen13b.py --data DIR --out DIR [--prompts valid_prompts.jsonl --name valid_generations --seeds 0 --no-base]
"""

import argparse
import json

import torch

MODEL = "allenai/OLMo-2-1124-13B"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompts", default="dev_prompts.jsonl")
    ap.add_argument("--name", default="dev_generations")
    ap.add_argument("--seeds", default="0,1")
    ap.add_argument("--no-base", action="store_true")
    a = ap.parse_args()
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    tok = AutoTokenizer.from_pretrained(MODEL)
    base = AutoModelForCausalLM.from_pretrained(
        MODEL, device_map={"": 0}, attn_implementation="sdpa", dtype=torch.bfloat16,
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                               bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16))
    model = PeftModel.from_pretrained(base, f"{a.out}/lora-13b-v1").eval()
    rows = [json.loads(line) for line in open(f"{a.data}/{a.prompts}", encoding="utf-8")]

    def one(r, seed):
        ids = tok(r["prompt"], return_tensors="pt").input_ids.to("cuda")
        torch.manual_seed(seed)
        out = model.generate(ids, do_sample=True, temperature=0.8, top_p=0.95, repetition_penalty=1.05,
                             max_new_tokens=r["max_new_tokens"], eos_token_id=tok.eos_token_id,
                             pad_token_id=tok.eos_token_id)[0, ids.shape[1]:]
        hit = bool((out == tok.eos_token_id).any())
        text = tok.decode(out, skip_special_tokens=True).split("\nNotes:")[0].strip()
        return {"id": r["id"], "seed": seed, "text": text, "words": len(text.split()),
                "new_tokens": int(out.shape[0]), "hit_eos": hit}

    with open(f"{a.out}/{a.name}.jsonl", "w", encoding="utf-8") as f:
        for seed in map(int, a.seeds.split(",")):
            for r in rows:
                g = one(r, seed)
                f.write(json.dumps(g) + "\n")
                f.flush()
                print("lora", r["id"], seed, g["words"], g["hit_eos"], flush=True)
    if a.no_base:
        print("GEN_OK", flush=True)
        return
    with open(f"{a.out}/{a.name}_base.jsonl", "w", encoding="utf-8") as f, model.disable_adapter():
        for r in rows:
            g = one(r, 0)
            f.write(json.dumps(g) + "\n")
            f.flush()
            print("base", r["id"], g["words"], g["hit_eos"], flush=True)
    print("GEN_OK", flush=True)


if __name__ == "__main__":
    main()
