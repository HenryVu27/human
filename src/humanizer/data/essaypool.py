"""Writer training pairs from the essay corpus (data/essays.jsonl, split "train"), for B26's voice writer.

The pool writer learned from FineWeb pages and the B17 writer from first-person FineWeb tech posts;
neither saw a writer with a voice. Here each training essay (cut to MAX_WORDS, as data/lora) gets
B25's notes (the FACTS prompt, first person kept), and the target is the essay. All of the notes are
kept, not the pool recipe's random 20 to 60%: in the notes route the writer always has the blogger's
whole list, and a writer trained to write past its notes adds content the prune then deletes. The
last 30 essays by id are held out for validation. Bench essays never enter.
"""

from __future__ import annotations

import json

from humanizer import ROOT
from humanizer.data.essays import OUT as ESSAYS
from humanizer.data.facts import FACTS, facts_prompt, parse_facts
from humanizer.data.lora import _fits
from humanizer.llm import claude_many

OUT = ROOT / "data" / "essaypool"
NOTES = FACTS.replace("- Add nothing", "- Where the writer speaks of themself, keep the first person (\"I started a company in 1995\").\n- Add nothing")


def build():
    docs = sorted((r for r in map(json.loads, ESSAYS.open()) if r["split"] == "train"), key=lambda r: r["id"])
    texts = [_fits(d["text"]) for d in docs]
    raws = claude_many([NOTES.format(text=t) for t in texts], model="sonnet")
    rows, bad = [], 0
    for d, t, raw in zip(docs, texts, raws):
        try:
            f = parse_facts(raw)
        except Exception:  # noqa: BLE001
            bad += 1
            continue
        rows.append({"id": d["id"], "author": d["author"], "prompt": facts_prompt(f, len(t.split()), d["id"]),
                     "completion": t, "n_facts": len(f.facts)})
    OUT.mkdir(parents=True, exist_ok=True)
    valid, train = rows[-30:], rows[:-30]
    for name, part in (("train", train), ("valid", valid)):
        (OUT / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in part))
    meta = {"train": len(train), "valid": len(valid), "unparsed": bad}
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1))
    print(meta)


if __name__ == "__main__":
    build()
