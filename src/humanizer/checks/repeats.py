"""Template repeats: sentences that mostly reuse word trigrams already in the piece.

Exact-repeat deletion misses a writer looping on a template ("What words would you use to explain your
X to someone?"), and the claim check passes the loop because questions state no facts (B20, a0612).
"""

import re

WORD = re.compile(r"[a-z0-9']+")
# 0.6 measured 2026-11-05: catches 63 of a0612's 64 loop sentences (each reuses about 2/3 of its
# trigrams, so 0.7 catches none) and flags 0.8% of the 38,089 sentences in data/human.jsonl.
MIN_TRIGRAMS, SHARE = 4, 0.6


def _trigrams(sentence: str) -> set[tuple[str, ...]]:
    w = WORD.findall(sentence.lower())
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


def template_repeats(sentences: list[str], seen: list[str] = (), share: float = SHARE) -> set[int]:
    """Indices of sentences, read in order after `seen`, of which more than `share` of the word
    trigrams already appeared. Sentences under MIN_TRIGRAMS trigrams (about 6 words) are never flagged."""
    used = set().union(*map(_trigrams, seen))
    out = set()
    for i, s in enumerate(sentences):
        t = _trigrams(s)
        if len(t) >= MIN_TRIGRAMS and len(t & used) > share * len(t):
            out.add(i)
        used |= t
    return out
