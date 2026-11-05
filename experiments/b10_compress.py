"""B10: does compressing an AI draft fall into Pangram's blind spot?

Pangram 4 builds its AI training text only from outputs longer than their input (summaries of
human input count as human), and its red team's one named bypass was an LLM writing short notes
from far more context than it output. So: an instruct model condenses each AI draft, adding
nothing, with no instruction to sound human. Dev a0600 to a0609 (fixed before scanning), Sonnet:

  K1: condensed to about 25 percent of the draft's words
  K2: condensed to about 50 percent

Baseline for the same drafts: the drafts themselves read AI (B3 to B5 premise; a0601 scored
AI 100% in the first probe). If K1 reads Human and K2 does not, compression ratio is a lever.

Usage:
  uv run python experiments/b10_compress.py texts
  uv run python experiments/b10_compress.py record K1_a0600=AI ...
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.llm import claude

sys.path.insert(0, str(ROOT / "experiments"))
from b5_matched import _sources  # noqa: E402

TEXTS = ROOT / "results" / "b10_texts.jsonl"
OUT = ROOT / "results" / "b10_compress.json"
RATIOS = {"K1": 0.25, "K2": 0.5}

CONDENSE = """Condense the article below into a shorter article of about {n} words for the same readers.
Keep only what the article says; add no facts, names, numbers or claims of your own. Return only the new article.

<article>
{text}
</article>"""


def texts():
    src = _sources()
    jobs = [(c, f"a{i:04d}") for c in RATIOS for i in range(600, 610)]

    def one(job):
        c, key = job
        d = src[key]
        n = int(round(len(d.split()) * RATIOS[c], -1))
        t = claude(CONDENSE.format(n=n, text=d), model="sonnet").strip()
        return {"id": f"{c}_{key}", "cell": c, "source": key, "target_words": n, "text": t, "words": len(t.split()),
                "draft_words": len(d.split())}

    with ThreadPoolExecutor(4) as ex:
        rows = list(ex.map(one, jobs))
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print([(r["id"], r["draft_words"], r["words"]) for r in rows])


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {c: {v: sum(verdicts[i] == v for i in ids if i.startswith(c)) for v in ("AI", "Mixed", "Human")} for c in RATIOS}
    OUT.write_text(json.dumps({"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    texts() if sys.argv[1] == "texts" else record(sys.argv[2:])
