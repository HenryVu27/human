"""Fact-only notes (B4): what a text states, with nothing of how it is built.

B3 showed the fine-tuned writer reads as human on Pangram when its notes come from
a human article and as AI when they come from an AI draft. Sectioned notes carry
the source's architecture: its parts, order, headings, contrasts and emphasis. A
human editor cutting an AI draft keeps the facts and throws that away. Here the
notes are a shuffled list of standalone facts under a neutral topic, so the writer
has to choose structure itself, and it is trained on the same shape.

Same corpus ranges and the same 30 validation articles as data/lora.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
from dataclasses import dataclass

from humanizer import ROOT
from humanizer.data.lora import TRAIN_IDS, _fits
from humanizer.llm import claude, claude_many

OUT = ROOT / "data" / "facts"

FACTS = """Below is a text. List every fact it states, so that someone could write about the same material without ever seeing the text.

- One fact per item: a terse, standalone fragment that makes sense on its own, in neutral wording.
- Keep every name, number, date and quoted phrase exactly. Quotes stay in quotation marks with who said them.
- Keep the content of advice, examples and claims, stated flatly ("fixed schedule helps sleep"), but not their framing.
- Leave out everything about how the text is built: headings, order, which point matters most, rhetorical questions, transitions, hooks, recaps, conclusions, and statements with no content of their own.
- No contrasts: never write "not X but Y", "rather than", "instead of", "not just"; state only what is the case.
- No category labels or prefixes ("Benefits:", "For children:"); one fact per item, written out.
- Add nothing that is not in the text.

Return only JSON: {{"topic": "neutral topic in 3 to 8 words", "facts": ["fact", "fact"]}}

<text>
{text}
</text>"""


REWORD = """Below is a numbered list of facts. Rewrite each one in plain, terse words of your own.

- Keep every name, number, date and quoted phrase exactly as written.
- Change all other wording: reuse no run of three or more words from the original, apart from names, numbers and quotes.
- Same meaning, nothing added, nothing dropped. One rewritten fact per input fact, in the same order.

Return only JSON: {{"facts": ["fact", "fact"]}} with exactly {n} items.

{facts}"""


@dataclass
class Facts:
    topic: str
    facts: list[str]


def parse_facts(raw: str) -> Facts:
    d = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
    return Facts(str(d["topic"]).strip(), [str(f).strip() for f in d["facts"] if str(f).strip()])


def extract(text: str) -> Facts:
    return parse_facts(claude(FACTS.format(text=text), model="sonnet"))


def reword(f: Facts) -> Facts:
    """B5: the same facts with the source's wording replaced, names, numbers and quotes kept."""
    listing = "\n".join(f"{i}. {x}" for i, x in enumerate(f.facts, 1))
    raw = claude(REWORD.format(n=len(f.facts), facts=listing), model="sonnet")
    out = parse_facts('{"topic": "", ' + re.search(r"\{(.*)\}", raw, re.S).group(1) + "}").facts
    if len(out) != len(f.facts):
        raise ValueError(f"reword returned {len(out)} facts for {len(f.facts)}")
    return Facts(f.topic, [x.removesuffix(".") for x in out])  # 97% of training facts end without one


def facts_prompt(f: Facts, words: int, key: str) -> str:
    """The one prompt format, shared by training and inference. Facts are shuffled by a
    seed derived from the document id, so their order carries none of the source's."""
    items = list(f.facts)
    random.Random(key).shuffle(items)
    body = "\n".join(f"- {x}" for x in items)
    return f"Facts:\nTopic: {f.topic}\nLength: about {int(round(words, -1))} words\n{body}\n\nArticle:\n"


def build():
    docs = [json.loads(line) for line in (ROOT / "data" / "human.jsonl").open()]
    valid_ids = {r["id"] for r in map(json.loads, (ROOT / "data" / "lora" / "valid.jsonl").open())}
    texts = [_fits(docs[i]["text"]) for i in TRAIN_IDS]
    raws = claude_many([FACTS.format(text=t) for t in texts], model="sonnet")
    rows, bad, ratio = [], 0, []
    for i, t, raw in zip(TRAIN_IDS, texts, raws):
        try:
            f = parse_facts(raw)
        except Exception:  # noqa: BLE001
            bad += 1
            continue
        hid = f"h{i:04d}"
        rows.append({"id": hid, "prompt": facts_prompt(f, len(t.split()), hid), "completion": t,
                     "n_facts": len(f.facts)})
        ratio.append(len(t.split()) / max(1, len(f.facts)))
    random.Random(0).shuffle(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    valid = [r for r in rows if r["id"] in valid_ids]
    train = [r for r in rows if r["id"] not in valid_ids]
    for name, part in [("valid", valid), ("train", train)]:
        (OUT / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in part))
    meta = {"train": len(train), "valid": len(valid), "unparsed": bad,
            "median_words_per_fact": statistics.median(ratio)}
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1))
    print(meta)


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args()
    build()
