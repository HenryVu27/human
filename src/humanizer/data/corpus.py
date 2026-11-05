"""Pre-2022 human explanatory prose from FineWeb-Edu (written before ChatGPT)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from humanizer import ROOT

# Spread across years so one crawl's quirks do not dominate.
DUMPS = ["CC-MAIN-2017-34", "CC-MAIN-2019-30", "CC-MAIN-2020-50", "CC-MAIN-2021-31"]
BOILERPLATE = re.compile(r"cookie|subscribe|sign up|log in|javascript", re.I)


def keep_doc(row: dict) -> bool:
    year = int(row["dump"].split("-")[2])
    words = len(row["text"].split())
    return (
        year < 2022
        and 350 <= words <= 1500
        and row.get("int_score", 0) >= 3
        and not BOILERPLATE.search(row["text"][:200])
    )


def build_corpus(n: int, out: Path) -> int:
    from datasets import load_dataset

    per_dump = -(-n // len(DUMPS))
    out.parent.mkdir(parents=True, exist_ok=True)
    seen, kept = set(), 0
    with out.open("w") as f:
        for dump in DUMPS:
            got = 0
            for r in load_dataset("HuggingFaceFW/fineweb-edu", name=dump, split="train", streaming=True):
                head = r["text"][:300]
                if not keep_doc(r) or head in seen:
                    continue
                seen.add(head)
                f.write(json.dumps({"id": f"h{kept:04d}", "text": r["text"], "url": r["url"],
                                    "dump": r["dump"], "words": len(r["text"].split())}) + "\n")
                kept += 1
                got += 1
                if got >= per_dump or kept >= n:
                    break
            print(f"{dump}: {got}")
    return kept


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=900)
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "human.jsonl")
    a = ap.parse_args()
    print("kept", build_corpus(a.n, a.out))
