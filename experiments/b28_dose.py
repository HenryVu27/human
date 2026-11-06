"""B28: how sparse can a blogger's notes be? Sonnet against the voice writer, on fresh essays.

B25 and B27: with notes as dense as a finished essay (4 to 8 per 100 words), Sonnet's post reads Mixed
(11 of 13) once the essay's wording is reworded out. A blogger's real prompt is far sparser. B5 found the
local writer reads Human from reworded human facts (7 of 10, FineWeb). This measures, at three note
densities, what each writer does with the same notes, and what a humanizer can do when it has only the
AI post (no notes). Pangram is Professional now (15,000 credits), so every cell is scanned.

Fixed before any B28 text exists (2026-11-05 18:28):
- Essays: data/essays.jsonl split "bench2": 20 essays (2 per writer, 10 writers), 500 to 1,500 words,
  published before 2022-11-30, never in the voice writer's training set.
- Notes: B25's NOTES prompt, then B27's rewording (B5's REWORD, chunks of 20). Doses 100%, 50%, 25%: a
  random order of the notes per essay (seed "b28<id>"); a dose keeps the first round(d * n) of that
  order, shown in the notes' own order. The doses are nested (25% within 50% within 100%).
- S100, S50, S25: Sonnet writes the post from the dose notes with B25's DRAFT prompt (title, first
  person, the essay's length T), scanned as plain text.
- L100, L50, L25: the voice writer (models/lora-13b-essaypool-mlx, B26) from the same dose notes: facts
  prompt at T (capped at 1,300 words), Guard and prune over the dose notes, template repeats dropped,
  cleanup, seeds 0 and 1 (two, not four: Mac time), the sample with the most supported claims kept.
- R: the humanizer with only the AI post. Sonnet extracts every fact of S100 (FACTS prompt), they are
  reworded as above, and the voice writer writes from them at T, Guard and prune against the S100 post,
  then as L.
- H: the 20 essays (calibration).
- Amended 18:31, before any B28 text exists: an essay whose notes Sonnet refuses is dropped and reported.
  Hanson's "Variolation Test Design" (about deliberate COVID infection) was refused by a safety
  classifier, so B28 has 19 essays.
- Amended 19:46, before any L or R text exists (Henry offered the idle PC): seed 0 is generated on the PC
  (experiments/gpu/gen13b_guard.py: transformers, the same adapter in its trained PEFT form, the same
  Guard file and capitalized-word list, checked equal, the same sampling; bf16 key-value cache where the
  Mac quantizes it to 4 bits), seed 1 on the Mac with gen_mlx. Every prompt's pick sees one sample from
  each machine, so no cell leans on one machine. Rows carry "machine": "pc" for the PC samples.
- Amended 20:46, still before any L or R text is picked or read: Henry needed the PC back after 27 of the
  76 seed-0 samples. The other 49 seed-0 samples and all seed-1 samples are generated on the Mac.
- Amended 22:41, before any seed-1 sample exists: Henry freed the PC. Seed 1 runs on both machines, the
  Mac in prompt order (gen_mlx into b28_gen_s1.jsonl) and the PC in reverse order (gen13b_guard into
  b28_gen_s1_pc.jsonl), and both stop once every prompt has a seed-1 sample. Where both wrote one, the
  Mac's is kept. Nothing reads the samples before the merge.
- Pangram on all 140 texts. Checks: length against T, claim support, copying from the essay (8-word
  runs), first person and sentence-length spread against the essay.
The writer was fixed before B26's scan; no Pangram result chooses it.
Predictions: H 19 or more of 20 Human. S at most 3 Human per dose, with AI rising as notes thin (S25 at
least 4 more AI than S100). L100 at least 12 of 20 Human; L falls with dose but beats S on Human count at
every dose. R reads Human less often than L100 (its facts include what Sonnet added). L's length falls
with dose, roughly 50%, 35% and 25% of T.

Usage:
  uv run python experiments/b28_dose.py notes       notes, rewording, doses (data/b28_bench.jsonl)
  uv run python experiments/b28_dose.py sonnet      S posts, and R's facts from S100
  uv run python experiments/b28_dose.py prompts     L and R prompts
  seed 0 on the PC: experiments/gpu/b28.cmd (copy b28_prompts.jsonl to C:/hgpu, fetch b28_gen_s0.jsonl back)
  uv run python experiments/gen_mlx.py results/b28_prompts.jsonl results/b28_gen_s1.jsonl --guard --adapter models/lora-13b-essaypool-mlx --seed 1
  uv run python experiments/b28_dose.py pick
  uv run python experiments/b28_dose.py scan_files DIR
  uv run python experiments/b28_dose.py record H_e1234abcd=Human ...
"""

import json
import random
import statistics
import sys
from pathlib import Path

from humanizer import ROOT
from humanizer.checks.copying import copied_share
from humanizer.data.essays import OUT as ESSAYS
from humanizer.data.facts import FACTS, Facts, parse_facts
from humanizer.llm import claude_many

sys.path.insert(0, str(ROOT / "experiments"))
import b25_blog  # noqa: E402
from b25_blog import DRAFT, NOTES, plain, voice  # noqa: E402
from b27_reworded import reword_all  # noqa: E402

BENCH = ROOT / "data" / "b28_bench.jsonl"
SONNET = ROOT / "data" / "b28_sonnet.jsonl"
PROMPTS = ROOT / "results" / "b28_prompts.jsonl"
TEXTS = ROOT / "results" / "b28_texts.jsonl"
OUT = ROOT / "results" / "b28_dose.json"
DOSES = {"100": 1.0, "50": 0.5, "25": 0.25}
CELLS = ("H", "S100", "S50", "S25", "L100", "L50", "L25", "R")


def _essays() -> list[dict]:
    return [r for r in map(json.loads, ESSAYS.open()) if r["split"] == "bench2"]


def dose(notes: list[str], key: str, d: float) -> list[str]:
    """The first round(d * n) notes of a fixed random order, shown in the notes' own order (nested doses)."""
    order = list(range(len(notes)))
    random.Random(f"b28{key}").shuffle(order)
    keep = sorted(order[:max(1, round(d * len(notes)))])
    return [notes[i] for i in keep]


def notes():
    essays, parsed = [], []
    for e, x in zip(_essays(), claude_many([NOTES.format(text=e["text"]) for e in _essays()], model="sonnet")):
        if x and "{" in x:
            essays.append(e)
            parsed.append(parse_facts(x))
        else:
            print("dropped, notes refused:", e["id"], e["author"], e["title"])
    raw, topics = [p.facts for p in parsed], [p.topic for p in parsed]
    reworded, kept = reword_all(raw)
    rows = [e | {"topic": t, "notes": n, "reworded": w, **{f"dose{k}": dose(w, e["id"], d) for k, d in DOSES.items()}}
            for e, t, n, w in zip(essays, topics, raw, reworded)]
    BENCH.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print("chunks not reworded:", kept)
    for r in rows:
        print(r["id"], r["author"][:16], r["words"], "words", len(r["notes"]), "notes",
              f"copied {copied_share(chr(10).join(r['notes']), r['text']):.2f} -> {copied_share(chr(10).join(r['reworded']), r['text']):.2f}")


def _bench() -> list[dict]:
    return [json.loads(line) for line in BENCH.open()]


def sonnet():
    rows = _bench()
    jobs = [(r, k) for r in rows for k in DOSES]
    posts = claude_many([DRAFT.format(title=r["title"], words=int(round(r["words"], -1)),
                                      notes="\n".join(f"- {x}" for x in r[f"dose{k}"])) for r, k in jobs], model="sonnet")
    out = {f"S{k}_{r['id']}": {"id": f"S{k}_{r['id']}", "source": r["id"], "cell": f"S{k}", "text": plain(p)}
           for (r, k), p in zip(jobs, posts)}
    s100 = [out[f"S100_{r['id']}"]["text"] for r in rows]
    facts = [parse_facts(x).facts for x in claude_many([FACTS.format(text=t) for t in s100], model="sonnet")]
    rf, kept = reword_all(facts)
    for r, f in zip(rows, rf):
        out[f"S100_{r['id']}"]["r_facts"] = f
    SONNET.write_text("".join(json.dumps(v) + "\n" for v in out.values()))
    print(len(out), "Sonnet posts; R facts chunks not reworded:", kept)


def prompts():
    rows = _bench()
    s = {x["id"]: x for x in map(json.loads, SONNET.open())}
    out = []
    for r in rows:
        for k in DOSES:
            n = r[f"dose{k}"]
            out.append(b25_blog._row(f"L{k}", r, Facts(r["topic"], n), "\n".join(n)))
        s100 = s[f"S100_{r['id']}"]
        out.append(b25_blog._row("R", r, Facts(r["topic"], s100["r_facts"]), s100["text"]))
    PROMPTS.write_text("".join(json.dumps(x) + "\n" for x in out))
    print(len(out), "prompts")


def pick():
    essays = {r["id"]: r for r in _bench()}
    b25_blog.pick("b28", PROMPTS, TEXTS, OUT, cells=("L100", "L50", "L25", "R"), seeds=(0, 1), essays=essays)
    s_checks = {}
    for x in map(json.loads, SONNET.open()):
        e = essays[x["source"]]
        s_checks[x["id"]] = {"words": len(x["text"].split()), "over_essay": len(x["text"].split()) / e["words"],
                             "copied_from_essay": copied_share(x["text"], e["text"]), "voice": voice(x["text"])}
    summary = {c: {"words": statistics.mean(v["words"] for k, v in s_checks.items() if k.startswith(c + "_")),
                   "copied_from_essay": statistics.mean(v["copied_from_essay"] for k, v in s_checks.items() if k.startswith(c + "_")),
                   **{m: statistics.mean(v["voice"][m] for k, v in s_checks.items() if k.startswith(c + "_"))
                      for m in ("first_person", "sentence_sd")}} for c in ("S100", "S50", "S25")}
    summary["H"] = {m: statistics.mean(voice(e["text"])[m] for e in essays.values()) for m in ("first_person", "sentence_sd")}
    prev = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(prev | {"sonnet_checks": summary, "sonnet_per_text": s_checks}, indent=1))
    print(json.dumps(summary, indent=1))


def scan_files(dest: str):
    d = Path(dest)
    d.mkdir(parents=True, exist_ok=True)
    for r in _bench():
        (d / f"H_{r['id']}.txt").write_text(r["text"])
    for x in map(json.loads, SONNET.open()):
        (d / f"{x['id']}.txt").write_text(x["text"])
    if TEXTS.exists():
        for x in map(json.loads, TEXTS.open()):
            (d / f"{x['id']}.txt").write_text(x["text"])


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    summary = {c: {v: sum(1 for k, x in verdicts.items() if k.split("_")[0] == c and x == v) for v in ("AI", "Mixed", "Human")}
               for c in CELLS}
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    pangram = out.get("pangram", {}) | verdicts
    OUT.write_text(json.dumps(out | {"pangram": pangram, "pangram_summary": {
        c: {v: sum(1 for k, x in pangram.items() if k.split("_")[0] == c and x == v) for v in ("AI", "Mixed", "Human")}
        for c in CELLS}}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "scan_files":
        scan_files(sys.argv[2])
    elif cmd == "record":
        record(sys.argv[2:])
    else:
        {"notes": notes, "sonnet": sonnet, "prompts": prompts, "pick": pick}[cmd]()
