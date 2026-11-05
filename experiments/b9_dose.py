"""B9: how much of the content has to come from a human source? (dose-response)

B5: on the same topics, facts from the human article read Human 10/10 (cell D), facts from the
AI draft 1/10 (cell A). Here each topic gets a fixed number of facts N (the human article's fact
count, so the 100% cell is B5 cell D itself) with a share s taken from the human article and the
rest from the AI draft, shuffled. B4 facts adapter on the Mac, seed 0, length N x median words
per fact, same as B5. Levels s = 0, 1/3, 2/3 are new (30 texts); s = 1 is B5 cell D.

If 1/3 flips most texts, a retrieve-and-cite step (human sources for the draft's claims) is worth
building. If 2/3 or more is needed, the content has to come mostly from a human or a base model.

Usage:
  uv run python experiments/b9_dose.py prompts
  uv run python experiments/gen_mlx.py results/b9_prompts.jsonl results/b9_generations.jsonl
  uv run python experiments/b9_dose.py record S0_a0600=AI ...
"""

import json
import random
import sys

from humanizer import ROOT
from humanizer.data.facts import OUT as FACTS, Facts, extract, facts_prompt
from humanizer.data.lora import MAX_WORDS

sys.path.insert(0, str(ROOT / "experiments"))
from b5_matched import _sources  # noqa: E402

PROMPTS = ROOT / "results" / "b9_prompts.jsonl"
GENS = ROOT / "results" / "b9_generations.jsonl"
OUT = ROOT / "results" / "b9_dose.json"
LEVELS = {"S0": 0.0, "S1": 1 / 3, "S2": 2 / 3}


def prompts():
    per_fact = json.loads((FACTS / "meta.json").read_text())["median_words_per_fact"]
    src = _sources()
    rows = []
    for i in range(600, 610):
        a, h = extract(src[f"a{i:04d}"]), extract(src[f"h{i:04d}"])  # cached: the B5 lists
        n = len(h.facts)
        for cell, s in LEVELS.items():
            rnd = random.Random(f"{cell}{i}")
            k = round(n * s)
            items = rnd.sample(h.facts, k) + rnd.sample(a.facts, min(len(a.facts), n - k))
            f = Facts(h.topic if s >= 0.5 else a.topic, items)
            words = min(MAX_WORDS, len(items) * per_fact)
            rows.append({"id": f"{cell}_a{i:04d}", "cell": cell, "human_share": round(k / len(items), 3),
                         "prompt": facts_prompt(f, words, f"{cell}{i}"), "target_words": int(round(words, -1)),
                         "max_new_tokens": int(words * 1.3 * 1.5) + 64, "n_facts": len(items)})
    PROMPTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "prompts;", [(r["id"], r["n_facts"], r["human_share"]) for r in rows])


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in GENS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {c: {v: sum(verdicts[i] == v for i in ids if i.startswith(c)) for v in ("AI", "Mixed", "Human")}
               for c in LEVELS}
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    prompts() if sys.argv[1] == "prompts" else record(sys.argv[2:])
