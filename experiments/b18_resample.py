"""B18: write, check, resample one paragraph at a time. Can the pipeline keep the draft's length?

B14's pieces pass Pangram (13 Human, 7 Mixed, 0 AI) but are about 40% of the draft's length,
because pruning deletes whole stretches the draft does not support. Here the pool writer writes
paragraph by paragraph and every paragraph is checked before the next one is written: the writer
proposes 4 candidate next paragraphs, Sonnet marks the sentences the draft does not support
(B11's rule), and the loop keeps the candidate that retains the most supported words, with its
unsupported sentences and exact repeats deleted. The article grows only from checked text, so it
can run to the draft's full length at high claim support, and the base model still decides what
comes next. If Pangram keeps its Human verdicts at full length, length is solved; if verdicts fall
toward AI as coverage of the draft rises, that maps the trade-off between keeping the draft's
content and passing (the dose-response of B9, measured on this pipeline).

Fixed before any B18 text exists:
- Drafts: B12's a0610 to a0629; prompts: results/b12_prompts.jsonl (specific facts, target length
  = the draft's).
- Writer: the pool adapter (results/gpu13b/out_pool/lora-13b-v1) served on the PC by
  gpu/serve13b.py, NF4 instead of the Mac's MLX 4-bit, Guard on, same sampling.
- Step: 4 candidates (one request, seed from the draft index and step). Keep the candidates with
  no unsupported sentence and take the one with the most words; if none, take the candidate with
  the most words left after deleting its unsupported sentences. Exact repeats of earlier
  sentences are always deleted. A candidate that ends the article is only taken once the article
  has 60% of the target length. Stop at the target length, at the article's end, after 2
  steps in a row that keep nothing, or after 40 steps.
- Then B13's deletion-only cleanup, the claim check, the share of the draft's facts the piece
  states (coverage, new here and also measured on B14's pieces) and B14's quality judge.
- Cell W: one text per draft, all 20 scanned. Pangram only scores; it selects nothing.

Usage (server running and tunnelled: ssh -N -L 8765:127.0.0.1:8765 <user>@<pc-tailscale-ip>):
  uv run python experiments/b18_resample.py write
  uv run python experiments/b18_resample.py coverage    B14 pieces, for comparison
  uv run python experiments/b18_resample.py record W_a0610=AI ...
"""

import json
import re
import statistics
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.quality import quality_pair
from humanizer.data.facts import extract
from humanizer.llm import claude

sys.path.insert(0, str(ROOT / "experiments"))
from b11_prune import SPLIT  # noqa: E402
from b12_replicate import _drafts  # noqa: E402
from b13_cleanup import clean_one  # noqa: E402
from judge_calibrate import _cut  # noqa: E402

SERVER = "http://127.0.0.1:8765/continue"
PROMPTS = ROOT / "results" / "b12_prompts.jsonl"
STEPS = ROOT / "results" / "b18_steps.jsonl"
TEXTS = ROOT / "results" / "b18_texts.jsonl"
OUT = ROOT / "results" / "b18_resample.json"
N, MAX_STEPS, MIN_END = 4, 40, 0.6

CHECK = """Below is a source draft and {n} candidate paragraphs, each with numbered sentences, written for an article based on the draft.
For each candidate, list the sentences that state something the draft does not say or clearly imply: a fact, number,
claim, example, recommendation or explanation that is not in the draft. Keep sentences that only
restate the draft, connect ideas, or are headings for content the draft covers.

Return only JSON with one key per candidate: {{"unsupported": {{"1": [sentence numbers], "2": [...]}}}}

<draft>
{draft}
</draft>

<candidates>
{candidates}
</candidates>"""

COVER = """Below is a numbered list of facts from a draft, and an article. Which facts does the article state (the same content, in any words)?

Return only JSON: {{"stated": [fact numbers]}}

<facts>
{facts}
</facts>

<article>
{article}
</article>"""


def _post(req: dict) -> dict:
    data = json.dumps(req).encode()
    with urllib.request.urlopen(urllib.request.Request(SERVER, data, {"Content-Type": "application/json"}),
                                timeout=900) as r:
        out = json.loads(r.read())
    if "error" in out:
        raise RuntimeError(out["error"])
    return out


def _sentences(text: str) -> list[str]:
    return [s for s in SPLIT.split(text.strip()) if s.strip()]


def _check(draft: str, cands: list[list[str]]) -> list[set[int]]:
    """Unsupported sentence indexes (0-based) per candidate; a missing answer keeps nothing."""
    listing = "\n\n".join(f"Candidate {c}:\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(ss, 1))
                          for c, ss in enumerate(cands, 1))
    raw = claude(CHECK.format(n=len(cands), draft=draft, candidates=listing), model="sonnet")
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return [set(range(len(ss))) for ss in cands]
    got = json.loads(m.group(0)).get("unsupported", {})
    return [{int(n) - 1 for n in got.get(str(c), [])} for c in range(1, len(cands) + 1)]


def write_one(row: dict, idx: int, support: str | None = None, cell: str = "W") -> dict:
    """support: what the text may say (default the draft; B19 adds the author's answers)."""
    draft = support or _drafts()[row["source"]]
    allowed = draft + "\n" + row["prompt"]
    paras, seen, log, empty = [], set(), [], 0
    words = lambda: sum(len(p.split()) for p in paras)  # noqa: E731
    for step in range(MAX_STEPS):
        prefix = row["prompt"] + "".join(p + "\n" for p in paras)
        got = _post({"prompt": prefix, "allowed_text": allowed, "n": N, "max_new_tokens": 300,
                     "seed": idx * 1000 + step})
        cands = [_sentences(t) for t in got["texts"]]
        bad = _check(draft, cands) if any(cands) else [set() for _ in cands]
        options = []
        for c, (ss, b, eos) in enumerate(zip(cands, bad, got["eos"])):
            kept = [s for i, s in enumerate(ss) if i not in b and s not in seen]
            if eos and words() < MIN_END * row["target_words"]:
                continue
            options.append((not b, len(" ".join(kept).split()), c, kept, eos))
        choice = max(options, default=None, key=lambda o: (o[0] and o[1] > 0, o[1]))
        rec = {"id": row["id"], "step": step, "secs": got["secs"],
               "candidates": [{"words": len(t.split()), "sentences": len(ss), "unsupported": len(b), "eos": e}
                              for t, ss, b, e in zip(got["texts"], cands, bad, got["eos"])],
               "chosen": choice[2] if choice else None, "kept_words": choice[1] if choice else 0}
        log.append(rec)
        if choice and choice[3]:
            paras.append(" ".join(choice[3]))
            seen.update(choice[3])
            empty = 0
        else:
            empty += 1
        if (choice and choice[4]) or empty >= 2 or words() >= row["target_words"]:
            break
    with STEPS.open("a") as f:
        f.writelines(json.dumps(r) + "\n" for r in log)
    return {"id": f"{cell}_{row['source']}", "raw": "\n".join(paras), "steps": len(log)}


def _coverage(draft: str, text: str) -> float:
    facts = extract(draft).facts
    listing = "\n".join(f"{i}. {x}" for i, x in enumerate(facts, 1))
    m = re.search(r"\{.*\}", claude(COVER.format(facts=listing, article=text), model="sonnet"), re.S)
    stated = {int(n) for n in json.loads(m.group(0))["stated"]} if m else set()
    return len(stated & set(range(1, len(facts) + 1))) / max(1, len(facts))


def write():
    rows = [json.loads(line) for line in PROMPTS.open()]
    done = {json.loads(line)["id"] for line in TEXTS.open()} if TEXTS.exists() else set()
    todo = [(r, i) for i, r in enumerate(rows) if f"W_{r['source']}" not in done]
    drafts = _drafts()
    human = [json.loads(line)["text"] for line in (ROOT / "data" / "human.jsonl").open()]

    def one(item):
        r, i = item
        w = write_one(r, i)
        draft = drafts[r["source"]]
        text, _ = clean_one(w["raw"])
        cc = claim_check(draft, text)
        out = w | {"text": text, "words": len(text.split()), "target_words": r["target_words"],
                   "claims_entailed": cc["claims_entailed"], "claims_total": cc["claims_total"],
                   "coverage": _coverage(draft, text),
                   "quality_vs_human_cut": quality_pair(_cut(human[int(r["source"][1:])], len(text.split())), text)}
        with TEXTS.open("a") as f:
            f.write(json.dumps(out) + "\n")
        print(out["id"], out["steps"], "steps", out["words"], "/", r["target_words"], "words",
              f"{out['claims_entailed']}/{out['claims_total']}", f"coverage {out['coverage']:.2f}", flush=True)
        return out

    with ThreadPoolExecutor(4) as ex:  # 4 drafts at once: at most 4 Claude calls in flight
        list(ex.map(one, todo))
    res = [json.loads(line) for line in TEXTS.open()]
    summary = {"texts": len(res), "words": statistics.mean(r["words"] for r in res),
               "length_ratio": statistics.mean(r["words"] / r["target_words"] for r in res),
               "claim_support": statistics.mean(r["claims_entailed"] / max(1, r["claims_total"]) for r in res),
               "coverage": statistics.mean(r["coverage"] for r in res),
               "quality_vs_human_cut": statistics.mean(r["quality_vs_human_cut"] for r in res)}
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(out | {"checks": summary}, indent=1))
    print(json.dumps(summary, indent=1))


def coverage():
    """The same coverage measure on B14's pieces (and B16's, once picked), for the comparison."""
    drafts = _drafts()
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for name in ("b14", "b16"):
        path = ROOT / "results" / f"{name}_texts.jsonl"
        if not path.exists():
            continue
        rows = [json.loads(line) for line in path.open()]
        with ThreadPoolExecutor(3) as ex:
            cov = list(ex.map(lambda r: _coverage(drafts[r["id"][2:]], r["text"]), rows))
        out[f"coverage_{name}"] = {"mean": statistics.mean(cov), "per_text": dict(zip((r["id"] for r in rows), cov))}
        print(name, round(statistics.mean(cov), 3))
    OUT.write_text(json.dumps(out, indent=1))


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {v: sum(verdicts[i] == v for i in ids) for v in ("AI", "Mixed", "Human")}
    out = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    step = sys.argv[1]
    {"write": write, "coverage": coverage}.get(step, lambda: record(sys.argv[2:]))()
