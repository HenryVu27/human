"""B37 (long-form gate 2a): can a better pick or the notes-first writer raise the per-window Human rate, cheaply?

Design doc docs/specs/2026-11-06-longform-program.md, amendment of 2026-11-06 11:16 CST. B36 found B30's rewriter
reads Human on 1 of 32 whole posts by unseen writers, because each 300-word stretch reads Human only about a third of
the time (red team: whole posts need about 0.8). Its leftover AI share tracks how much of Sonnet's post it copies, and
its pick rule (most supported claims) favoured the seed that copies more. Gate 2b (training at scale) waits on this.

Rules, fixed 2026-11-06 11:16 CST, before any B37 generation, pick or score.

Form checks (src/humanizer/checks/form.py, with tests): every candidate must pass check_form against its input
section (non-English runs, new code, new framing, header count, and post-opening restarts in sections after the
first). On B36's picked sections they flag the French text, the invented code and 7 of the 13 posts the red team found
restarting (10 of 84 sections); 150 of B36's 168 raw samples pass.

Development arms on test-A (already scanned by Pangram, so development only: no Pangram on any test-A text)
- C0: B36's pick (seeds 0 and 1, most supported claims), unchanged, the baseline.
- C1: copy-penalized pick over 4 seeds. Seeds 2 and 3 are generated exactly as B36's (experiments/modal/
  lf_rewrite_hf.py, B30 adapter, 4-bit, Guard, T 0.8, top-p 0.95, repetition penalty 1.05), batched 16. Every
  candidate gets B36's prune, repeat drop, cleanup and claim check against its input section. Eligible: passes the
  form checks, claim support (entailed / total) at least 0.90, and at least 50% of the section's words. Pick: the
  eligible candidate with the least copying from the input section (8-word runs); ties to more supported claims. If no
  candidate is eligible, the form-passing candidate with the most supported claims; if none passes the form checks,
  B36's pick, flagged.
- L: B28's notes-first voice writer (B26's adapter, OLMo-2-13B QLoRA on 630 essays) from the same 50% reworded notes D
  was written from, at full length: B25's facts prompt with the human post's word count (no 1,300-word cap), max new
  tokens min(1.95 x words + 64, room in 4,096), Guard over the notes, seeds 0 and 1. Prune, cleanup and claim check
  against the notes; pick among form-passing candidates by most supported claims (B28's rule).
- A context arm (carrying the previous section's text) is not run: it needs pick-then-generate rounds per section,
  and the restart check now rejects detected restarts at pick time instead.

Development judge: MELD per-window rate (B33: the only open detector that agrees with Pangram in every stratum)
- Windows: each text is cut into consecutive windows of about 300 words at sentence ends (a window closes at the first
  sentence end at or after 280 words; a last window under 150 words joins the previous one).
- Reference, label-free: windows of 100 B32 pilot posts from the train split (site buckets 0 to 74, ordered by
  sha256("b37-ref:" + id)). T is the 95th percentile of their MELD scores. A window is human-like if its score is at or
  below T.
- Per arm: the share of human-like windows (the per-window rate), the share of posts whose windows are all
  human-like, and the mean MELD window score. Paired by post: Wilcoxon signed-rank on each post's mean window score.
- Calibration, descriptive: the same measure on B36's scanned 300-word texts (C300, D300, H300) beside their Pangram
  labels shows how MELD's rate maps to Pangram's (B36: Pangram's per-window Human rate for C was about 0.34).

Pangram decision rule (at most 800 credits for gate 2a; dashboard 9,634 before)
- An arm qualifies for a Pangram test if, against C0 on test-A: its per-window rate is at least 0.10 higher, its
  paired mean window score is lower (Wilcoxon p below 0.05), claim support is 0.90 or more, at least 95% of its
  sections (whole texts for L) pass the form checks, and its length is at least 70% of D (C arms) or 60% of the human
  post (L).
- If one or more qualify, the best (highest per-window rate) is tested on fresh test-B posts (site buckets 95 to 99,
  selected as B36's test-A with the same fixes, labels and an independent page-type audit, inputs as B36), paired with
  C0's rule on the same generations: both cells scanned in full and as 300-word prefixes, blinded. Primary: Wilcoxon
  on the paired full-length AI share; secondary: Human counts. n is the largest of 8 to 16 that the credits left after
  the Henry arm allow at about 40 credits per post.
- Henry arm, always (credits first): B30's rewriter on the prose sections of Henry's two published posts with C1's
  rule over seeds 0 to 3 (seeds 2 and 3 new), the same confidentiality filter as B36. LaTeX (inline and display math,
  backslash commands) is stripped from originals and rewrites alike before scanning. Scanned the same day: every
  original section of 150 words or more, every rewritten section of 150 words or more, and both whole posts, original
  and rewritten. Analysis: sign test on sections (label order AI < Mixed < Human), whole-post labels and AI shares.
- Splice probe, only if at least 150 credits remain: human posts with a Sonnet block of known size and position, to
  measure how Pangram aggregates windows; its rules are added by amendment before it is built.
- Prediction: C1 raises the per-window rate modestly (copying is one of two drivers) but not to Pangram's 0.8; L's rate
  is higher than C0's at the cost of length.

Usage:
  uv run python experiments/b37_gate2a.py prompts
  modal run experiments/modal/lf_rewrite_hf.py --prompts results/b36_prompts.jsonl --out results/b37_gen.jsonl --seeds 2,3 --batch 16
  modal run experiments/modal/lf_rewrite_hf.py --prompts results/b37_prompts_L.jsonl --out results/b37_gen_L.jsonl --seeds 0,1 --adapter b26-essaypool --batch 16
  uv run python experiments/b37_gate2a.py pick
  uv run python experiments/b37_gate2a.py meld_inputs
  modal run experiments/modal/lf_detect.py::score --inp results/b37_meld_inputs.jsonl --out results/b37_meld_scores.jsonl --only meld
  uv run python experiments/b37_gate2a.py dev
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.copying import copied_share
from humanizer.checks.form import check_form
from humanizer.data.facts import Facts, facts_prompt

sys.path.insert(0, str(ROOT / "experiments"))
from b11_prune import prune_one  # noqa: E402
from b13_cleanup import clean_one  # noqa: E402
from b24_cited import _drop_repeats  # noqa: E402
from b25_blog import voice  # noqa: E402
from b36_transfer import HENRY_POSTS, confidential, henry_sections  # noqa: E402

RES = ROOT / "results"
CONTEXT = 4096
PROMPTS_L = RES / "b37_prompts_L.jsonl"
GEN_C = [RES / "b36_gen.jsonl", RES / "b37_gen.jsonl"]
GEN_L = RES / "b37_gen_L.jsonl"
TEXTS = RES / "b37_texts.jsonl"
OUT = RES / "b37_gate2a.json"
MELD_IN = RES / "b37_meld_inputs.jsonl"
MELD_OUT = RES / "b37_meld_scores.jsonl"


def _load(p):
    return [json.loads(line) for line in p.open()] if p.exists() else []


def prompts():
    rows = []
    for r in _load(RES / "b36_inputs.jsonl"):
        f = Facts(r["title"], r["dose50"])
        prompt = facts_prompt(f, r["words"], f"b25{r['id']}")
        room = CONTEXT - int(len(prompt.split()) * 1.5) - 32
        rows.append({"id": f"L_{r['id']}", "doc": r["id"], "arm": "L", "prompt": prompt,
                     "allowed_text": "\n".join(r["dose50"]), "target_words": int(round(r["words"], -1)),
                     "max_new_tokens": min(int(r["words"] * 1.95) + 64, room)})
    PROMPTS_L.write_text("".join(json.dumps(x) + "\n" for x in rows))
    print(len(rows), "L prompts; max_new_tokens", min(x["max_new_tokens"] for x in rows), "to",
          max(x["max_new_tokens"] for x in rows))


def _assess(g: dict, p: dict) -> dict:
    """B36's prune, repeat drop, cleanup and claim check, plus the form checks and copying, for one candidate."""
    src = p["allowed_text"]
    text, dropped = confidential(g["text"], src) if p.get("arm") == "HR" else (g["text"], 0)
    pruned, _ = prune_one(text, src)
    cleaned, _ = clean_one(_drop_repeats(pruned))
    cc = claim_check(src, cleaned)
    form = check_form(cleaned, src, later_section=p.get("part", 0) > 0 and p.get("arm") != "L")
    return {"id": g["id"], "seed": g["seed"], "text": cleaned, "words": len(cleaned.split()),
            "claims_entailed": cc["claims_entailed"], "claims_total": cc["claims_total"],
            "support": cc["claims_entailed"] / max(1, cc["claims_total"]), "form_ok": form["ok"],
            "form": {k: v for k, v in form.items() if k != "ok" and v}, "copied": copied_share(cleaned, src),
            "confidential_dropped": dropped}


def _pick_c1(cands: list[dict], words_in: int) -> tuple[dict, str]:
    elig = [c for c in cands if c["form_ok"] and c["support"] >= 0.90 and c["words"] >= 0.5 * words_in]
    if elig:
        return min(elig, key=lambda c: (c["copied"], -c["claims_entailed"])), "eligible"
    ok = [c for c in cands if c["form_ok"]]
    if ok:
        return max(ok, key=lambda c: (c["claims_entailed"], c["support"])), "form_only"
    return None, "none"


def pick():
    prm = {p["id"]: p for p in _load(RES / "b36_prompts.jsonl")} | {p["id"]: p for p in _load(PROMPTS_L)}
    gens = [g for f in GEN_C for g in _load(f)] + _load(GEN_L)
    workers = int(os.environ.get("B37_WORKERS", "4"))
    with ThreadPoolExecutor(workers) as ex:
        assessed = list(ex.map(lambda g: _assess(g, prm[g["id"]]), gens))
    by: dict[str, list] = {}
    for a in assessed:
        by.setdefault(a["id"], []).append(a)
    b36 = {r["doc"]: r for r in _load(RES / "b36_texts.jsonl") if r["cell"] == "C"}
    inputs = {r["id"]: r for r in _load(RES / "b36_inputs.jsonl")}
    docs = {r["id"]: r for r in _load(RES / "b36_docs.jsonl")}
    texts, stats = [], {"C1_rule": {}, "L_rule": {}}
    for doc in inputs:
        parts = sorted((p for p in prm.values() if p.get("arm") == "C" and p["doc"] == doc), key=lambda p: p["part"])
        chosen = []
        for p in parts:
            c, how = _pick_c1(by.get(p["id"], []), p["words"])
            stats["C1_rule"][how] = stats["C1_rule"].get(how, 0) + 1
            if c is None:  # B36's pick, flagged
                c = next(x for x in by[p["id"]] if x["seed"] == b36[doc]["seeds"][p["part"]])
            chosen.append(c | {"part": p["part"], "rule": how})
        t = "\n\n".join(c["text"] for c in chosen)
        d, human = inputs[doc]["D"], docs[doc]["text"]
        texts.append({"id": f"C1_{doc}", "cell": "C1", "doc": doc, "text": t, "words": len(t.split()),
                      "D_words": len(d.split()), "human_words": docs[doc]["words"],
                      "claims_entailed": sum(c["claims_entailed"] for c in chosen),
                      "claims_total": sum(c["claims_total"] for c in chosen),
                      "sections_form_ok": sum(c["form_ok"] for c in chosen), "sections": len(chosen),
                      "copied_from_D": copied_share(t, d), "copied_from_human": copied_share(t, human),
                      "seeds": [c["seed"] for c in chosen], "rules": [c["rule"] for c in chosen], "voice": voice(t)})
        c0 = b36[doc]
        c0_form = [check_form(next(x for x in by[p["id"]] if x["seed"] == c0["seeds"][p["part"]])["text"],
                              p["allowed_text"], later_section=p["part"] > 0)["ok"] for p in parts]
        texts.append({"id": f"C0_{doc}", "cell": "C0", "doc": doc, "text": c0["text"], "words": c0["words"],
                      "D_words": c0["D_words"], "human_words": c0["human_words"], "claims_entailed": c0["claims_entailed"],
                      "claims_total": c0["claims_total"], "sections_form_ok": sum(c0_form), "sections": len(parts),
                      "copied_from_D": c0["copied_from_D"], "copied_from_human": c0["copied_from_human"],
                      "seeds": c0["seeds"], "voice": c0["voice"]})
        lc = [c for c in by.get(f"L_{doc}", []) if c["form_ok"]]
        lpick = max(lc, key=lambda c: (c["claims_entailed"], c["support"])) if lc else None
        stats["L_rule"]["form_ok" if lpick else "none"] = stats["L_rule"].get("form_ok" if lpick else "none", 0) + 1
        if lpick is None and by.get(f"L_{doc}"):
            lpick = max(by[f"L_{doc}"], key=lambda c: (c["claims_entailed"], c["support"])) | {"flag": "form"}
        if lpick:
            texts.append({"id": f"L_{doc}", "cell": "L", "doc": doc, "text": lpick["text"], "words": lpick["words"],
                          "D_words": len(d.split()), "human_words": docs[doc]["words"],
                          "claims_entailed": lpick["claims_entailed"], "claims_total": lpick["claims_total"],
                          "sections_form_ok": int(lpick["form_ok"]), "sections": 1,
                          "copied_from_D": copied_share(lpick["text"], d),
                          "copied_from_human": copied_share(lpick["text"], human), "seeds": [lpick["seed"]],
                          "voice": voice(lpick["text"])})
    for post, path in HENRY_POSTS.items():
        secs = henry_sections(path)
        parts = sorted((p for p in prm.values() if p.get("arm") == "HR" and p["doc"] == post), key=lambda p: p["part"])
        by_sec: dict[int, list] = {}
        for p in parts:
            c, how = _pick_c1(by.get(p["id"], []), p["words"])
            if c is None:
                c = max(by[p["id"]], key=lambda x: x["claims_entailed"])
            by_sec.setdefault(p["section"], []).append(c)
        for si, cs in sorted(by_sec.items()):
            t = "\n".join(c["text"] for c in cs)
            texts.append({"id": f"HR1_{post}_s{si}", "cell": "HR1_sec", "doc": post, "section": si, "text": t,
                          "words": len(t.split()), "original": secs[si - 1]["text"],
                          "claims_entailed": sum(c["claims_entailed"] for c in cs),
                          "claims_total": sum(c["claims_total"] for c in cs),
                          "form_ok": all(c["form_ok"] for c in cs),
                          "confidential_dropped": sum(c["confidential_dropped"] for c in cs),
                          "copied_from_original": copied_share(t, secs[si - 1]["text"])})
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in texts))
    summ = {"rules": stats}
    for cell in ("C0", "C1", "L"):
        cr = [r for r in texts if r["cell"] == cell]
        if not cr:
            continue
        summ[cell] = {"texts": len(cr), "words": statistics.mean(r["words"] for r in cr),
                      "over_D": statistics.mean(r["words"] / r["D_words"] for r in cr),
                      "over_human": statistics.mean(r["words"] / r["human_words"] for r in cr),
                      "claim_support": statistics.mean(r["claims_entailed"] / max(1, r["claims_total"]) for r in cr),
                      "sections_form_ok": sum(r["sections_form_ok"] for r in cr) / sum(r["sections"] for r in cr),
                      "copied_from_D": statistics.mean(r["copied_from_D"] for r in cr),
                      "copied_from_human": statistics.mean(r["copied_from_human"] for r in cr),
                      "max_copied_from_human": max(r["copied_from_human"] for r in cr)}
    hr = [r for r in texts if r["cell"] == "HR1_sec"]
    summ["HR1"] = {"sections": len(hr), "form_ok": sum(r["form_ok"] for r in hr),
                   "claim_support": sum(r["claims_entailed"] for r in hr) / max(1, sum(r["claims_total"] for r in hr)),
                   "confidential_dropped": sum(r["confidential_dropped"] for r in hr),
                   "copied_from_original": statistics.mean(r["copied_from_original"] for r in hr) if hr else None}
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {"pick": summ}, indent=1))
    print(json.dumps(summ, indent=1))


SENT_END = re.compile(r"[.!?][\"')\]]?(?=\s|$)")


def windows(text: str, size: int = 280, tail: int = 150) -> list[str]:
    words = text.split()
    out, start = [], 0
    joined = " ".join(words)
    pos = [m.end() for m in SENT_END.finditer(joined)]
    cuts, count = [], 0
    for e in pos:
        n = len(joined[:e].split())
        if n - count >= size:
            cuts.append(n)
            count = n
    bounds = [0] + cuts + ([len(words)] if not cuts or cuts[-1] < len(words) else [])
    for a, b in zip(bounds, bounds[1:]):
        out.append(" ".join(words[a:b]))
    if len(out) > 1 and len(out[-1].split()) < tail:
        out[-2] = out[-2] + " " + out.pop()
    return [w for w in out if w.strip()]


def meld_inputs():
    rows = []
    for r in _load(TEXTS):
        if r["cell"] in ("C0", "C1", "L"):
            for k, w in enumerate(windows(r["text"])):
                rows.append({"id": f"{r['id']}#w{k}", "text": w})
    full = RES / "b32_pilot_full.jsonl"
    ref = []
    for line in full.open():
        r = json.loads(line)
        b = int(hashlib.sha256(f"b32-split-v1:{r['site']}".encode()).hexdigest(), 16) % 100
        if b < 75 and not r.get("prior_site"):
            ref.append(r)
    ref.sort(key=lambda r: hashlib.sha256(f"b37-ref:{r['id']}".encode()).hexdigest())
    for r in ref[:100]:
        for k, w in enumerate(windows(r["text"])):
            rows.append({"id": f"REF_{r['id']}#w{k}", "text": w})
    blind = json.loads((RES / "b36_blind.json").read_text())
    scanned = {v["key"]: v for v in blind.values()}
    from b36_transfer import scan_texts  # the exact texts scanned in B36
    for t in scan_texts():
        if t["cell"] in ("C300", "D300", "H300"):
            rows.append({"id": f"CAL_{t['key']}", "text": t["text"]})
    MELD_IN.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "windows;", sum(r["id"].startswith("REF_") for r in rows), "reference;",
          sum(r["id"].startswith("CAL_") for r in rows), "calibration;", len(scanned), "B36 scanned keys")


def dev():
    from scipy.stats import wilcoxon

    sc = {r["id"]: r["meld"]["score"] for r in _load(MELD_OUT) if r.get("meld")}
    ref = sorted(v for k, v in sc.items() if k.startswith("REF_"))
    T = ref[int(0.95 * (len(ref) - 1))]
    per: dict[str, dict[str, list]] = {}
    for k, v in sc.items():
        if k.startswith(("REF_", "CAL_")):
            continue
        tid, _ = k.split("#w")
        cell, doc = tid.split("_", 1)
        per.setdefault(cell, {}).setdefault(doc, []).append(v)
    res = {"threshold_T": round(T, 3), "reference_windows": len(ref), "arms": {}}
    for cell, d in per.items():
        allw = [x for v in d.values() for x in v]
        res["arms"][cell] = {"posts": len(d), "windows": len(allw),
                             "per_window_rate": round(sum(x <= T for x in allw) / len(allw), 3),
                             "posts_all_windows": sum(all(x <= T for x in v) for v in d.values()),
                             "mean_window_score": round(statistics.mean(allw), 3)}
    for cell in ("C1", "L"):
        if cell in per and "C0" in per:
            docs = sorted(set(per[cell]) & set(per["C0"]))
            diffs = [statistics.mean(per[cell][x]) - statistics.mean(per["C0"][x]) for x in docs]
            res["arms"][cell]["vs_C0"] = {"pairs": len(docs), "mean_score_diff": round(statistics.mean(diffs), 3),
                                          "p_wilcoxon": round(float(wilcoxon(diffs).pvalue), 6),
                                          "rate_diff": round(res["arms"][cell]["per_window_rate"]
                                                             - res["arms"]["C0"]["per_window_rate"], 3)}
    pang = {r["key"]: r for r in _load(RES / "b36_pangram.jsonl")}
    cal = {}
    for k, v in sc.items():
        if k.startswith("CAL_"):
            key = k[4:]
            cell = key.split("_")[0]
            lab = pang[key]["label"] if key in pang else None
            cal.setdefault(cell, []).append((v <= T, lab == "Human"))
    res["calibration"] = {c: {"n": len(v), "meld_human_like": sum(a for a, _ in v), "pangram_human": sum(b for _, b in v),
                              "agree": sum(a == b for a, b in v)} for c, v in cal.items()}
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {"dev": res}, indent=1))
    print(json.dumps(res, indent=1))


# ------------------------------------------------------------------------------------------- Pangram: Henry arm

MATH_DISPLAY = re.compile(r"\$\$.+?\$\$|\\\[.+?\\\]", re.S)
MATH_INLINE = re.compile(r"\\\((.+?)\\\)|\$([^$\n]{1,120}?)\$")
BLIND = RES / "b37_blind.json"
PANGRAM = RES / "b37_pangram.jsonl"


def strip_latex(text: str) -> str:
    """Delete math, never currency: display math always; an inline $...$ span only if it holds a LaTeX marker
    (backslash, ^, _, braces) or is a lone symbol ($K$, $t$, $O(n)$); bare backslash commands too."""
    t = MATH_DISPLAY.sub(" ", text)

    def inline(m):
        body = m.group(1) if m.group(1) is not None else m.group(2)
        if m.group(1) is not None or re.search(r"[\\^_{}]", body) or re.fullmatch(r"\s*[A-Za-z](\([^)]*\))?\s*", body):
            return " "
        return m.group(0)

    t = MATH_INLINE.sub(inline, t)
    t = re.sub(r"\\[A-Za-z]+(\{[^}]*\})?", " ", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return re.sub(r" +([.,;:])", r"\1", t).strip()


def henry_texts() -> list[dict]:
    """Same-day Henry arm: originals and C1-rule rewrites, LaTeX stripped from both."""
    out = []
    hr = {(r["doc"], r["section"]): r for r in _load(TEXTS) if r["cell"] == "HR1_sec"}
    for post, path in HENRY_POSTS.items():
        secs = henry_sections(path)
        o_all, r_all = [], []
        for si, sec in enumerate(secs, 1):
            o = strip_latex(sec["text"])
            o_all.append(o)
            if len(o.split()) >= 150:
                out.append({"key": f"HO2_{post}_s{si}", "cell": "HO2_sec", "doc": f"{post}_s{si}", "text": o})
            if (post, si) in hr:
                r = strip_latex(hr[(post, si)]["text"])
                r_all.append(r)
                if len(r.split()) >= 150:
                    out.append({"key": f"HR2_{post}_s{si}", "cell": "HR2_sec", "doc": f"{post}_s{si}", "text": r})
        out.append({"key": f"HO2_{post}", "cell": "HO2_post", "doc": post, "text": "\n\n".join(o_all)})
        out.append({"key": f"HR2_{post}", "cell": "HR2_post", "doc": post, "text": "\n\n".join(r_all)})
    return out


def scanfiles(dest: str):
    import math
    import random
    import subprocess
    from pathlib import Path

    texts = henry_texts() + _load(RES / "b37_testb_scan.jsonl")
    for t in texts:
        t["words"] = len(t["text"].split())
    credits = sum(math.ceil(1.15 * t["words"] / 100) for t in texts)  # Pangram counts about 15% more words than we do
    print(len(texts), "texts, about", credits, "credits")
    if credits > 800:
        sys.exit("over gate 2a's 800 credits; stop")
    rng = random.Random("b37")
    rng.shuffle(texts)
    keymap, used = {}, set()
    for i, t in enumerate(texts):
        name = rng.randbytes(4).hex()
        while name in used:
            name = rng.randbytes(4).hex()
        used.add(name)
        sub = Path(dest) / f"batch{i // 100:02d}"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / f"{name}.txt").write_text(t["text"] + "\n")
        subprocess.run(["textutil", "-convert", "docx", str(sub / f"{name}.txt")], check=True)
        (sub / f"{name}.txt").unlink()
        keymap[name] = {"key": t["key"], "cell": t["cell"], "doc": t["doc"], "words": t["words"], "batch": i // 100}
    BLIND.write_text(json.dumps(keymap, indent=1))


def record(path: str):
    keymap = json.loads(BLIND.read_text())
    rows = [json.loads(line) for line in open(path) if line.strip()]
    PANGRAM.write_text("".join(json.dumps(keymap[r["name"]] | r) + "\n" for r in rows))
    print(len(rows), "verdicts of", len(keymap))


def analyze():
    from scipy.stats import binomtest

    rows = {r["key"]: r for r in _load(PANGRAM)}
    order = {"AI": 0, "Mixed": 1, "Human": 2}
    secs = sorted({r["doc"] for r in rows.values() if r["cell"] in ("HO2_sec", "HR2_sec")})
    pairs = [(rows.get(f"HO2_{d}"), rows.get(f"HR2_{d}")) for d in secs]
    pairs = [(o, r) for o, r in pairs if o and r]
    up = sum(order[r["label"]] > order[o["label"]] for o, r in pairs)
    down = sum(order[r["label"]] < order[o["label"]] for o, r in pairs)
    res = {"henry_sections": {"pairs": len(pairs), "better": up, "worse": down,
                              "p_sign": round(float(binomtest(up, up + down, 0.5).pvalue), 4) if up + down else 1.0,
                              "original_human": sum(o["label"] == "Human" for o, _ in pairs),
                              "rewrite_human": sum(r["label"] == "Human" for _, r in pairs),
                              "rows": {d: [o["label"], o["ai_share"], r["label"], r["ai_share"]]
                                       for d, (o, r) in zip(secs, pairs)}},
           "henry_posts": {k: [v["label"], v["ai_share"], v["words"]] for k, v in rows.items()
                           if v["cell"] in ("HO2_post", "HR2_post")}}
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {"pangram": res}, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd in ("scanfiles", "record"):
        {"scanfiles": scanfiles, "record": record}[cmd](sys.argv[2])
    else:
        {"prompts": prompts, "pick": pick, "meld_inputs": meld_inputs, "dev": dev, "analyze": analyze}[cmd]()
