"""B5: on the same 10 topics, is the Pangram signal in the AI draft's wording or in its choice of facts?

A 2 by 2 on dev topics 600 to 609 (each AI draft a06xx is a mirror of human article h06xx,
neither trained on), all written by the B4 facts adapter on the Mac, seed 0:

  cell A: facts of the AI draft, in the extractor's words (as B4; regenerated here on the Mac)
  cell C: the same facts reworded (only names, numbers and quotes kept verbatim)
  cell D: facts of the human original, as A
  cell E: the same facts reworded, as C

Length for every cell: facts times the training median words per fact, capped at MAX_WORDS.
A and C share the fact order (shuffle key a06xx), as do D and E (key h06xx).
Selection is fixed by id range before any text is scanned.

Usage:
  uv run python experiments/b5_matched.py prompts
  uv run python experiments/gen_mlx.py results/b5_prompts.jsonl results/b5_generations.jsonl
  uv run python experiments/b5_matched.py overlap
  uv run python experiments/b5_matched.py record A_a0600=AI ...   dashboard verdicts
"""

import json
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.data.facts import OUT as FACTS, extract, facts_prompt, reword
from humanizer.data.lora import MAX_WORDS, _fits

PROMPTS = ROOT / "results" / "b5_prompts.jsonl"
GENS = ROOT / "results" / "b5_generations.jsonl"
OUT = ROOT / "results" / "b5_matched.json"
NUMS = range(600, 610)


def _sources():
    drafts = {d["id"]: d["text"] for d in map(json.loads, (ROOT / "data" / "drafts" / "dev.jsonl").open())}
    human = [json.loads(line)["text"] for line in (ROOT / "data" / "human.jsonl").open()]
    return {f"a{i:04d}": drafts[f"a{i:04d}"] for i in NUMS} | {f"h{i:04d}": _fits(human[i]) for i in NUMS}


def prompts():
    per_fact = json.loads((FACTS / "meta.json").read_text())["median_words_per_fact"]
    src = _sources()
    with ThreadPoolExecutor(4) as ex:
        facts = dict(zip(src, ex.map(extract, src.values())))
        worded = dict(zip(facts, ex.map(reword, facts.values())))
    rows = []
    for cell, key, f in [(c, k, (facts if c in "AD" else worded)[k]) for c in "ACDE"
                         for k in src if (k[0] == "a") == (c in "AC")]:
        words = min(MAX_WORDS, len(f.facts) * per_fact)
        rows.append({"id": f"{cell}_{key}", "cell": cell, "source": key, "prompt": facts_prompt(f, words, key),
                     "target_words": int(round(words, -1)), "max_new_tokens": int(words * 1.3 * 1.5) + 64,
                     "n_facts": len(f.facts)})
    PROMPTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "prompts;", [(r["id"], r["n_facts"], r["target_words"]) for r in rows])


def _ng(t: str, n: int = 4) -> set:
    w = re.findall(r"[a-z0-9']+", t.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def overlap():
    """Share of each text's word 4-grams found in its prompt and in its source, by cell."""
    src = _sources()
    p = {r["id"]: r for r in map(json.loads, PROMPTS.open())}
    rows = []
    for g in map(json.loads, GENS.open()):
        o, f, s = _ng(g["text"]), _ng(p[g["id"]]["prompt"]), _ng(src[p[g["id"]]["source"]])
        sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n", g["text"]) if len(x.strip()) > 30]
        rows.append({"id": g["id"], "cell": p[g["id"]]["cell"], "words": g["words"], "hit_eos": g["hit_eos"],
                     "facts_from_source": len(f & s) / max(1, len(f)), "out_in_facts": len(o & f) / max(1, len(o)),
                     "out_in_source": len(o & s) / max(1, len(o)),
                     "repeat_share": 1 - len(set(sents)) / max(1, len(sents))})
    summary = {c: {k: round(statistics.mean(r[k] for r in rows if r["cell"] == c), 3)
                   for k in ("words", "hit_eos", "facts_from_source", "out_in_facts", "out_in_source", "repeat_share")}
               for c in "ACDE"}
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(out | {"overlap_summary": summary, "overlap_rows": rows}, indent=1))
    print(json.dumps(summary, indent=1))


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in GENS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {c: {v: sum(verdicts[i] == v for i in ids if i[0] == c) for v in ("AI", "Mixed", "Human")} for c in "ACDE"}
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    step = sys.argv[1]
    {"prompts": prompts, "overlap": overlap}.get(step, lambda: record(sys.argv[2:]))()
