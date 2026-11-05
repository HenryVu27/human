"""B25: the blog track. Does the humanizer work on personal blog essays, its real genre?

Every experiment through B24 drew its drafts from FineWeb pages (essay mills, SEO and health sites):
median 0 first-person words per 100, and 7% of pages above 1. The humanizer's use is a personal
blog post, and Henry asked for writing that sounds like a person (Paul Graham, Richard Sutton,
Fernando Borretti, economists). The bench is data/essays.jsonl, split "bench" (humanizer.data.essays):
13 writers, 2 essays each of 500 to 1,500 words, all published before 2022-11-30, chosen by url hash
before any text was read. Per writer, the essay first in hash order is the test set (scanned); the
second is the dev set (never scanned; for local checks, blind reads and later iteration).

A blogger who uses AI gives it their ideas and gets back a post. So for each essay:
- notes: Sonnet lists what the essay says (the FACTS prompt, first person kept where the writer
  speaks of themself): the writer's points, examples and specifics, none of its sentences or structure.
- draft (cell D): Sonnet writes the post from the notes, in their order, as a blogger would ask:
  "Write my blog post from these notes", title given, first person, the essay's length T.
The draft is the humanizer's input; the essay is the human the output should be as good as.

Cells on the 13 test essays, all scanned on Pangram (the held-out judge; it selects nothing):
- H: the essays themselves. Calibration: a writer whose own essay reads AI is reported, not dropped.
- D: the AI drafts. If 6 or more read Human, the bench has too little to humanize and P and N are
  not scanned.
- P: the current humanizer on the draft, B14's recipe: the draft's specific facts, pool writer
  (models/lora-13b-pool-mlx), seeds 0 to 3, Guard over the draft, prune against the draft, template
  repeats dropped, cleanup, the sample with the most supported claims kept.
- N: the notes route. The same writer from all of the notes (facts prompt at T, words capped at 1,300
  as in training), Guard over the notes, prune against the notes, then as P. It never sees the draft.
  In use this means the humanizer asks for what the blogger gave the AI.
Checks (local, not Pangram): length against T, claim support against the cell's material, first person
per 100 words against the essay's, sentence length spread (standard deviation, a burstiness measure),
quality_pair against the essay itself cut to the same length.
Prediction: H 12 or more of 13 Human. D 2 or fewer Human. P about B14's rate (half Human) at about 40%
of T. N 9 or more Human with at most 1 AI (B9: human-chosen facts read Human), at 50% or more of T.
Credits: about 125 (H) + 125 (D) + 50 (P) + 65 (N), of about 415 left after B24.
Amended 16:48, before any bench text exists: a P or N text under 150 words is not scanned (Pangram is
unreliable below that) and counts as not Human; essays have few numbers and names, so P's
specific-facts prompt may leave the writer little to keep.

Usage:
  uv run python -m humanizer.data.essays
  uv run python experiments/b25_blog.py bench      notes and drafts for test and dev (data/b25_bench.jsonl)
  uv run python experiments/b25_blog.py prompts    P and N prompts for the test set
  for s in 0 1 2 3: uv run python experiments/gen_mlx.py results/b25_prompts.jsonl results/b25_gen_s$s.jsonl --guard --adapter models/lora-13b-pool-mlx --seed $s
  uv run python experiments/b25_blog.py pick
  uv run python experiments/b25_blog.py record H_e1234abcd=Human ...
"""

import json
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.quality import quality_pair
from humanizer.data.essays import OUT as ESSAYS, _rank
from humanizer.data.facts import FACTS, Facts, extract, facts_prompt, parse_facts
from humanizer.data.lora import MAX_WORDS
from humanizer.llm import claude_many

sys.path.insert(0, str(ROOT / "experiments"))
from b6_selection import specific  # noqa: E402
from b11_prune import prune_one  # noqa: E402
from b13_cleanup import clean_one  # noqa: E402
from b24_cited import _drop_repeats  # noqa: E402
from judge_calibrate import _cut  # noqa: E402

BENCH = ROOT / "data" / "b25_bench.jsonl"  # notes and drafts stay with the essays, out of git
MANIFEST = ROOT / "results" / "b25_manifest.jsonl"
PROMPTS = ROOT / "results" / "b25_prompts.jsonl"
TEXTS = ROOT / "results" / "b25_texts.jsonl"
OUT = ROOT / "results" / "b25_blog.json"
SEEDS = (0, 1, 2, 3)
CONTEXT = 4096  # OLMo-2's window: prompt plus new tokens must fit

NOTES = FACTS.replace("- Add nothing", "- Where the writer speaks of themself, keep the first person (\"I started a company in 1995\").\n- Add nothing")
DRAFT = """Write my blog post from these notes. Title: "{title}". First person, about {words} words. Output only the post, in markdown.

Notes:
{notes}"""
FIRST = re.compile(r"\b(I|I'm|I've|I'd|I'll|me|my|mine|myself)\b")
SENT = re.compile(r"(?<=[.!?])\s+(?=[\"'(A-Z0-9])")


def _essays() -> list[dict]:
    """Bench essays with their split: per writer, first in hash order is test, second dev."""
    rows = [r for r in map(json.loads, ESSAYS.open()) if r["split"] == "bench"]
    out, seen = [], {}
    for r in sorted(rows, key=lambda r: _rank(r["url"])):
        seen[r["author"]] = seen.get(r["author"], 0) + 1
        out.append(r | {"split": "test" if seen[r["author"]] == 1 else "dev"})
    return out


def bench():
    essays = _essays()
    notes = [parse_facts(raw) for raw in claude_many([NOTES.format(text=e["text"]) for e in essays], model="sonnet")]
    drafts = claude_many([DRAFT.format(title=e["title"], words=int(round(e["words"], -1)),
                                       notes="\n".join(f"- {x}" for x in n.facts)) for e, n in zip(essays, notes)],
                         model="sonnet")
    rows = [e | {"topic": n.topic, "notes": n.facts, "draft": d.strip(), "draft_words": len(d.split())}
            for e, n, d in zip(essays, notes, drafts)]
    BENCH.write_text("".join(json.dumps(r) + "\n" for r in rows))
    MANIFEST.write_text("".join(json.dumps({k: r[k] for k in ("id", "author", "title", "url", "date", "words", "split",
                                                               "draft_words")} | {"n_notes": len(r["notes"])}) + "\n"
                                for r in rows))
    for r in rows:
        print(r["split"], r["id"], r["author"][:16], r["words"], "words", len(r["notes"]), "notes", r["draft_words"], "draft")


def _bench(split: str = "test") -> list[dict]:
    return [r for r in map(json.loads, BENCH.open()) if r["split"] == split]


def _row(cell: str, r: dict, f: Facts, material: str) -> dict:
    words = min(MAX_WORDS, r["words"])
    prompt = facts_prompt(f, words, f"b25{r['id']}")
    room = CONTEXT - int(len(prompt.split()) * 1.5) - 32
    return {"id": f"{cell}_{r['id']}", "source": r["id"], "cell": cell, "prompt": prompt, "allowed_text": material,
            "target_words": int(round(words, -1)), "max_new_tokens": min(int(words * 1.3 * 1.5) + 64, room),
            "n_facts": len(f.facts)}


def prompts():
    rows = _bench()
    with ThreadPoolExecutor(4) as ex:
        facts = list(ex.map(lambda r: extract(r["draft"]), rows))
        keep = list(ex.map(specific, facts))
    out = []
    for r, f, k in zip(rows, facts, keep):
        out.append(_row("P", r, Facts(f.topic, [f.facts[j] for j in k]), r["draft"]))
        out.append(_row("N", r, Facts(r["topic"], r["notes"]), "\n".join(r["notes"])))
    PROMPTS.write_text("".join(json.dumps(x) + "\n" for x in out))
    for x in out:
        print(x["id"], x["n_facts"], "facts", x["target_words"], "words", x["max_new_tokens"], "max tokens")


def voice(text: str) -> dict:
    sents = [s for s in SENT.split(" ".join(text.split())) if s]
    lens = [len(s.split()) for s in sents]
    return {"first_person": 100 * len(FIRST.findall(text)) / max(1, len(text.split())),
            "sentence_mean": statistics.mean(lens) if lens else 0.0,
            "sentence_sd": statistics.pstdev(lens) if len(lens) > 1 else 0.0}


def pick(prefix: str = "b25", prompts=PROMPTS, texts=TEXTS, out=OUT, cells: tuple = ("P", "N")):
    """Prune, drop repeats, clean and claim-check every sample; keep the one with the most supported claims."""
    bench_rows = {r["id"]: r for r in _bench()}
    prm = {p["id"]: p for p in map(json.loads, prompts.open())}
    gens = [json.loads(line) for s in SEEDS for line in (ROOT / "results" / f"{prefix}_gen_s{s}.jsonl").open()]

    def one(g):
        material = prm[g["id"]]["allowed_text"]
        pruned, _ = prune_one(g["text"], material)
        text, _ = clean_one(_drop_repeats(pruned))
        cc = claim_check(material, text)
        return g["id"], {"seed": g["seed"], "text": text, "raw_words": g["words"], "hit_eos": g.get("hit_eos"),
                         "claims_entailed": cc["claims_entailed"], "claims_total": cc["claims_total"]}

    samples = {k: [] for k in prm}
    with ThreadPoolExecutor(4) as ex:
        for key, s in ex.map(one, gens):
            samples[key].append(s)

    def finish(key):
        best = max(samples[key], key=lambda c: (c["claims_entailed"], c["claims_entailed"] / max(1, c["claims_total"])))
        essay = bench_rows[prm[key]["source"]]
        n = len(best["text"].split())
        return {"id": key, "cell": prm[key]["cell"], "source": essay["id"], "author": essay["author"], "seed": best["seed"],
                "text": best["text"], "words": n, "target_words": prm[key]["target_words"], "raw_words": best["raw_words"],
                "claims_entailed": best["claims_entailed"], "claims_total": best["claims_total"],
                "voice": voice(best["text"]), "essay_voice": voice(essay["text"]),
                "quality_vs_essay": quality_pair(_cut(essay["text"], n), best["text"]),
                "candidates": [{k: c[k] for k in ("seed", "claims_entailed", "claims_total", "raw_words", "hit_eos")}
                               | {"words": len(c["text"].split())} for c in samples[key]]}

    with ThreadPoolExecutor(4) as ex:
        rows = list(ex.map(finish, list(prm)))
    texts.write_text("".join(json.dumps(r) + "\n" for r in rows))
    summary = {}
    for cell in cells:
        cr = [r for r in rows if r["cell"] == cell]
        summary[cell] = {"texts": len(cr), "words": statistics.mean(r["words"] for r in cr),
                         "length_ratio": statistics.mean(r["words"] / r["target_words"] for r in cr),
                         "claim_support": statistics.mean(r["claims_entailed"] / max(1, r["claims_total"]) for r in cr),
                         "quality_vs_essay": statistics.mean(r["quality_vs_essay"] for r in cr),
                         **{k: statistics.mean(r["voice"][k] for r in cr) for k in ("first_person", "sentence_sd")}}
    b = list(bench_rows.values())
    for cell, key in (("H", "text"), ("D", "draft")):
        summary[cell] = {"texts": len(b), "words": statistics.mean(len(r[key].split()) for r in b),
                         **{k: statistics.mean(voice(r[key])[k] for r in b) for k in ("first_person", "sentence_sd")}}
    out.write_text(json.dumps({"checks": summary}, indent=1))
    print(json.dumps(summary, indent=1))


def scan_files(dest: str):
    """Plain bodies for the Pangram upload: H (essays), D (drafts), P and N (picked texts), one .txt each."""
    from pathlib import Path
    d = Path(dest)
    d.mkdir(parents=True, exist_ok=True)
    for r in _bench():
        (d / f"H_{r['id']}.txt").write_text(r["text"])
        (d / f"D_{r['id']}.txt").write_text(r["draft"])
    if TEXTS.exists():
        for r in map(json.loads, TEXTS.open()):
            (d / f"{r['id']}.txt").write_text(r["text"])


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    summary = {cell: {v: sum(1 for k, x in verdicts.items() if k.startswith(cell + "_") and x == v)
                      for v in ("AI", "Mixed", "Human")} for cell in "HDPN"}
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"bench": bench, "prompts": prompts, "pick": pick}.get(cmd, lambda: None)()
    if cmd == "scan_files":
        scan_files(sys.argv[2])
    elif cmd == "record":
        record(sys.argv[2:])
