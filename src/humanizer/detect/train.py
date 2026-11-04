"""Train the local detector: human corpus vs synthetic mirrors, split by topic.

With hard=True it also trains on AI continuations, rewrites and "sound human"
pieces (data/ai_hard.jsonl), and on random crops, so it cannot key on how a
document starts or how long it is. Stress metrics test it on the B1
continuations and the dev drafts, none of which it trained on.
Writes the checkpoint to models/<name>/ and metrics to results/<name>.json.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from humanizer import ROOT
from humanizer.detect.score import WINDOW, Detector, normalize, windows

BASE = "answerdotai/ModernBERT-base"


OPEN_WORDS = 120  # continuations in ai_hard.jsonl and B1 start after this many words


def load_pairs(exclude_generator: str | None = None, hard: bool = False):
    human = {r["id"]: r for r in map(json.loads, (ROOT / "data/human.jsonl").open())}
    ai = [json.loads(line) for line in (ROOT / "data/ai.jsonl").open()]
    if hard:
        ai += [json.loads(line) for line in (ROOT / "data/ai_hard.jsonl").open()]
    docs = []
    for a in ai:
        if exclude_generator and a["generator"].startswith(exclude_generator):
            continue
        h = human[a["source_id"]]["text"]
        if a.get("kind") == "continuation":  # match like with like: the human text's own continuation
            h = " ".join(h.split()[OPEN_WORDS:])
        docs.append({"topic": a["source_id"], "text": a["text"], "label": 1, "gen": a["generator"]})
        docs.append({"topic": a["source_id"], "text": h, "label": 0, "gen": "human"})
    return docs


def crops(ids: list[int], k: int, rng: random.Random, lo: int = 64, hi: int = WINDOW - 2) -> list[list[int]]:
    """k windows of random length in [lo, hi] at random offsets, to hide start-of-document and length cues."""
    if len(ids) < lo:
        return []
    out = []
    for _ in range(k):
        n = rng.randint(lo, min(hi, len(ids)))
        s = rng.randint(0, len(ids) - n)
        out.append(ids[s:s + n])
    return out


def stress(det) -> dict:
    """AUROC on texts the detector never trained on: B1 continuations and dev drafts against dev human text."""
    dev = [json.loads(line) for line in (ROOT / "data/human.jsonl").open()][600:700]
    out = {}
    b1 = ROOT / "results/b1_generations.jsonl"
    if b1.exists():
        rows = [json.loads(line) for line in b1.open()]
        ids = {r["source_id"] for r in rows}
        hs = [det.score(" ".join(d["text"].split()[OPEN_WORDS:OPEN_WORDS + 450])) for d in dev if d["id"] in ids]
        for m in sorted({r["model"] for r in rows}):
            s = [det.score(r["continuation"]) for r in rows if r["model"] == m and len(r["continuation"].split()) > 50]
            out[f"b1_{m}_auroc"] = auroc([1] * len(s) + [0] * len(hs), s + hs)
            out[f"b1_{m}_flagged"] = sum(x > 0.5 for x in s) / len(s)
        out["b1_human_flagged"] = sum(x > 0.5 for x in hs) / len(hs)
    drafts = [json.loads(line) for line in (ROOT / "data/drafts/dev.jsonl").open()][:50]
    hs = [det.score(d["text"]) for d in dev[:50]]
    ds = [det.score(d["text"]) for d in drafts]
    out["dev_drafts_auroc"] = auroc([1] * len(ds) + [0] * len(hs), ds + hs)
    out["dev_drafts_flagged"] = sum(x > 0.5 for x in ds) / len(ds)
    out["dev_human_flagged"] = sum(x > 0.5 for x in hs) / len(hs)
    return out


def split_topics(docs, seed=0):
    topics = sorted({d["topic"] for d in docs})
    random.Random(seed).shuffle(topics)
    n = len(topics)
    tr, va = set(topics[: int(0.8 * n)]), set(topics[int(0.8 * n): int(0.9 * n)])
    pick = lambda s: [d for d in docs if d["topic"] in s]  # noqa: E731
    return pick(tr), pick(va), [d for d in docs if d["topic"] not in tr | va]


def auroc(labels, scores) -> float:
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(labels, scores))


def train(name: str, exclude_generator: str | None = None, epochs: int = 2, lr: float = 3e-5,
          hard: bool = False) -> dict:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForSequenceClassification.from_pretrained(BASE, num_labels=2).to(device)
    tr, va, te = split_topics(load_pairs(exclude_generator, hard))

    examples = []
    crop_rng = random.Random(1)
    for d in tr:
        ids = tok(normalize(d["text"]), add_special_tokens=False)["input_ids"]
        ws = [w for w in windows(ids, WINDOW - 2, WINDOW - 2) if len(w) >= 64]
        if hard:
            ws += crops(ids, 2, crop_rng)
        for w in ws:
            examples.append(([tok.cls_token_id, *w, tok.sep_token_id], d["label"]))
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    steps = epochs * (len(examples) // 8 + 1)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps, pct_start=0.1)
    model.train()
    rng = random.Random(0)
    for ep in range(epochs):
        rng.shuffle(examples)
        for b in range(0, len(examples), 8):
            batch = examples[b:b + 8]
            L = max(len(x) for x, _ in batch)
            ids = torch.tensor([x + [tok.pad_token_id] * (L - len(x)) for x, _ in batch], device=device)
            mask = (ids != tok.pad_token_id).long()
            y = torch.tensor([lab for _, lab in batch], device=device)
            loss = model(input_ids=ids, attention_mask=mask, labels=y).loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            if (b // 8) % 50 == 0:
                print(f"epoch {ep} step {b // 8} loss {loss.item():.4f}", flush=True)
    model.eval()
    out = ROOT / "models" / name
    model.save_pretrained(out)
    tok.save_pretrained(out)

    det = Detector(model, tok, device)
    metrics = {"name": name, "exclude_generator": exclude_generator, "hard": hard, "train_docs": len(tr),
               "train_windows": len(examples)}
    for split, docs in [("val", va), ("test", te)]:
        scores = [det.score(d["text"]) for d in docs]
        metrics[f"{split}_auroc"] = auroc([d["label"] for d in docs], scores)
    if exclude_generator:
        held = [d for d in load_pairs() if d["gen"].startswith(exclude_generator) or d["gen"] == "human"]
        held_topics = {d["topic"] for d in held if d["label"] == 1}
        held = [d for d in held if d["topic"] in held_topics and d["topic"] not in {x["topic"] for x in tr}]
        metrics["heldout_generator_auroc"] = auroc([d["label"] for d in held], [det.score(d["text"]) for d in held])
        metrics["heldout_generator_docs"] = len(held)
    metrics["stress"] = stress(det)
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / f"{name}.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="detector-v1")
    ap.add_argument("--exclude-generator")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--hard", action="store_true", help="add data/ai_hard.jsonl and random crops")
    ap.add_argument("--stress-only", action="store_true", help="score an existing models/<name> on the stress sets")
    a = ap.parse_args()
    if a.stress_only:
        print(json.dumps(stress(Detector.load(ROOT / "models" / a.name)), indent=1))
    else:
        train(a.name, a.exclude_generator, a.epochs, hard=a.hard)
