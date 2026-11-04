"""B2 on the dev set: does the base-model writer beat an instruct writer from the same notes?

Arms, all from the same editor plan per draft:
  draft    the AI draft unchanged
  claude   claude:sonnet writes from the notes (instruct control)
  base     the 9B base model writes from the notes (B2)
Records local detector P(AI), claim check and quality win rate against the draft.
"""

import argparse
import json
import statistics

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.quality import quality_pair
from humanizer.detect.score import Detector
from humanizer.pipeline.editor import edit_plan
from humanizer.pipeline.writer import write

BASE = f"mlx:{ROOT / 'models' / 'olmo2-13b-base-4bit'}"
ARMS = {"claude": "claude:sonnet", "base": BASE}
OUT = ROOT / "results" / "b2_dev_rows.jsonl"


def run(n: int, detector: str):
    drafts = [json.loads(line) for line in (ROOT / "data" / "drafts" / "dev.jsonl").open()][:n]
    det = Detector.load(ROOT / "models" / detector)
    done = {json.loads(line)["id"] for line in OUT.open()} if OUT.exists() else set()
    for d in drafts:
        if d["id"] in done:
            continue
        plan = edit_plan(d["text"])
        row = {"id": d["id"], "generator": d["generator"], "words_in": len(d["text"].split()),
               "draft_p_ai": det.score(d["text"]), "target_words": plan.target_words}
        for arm, writer in ARMS.items():
            text = write(plan, writer)
            cc = claim_check(d["text"], text)
            row[arm] = {"text": text, "words": len(text.split()), "p_ai": det.score(text),
                        "claim_pass": cc["pass"], "unsupported_specifics": cc["unsupported_specifics"],
                        "entailed": f"{cc['claims_entailed']}/{cc['claims_total']}",
                        "quality_vs_draft": quality_pair(d["text"], text)}
        with OUT.open("a") as f:
            f.write(json.dumps(row) + "\n")
        print(d["id"], row["draft_p_ai"], {a: round(row[a]["p_ai"], 3) for a in ARMS}, flush=True)
    summarize()


def summarize():
    rows = [json.loads(line) for line in OUT.open()]
    res = {"n": len(rows), "draft_mean_p_ai": statistics.mean(r["draft_p_ai"] for r in rows)}
    for arm in ARMS:
        res[arm] = {
            "mean_p_ai": statistics.mean(r[arm]["p_ai"] for r in rows),
            "share_below_0.5": sum(r[arm]["p_ai"] < 0.5 for r in rows) / len(rows),
            "claim_pass_rate": sum(r[arm]["claim_pass"] for r in rows) / len(rows),
            "quality_win_rate": statistics.mean(r[arm]["quality_vs_draft"] for r in rows),
            "mean_words": statistics.mean(r[arm]["words"] for r in rows),
        }
    (ROOT / "results" / "b2_dev.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--detector", default="detector-v2")
    a = ap.parse_args()
    run(a.n, a.detector)
