"""Writers turn an editor's Plan into prose.

base (B2): a base model continues a document of (notes -> human article) pairs,
so it maps notes to prose by imitating pre-2022 human writing, not by following
instructions. claude: an instruct control arm that writes from the same notes.
"""

from __future__ import annotations

import json
import random
import re

from humanizer import ROOT
from humanizer.llm import claude, local_generate
from humanizer.pipeline.editor import Plan, notes_for_article

BREAK = "=== NOTES ==="
ARTICLE = "=== ARTICLE ==="
EXAMPLE_IDS = range(850, 900)  # the corpus "spare" split, never used for detector pairs or drafts
MAX_EXAMPLE_WORDS = 550  # OLMo-2 has a 4,096-token context; two examples must leave room to write
CONTEXT = 4096

CLAUDE_WRITE = """Write the article these editor's notes describe. Use only what the notes contain; add no facts, names, numbers or quotes. Output only the article.

{notes}"""


def truncate_at_document_break(text: str) -> str:
    """Base models run on into a new document; keep only the first."""
    cut = len(text)
    for marker in (BREAK, ARTICLE, "<|endoftext|>", "\n# ", "\n\n\n\n"):
        i = text.find(marker)
        if i != -1:
            cut = min(cut, i)
    return text[:cut].strip()


def _examples(k: int, seed: int) -> list[tuple[Plan, str]]:
    docs = [json.loads(line) for line in (ROOT / "data" / "human.jsonl").open()]
    pool = [docs[i] for i in EXAMPLE_IDS if i < len(docs) and docs[i]["words"] <= MAX_EXAMPLE_WORDS]
    picks = random.Random(seed).sample(pool, k)
    return [(notes_for_article(d["text"]), d["text"].strip()) for d in picks]


def base_prompt(plan: Plan, *, k: int = 2, seed: int = 0) -> str:
    parts = []
    for notes, text in _examples(k, seed):
        parts.append(f"{BREAK}\n{notes.render_notes()}\n{ARTICLE}\n{notes.title}\n\n{text}\n")
    parts.append(f"{BREAK}\n{plan.render_notes()}\n{ARTICLE}\n{plan.title}\n\n")
    return "\n".join(parts)


def write(plan: Plan, writer: str, *, seed: int = 0, draft: str = "") -> str:
    """writer is claude:<model>, mlx:<base model> (whole article), sec:<base model> (sectional + guard)
    or lora:<base model>+<adapter dir> (fine-tuned writer from dense notes)."""
    kind, model = writer.split(":", 1)
    if kind == "claude":
        return claude(CLAUDE_WRITE.format(notes=plan.render_notes()), model=model).strip()
    if kind == "lora":
        from humanizer.pipeline.lora_writer import write_lora
        base, adapter = model.split("+", 1)
        return write_lora(plan, base, adapter, draft, seed=seed)
    if kind == "sec":
        from humanizer.pipeline.sectional import write_sectional
        return write_sectional(plan, model, draft, seed=seed)
    from humanizer.llm import load_mlx

    prompt = base_prompt(plan, seed=seed)
    room = CONTEXT - len(load_mlx(model)[1].encode(prompt)) - 16
    raw = local_generate(model, prompt, max_tokens=max(256, min(int(plan.target_words * 1.8) + 64, room)),
                         temp=0.8, top_p=0.95, seed=seed, kv_bits=4)
    text = truncate_at_document_break(raw)
    return re.sub(rf"^{re.escape(plan.title)}\s*\n", "", text).strip()
