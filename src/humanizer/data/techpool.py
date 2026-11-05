"""Pool-writer training pairs from the technical blog corpus (data/techblog.jsonl).

Same recipe as experiments/b7_pool.py on data/facts: Sonnet extracts each post's facts with the
FACTS prompt, the prompt keeps a random 20 to 60 percent of them (at least 3), and the target is
the whole post. The last 30 posts by id are held out for validation.
"""

from __future__ import annotations

import json
import random

from humanizer import ROOT
from humanizer.data.facts import FACTS, facts_prompt, parse_facts
from humanizer.data.lora import _fits
from humanizer.llm import claude_many

SRC = ROOT / "data" / "techblog.jsonl"
OUT = ROOT / "data" / "techpool"


def build():
    docs = [json.loads(line) for line in SRC.open()]
    texts = [_fits(d["text"]) for d in docs]
    raws = claude_many([FACTS.format(text=t) for t in texts], model="sonnet")
    rows, bad = [], 0
    for d, t, raw in zip(docs, texts, raws):
        try:
            f = parse_facts(raw)
        except Exception:  # noqa: BLE001
            bad += 1
            continue
        rnd = random.Random(f"tech{d['id']}")
        keep = rnd.sample(f.facts, min(len(f.facts), max(3, round(len(f.facts) * rnd.uniform(0.2, 0.6)))))
        f.facts = keep
        rows.append({"id": d["id"], "prompt": facts_prompt(f, len(t.split()), d["id"]), "completion": t,
                     "n_facts": len(keep)})
    OUT.mkdir(parents=True, exist_ok=True)
    valid, train = rows[-30:], rows[:-30]
    for name, part in (("train", train), ("valid", valid)):
        (OUT / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in part))
    meta = {"train": len(train), "valid": len(valid), "unparsed": bad}
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1))
    print(meta)


if __name__ == "__main__":
    build()
