"""B15: the B14 pipeline on Henry's own AI-written post, section by section.

Post: ~/personal/blog/series/ai-engineering/part1.html ("context engineering"), fixed before any
generation. Each h2 section's prose (paragraphs, list items, h3 and blockquotes; code, tables and
figures left out) is one draft. Skipped: "Contents", "References" and the series navigation.
Cells: O = the original section (expected AI; Henry says the post is AI-rewritten), B = the B14
pipeline (specific facts, pool writer, 4 seeds, prune, clean, keep the most supported claims).
Henry reads both blind for quality; Pangram scans both.

Usage:
  uv run python experiments/b15_blog.py prompts
  for s in 0 1 2 3: uv run python experiments/gen_mlx.py results/b15_prompts.jsonl results/b15_gen_s$s.jsonl --guard --adapter models/lora-13b-pool-mlx --seed $s
  uv run python experiments/b15_blog.py pick
  uv run python experiments/b15_blog.py record O_s1=AI ...
"""

import html
import json
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.data.facts import Facts, extract, facts_prompt
from humanizer.data.lora import MAX_WORDS

sys.path.insert(0, str(ROOT / "experiments"))
from b6_selection import specific  # noqa: E402
from b11_prune import prune_one  # noqa: E402
from b13_cleanup import clean_one  # noqa: E402

POST = Path.home() / "personal" / "blog" / "series" / "ai-engineering" / "part1.html"
SKIP = {"Contents", "References", "AI Engineering"}
SECTIONS = ROOT / "results" / "b15_sections.jsonl"
PROMPTS = ROOT / "results" / "b15_prompts.jsonl"
TEXTS = ROOT / "results" / "b15_texts.jsonl"
OUT = ROOT / "results" / "b15_blog.json"


def sections() -> list[dict]:
    s = POST.read_text()
    parts = re.split(r"(<h2[^>]*>.*?</h2>)", s)
    out = []
    for i in range(1, len(parts), 2):
        title = html.unescape(re.sub("<[^>]+>", "", parts[i])).strip()
        title = re.sub(r"^\d+", "", title).strip()
        if title in SKIP:
            continue
        body = re.sub(r"(?s)<(script|style|pre|code|nav|header|footer|table|figure|svg)[^>]*>.*?</\1>", "", parts[i + 1])
        paras = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", p))).strip()
                 for p in re.findall(r"(?s)<(?:p|li|h3|blockquote)[^>]*>(.*?)</(?:p|li|h3|blockquote)>", body)]
        text = "\n".join(p for p in paras if p)
        out.append({"id": f"s{len(out) + 1}", "title": title, "text": text, "words": len(text.split())})
    return out


def prompts():
    secs = sections()
    SECTIONS.write_text("".join(json.dumps(r) + "\n" for r in secs))
    with ThreadPoolExecutor(4) as ex:
        facts = list(ex.map(lambda r: extract(r["text"]), secs))
        keep = list(ex.map(specific, facts))
    rows = []
    for r, f, k in zip(secs, facts, keep):
        spec = Facts(f.topic, [f.facts[j] for j in k])
        words = min(MAX_WORDS, r["words"])
        rows.append({"id": f"B_{r['id']}", "source": r["id"], "allowed_text": r["text"],
                     "prompt": facts_prompt(spec, words, r["id"]), "target_words": int(round(words, -1)),
                     "max_new_tokens": int(words * 1.3 * 1.5) + 64, "n_facts": len(spec.facts), "n_facts_all": len(f.facts)})
    PROMPTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print([(r["id"], r["n_facts"], r["n_facts_all"], r["target_words"]) for r in rows])


def pick(prefix: str = "b15", cell: str = "B"):
    secs = {r["id"]: r for r in map(json.loads, SECTIONS.open())}
    gens = [(s, json.loads(line)) for s in (0, 1, 2, 3) for line in (ROOT / "results" / f"{prefix}_gen_s{s}.jsonl").open()]

    def one(item):
        s, g = item
        draft = secs[g["id"][2:]]["text"]
        pruned, _ = prune_one(g["text"], draft)
        text, _ = clean_one(pruned)
        cc = claim_check(draft, text)
        return g["id"][2:], {"seed": s, "text": text, "claims_entailed": cc["claims_entailed"], "claims_total": cc["claims_total"]}

    cands = {}
    with ThreadPoolExecutor(2) as ex:
        for key, r in ex.map(one, gens):
            cands.setdefault(key, []).append(r)
    rows = []
    for key, sec in secs.items():
        best = max(cands[key], key=lambda c: (c["claims_entailed"], c["claims_entailed"] / max(1, c["claims_total"])))
        if cell == "B":
            rows.append({"id": f"O_{key}", "title": sec["title"], "text": sec["text"], "words": sec["words"]})
        rows.append({"id": f"{cell}_{key}", "title": sec["title"], "seed": best["seed"], "text": best["text"],
                     "words": len(best["text"].split()), "claims_entailed": best["claims_entailed"],
                     "claims_total": best["claims_total"]})
    (ROOT / "results" / f"{prefix}_texts.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    b = [r for r in rows if r["id"][0] == cell]
    summary = {"sections": len(b), "words_original": sum(r["words"] for r in secs.values()),
               "words_output": sum(r["words"] for r in b),
               "claim_support": statistics.mean(r["claims_entailed"] / max(1, r["claims_total"]) for r in b)}
    (ROOT / "results" / f"{prefix}_blog.json").write_text(json.dumps({"checks": summary}, indent=1))
    print(json.dumps(summary, indent=1))


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {c: {v: sum(verdicts[i] == v for i in ids if i[0] == c) for v in ("AI", "Mixed", "Human")} for c in "OB"}
    out = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    step = sys.argv[1]
    {"prompts": prompts, "pick": pick}.get(step, lambda: record(sys.argv[2:]))()
