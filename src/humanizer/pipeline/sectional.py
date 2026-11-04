"""Writer v2: a base model writes one section at a time, with a grounding guard.

B2's whole-article base writer read as human but invented names and venues and
ran short of the notes. Two changes, both keep base-model statistics:

- Sectional few-shot. Each human example interleaves a section's notes with that
  section's text, so the model learns "notes, then the paragraph they describe".
  We then generate our article one section at a time from its own notes, which
  gives coverage of every note and length control per section.
- Grounding guard (constrained decoding). Mid-sentence, a token that starts a
  capitalized word, or any token with a digit, is blocked unless it is a prefix
  of a name or number that appears in the draft. Sentence starts stay free.
"""

from __future__ import annotations

import json
import random
import re

from humanizer import ROOT
from humanizer.llm import _cache_get, _cache_put, _key, claude, load_mlx
from humanizer.pipeline.editor import Plan, Section, parse_plan

CONTEXT = 4096
EXAMPLE_IDS = range(850, 900)  # corpus "spare" split, as in writer.py
MAX_EXAMPLE_WORDS = 550
OPEN, CLOSE = "<<notes:", ">>"
SENTENCE_END = (".", "!", "?", ":", "\n", '"', "“", "(")

NOTES_SECTIONED = """Write the editor's notes that this finished article could have been written from. Split the article into its natural sections, in order, covering all of it. For each section give terse fragment notes the way an editor scribbles, its approximate word count, and "start": the first six words of the section copied exactly from the article. Return only JSON:
{{"title": "...", "sections": [{{"heading": null, "start": "first six words exactly", "points": [{{"note": "terse fragment", "quote": ""}}], "target_words": 120}}], "cut": []}}

<article>
{text}
</article>"""


def render_section_notes(s: Section) -> str:
    return f"{OPEN} " + " | ".join(p["note"] for p in s.points) + f" | about {s.target_words} words{CLOSE}"


def split_by_starts(text: str, starts: list[str]) -> list[str] | None:
    """Cut text at each section's verbatim start phrase. None if any is missing or out of order."""
    flat = re.sub(r"\s+", " ", text).strip()
    pos, cuts = 0, []
    for s in starts:
        i = flat.find(re.sub(r"\s+", " ", s).strip(), pos)
        if i < 0:
            return None
        cuts.append(i)
        pos = i + 1
    cuts[0] = 0
    return [flat[a:b].strip() for a, b in zip(cuts, cuts[1:] + [len(flat)])]


def _sectioned_examples(k: int, seed: int) -> list[tuple[Plan, list[str]]]:
    docs = [json.loads(line) for line in (ROOT / "data" / "human.jsonl").open()]
    pool = [docs[i] for i in EXAMPLE_IDS if i < len(docs) and docs[i]["words"] <= MAX_EXAMPLE_WORDS]
    random.Random(seed).shuffle(pool)
    out = []
    for d in pool:
        raw = claude(NOTES_SECTIONED.format(text=d["text"]), model="sonnet")
        try:
            plan = parse_plan(raw)
            starts = [s["start"] for s in json.loads(re.search(r"\{.*\}", raw, re.S).group(0))["sections"]]
        except Exception:  # noqa: BLE001
            continue
        parts = split_by_starts(d["text"], starts)
        if parts and len(parts) == len(plan.sections) and len(parts) >= 2:
            out.append((plan, parts))
        if len(out) == k:
            break
    return out


def _doc(plan: Plan, parts: list[str]) -> str:
    """One document in the few-shot format; parts may be shorter than plan.sections (article so far)."""
    lines = [f"Title: {plan.title}", ""]
    for s, text in zip(plan.sections, parts):
        lines.append(render_section_notes(s))
        if s.heading:
            lines.append(s.heading)
        lines += [text, ""]
    return "\n".join(lines)


def sectional_prompt(plan: Plan, done: list[str], examples: list[tuple[Plan, list[str]]]) -> str:
    shots = "".join(f"=== ARTICLE ===\n{_doc(p, parts)}\n" for p, parts in examples)
    s = plan.sections[len(done)]
    head = f"{s.heading}\n" if s.heading else ""
    return f"{shots}=== ARTICLE ===\n{_doc(plan, done)}{render_section_notes(s)}\n{head}"


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


def common_capitalized(min_count: int = 2) -> set[str]:
    """Ordinary English words, capitalized: words seen lowercase in the human corpus at least min_count times."""
    from collections import Counter

    c = Counter(w for d in map(json.loads, (ROOT / "data" / "human.jsonl").open())
                for w in re.findall(r"\b[a-z][a-z']*\b", d["text"]))
    return {w.capitalize() for w, n in c.items() if n >= min_count}


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

        self.text = [""] * vocab
        for i in range(vocab):
            try:
                self.text[i] = self.tok.decode([i])
            except Exception:  # noqa: BLE001  padded rows past the tokenizer's vocab
                pass
        core = [t.strip() for t in self.text]
        lead = np.array([bool(t) and t[0] in " \n\t" for t in self.text])
        alnum = np.array([bool(c) and c[0].isalnum() for c in core])
        self.cont = ~lead & alnum  # continues the word in progress
        self.ends = np.array([bool(c) and c.endswith(SENTENCE_END) or "\n" in t for c, t in zip(core, self.text)])
        constrained = np.array([bool(c) and (c[0].isupper() or c[0].isdigit()) for c in core])
        quote = np.array([any(q in t for q in QUOTES) for t in self.text])
        self.cont_ids = np.flatnonzero(self.cont)
        self.block = {}
        for mode in ("mid", "sent"):
            ok = np.array([not k or c in self.prefix[mode] for k, c in zip(constrained, core)])
            self.block[mode] = {
                "new_word": alnum & ~ok,          # any alnum token may start a word when no word is in progress
                "after_word": lead & alnum & ~ok,  # after a finished word only a spaced token starts a new one
            }
        self.quote = quote

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

    def __call__(self, tokens, logits):
        import mlx.core as mx
        import numpy as np

        if self.text is None:
            self._build(logits.shape[-1])
        ids = tokens[-24:].tolist() if tokens.size else []
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
        return mx.where(mx.array(block), -mx.inf, logits)


def _stop_at_marker(text: str) -> tuple[str, bool]:
    for m in ("<<", "===", "\n\n\n"):
        i = text.find(m)
        if i != -1:
            return text[:i], True
    return text, False


def write_sectional(plan: Plan, model_id: str, draft: str, *, seed: int = 0, k: int = 2,
                    temp: float = 0.8, top_p: float = 0.95, guard: bool = True) -> str:
    import mlx.core as mx
    from mlx_lm import stream_generate
    from mlx_lm.sample_utils import make_logits_processors, make_sampler

    examples = _sectioned_examples(k, seed)
    allowed = allowed_specifics(draft, plan.render_notes())
    quotes = any(q in draft for q in QUOTES)
    model, tok = load_mlx(model_id)
    g = None
    done: list[str] = []
    for idx, s in enumerate(plan.sections):
        max_new = int(s.target_words * 1.7) + 40
        shots = list(examples)
        prompt = sectional_prompt(plan, done, shots)
        while shots and len(tok.encode(prompt)) + max_new > CONTEXT - 16:
            shots = shots[:-1]  # drop examples before overflowing the 4k context
            prompt = sectional_prompt(plan, done, shots)
        key = _key("sectional-g2", model_id, prompt, max_new, temp, top_p, seed, guard, sorted(allowed), quotes)
        text = _cache_get(key)
        if text is None:
            if guard and g is None:
                g = Guard(tok, allowed, common_capitalized(), allow_quotes=quotes)
            procs = make_logits_processors(repetition_penalty=1.05) + ([g] if guard else [])
            mx.random.seed(seed * 1000 + idx)
            text = ""
            for r in stream_generate(model, tok, prompt, max_tokens=max_new,
                                     sampler=make_sampler(temp=temp, top_p=top_p), logits_processors=procs,
                                     prefill_step_size=512, kv_bits=4, quantized_kv_start=0):
                text += r.text
                text, stop = _stop_at_marker(text)
                if stop:
                    break
            text = text.strip()
            _cache_put(key, text)
        done.append(text)
    out = []
    for s, t in zip(plan.sections, done):
        out += ([f"## {s.heading}"] if s.heading else []) + [t]
    return "\n\n".join(x for x in out if x)
