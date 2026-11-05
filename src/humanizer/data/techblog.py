"""Pre-2022 first-person technical blog posts from FineWeb-Edu, for a genre-matched pool writer.

B15 showed the pool writer, trained on general web articles, mangles a first-person technical
essay (Henry's context-engineering post): lists turn into fragments and "I" becomes "the author".
This collects the genre it never saw: posts written in the first person about software, data or
machine learning, from blog-like sites, written before ChatGPT. Same dumps and length rules as
data/corpus.py.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from humanizer import ROOT
from humanizer.data.corpus import BOILERPLATE, DUMPS

BLOGGY = re.compile(r"blog|medium\.com|dev\.to|towardsdatascience|wordpress|github\.io|substack|hashnode|"
                    r"/posts?/|/\d{4}/\d{2}/", re.I)
TECH = re.compile(r"\b(code|python|javascript|api|model|data(set)?|algorithm|software|server|database|"
                  r"neural|machine learning|training|compiler|function|library|framework|deploy|query|"
                  r"latency|cache|token|gpu|kubernetes|docker|regression|gradient)\b", re.I)
FIRST = re.compile(r"\b(I|I'm|I've|my|we|we're|our)\b")


def keep_doc(row: dict) -> bool:
    text, words = row["text"], len(row["text"].split())
    if int(row["dump"].split("-")[2]) >= 2022 or not 400 <= words <= 1500 or BOILERPLATE.search(text[:200]):
        return False
    tech = len(TECH.findall(text)) / words
    first = len(FIRST.findall(text)) / words
    return first >= 0.012 and tech >= 0.012 and (bool(BLOGGY.search(row["url"])) or tech >= 0.025)


def build(n: int, out: Path) -> int:
    from datasets import load_dataset

    per_dump = -(-n // len(DUMPS))
    out.parent.mkdir(parents=True, exist_ok=True)
    seen, kept = set(), 0
    with out.open("w") as f:
        for dump in DUMPS:
            got = 0
            for r in load_dataset("HuggingFaceFW/fineweb-edu", name=dump, split="train", streaming=True):
                head = r["text"][:300]
                if head in seen or not keep_doc(r):
                    continue
                seen.add(head)
                f.write(json.dumps({"id": f"t{kept:04d}", "text": r["text"], "url": r["url"], "dump": r["dump"],
                                    "words": len(r["text"].split())}) + "\n")
                kept += 1
                got += 1
                if got >= per_dump or kept >= n:
                    break
            print(f"{dump}: {got}", flush=True)
    return kept


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=700)
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "techblog.jsonl")
    a = ap.parse_args()
    print("kept", build(a.n, a.out))
