"""B11: delete what the draft does not support. Does the B7 gain survive?

B7's pool writer moved AI drafts toward Human (cell P: 6 Human, 3 Mixed, 1 AI) by writing much of
the article itself: only about 45% of its claims are supported by the draft. The outside evidence
(GitHub humanization lab, Whitcomb) says deleting sentences, without rewording any, keeps a Human
verdict. So: for every B7 P and Q text (all 20, fixed before scanning), Sonnet marks the sentences
whose content the draft does not support, and those sentences plus exact repeats are deleted. No
word is changed or added. Then the claim check runs again and Pangram scans the pruned texts.

If the pruned texts keep most of their Human verdicts at high claim support, prune-after-free-writing
is the humanizer's shape. If they fall back to AI, the Human verdicts came from the added content.

Usage:
  uv run python experiments/b11_prune.py prune
  uv run python experiments/b11_prune.py record P_a0600=AI ...
"""

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.llm import claude

sys.path.insert(0, str(ROOT / "experiments"))
from b5_matched import _sources  # noqa: E402

TEXTS = ROOT / "results" / "b11_texts.jsonl"
OUT = ROOT / "results" / "b11_prune.json"

UNSUPPORTED = """Below is a source draft and a numbered list of sentences from an article written from it.
List the sentences that state something the draft does not say or clearly imply: a fact, number,
claim, example, recommendation or explanation that is not in the draft. Keep sentences that only
restate the draft, connect ideas, or are headings for content the draft covers.

Return only JSON: {{"unsupported": [sentence numbers]}}

<draft>
{draft}
</draft>

<sentences>
{sentences}
</sentences>"""

SPLIT = re.compile(r"(?<=[.!?])\s+")


def _units(text: str) -> list[tuple[int, str]]:
    """(paragraph index, sentence) for every sentence, so paragraphs survive deletion."""
    return [(p, s) for p, para in enumerate(text.split("\n")) for s in SPLIT.split(para.strip()) if s.strip()]


def prune_one(text: str, draft: str) -> tuple[str, dict]:
    units = _units(text)
    listing = "\n".join(f"{i}. {s}" for i, (_, s) in enumerate(units, 1))
    raw = claude(UNSUPPORTED.format(draft=draft, sentences=listing), model="sonnet")
    bad = {int(n) - 1 for n in json.loads(re.search(r"\{.*\}", raw, re.S).group(0))["unsupported"]}
    seen, keep = set(), []
    for i, (p, s) in enumerate(units):
        if i in bad or s in seen:
            continue
        seen.add(s)
        keep.append((p, s))
    paras = {}
    for p, s in keep:
        paras.setdefault(p, []).append(s)
    pruned = "\n".join(" ".join(v) for _, v in sorted(paras.items()))
    return pruned, {"sentences": len(units), "unsupported": len(bad), "kept": len(keep)}


def prune():
    src = _sources()
    rows = [r for r in map(json.loads, (ROOT / "results" / "b7_generations.jsonl").open()) if r["id"][0] in "PQ"]

    def one(r):
        draft = src[r["id"][2:]]
        text, stats = prune_one(r["text"], draft)
        cc = claim_check(draft, text)
        return {"id": r["id"], "text": text, "words": len(text.split()), "words_before": r["words"], **stats,
                "claims_total": cc["claims_total"], "claims_entailed": cc["claims_entailed"],
                "unsupported_specifics": cc["unsupported_specifics"]}

    with ThreadPoolExecutor(2) as ex:
        res = list(ex.map(one, rows))
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in res))
    for r in res:
        print(r["id"], r["words_before"], "->", r["words"], f"{r['claims_entailed']}/{r['claims_total']}")


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {c: {v: sum(verdicts[i] == v for i in ids if i[0] == c) for v in ("AI", "Mixed", "Human")} for c in "PQ"}
    OUT.write_text(json.dumps({"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    prune() if sys.argv[1] == "prune" else record(sys.argv[2:])
