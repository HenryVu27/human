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


WORD = re.compile(r"[A-Za-z][\w'\-]*|\d[\d,.]*")


def allowed_specifics(*texts: str) -> set[str]:
    """Capitalized words and numbers the draft or notes already contain, plus 'I'."""
    out = {"I"}
    for t in texts:
        for w in WORD.findall(t):
            if w[0].isupper() or w[0].isdigit():
                out.add(w.rstrip(".,"))
    return out


class Guard:
    """mlx_lm logits processor: block new names and numbers mid-sentence. Masks are built on first call."""

    def __init__(self, tok, allowed: set[str]):
        self.tok, self.allowed = tok, list(allowed)
        self.block_mid = self.block_any = self.ends = None

    def _build(self, vocab: int):
        import mlx.core as mx
        import numpy as np

        caps, digits, ends, ok = (np.zeros(vocab, bool) for _ in range(4))
        for i in range(vocab):
            try:
                t = self.tok.decode([i])
            except Exception:  # noqa: BLE001  padded rows past the tokenizer's vocab
                continue
            core = t.strip()
            if not core:
                ends[i] = "\n" in t
                continue
            ends[i] = core.endswith(SENTENCE_END) or "\n" in t
            digits[i] = any(c.isdigit() for c in core)
            caps[i] = t[0] in " \n" and core[0].isupper()
            if digits[i] or caps[i]:
                ok[i] = any(a.startswith(core) or (digits[i] and core.strip(".,") in a) for a in self.allowed)
        self.block_mid = mx.array((caps | digits) & ~ok)
        self.block_any = mx.array(digits & ~ok)
        self.ends = ends

    def __call__(self, tokens, logits):
        import mlx.core as mx

        if self.ends is None:
            self._build(logits.shape[-1])
        last = int(tokens[-1]) if tokens.size else 0
        mask = self.block_any if self.ends[last] else self.block_mid
        return mx.where(mask, -mx.inf, logits)


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
        key = _key("sectional", model_id, prompt, max_new, temp, top_p, seed, guard, sorted(allowed))
        text = _cache_get(key)
        if text is None:
            if guard and g is None:
                g = Guard(tok, allowed)
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
