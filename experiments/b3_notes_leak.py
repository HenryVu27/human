"""B3: does the AI signal reach the fine-tuned writer's output through the notes?

Same model (OLMo-2-13B + lora-13b-v1), same notes prompt, same sampling (seed 0).
Group A: notes made from AI drafts (dev a0600-a0609, the B2 lora13 arm).
Group B: notes made from held-out human articles (the first 10 rows of data/lora/valid.jsonl).
The selection is by file order only, fixed on 2026-11-04 before any of these texts was scanned.

If B reads human and A reads AI, the notes carry the signal. If both read AI, the writer does.

Usage:
  uv run python experiments/b3_notes_leak.py freeze
  PANGRAM_API_KEY=... uv run python experiments/b3_notes_leak.py scan [--max-usd 8]
"""

import argparse
import json
import statistics
import sys

from humanizer import ROOT

sys.path.insert(0, str(ROOT / "experiments"))
import pangram_api  # noqa: E402

GPU = ROOT / "results" / "gpu13b" / "out"
TEXTS = ROOT / "results" / "b3_notes_leak_texts.jsonl"
OUT = ROOT / "results" / "b3_notes_leak.json"
DEV_IDS = [f"a{i:04d}" for i in range(600, 610)]


def freeze():
    a = {g["id"]: g for g in map(json.loads, (GPU / "dev_generations.jsonl").open()) if g["seed"] == 0}
    b = [g for g in map(json.loads, (GPU / "valid_generations.jsonl").open()) if g["seed"] == 0][:10]
    rows = [{"group": "A_ai_notes", **a[i]} for i in DEV_IDS] + [{"group": "B_human_notes", **g} for g in b]
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "texts;", sum(r["words"] for r in rows), "words")


def scan(max_usd: float):
    rows = [json.loads(line) for line in TEXTS.open()]
    est = pangram_api.cost([r["text"] for r in rows])
    print(f"estimated ${est:.2f} for uncached texts")
    if est > max_usd:
        raise SystemExit(f"over --max-usd {max_usd}")
    for r in rows:
        res = pangram_api.scan(r["text"])
        r["pangram"] = {k: res.get(k) for k in ("version", "prediction_short", "headline", "fraction_ai",
                                                 "fraction_ai_assisted", "fraction_human")}
        print(r["group"], r["id"], r["words"], r["pangram"]["prediction_short"],
              round(r["pangram"]["fraction_ai"], 2), flush=True)
    summary = {}
    for g in ("A_ai_notes", "B_human_notes"):
        rs = [r for r in rows if r["group"] == g]
        summary[g] = {
            "n": len(rs),
            "verdicts": {v: sum(r["pangram"]["prediction_short"] == v for r in rs) for v in ("AI", "Mixed", "Human")},
            "mean_fraction_ai": statistics.mean(r["pangram"]["fraction_ai"] for r in rs),
            "mean_fraction_ai_assisted": statistics.mean(r["pangram"]["fraction_ai_assisted"] for r in rs),
            "mean_words": statistics.mean(r["words"] for r in rs),
        }
    OUT.write_text(json.dumps({"summary": summary, "rows": [{k: v for k, v in r.items() if k != "text"} for r in rows]},
                              indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["freeze", "scan"])
    ap.add_argument("--max-usd", type=float, default=8.0)
    a = ap.parse_args()
    freeze() if a.step == "freeze" else scan(a.max_usd)
