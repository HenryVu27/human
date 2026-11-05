"""Henry's blind read: does the pipeline's prose hold up next to human writing on the same topic?

The Sonnet quality judge is biased toward Sonnet's own style (judge_calibrate.json), so quality
needs a person. Each pair puts a pipeline piece next to the human article its draft's topic came
from, both cut at a paragraph boundary after about 350 words, sides shuffled. Henry answers two
questions per pair: which reads better, and which one had a machine's help.

Fixed before Henry reads anything:
- Pipeline pieces: B14 cell B (best of 4, about 400 words) and B18 cell W (paragraph resampling,
  full length) on drafts a0610 to a0615, the first six by id: 12 pairs.
- Controls: B12 cell K (Sonnet condensing the draft) on a0616 and a0617, 2 pairs, to show
  whether plain instruct-model prose is easy to spot for this reader.
- Sides: random.Random("blind-read"), stored only in the key file, never on the page.

Usage:
  uv run python experiments/blind_read.py build     writes results/blind_pairs.json, results/blind_key.json and the page results/blind_read.html
  uv run python experiments/blind_read.py score results/blind_answers.json
"""

import json
import random
import sys

from humanizer import ROOT

sys.path.insert(0, str(ROOT / "experiments"))
from judge_calibrate import _cut  # noqa: E402

PAIRS = ROOT / "results" / "blind_pairs.json"
KEY = ROOT / "results" / "blind_key.json"
OUT = ROOT / "results" / "blind_read.json"
PAGE = ROOT / "results" / "blind_read.html"  # published as Henry's private artifact; answers land in its db
CELLS = [("b14_texts.jsonl", "B", ["a0610", "a0611", "a0612", "a0613", "a0614", "a0615"]),
         ("b18_texts.jsonl", "W", ["a0610", "a0611", "a0612", "a0613", "a0614", "a0615"]),
         ("b12_texts.jsonl", "K", ["a0616", "a0617"])]
WORDS = 350


def build():
    human = [json.loads(line)["text"] for line in (ROOT / "data" / "human.jsonl").open()]
    items = []
    for name, cell, keys in CELLS:
        rows = {r["id"]: r for r in map(json.loads, (ROOT / "results" / name).open())}
        for k in keys:
            items.append((cell, k, _cut(rows[f"{cell}_{k}"]["text"], WORDS), _cut(human[int(k[1:])], WORDS)))
    rnd = random.Random("blind-read")
    rnd.shuffle(items)
    pairs, key = [], {}
    for i, (cell, k, machine, person) in enumerate(items, 1):
        pid = f"p{i:02d}"
        machine_side = rnd.choice("AB")
        a, b = (machine, person) if machine_side == "A" else (person, machine)
        pairs.append({"id": pid, "a": a, "b": b})
        key[pid] = {"cell": cell, "draft": k, "machine": machine_side}
    PAIRS.write_text(json.dumps(pairs, indent=1))
    KEY.write_text(json.dumps(key, indent=1))
    page = (ROOT / "experiments" / "blind_read_page.html").read_text()
    PAGE.write_text(page.replace("__PAIRS__", json.dumps(pairs).replace("</", "<\\/")))
    print(len(pairs), "pairs,", sum(len(p["a"].split()) + len(p["b"].split()) for p in pairs), "words")


def score(path: str):
    """answers: {pair id: {"better": "A"|"B"|"same", "machine": "A"|"B"|"unsure", "note": str}}"""
    answers = json.loads(open(path).read())
    key = json.loads(KEY.read_text())
    out = {}
    for cell in "BWK":
        ids = [p for p, k in key.items() if k["cell"] == cell and p in answers]
        m = lambda p: key[p]["machine"]  # noqa: E731
        out[cell] = {
            "answered": len(ids),
            "pipeline_reads_better": sum(answers[p]["better"] == m(p) for p in ids),
            "human_reads_better": sum(answers[p]["better"] not in (m(p), "same") for p in ids),
            "same": sum(answers[p]["better"] == "same" for p in ids),
            "machine_spotted": sum(answers[p]["machine"] == m(p) for p in ids),
            "machine_missed": sum(answers[p]["machine"] not in (m(p), "unsure") for p in ids),
            "unsure": sum(answers[p]["machine"] == "unsure" for p in ids),
        }
    OUT.write_text(json.dumps({"summary": out, "answers": answers}, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    build() if sys.argv[1] == "build" else score(sys.argv[2])
