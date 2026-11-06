"""Power and credit analysis for the long-form program's final test (B39), on documents, paired designs.

Long-form program design doc (docs/specs/2026-11-06-longform-program.md), section 7. The unit of analysis is the
test document: every condition is generated from the same document, so contrasts are paired.

Model. Each document d and condition c gets a Pangram AI share a = expit(b_c + u_d + e_dc), with u_d ~ N(0, s_u^2)
shared by all conditions of a document (B31: the document matters more than the model) and e_dc ~ N(0, s_e^2),
s_u^2 + s_e^2 = S^2 (S = 2 logit units; rho = s_u^2 / S^2 is the within-document correlation). The label follows
Pangram's rule with AI-Assisted characters ignored: Human if a <= 0.10, AI if a >= 0.80, Mixed otherwise. b_c is set
so that P(Human) equals the scenario's rate for condition c.

Two endpoints are simulated:
- label: McNemar's exact test on Human against not Human (two-sided);
- share: Wilcoxon signed-rank test on the paired AI shares (two-sided).
Holm correction over the design's primary contrasts, alpha 0.05, 2,000 simulations per cell, seed 0.

Designs.
- A (first draft of the design doc): D, CAI, CAIN, CN on all n documents; contrasts CAI>D, CAIN>CAI, CN>CAIN.
- B (tried 2026-11-06 02:29 CST): D on 16 documents only (a gate: B28 S50 read 0 of 19 Human), CAI, CAIN, CN on
  all n. Rejected: 16 pairs leave CAI>D with power 0.1 to 0.5.
Decision (2026-11-06 02:33 CST): design A, contrasts tested on the AI share (Wilcoxon), labels reported as Human
rates with Wilson intervals and McNemar as a secondary test (section 7 of the design doc). Amended 03:14 CST after
B30's verdicts: the scenario sets are kept side by side ("set1_*" is the first set, unprefixed the B30-informed
set), n runs over 32, 40, 48 and 64, and design B is no longer simulated.

Credits. One credit per started 100 words per scan (verified against B31's charges). Words per output are drawn from
the B32 pilot lengths between 1,500 and 3,000 words; each output is also scanned as a 300-word prefix (3 credits).

  uv run python experiments/lf_power.py
"""

from __future__ import annotations

import json
import math
import pathlib
from statistics import NormalDist

import numpy as np
from scipy.stats import binomtest, wilcoxon

ROOT = pathlib.Path(__file__).resolve().parents[1]
ND = NormalDist()
S = 2.0
LOGIT_HUMAN = math.log(0.10 / 0.90)

# Human rates at length per condition. Short-text evidence: D, Sonnet from half the notes, B28 S50 0 of 19 Human;
# CAI, the rewriter from the AI post alone, B30 T50 13 of 19 Human at about 600 words (seen authors); CAIN, no
# evidence; CN, the voice writer from notes, B26 V 11 of 13 at about 670 words. Revised 2026-11-06 02:47 CST when
# B30's verdicts arrived (the first set had CAI at 0.15, 0.30, 0.45, CAIN 0.30, 0.50, 0.65, CN 0.50, 0.65, 0.80).
# At length and on unseen authors the rates should be lower than the short-text ones, hence the central values.
SCENARIOS = {
    "pessimistic": {"D": 0.02, "CAI": 0.25, "CAIN": 0.35, "CN": 0.45},
    "central": {"D": 0.03, "CAI": 0.50, "CAIN": 0.60, "CN": 0.65},
    "optimistic": {"D": 0.05, "CAI": 0.70, "CAIN": 0.80, "CN": 0.80},
    "set1_pessimistic": {"D": 0.02, "CAI": 0.15, "CAIN": 0.30, "CN": 0.50},
    "set1_central": {"D": 0.03, "CAI": 0.30, "CAIN": 0.50, "CN": 0.65},
    "set1_optimistic": {"D": 0.05, "CAI": 0.45, "CAIN": 0.65, "CN": 0.80},
}
RHOS = [0.2, 0.5]
NS = [32, 40, 48, 64]
SIMS = 2000
N_D_GATE = 16


def holm(ps: list[float], alpha: float = 0.05) -> list[bool]:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    rej = [False] * len(ps)
    for rank, i in enumerate(order):
        if ps[i] <= alpha / (len(ps) - rank):
            rej[i] = True
        else:
            break
    return rej


def mcnemar(yh: np.ndarray, yl: np.ndarray) -> float:
    b, c = int((yh & ~yl).sum()), int((~yh & yl).sum())
    return 1.0 if b + c == 0 else binomtest(b, b + c, 0.5).pvalue


def wil(ah: np.ndarray, al: np.ndarray) -> float:
    d = al - ah  # lower AI share is better for the higher condition
    if np.allclose(d, 0):
        return 1.0
    return float(wilcoxon(d, zero_method="zsplit").pvalue)


def simulate(p: dict, rho: float, n: int, design: str, rng) -> dict:
    su, se = S * math.sqrt(rho), S * math.sqrt(1 - rho)
    b = {c: LOGIT_HUMAN - S * ND.inv_cdf(v) for c, v in p.items()}  # P(b + N(0, S^2) <= logit 0.1) = p
    keys = ["CAI>D", "CAIN>CAI", "CN>CAIN"]
    hits = {f"{e}:{k}": 0 for e in ("label", "share") for k in keys}
    for _ in range(SIMS):
        u = rng.normal(0, su, n)
        a = {c: 1 / (1 + np.exp(-(b[c] + u + rng.normal(0, se, n)))) for c in p}
        human = {c: a[c] <= 0.10 for c in p}
        m = slice(0, n) if design == "A" else slice(0, N_D_GATE)
        for ep in ("label", "share"):
            if ep == "label":
                ps = [mcnemar(human["CAI"][m], human["D"][m]), mcnemar(human["CAIN"], human["CAI"]),
                      mcnemar(human["CN"], human["CAIN"])]
            else:
                ps = [mcnemar(human["CAI"][m], human["D"][m]) if design == "B" else wil(a["CAI"][m], a["D"][m]),
                      wil(a["CAIN"], a["CAI"]), wil(a["CN"], a["CAIN"])]
            for k, r in zip(keys, holm(ps)):
                hits[f"{ep}:{k}"] += r
    return {k: round(v / SIMS, 3) for k, v in hits.items()}


def wilson_halfwidth(p: float, n: int) -> float:
    z = 1.96
    return round(z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n), 3)


def main() -> None:
    rng = np.random.default_rng(0)
    meta = ROOT / "results" / "b32_pilot_meta.jsonl"
    words = [json.loads(line)["words"] for line in meta.read_text().splitlines()] if meta.exists() else []
    words = [w for w in words if 1500 <= w <= 3000] or [2000]
    cps = float(np.mean([math.ceil(w / 100) for w in words]))
    out = {"model": __doc__.split("Two endpoints")[0].strip(), "sims": SIMS, "alpha": 0.05, "S_logit": S,
           "credits_per_full_scan": round(cps, 1), "words_basis": {"n": len(words), "median": int(np.median(words))},
           "power": {}, "precision": {}, "credits": {}}
    for design in ("A",):
        for name, p in SCENARIOS.items():
            for rho in RHOS:
                for n in NS:
                    out["power"][f"{design}|{name}|rho={rho}|n={n}"] = simulate(p, rho, n, design, rng)
    for n in NS:
        out["precision"][n] = {"wilson_95_halfwidth_p0.5": wilson_halfwidth(0.5, n), "p0.3": wilson_halfwidth(0.3, n)}
        out["credits"][n] = {
            "A_full_and_prefix": round(4 * n * (cps + 3)),
            "B_full_and_prefix": round(3 * n * (cps + 3) + N_D_GATE * (cps + 3)),
        }
    (ROOT / "results" / "b39_power.json").write_text(json.dumps(out, indent=1))
    print(f"credits per full scan {cps:.1f} (median words {int(np.median(words))})")
    for k, v in out["power"].items():
        print(k, v)
    for n in NS:
        print(n, out["credits"][n], out["precision"][n])


if __name__ == "__main__":
    main()
