"""A1b and A1c: follow-ups to A1 asked for by its validators (results/research/a2-redteam-a1.md, a2-reader-a1.md).
Phase 1 credits (approved by Henry 2026-11-06). Rules fixed before any A1b or A1c text is scored or scanned.

A1b: is the rewriter needed once the notes are complete? Scan D100 (results/a1_d100.jsonl, Sonnet's post from all the
reworded notes, as written) and compare with C100's A1 scan, paired by post, on the 30 posts of A1's primary set.
Outcome: paired AI share D100 minus C100, Wilcoxon and post bootstrap interval (seed "a1b"); Human counts.
- Rewriter needed: D100 higher by at least 0.10 with p < 0.05.
- Rewriter adds little: the interval excludes a difference of 0.10.
- Otherwise inconclusive.
Prediction from attempt 1 (B28 S100: 1 Human, 18 Mixed of 19 at about 500 words): D100 reads mostly Mixed.

A1c: do the rewrites' defects earn their Human verdicts? Cell C100d: each C100 text with every sentence that
humanizer.checks.defects.prose_defects (claude-sonnet-5-5, pinned) quotes removed, plus every sentence
form.non_english_runs flags; deletion only, nothing reworded or added. A quoted defect that is not found verbatim in
the text is skipped (logged). Paired with C100's A1 scan on the same 30 posts.
- Defects help Pangram: C100d's AI share higher by at least 0.05 with p < 0.05.
- Defects do not drive the verdicts: the interval excludes a rise of 0.05.
- Otherwise inconclusive. Words removed per text are reported; texts losing more than 30% of their words are reported
  separately and kept in the test.

Both cells, plus the session's canaries, go in one blinded batch (at most 1,200 credits). Cross-session comparison
with A1's C100 scan is valid only if every frozen canary returns output identical to A1's (design amendment 6.0); if
not, C100 is rescanned in this batch and the comparisons use that.

Run:
  .venv/bin/python experiments/a1b_followups.py build
  .venv/bin/python experiments/a1b_followups.py scanfiles <dest>
  (dashboard; results/a1b_pangram_transcript.txt and results/a1b_pangram_shares.json)
  .venv/bin/python experiments/a1b_followups.py analyze
"""
import json
import random
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from humanizer.checks.defects import prose_defects
from humanizer.checks.form import non_english_runs
from humanizer.eval import scan

RES = Path("results")
TEXTS = RES / "a1b_texts.jsonl"
OUT = RES / "a1b_followups.json"


def _load(p):
    return [json.loads(line) for line in open(p)]


def _primary_docs():
    t = {r["id"]: r for r in _load(RES / "a1_texts.jsonl")}
    ex = {d["id"] for d in _load(RES / "a1_d100.jsonl") if d["excluded"]}
    return sorted(d for d in {r["doc"] for r in t.values()} - ex
                  if not t[f"C100_{d}"]["excluded"] and not t[f"C50_{d}"]["excluded"])


def _delete(text, sentences):
    removed, skipped = 0, 0
    for s in sorted(set(sentences), key=len, reverse=True):
        s = s.strip()
        if s and s in text:
            text = text.replace(s, "", 1)
            removed += len(s.split())
        else:
            skipped += 1
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text, removed, skipped


def build():
    docs = _primary_docs()
    t = {r["id"]: r for r in _load(RES / "a1_texts.jsonl")}
    d100 = {d["id"]: d for d in _load(RES / "a1_d100.jsonl")}
    rows = [{"id": f"D100_{d}", "cell": "D100", "doc": d, "text": d100[d]["D100"]} for d in docs]

    def one(d):
        src = t[f"C100_{d}"]["text"]
        bad = prose_defects(src) + non_english_runs(src)
        text, removed, skipped = _delete(src, bad)
        return {"id": f"C100d_{d}", "cell": "C100d", "doc": d, "text": text, "flagged": len(bad),
                "words_removed": removed, "skipped": skipped, "share_removed": removed / max(1, len(src.split()))}

    with ThreadPoolExecutor(4) as ex:
        rows += list(ex.map(one, docs))
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    cd = [r for r in rows if r["cell"] == "C100d"]
    summ = {"docs": len(docs), "C100d_share_removed_mean": round(statistics.mean(r["share_removed"] for r in cd), 3),
            "C100d_over_30pct": sum(r["share_removed"] > 0.30 for r in cd),
            "flagged_sentences": sum(r["flagged"] for r in cd), "skipped": sum(r["skipped"] for r in cd)}
    OUT.write_text(json.dumps({"build": summ}, indent=1))
    print(json.dumps(summ, indent=1))


def scanfiles(dest):
    texts = [{"key": r["id"], "cell": r["cell"], "doc": r["doc"], "text": r["text"]} for r in _load(TEXTS)]
    texts += scan.canaries()
    print(len(texts), "files, about", scan.write_batch("a1b", texts, dest, max_credits=1200), "credits")


def _boot(d, seed, n=5000):
    rng = random.Random(seed)
    m = sorted(statistics.mean(rng.choice(d) for _ in d) for _ in range(n))
    return [round(m[int(0.025 * n)], 4), round(m[int(0.975 * n) - 1], 4)]


def analyze():
    from scipy.stats import wilcoxon
    rows = scan.record("a1b")
    a1 = {r["key"]: r for r in _load(RES / "a1_pangram.jsonl")}
    now = {r["key"]: r for r in rows}
    can = scan.canary_check(rows, {k: {"label": v["label"], "ai_share": v["ai_share"]}
                                   for k, v in a1.items() if v["cell"] == "CAN" and "perturbed" not in k})
    res = {"canaries_identical": can["identical"], "canary_changes": can["changed"]}
    for cell, thr, name in (("D100", 0.10, "A1b_D100_minus_C100"), ("C100d", 0.05, "A1c_C100d_minus_C100")):
        docs = [d for d in _primary_docs() if f"{cell}_{d}" in now]
        diff = [now[f"{cell}_{d}"]["ai_share"] - a1[f"C100_{d}"]["ai_share"] for d in docs]
        p = float(wilcoxon(diff).pvalue) if any(diff) else 1.0
        ci = _boot(diff, f"a1b:{cell}")
        m = statistics.mean(diff)
        if m >= thr and p < 0.05:
            band = "rewriter needed" if cell == "D100" else "defects help Pangram"
        elif ci[1] < thr:
            band = "rewriter adds little" if cell == "D100" else "defects do not drive the verdicts"
        else:
            band = "inconclusive"
        res[name] = {"n": len(docs), "mean_diff": round(m, 4), "ci95": ci, "p": p, "band": band,
                     "human": [sum(now[f"{cell}_{d}"]["label"] == "Human" for d in docs),
                               sum(a1[f"C100_{d}"]["label"] == "Human" for d in docs)],
                     "mean_share": round(statistics.mean(now[f"{cell}_{d}"]["ai_share"] for d in docs), 4)}
    prev = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(prev | {"analysis": res}, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"build": build, "analyze": analyze}.get(sys.argv[1], lambda: scanfiles(sys.argv[2]))()
