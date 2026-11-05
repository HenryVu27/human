"""B23: what does the prune delete, and how much length would a narrower rule keep?

B14's writer writes full length (raw median 1,218 words against a 1,065-word target); the prune
(b11_prune.UNSUPPORTED) keeps about 385. That prompt deletes any "fact, number, claim, example,
recommendation or explanation that is not in the draft". The project's rule (spec, CLAUDE.md) is
narrower: add no facts, numbers, names, dates or quotes. Between the two sits the writer's own
elaboration: reasoning, implications, generic examples, opinion framed as the writer's, questions,
transitions. B14 reads Human because the writer, not the AI draft, chooses what to say around a few
facts; if elaboration is most of what the prune deletes, a narrower rule might keep both length and
the writer's plan.

Fixed before any B23 output exists (2026-11-05 13:30):
- Texts: B14's seed-1 raw generations (results/b14_gen_s1.jsonl) for the 20 drafts a0610 to a0629.
  One fixed seed, not B14's pick, so the sample is not chosen by any score.
- Sonnet labels every sentence against the draft: S restates or connects the draft; N a new
  specific (number, date, name, quote, study, statistic, named event, product or place); C a new
  general claim about the world that could be checked true or false, with no specifics; E the
  writer's elaboration that asserts no new checkable fact (reasoning or implication from the
  draft, generic or hypothetical example, analogy, opinion or advice framed as the writer's,
  question, transition); X template repeats (humanizer.checks.repeats), labelled before Sonnet.
- Report words by label, and words kept under rule SE (keep S and E) against B14's prune.
- Prediction: E is at least 30% of raw words, so SE keeps at least 60% of the draft's length.
- Only if SE averages 60% or more of the draft's length: build SE texts for a0610 to a0619 (B13
  cleanup after deletion), run the claim check, and scan all 10 (cell E). That scan is the held-out
  judge; nothing about the rule is changed after it.

Usage:
  uv run python experiments/b23_prune_tiers.py label
"""

import json
import re
import statistics
import sys

from humanizer import ROOT
from humanizer.checks.repeats import template_repeats
from humanizer.llm import claude_many

sys.path.insert(0, str(ROOT / "experiments"))
from b11_prune import _units  # noqa: E402
from b12_replicate import _drafts  # noqa: E402

GEN = ROOT / "results" / "b14_gen_s1.jsonl"
LABELS = ROOT / "results" / "b23_labels.jsonl"
OUT = ROOT / "results" / "b23_prune_tiers.json"
TIERS = "SNCEX"

PROMPT = """Below is a source draft and a numbered list of sentences from an article written from it.
Label every sentence with one letter:
S: it restates, summarizes or connects what the draft says or clearly implies.
N: it adds a specific the draft does not have: a number, date, name, quote, study, statistic, named event, product or place.
C: it adds a general claim about the world, with no specifics, that could be checked true or false and is not in the draft.
E: it is the writer's own elaboration and asserts no new checkable fact: reasoning or an implication drawn from the draft, a generic or hypothetical example, an analogy, an opinion or advice framed as the writer's, a question, or a transition.
When a sentence mixes labels, use the first that applies in the order N, C, E, S.

Return only JSON: {{"labels": {{"1": "S", "2": "E", ...}}}}

<draft>
{draft}
</draft>

<sentences>
{sentences}
</sentences>"""


def _parse(raw: str | None, n: int) -> list[str] | None:
    m = re.search(r"\{.*\}", raw or "", re.S)
    try:
        got = json.loads(m.group(0))["labels"] if m else None
    except (json.JSONDecodeError, KeyError):
        return None
    if not isinstance(got, dict):
        return None
    out = [str(got.get(str(i), "")).strip().upper()[:1] for i in range(1, n + 1)]
    return out if all(x in TIERS for x in out) else None


def label():
    drafts = _drafts()
    gens = [g for g in map(json.loads, GEN.open()) if g["id"][2:] in drafts]
    jobs = []
    for g in gens:
        units = _units(g["text"])
        sents = [s for _, s in units]
        rep = template_repeats(sents)
        listing = "\n".join(f"{i}. {s}" for i, s in enumerate(sents, 1))
        jobs.append((g, units, rep, PROMPT.format(draft=drafts[g["id"][2:]], sentences=listing)))
    replies = claude_many([j[3] for j in jobs], model="sonnet", workers=2)  # B16's pick holds the other 2
    rows = []
    for (g, units, rep, _), raw in zip(jobs, replies):
        labels = _parse(raw, len(units))
        if labels is None:
            print("unparsed", g["id"])
            continue
        labels = ["X" if i in rep else lab for i, lab in enumerate(labels)]
        rows.append({"id": g["id"][2:], "units": [[p, s, lab] for (p, s), lab in zip(units, labels)]})
    LABELS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    target = {r["source"]: r["target_words"] for r in map(json.loads, (ROOT / "results" / "b12_prompts.jsonl").open())}
    b14 = {r["id"][2:]: r["words"] for r in map(json.loads, (ROOT / "results" / "b14_texts.jsonl").open())}
    per = []
    for r in rows:
        w = {t: sum(len(s.split()) for _, s, lab in r["units"] if lab == t) for t in TIERS}
        raw_words = sum(w.values())
        per.append({"id": r["id"], "words": w, "raw": raw_words, "target": target[r["id"]],
                    "se_ratio": (w["S"] + w["E"]) / target[r["id"]], "s_ratio": w["S"] / target[r["id"]],
                    "b14_ratio": b14[r["id"]] / target[r["id"]]})
    total = sum(p["raw"] for p in per)
    summary = {"texts": len(per),
               "share_of_raw_words": {t: sum(p["words"][t] for p in per) / total for t in TIERS},
               "se_length_ratio": statistics.mean(p["se_ratio"] for p in per),
               "s_length_ratio": statistics.mean(p["s_ratio"] for p in per),
               "b14_length_ratio": statistics.mean(p["b14_ratio"] for p in per),
               "se_at_least_60pct": sum(p["se_ratio"] >= 0.6 for p in per)}
    OUT.write_text(json.dumps({"summary": summary, "per_text": per}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    label()
