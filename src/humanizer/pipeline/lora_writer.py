"""Fine-tuned writer: OLMo-2 base with a LoRA adapter trained on (notes, human article) pairs.

Training notes cover every point of their article (data/lora.py), so the writer
learns that whatever it writes is in the notes. Inference has to match: the
editor's terse plan carries about a third of the notes per output word that
training notes do, and a writer given thin notes pads or invents. So the draft
gets the same dense notes as training, and the editor's judgment is applied as
selection: Claude picks which numbered notes to keep, in what order, and never
rewords them.
"""

from __future__ import annotations

import json
import re

from humanizer.data.lora import ARTICLE_NOTES, lora_prompt
from humanizer.llm import _cache_get, _cache_put, _key, claude, load_mlx
from humanizer.pipeline.editor import Plan, Section, parse_plan

SELECT = """You are a senior editor at a publication known for writing that respects readers' time. Below are numbered notes covering everything a draft says, and another editor's plan for cutting it.

Choose the notes the final piece keeps, following the plan: keep what a busy expert reader would want, cut coverage that exists for completeness, generic advice, hedging, throat-clearing and any ending that recaps. You may reorder. You may not change or add notes.

Return only JSON: {{"keep": [note numbers, in the order the final piece should present them]}}

<plan>
{plan}
</plan>

<notes>
{notes}
</notes>"""


def dense_plan(draft: str) -> Plan:
    return parse_plan(claude(ARTICLE_NOTES.format(text=draft), model="sonnet"))


def numbered_notes(plan: Plan) -> tuple[str, list[tuple[int, dict]]]:
    flat, lines = [], []
    for si, s in enumerate(plan.sections):
        lines.append(f"Part: {s.heading or ''}")
        for p in s.points:
            flat.append((si, p))
            lines.append(f"[{len(flat)}] {p['note']}")
    return "\n".join(lines), flat


def apply_selection(plan: Plan, flat: list[tuple[int, dict]], keep: list[int]) -> Plan:
    """Kept notes, in the chosen order; a new part starts whenever the source section changes.
    Each part's word target is its source section's target times the share of notes kept."""
    parts: list[tuple[int, list[dict]]] = []
    seen = set()
    for k in keep:
        if not 1 <= k <= len(flat) or k in seen:
            continue
        seen.add(k)
        si, p = flat[k - 1]
        if parts and parts[-1][0] == si:
            parts[-1][1].append(p)
        else:
            parts.append((si, [p]))
    secs = []
    for si, pts in parts:
        src = plan.sections[si]
        secs.append(Section(src.heading, pts, max(30, int(round(src.target_words * len(pts) / max(1, len(src.points)), -1)))))
    return Plan(plan.title, secs)


def select(plan: Plan, editor_plan: Plan) -> Plan:
    listing, flat = numbered_notes(plan)
    raw = claude(SELECT.format(plan=editor_plan.to_json(), notes=listing), model="opus")
    try:
        keep = [int(i) for i in json.loads(re.search(r"\{.*\}", raw, re.S).group(0))["keep"]]
    except Exception:  # noqa: BLE001
        keep = list(range(1, len(flat) + 1))
    out = apply_selection(plan, flat, keep)
    return out if out.sections else plan


def write_lora(editor_plan: Plan, model_id: str, adapter: str, draft: str, *, seed: int = 0,
               temp: float = 0.8, top_p: float = 0.95, guard: bool = True) -> str:
    import mlx.core as mx
    from mlx_lm import stream_generate
    from mlx_lm.sample_utils import make_logits_processors, make_sampler

    from humanizer.pipeline.sectional import QUOTES, Guard, allowed_specifics, common_capitalized

    plan = select(dense_plan(draft), editor_plan)
    prompt = lora_prompt(plan)
    allowed = allowed_specifics(draft, prompt)
    quotes = any(q in draft for q in QUOTES)
    max_new = int(plan.target_words * 1.3 * 1.5) + 64
    key = _key("lora-v1", model_id, adapter, prompt, max_new, temp, top_p, seed, guard, sorted(allowed), quotes)
    if (hit := _cache_get(key)) is not None:
        return hit
    model, tok = load_mlx(model_id, adapter)
    procs = make_logits_processors(repetition_penalty=1.05)
    if guard:
        procs.append(Guard(tok, allowed, common_capitalized(), allow_quotes=quotes))
    mx.random.seed(seed)
    text = "".join(r.text for r in stream_generate(model, tok, prompt, max_tokens=max_new,
                                                   sampler=make_sampler(temp=temp, top_p=top_p),
                                                   logits_processors=procs, prefill_step_size=512))
    text = text.split("Notes:\n")[0].strip()  # in case it runs on into another document
    _cache_put(key, text)
    return text
