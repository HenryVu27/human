"""A1: does full human content choice rescue whole posts on writers the rewriter never saw? (attempt-2 design,
section 6.3; phase 1 approved by Henry 2026-11-06.)

Rules, fixed before any A1 text exists (committed with this file; amendments carry the time from `date`).

Documents: B36's 32 test-A posts (results/b36_inputs.jsonl), development data since B37. Paired across cells.

Cells
- D100 (input, not scanned): B25's DRAFT prompt (as B36) with the post's title and word count and ALL its reworded
  notes (b36_inputs "reworded"), Sonnet through humanizer.llm with the alias "sonnet", exactly as B36 drew D50; the
  resolved model is logged in the call cache and must be claude-sonnet-5-5, the model that answered for attempt 1's
  checks. A D100 under 1,000 words is excluded from every contrast (reported), not replaced.
- C100 (scanned): B30's rewriter on D100, section by section (B36's sections(), 600 to 1,000 words; B36's prompt row),
  4 seeds (0 to 3) through experiments/modal/lf_rewrite_hf.py unchanged (4-bit, Guard, T 0.8, top-p 0.95, rep 1.05).
  Each candidate gets B37's _assess (prune, repeat drop, cleanup, claim check against its section, form checks,
  copying) and B37's C1 pick (least copying among candidates passing the form checks with claim support at least
  0.90 and at least half the section's words; fallbacks as B37). Sections are joined in order.
- C50 (scanned): B37's C1 texts (results/b37_texts.jsonl, cell C1), unchanged: the same rewriter, seeds 0 to 3 and pick
  on D50. Never scanned before.
- S50 (scanned): Smaug-Humanizer (experiments/modal/a1_smaug.py, the model card's prompt and sampling, no Guard) on
  D50 cut into chunks of about 400 to 600 words at paragraph ends (B36's sections() with lo 380, hi 600, tail 150),
  4 seeds; the same _assess and C1 pick per chunk; chunks joined.
- L (all-notes notes-first writer): deferred to December's Modal credit by this rule; not generated in November.

Exclusions and covariates (all cells): a text copying more than 15% of its words from the human post in 8-word runs
is excluded from contrasts involving it (B36's rule). Reported per cell: C1 fallback counts, length over D and over
the human post, claim support, copying from D. A sensitivity analysis drops posts with any fallback section.

Scan: C100, C50 and S50 (96 texts) plus the session's canaries (humanizer.eval.scan.canaries), one blinded shuffled
batch, scoring form = the texts as written (prose; these posts carry no code or math by B36's selection, checked by
scoring_form leaving them unchanged within 1% of words). At most 1,500 credits by write_batch's guard.

Primary contrast: C100 against C50, paired whole-post AI share, Wilcoxon signed-rank (two-sided) and the paired mean
difference with a post bootstrap 95% interval (5,000 resamples, seed "a1").
Bands (exhaustive; Holm-adjusted p over the two A1 contrasts here, re-adjusted with A2-N at G1):
- large content effect: C100 lower by at least 0.10 and p_adj < 0.05;
- small content effect: lower, p_adj < 0.05, by under 0.10;
- no useful content effect: p_adj >= 0.05 and the interval's lower end (the largest plausible drop) is under 0.10;
- inconclusive: p_adj >= 0.05 and the interval includes a drop of 0.10;
- content hurts: C100 higher with p_adj < 0.05.
Reported beside the band, not in it: Human counts (McNemar), median shares, whole-post Human rate.
Secondary: S50 against C50, same test; S50 lower by at least 0.05 with p_adj < 0.05 means phase 2 tries Smaug's
weights as R2's starting point (chunk size and model are confounded, so the conclusion names only the weights).
Quality: 10 C100-against-D100 and 10 S50-against-D50 section pairs, drawn by seed "a1-q" from posts with a passing
section, go to Henry's G1 blind read.

Amendment 2026-11-06 20:03 CST, before any C100 or S50 text is assessed or scanned: November's Modal free credit (about $7.6 left after
a failed C100 run at batch 16, all four containers out of memory, $1.08) covers C100 at batch 8 but not S50 as well.
S50 moves to December's credit (or the PC, Smaug's GGUF), so no paid spend occurs. The first A1 scan is C100, C50 and
the canaries; the primary contrast (C100 against C50) is unchanged and same-batch. S50 is scanned later in its own
batch with the canaries; S50 against C50 uses the earlier C50 scan only if every canary returns identical output,
otherwise C50 is rescanned in S50's batch. Holm stays over the two A1 contrasts.

Usage:
  .venv/bin/python experiments/a1_content.py drafts          # D100 (Sonnet)
  .venv/bin/python experiments/a1_content.py prompts         # C100 and S50 prompt rows
  ~/.local/bin/modal run experiments/modal/lf_rewrite_hf.py --prompts results/a1_prompts_c100.jsonl --out results/a1_gen_c100.jsonl --seeds 0,1,2,3 --batch 16
  ~/.local/bin/modal run experiments/modal/a1_smaug.py --prompts results/a1_prompts_s50.jsonl --out results/a1_gen_s50.jsonl --seeds 0,1,2,3
  .venv/bin/python experiments/a1_content.py pick
  .venv/bin/python experiments/a1_content.py scanfiles <dest>
  (dashboard scan; transcript and shares saved as results/a1_pangram_transcript.txt, results/a1_pangram_shares.json)
  .venv/bin/python experiments/a1_content.py analyze
"""
from __future__ import annotations

import json
import random
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from b25_blog import DRAFT, plain, voice  # noqa: E402
from b36_transfer import _prompt_row, sections  # noqa: E402
from b37_gate2a import _assess, _pick_c1  # noqa: E402

from humanizer.checks.copying import copied_share  # noqa: E402
from humanizer.eval import scan  # noqa: E402
from humanizer.llm import claude_many  # noqa: E402

RES = Path("results")
INPUTS = RES / "b36_inputs.jsonl"
DOCS = RES / "b36_docs.jsonl"
D100 = RES / "a1_d100.jsonl"
P_C100 = RES / "a1_prompts_c100.jsonl"
P_S50 = RES / "a1_prompts_s50.jsonl"
G_C100 = RES / "a1_gen_c100.jsonl"
G_S50 = RES / "a1_gen_s50.jsonl"
TEXTS = RES / "a1_texts.jsonl"
OUT = RES / "a1_content.json"
MAX_CREDITS = 1500


def _load(p):
    return [json.loads(line) for line in open(p)] if Path(p).exists() else []


def _save(path, rows):
    Path(path).write_text("".join(json.dumps(r) + "\n" for r in rows))


def _merge(key, val):
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {key: val}, indent=1))


def drafts():
    rows = _load(INPUTS)
    posts = claude_many([DRAFT.format(title=r["title"], words=int(round(r["words"], -1)),
                                      notes="\n".join(f"- {x}" for x in r["reworded"])) for r in rows], model="sonnet")
    docs = {d["id"]: d for d in _load(DOCS)}
    out = []
    for r, post in zip(rows, posts):
        text = plain(post) if post else ""
        out.append({"id": r["id"], "D100": text, "words": len(text.split()), "notes": len(r["reworded"]),
                    "excluded": len(text.split()) < 1000,
                    "D100_copied_from_human": copied_share(text, docs[r["id"]]["text"])})
    _save(D100, out)
    summ = {"docs": len(out), "excluded_under_1000": sum(o["excluded"] for o in out),
            "D100_words": statistics.mean(o["words"] for o in out),
            "D50_words": statistics.mean(len(r["D"].split()) for r in rows),
            "notes_per_post": statistics.mean(o["notes"] for o in out),
            "D100_copied_from_human": statistics.mean(o["D100_copied_from_human"] for o in out)}
    _merge("drafts", summ)
    print(json.dumps(summ, indent=1))


def prompts():
    c, s = [], []
    for d in _load(D100):
        if d["excluded"]:
            continue
        for k, sec in enumerate(sections(d["D100"])):
            c.append(_prompt_row(f"C100_{d['id']}_{k}", sec) | {"doc": d["id"], "part": k, "arm": "C"})
    for r in _load(INPUTS):
        for k, ch in enumerate(sections(r["D"], lo=380, hi=600, tail=150)):
            w = len(ch.split())
            s.append({"id": f"S50_{r['id']}_{k}", "text": ch, "allowed_text": ch, "prompt": ch, "words": w,
                      "max_new_tokens": int(w * 1.4 * 1.5) + 64, "doc": r["id"], "part": k, "arm": "S"})
    _save(P_C100, c)
    _save(P_S50, s)
    print(len(c), "C100 section prompts;", len(s), "S50 chunk prompts")


def _cell(name, prompts_path, gen_path, workers=4):
    prm = {p["id"]: p for p in _load(prompts_path)}
    gens = [g for g in _load(gen_path) if g["id"] in prm]
    with ThreadPoolExecutor(workers) as ex:
        assessed = list(ex.map(lambda g: _assess(g, prm[g["id"]]), gens))
    by = {}
    for a in assessed:
        by.setdefault(a["id"], []).append(a)
    docs = {d["id"]: d for d in _load(DOCS)}
    out, rules = [], {}
    for doc in sorted({p["doc"] for p in prm.values()}):
        parts = sorted((p for p in prm.values() if p["doc"] == doc), key=lambda p: p["part"])
        chosen = []
        for p in parts:
            c, how = _pick_c1(by.get(p["id"], []), p["words"])
            if c is None:
                c, how = max(by[p["id"]], key=lambda x: (x["claims_entailed"], x["support"])), "none_most_supported"
            rules[how] = rules.get(how, 0) + 1
            chosen.append(c | {"rule": how})
        t = "\n\n".join(c["text"] for c in chosen)
        src = "\n\n".join(p["allowed_text"] for p in parts)
        out.append({"id": f"{name}_{doc}", "cell": name, "doc": doc, "text": t, "words": len(t.split()),
                    "input_words": len(src.split()), "human_words": docs[doc]["words"],
                    "claims_entailed": sum(c["claims_entailed"] for c in chosen),
                    "claims_total": sum(c["claims_total"] for c in chosen),
                    "sections_form_ok": sum(c["form_ok"] for c in chosen), "sections": len(chosen),
                    "fallback_sections": sum(c["rule"] != "eligible" for c in chosen),
                    "copied_from_input": copied_share(t, src), "copied_from_human": copied_share(t, docs[doc]["text"]),
                    "seeds": [c["seed"] for c in chosen], "voice": voice(t)})
    return out, rules


def pick():
    c100, r100 = _cell("C100", P_C100, G_C100)
    s50, r50 = _cell("S50", P_S50, G_S50)
    docs = {d["id"]: d for d in _load(DOCS)}
    inputs = {r["id"]: r for r in _load(INPUTS)}
    c50 = []
    for r in _load(RES / "b37_texts.jsonl"):
        if r["cell"] == "C1":
            c50.append({"id": f"C50_{r['doc']}", "cell": "C50", "doc": r["doc"], "text": r["text"], "words": r["words"],
                        "input_words": len(inputs[r["doc"]]["D"].split()), "human_words": docs[r["doc"]]["words"],
                        "claims_entailed": r["claims_entailed"], "claims_total": r["claims_total"],
                        "sections_form_ok": r["sections_form_ok"], "sections": r["sections"],
                        "fallback_sections": sum(x != "eligible" for x in r["rules"]),
                        "copied_from_input": r["copied_from_D"], "copied_from_human": r["copied_from_human"],
                        "seeds": r["seeds"], "voice": r["voice"]})
    texts = c100 + c50 + s50
    for t in texts:
        t["excluded"] = t["copied_from_human"] > 0.15
        t["scoring_form_change"] = 1 - len(scan.scoring_form(t["text"]).split()) / max(1, t["words"])
    _save(TEXTS, texts)
    summ = {"rules": {"C100": r100, "S50": r50}}
    for cell in ("C100", "C50", "S50"):
        cr = [t for t in texts if t["cell"] == cell]
        summ[cell] = {"texts": len(cr), "excluded": sum(t["excluded"] for t in cr),
                      "words": round(statistics.mean(t["words"] for t in cr)),
                      "over_input": round(statistics.mean(t["words"] / t["input_words"] for t in cr), 3),
                      "over_human": round(statistics.mean(t["words"] / t["human_words"] for t in cr), 3),
                      "claim_support": round(sum(t["claims_entailed"] for t in cr) / max(1, sum(t["claims_total"] for t in cr)), 3),
                      "fallback_sections": sum(t["fallback_sections"] for t in cr),
                      "sections": sum(t["sections"] for t in cr),
                      "copied_from_input": round(statistics.mean(t["copied_from_input"] for t in cr), 3),
                      "max_copied_from_human": round(max(t["copied_from_human"] for t in cr), 3),
                      "max_scoring_form_change": round(max(t["scoring_form_change"] for t in cr), 3)}
    _merge("pick", summ)
    print(json.dumps(summ, indent=1))


def scanfiles(dest):
    texts = [{"key": t["id"], "cell": t["cell"], "doc": t["doc"], "text": t["text"]} for t in _load(TEXTS)]
    texts += scan.canaries()
    total = scan.write_batch("a1", texts, dest, max_credits=MAX_CREDITS)
    print(len(texts), "files, about", total, "credits")


def _wilcoxon(d):
    from scipy.stats import wilcoxon
    return float(wilcoxon(d).pvalue) if any(d) else 1.0


def _boot(d, seed="a1", n=5000):
    rng = random.Random(seed)
    m = sorted(statistics.mean(rng.choice(d) for _ in d) for _ in range(n))
    return [round(m[int(0.025 * n)], 4), round(m[int(0.975 * n) - 1], 4)]


def analyze():
    rows = scan.record("a1")
    sh = {r["key"]: r for r in rows}
    texts = {t["id"]: t for t in _load(TEXTS)}
    excl_d100 = {d["id"] for d in _load(D100) if d["excluded"]}

    def contrast(a, b):
        docs = sorted({t["doc"] for t in texts.values()} - excl_d100)
        pairs = [(sh[f"{a}_{d}"], sh[f"{b}_{d}"]) for d in docs
                 if f"{a}_{d}" in sh and f"{b}_{d}" in sh
                 and not texts[f"{a}_{d}"]["excluded"] and not texts[f"{b}_{d}"]["excluded"]]
        diff = [x["ai_share"] - y["ai_share"] for x, y in pairs]
        hx = sum(x["label"] == "Human" for x, _ in pairs)
        hy = sum(y["label"] == "Human" for _, y in pairs)
        only_a = sum(x["label"] == "Human" and y["label"] != "Human" for x, y in pairs)
        only_b = sum(y["label"] == "Human" and x["label"] != "Human" for x, y in pairs)
        from scipy.stats import binomtest
        return {"n": len(pairs), "mean_diff": round(statistics.mean(diff), 4), "ci95": _boot(diff),
                "p": _wilcoxon(diff), "human": [hx, hy], "mcnemar_p": binomtest(only_a, only_a + only_b).pvalue if only_a + only_b else 1.0,
                "median_share": [statistics.median(x["ai_share"] for x, _ in pairs), statistics.median(y["ai_share"] for _, y in pairs)]}

    prim, sec = contrast("C100", "C50"), contrast("S50", "C50")
    ps = sorted([("prim", prim["p"]), ("sec", sec["p"])], key=lambda x: x[1])
    adj = {ps[0][0]: min(1, ps[0][1] * 2), ps[1][0]: min(1, max(ps[0][1] * 2, ps[1][1]))}
    prim["p_holm"], sec["p_holm"] = adj["prim"], adj["sec"]
    d, (lo, hi) = prim["mean_diff"], prim["ci95"]
    if prim["p_holm"] < 0.05 and d < 0:
        band = "large content effect" if d <= -0.10 else "small content effect"
    elif prim["p_holm"] < 0.05 and d > 0:
        band = "content hurts"
    else:
        band = "no useful content effect" if lo > -0.10 else "inconclusive"
    smaug = sec["p_holm"] < 0.05 and sec["mean_diff"] <= -0.05
    cells = {}
    for cell in ("C100", "C50", "S50", "CAN"):
        cr = [r for r in rows if r["cell"] == cell]
        cells[cell] = {"n": len(cr), "labels": {k: sum(r["label"] == k for r in cr) for k in ("Human", "Mixed", "AI")},
                       "mean_share": round(statistics.mean(r["ai_share"] for r in cr), 4) if cr else None}
    res = {"cells": cells, "primary_C100_vs_C50": prim, "band": band, "secondary_S50_vs_C50": sec,
           "smaug_weights_for_R2": smaug,
           "canaries": {r["key"]: {"label": r["label"], "ai_share": r["ai_share"]} for r in rows if r["cell"] == "CAN"}}
    _merge("analysis", res)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"drafts": drafts, "prompts": prompts, "pick": pick, "analyze": analyze}.get(cmd, lambda: scanfiles(sys.argv[2]))()
