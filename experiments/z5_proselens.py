"""Z5: does an open judge distilled from Pangram labels (ProseLens-ModernBERT-L) rank tries within a section better
than "copies least from the draft"? (attempt-2 design, section 6.5). Free except under $1 of Modal; no Pangram scan.

Rules, fixed before any score is computed (committed with this file):
- Texts: B38's 55 scanned calibration candidates (results/b38_calib_cands.jsonl, Pangram shares in
  b38_pangram.jsonl) and the 1,534 Pangram-labelled texts of results/b38_data.jsonl. ProseLens scores P(ai) per text
  (experiments/modal/z5_proselens.py).
- Gate (B37's C1 eligibility, as B38): form_ok, claim support at least 0.90, at least half the input's words.
- Primary measure: within-section pair accuracy among gate-passing candidates of the same section, over pairs whose
  Pangram shares differ by more than 0.05 (B38's rule). A pair is right when the lower score goes with the lower share.
  ProseLens against least-copying (copied_from_input) on the same pairs.
- Bar: ProseLens's pair accuracy at least 0.10 above least-copying's, with a section-clustered bootstrap 95% interval
  of the difference (2,000 resamples of sections, seed "z5") that excludes 0. Otherwise Z5 fails and the judge route
  stays closed unless Henry allows Pangram to pick in his own use (design decision 6).
- Secondary (reported, not decisive): gated best-of-4 mean share by ProseLens, least-copying, random and oracle;
  AUROC for Pangram not-Human on the 561 rewrites and within experiment and cell; AUROC on all 1,534.

Run:
  .venv/bin/python experiments/z5_proselens.py inputs
  ~/.local/bin/modal run experiments/modal/z5_proselens.py --inp results/z5_inputs.jsonl --out results/z5_scores.json
  .venv/bin/python experiments/z5_proselens.py evaluate   -> results/z5_proselens.json
"""
import collections
import itertools
import json
import random
import statistics
import sys
from pathlib import Path

RES = Path("results")


def _load(p):
    return [json.loads(line) for line in open(p)]


def inputs():
    rows = [{"id": f"CAND:{c['cid']}", "text": c["text"]} for c in _load(RES / "b38_calib_cands.jsonl")]
    rows += [{"id": f"DATA:{d['uid']}", "text": d["text"]} for d in _load(RES / "b38_data.jsonl")]
    (RES / "z5_inputs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "texts")


def _auroc(scores, labels):
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def evaluate():
    sc = json.loads((RES / "z5_scores.json").read_text())
    scans = {r["key"]: r for r in _load(RES / "b38_pangram.jsonl")}
    by = collections.defaultdict(list)
    for c in _load(RES / "b38_calib_cands.jsonl"):
        if c["cid"] not in scans:
            continue
        c = c | {"share": scans[c["cid"]]["ai_share"], "pl": sc[f"CAND:{c['cid']}"],
                 "claims": c["claims_entailed"] / max(1, c["claims_total"]), "ratio": c["words"] / c["input_words"]}
        if c["form_ok"] and c["claims"] >= 0.90 and c["ratio"] >= 0.5:
            by[c["section"]].append(c)

    def pairs(sections):
        out = []
        for s in sections:
            for a, b in itertools.combinations(by[s], 2):
                if abs(a["share"] - b["share"]) > 0.05:
                    out.append((s, a, b))
        return out

    def acc(ps, key):
        return sum((a[key] < b[key]) == (a["share"] < b["share"]) for _, a, b in ps) / len(ps) if ps else None

    secs = sorted(by)
    ps = pairs(secs)
    pl, lc = acc(ps, "pl"), acc(ps, "copied_from_input")
    rng = random.Random("z5")
    diffs = []
    for _ in range(2000):
        bs = [rng.choice(secs) for _ in secs]
        bp = [p for s in bs for p in pairs([s])]
        if bp:
            diffs.append(acc(bp, "pl") - acc(bp, "copied_from_input"))
    diffs.sort()
    ci = (diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs)) - 1])
    passed = pl - lc >= 0.10 and ci[0] > 0

    def best(key):
        return round(statistics.mean(min(by[s], key=lambda c: c[key])["share"] for s in secs), 3)

    rand = round(statistics.mean(statistics.mean(c["share"] for c in by[s]) for s in secs), 3)
    data = _load(RES / "b38_data.jsonl")
    s_all = [sc[f"DATA:{d['uid']}"] for d in data]
    y_all = [d["label"] != "Human" for d in data]
    rw = [(s, y, d) for s, y, d in zip(s_all, y_all, data) if d["rewrite"]]
    cells = collections.defaultdict(list)
    for s, y, d in rw:
        cells[(d["exp"], d["cell"])].append((s, y))
    within = [(_auroc([s for s, _ in v], [y for _, y in v]), len(v)) for v in cells.values()]
    within = [(a, n) for a, n in within if a is not None]
    res = {
        "sections": len(secs), "pairs": len(ps),
        "pair_accuracy": {"proselens": round(pl, 3), "least_copied": round(lc, 3)},
        "difference": round(pl - lc, 3), "difference_ci95": [round(ci[0], 3), round(ci[1], 3)],
        "bar": "difference at least 0.10 and CI excludes 0", "pass": passed,
        "gated_best_of_k_share": {"proselens": best("pl"), "least_copied": best("copied_from_input"),
                                  "random": rand, "oracle": best("share")},
        "auroc_all_1534": round(_auroc(s_all, y_all), 3),
        "auroc_rewrites_561": round(_auroc([s for s, _, _ in rw], [y for _, y, _ in rw]), 3),
        "auroc_rewrites_within_cell_weighted": round(sum(a * n for a, n in within) / sum(n for _, n in within), 3),
    }
    (RES / "z5_proselens.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"inputs": inputs, "evaluate": evaluate}[sys.argv[1]]()
