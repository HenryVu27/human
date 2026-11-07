"""Z5 on Modal: score texts with ProseLens-ModernBERT-L (rishanthrajendhran, CC BY-NC-SA; non-commercial research use).

Reads a JSONL of {id, text}; writes {id: p_ai} where p_ai = softmax probability of label "ai" (id 1). Texts longer
than the model's 8,192 tokens are scored as token-weighted means of 8,192-token chunks. One L4 (fallback A10G),
bf16, no training. Rules and analysis: experiments/z5_proselens.py.

  ~/.local/bin/modal run experiments/modal/z5_proselens.py --inp results/z5_inputs.jsonl --out results/z5_scores.json
"""

from __future__ import annotations

import json
import pathlib

import modal

app = modal.App("z5-proselens")
IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("torch==2.11.0", "transformers==5.22.1", "accelerate==1.15.0", "safetensors",
                    "huggingface_hub[hf_xet]", extra_index_url="https://download.pytorch.org/whl/cu128")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "TOKENIZERS_PARALLELISM": "false"})
)
MODEL = "rishanthrajendhran/ProseLens-ModernBERT-L"
MAXLEN = 8192


@app.function(image=IMAGE, gpu=["L4", "A10G"], timeout=3600)
def score(rows: list[dict]) -> dict[str, float]:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, torch_dtype=torch.bfloat16).cuda().eval()
    out = {}
    for r in rows:
        ids = tok(r["text"], add_special_tokens=False)["input_ids"]
        chunks = [ids[i:i + MAXLEN - 2] for i in range(0, max(1, len(ids)), MAXLEN - 2)]
        num = den = 0.0
        for c in chunks:
            x = torch.tensor([[tok.cls_token_id] + c + [tok.sep_token_id]]).cuda()
            with torch.no_grad():
                p = torch.softmax(model(input_ids=x).logits.float(), -1)[0, 1].item()
            num += p * len(c)
            den += len(c)
        out[r["id"]] = num / den
    return out


@app.local_entrypoint()
def main(inp: str, out: str):
    rows = [json.loads(line) for line in open(inp)]
    res = score.remote(rows)
    pathlib.Path(out).write_text(json.dumps(res))
    print(len(res), "scored")
