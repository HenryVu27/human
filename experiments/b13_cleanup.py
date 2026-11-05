"""B13: does a deletion-only cleanup fix the pruned text's quality without losing the Human verdict?

B12's pipeline output reads Human 12/20 but loses every quality comparison: the judge prefers the
AI draft 39/40 and Sonnet's own condensation 20/20. Reading it shows why: the same point is made
two or three times, list lead-ins ("These behaviors may include:") are left with nothing after
them, and the Guard produced odd fragments like "(S.D.)". So: for each B12 R text, Sonnet marks
sentences that repeat an earlier sentence's content, lead-ins or headings with nothing left under
them, and broken fragments; those are deleted. No word is changed or added. Then the quality
judge (against the condensation K and the draft), the claim check and Pangram run again.
Texts: all 20 B12 R texts, fixed before scanning.

Usage:
  uv run python experiments/b13_cleanup.py clean
  uv run python experiments/b13_cleanup.py record C_a0610=AI ...
"""

import json
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.quality import quality_pair
from humanizer.llm import claude

sys.path.insert(0, str(ROOT / "experiments"))
from b11_prune import _units  # noqa: E402
from b12_replicate import _drafts  # noqa: E402

TEXTS = ROOT / "results" / "b13_texts.jsonl"
OUT = ROOT / "results" / "b13_cleanup.json"

CLEAN = """Below is a numbered list of the sentences and headings of an article, in order. List the ones a
careful editor would delete because they:
- repeat the content of an earlier sentence (keep the first, list the later ones),
- introduce a list, example or section that has nothing after it,
- are headings with nothing under them, or
- are broken fragments that do not read as a sentence.
Do not list anything else.

Return only JSON: {{"delete": [numbers]}}

{sentences}"""


def clean_one(text: str) -> tuple[str, int]:
    units = _units(text)
    listing = "\n".join(f"{i}. {s}" for i, (_, s) in enumerate(units, 1))
    raw = claude(CLEAN.format(sentences=listing), model="sonnet")
    bad = {int(n) - 1 for n in json.loads(re.search(r"\{.*\}", raw, re.S).group(0))["delete"]}
    paras = {}
    for i, (p, s) in enumerate(units):
        if i not in bad:
            paras.setdefault(p, []).append(s)
    return "\n".join(" ".join(v) for _, v in sorted(paras.items())), len(bad)


def clean():
    drafts = _drafts()
    b12 = {r["id"]: r for r in map(json.loads, (ROOT / "results" / "b12_texts.jsonl").open())}
    keys = [k[2:] for k in b12 if k.startswith("R_")]

    def one(k):
        text, deleted = clean_one(b12[f"R_{k}"]["text"])
        cc = claim_check(drafts[k], text)
        return {"id": f"C_{k}", "text": text, "words": len(text.split()), "deleted": deleted,
                "claims_total": cc["claims_total"], "claims_entailed": cc["claims_entailed"],
                "quality_vs_condensed": quality_pair(b12[f"K_{k}"]["text"], text),
                "quality_vs_draft": quality_pair(drafts[k], text)}

    with ThreadPoolExecutor(2) as ex:
        rows = list(ex.map(one, keys))
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    summary = {k: statistics.mean(r[k] for r in rows) for k in ("words", "deleted", "quality_vs_condensed", "quality_vs_draft")}
    summary["claim_support"] = statistics.mean(r["claims_entailed"] / max(1, r["claims_total"]) for r in rows)
    OUT.write_text(json.dumps({"checks": summary}, indent=1))
    print(json.dumps(summary, indent=1))


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {v: sum(verdicts[i] == v for i in ids) for v in ("AI", "Mixed", "Human")}
    out = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    clean() if sys.argv[1] == "clean" else record(sys.argv[2:])
