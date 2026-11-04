"""Pairwise quality judge, run in both orders to cancel position bias."""

from __future__ import annotations

from humanizer.llm import claude

JUDGE = """Two versions of the same piece follow. Which one would a busy, expert reader rather read? Judge clarity, substance, and whether every paragraph earns its place. Ignore length on its own. Answer with exactly one letter: A or B.

<A>
{a}
</A>

<B>
{b}
</B>"""


def _pick(raw: str) -> str:
    s = raw.strip().upper()
    return "A" if s.startswith("A") else "B" if s.startswith("B") else "?"


def quality_pair(draft: str, output: str, *, model: str = "sonnet") -> float:
    """1.0 if the output wins both orders, 0.5 for a split, 0.0 for a loss."""
    first = _pick(claude(JUDGE.format(a=draft, b=output), model=model))   # output is B
    second = _pick(claude(JUDGE.format(a=output, b=draft), model=model))  # output is A
    return ((first == "B") + (second == "A")) / 2
