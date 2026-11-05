"""B6: does cutting the AI draft's generic facts remove the signal?

B5 showed the signal follows the source (AI draft facts read AI, human-article facts read Human,
on the same topics) and survives rewording. AI drafts also state more facts than the human
article on the same topic. Two cells on dev topics 600 to 609, B4 facts adapter on the Mac, seed 0:

  cell F (specific only): the AI draft's facts that name a particular person, place, number, date,
          study, quote or concrete example; general claims, advice and definitions are cut.
  cell G (count control): a random subset of the AI draft's facts, the same size as F.

A first design used an oracle (AI facts the human original also states), but the mirrors were
written from the topic alone and share only 0 to 11 of about 50 facts with the human article,
too few to write from; those counts are kept in results/b6_selection.json as "oracle_overlap".
On the same topics AI drafts give 53 facts per document against 35, with fewer numbers (16%
against 25%) and names (28% against 43%) and more generic hedges (18% against 12%).

Rule fixed before generation: a draft takes part only if it has at least 9 specific facts (a
target of about 160 words; Pangram says it is less certain under 150), which drops a0602 and a0605.

If F reads Human and G reads AI, cutting generic padding is the editor's fix and needs no
human source. If both read Human, fewer facts is enough. If both read AI, selection alone
does not fix it.

Usage:
  uv run python experiments/b6_selection.py prompts
  uv run python experiments/gen_mlx.py results/b6_prompts.jsonl results/b6_generations.jsonl
  uv run python experiments/b6_selection.py record F_a0600=AI ...
"""

import json
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.data.facts import OUT as FACTS, Facts, extract, facts_prompt
from humanizer.data.lora import MAX_WORDS
from humanizer.llm import claude

sys.path.insert(0, str(ROOT / "experiments"))
from b5_matched import _sources  # noqa: E402

PROMPTS = ROOT / "results" / "b6_prompts.jsonl"
GENS = ROOT / "results" / "b6_generations.jsonl"
OUT = ROOT / "results" / "b6_selection.json"
NUMS = range(600, 610)

SPECIFIC = """Below is a numbered list of facts from one article. Mark each fact S if it states something particular: a named person, organization, place, product, study, date, number, quote, or a concrete example or event. Mark it G if it is a general claim, advice, definition or explanation that could appear in any article on this topic.

Return only JSON: {{"specific": [numbers of the S facts]}}

{facts}"""

SUPPORTED = """Below is an article and a numbered list of facts. For each fact, decide whether the article states it or something with the same content (wording may differ; a fact is supported only if the article clearly says it).

Return only JSON: {{"supported": [numbers of supported facts]}}

<article>
{article}
</article>

<facts>
{facts}
</facts>"""


def supported(f: Facts, article: str) -> list[int]:
    listing = "\n".join(f"{i}. {x}" for i, x in enumerate(f.facts, 1))
    raw = claude(SUPPORTED.format(article=article, facts=listing), model="sonnet")
    nums = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))["supported"]
    return sorted({int(n) - 1 for n in nums if 1 <= int(n) <= len(f.facts)})


def specific(f: Facts) -> list[int]:
    listing = "\n".join(f"{i}. {x}" for i, x in enumerate(f.facts, 1))
    raw = claude(SPECIFIC.format(facts=listing), model="sonnet")
    nums = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))["specific"]
    return sorted({int(n) - 1 for n in nums if 1 <= int(n) <= len(f.facts)})


def prompts():
    per_fact = json.loads((FACTS / "meta.json").read_text())["median_words_per_fact"]
    src = _sources()
    ids = [f"{i:04d}" for i in NUMS]
    with ThreadPoolExecutor(4) as ex:
        facts = list(ex.map(lambda n: extract(src[f"a{n}"]), ids))
        oracle = list(ex.map(lambda p: supported(p[0], src[f"h{p[1]}"]), zip(facts, ids)))
        keep = list(ex.map(specific, facts))
    rows, stats = [], []
    for n, f, k, o in zip(ids, facts, keep, oracle):
        rnd = sorted(random.Random(f"G{n}").sample(range(len(f.facts)), len(k)))
        stats.append({"id": f"a{n}", "ai_facts": len(f.facts), "specific": len(k), "oracle_overlap": len(o)})
        if len(k) < 9:
            continue
        for cell, idx in (("F", k), ("G", rnd)):
            sub = Facts(f.topic, [f.facts[i] for i in idx])
            words = min(MAX_WORDS, len(sub.facts) * per_fact)
            rows.append({"id": f"{cell}_a{n}", "cell": cell, "source": f"a{n}",
                         "prompt": facts_prompt(sub, words, f"a{n}"), "target_words": int(round(words, -1)),
                         "max_new_tokens": int(words * 1.3 * 1.5) + 64, "n_facts": len(sub.facts)})
    PROMPTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    OUT.write_text(json.dumps({"selection": stats}, indent=1))
    print(json.dumps(stats))


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in GENS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {c: {v: sum(verdicts[i] == v for i in ids if i[0] == c) for v in ("AI", "Mixed", "Human")} for c in "FG"}
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    prompts() if sys.argv[1] == "prompts" else record(sys.argv[2:])
