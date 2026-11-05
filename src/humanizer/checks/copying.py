"""Verbatim copying: the share of a text's words that sit inside a run of N words found in a source.

Found 2026-11-05 before B24's scan: texts written from extracted facts copy long runs of the source's
wording (B5 cell D 8 to 57% of words in shared 8-word runs, B9 S2 5 to 62%, B24 8 to 27%), mostly
because the facts keep that wording. `beyond` excludes runs present in the prompt, which leaves
what the writer reproduced on its own (memorized pretraining text, or Guard steering).
"""

import re

WORD = re.compile(r"[a-z0-9']+")
N = 8


def grams(text: str, n: int = N) -> set[tuple[str, ...]]:
    w = WORD.findall(text.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def copied_share(text: str, source: str, beyond: str = "", n: int = N) -> float:
    keep = grams(source, n) - (grams(beyond, n) if beyond else set())
    w = WORD.findall(text.lower())
    cov = [False] * len(w)
    for i in range(len(w) - n + 1):
        if tuple(w[i:i + n]) in keep:
            cov[i:i + n] = [True] * n
    return sum(cov) / max(1, len(w))
