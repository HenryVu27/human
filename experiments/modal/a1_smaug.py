"""A1 cell S50 on Modal: Smaug-Humanizer (abacusai/Smaug-Humanizer, Apache 2.0, gemma-4-12B base) rewriting chunks.

Follows the model card exactly: one user turn with the card's PROMPT, the chat template, temperature 1.0, top-p
0.95, top-k 64, stop at <end_of_turn>, bf16, transformers (AutoModelForImageTextToText, as the card's Transformers
example). Batches of 8 prompts of similar length, left-padded; one torch seed per batch and seed. No Guard: the card's
recipe is run as published, and every output goes through the same prune, claim, form and copying checks as C50 and
C100 afterwards (experiments/a1_content.py).

  ~/.local/bin/modal run experiments/modal/a1_smaug.py --prompts results/a1_prompts_s50.jsonl --out results/a1_gen_s50.jsonl --seeds 0,1,2,3

Input rows: {"id", "text", "max_new_tokens"}. Output rows: {"id", "seed", "text", "words", "new_tokens", "hit_eos",
"machine"}. Rows already in --out are skipped.
"""

from __future__ import annotations

import json
import pathlib

import modal

app = modal.App("a1-smaug")
MODEL = "abacusai/Smaug-Humanizer"
IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("torch==2.11.0", "transformers==5.22.1", "accelerate==1.15.0", "safetensors", "pillow",
                    "huggingface_hub[hf_xet]", extra_index_url="https://download.pytorch.org/whl/cu128")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "TOKENIZERS_PARALLELISM": "false"})
)
CACHE = modal.Volume.from_name("b31-weights")
PROMPT = """Rewrite the AI-written text below so that it reads as if a person wrote it, in a person's own voice, wording and rhythm.

Keep every fact, number, name and quote. Keep the structure and the language of the text. Output only the rewritten text.

Text:
{text}"""


@app.function(image=IMAGE, volumes={"/vol": CACHE}, gpu=["L40S", "A100-80GB"], timeout=3 * 3600)
def generate(rows: list[dict], seeds: list[int]) -> list[dict]:
    import os

    import torch
    from transformers import AutoModelForImageTextToText, AutoTokenizer

    os.environ["HF_HOME"] = "/vol/hf"
    tok = AutoTokenizer.from_pretrained(MODEL)
    tok.padding_side = "left"
    model = AutoModelForImageTextToText.from_pretrained(MODEL, dtype=torch.bfloat16, device_map="cuda").eval()
    stop = tok.convert_tokens_to_ids("<end_of_turn>")
    machine = f"modal-{torch.cuda.get_device_name(0)}"
    out = []
    rows = sorted(rows, key=lambda r: len(r["text"]))
    for seed in seeds:
        for i in range(0, len(rows), 8):
            batch = rows[i:i + 8]
            chats = [tok.apply_chat_template([{"role": "user", "content": PROMPT.format(text=r["text"])}],
                                             add_generation_prompt=True, tokenize=False) for r in batch]
            enc = tok(chats, return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
            torch.manual_seed(seed * 100003 + i)
            with torch.no_grad():
                gen = model.generate(**enc, do_sample=True, temperature=1.0, top_p=0.95, top_k=64,
                                     max_new_tokens=max(r["max_new_tokens"] for r in batch),
                                     eos_token_id=[stop, tok.eos_token_id], pad_token_id=tok.pad_token_id,
                                     tokenizer=tok)  # the card: needed for the <end_of_turn> stop string
            for r, g in zip(batch, gen[:, enc["input_ids"].shape[1]:]):
                ids = g.tolist()
                hit = stop in ids or tok.eos_token_id in ids
                text = tok.decode(ids, skip_special_tokens=True).split("<end_of_turn>")[0].strip()
                out.append({"id": r["id"], "seed": seed, "text": text, "words": len(text.split()),
                            "new_tokens": sum(t != tok.pad_token_id for t in ids), "hit_eos": hit, "machine": machine})
    CACHE.commit()
    return out


@app.local_entrypoint()
def main(prompts: str, out: str, seeds: str = "0,1,2,3"):
    rows = [json.loads(line) for line in open(prompts)]
    done = set()
    p = pathlib.Path(out)
    if p.exists():
        done = {(json.loads(x)["id"], json.loads(x)["seed"]) for x in p.read_text().splitlines() if x.strip()}
    want = [int(s) for s in seeds.split(",")]
    todo_seeds = [s for s in want if any((r["id"], s) not in done for r in rows)]
    if not todo_seeds:
        print("nothing to do")
        return
    res = generate.remote(rows, todo_seeds)
    with p.open("a") as f:
        for r in res:
            if (r["id"], r["seed"]) not in done:
                f.write(json.dumps(r) + "\n")
    print(len(res), "generations")
