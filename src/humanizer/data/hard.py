"""Hard AI negatives for the detector, built from the pairs split only.

detector-v1 learned the mirror format (whole AI documents written from a topic)
and scored instruct continuations of human openings as human. These kinds are
closer to what a humanizer produces:
  continuation  AI continues the first 120 words of a human text (continuation only kept)
  rewrite       AI rewrites a human text in its own words
  styled        AI writes on the topic while told to sound human and avoid AI tells
"""

from __future__ import annotations

import json
import re

from humanizer import ROOT
from humanizer.data.mirror import ngram_overlap
from humanizer.llm import claude_many

DATA = ROOT / "data"
OPEN_WORDS = 120

CONTINUE = """Continue the following text for about {words} more words, in the same voice. Output only the continuation.

{opening}"""

REWRITE = """Rewrite this article in your own words, keeping its content and roughly its length. Output only the article.

{text}"""

STYLED = """Write a {genre} titled "{title}" about {topic} About {words} words.
Make it read like a real person wrote it, not an AI: vary sentence length, skip tidy summaries and signposting, no "it's not X, it's Y", no lists of three, be specific and a little uneven. Output only the piece."""

# (kind, generator, corpus index range) - disjoint ranges so each source feeds one kind.
PLAN = [
    ("continuation", "haiku", range(0, 80)),
    ("continuation", "sonnet", range(80, 160)),
    ("rewrite", "sonnet", range(160, 260)),
    ("styled", "haiku", range(260, 320)),
    ("styled", "sonnet", range(320, 380)),
]


def prompt_for(kind: str, doc: dict, topic: dict | None) -> str:
    words = doc["text"].split()
    if kind == "continuation":
        return CONTINUE.format(words=min(600, max(250, len(words) - OPEN_WORDS)), opening=" ".join(words[:OPEN_WORDS]))
    if kind == "rewrite":
        return REWRITE.format(text=doc["text"])
    return STYLED.format(genre=topic["genre"], title=topic["title"], topic=topic["topic"], words=round(len(words), -1))


def build() -> None:
    docs = [json.loads(line) for line in (DATA / "human.jsonl").open()]
    topics = {r["id"]: r for r in map(json.loads, (DATA / "topics.jsonl").open())}
    rows = []
    for kind, model, idx in PLAN:
        items = [docs[i] for i in idx if kind != "styled" or docs[i]["id"] in topics]
        outs = claude_many([prompt_for(kind, d, topics.get(d["id"])) for d in items], model=model)
        kept = 0
        for d, text in zip(items, outs):
            if not text or len(text.split()) < 100 or ngram_overlap(d["text"], text):
                continue
            text = re.sub(r"^\s*(\.\.\.|…)\s*", "", text)  # a leading ellipsis would be a free label
            rows.append({"id": f"{kind[0]}{d['id'][1:]}", "source_id": d["id"], "generator": f"claude:{model}",
                         "kind": kind, "text": text.strip()})
            kept += 1
        print(kind, model, f"{kept}/{len(items)}", flush=True)
    (DATA / "ai_hard.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    print("ai_hard", len(rows))


if __name__ == "__main__":
    build()
