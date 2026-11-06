"""B38's J2 judge on Modal: ModernBERT-base fine-tuned to regress Pangram's AI share at document level.

Rules are in experiments/b38_judge.py. One L40S container runs every training of the evaluation: 5 folds grouped by
the group key (out-of-fold predictions), a leave-one-experiment-out model (trained without B36 and B37), and a model
on all data that scores the calibration candidates. Each training: 3 epochs, learning rate 3e-5, AdamW, linear decay,
batches of 8 texts of similar length, mean squared error on a sigmoid output, bf16 autocast, seed 0. Texts are cut
to 2,048 tokens for training; predictions on longer texts average 2,048-token chunks weighted by their tokens.

  modal run experiments/modal/lf_judge.py --data results/b38_data.jsonl --calib none --out results/b38_j2_preds.json
  modal run experiments/modal/lf_judge.py --data results/b38_data.jsonl --calib results/b38_calib_cands.jsonl --out results/b38_j2_preds.json --full-only
  (the evaluation runs first; the model on all data that scores the calibration candidates runs when they exist)
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import modal

app = modal.App("lf-judge")
IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("torch==2.11.0", "transformers==5.22.1", "accelerate==1.15.0", "safetensors",
                    "huggingface_hub[hf_xet]", extra_index_url="https://download.pytorch.org/whl/cu128")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "TOKENIZERS_PARALLELISM": "false"})
)
MODEL = "answerdotai/ModernBERT-base"
MAXLEN = 2048


def folds(rows: list[dict], k: int = 5) -> dict[str, int]:
    """Identical to experiments/b38_judge.py _folds: groups ordered by hash, largest first, to the lightest fold."""
    groups = sorted({r["group"] for r in rows}, key=lambda g: hashlib.sha256(f"b38-fold:{g}".encode()).hexdigest())
    sizes = {g: sum(r["group"] == g for r in rows) for g in groups}
    load, out = [0] * k, {}
    for g in sorted(groups, key=lambda g: -sizes[g]):
        f = min(range(k), key=lambda i: load[i])
        out[g] = f
        load[f] += sizes[g]
    return out


@app.function(image=IMAGE, gpu="L40S", cpu=4, memory=32768, timeout=3 * 3600)
def run(rows: list[dict], calib: list[dict], full_only: bool = False) -> dict:
    import random

    import torch
    from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup

    tok = AutoTokenizer.from_pretrained(MODEL)

    class Judge(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.enc = AutoModel.from_pretrained(MODEL)
            self.head = torch.nn.Linear(self.enc.config.hidden_size, 1)

        def forward(self, ids, att):
            h = self.enc(input_ids=ids, attention_mask=att).last_hidden_state
            m = att.unsqueeze(-1).float()
            return torch.sigmoid(self.head((h * m).sum(1) / m.sum(1)).squeeze(-1))

    enc_cache: dict[str, list[int]] = {}

    def ids_of(t: str) -> list[int]:
        if t not in enc_cache:
            enc_cache[t] = tok(t, add_special_tokens=False)["input_ids"]
        return enc_cache[t]

    def batchify(items, bs=8):
        items = sorted(items, key=lambda x: len(x[0]))
        return [items[i:i + bs] for i in range(0, len(items), bs)]

    def pad(chunk):
        L = max(len(x[0]) for x in chunk) + 2
        inp = torch.full((len(chunk), L), tok.pad_token_id, dtype=torch.long)
        att = torch.zeros((len(chunk), L), dtype=torch.long)
        for i, (ids, _) in enumerate(chunk):
            seq = [tok.cls_token_id] + ids + [tok.sep_token_id]
            inp[i, :len(seq)] = torch.tensor(seq)
            att[i, :len(seq)] = 1
        return inp.cuda(), att.cuda()

    def train(train_rows):
        torch.manual_seed(0)
        random.seed(0)
        model = Judge().cuda()
        items = [(ids_of(r["text"])[:MAXLEN - 2], r["target"]) for r in train_rows]
        batches = batchify(items)
        opt = torch.optim.AdamW(model.parameters(), lr=3e-5, weight_decay=0.01)
        steps = 3 * len(batches)
        sch = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps)
        model.train()
        for _ in range(3):
            random.shuffle(batches)
            for b in batches:
                inp, att = pad(b)
                y = torch.tensor([t for _, t in b], dtype=torch.float32, device="cuda")
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    p = model(inp, att)
                loss = torch.nn.functional.mse_loss(p.float(), y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                sch.step()
                opt.zero_grad()
        model.eval()
        return model

    @torch.no_grad()
    def predict(model, texts):
        chunks = []
        for i, t in enumerate(texts):
            ids = ids_of(t)
            for s in range(0, max(1, len(ids)), MAXLEN - 2):
                c = ids[s:s + MAXLEN - 2]
                if c or s == 0:
                    chunks.append((c, i))
        out = [[0.0, 0] for _ in texts]
        for b in batchify(chunks, 16):
            inp, att = pad(b)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                p = model(inp, att).float().cpu().tolist()
            for (c, i), v in zip(b, p):
                out[i][0] += v * max(1, len(c))
                out[i][1] += max(1, len(c))
        return [a / max(1, n) for a, n in out]

    fold = folds(rows)
    oof, loeo = {}, {}
    for f in ([] if full_only else range(5)):
        tr = [r for r in rows if fold[r["group"]] != f]
        te = [r for r in rows if fold[r["group"]] == f]
        m = train(tr)
        for r, p in zip(te, predict(m, [r["text"] for r in te])):
            oof[r["uid"]] = p
        del m
        torch.cuda.empty_cache()
        print(f"fold {f}: trained on {len(tr)}, predicted {len(te)}", flush=True)
    if not full_only:
        m = train([r for r in rows if not r["loeo_test"]])
        te = [r for r in rows if r["loeo_test"]]
        loeo = dict(zip([r["uid"] for r in te], predict(m, [r["text"] for r in te])))
        del m
        torch.cuda.empty_cache()
    cal = {}
    if calib:
        m = train(rows)
        cal = dict(zip([c["cid"] for c in calib], predict(m, [c["text"] for c in calib])))
    print("done", flush=True)
    return {"oof": oof, "loeo": loeo, "calib": cal, "folds": {r["uid"]: fold[r["group"]] for r in rows}}


@app.local_entrypoint()
def main(data: str, calib: str, out: str, full_only: bool = False):
    rows = [json.loads(line) for line in pathlib.Path(data).read_text().splitlines()]
    rows = [{k: r[k] for k in ("uid", "text", "target", "group", "loeo_test")} for r in rows]
    cal = [json.loads(line) for line in pathlib.Path(calib).read_text().splitlines()] if pathlib.Path(calib).exists() else []
    cal = [{"cid": c["cid"], "text": c["text"]} for c in cal]
    res = run.remote(rows, cal, full_only)
    prev = json.loads(pathlib.Path(out).read_text()) if pathlib.Path(out).exists() else {}
    merged = {k: (res[k] or prev.get(k, {})) for k in ("oof", "loeo", "calib", "folds")}
    pathlib.Path(out).write_text(json.dumps(merged))
    print(len(res["oof"]), "out-of-fold,", len(res["loeo"]), "leave-one-experiment-out,", len(res["calib"]), "calibration")
