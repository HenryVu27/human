"""B12: replicate the B7-P plus B11 pipeline on 20 new drafts, against a length-matched control.

Pipeline (cell R), fixed from B7 cell P and B11 before any B12 text exists:
  1. Sonnet extracts the draft's facts and keeps the specific ones (b6_selection.specific).
  2. The pool writer (models/lora-13b-pool-mlx) writes the draft's full length from them, Guard on,
     seed 0 (experiments/gen_mlx.py --guard).
  3. Sonnet marks sentences the draft does not support; they and exact repeats are deleted
     (b11_prune.prune_one). No word is changed or added.
Control (cell K): Sonnet condenses the draft itself to the same word count as its R text, adding
nothing (B10's prompt). B10 showed condensed drafts read AI 20/20, so K separates "shorter" from
"rewritten by the pipeline".
Drafts: dev a0610 to a0629, by id, fixed before generation. Also scored: claim support (claim
check against the draft) and the quality judge (R against the draft).

Usage:
  uv run python experiments/b12_replicate.py prompts
  uv run python experiments/gen_mlx.py results/b12_prompts.jsonl results/b12_generations.jsonl --guard --adapter models/lora-13b-pool-mlx
  uv run python experiments/b12_replicate.py finish    prune, control, claim check, quality judge
  uv run python experiments/b12_replicate.py record R_a0610=AI ...
"""

import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.quality import quality_pair
from humanizer.data.facts import Facts, extract, facts_prompt
from humanizer.data.lora import MAX_WORDS
from humanizer.llm import claude

sys.path.insert(0, str(ROOT / "experiments"))
from b6_selection import specific  # noqa: E402
from b10_compress import CONDENSE  # noqa: E402
from b11_prune import prune_one  # noqa: E402

PROMPTS = ROOT / "results" / "b12_prompts.jsonl"
GENS = ROOT / "results" / "b12_generations.jsonl"
TEXTS = ROOT / "results" / "b12_texts.jsonl"
OUT = ROOT / "results" / "b12_replicate.json"
IDS = [f"a{i:04d}" for i in range(610, 630)]


def _drafts() -> dict[str, str]:
    d = {r["id"]: r["text"] for r in map(json.loads, (ROOT / "data" / "drafts" / "dev.jsonl").open())}
    return {i: d[i] for i in IDS}


def prompts():
    drafts = _drafts()
    with ThreadPoolExecutor(4) as ex:
        facts = list(ex.map(extract, drafts.values()))
        keep = list(ex.map(specific, facts))
    rows = []
    for (key, draft), f, k in zip(drafts.items(), facts, keep):
        spec = Facts(f.topic, [f.facts[j] for j in k])
        words = min(MAX_WORDS, len(draft.split()))
        rows.append({"id": f"R_{key}", "source": key, "allowed_text": draft, "prompt": facts_prompt(spec, words, key),
                     "target_words": int(round(words, -1)), "max_new_tokens": int(words * 1.3 * 1.5) + 64,
                     "n_facts": len(spec.facts), "n_facts_all": len(f.facts)})
    PROMPTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print([(r["id"], r["n_facts"], r["n_facts_all"]) for r in rows])


def finish():
    drafts = _drafts()
    gens = [json.loads(line) for line in GENS.open()]

    def one(g):
        key = g["id"][2:]
        draft = drafts[key]
        text, stats = prune_one(g["text"], draft)
        n = max(50, int(round(len(text.split()), -1)))
        control = claude(CONDENSE.format(n=n, text=draft), model="sonnet").strip()
        out = []
        for cell, t in (("R", text), ("K", control)):
            cc = claim_check(draft, t)
            out.append({"id": f"{cell}_{key}", "cell": cell, "text": t, "words": len(t.split()),
                        "claims_total": cc["claims_total"], "claims_entailed": cc["claims_entailed"],
                        "unsupported_specifics": cc["unsupported_specifics"],
                        "quality_vs_draft": quality_pair(draft, t) if cell == "R" else None,
                        **({"words_before_prune": g["words"], **stats} if cell == "R" else {})})
        return out

    with ThreadPoolExecutor(2) as ex:
        rows = [r for pair in ex.map(one, gens) for r in pair]
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    summary = {c: {"words": statistics.mean(r["words"] for r in rows if r["cell"] == c),
                   "claim_support": statistics.mean(r["claims_entailed"] / max(1, r["claims_total"])
                                                    for r in rows if r["cell"] == c)} for c in "RK"}
    summary["R"]["quality_win_rate"] = statistics.mean(r["quality_vs_draft"] for r in rows if r["cell"] == "R")
    OUT.write_text(json.dumps({"checks": summary}, indent=1))
    print(json.dumps(summary, indent=1))


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {c: {v: sum(verdicts[i] == v for i in ids if i[0] == c) for v in ("AI", "Mixed", "Human")} for c in "RK"}
    out = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    step = sys.argv[1]
    {"prompts": prompts, "finish": finish}.get(step, lambda: record(sys.argv[2:]))()
