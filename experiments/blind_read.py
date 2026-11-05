"""Henry's blind read: does the pipeline's prose hold up next to human writing on the same topic?

The Sonnet quality judge is biased toward Sonnet's own style (judge_calibrate.json), so quality
needs a person. Each item puts pipeline pieces next to the human article their draft's topic came
from, all cut at a paragraph boundary after about 350 words, order shuffled. Henry answers which
reads best and, for every text, whether a person wrote it or a machine helped.

Fixed before Henry reads anything:
- Items: for drafts a0610 to a0615, one triad each: the human original, B14 cell B (best of 4,
  about 400 words) and B18 cell W (paragraph resampling). Each human text appears once, so memory
  of an earlier item cannot answer a later one.
- Controls: B12 cell K (Sonnet condensing the draft) against the human original on a0616 and a0617,
  2 pairs, to show whether plain instruct-model prose is easy to spot for this reader.
- Order within an item: random.Random("blind-read"), stored only in the key file, never on the page.
- Every text, human or machine, loses Markdown heading marks and bold markers, and every leading
  line until the first one of 12 or more words that ends like a sentence (titles, bylines, dates,
  navigation left over from scraping), so formatting and scraping debris give little away. Known
  leftovers: a0610's human text fuses its heading into its first sentence, and a0615's has a
  missing space from scraping. (Revised from a pair design before Henry read anything: the
  pair design showed each human text twice, and one control opened with a "# " heading.)

Usage:
  uv run python experiments/blind_read.py build     writes results/blind_pairs.json, results/blind_key.json and the page results/blind_read.html
  uv run python experiments/blind_read.py score results/blind_answers.json
"""

import json
import random
import re
import sys

from humanizer import ROOT

sys.path.insert(0, str(ROOT / "experiments"))
from judge_calibrate import _cut  # noqa: E402

PAIRS = ROOT / "results" / "blind_pairs.json"
KEY = ROOT / "results" / "blind_key.json"
OUT = ROOT / "results" / "blind_read.json"
PAGE = ROOT / "results" / "blind_read.html"  # published as Henry's private artifact; answers land in its db
TRIADS = ["a0610", "a0611", "a0612", "a0613", "a0614", "a0615"]
CONTROLS = ["a0616", "a0617"]
WORDS, MIN_LEAD, SENTENCE_END = 350, 12, (".", "?", "!", "\u201d", '"', ")")


def _plain(text: str) -> str:
    text = re.sub(r"^#+\s*", "", text.replace("**", "").replace("__", ""), flags=re.M)
    lines = text.strip().split("\n")
    while lines and not (len(lines[0].split()) >= MIN_LEAD and lines[0].rstrip().endswith(SENTENCE_END)):
        lines.pop(0)
    return "\n".join(lines)


def build():
    human = [json.loads(line)["text"] for line in (ROOT / "data" / "human.jsonl").open()]
    rows = {}
    for name in ("b14_texts.jsonl", "b18_texts.jsonl", "b12_texts.jsonl"):
        rows |= {r["id"]: r["text"] for r in map(json.loads, (ROOT / "results" / name).open())}
    text = lambda t: _cut(_plain(t), WORDS)  # noqa: E731
    items = [(k, {"human": text(human[int(k[1:])]), "B": text(rows[f"B_{k}"]), "W": text(rows[f"W_{k}"])})
             for k in TRIADS]
    items += [(k, {"human": text(human[int(k[1:])]), "K": text(rows[f"K_{k}"])}) for k in CONTROLS]
    rnd = random.Random("blind-read")
    rnd.shuffle(items)
    pairs, key = [], {}
    for i, (k, texts) in enumerate(items, 1):
        pid = f"p{i:02d}"
        cells = list(texts)
        rnd.shuffle(cells)
        letters = "ABC"[:len(cells)]
        pairs.append({"id": pid, "texts": [texts[c] for c in cells]})
        key[pid] = {"draft": k, "cells": dict(zip(letters, cells))}
    PAIRS.write_text(json.dumps(pairs, indent=1))
    KEY.write_text(json.dumps(key, indent=1))
    page = (ROOT / "experiments" / "blind_read_page.html").read_text()
    PAGE.write_text(page.replace("__PAIRS__", json.dumps(pairs).replace("</", "<\\/")))
    print(len(pairs), "items,", sum(len(t.split()) for p in pairs for t in p["texts"]), "words")


def score(path: str):
    """answers: {item id: {"best": "A"|"B"|"C"|"same", "labels": {"A": "person"|"machine"|"unsure"}, "note": str}}"""
    answers = json.loads(open(path).read())
    key = json.loads(KEY.read_text())
    out = {}
    for cell in ("human", "B", "W", "K"):
        seen = [(p, letter) for p, k in key.items() if p in answers for letter, c in k["cells"].items() if c == cell]
        labels = [answers[p].get("labels", {}).get(letter) for p, letter in seen]
        out[cell] = {"shown": len(seen), "best": sum(answers[p].get("best") == letter for p, letter in seen),
                     "called_person": labels.count("person"), "called_machine": labels.count("machine"),
                     "unsure": labels.count("unsure")}
    out["same"] = sum(a.get("best") == "same" for a in answers.values())
    OUT.write_text(json.dumps({"summary": out, "answers": answers}, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    build() if sys.argv[1] == "build" else score(sys.argv[2])
