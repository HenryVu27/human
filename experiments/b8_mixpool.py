"""B8: teach the writer to drop AI-typical facts.

Pangram 4 labels as AI exactly what an LLM writes when given only a human document's topic
(its "synthetic mirrors"), and B5 showed the AI's choice of facts is what carries the signal.
Our corpus has the same thing: 593 AI mirrors (data/ai.jsonl), one per training article.

Mixed-pool writer: the 13B adapter trained on prompts whose fact list mixes a random 20 to 60
percent of the human article's facts with facts from the AI mirror of the same topic (shuffled,
same format as data/facts), and the human article as the target. To predict the article it has
to use the human facts and ignore the mirror's, so it learns which facts a human writer would
not state. Rows without a mirror keep a human-only pool (as data/pool).

Usage:
  uv run python experiments/b8_mixpool.py extract   facts of the 593 mirrors (Sonnet, cached)
  uv run python experiments/b8_mixpool.py data      -> data/mixpool/{train,valid}.jsonl
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


if __name__ == "__main__":
    {"extract": extract, "data": data}[sys.argv[1]]()
