"""B14: best of 4 samples per draft, picked by local checks only. Does it keep more of the draft?

B12/B13's pipeline output is short (about 300 words from 1,100-word drafts) because pruning removes
what the draft does not support. Sampling several pool-writer drafts and keeping the one that
retains the most supported content should give longer, fuller pieces. The pick uses only the
claim check (number of supported claims after pruning), never Pangram.
Drafts: B12's a0610 to a0629. Seed 0 is B12's R generation; seeds 1 to 3 are new, same prompts.
Each sample is pruned (b11_prune.prune_one) and cleaned (b13_cleanup.clean_one) exactly as B13.

Usage:
  for s in 1 2 3: uv run python experiments/gen_mlx.py results/b12_prompts.jsonl results/b14_gen_s$s.jsonl --guard --adapter models/lora-13b-pool-mlx --seed $s
  uv run python experiments/b14_bestof.py pick
  uv run python experiments/b14_bestof.py record B_a0610=AI ...
"""

import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.quality import quality_pair

sys.path.insert(0, str(ROOT / "experiments"))
from b11_prune import prune_one  # noqa: E402
from b12_replicate import _drafts  # noqa: E402
from b13_cleanup import clean_one  # noqa: E402
from judge_calibrate import _cut  # noqa: E402

TEXTS = ROOT / "results" / "b14_texts.jsonl"
OUT = ROOT / "results" / "b14_bestof.json"


def pick():
    drafts = _drafts()
    human = [json.loads(line)["text"] for line in (ROOT / "data" / "human.jsonl").open()]
    b13 = {r["id"][2:]: r for r in map(json.loads, (ROOT / "results" / "b13_texts.jsonl").open())}
    samples = {k: [{"seed": 0, "text": b13[k]["text"], "claims_entailed": b13[k]["claims_entailed"],
                    "claims_total": b13[k]["claims_total"]}] for k in drafts}
    gens = [(s, json.loads(line)) for s in (1, 2, 3)
            for line in (ROOT / "results" / f"b14_gen_s{s}.jsonl").open()]

    def one(item):
        s, g = item
        key = g["id"][2:]
        pruned, _ = prune_one(g["text"], drafts[key])
        text, _ = clean_one(pruned)
        cc = claim_check(drafts[key], text)
        return key, {"seed": s, "text": text, "claims_entailed": cc["claims_entailed"], "claims_total": cc["claims_total"]}

    with ThreadPoolExecutor(2) as ex:
        for key, r in ex.map(one, gens):
            samples[key].append(r)
    rows = []
    for key, cands in samples.items():
        best = max(cands, key=lambda c: (c["claims_entailed"], c["claims_entailed"] / max(1, c["claims_total"])))
        cut = _cut(human[int(key[1:])], len(best["text"].split()))
        rows.append({"id": f"B_{key}", "seed": best["seed"], "text": best["text"], "words": len(best["text"].split()),
                     "claims_entailed": best["claims_entailed"], "claims_total": best["claims_total"],
                     "quality_vs_human_cut": quality_pair(cut, best["text"]),
                     "candidates": [{k: c[k] for k in ("seed", "claims_entailed", "claims_total")} | {"words": len(c["text"].split())}
                                    for c in cands]})
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    summary = {"words": statistics.mean(r["words"] for r in rows),
               "claims_entailed": statistics.mean(r["claims_entailed"] for r in rows),
               "claim_support": statistics.mean(r["claims_entailed"] / max(1, r["claims_total"]) for r in rows),
               "quality_vs_human_cut": statistics.mean(r["quality_vs_human_cut"] for r in rows),
               "seed0_picked": sum(r["seed"] == 0 for r in rows)}
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
    pick() if sys.argv[1] == "pick" else record(sys.argv[2:])
