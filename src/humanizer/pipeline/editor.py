"""Editor: read an AI draft as a pile of claims and plan a human edit. Notes only, never prose."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field

from humanizer.llm import claude

EDIT = """You are a senior editor at a publication known for writing that respects readers' time. A writer handed you the draft below. Plan the edit; someone else will write the final prose from your notes.

Decide like a demanding human editor:
- Keep only what a busy expert reader would want. Cut coverage that exists for completeness, generic advice, both-sides hedging, throat-clearing intros, and any ending that recaps.
- Prefer depth on the strongest one or two points over a tour of five. If the draft lists many items with equal weight, keep the ones that matter and drop or merge the rest.
- Order by what serves the reader, not by the draft's outline. End where the argument ends.
- Do not add anything. Every point must be supported by a verbatim quote from the draft.
- Write notes as terse fragments, the way an editor scribbles, not as finished sentences.

Return only JSON:
{{"title": "...", "sections": [{{"heading": null or "short heading", "points": [{{"note": "terse fragment", "quote": "verbatim supporting quote from the draft"}}], "target_words": 120}}], "cut": ["what you cut and why, one line each"]}}

Total target_words across sections: about {target} words.

<draft>
{draft}
</draft>"""

NOTES_FROM_ARTICLE = """Write the editor's notes that this finished article could have been written from: a title, sections (heading null if the article has none), and for each section terse fragment notes, the way an editor scribbles, plus the section's approximate word count. Return only JSON:
{{"title": "...", "sections": [{{"heading": null, "points": [{{"note": "terse fragment", "quote": ""}}], "target_words": 120}}], "cut": []}}

<article>
{text}
</article>"""


@dataclass
class Section:
    heading: str | None
    points: list[dict]
    target_words: int


@dataclass
class Plan:
    title: str
    sections: list[Section]
    cut: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=1)

    def render_notes(self) -> str:
        lines = [f"Title: {self.title}"]
        for s in self.sections:
            lines.append(f"Section: {s.heading}" if s.heading else "Section:")
            lines += [f"- {p['note']}" for p in s.points]
            lines.append(f"(about {s.target_words} words)")
        return "\n".join(lines)

    @property
    def target_words(self) -> int:
        return sum(s.target_words for s in self.sections)


def parse_plan(raw: str) -> Plan:
    d = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
    secs = [Section(s.get("heading"), s.get("points", []), int(s.get("target_words", 120))) for s in d["sections"]]
    return Plan(d["title"], secs, d.get("cut", []))


def edit_plan(draft: str, *, model: str = "opus", ratio: float = 0.7) -> Plan:
    target = round(len(draft.split()) * ratio, -1)
    return parse_plan(claude(EDIT.format(draft=draft, target=int(target)), model=model))


def notes_for_article(text: str, *, model: str = "sonnet") -> Plan:
    return parse_plan(claude(NOTES_FROM_ARTICLE.format(text=text), model=model))
