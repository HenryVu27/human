"""Synthetic mirrors (Pangram's recipe) and the frozen test-draft splits.

A mirror is an AI text written from only the topic of a human text, so the
detector learns how a text was written rather than what it is about.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from humanizer import ROOT
from humanizer.llm import claude_many, local_generate

DATA = ROOT / "data"
QWEN_4B = "mlx-community/Qwen3.5-4B-MLX-4bit"
MIRROR_GENERATORS = ["claude:haiku", "claude:sonnet", f"mlx:{QWEN_4B}"]
DRAFT_GENERATORS = ["claude:sonnet", "claude:opus"]

TOPIC = """Read the document below and describe it so someone could write a new piece on the same subject without seeing it.
Return only JSON: {{"title": short title, "topic": one sentence on the subject and angle, "genre": e.g. explainer, news feature, how-to, opinion essay, product guide}}.

<document>
{text}
</document>"""


def split_of(i: int) -> str:
    """Frozen splits by corpus index. Never change these ranges."""
    if i < 600:
        return "pairs"
    if i < 700:
        return "dev"
    if i < 800:
        return "h1"
    if i < 850:
        return "h2"
    return "spare"


def topic_prompt(doc: dict) -> str:
    return TOPIC.format(text=doc["text"][:6000])


def parse_topic(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.S)
    return json.loads(m.group(0))


def mirror_prompt(t: dict, words: int) -> str:
    return (f"Write a {t['genre']} titled \"{t['title']}\" about {t['topic']} "
            f"It should be about {words} words. Output only the piece itself.")


def draft_prompt(t: dict) -> str:
    return (f"Write a blog post about {t['topic']} Working title: \"{t['title']}\". "
            "Aim for 700 to 1,000 words. Output only the post, in markdown.")


def ngram_overlap(src: str, gen: str, n: int = 12) -> bool:
    def grams(s):
        w = s.lower().split()
        return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}
    return bool(grams(src) & grams(gen))


def _generate(gen: str, prompts: list[str], max_tokens: int) -> list[str | None]:
    kind, model = gen.split(":", 1)
    if kind == "claude":
        return claude_many(prompts, model=model, workers=4)
    return [local_generate(model, p, max_tokens=max_tokens, temp=0.7, chat=True) for p in prompts]


def build(human: Path = DATA / "human.jsonl", only: str | None = None) -> None:
    docs = [json.loads(line) for line in human.open()]
    topics_path = DATA / "topics.jsonl"
    if topics_path.exists():
        topics = {r["id"]: r for r in map(json.loads, topics_path.open())}
    else:
        raws = claude_many([topic_prompt(d) for d in docs], model="haiku")
        topics = {}
        with topics_path.open("w") as f:
            for d, raw in zip(docs, raws):
                try:
                    t = parse_topic(raw) | {"id": d["id"]}
                except Exception:  # noqa: BLE001
                    continue
                topics[d["id"]] = t
                f.write(json.dumps(t) + "\n")
    print("topics", len(topics))

    jobs: dict[str, list[tuple[int, dict, str]]] = {}
    for i, d in enumerate(docs):
        t = topics.get(d["id"])
        s = split_of(i)
        if t is None or s == "spare":
            continue
        if s == "pairs":
            gen = MIRROR_GENERATORS[i % len(MIRROR_GENERATORS)]
            words = max(400, min(1200, round(d["words"] / 10) * 10))
            jobs.setdefault(gen, []).append((i, d, mirror_prompt(t, words)))
        else:
            gen = DRAFT_GENERATORS[i % len(DRAFT_GENERATORS)]
            jobs.setdefault(gen, []).append((i, d, draft_prompt(t)))

    rows: dict[str, list[dict]] = {}
    for gen, items in jobs.items():
        if only and not gen.startswith(only):
            continue
        outs = _generate(gen, [p for _, _, p in items], max_tokens=1800)
        for (i, d, _), text in zip(items, outs):
            if not text or ngram_overlap(d["text"], text):
                continue
            rows.setdefault(split_of(i), []).append(
                {"id": f"a{i:04d}", "source_id": d["id"], "generator": gen, "text": text.strip()})
        print(gen, len(items))

    # Merge with rows already on disk so per-generator runs accumulate.
    (DATA / "drafts").mkdir(exist_ok=True)
    for split, new in rows.items():
        path = DATA / "ai.jsonl" if split == "pairs" else DATA / "drafts" / f"{split}.jsonl"
        old = {r["id"]: r for r in map(json.loads, path.open())} if path.exists() else {}
        old |= {r["id"]: r for r in new}
        path.write_text("".join(json.dumps(r) + "\n" for r in sorted(old.values(), key=lambda r: r["id"])))
        print(split, len(old))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="run one generator prefix, e.g. claude:haiku or mlx")
    build(only=ap.parse_args().only)
