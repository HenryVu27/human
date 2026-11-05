"""B7: let the writer choose what to say, the way a human writer does.

B5 showed Pangram follows who chose the content: facts from a human article read Human, facts from
an AI draft read AI, on the same topics and whatever the wording. B1 showed base-model text that
starts from human context reads Human. So the humanizer has to let the base model plan the
article, giving it only part of the draft's material and room to write the rest itself.

Pool writer: the 13B adapter retrained on pairs whose prompt lists only a random 20 to 60 percent
of the human article's facts (same format and length line as data/facts), with the full article as
the target. It learns to write a whole human article around a partial pool.

Cells on dev a0600 to a0609, all with the Guard (names, numbers and quotes only from the draft),
length = the draft's length capped at MAX_WORDS, seed 0:

  H: B4 facts adapter (no retraining), the draft's specific facts (B6's list), draft length
  P: pool adapter, the draft's specific facts, draft length
  Q: pool adapter, a random 40 percent of all the draft's facts, draft length

Selection and cells fixed before generation. P against B6 F (same facts, short) shows what the
base model's own planning adds; P against Q shows whether specific facts matter once it plans.
Generic content the writer adds is counted by the claim check and reported, not hidden.

Usage:
  uv run python experiments/b7_pool.py data      -> data/pool/{train,valid}.jsonl (copy to the PC)
  uv run python experiments/b7_pool.py prompts   -> results/b7_prompts.jsonl
  uv run python experiments/gen_mlx.py results/b7_prompts_H.jsonl results/b7_generations.jsonl --guard
  uv run python experiments/gen_mlx.py results/b7_prompts_PQ.jsonl results/b7_generations.jsonl --guard --adapter models/lora-13b-pool-mlx
  uv run python experiments/b7_pool.py record H_a0600=AI ...
"""

import json
import random
import sys

from humanizer import ROOT
from humanizer.data.facts import OUT as FACTS, Facts, extract, facts_prompt
from humanizer.data.lora import MAX_WORDS

sys.path.insert(0, str(ROOT / "experiments"))
from b5_matched import _sources  # noqa: E402
from b6_selection import specific  # noqa: E402

POOL = ROOT / "data" / "pool"
OUT = ROOT / "results" / "b7_pool.json"
NUMS = range(600, 610)


def _split(prompt: str) -> tuple[str, str, list[str]]:
    lines = prompt.split("\n")
    topic = lines[1].removeprefix("Topic: ")
    words = lines[2].removeprefix("Length: about ").removesuffix(" words")
    return topic, words, [x[2:] for x in lines[3:] if x.startswith("- ")]


def data():
    """Same rows as data/facts, with each fact list cut to a random 20 to 60 percent (at least 3)."""
    POOL.mkdir(parents=True, exist_ok=True)
    for name in ("train", "valid"):
        rows = []
        for r in map(json.loads, (FACTS / f"{name}.jsonl").open()):
            topic, words, facts = _split(r["prompt"])
            rnd = random.Random(f"pool{r['id']}")
            k = max(3, round(len(facts) * rnd.uniform(0.2, 0.6)))
            keep = rnd.sample(facts, min(k, len(facts)))
            prompt = f"Facts:\nTopic: {topic}\nLength: about {words} words\n" + "".join(f"- {x}\n" for x in keep) + "\nArticle:\n"
            rows.append(r | {"prompt": prompt, "n_facts": len(keep), "n_facts_full": len(facts)})
        (POOL / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        print(name, len(rows), "rows; mean share kept",
              round(sum(r["n_facts"] / r["n_facts_full"] for r in rows) / len(rows), 2))


def prompts():
    src = _sources()
    rows = {"H": [], "P": [], "Q": []}
    for i in NUMS:
        key = f"a{i:04d}"
        draft = src[key]
        f = extract(draft)
        spec = Facts(f.topic, [f.facts[j] for j in specific(f)])
        rnd = Facts(f.topic, random.Random(f"Q{key}").sample(f.facts, round(len(f.facts) * 0.4)))
        words = min(MAX_WORDS, len(draft.split()))
        for cell, facts in (("H", spec), ("P", spec), ("Q", rnd)):
            rows[cell].append({"id": f"{cell}_{key}", "cell": cell, "source": key, "allowed_text": draft,
                               "prompt": facts_prompt(facts, words, key), "target_words": int(round(words, -1)),
                               "max_new_tokens": int(words * 1.3 * 1.5) + 64, "n_facts": len(facts.facts)})
    for name, cells in (("H", "H"), ("PQ", "PQ")):
        (ROOT / "results" / f"b7_prompts_{name}.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for c in cells for r in rows[c]))
    print({c: [r["n_facts"] for r in v] for c, v in rows.items()}, "words", [r["target_words"] for r in rows["P"]])


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in (ROOT / "results" / "b7_generations.jsonl").open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {c: {v: sum(verdicts[i] == v for i in ids if i[0] == c) for v in ("AI", "Mixed", "Human")} for c in "HPQ"}
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))




def check():
    """Claim check of every P and Q text against its draft, plus the repeated-sentence share."""
    import re
    from concurrent.futures import ThreadPoolExecutor

    from humanizer.checks.claims import claim_check

    src = _sources()
    rows = [r for r in map(json.loads, (ROOT / "results" / "b7_generations.jsonl").open()) if r["id"][0] in "PQ"]

    def one(r):
        cc = claim_check(src[r["id"][2:]], r["text"])
        sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n", r["text"]) if len(x.strip()) > 30]
        return {"id": r["id"], "words": r["words"], "repeat_share": round(1 - len(set(sents)) / max(1, len(sents)), 2),
                "claims_total": cc["claims_total"], "claims_entailed": cc["claims_entailed"],
                "unsupported_specifics": cc["unsupported_specifics"], "claim_pass": cc["pass"]}

    with ThreadPoolExecutor(2) as ex:
        res = list(ex.map(one, rows))
    out = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(out | {"claim_rows": res}, indent=1))
    for r in res:
        print(r["id"], r["words"], r["repeat_share"], f"{r['claims_entailed']}/{r['claims_total']}", r["unsupported_specifics"][:3])


if __name__ == "__main__":
    step = sys.argv[1]
    {"data": data, "prompts": prompts, "check": check}.get(step, lambda: record(sys.argv[2:]))()
