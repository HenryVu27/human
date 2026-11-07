"""Attempt 2, step 0: recompute the attempt-1 claims that attempt 2 builds on, from the raw files.

Run: .venv/bin/python experiments/a2_rechecks.py
Reads only committed or local raw result files; scans nothing, spends nothing.
"""
import collections
import json

import numpy as np
from scipy import stats

R = "results/"


def jl(name):
    return [json.loads(line) for line in open(R + name)]


def cells(rows):
    out = {}
    g = collections.defaultdict(list)
    for x in rows:
        g[x["cell"]].append(x)
    for c, xs in sorted(g.items()):
        out[c] = {
            "n": len(xs),
            "labels": dict(collections.Counter(x["label"] for x in xs)),
            "mean_share": round(float(np.mean([x["ai_share"] for x in xs])), 3),
            "mean_words": round(float(np.mean([x["words"] for x in xs]))),
        }
    return out


def b36():
    rows = jl("b36_pangram.jsonl")
    cfull = sorted(x["ai_share"] for x in rows if x["cell"] == "Cfull")
    return {"cells": cells(rows), "cfull_shares": cfull,
            "cfull_under_0.20": sum(s < 0.20 for s in cfull)}


def b37_splice():
    rows = [x for x in jl("b37_pangram.jsonl") if x["cell"] == "SP"]
    base = {x["doc"]: x["words"] for x in rows if x["key"].endswith("_none")}
    out = []
    for x in rows:
        block = x["words"] - base[x["doc"]]
        out.append({"key": x["key"], "block_share": round(block / x["words"], 3),
                    "ai_share": x["ai_share"], "label": x["label"]})
    err = [abs(o["ai_share"] - o["block_share"]) for o in out]
    return {"rows": sorted(out, key=lambda o: o["block_share"]), "max_abs_error": round(max(err), 3),
            "note": "single contiguous Sonnet blocks of 88 to 248 words in 2 human posts only"}


def b38_copying():
    scans = {x["key"]: x for x in jl("b38_pangram.jsonl")}
    cands = [c for c in jl("b38_calib_cands.jsonl") if c["cid"] in scans]
    cop = np.array([c["copied_from_input"] for c in cands])
    share = np.array([scans[c["cid"]]["ai_share"] for c in cands])
    lenr = np.array([c["words"] / c["input_words"] for c in cands])
    claims = np.array([c["claims_entailed"] / max(1, c["claims_total"]) for c in cands])
    rk = stats.rankdata
    X = np.column_stack([np.ones(len(cands)), rk(lenr), rk(claims)])
    res = lambda y: y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    d0, d1 = cop.copy(), share.copy()
    by = collections.defaultdict(list)
    for i, c in enumerate(cands):
        by[c["section"]].append(i)
    for ix in by.values():
        d0[ix] -= d0[ix].mean()
        d1[ix] -= d1[ix].mean()
    return {
        "n": len(cands),
        "spearman_copied_share": round(stats.spearmanr(cop, share)[0], 3),
        "spearman_claims_share": round(stats.spearmanr(claims, share)[0], 3),
        "spearman_lenratio_share": round(stats.spearmanr(lenr, share)[0], 3),
        "spearman_copied_claims": round(stats.spearmanr(cop, claims)[0], 3),
        "partial_copied_share_given_len_claims": round(float(np.corrcoef(res(rk(cop)), res(rk(share)))[0, 1]), 3),
        "within_section_pearson_copied_share": round(float(np.corrcoef(d0, d1)[0, 1]), 3),
        "sections": len(by),
    }


def b30():
    d = json.load(open(R + "b30_rewriter.json"))
    return {"pangram": d["pangram_summary"], "checks": d["checks"]}


if __name__ == "__main__":
    out = {"b36": b36(), "b37_splice": b37_splice(), "b38_copying": b38_copying(), "b30": b30()}
    json.dump(out, open(R + "a2_rechecks.json", "w"), indent=1)
    print(json.dumps({k: (v if k != "b37_splice" else {"max_abs_error": v["max_abs_error"]}) for k, v in out.items()},
                     indent=1)[:4000])
