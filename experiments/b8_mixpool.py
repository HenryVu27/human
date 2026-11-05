"""B8: teach the writer to drop AI-typical facts.

Pangram 4 labels as AI exactly what an LLM writes when given only a human document's topic
(its "synthetic mirrors"), and B5 showed the AI's choice of facts is what carries the signal.
Our corpus has the same thing: 593 AI mirrors (data/ai.jsonl), one per training article.

Mixed-pool writer: the 13B adapter trained on prompts whose fact list mixes a random 20 to 60
percent of the human article's facts with facts from the AI mirror of the same topic (shuffled,
same format as data/facts), and the human article as the target. To predict the article it has
to use the human facts and ignore the mirror's, so it learns which facts a human writer would
not state. Rows without a mirror keep a human-only pool (as data/pool).

Test (cell M), fixed before generation: B12's drafts a0610 to a0629, ALL of each draft's facts,
the draft's full length, Guard on, seed 0, then B11's pruning and B13's cleanup, so M compares
directly with B13's cleaned pipeline (same drafts, specific facts only, pool writer).

Usage:
  uv run python experiments/b8_mixpool.py extract   facts of the 593 mirrors (Sonnet, cached)
  uv run python experiments/b8_mixpool.py data      -> data/mixpool/{train,valid}.jsonl
  uv run python experiments/b8_mixpool.py prompts   -> results/b8_prompts.jsonl
  uv run python experiments/gen_mlx.py results/b8_prompts.jsonl results/b8_generations.jsonl --guard --adapter models/lora-13b-mixpool-mlx
  uv run python experiments/b8_mixpool.py finish    prune, clean, claim check, quality against same-topic human text
  uv run python experiments/b8_mixpool.py record M_a0610=AI ...
"""

import json
import random
import sys

from humanizer import ROOT
from humanizer.data.facts import FACTS as FACTS_PROMPT, OUT as FACTS, parse_facts
from humanizer.data.lora import _fits
from humanizer.llm import claude_many

sys.path.insert(0, str(ROOT / "experiments"))
from b7_pool import _split  # noqa: E402

MIX = ROOT / "data" / "mixpool"
MIRROR_FACTS = ROOT / "data" / "mixpool" / "mirror_facts.jsonl"


def extract():
    mirrors = [json.loads(line) for line in (ROOT / "data" / "ai.jsonl").open()]
    raws = claude_many([FACTS_PROMPT.format(text=_fits(m["text"])) for m in mirrors], model="sonnet")
    MIX.mkdir(parents=True, exist_ok=True)
    ok = 0
    with MIRROR_FACTS.open("w") as f:
        for m, raw in zip(mirrors, raws):
            try:
                facts = parse_facts(raw)
            except Exception:  # noqa: BLE001
                continue
            ok += 1
            f.write(json.dumps({"id": m["id"], "source_id": m["source_id"], "generator": m["generator"],
                                "topic": facts.topic, "facts": facts.facts}) + "\n")
    print(ok, "of", len(mirrors), "mirrors parsed")


def data():
    mirror = {r["source_id"]: r for r in map(json.loads, MIRROR_FACTS.open())}
    for name in ("train", "valid"):
        rows, mixed = [], 0
        for r in map(json.loads, (FACTS / f"{name}.jsonl").open()):
            topic, words, facts = _split(r["prompt"])
            rnd = random.Random(f"mix{r['id']}")
            k = max(3, round(len(facts) * rnd.uniform(0.2, 0.6)))
            keep = rnd.sample(facts, min(k, len(facts)))
            ai = []
            if r["id"] in mirror:
                pool = mirror[r["id"]]["facts"]
                ai = rnd.sample(pool, min(len(pool), round(len(keep) * rnd.uniform(0.5, 1.5))))
                mixed += 1
            items = keep + ai
            rnd.shuffle(items)
            prompt = f"Facts:\nTopic: {topic}\nLength: about {words} words\n" + "".join(f"- {x}\n" for x in items) + "\nArticle:\n"
            rows.append(r | {"prompt": prompt, "n_facts": len(items), "n_human": len(keep), "n_ai": len(ai)})
        (MIX / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        print(name, len(rows), "rows;", mixed, "with mirror facts; mean AI share",
              round(sum(r["n_ai"] / r["n_facts"] for r in rows) / len(rows), 2))


def prompts():
    from humanizer.data.facts import extract, facts_prompt
    from humanizer.data.lora import MAX_WORDS
    from b12_replicate import _drafts

    rows = []
    for key, draft in _drafts().items():
        f = extract(draft)
        words = min(MAX_WORDS, len(draft.split()))
        rows.append({"id": f"M_{key}", "source": key, "allowed_text": draft, "prompt": facts_prompt(f, words, key),
                     "target_words": int(round(words, -1)), "max_new_tokens": int(words * 1.3 * 1.5) + 64,
                     "n_facts": len(f.facts)})
    (ROOT / "results" / "b8_prompts.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    print([(r["id"], r["n_facts"]) for r in rows])


def finish():
    import statistics
    from concurrent.futures import ThreadPoolExecutor

    from humanizer.checks.claims import claim_check
    from humanizer.checks.quality import quality_pair
    from b11_prune import prune_one
    from b12_replicate import _drafts
    from b13_cleanup import clean_one
    from judge_calibrate import _cut

    drafts = _drafts()
    human = [json.loads(line)["text"] for line in (ROOT / "data" / "human.jsonl").open()]
    gens = [json.loads(line) for line in (ROOT / "results" / "b8_generations.jsonl").open()]

    def one(g):
        key = g["id"][2:]
        pruned, stats = prune_one(g["text"], drafts[key])
        text, _ = clean_one(pruned)
        cc = claim_check(drafts[key], text)
        return {"id": g["id"], "text": text, "words": len(text.split()), "words_before": g["words"],
                "claims_entailed": cc["claims_entailed"], "claims_total": cc["claims_total"],
                "quality_vs_human_cut": quality_pair(_cut(human[int(key[1:])], len(text.split())), text)}

    with ThreadPoolExecutor(2) as ex:
        rows = list(ex.map(one, gens))
    (ROOT / "results" / "b8_texts.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    summary = {"words": statistics.mean(r["words"] for r in rows),
               "claims_entailed": statistics.mean(r["claims_entailed"] for r in rows),
               "claim_support": statistics.mean(r["claims_entailed"] / max(1, r["claims_total"]) for r in rows),
               "quality_vs_human_cut": statistics.mean(r["quality_vs_human_cut"] for r in rows)}
    (ROOT / "results" / "b8_mixpool.json").write_text(json.dumps({"checks": summary}, indent=1))
    print(json.dumps(summary, indent=1))


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in (ROOT / "results" / "b8_texts.jsonl").open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {v: sum(verdicts[i] == v for i in ids) for v in ("AI", "Mixed", "Human")}
    path = ROOT / "results" / "b8_mixpool.json"
    out = json.loads(path.read_text())
    path.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    step = sys.argv[1]
    {"extract": extract, "data": data, "prompts": prompts, "finish": finish}.get(step, lambda: record(sys.argv[2:]))()
