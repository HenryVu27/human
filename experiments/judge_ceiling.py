"""Human ceiling for the B2 quality metric: does the pairwise judge prefer the real
human article over the AI draft written on the same topic?

If human articles lose to the drafts, quality_win_rate rewards AI polish, and a
writer that sounds human cannot be expected to beat the draft on it.

Usage: uv run python experiments/judge_ceiling.py [--split dev]
"""

import argparse
import json
import statistics
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.quality import quality_pair

DATA = ROOT / "data"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    a = ap.parse_args()
    human = {d["id"]: d for d in map(json.loads, (DATA / "human.jsonl").open())}
    drafts = [json.loads(line) for line in (DATA / "drafts" / f"{a.split}.jsonl").open()]
    with ThreadPoolExecutor(4) as ex:
        wins = list(ex.map(lambda d: quality_pair(d["text"], human[d["source_id"]]["text"]), drafts))
    rows = [{"id": d["id"], "source_id": d["source_id"], "human_vs_draft": w,
             "human_words": len(human[d["source_id"]]["text"].split()), "draft_words": len(d["text"].split())}
            for d, w in zip(drafts, wins)]
    out = {"split": a.split, "n": len(rows), "human_win_rate": statistics.mean(wins), "rows": rows}
    (ROOT / "results" / f"judge_ceiling_{a.split}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}))


if __name__ == "__main__":
    main()
