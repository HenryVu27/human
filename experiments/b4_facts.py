"""B4: does a writer trained on fact-only notes pass Pangram when the facts come from an AI draft?

Same design as B3 (experiments/b3_notes_leak.py), with fact-only notes (humanizer.data.facts)
and a 13B adapter retrained on that note shape (lora-13b-facts, trained on the PC).
Group A: facts of AI drafts dev a0600-a0609. Group B: facts of the same 10 held-out human
articles as B3. Selection by file order, fixed before generation.

Length for A: facts times the training set's median words per fact, so the writer sees the
same fact density as in training (capped at the training maximum). B: the article's length.

Usage:
  uv run python experiments/b4_facts.py prompts   -> results/gpu13b/b4_prompts.jsonl (copy to the PC)
  uv run python experiments/b4_facts.py freeze    (after results/gpu13b/out_facts/b4_generations.jsonl is back)
  uv run python experiments/b4_facts.py check     claim check and quality judge for group A
  uv run python experiments/b4_facts.py record A_a0600=AI ...   dashboard verdicts
"""

import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.quality import quality_pair
from humanizer.data.facts import OUT as FACTS, extract, facts_prompt
from humanizer.data.lora import MAX_WORDS

PROMPTS = ROOT / "results" / "gpu13b" / "b4_prompts.jsonl"
GENS = ROOT / "results" / "gpu13b" / "out_facts" / "b4_generations.jsonl"
TEXTS = ROOT / "results" / "b4_texts.jsonl"
OUT = ROOT / "results" / "b4_facts.json"
DEV_IDS = [f"a{i:04d}" for i in range(600, 610)]


def _max_new(words: int) -> int:
    return int(words * 1.3 * 1.5) + 64


def prompts():
    per_fact = json.loads((FACTS / "meta.json").read_text())["median_words_per_fact"]
    drafts = {d["id"]: d for d in map(json.loads, (ROOT / "data" / "drafts" / "dev.jsonl").open())}
    with ThreadPoolExecutor(4) as ex:
        facts = list(ex.map(lambda i: extract(drafts[i]["text"]), DEV_IDS))
    rows = []
    for i, f in zip(DEV_IDS, facts):
        words = min(MAX_WORDS, len(f.facts) * per_fact)
        rows.append({"id": i, "group": "A_ai_facts", "prompt": facts_prompt(f, words, i),
                     "target_words": int(round(words, -1)), "max_new_tokens": _max_new(words), "n_facts": len(f.facts)})
    b3_ids = [json.loads(line)["id"] for line in (ROOT / "data" / "lora" / "valid.jsonl").open()][:10]
    valid = {r["id"]: r for r in map(json.loads, (FACTS / "valid.jsonl").open())}
    for i in b3_ids:
        r = valid[i]
        words = len(r["completion"].split())
        rows.append({"id": i, "group": "B_human_facts", "prompt": r["prompt"], "target_words": words,
                     "max_new_tokens": _max_new(words), "n_facts": r["n_facts"]})
    PROMPTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "prompts;", [(r["id"], r["n_facts"], r["target_words"]) for r in rows])


def freeze():
    group = {r["id"]: r["group"] for r in map(json.loads, PROMPTS.open())}
    rows = [{"group": group[g["id"]], **g} for g in map(json.loads, GENS.open()) if g["seed"] == 0]
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "texts;", sum(r["words"] for r in rows), "words")


def check():
    drafts = {d["id"]: d for d in map(json.loads, (ROOT / "data" / "drafts" / "dev.jsonl").open())}
    rows = [r for r in map(json.loads, TEXTS.open()) if r["group"] == "A_ai_facts"]

    def one(r):
        d = drafts[r["id"]]["text"]
        cc = claim_check(d, r["text"])
        return {"id": r["id"], "words": r["words"], "claim_pass": cc["pass"],
                "unsupported_specifics": cc["unsupported_specifics"],
                "entailed": f"{cc['claims_entailed']}/{cc['claims_total']}", "quality_vs_draft": quality_pair(d, r["text"])}

    with ThreadPoolExecutor(2) as ex:
        res = list(ex.map(one, rows))
    share = [int(x["entailed"].split("/")[0]) / max(1, int(x["entailed"].split("/")[1])) for x in res]
    summary = {"claim_pass_rate": statistics.mean(x["claim_pass"] for x in res),
               "no_new_specifics_rate": statistics.mean(not x["unsupported_specifics"] for x in res),
               "entailed_share": statistics.mean(share),
               "quality_win_rate": statistics.mean(x["quality_vs_draft"] for x in res),
               "mean_words": statistics.mean(x["words"] for x in res)}
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    out |= {"group_a_checks": summary, "group_a_rows": res}
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(summary, indent=1))


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    rows = [json.loads(line) for line in TEXTS.open()]
    assert set(verdicts) == {f"{r['group'][0]}_{r['id']}" for r in rows}, "need a verdict for every text"
    summary = {}
    for g in ("A_ai_facts", "B_human_facts"):
        v = [verdicts[f"{g[0]}_{r['id']}"] for r in rows if r["group"] == g]
        summary[g] = {x: v.count(x) for x in ("AI", "Mixed", "Human")} | {"n": len(v)}
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    out |= {"pangram_summary": summary,
            "pangram_rows": [{"group": r["group"], "id": r["id"], "words": r["words"],
                              "pangram": verdicts[f"{r['group'][0]}_{r['id']}"]} for r in rows]}
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    step = sys.argv[1]
    {"prompts": prompts, "freeze": freeze, "check": check}.get(step, lambda: record(sys.argv[2:]))()
