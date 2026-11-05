"""Training pairs for the fine-tuned writer: (notes, human article).

The prompted base writer reads as human but does not follow notes. A base model
fine-tuned to turn notes into the human article they came from should learn to
follow notes, while every target it sees stays pre-2022 human prose.

Notes must cover the whole article: if a training article says things its notes
do not, the writer learns that inventing is part of the job.

Only the pairs (0-599) and spare (850-899) corpus ranges are used. Dev, H1 and
H2 drafts were written from the topics of documents 600-849, so training on those
would leak.
"""

from __future__ import annotations

import argparse
import json
import random

from humanizer import ROOT
from humanizer.llm import claude_many
from humanizer.pipeline.editor import Plan, parse_plan

OUT = ROOT / "data" / "lora"
TRAIN_IDS = [*range(0, 600), *range(850, 900)]
N_VALID = 30
MAX_WORDS = 1300  # keeps notes plus article under 2,048 tokens

ARTICLE_NOTES = """Here is a finished article. Write the notes a writer could have worked from.

Split it into the article's natural parts. For each part give a short heading (the article's own heading if it has one, otherwise a two-to-five-word label) and list, in order, every point the part makes, as terse fragments the way an editor scribbles. Cover everything: a reader of the notes should be able to tell what every paragraph says. Keep every name, number, date and quoted phrase that appears; drop the wording. Add nothing that is not in the article. Give each part's word count.

Return only JSON:
{{"title": "short title", "sections": [{{"heading": "short heading", "points": [{{"note": "terse fragment", "quote": ""}}], "target_words": 120}}], "cut": []}}

<article>
{text}
</article>"""


def lora_prompt(plan: Plan) -> str:
    """The one prompt format, shared by training and inference."""
    lines = [f"Title: {plan.title}", ""]
    for s in plan.sections:
        lines.append(f"Part: {s.heading or ''} (about {s.target_words} words)")
        lines += [f"- {p['note']}" for p in s.points]
        lines.append("")
    return "Notes:\n" + "\n".join(lines) + "\nArticle:\n"


def _fits(text: str) -> str:
    """Cut long articles at a paragraph break under MAX_WORDS."""
    out, n = [], 0
    for para in text.split("\n"):
        w = len(para.split())
        if n + w > MAX_WORDS and out:
            break
        out.append(para)
        n += w
    return "\n".join(out).strip()


def build(limit: int | None = None):
    docs = [json.loads(line) for line in (ROOT / "data" / "human.jsonl").open()]
    ids = TRAIN_IDS[:limit] if limit else TRAIN_IDS
    texts = [_fits(docs[i]["text"]) for i in ids]
    raws = claude_many([ARTICLE_NOTES.format(text=t) for t in texts], model="sonnet")
    rows, bad = [], 0
    for i, t, raw in zip(ids, texts, raws):
        try:
            plan = parse_plan(raw)
        except Exception:  # noqa: BLE001
            bad += 1
            continue
        rows.append({"id": f"h{i:04d}", "prompt": lora_prompt(plan), "completion": t})
    random.Random(0).shuffle(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, part in [("valid", rows[:N_VALID]), ("train", rows[N_VALID:])]:
        (OUT / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in part))
    print(f"train {len(rows) - N_VALID}, valid {N_VALID}, unparsed {bad}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    build(ap.parse_args().limit)
