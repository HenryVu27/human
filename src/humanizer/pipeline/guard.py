"""Grounding guard: constrained decoding that keeps names, numbers and quotes to the draft's own.

Mid-sentence, a token that starts a capitalized word, or any token with a digit, is blocked unless
it is a prefix of a name or number that appears in the draft. Sentence starts may also use ordinary
English words. Needs only numpy, so the Windows GPU box can import this file on its own; Guard is
the mlx_lm processor and TorchGuard the transformers one.
"""

from __future__ import annotations

import re

SENTENCE_END = (".", "!", "?", ":", "\n", '"', "\u201c", "(")
_VOCAB: dict = {}
WORD = re.compile(r"[A-Za-z][\w']*|\d[\d,.]*")
QUOTES = ('"', "\u201c", "\u201d")


def allowed_specifics(*texts: str) -> set[str]:
    """Capitalized words and numbers the draft or notes already contain, plus 'I'."""
    out = {"I"}
    for t in texts:
        for w in WORD.findall(t):
            if w[0].isupper() or w[0].isdigit():
                out.add(w.rstrip(".,"))
    return out


def _prefixes(words) -> set[str]:
    return {w[:i] for w in words for i in range(1, len(w) + 1)}


class Guard:
    """mlx_lm logits processor that keeps names and numbers to the draft's own.

    Word level: a capitalized word or a number may only grow into, and end as, a
    word the draft contains. At a sentence start, ordinary English words
    (common_capitalized) are also allowed. Quote marks are blocked when the
    draft has none. Lowercase words are never touched.
    """

    def __init__(self, tok, allowed: set[str], common: set[str] = frozenset(), allow_quotes: bool = True):
        self.tok, self.allow_quotes = tok, allow_quotes
        self.complete = {"mid": set(allowed), "sent": set(allowed) | set(common)}
        self.prefix = {k: _prefixes(v) for k, v in self.complete.items()}
        self.text = None

    def _build(self, vocab: int):
        import numpy as np

        key = (id(self.tok), vocab)
        if key not in _VOCAB:  # decoding the whole vocabulary is the slow part; do it once per tokenizer
            text = [""] * vocab
            for i in range(vocab):
                try:
                    text[i] = self.tok.decode([i])
                except Exception:  # noqa: BLE001  padded rows past the tokenizer's vocab
                    pass
            core = [t.strip() for t in text]
            _VOCAB[key] = {
                "text": text, "core": core,
                "lead": np.array([bool(t) and t[0] in " \n\t" for t in text]),
                "alnum": np.array([bool(c) and c[0].isalnum() for c in core]),
                "ends": np.array([bool(c) and c.endswith(SENTENCE_END) or "\n" in t for c, t in zip(core, text)]),
                "constrained": np.array([bool(c) and (c[0].isupper() or c[0].isdigit()) for c in core]),
                "quote": np.array([any(q in t for q in QUOTES) for t in text]),
            }
        v = _VOCAB[key]
        self.text, core, lead, alnum = v["text"], v["core"], v["lead"], v["alnum"]
        self.cont = ~lead & alnum  # continues the word in progress
        self.ends = v["ends"]
        self.cont_ids = np.flatnonzero(self.cont)
        self.block = {}
        for mode in ("mid", "sent"):
            ok = np.array([not k or c in self.prefix[mode] for k, c in zip(v["constrained"], core)])
            self.block[mode] = {
                "new_word": alnum & ~ok,          # any alnum token may start a word when no word is in progress
                "after_word": lead & alnum & ~ok,  # after a finished word only a spaced token starts a new one
            }
        self.quote = v["quote"]

    def _state(self, ids: list[int]):
        """(current word, mode) for the word in progress at the end of ids, or (None, mode for the next word)."""
        i = len(ids) - 1
        while i > 0 and self.cont[ids[i]] and not self._is_start(ids, i):
            i -= 1
        if i < 0 or not self.text[ids[i]].strip()[:1].isalnum():
            return None, "sent" if (ids and self.ends[ids[-1]]) else "mid"
        word = "".join(self.text[t] for t in ids[i:]).strip()
        mode = "sent" if i == 0 or self.ends[ids[i - 1]] else "mid"
        return word, mode

    def _is_start(self, ids, i):
        prev = self.text[ids[i - 1]]
        return not prev.strip() or not prev.strip()[-1].isalnum()

    def mask(self, ids: list[int], vocab: int):
        """Boolean array over the vocabulary: True where the next token is blocked."""
        import numpy as np

        if self.text is None:
            self._build(vocab)
        ids = ids[-24:]
        word, mode = self._state(ids)
        if word is None:
            block = self.block[mode]["new_word"].copy()
        elif not (word[0].isupper() or word[0].isdigit()):
            block = self.block["mid"]["after_word"].copy()
        else:
            block = np.ones_like(self.cont)
            pre = self.prefix[mode]
            for t in self.cont_ids:
                if word + self.text[t].strip() in pre:
                    block[t] = False
            if word in self.complete[mode]:
                block[~self.cont] = self.block["mid"]["after_word"][~self.cont]
        if not self.allow_quotes:
            block |= self.quote
        if block.all():  # never leave the sampler with nothing
            block = np.zeros_like(block)
        return block

    def __call__(self, tokens, logits):
        import mlx.core as mx

        block = self.mask(tokens[-24:].tolist() if tokens.size else [], logits.shape[-1])
        return mx.where(mx.array(block), -mx.inf, logits)


class TorchGuard:
    """The same Guard as a transformers logits processor, one Guard state per batch row (gpu/serve13b.py)."""

    def __init__(self, guard: Guard):
        self.guard = guard

    def __call__(self, input_ids, scores):
        import numpy as np
        import torch

        rows = [self.guard.mask(r[-24:].tolist(), scores.shape[-1]) for r in input_ids]
        block = torch.as_tensor(np.stack(rows), device=scores.device)
        return scores.masked_fill(block, float("-inf"))
