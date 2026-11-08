"""Degenerate loops: text that starts repeating itself and never stops.

B34 and P2c (results/p2c_bakeoff.json) found base-model continuations collapsing into a repeated phrase until the
token cap. Such text copies almost nothing from its input, so a least-copying pick prefers it unless this check runs
first. Standard library only, so the Windows GPU box can import this file on its own.
"""

from __future__ import annotations

import re

WORD = re.compile(r"[a-z0-9']+")
SENTENCE_END = re.compile(r"[.!?][\"'”)\]]*(?=\s|$)")
LIMIT = 0.25  # share of repeated word 4-grams; P2c's human-like stopped texts average 0.05, its loops 0.79
WINDOW = 30


def _grams(words: list[str], n: int = 4) -> list[tuple[str, ...]]:
    return [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]


def repeat_share(text: str) -> float:
    """Share of word 4-grams that repeat an earlier 4-gram of the same text."""
    g = _grams(WORD.findall(text.lower()))
    return 1 - len(set(g)) / len(g) if g else 0.0


def is_loop(text: str, limit: float = LIMIT) -> bool:
    return repeat_share(text) > limit


def trailing_loop(text: str, window: int = 80, limit: float = 0.5) -> bool:
    """True if the last `window` words are mostly repeats of themselves: stop generating."""
    w = WORD.findall(text.lower())
    return len(w) >= window and repeat_share(" ".join(w[-window:])) > limit


def cut_loop(text: str) -> str:
    """The text up to the last sentence end before a sustained repetition starts; the whole text if there is none."""
    matches = list(WORD.finditer(text.lower()))
    words = [m.group(0) for m in matches]
    seen: set[tuple[str, ...]] = set()
    flags = []
    for g in _grams(words):
        flags.append(g in seen)
        seen.add(g)
    start = next((i for i in range(len(flags)) if flags[i] and sum(flags[i:i + WINDOW]) >= 0.6 * WINDOW), None)
    if start is None:
        return text
    return last_sentence(text[: matches[start].start()])


def last_sentence(text: str) -> str:
    """The text up to and including its last complete sentence ('' if it has none)."""
    ends = list(SENTENCE_END.finditer(text))
    return text[: ends[-1].end()].rstrip() if ends else ""
