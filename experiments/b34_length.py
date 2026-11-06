"""B34: does length by itself move Pangram's verdict? Human posts and raw base-model text at 300 words and at length.

Long-form program, gate 1 (design doc docs/specs/2026-11-06-longform-program.md, amendment of 2026-11-06 09:07 CST).
Pangram labels a document Human only if 90% of its characters are labelled Human, and publishes no accuracy above
499 words. This is detector calibration (spec section 8): nothing here selects a model, prompt or writer.

Rules, fixed 2026-11-06 09:07 CST, before any document is selected or any B34 text exists.
- Documents: B32 pilot posts in the calib split (site bucket 75 to 79), 1,800 to 3,000 words, after the B32 judge's
  fixes, page type personal_post or technical_post with a single author, in the order sha256("b34-v1:" + id); all
  chosen by experiments/b36_transfer.py `select` (results/b34_docs.jsonl): the first 10 are H, the next 8 are B.
- H cells: H300 is the post cut at the last sentence end at or before 300 words (at least 250); Hfull is the post.
- B cells: OLMo-2-1124-13B base (bf16, vLLM on Modal, experiments/modal/lf_continue.py; the base of B30's rewriter)
  continues the post's first 300 words (cut as H300), temperature 0.8, top-p 0.95, up to 2,800 new tokens, seeds 0,
  1, 2 tried in order. A try is kept if its continuation has at least 1,500 words, at most 20% of its word 4-grams
  repeated, and at most 5% of its words in 8-word runs copied from the source post; a post with no passing try is
  excluded and reported. Only the continuation is scanned: B300 is its first 300 words cut as above, Bfull the
  continuation cut at the last sentence end at or before 2,000 words.
- Scanned blinded inside B36's scan (one shuffled order, b36_transfer.py `scanfiles`). A text under 150 words counts
  as not Human. About 420 credits.
- Predictions: H300 and Hfull read Human on 10 of 10 each (no false positives at length). B: the full continuation
  reads Human no more often than its 300-word prefix, and Bfull reads Human on at most 5 of 8 (B31: OLMo-2-13B
  continuations read not Human on 17% of 150 to 250-word texts; the 90% rule should push long texts toward Mixed).
- Analysis: per cell the Human count with a Wilson 95% interval and the mean AI share; McNemar on prefix against
  full for H and for B (descriptive at these sizes); pooled with B36's C300 against Cfull and D300 against Dfull in
  the report.

Usage:
  uv run python experiments/b34_length.py prompts
  modal run experiments/modal/lf_continue.py --prompts results/b34_cont_prompts.jsonl --out results/b34_cont_raw.jsonl
  uv run python experiments/b34_length.py pick
  (scan with experiments/b36_transfer.py scanfiles and record)
  uv run python experiments/b34_length.py analyze
"""

from __future__ import annotations

import json
import re
import statistics
import sys

from humanizer import ROOT
from humanizer.checks.copying import copied_share

sys.path.insert(0, str(ROOT / "experiments"))
from b36_transfer import PANGRAM, _wilson, cut300  # noqa: E402

RES = ROOT / "results"
DOCS = RES / "b34_docs.jsonl"
PROMPTS = RES / "b34_cont_prompts.jsonl"
RAW = RES / "b34_cont_raw.jsonl"
TEXTS = RES / "b34_texts.jsonl"
OUT = RES / "b34_length.json"


def cut_at(text: str, n: int) -> str:
    words = text.split()
    if len(words) <= n:
        return text.strip()
    head = " ".join(words[:n])
    ends = [m.end() for m in re.finditer(r"[.!?][\"')\]]?(?=\s|$)", head)]
    return head[:ends[-1]] if ends else head


def repeated_4grams(text: str) -> float:
    w = re.findall(r"[a-z0-9']+", text.lower())
    grams = [tuple(w[i:i + 4]) for i in range(len(w) - 3)]
    return 1 - len(set(grams)) / max(1, len(grams))


def prompts():
    docs = [json.loads(line) for line in DOCS.open() if json.loads(line)["role"] == "B"]
    rows = [{"id": d["id"], "try": t, "seed": t, "opening": cut300(d["text"]), "max_tokens": 2800}
            for d in docs for t in range(3)]
    PROMPTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "continuation prompts")


def pick():
    docs = {json.loads(line)["id"]: json.loads(line) for line in DOCS.open()}
    raw = [json.loads(line) for line in RAW.open()]
    texts, excluded, tries = [], [], {}
    for d in (x for x in docs.values() if x["role"] == "H"):
        texts += [{"key": f"H300_{d['id']}", "cell": "H300", "doc": d["id"], "text": cut300(d["text"])},
                  {"key": f"Hfull_{d['id']}", "cell": "Hfull", "doc": d["id"], "text": d["text"]}]
    for d in (x for x in docs.values() if x["role"] == "B"):
        kept = None
        for r in sorted((r for r in raw if r["id"] == d["id"]), key=lambda r: r["try"]):
            t = r["text"].strip()
            checks = {"words": len(t.split()), "repeat4": round(repeated_4grams(t), 3),
                      "copied": round(copied_share(t, d["text"]), 3)}
            tries.setdefault(d["id"], []).append(checks)
            if checks["words"] >= 1500 and checks["repeat4"] <= 0.20 and checks["copied"] <= 0.05:
                kept = t
                break
        if kept is None:
            excluded.append(d["id"])
            continue
        texts += [{"key": f"B300_{d['id']}", "cell": "B300", "doc": d["id"], "text": cut300(kept)},
                  {"key": f"Bfull_{d['id']}", "cell": "Bfull", "doc": d["id"], "text": cut_at(kept, 2000)}]
    TEXTS.write_text("".join(json.dumps(t | {"words": len(t["text"].split())}) + "\n" for t in texts))
    summ = {"texts": len(texts), "excluded_B": excluded, "tries": tries,
            "words": {c: statistics.mean(len(t["text"].split()) for t in texts if t["cell"] == c)
                      for c in ("H300", "Hfull", "B300", "Bfull") if any(t["cell"] == c for t in texts)}}
    OUT.write_text(json.dumps({"pick": summ}, indent=1))
    print(json.dumps(summ, indent=1))


def analyze():
    from scipy.stats import binomtest

    rows = [json.loads(line) for line in PANGRAM.open()]
    by = {}
    for r in rows:
        if r["cell"] in ("H300", "Hfull", "B300", "Bfull"):
            r["human"] = r["label"] == "Human" and r["words"] >= 150
            by.setdefault(r["cell"], {})[r["doc"]] = r
    cells = {c: {"n": len(d), "human": sum(v["human"] for v in d.values()),
                 "human_ci": _wilson(sum(v["human"] for v in d.values()), len(d)),
                 "labels": {x: sum(v["label"] == x for v in d.values()) for x in ("Human", "Mixed", "AI")},
                 "mean_ai_share": round(statistics.mean(v["ai_share"] for v in d.values()), 3)}
             for c, d in sorted(by.items())}
    pairs = {}
    for a, b in (("H300", "Hfull"), ("B300", "Bfull")):
        docs = sorted(set(by.get(a, {})) & set(by.get(b, {})))
        up = sum(by[a][x]["human"] and not by[b][x]["human"] for x in docs)
        down = sum(by[b][x]["human"] and not by[a][x]["human"] for x in docs)
        pairs[f"{a}_vs_{b}"] = {"pairs": len(docs), "prefix_only_human": up, "full_only_human": down,
                                "p_mcnemar": round(float(binomtest(up, up + down, 0.5).pvalue), 4) if up + down else 1.0,
                                "mean_ai_share_full_minus_prefix": round(statistics.mean(
                                    by[b][x]["ai_share"] - by[a][x]["ai_share"] for x in docs), 3) if docs else None}
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {"pangram": {"cells": cells, "pairs": pairs}}, indent=1))
    print(json.dumps({"cells": cells, "pairs": pairs}, indent=1))


if __name__ == "__main__":
    {"prompts": prompts, "pick": pick, "analyze": analyze}[sys.argv[1]]()
