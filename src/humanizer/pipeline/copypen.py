"""Copy penalty for decoding (A2-N): a soft, length-normalized penalty on tokens that would extend a verbatim run
copied from the input section.

Token level. The input's token n-grams (n = `span`, about 6 words at 8 tokens) are indexed by their first n - 1
tokens. At each step, if the last n - 1 generated tokens match such a prefix, every token that would complete a copied
n-gram gets `strength` subtracted from its logit. Runs that are names or numbers (the completing token starts with a
capital or a digit) are exempt, since copying them is what faithfulness requires; so are the input's own quotes
(any token inside a quotation in the input is exempt). Needs only numpy, like guard.py.

`strength` 0 is off; A2-N's medium and strong cells use 2.0 and 6.0 (fixed in experiments/a2n_copy.py).
"""

from __future__ import annotations

from collections import defaultdict

QUOTE_CHARS = ('"', "“", "”")


class CopyPenalty:
    def __init__(self, tok, source: str, strength: float, span: int = 8):
        self.strength, self.span = strength, span
        ids = tok(source, add_special_tokens=False)["input_ids"]
        texts = [tok.decode([i]) for i in ids]
        inside, quoted = False, []
        for t in texts:
            quoted.append(inside)
            if any(q in t for q in QUOTE_CHARS):
                inside = not inside
        self.next: dict[tuple, set[int]] = defaultdict(set)
        for i in range(len(ids) - span + 1):
            last = ids[i + span - 1]
            core = texts[i + span - 1].strip()
            if quoted[i + span - 1] or (core[:1].isupper() or core[:1].isdigit()):
                continue
            self.next[tuple(ids[i:i + span - 1])].add(last)

    def penalized(self, generated: list[int]) -> set[int]:
        """Token ids that would complete a copied run after `generated`."""
        if self.strength <= 0 or len(generated) < self.span - 1:
            return set()
        return self.next.get(tuple(generated[-(self.span - 1):]), set())


class TorchCopyPenalty:
    """transformers logits processor: one CopyPenalty per batch row; `prompt_len` tokens of each row are the prompt."""

    def __init__(self, penalties: list[CopyPenalty], prompt_len: int):
        self.penalties, self.prompt_len = penalties, prompt_len

    def __call__(self, input_ids, scores):
        for row, (pen, ids) in enumerate(zip(self.penalties, input_ids)):
            hit = pen.penalized(ids[self.prompt_len:].tolist())
            if hit:
                idx = list(hit)
                scores[row, idx] = scores[row, idx] - pen.strength
        return scores
