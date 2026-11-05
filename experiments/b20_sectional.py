"""B20: at B14's fact density but full length, written section by section, does B14 hold?

B14 (pool writer, the draft's ~6 specific facts, best of 4, prune) reads Human 13 of 20, but at about
40% of the draft's length. B18's first two pieces show why: once the writer has used its facts, every
new paragraph states something the draft does not, the check deletes it, and the loop stops at 15 to
25% of the target. Putting all the facts in one prompt is not the fix: B9 S0 (every fact from the AI
draft, at the draft's own density) read 0 Human, 7 AI. The B12 drafts state 40 to 68 facts in about
1,000 to 1,200 words (about 5 per 100 words); B14's pieces carry about 6 in 400 (about 1.5 per 100).
So a full-length piece at B14's density can carry only about a third of the draft's facts. Pangram
labels windows of text; the hypothesis is that it reads AI-planned content per window, so a piece
made of B14-density sections should read like B14 at full length.

Fixed before any B20 text exists:
- Drafts a0610 to a0619 (paired with B14 cell B, B18 cell W and B19).
- k = round(T / 400) sections (T = B12's target, the draft's length). 6k of the draft's facts (the
  FACTS extraction, in the draft's order), taken evenly spaced so the piece follows the whole draft,
  cut in order into k sections of 6.
- Section j's prompt is the B12 facts prompt for its own 6 facts, at the whole article's length T,
  followed by the text written so far. Each step is B18's: 4 candidate paragraphs from the PC server,
  Sonnet marks unsupported sentences against the whole draft, the fully supported candidate with the
  most words wins, else the one with the most words left after deletion; exact repeats are always
  deleted.
- A section ends at T / k words, after 2 empty steps, or after 10 steps. An article-ending candidate
  is skipped except in the last section after 0.6 T. Then B13's cleanup.
- Cell S: all 10 texts scanned. Checks: length against T, claim support against the draft, coverage
  of the draft's facts (B18's measure; expected near 6k / n, about a third), quality against the
  human cut.
Prediction: if Pangram reads AI content per window, S matches B14 (about 6 or 7 of 10 Human) at 70% or
more of T; if it reads the whole article's plan, S falls toward B9 S0.
Sharpened at 09:20, before any B20 text was scanned: Pangram 4 reads 512-token windows (stride 256) and
calls a document Human only when 90% of its characters are Human (technical report, arXiv 2607.27183,
via research/r2-primary-sources.md). If windows passed independently at B14's rate (13 of 20), a
three-window piece would read Human about 0.65^3, so 2 to 4 of 10. The test that separates the two
readings is the AI count: per-window reading predicts AI at B14's level (0 to 1 of 10) with Mixed for
most of the rest; whole-plan reading predicts AI verdicts near B9 S0 (7 of 10).

Usage (paragraph server running and tunnelled, as for B18):
  uv run python experiments/b20_sectional.py write
  uv run python experiments/b20_sectional.py record S_a0610=AI ...
"""

import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.quality import quality_pair
from humanizer.data.facts import Facts, extract, facts_prompt

sys.path.insert(0, str(ROOT / "experiments"))
from b12_replicate import _drafts  # noqa: E402
from b13_cleanup import clean_one  # noqa: E402
from b18_resample import MIN_END, N, _check, _coverage, _post, _sentences  # noqa: E402
from judge_calibrate import _cut  # noqa: E402

IDS = [f"a{n:04d}" for n in range(610, 620)]
PER, SEC_WORDS, SEC_STEPS = 6, 400, 10
PROMPTS = ROOT / "results" / "b12_prompts.jsonl"
STEPS = ROOT / "results" / "b20_steps.jsonl"
TEXTS = ROOT / "results" / "b20_texts.jsonl"
OUT = ROOT / "results" / "b20_sectional.json"


def sections(facts: list[str], target: int) -> list[list[str]]:
    """k = round(target / 400) sections of 6 facts, evenly spaced through the draft, in its order."""
    k = max(1, round(target / SEC_WORDS))
    m = min(len(facts), PER * k)
    picked = [facts[i * len(facts) // m] for i in range(m)]
    return [picked[i * m // k:(i + 1) * m // k] for i in range(k)]


def write_one(row: dict, idx: int, draft: str) -> dict:
    f = extract(draft)
    target = row["target_words"]
    secs = sections(f.facts, target)
    allowed = draft + "\n" + "\n".join(f.facts)
    paras, seen, log, ended = [], set(), [], False
    words = lambda: sum(len(p.split()) for p in paras)  # noqa: E731
    for j, chunk in enumerate(secs):
        head = facts_prompt(Facts(f.topic, chunk), target, f"{row['source']}-s{j}")
        start, empty, last = words(), 0, j == len(secs) - 1
        for step in range(SEC_STEPS):
            got = _post({"prompt": head + "".join(p + "\n" for p in paras), "allowed_text": allowed, "n": N,
                         "max_new_tokens": 300, "seed": idx * 1000 + j * 100 + step})
            cands = [_sentences(t) for t in got["texts"]]
            bad = _check(draft, cands) if any(cands) else [set() for _ in cands]
            options = []
            for c, (ss, b, eos) in enumerate(zip(cands, bad, got["eos"])):
                if eos and not (last and words() >= MIN_END * target):
                    continue
                kept = [s for i, s in enumerate(ss) if i not in b and s not in seen]
                options.append((not b, len(" ".join(kept).split()), c, kept, eos))
            choice = max(options, default=None, key=lambda o: (o[0] and o[1] > 0, o[1]))
            log.append({"id": row["source"], "section": j, "step": step, "secs": got["secs"],
                        "candidates": [{"words": len(t.split()), "sentences": len(ss), "unsupported": len(b), "eos": e}
                                       for t, ss, b, e in zip(got["texts"], cands, bad, got["eos"])],
                        "chosen": choice[2] if choice else None, "kept_words": choice[1] if choice else 0})
            if choice and choice[3]:
                paras.append(" ".join(choice[3]))
                seen.update(choice[3])
                empty = 0
            else:
                empty += 1
            ended = bool(choice and choice[4])
            if ended or empty >= 2 or words() - start >= target / len(secs):
                break
        if ended:
            break
    with STEPS.open("a") as fh:
        fh.writelines(json.dumps(r) + "\n" for r in log)
    return {"id": f"S_{row['source']}", "raw": "\n".join(paras), "steps": len(log), "sections": len(secs),
            "n_facts": len(f.facts), "n_used": sum(map(len, secs))}


def write():
    rows = {r["source"]: r for r in map(json.loads, PROMPTS.open())}
    done = {json.loads(line)["id"] for line in TEXTS.open()} if TEXTS.exists() else set()
    drafts = _drafts()
    human = [json.loads(line)["text"] for line in (ROOT / "data" / "human.jsonl").open()]

    def one(item):
        i, k = item
        r, draft = rows[k], drafts[k]
        w = write_one(r, 200 + i, draft)
        text, _ = clean_one(w["raw"])
        cc = claim_check(draft, text)
        out = w | {"text": text, "words": len(text.split()), "target_words": r["target_words"],
                   "claims_entailed": cc["claims_entailed"], "claims_total": cc["claims_total"],
                   "coverage": _coverage(draft, text),
                   "quality_vs_human_cut": quality_pair(_cut(human[int(k[1:])], len(text.split())), text)}
        with TEXTS.open("a") as fh:
            fh.write(json.dumps(out) + "\n")
        print(out["id"], out["sections"], "sections", out["steps"], "steps", out["words"], "/", r["target_words"],
              "words", f"{out['claims_entailed']}/{out['claims_total']}", f"coverage {out['coverage']:.2f}", flush=True)

    with ThreadPoolExecutor(4) as ex:  # 4 drafts at once: at most 4 Claude calls in flight
        list(ex.map(one, [(i, k) for i, k in enumerate(IDS) if f"S_{k}" not in done]))
    res = [json.loads(line) for line in TEXTS.open()]
    summary = {"texts": len(res), "words": statistics.mean(r["words"] for r in res),
               "length_ratio": statistics.mean(r["words"] / r["target_words"] for r in res),
               "claim_support": statistics.mean(r["claims_entailed"] / max(1, r["claims_total"]) for r in res),
               "coverage": statistics.mean(r["coverage"] for r in res),
               "quality_vs_human_cut": statistics.mean(r["quality_vs_human_cut"] for r in res)}
    OUT.write_text(json.dumps({"checks": summary}, indent=1))
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
    write() if sys.argv[1] == "write" else record(sys.argv[2:])
