"""B33: how well do open AI-text detectors agree with Pangram, and how do they behave on long human posts?

Long-form program (docs/specs/2026-11-06-longform-program.md), phase 1. The open panel
(experiments/modal/lf_detect.py: Binoculars, Fast-DetectGPT on the Falcon pair and on Llama 3.1 8B, MELD,
desklib) is the development judge; Pangram stays held out. This is detector calibration in the sense of the
spec (section 8): it reads Pangram verdicts that already exist and never trains or tunes anything on them.

Inputs
- results/b33_calib.jsonl: every Pangram verdict from B1 to B31 joined to the exact scanned text (1,201 rows,
  built and checked by a separate agent; manifest in results/b33_calib_manifest.json).
- results/b32_pilot_corpus.jsonl: the B32 pilot corpus of long pre-ChatGPT blog posts (human, no Pangram label).

Rules, fixed 2026-11-06 02:07 CST, before any detector score existed
- Deduplication: rows with identical text are scored once; the analysis keeps the first id of each group (8 pairs
  in the manifest, all with equal verdicts).
- Targets: (a) not Human (Mixed or AI) against Human; (b) AI against Human or Mixed. Each detector's `ai` value is
  oriented so that higher means more AI-like. The primary statistic is the area under the ROC curve (AUROC) for
  target (a) on all rows, with a 95% interval from a bootstrap that resamples source documents (the id's last
  field: the opening, draft or essay the text came from), 2,000 resamples, seed 0. Secondary: AUROC by origin
  (human, base, local_writer, instruct; reported where both classes have 5 or more rows), by length (under 200,
  200 to 399, 400 to 799, 800 or more words), Spearman correlation with Pangram's AI share where it was recorded
  (B1, B31), and Cohen's kappa between a detector flag and Pangram's not-Human verdict.
- Thresholds for flags are never fitted to Pangram labels. Two are used: the detector's shipped threshold where
  one exists (Binoculars 0.8536 low-FPR mode, MELD's 1% FPR offset 3.92, desklib p 0.5), and the threshold at a 5%
  false-positive rate on the B32 pilot corpus (human posts, all splits; label-free).
- Panel score: the mean over the four mechanisms (binoculars, fdg_llama, meld, desklib) of each detector's
  percentile within the B32 pilot corpus distribution. Label-free and fixed in advance; fdg_falcon is left out
  because it shares binoculars' forward passes.
- Long human posts: each detector's false-positive rate at its shipped threshold on the pilot corpus, by length
  (1,500 to 1,999, 2,000 to 2,999, 3,000 to 4,000 words) and genre, and Spearman correlation of the score with
  length.

  uv run python experiments/b33_calibrate.py prep
  modal run experiments/modal/lf_detect.py::score --inp results/b33_calib_inputs.jsonl --out results/b33_scores_calib.jsonl
  modal run experiments/modal/lf_detect.py::score --inp results/b33_corpus_inputs.jsonl --out results/b33_scores_corpus.jsonl
  uv run python experiments/b33_calibrate.py analyze
"""

from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RES = ROOT / "results"
DETS = ["binoculars", "fdg_falcon", "fdg_llama", "meld", "desklib"]
PANEL = ["binoculars", "fdg_llama", "meld", "desklib"]
SHIPPED = {"binoculars": -0.8536432310785527, "meld": 3.919607639312744, "desklib": 0.0}  # in `ai` orientation
LEN_BINS = [(0, 200, "<200"), (200, 400, "200-399"), (400, 800, "400-799"), (800, 10**9, "800+")]
LONG_BINS = [(1500, 2000, "1500-1999"), (2000, 3000, "2000-2999"), (3000, 4001, "3000-4000")]


def load(p: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def prep() -> None:
    rows = load(RES / "b33_calib.jsonl")
    seen, keep, dups = {}, [], []
    for r in rows:
        if r["text"] in seen:
            dups.append([seen[r["text"]], r["id"]])
            continue
        seen[r["text"]] = r["id"]
        keep.append({"id": r["id"], "text": r["text"]})
    (RES / "b33_calib_inputs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in keep))
    if not (RES / "b32_pilot_corpus.jsonl").exists():
        print(f"calib {len(keep)} unique of {len(rows)} ({len(dups)} duplicates); no corpus yet")
        return
    corpus = load(RES / "b32_pilot_corpus.jsonl")
    (RES / "b33_corpus_inputs.jsonl").write_text("".join(json.dumps({"id": r["id"], "text": r["text"]}) + "\n"
                                                         for r in corpus))
    print(f"calib {len(keep)} unique of {len(rows)} ({len(dups)} duplicates); corpus {len(corpus)}")


def auroc(pos: np.ndarray, neg: np.ndarray) -> float | None:
    if len(pos) == 0 or len(neg) == 0:
        return None
    allv = np.concatenate([pos, neg])
    order = allv.argsort(kind="mergesort")
    ranks = np.empty(len(allv))
    sv = allv[order]
    i = 0
    while i < len(sv):  # average ranks for ties
        j = i
        while j + 1 < len(sv) and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    rp = ranks[: len(pos)].sum()
    return float((rp - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def spearman(x: np.ndarray, y: np.ndarray) -> float | None:
    """Tie-aware (average ranks). Fixed 2026-11-06 03:14 CST after the outside judge found the first version broke
    ties by file order (474 of the 680 AI shares are 0.0)."""
    from scipy.stats import spearmanr

    if len(x) < 5:
        return None
    return float(spearmanr(x, y).statistic)


def kappa(a: np.ndarray, b: np.ndarray) -> float | None:
    if len(a) == 0:
        return None
    po = float((a == b).mean())
    pe = float(a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean()))
    return None if pe == 1 else (po - pe) / (1 - pe)


def boot_auroc(score, y, clusters, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    keys = np.unique(clusters)
    idx_by = {k: np.where(clusters == k)[0] for k in keys}
    vals = []
    for _ in range(n):
        pick = rng.choice(keys, size=len(keys), replace=True)
        idx = np.concatenate([idx_by[k] for k in pick])
        a = auroc(score[idx][y[idx] == 1], score[idx][y[idx] == 0])
        if a is not None:
            vals.append(a)
    return [round(float(np.percentile(vals, 2.5)), 3), round(float(np.percentile(vals, 97.5)), 3)]


def analyze() -> None:
    calib = {r["id"]: r for r in load(RES / "b33_calib.jsonl")}
    sc = {r["id"]: r for r in load(RES / "b33_scores_calib.jsonl")}
    corpus = {r["id"]: r for r in load(RES / "b32_pilot_corpus.jsonl")}
    scc = {r["id"]: r for r in load(RES / "b33_scores_corpus.jsonl")}
    ids = [i for i in sc if i in calib]
    out = {"n_calib": len(ids), "n_corpus": len(scc), "detectors": {}, "panel_members": PANEL}

    # label-free reference distribution: the long human corpus
    ref = {d: np.array(sorted(scc[i][d]["ai"] for i in scc if scc[i].get(d))) for d in DETS}
    thr5 = {d: float(np.percentile(ref[d], 95)) for d in DETS if len(ref[d])}

    def pct(d, v):
        return float(np.searchsorted(ref[d], v, side="right") / len(ref[d]))

    def val(row, d):
        if d == "panel":
            if not all(row.get(m) for m in PANEL):
                return None
            return float(np.mean([pct(m, row[m]["ai"]) for m in PANEL]))
        return row[d]["ai"] if row.get(d) else None

    panel_ref = np.array(sorted(v for v in (val(scc[i], "panel") for i in scc) if v is not None))
    thr5["panel"] = float(np.percentile(panel_ref, 95))

    for d in DETS + ["panel"]:
        rows = [(i, val(sc[i], d)) for i in ids]
        rows = [(i, v) for i, v in rows if v is not None]
        s = np.array([v for _, v in rows])
        lab = [calib[i]["label"] for i, _ in rows]
        y_nh = np.array([lb != "Human" for lb in lab], dtype=int)
        y_ai = np.array([lb == "AI" for lb in lab], dtype=int)
        cl = np.array([i.split(":")[-1] for i, _ in rows])
        org = np.array([calib[i]["origin"] for i, _ in rows])
        words = np.array([calib[i]["words"] for i, _ in rows])
        res = {"n": len(rows),
               "auroc_not_human": round(auroc(s[y_nh == 1], s[y_nh == 0]), 3),
               "auroc_not_human_ci": boot_auroc(s, y_nh, cl),
               "auroc_ai": round(auroc(s[y_ai == 1], s[y_ai == 0]), 3),
               "auroc_ai_ci": boot_auroc(s, y_ai, cl)}
        by_origin = {}
        for o in ["human", "base", "local_writer", "instruct"]:
            m = org == o
            n1, n0 = int(y_nh[m].sum()), int((1 - y_nh[m]).sum())
            a = auroc(s[m & (y_nh == 1)], s[m & (y_nh == 0)]) if n1 >= 5 and n0 >= 5 else None
            by_origin[o] = {"n": int(m.sum()), "not_human": n1, "auroc_not_human": None if a is None else round(a, 3),
                            "mean_ai": round(float(s[m].mean()), 3) if m.any() else None}
        res["by_origin"] = by_origin
        by_len = {}
        for lo, hi, name in LEN_BINS:
            m = (words >= lo) & (words < hi)
            a = auroc(s[m & (y_nh == 1)], s[m & (y_nh == 0)])
            by_len[name] = {"n": int(m.sum()), "not_human": int(y_nh[m].sum()),
                            "auroc_not_human": None if a is None else round(a, 3)}
        res["by_length"] = by_len
        share = [(v, calib[i]["ai_share"]) for i, v in rows if calib[i]["ai_share"] is not None]
        if share:
            res["spearman_ai_share"] = round(spearman(np.array([a for a, _ in share]), np.array([b for _, b in share])), 3)
            res["n_ai_share"] = len(share)
        flags = {}
        for name, t in (("shipped", SHIPPED.get(d)), ("fpr5_corpus", thr5.get(d))):
            if t is None:
                continue
            f = (s > t).astype(int)
            flags[name] = {"threshold_ai": round(t, 4), "flag_rate": round(float(f.mean()), 3),
                           "kappa_not_human": round(kappa(f, y_nh), 3),
                           "agree_not_human": round(float((f == y_nh).mean()), 3),
                           "flag_rate_on_pangram_human": round(float(f[y_nh == 0].mean()), 3),
                           "flag_rate_on_pangram_not_human": round(float(f[y_nh == 1].mean()), 3)}
        res["flags"] = flags
        # long human corpus behaviour
        cv = [(i, val(scc[i], d)) for i in scc]
        cv = [(i, v) for i, v in cv if v is not None]
        cs = np.array([v for _, v in cv])
        cw = np.array([corpus[i]["words"] for i, _ in cv])
        cg = np.array([corpus[i]["genre"] for i, _ in cv])
        long = {"n": len(cv), "spearman_with_words": round(spearman(cs, cw), 3)}
        t = SHIPPED.get(d)
        if t is not None:
            long["fpr_shipped"] = round(float((cs > t).mean()), 3)
            long["fpr_shipped_by_length"] = {name: round(float((cs[(cw >= lo) & (cw < hi)] > t).mean()), 3)
                                             if ((cw >= lo) & (cw < hi)).any() else None for lo, hi, name in LONG_BINS}
            long["fpr_shipped_by_genre"] = {g: round(float((cs[cg == g] > t).mean()), 3) for g in sorted(set(cg))}
        res["long_human_corpus"] = long
        out["detectors"][d] = res

    # how different are the detectors? Spearman between detectors on the calibration rows
    mat = {}
    for a in DETS:
        for b in DETS:
            if a < b:
                pairs = [(sc[i][a]["ai"], sc[i][b]["ai"]) for i in ids if sc[i].get(a) and sc[i].get(b)]
                mat[f"{a}~{b}"] = round(spearman(np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])), 3)
    out["inter_detector_spearman"] = mat
    (RES / "b33_calibration.json").write_text(json.dumps(out, indent=1))
    print(f"{'detector':12} {'AUROC notH':>10} {'95% CI':>14} {'AUROC AI':>9} {'rho share':>9} {'kappa5%':>8} {'FPR long':>8}")
    for d, r in out["detectors"].items():
        k = r["flags"].get("fpr5_corpus", {}).get("kappa_not_human")
        print(f"{d:12} {r['auroc_not_human']:>10} {str(r['auroc_not_human_ci']):>14} {r['auroc_ai']:>9} "
              f"{str(r.get('spearman_ai_share')):>9} {str(k):>8} {str(r['long_human_corpus'].get('fpr_shipped')):>8}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["prep", "analyze"])
    a = ap.parse_args()
    {"prep": prep, "analyze": analyze}[a.step]()
