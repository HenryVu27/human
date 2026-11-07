"""Prose defect check: sentences a reader would stop at (cut off, garbled, ungrammatical, word salad, a proof or
derivation that no longer follows). The claim check and form checks pass these; B38's bandits rewrite read Human
with broken sentences and a garbled proof.

`prose_defects(text)` returns the defective sentences quoted from the text. A floor, never a score to maximize.
"""

from __future__ import annotations

import json
import re

from humanizer.llm import claude

PROMPT = """Read the text below as a copy editor. List every sentence a careful reader would stop at because it is broken: cut off mid-thought, garbled, ungrammatical beyond a style choice, word salad, a repeated or looping phrase, or a step of reasoning that no longer follows. Do not list sentences that are merely informal, terse, opinionated or stylistically unusual. Quote each one exactly as it appears. Return only JSON: {{"defects": ["...", ...]}}

<text>
{text}
</text>"""

MODEL = "claude-sonnet-5-5"


def prose_defects(text: str, *, model: str = MODEL) -> list[str]:
    raw = claude(PROMPT.format(text=text), model=model)
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        items = json.loads(m.group(0)).get("defects", []) if m else []
    except json.JSONDecodeError:
        items = []
    return [i for i in items if isinstance(i, str) and i.strip()]
