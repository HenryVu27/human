"""Claim check: the output may cut and reorder, but must not add anything.

Two parts: a deterministic check that every number, quotation and multi-word
name in the output appears in the draft, and a model judge that every claim
in the output is entailed by the draft.
"""

from __future__ import annotations

import json
import re

from humanizer.llm import claude

CODE = re.compile(r"```.*?```|`[^`\n]+`", re.S)
HEADING = re.compile(r"^\s{0,3}#{1,6}\s.*$", re.M)  # headings come from the editor's plan and are Title Case
NUMBER = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?%?")
QUOTE = re.compile(r"[\"“]([^\"”\n]{3,160})[\"”]")
NAME = re.compile(r"\b[A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)+\b|\b[A-Z]{2,}[a-z]?\b")
STOP_STARTS = {"The", "This", "That", "These", "Those", "In", "On", "At", "For", "And", "But", "When", "If",
               "It", "A", "An", "As", "So", "Yet", "Or", "We", "You", "They", "He", "She", "I"}

ENTAIL = """Below are a SOURCE draft and an EDITED version. List every factual claim the EDITED version makes, and for each say whether the SOURCE supports it (true) or not (false). Opinions and framing that the SOURCE also expresses count as supported. Return only JSON: [{{"claim": "...", "supported": true}}, ...]

<source>
{draft}
</source>

<edited>
{output}
</edited>"""


def _clean_name(n: str) -> str:
    words = n.split()
    while words and words[0] in STOP_STARTS:
        words = words[1:]
    return " ".join(words)


def specifics(text: str) -> set[str]:
    text = HEADING.sub("\n", CODE.sub(" ", text))
    found = {m.group(0).replace(",", "") for m in NUMBER.finditer(text)}
    found |= {m.group(1).strip() for m in QUOTE.finditer(text)}
    for m in NAME.finditer(text):
        name = _clean_name(m.group(0))
        if len(name.split()) >= 2 or (name.isupper() and len(name) >= 2):
            found.add(name)
    return found


def unsupported_specifics(draft: str, output: str) -> set[str]:
    hay = CODE.sub(" ", draft).replace(",", "").lower()
    bad = set()
    for s in specifics(output):
        if s.replace(",", "").lower() not in hay:
            bad.add(s if not NUMBER.fullmatch(s) else _restore(s, output))
    return bad


def _restore(num: str, text: str) -> str:
    """Report a number the way the output wrote it (with its commas)."""
    for m in NUMBER.finditer(text):
        if m.group(0).replace(",", "") == num:
            return m.group(0)
    return num


def claim_check(draft: str, output: str, *, model: str = "sonnet") -> dict:
    bad = unsupported_specifics(draft, output)
    raw = claude(ENTAIL.format(draft=draft, output=output), model=model)
    m = re.search(r"\[.*\]", raw, re.S)
    items = json.loads(m.group(0)) if m else []
    total = len(items)
    ok = sum(1 for i in items if i.get("supported"))
    share = ok / total if total else 1.0
    return {"unsupported_specifics": sorted(bad), "claims_total": total, "claims_entailed": ok,
            "unsupported_claims": [i["claim"] for i in items if not i.get("supported")],
            "pass": not bad and share >= 0.95}
