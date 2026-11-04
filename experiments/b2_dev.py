"""B2 on the dev set: does the base-model writer beat an instruct writer from the same notes?

Arms, all from the same editor plan per draft:
  draft    the AI draft unchanged
  claude   claude:sonnet writes from the notes (instruct control)
  base     the 9B base model writes from the notes (B2)
Records local detector P(AI), claim check and quality win rate against the draft.

Two steps in separate processes so the 13B writer and the detector never share
GPU memory (one process holding both ran out of Metal memory on 2026-11-04):
  generate  editor plan and both writers' texts -> results/b2_dev_texts.jsonl
  score     detector, claim check, quality judge -> results/b2_dev_rows.jsonl
"""

import argparse
import json
import statistics

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.quality import quality_pair
from humanizer.pipeline.editor import edit_plan
from humanizer.pipeline.prune import prune
from humanizer.pipeline.writer import write

BASE = f"mlx:{ROOT / 'models' / 'olmo2-13b-base-4bit'}"
SEC = BASE.replace("mlx:", "sec:", 1)
# sec: sectional writer with the token-level guard (first run, 2026-11-04 morning).
# sec2: word-level guard, content-only notes and a minimum section length (cache "sectional-g3").
# sec2p: sec2 after the deletion-only pruner (no new words).
# lora: OLMo-2-7B base fine-tuned on (notes, human article), writing from dense notes the editor selected.
LORA = f"lora:{ROOT / 'models' / 'olmo2-7b-base-4bit'}+{ROOT / 'models' / 'lora-7b-v1'}"
# lora13, base13: 13B with and without the adapter, generated on the Windows GPU (experiments/import_gpu.py).
ARMS = {"claude": "claude:sonnet", "base": BASE, "sec": SEC, "sec2": SEC, "sec2p": "prune:sec2", "lora": LORA,
        "lora13": "import:gpu", "base13": "import:gpu"}
TEXTS = ROOT / "results" / "b2_dev_texts.jsonl"
OUT = ROOT / "results" / "b2_dev_rows.jsonl"


def generate(n: int, arms: list[str]):
    """Fill in any missing arm for the first n dev drafts; rows already written keep their texts."""
    drafts = [json.loads(line) for line in (ROOT / "data" / "drafts" / "dev.jsonl").open()][:n]
    rows = {r["id"]: r for r in map(json.loads, TEXTS.open())} if TEXTS.exists() else {}
    for d in drafts:
        row = rows.get(d["id"], {"id": d["id"]})
        missing = [a for a in arms if a not in row and not ARMS[a].startswith("import:")]
        if not missing:
            continue
        plan = edit_plan(d["text"])  # cached, so every arm sees the same plan
        row |= {"target_words": plan.target_words, "notes": plan.render_notes()}
        for a in missing:
            if ARMS[a].startswith("prune:"):
                row[a] = prune(d["text"], row[ARMS[a].split(":", 1)[1]])
            else:
                row[a] = write(plan, ARMS[a], draft=d["text"])
        rows[d["id"]] = row
        TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows.values()))
        print(d["id"], {a: len(row[a].split()) for a in arms}, flush=True)


def score(detector: str):
    drafts = {d["id"]: d for d in map(json.loads, (ROOT / "data" / "drafts" / "dev.jsonl").open())}
    from humanizer.detect.score import Detector

    det = Detector.load(ROOT / "models" / detector)
    OUT.write_text("")  # rescore everything; Claude checks are cached
    for t in map(json.loads, TEXTS.open()):
        d = drafts[t["id"]]
        row = {"id": d["id"], "generator": d["generator"], "words_in": len(d["text"].split()),
               "draft_p_ai": det.score(d["text"]), "target_words": t["target_words"]}
        for arm in [a for a in ARMS if a in t]:
            text = t[arm]
            cc = claim_check(d["text"], text)
            row[arm] = {"text": text, "words": len(text.split()), "p_ai": det.score(text),
                        "claim_pass": cc["pass"], "unsupported_specifics": cc["unsupported_specifics"],
                        "entailed": f"{cc['claims_entailed']}/{cc['claims_total']}",
                        "quality_vs_draft": quality_pair(d["text"], text)}
        with OUT.open("a") as f:
            f.write(json.dumps(row) + "\n")
        print(d["id"], round(row["draft_p_ai"], 3), {a: round(row[a]["p_ai"], 3) for a in ARMS if a in row}, flush=True)
    summarize()


def _share(frac: str) -> float:
    a, b = map(int, frac.split("/"))
    return a / b if b else 1.0


def summarize():
    rows = [json.loads(line) for line in OUT.open()]
    res = {"n": len(rows), "draft_mean_p_ai": statistics.mean(r["draft_p_ai"] for r in rows)}
    for arm in [a for a in ARMS if all(a in r for r in rows)]:
        res[arm] = {
            "mean_p_ai": statistics.mean(r[arm]["p_ai"] for r in rows),
            "share_below_0.5": sum(r[arm]["p_ai"] < 0.5 for r in rows) / len(rows),
            "claim_pass_rate": sum(r[arm]["claim_pass"] for r in rows) / len(rows),
            "no_new_specifics_rate": sum(not r[arm]["unsupported_specifics"] for r in rows) / len(rows),
            "entailed_share": statistics.mean(_share(r[arm]["entailed"]) for r in rows),
            "quality_win_rate": statistics.mean(r[arm]["quality_vs_draft"] for r in rows),
            "mean_words": statistics.mean(r[arm]["words"] for r in rows),
        }
    (ROOT / "results" / "b2_dev.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["generate", "score"])
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--arms", default="claude,base,sec2,sec2p")
    ap.add_argument("--detector", default="detector-v2")
    a = ap.parse_args()
    generate(a.n, a.arms.split(",")) if a.step == "generate" else score(a.detector)
