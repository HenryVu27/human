"""Deletion-only edit: cut whole sentences, never reword.

The base-model writer reads as human but rambles and makes small claims the
draft does not support. A human editor's cheapest fix is the cut. Every
sentence that survives is still the writer's own text, so the edit cannot add
an assistant register. Claude only picks sentence numbers to delete.
"""

from __future__ import annotations

import json
import re

from humanizer.llm import claude

MAX_CUT = 0.4  # never delete more than this share of the words

PRUNE = """You are editing a piece by cutting only. You may delete whole sentences; you may not change, add or move any words.

Delete a sentence if:
- it states a fact, name, number, quote or claim that the source draft does not support, or
- it repeats an earlier point, restates the obvious, or is filler a busy expert reader would skip.
Keep the piece readable: do not cut a sentence that a later kept sentence depends on. Cut as little as these rules allow.

Return only JSON: {{"delete": [sentence numbers]}}

<source_draft>
{draft}
</source_draft>

<piece>
{numbered}
</piece>"""

SENT = re.compile(r"(?<=[.!?])[\"”)]?\s+(?=[A-Z\"“(])")


def split_sentences(text: str) -> list[list[str]]:
    """Paragraphs as lists of sentences. Headings stay one 'sentence' each."""
    return [SENT.split(p.strip()) if not p.lstrip().startswith("#") else [p.strip()]
            for p in re.split(r"\n\s*\n", text) if p.strip()]


def numbered(paras: list[list[str]]) -> tuple[str, list[str]]:
    flat, lines = [], []
    for p in paras:
        for s in p:
            flat.append(s)
            lines.append(f"[{len(flat)}] {s}")
        lines.append("")
    return "\n".join(lines).strip(), flat


def apply_deletions(paras: list[list[str]], delete: set[int]) -> str:
    out, n = [], 0
    for p in paras:
        if p[0].lstrip().startswith("#"):
            n += 1
            out.append(p[0])  # headings are never cut directly
            continue
        kept = []
        for s in p:
            n += 1
            if n not in delete:
                kept.append(s)
        if kept:
            out.append(" ".join(kept))
    # a heading whose whole section was cut goes too
    out = [x for i, x in enumerate(out) if not (x.startswith("#") and (i + 1 == len(out) or out[i + 1].startswith("#")))]
    return "\n\n".join(out)


def prune(draft: str, text: str, *, model: str = "sonnet") -> str:
    paras = split_sentences(text)
    listing, flat = numbered(paras)
    raw = claude(PRUNE.format(draft=draft, numbered=listing), model=model)
    try:
        delete = {int(i) for i in json.loads(re.search(r"\{.*\}", raw, re.S).group(0))["delete"]}
    except Exception:  # noqa: BLE001
        return text
    total = sum(len(s.split()) for s in flat)
    cut, chosen = 0, set()
    for i in sorted(delete):  # cap the cut, earliest first
        if 1 <= i <= len(flat) and cut + len(flat[i - 1].split()) <= MAX_CUT * total:
            chosen.add(i)
            cut += len(flat[i - 1].split())
    return apply_deletions(paras, chosen)
