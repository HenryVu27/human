"""B24: full length with cited human sources. Does two-thirds retrieved human content read Human?

Henry chose this route on 2026-11-05 (report, "Where this stands"). B9: with two-thirds of the facts
from the human article the draft's topic came from, pieces read Human 7 of 10 and AI 0 at full
length (cell S2). That source was an oracle; a humanizer has no human original. Here the human
facts come from sources found for the draft's topic, cited, and the draft keeps a third of the
content. B14 on the same drafts reads 7 Human, 3 Mixed, but at about 40% of the length.

Fixed before any B24 text exists (2026-11-05, committed before the sources step runs):
- Drafts a0610 to a0619 (paired with B14 cell B, B18 cell W, B20 and the blind read). Their human
  originals are not on Wikipedia, so no source can be the oracle.
- Sources: Sonnet names 5 English Wikipedia articles a writer would read for the draft's topic. Each
  is read as its last revision before 2022-01-01 (humanizer.data.wiki; redirects followed; a title
  with no such revision falls back to the top search hit for it). The first 3 that are distinct and
  have at least 300 words of body text are kept, each cut to its first 1,500 words of whole
  paragraphs. The revision permalink is the citation.
- Facts: n = round(T / 17.87) (T = B12's target, the draft's length capped at 1,300; 17.87 is the
  training corpus's median words per fact, as in B5 and B9). n_d = round(n / 3) draft facts: its
  specific facts first (evenly spaced if more than n_d), then others at random (seed "b24<id>").
  n - n_d source facts: each source's FACTS extraction, from which Sonnet chooses facts that belong
  in an article on the draft's topic, add to the draft facts without repeating or contradicting
  them, and spread across the sources. Shuffled together by facts_prompt; topic is the draft's.
- Writer: the pool writer (models/lora-13b-pool-mlx) on the Mac, Guard on with the draft and the 3
  source texts as allowed text, seeds 0 to 3, B12's token budget.
- Each sample: B11 prune against the draft plus sources, then template repeats deleted
  (humanizer.checks.repeats; B23 found a third of raw words are repeats), then B13 cleanup. The
  sample with the most supported claims (claim check against draft plus sources) is kept, as in B14.
- Checks: length against T, claim support, coverage of the draft's facts, quality against the
  human cut, and Sonnet's attribution of every sentence to draft, source, both, or neither (the
  measured human-sourced share). Each kept text gets a cited version (results/b24_cited/) with a
  source number after every sentence attributed to a source and a list of permalinks.
- Pangram: all 10 bodies, without citation markers or the source list (cell R). Nothing above is
  changed after the scan.
Prediction: R reads like B9 S2 (6 or more of 10 Human, at most 1 AI) at 70% or more of T. If it reads
like B14 at full length, cited human sources solve the length problem. If AI verdicts rise, the
draft's third carries its plan even when outnumbered, unlike in B9.

Usage:
  uv run python experiments/b24_cited.py sources
  uv run python experiments/b24_cited.py prompts
  for s in 0 1 2 3: uv run python experiments/gen_mlx.py results/b24_prompts.jsonl results/b24_gen_s$s.jsonl --guard --adapter models/lora-13b-pool-mlx --seed $s
  uv run python experiments/b24_cited.py pick
  uv run python experiments/b24_cited.py record R_a0610=AI ...
"""

import json
import random
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.quality import quality_pair
from humanizer.checks.repeats import template_repeats
from humanizer.data import wiki
from humanizer.data.facts import OUT as FACTS_DIR, Facts, extract, facts_prompt
from humanizer.llm import claude

sys.path.insert(0, str(ROOT / "experiments"))
from b6_selection import specific  # noqa: E402
from b11_prune import _units, prune_one  # noqa: E402
from b12_replicate import _drafts  # noqa: E402
from b13_cleanup import clean_one  # noqa: E402
from b18_resample import _coverage, _first_json  # noqa: E402
from judge_calibrate import _cut  # noqa: E402

IDS = [f"a{n:04d}" for n in range(610, 620)]
N_TITLES, N_SOURCES, SOURCE_WORDS, MIN_WORDS, SEEDS = 5, 3, 1500, 300, (0, 1, 2, 3)
SOURCES = ROOT / "results" / "b24_sources.jsonl"
PROMPTS = ROOT / "results" / "b24_prompts.jsonl"
TEXTS = ROOT / "results" / "b24_texts.jsonl"
CITED = ROOT / "results" / "b24_cited"
OUT = ROOT / "results" / "b24_cited.json"

TITLES = """Below is the topic of an article and some of its facts. Name {n} English Wikipedia articles a careful writer would read as sources for it, most useful first: real article titles, the article on the subject itself before broader ones.

Return only JSON: {{"titles": ["...", ...]}}

Topic: {topic}
Facts:
{facts}"""

CHOOSE = """Below is the topic of an article, the facts it already has, and a numbered list of facts from reference articles. Choose {k} reference facts that belong in the article: on its topic, adding to the facts it has rather than repeating them, never contradicting them, and spread across the reference articles.

Return only JSON: {{"chosen": [numbers]}}

Topic: {topic}

<facts it has>
{have}
</facts it has>

<reference facts>
{pool}
</reference facts>"""

ATTRIBUTE = """Below are a draft, numbered reference articles, and the numbered sentences of an article written from them. For each sentence, say where its content comes from: D the draft only; R1, R2 or R3 a reference article (the main one if several); B both the draft and a reference article; W neither (the writer's own framing, or a claim no source makes).

Return only JSON: {{"labels": {{"1": "D", "2": "R2", ...}}}}

<draft>
{draft}
</draft>

{refs}

<sentences>
{sentences}
</sentences>"""


def _lead(paras: list[str], n: int) -> str:
    out, words = [], 0
    for p in paras:
        if words >= n:
            break
        out.append(p)
        words += len(p.split())
    return "\n".join(out)


def find_sources(key: str, draft: str) -> dict:
    f = extract(draft)
    obj = _first_json(claude(TITLES.format(n=N_TITLES, topic=f.topic, facts="\n".join(f"- {x}" for x in f.facts[:12])),
                             model="sonnet"))
    titles = [str(t) for t in obj.get("titles", [])] if isinstance(obj, dict) else []
    kept, seen = [], set()
    for t in titles:
        rev = wiki.revision(t) or next((r for r in map(wiki.revision, wiki.search(t, 1)) if r), None)
        if not rev or rev["revid"] in seen:
            continue
        paras = wiki.paragraphs(rev["revid"])
        text = _lead(paras, SOURCE_WORDS)
        if len(text.split()) < MIN_WORDS or "may refer to" in text[:400]:
            continue
        seen.add(rev["revid"])
        kept.append(rev | {"asked": t, "text": text})
        if len(kept) == N_SOURCES:
            break
    return {"id": key, "topic": f.topic, "titles": titles, "sources": kept}


def sources():
    drafts = _drafts()
    with ThreadPoolExecutor(4) as ex:
        rows = list(ex.map(lambda k: find_sources(k, drafts[k]), IDS))
    SOURCES.write_text("".join(json.dumps(r) + "\n" for r in rows))
    for r in rows:
        print(r["id"], r["topic"][:60], "|", [s["title"] for s in r["sources"]], [len(s["text"].split()) for s in r["sources"]])


def _draft_items(f: Facts, spec: list[int], n_d: int, key: str) -> list[str]:
    if len(spec) >= n_d:
        return [f.facts[spec[i * len(spec) // n_d]] for i in range(n_d)]
    rest = [x for i, x in enumerate(f.facts) if i not in set(spec)]
    return [f.facts[i] for i in spec] + random.Random(f"b24{key}").sample(rest, min(len(rest), n_d - len(spec)))


def build_prompt(row: dict, draft: str, target: int, per_fact: float) -> dict:
    key = row["id"]
    f = extract(draft)
    n = round(target / per_fact)
    n_d = round(n / 3)
    have = _draft_items(f, specific(f), n_d, key)
    pool = [(j, x) for j, s in enumerate(row["sources"]) for x in extract(s["text"]).facts]
    listing = "\n".join(f"{i}. [R{j + 1}] {x}" for i, (j, x) in enumerate(pool, 1))
    obj = _first_json(claude(CHOOSE.format(k=n - n_d, topic=f.topic, have="\n".join(f"- {x}" for x in have), pool=listing),
                             model="sonnet"))
    nums = [int(i) for i in obj.get("chosen", []) if str(i).isdigit()] if isinstance(obj, dict) else []
    chosen = [pool[i - 1] for i in dict.fromkeys(nums) if 1 <= i <= len(pool)][:n - n_d]
    items = have + [x for _, x in chosen]
    allowed = draft + "\n\n" + "\n\n".join(s["text"] for s in row["sources"])
    return {"id": f"R_{key}", "source": key, "prompt": facts_prompt(Facts(f.topic, items), target, f"b24{key}"),
            "allowed_text": allowed, "target_words": target, "max_new_tokens": int(target * 1.3 * 1.5) + 64,
            "n_facts": len(items), "n_draft": len(have), "n_source": len(chosen),
            "source_facts_per_ref": [sum(j == r for j, _ in chosen) for r in range(len(row["sources"]))]}


def prompts():
    drafts = _drafts()
    per_fact = json.loads((FACTS_DIR / "meta.json").read_text())["median_words_per_fact"]
    target = {r["source"]: r["target_words"] for r in map(json.loads, (ROOT / "results" / "b12_prompts.jsonl").open())}
    rows = [json.loads(line) for line in SOURCES.open()]
    with ThreadPoolExecutor(4) as ex:
        out = list(ex.map(lambda r: build_prompt(r, drafts[r["id"]], target[r["id"]], per_fact), rows))
    PROMPTS.write_text("".join(json.dumps(r) + "\n" for r in out))
    for r in out:
        print(r["id"], r["target_words"], "words;", r["n_draft"], "draft +", r["n_source"], "source facts", r["source_facts_per_ref"])


def _drop_repeats(text: str) -> str:
    units = _units(text)
    bad = template_repeats([s for _, s in units])
    paras = {}
    for i, (p, s) in enumerate(units):
        if i not in bad:
            paras.setdefault(p, []).append(s)
    return "\n".join(" ".join(v) for _, v in sorted(paras.items()))


def _refs(row: dict) -> str:
    return "\n\n".join(f'<reference R{j}: {s["title"]}>\n{s["text"]}\n</reference R{j}>' for j, s in enumerate(row["sources"], 1))


def attribute(draft: str, row: dict, text: str) -> list[tuple[str, str]]:
    sents = [s for _, s in _units(text)]
    listing = "\n".join(f"{i}. {s}" for i, s in enumerate(sents, 1))
    obj = _first_json(claude(ATTRIBUTE.format(draft=draft, refs=_refs(row), sentences=listing), model="sonnet"))
    labels = obj.get("labels", {}) if isinstance(obj, dict) else {}
    return [(s, str(labels.get(str(i), "?")).upper()) for i, s in enumerate(sents, 1)]


def _cited(text: str, labels: list[tuple[str, str]], row: dict) -> str:
    """The text with a source number after each sentence attributed to one source, then the sources."""
    paras = {}
    for (p, s), (_, lab) in zip(_units(text), labels):
        paras.setdefault(p, []).append(s + (f" [{lab[1:]}]" if re.fullmatch(r"R\d", lab) else ""))
    body = "\n\n".join(" ".join(v) for _, v in sorted(paras.items()))
    refs = "\n".join(f"{j}. {s['title']}, Wikipedia, revision of {s['timestamp'][:10]}: {s['url']}"
                     for j, s in enumerate(row["sources"], 1))
    return f"{body}\n\nSources\n{refs}\n"


def pick():
    drafts = _drafts()
    src = {r["id"]: r for r in map(json.loads, SOURCES.open())}
    prm = {r["source"]: r for r in map(json.loads, PROMPTS.open())}
    human = [json.loads(line)["text"] for line in (ROOT / "data" / "human.jsonl").open()]
    gens = [json.loads(line) for s in SEEDS for line in (ROOT / "results" / f"b24_gen_s{s}.jsonl").open()]

    def one(g):
        key = g["id"][2:]
        material = prm[key]["allowed_text"]
        pruned, _ = prune_one(g["text"], material)
        text, _ = clean_one(_drop_repeats(pruned))
        cc = claim_check(material, text)
        return key, {"seed": g["seed"], "text": text, "raw_words": g["words"],
                     "claims_entailed": cc["claims_entailed"], "claims_total": cc["claims_total"]}

    samples = {k: [] for k in IDS}
    with ThreadPoolExecutor(4) as ex:
        for key, r in ex.map(one, gens):
            samples[key].append(r)
    CITED.mkdir(exist_ok=True)

    def finish(key):
        cands = samples[key]
        best = max(cands, key=lambda c: (c["claims_entailed"], c["claims_entailed"] / max(1, c["claims_total"])))
        labels = attribute(drafts[key], src[key], best["text"])
        words = {t: sum(len(s.split()) for s, lab in labels if (lab[0] if lab else "?") == t) for t in "DRBW?"}
        n_words = len(best["text"].split())
        (CITED / f"R_{key}.md").write_text(_cited(best["text"], labels, src[key]))
        return {"id": f"R_{key}", "seed": best["seed"], "text": best["text"], "words": n_words,
                "target_words": prm[key]["target_words"], "raw_words": best["raw_words"],
                "claims_entailed": best["claims_entailed"], "claims_total": best["claims_total"],
                "attribution_words": words, "source_share": words["R"] / max(1, n_words),
                "draft_share": (words["D"] + words["B"]) / max(1, n_words),
                "coverage": _coverage(drafts[key], best["text"]),
                "quality_vs_human_cut": quality_pair(_cut(human[int(key[1:])], n_words), best["text"]),
                "candidates": [{k: c[k] for k in ("seed", "claims_entailed", "claims_total", "raw_words")}
                               | {"words": len(c["text"].split())} for c in cands]}

    with ThreadPoolExecutor(4) as ex:
        rows = list(ex.map(finish, IDS))
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    summary = {"texts": len(rows), "words": statistics.mean(r["words"] for r in rows),
               "length_ratio": statistics.mean(r["words"] / r["target_words"] for r in rows),
               "claim_support": statistics.mean(r["claims_entailed"] / max(1, r["claims_total"]) for r in rows),
               "source_share": statistics.mean(r["source_share"] for r in rows),
               "draft_share": statistics.mean(r["draft_share"] for r in rows),
               "coverage": statistics.mean(r["coverage"] for r in rows),
               "quality_vs_human_cut": statistics.mean(r["quality_vs_human_cut"] for r in rows)}
    OUT.write_text(json.dumps({"checks": summary}, indent=1))
    for r in rows:
        print(r["id"], r["words"], "/", r["target_words"], f"source {r['source_share']:.2f} draft {r['draft_share']:.2f}",
              f"claims {r['claims_entailed']}/{r['claims_total']}")
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
    {"sources": sources, "prompts": prompts, "pick": pick}.get(sys.argv[1], lambda: record(sys.argv[2:]))()
