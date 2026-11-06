"""B38: a local judge trained on the project's Pangram labels, to pick among rewrites and develop the rewriter.

Henry's decision (2026-11-06 13:08, CLAUDE.md commit f578571): "Yes, train it." Design doc amendment of 2026-11-06
13:10 CST. Gate 2a showed MELD ranks rewrites no better than chance against Pangram (AUROC 0.55) while the tries of one
section differ a lot on Pangram, so the program lacks a judge that tracks Pangram within rewrites.

Rules, fixed 2026-11-06 13:13 CST, before any judge is trained, any feature is scored, or any B38 text is generated.

Final test reserve: results/b39_reserved_testB.json (798 test-B posts by ID and text hash, committed a99a393). No step
here reads them; `data` and `calib_*` assert that none of their texts' source posts is reserved.

Data (step `data`, results/b38_data.jsonl, texts local)
- Every Pangram-labelled text from B1 to B37: the B33 calibration set (B1 to B31, deduplicated by text), B28's L and R
  cells, B30's T cells, B34's H cells, B36's 169 texts and B37's 48, each with label, AI share where the scan recorded
  it, words, experiment, cell, origin and a group key: the author for the 13 essayists, the site for FineWeb pages and
  pilot posts, "henry" for Henry's posts, and the base post's site for splices.
- Rewrites (the primary domain): texts written by the project's local writers and rewriters (B3 to B26 local-writer
  cells, B28 L and R, B30 T, B36 C300 and Cfull, B36 and B37 Henry rewrites).
- Target: Pangram's AI share where measured; otherwise a proxy from the label (Human 0.03, Mixed 0.40, AI 0.95). The
  binary outcome is not Human (Mixed or AI).
- Unit: the whole document, not windows. The B37 splice probe showed Pangram's share is the share of flagged words,
  added over the text; window-level training would have to give each window its document's share, which is wrong
  exactly where AI words cluster (a splice). A document-level judge sees each text whole up to 2,048 tokens; longer
  texts are scored as 2,048-token chunks whose predictions are averaged by tokens, which matches the additive reading.

Within-section candidate labels (steps `calib_*`, the only new Pangram labels)
- Posts: the 4 calibration-split posts (site buckets 75 to 79) that were labelled single-author personal or technical
  posts in B36's selection but not used by B34: p3f93342833, pdcbac3657f, p7dd69444fe, pf688f8ab80. Never test-A (now
  development) or test-B (reserved).
- Inputs as B36: Sonnet notes, rewording, the 50% dose, Sonnet's post D; D cut into sections as B36.
- Candidates: B30's rewriter, seeds 0 to 3 per section (experiments/modal/lf_rewrite_hf.py), each pruned, cleaned and
  claim-checked against its section, with the form checks recorded. Every candidate is scanned, whatever its checks,
  so the judge can be tested on the full spread. Blinded, one shuffled batch with step 6's texts.
- These candidates are held out of all training and of the choice among judges: they test the chosen judge only.

Optional step 6, same batch: Henry's bandits post (prose sections as B15 extracts them) with the math kept and with
the math stripped (B37's strip_latex), scanned the same day. The context-engineering post has almost no math and is
not rescanned. Pangram: at most 600 credits in all; the scan script stops above that.

Evaluation, fixed now
- Splits: 5 folds grouped by the group key (no author, site or Henry post in two folds); a leave-one-experiment-out
  split trains without B36 and B37 and tests on them.
- Primary metrics, on rewrites, from out-of-fold predictions: AUROC for not Human against Human; Spearman correlation
  with the AI share (rows with a measured share). On the calibration candidates: within-section pairwise pick accuracy
  (pairs whose Pangram shares differ by more than 0.05; the share the judge predicts lower should be lower), and the
  Pangram share of the judge's best-of-4 pick against the mean of the section's four (a random pick) and the best of
  four (an oracle).
- Bar: a judge clears it if its out-of-fold AUROC on rewrites is at least 0.70.
- Choice among judges: the highest out-of-fold AUROC on rewrites; a judge within 0.02 of the best that is simpler (the
  linear model) wins. Nothing on the calibration candidates or the leave-one-experiment-out split enters the choice.
- Proxy exploitation: on the calibration candidates, the mean gap between the chosen judge's predicted share of its
  picks and their Pangram share, against the same gap over all candidates.

Candidate judges
- J1: logistic regression (Human against not Human; class weights balanced; C = 1) on the open detectors' scores
  (MELD, Binoculars, Fast-DetectGPT on the Falcon pair and on Llama 3.1 8B, desklib; lf_detect.py, unchanged) and log
  words, standardized.
- J2: ModernBERT-base (answerdotai/ModernBERT-base) fine-tuned to regress the target share (sigmoid output, mean squared
  error), trained on the first 2,048 tokens, 3 epochs, learning rate 3e-5, batches of 8 texts of similar length, one
  seed; experiments/modal/lf_judge.py.

Use, if a judge clears the bar: best-of-4 on the calibration candidates with the chosen judge, reporting its Pangram
outcome and the proxy gap above. No other use of the calibration candidates.

Usage:
  uv run python experiments/b38_judge.py data
  uv run python experiments/b38_judge.py calib_inputs
  uv run python experiments/b38_judge.py calib_prompts
  modal run experiments/modal/lf_rewrite_hf.py --prompts results/b38_calib_prompts.jsonl --out results/b38_calib_gen.jsonl --seeds 0,1,2,3 --batch 8
  uv run python experiments/b38_judge.py calib_assess
  uv run python experiments/b38_judge.py scanfiles DIR ; record FILE
  uv run python experiments/b38_judge.py features
  modal run experiments/modal/lf_detect.py::score --inp results/b38_det_inputs.jsonl --out results/b38_det_scores.jsonl
  uv run python experiments/b38_judge.py linear
  modal run experiments/modal/lf_judge.py --data results/b38_data.jsonl --calib results/b38_calib_cands.jsonl --out results/b38_j2_preds.json
  uv run python experiments/b38_judge.py evaluate
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.copying import copied_share
from humanizer.checks.form import check_form
from humanizer.data.facts import parse_facts
from humanizer.llm import claude_many

sys.path.insert(0, str(ROOT / "experiments"))
from b11_prune import prune_one  # noqa: E402
from b13_cleanup import clean_one  # noqa: E402
from b24_cited import _drop_repeats  # noqa: E402
from b25_blog import DRAFT, NOTES, plain  # noqa: E402
from b27_reworded import reword_all  # noqa: E402
from b36_transfer import HENRY_POSTS, _prompt_row, dose, henry_sections, scan_texts, sections  # noqa: E402

RES = ROOT / "results"
DATA = RES / "b38_data.jsonl"
CAL_IN = RES / "b38_calib_inputs.jsonl"
CAL_PROMPTS = RES / "b38_calib_prompts.jsonl"
CAL_GEN = RES / "b38_calib_gen.jsonl"
CANDS = RES / "b38_calib_cands.jsonl"
BLIND = RES / "b38_blind.json"
PANGRAM = RES / "b38_pangram.jsonl"
DET_IN = RES / "b38_det_inputs.jsonl"
DET_OUT = RES / "b38_det_scores.jsonl"
OUT = RES / "b38_judge.json"
CALIB_POSTS = ["p3f93342833", "pdcbac3657f", "p7dd69444fe", "pf688f8ab80"]
PROXY = {"Human": 0.03, "Mixed": 0.40, "AI": 0.95}
REWRITE_CELLS = {"C300", "Cfull", "HR_post", "HR_sec", "HR2_post", "HR2_sec"}


def _load(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.open()] if p.exists() else []


def _reserved() -> set[str]:
    return set(json.loads((RES / "b39_reserved_testB.json").read_text())["ids"])


def _site(url: str) -> str:
    from b36_transfer import core_name
    return core_name(url)


def data():
    reserved = _reserved()
    human = {r["id"]: r for r in _load(ROOT / "data" / "human.jsonl")}
    drafts = {r["id"]: r for r in _load(ROOT / "data" / "drafts" / "dev.jsonl")}
    essays = {r["id"]: r for r in _load(ROOT / "data" / "essays.jsonl")}
    pilot_ids = {}
    for f in ("b36_docs.jsonl", "b34_docs.jsonl"):
        for r in _load(RES / f):
            pilot_ids[r["id"]] = r

    def group(doc: str) -> str:
        if doc in essays:
            return "author:" + essays[doc]["author"]
        if doc in human:
            return "site:" + _site(human[doc]["url"])
        if doc in drafts and drafts[doc].get("source_id") in human:
            return "site:" + _site(human[drafts[doc]["source_id"]]["url"])
        if doc in pilot_ids:
            return "site:" + _site(pilot_ids[doc]["url"])
        if doc in ("aieng", "bandits") or doc.startswith(("aieng", "bandits")) or doc in {"s1", "s2", "s3", "s4", "s5", "s6", "s7"}:
            return "henry"
        return "doc:" + doc

    rows, seen = [], set()

    def add(exp, cell, doc, text, label, share, origin, rewrite):
        if not text or text in seen:
            return
        seen.add(text)
        assert doc not in reserved, doc
        rows.append({"uid": f"{exp}:{cell}:{doc}:{len(rows)}", "exp": exp, "cell": cell, "doc": doc, "text": text,
                     "label": label, "ai_share": share, "target": share if share is not None else PROXY[label],
                     "words": len(text.split()), "origin": origin, "group": group(doc), "rewrite": rewrite,
                     "loeo_test": exp in ("B36", "B37")})

    for r in _load(RES / "b33_calib.jsonl"):
        doc = r["id"].split(":")[-1]
        if r["exp"] in ("B15", "B17"):
            doc = "henry_" + doc
        add(r["exp"], r["cell"], doc, r["text"], r["label"], r["ai_share"], r["origin"], r["origin"] == "local_writer")
    for r in _load(RES / "b33_calib.jsonl"):
        pass
    b28 = json.loads((RES / "b28_dose.json").read_text())["pangram"]
    for r in _load(RES / "b28_texts.jsonl"):
        if r["id"] in b28:
            add("B28", r["cell"], r["source"], r["text"], b28[r["id"]], None, "local_writer", True)
    b30 = json.loads((RES / "b30_rewriter.json").read_text())["pangram"]
    for r in _load(RES / "b30_texts.jsonl"):
        if r["id"] in b30:
            add("B30", r["cell"], r["source"], r["text"], b30[r["id"]], None, "local_writer", True)
    texts36 = {t["key"]: t for t in scan_texts()}
    for r in _load(RES / "b36_pangram.jsonl"):
        t = texts36[r["key"]]
        exp = "B34" if r["cell"] in ("H300", "Hfull") else "B36"
        origin = {"D300": "instruct", "Dfull": "instruct", "H300": "human", "Hfull": "human", "HO_post": "henry_original",
                  "HO_sec": "henry_original"}.get(r["cell"], "local_writer")
        doc = r["doc"] if not r["cell"].startswith("H") or r["cell"] in ("H300", "Hfull") else "henry_" + r["key"]
        add(exp, r["cell"], doc, t["text"], r["label"], r["ai_share"], origin, r["cell"] in REWRITE_CELLS)
    sys.path.insert(0, str(ROOT / "experiments"))
    from b37_gate2a import henry_texts
    t37 = {t["key"]: t for t in henry_texts()} | {t["key"]: t for t in _load(RES / "b37_splice_scan.jsonl")}
    for r in _load(RES / "b37_pangram.jsonl"):
        t = t37[r["key"]]
        origin = "splice" if r["cell"] == "SP" else ("henry_original" if r["cell"].startswith("HO") else "local_writer")
        doc = r["doc"] if r["cell"] == "SP" else "henry_" + r["key"]
        add("B37", r["cell"], doc, t["text"], r["label"], r["ai_share"], origin, r["cell"] in REWRITE_CELLS)
    for r in rows:
        if r["doc"].startswith("henry"):
            r["group"] = "henry"
    DATA.write_text("".join(json.dumps(r) + "\n" for r in rows))
    summ = {"rows": len(rows), "rewrites": sum(r["rewrite"] for r in rows),
            "rewrites_not_human": sum(r["rewrite"] and r["label"] != "Human" for r in rows),
            "with_share": sum(r["ai_share"] is not None for r in rows), "groups": len({r["group"] for r in rows}),
            "by_exp": {e: sum(r["exp"] == e for r in rows) for e in sorted({r["exp"] for r in rows})}}
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {"data": summ}, indent=1))
    print(json.dumps(summ, indent=1))


# ------------------------------------------------------------------------------- calibration candidates

def calib_inputs():
    reserved = _reserved()
    docs = {}
    for line in (RES / "b32_pilot_full.jsonl").open():
        r = json.loads(line)
        if r["id"] in CALIB_POSTS:
            docs[r["id"]] = r
    assert not set(docs) & reserved
    order = [docs[i] for i in CALIB_POSTS]
    raws = claude_many([NOTES.format(text=d["text"]) for d in order], model="sonnet")
    parsed = [parse_facts(x) for x in raws]
    reworded, kept = reword_all([p.facts for p in parsed])
    halves = [dose(w, d["id"]) for d, w in zip(order, reworded)]
    posts = claude_many([DRAFT.format(title=p.topic, words=int(round(d["words"], -1)),
                                      notes="\n".join(f"- {x}" for x in h)) for d, p, h in zip(order, parsed, halves)],
                        model="sonnet")
    rows = [{"id": d["id"], "site": d["site"], "words": d["words"], "title": p.topic, "dose50": h, "D": plain(post),
             "human": d["text"]} for d, p, h, post in zip(order, parsed, halves, posts)]
    CAL_IN.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print([(r["id"], len(r["D"].split())) for r in rows])


def calib_prompts():
    rows = []
    for r in _load(CAL_IN):
        for k, s in enumerate(sections(r["D"])):
            rows.append(_prompt_row(f"K_{r['id']}_{k}", s) | {"doc": r["id"], "part": k, "arm": "C"})
    CAL_PROMPTS.write_text("".join(json.dumps(x) + "\n" for x in rows))
    print(len(rows), "sections")


def calib_assess():
    prm = {p["id"]: p for p in _load(CAL_PROMPTS)}
    gens = _load(CAL_GEN)

    def one(g):
        p = prm[g["id"]]
        pruned, _ = prune_one(g["text"], p["allowed_text"])
        cleaned, _ = clean_one(_drop_repeats(pruned))
        cc = claim_check(p["allowed_text"], cleaned)
        form = check_form(cleaned, p["allowed_text"], later_section=p["part"] > 0)
        return {"cid": f"{g['id']}_s{g['seed']}", "section": g["id"], "doc": p["doc"], "part": p["part"],
                "seed": g["seed"], "text": cleaned, "words": len(cleaned.split()), "input_words": p["words"],
                "claims_entailed": cc["claims_entailed"], "claims_total": cc["claims_total"], "form_ok": form["ok"],
                "copied_from_input": copied_share(cleaned, p["allowed_text"])}

    with ThreadPoolExecutor(int(os.environ.get("B38_WORKERS", "4"))) as ex:
        rows = list(ex.map(one, gens))
    CANDS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "candidates;", sum(r["form_ok"] for r in rows), "pass the form checks; words",
          round(statistics.mean(r["words"] for r in rows)))


def scanfiles(dest: str):
    from b37_gate2a import strip_latex

    texts = [{"key": c["cid"], "cell": "K", "doc": c["doc"], "text": c["text"]} for c in _load(CANDS)
             if len(c["text"].split()) >= 50]
    secs = henry_sections(HENRY_POSTS["bandits"])
    kept = "\n\n".join(s["text"] for s in secs)
    texts += [{"key": "M_bandits_kept", "cell": "M_kept", "doc": "bandits", "text": kept},
              {"key": "M_bandits_stripped", "cell": "M_stripped", "doc": "bandits", "text": strip_latex(kept)}]
    for t in texts:
        t["words"] = len(t["text"].split())
    credits = sum(math.ceil(1.3 * t["words"] / 100) for t in texts)  # Pangram counts up to 30% more words with math
    print(len(texts), "texts, about", credits, "credits")
    if credits > 600:
        sys.exit("over B38's 600 credits; stop")
    rng = random.Random("b38")
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
        keymap[name] = {"key": t["key"], "cell": t["cell"], "doc": t["doc"], "words": t["words"]}
    BLIND.write_text(json.dumps(keymap, indent=1))


def record(path: str):
    keymap = json.loads(BLIND.read_text())
    rows = [json.loads(line) for line in open(path) if line.strip()]
    PANGRAM.write_text("".join(json.dumps(keymap[r["name"]] | r) + "\n" for r in rows))
    print(len(rows), "verdicts of", len(keymap))


# --------------------------------------------------------------------------------------------- judges

DETS = ["meld", "binoculars", "fdg_falcon", "fdg_llama", "desklib"]


def _b33_scores_by_text() -> dict[str, dict]:
    """B33 already scored every B1 to B31 text with the same detectors (lf_detect.py, unchanged); reuse by text."""
    calib = {r["id"]: r["text"] for r in _load(RES / "b33_calib.jsonl")}
    return {calib[r["id"]]: r for r in _load(RES / "b33_scores_calib.jsonl") if r["id"] in calib}


def features():
    have = _b33_scores_by_text()
    rows = [{"id": r["uid"], "text": r["text"]} for r in _load(DATA) if r["text"] not in have] + \
           [{"id": "CAND:" + c["cid"], "text": c["text"]} for c in _load(CANDS)]
    DET_IN.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "texts to score;", len(have), "reused from B33")


def _scores() -> dict[str, dict]:
    by_text = _b33_scores_by_text()
    sc = {r["id"]: r for r in _load(DET_OUT)}
    for r in _load(DATA):
        if r["uid"] not in sc and r["text"] in by_text:
            sc[r["uid"]] = by_text[r["text"]]
    return sc


def _feat(score_row: dict, words: int):
    v = [score_row.get(d, {}).get("ai") if score_row.get(d) else None for d in DETS]
    if any(x is None for x in v):
        return None
    return v + [math.log(max(words, 1))]


def _folds(rows: list[dict], k: int = 5) -> dict[str, int]:
    groups = sorted({r["group"] for r in rows}, key=lambda g: hashlib.sha256(f"b38-fold:{g}".encode()).hexdigest())
    sizes = {g: sum(r["group"] == g for r in rows) for g in groups}
    load, out = [0] * k, {}
    for g in sorted(groups, key=lambda g: -sizes[g]):
        f = min(range(k), key=lambda i: load[i])
        out[g] = f
        load[f] += sizes[g]
    return out


def linear():
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    sc = _scores()
    rows = [r for r in _load(DATA) if r["uid"] in sc and _feat(sc[r["uid"]], r["words"])]
    X = np.array([_feat(sc[r["uid"]], r["words"]) for r in rows])
    y = np.array([r["label"] != "Human" for r in rows], dtype=int)
    fold = _folds(rows)
    oof = np.zeros(len(rows))
    model = lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000))
    for f in range(5):
        tr = np.array([fold[r["group"]] != f for r in rows])
        m = model().fit(X[tr], y[tr])
        oof[~tr] = m.predict_proba(X[~tr])[:, 1]
    lo_tr = np.array([not r["loeo_test"] for r in rows])
    m = model().fit(X[lo_tr], y[lo_tr])
    loeo = m.predict_proba(X)[:, 1]
    full = model().fit(X, y)
    cands = [c for c in _load(CANDS) if "CAND:" + c["cid"] in sc]
    cand_pred = {c["cid"]: float(full.predict_proba(np.array([_feat(sc["CAND:" + c["cid"]], c["words"])]))[0, 1])
                 for c in cands if _feat(sc["CAND:" + c["cid"]], c["words"])}
    out = {"oof": {r["uid"]: float(p) for r, p in zip(rows, oof)},
           "loeo": {r["uid"]: float(p) for r, p in zip(rows, loeo) if r["loeo_test"]}, "calib": cand_pred,
           "folds": {r["uid"]: fold[r["group"]] for r in rows}}
    (RES / "b38_j1_preds.json").write_text(json.dumps(out))
    print("J1:", len(rows), "rows,", len(cand_pred), "candidates scored")


def _auroc(s, y):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, s)) if 0 < sum(y) < len(y) else None


def _metrics(pred: dict, rows: list[dict]) -> dict:
    from scipy.stats import spearmanr

    rr = [r for r in rows if r["uid"] in pred]
    out = {}
    for name, sub in (("rewrites", [r for r in rr if r["rewrite"]]), ("all", rr)):
        y = [int(r["label"] != "Human") for r in sub]
        s = [pred[r["uid"]] for r in sub]
        sh = [(pred[r["uid"]], r["ai_share"]) for r in sub if r["ai_share"] is not None]
        out[name] = {"n": len(sub), "not_human": sum(y), "auroc": _auroc(s, y),
                     "spearman_share": float(spearmanr([a for a, _ in sh], [b for _, b in sh]).statistic) if len(sh) > 5 else None,
                     "n_share": len(sh)}
    return out


def _pick_metrics(pred: dict) -> dict:
    pang = {r["key"]: r for r in _load(PANGRAM) if r["cell"] == "K"}
    cands = [c for c in _load(CANDS) if c["cid"] in pang and c["cid"] in pred]
    by = {}
    for c in cands:
        by.setdefault(c["section"], []).append(c)
    pairs = right = 0
    picked, rand, oracle, gaps_pick, gaps_all = [], [], [], [], []
    for sec, cs in by.items():
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                a, b = pang[cs[i]["cid"]]["ai_share"], pang[cs[j]["cid"]]["ai_share"]
                if abs(a - b) > 0.05:
                    pairs += 1
                    right += (pred[cs[i]["cid"]] < pred[cs[j]["cid"]]) == (a < b)
        if len(cs) < 2:
            continue
        best = min(cs, key=lambda c: pred[c["cid"]])
        picked.append(pang[best["cid"]]["ai_share"])
        rand.append(statistics.mean(pang[c["cid"]]["ai_share"] for c in cs))
        oracle.append(min(pang[c["cid"]]["ai_share"] for c in cs))
        gaps_pick.append(pred[best["cid"]] - pang[best["cid"]]["ai_share"])
        gaps_all += [pred[c["cid"]] - pang[c["cid"]]["ai_share"] for c in cs]
    return {"sections": len(picked), "pairs": pairs, "pair_accuracy": right / pairs if pairs else None,
            "best_of_4_share": statistics.mean(picked) if picked else None,
            "random_share": statistics.mean(rand) if rand else None,
            "oracle_share": statistics.mean(oracle) if oracle else None,
            "pred_minus_pangram_on_picks": statistics.mean(gaps_pick) if gaps_pick else None,
            "pred_minus_pangram_all": statistics.mean(gaps_all) if gaps_all else None}


def _post_metrics(pred: dict) -> dict:
    """Added 13:42, after the scan, to summarise the same picks per post; no rule changes. A whole post's share is the
    word-weighted mean of its sections' shares (B37: Pangram adds up flagged words). Random is the exact expectation over
    every combination of one scanned candidate per section; the oracle takes each section's lowest share, as in
    _pick_metrics; the label reading is Human under 0.10, AI from 0.80."""
    import itertools

    pang = {r["key"]: r for r in _load(PANGRAM) if r["cell"] == "K"}
    cands = [c for c in _load(CANDS) if c["cid"] in pang and c["cid"] in pred]
    out = {}
    for doc in CALIB_POSTS:
        secs = {}
        for c in cands:
            if c["doc"] == doc:
                secs.setdefault(c["section"], []).append(c)
        secs = [secs[k] for k in sorted(secs)]

        def share(pick):
            return sum(pang[c["cid"]]["ai_share"] * c["words"] for c in pick) / sum(c["words"] for c in pick)

        combos = [share(p) for p in itertools.product(*secs)]
        pick = share([min(cs, key=lambda c: pred[c["cid"]]) for cs in secs])
        orc = share([min(cs, key=lambda c: pang[c["cid"]]["ai_share"]) for cs in secs])
        out[doc] = {"sections": len(secs), "judge_pick": round(pick, 3), "random": round(statistics.mean(combos), 3),
                    "oracle": round(orc, 3), "judge_reads_human": pick < 0.10,
                    "random_p_human": round(sum(s < 0.10 for s in combos) / len(combos), 3),
                    "oracle_reads_human": orc < 0.10}
    return out


def evaluate():
    rows = _load(DATA)
    res = {"judges": {}}
    for name, f in (("J1", RES / "b38_j1_preds.json"), ("J2", RES / "b38_j2_preds.json")):
        if not f.exists():
            continue
        p = json.loads(f.read_text())
        res["judges"][name] = {"oof": _metrics(p["oof"], rows),
                               "loeo": _metrics(p["loeo"], [r for r in rows if r["loeo_test"]]),
                               "calib_pick": _pick_metrics(p["calib"]),
                               "calib_posts": _post_metrics(p["calib"])}
    res["math_probe"] = {r["key"]: {"label": r["label"], "ai_share": r["ai_share"], "words": r["words"],
                                    "pangram_words": r.get("pangram_words")}
                         for r in _load(PANGRAM) if r["cell"] != "K"}
    res["unscanned"] = [c["cid"] for c in _load(CANDS) if len(c["text"].split()) < 50]
    cands = {k: v["oof"]["rewrites"]["auroc"] or 0 for k, v in res["judges"].items()}
    if cands:
        best = max(cands, key=cands.get)
        if best != "J1" and "J1" in cands and cands[best] - cands["J1"] < 0.02:
            best = "J1"
        res["chosen"] = best
        res["clears_bar"] = cands[best] >= 0.70
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {"evaluation": res}, indent=1))
    print(json.dumps(res, indent=1))


def explore():
    """Post hoc, added 13:50 after the evaluation; none of this was pre-registered and none of it changes the choice.

    Looking at the J1 picks showed many short candidates. Two questions: does the gain come from picking short texts
    (which drop content), and does a free heuristic do as well? Heuristics: the shortest candidate; the candidate that
    copies the least from its input section (copied_from_input, 8-word runs, computed by calib_assess before the scan).
    The length floor keeps candidates with at least 80% of the input's words (falling back to all when none does).
    The copied-share heuristic is then checked on texts it was not found on: B36's C300 and Cfull rewrites of Sonnet's
    post D, against J1's out-of-fold and leave-one-experiment-out predictions on the same rows."""
    import numpy as np
    from scipy.stats import spearmanr
    from sklearn.metrics import roc_auc_score

    pang = {r["key"]: r for r in _load(PANGRAM) if r["cell"] == "K"}
    preds = {n: json.loads((RES / f"b38_{n.lower()}_preds.json").read_text()) for n in ("J1", "J2")}
    cands = [c for c in _load(CANDS) if c["cid"] in pang]
    for c in cands:
        c["share"] = pang[c["cid"]]["ai_share"]
        c["ratio"] = c["words"] / c["input_words"]
        c["claims"] = c["claims_entailed"] / c["claims_total"]
    by = {}
    for c in cands:
        by.setdefault(c["section"], []).append(c)
    rules = {"J1": lambda c: preds["J1"]["calib"][c["cid"]], "J2": lambda c: preds["J2"]["calib"][c["cid"]],
             "shortest": lambda c: c["words"], "least_copied": lambda c: c["copied_from_input"],
             "oracle": lambda c: c["share"]}

    def picks(rule, floor=0.0):
        out = []
        for cs in by.values():
            pool = [c for c in cs if c["ratio"] >= floor] or cs
            out.append(min(pool, key=rule))
        return out

    def summ(ps):
        return {"share": round(statistics.mean(c["share"] for c in ps), 3),
                "words_over_input": round(statistics.mean(c["ratio"] for c in ps), 2),
                "claims_entailed": round(statistics.mean(c["claims"] for c in ps), 2),
                "picks_under_70pct_words": sum(c["ratio"] < 0.7 for c in ps)}

    def pair_acc(rule):
        n = r = 0
        for cs in by.values():
            for i in range(len(cs)):
                for j in range(i + 1, len(cs)):
                    a, b = cs[i], cs[j]
                    if abs(a["share"] - b["share"]) > 0.05:
                        n += 1
                        r += (rule(a) < rule(b)) == (a["share"] < b["share"])
        return round(r / n, 3)

    res = {"all_candidates": {"share": round(statistics.mean(c["share"] for c in cands), 3),
                              "words_over_input": round(statistics.mean(c["ratio"] for c in cands), 2)}}
    res["best_of_4"] = {k: summ(picks(f)) | {"pair_accuracy": pair_acc(f)} for k, f in rules.items()}
    res["best_of_4_floor80"] = {k: summ(picks(f, 0.8)) for k, f in rules.items()}
    res["best_of_4_floor80"]["random"] = {"share": round(statistics.mean(
        statistics.mean(c["share"] for c in ([c for c in cs if c["ratio"] >= 0.8] or cs)) for cs in by.values()), 3)}
    res["spearman_on_candidates"] = {
        "J1_vs_share": round(float(spearmanr([rules["J1"](c) for c in cands], [c["share"] for c in cands]).statistic), 2),
        "J1_vs_words_ratio": round(float(spearmanr([rules["J1"](c) for c in cands], [c["ratio"] for c in cands]).statistic), 2),
        "share_vs_words_ratio": round(float(spearmanr([c["share"] for c in cands], [c["ratio"] for c in cands]).statistic), 2),
        "copied_vs_share": round(float(spearmanr([c["copied_from_input"] for c in cands], [c["share"] for c in cands]).statistic), 2)}
    rng = random.Random(0)
    gain = [statistics.mean(c["share"] for c in cs) - min(cs, key=rules["J1"])["share"] for cs in by.values()]
    diff = [g - (statistics.mean(c["share"] for c in cs) - min(cs, key=rules["least_copied"])["share"])
            for g, cs in zip(gain, by.values())]

    def ci(v):
        bs = sorted(statistics.mean(rng.choice(v) for _ in v) for _ in range(10000))
        return [round(statistics.mean(v), 3), round(bs[250], 3), round(bs[9750], 3)]

    res["section_bootstrap_95"] = {"J1_gain_over_random": ci(gain), "J1_minus_least_copied_gain": ci(diff),
                                   "sections_J1_better_than_random": sum(g > 0 for g in gain),
                                   "sections_J1_worse": sum(g < 0 for g in gain)}
    dtext = {r["id"]: r["D"] for r in _load(RES / "b36_inputs.jsonl")}
    rows = [r for r in _load(DATA) if r["exp"] == "B36" and r["cell"] in ("C300", "Cfull") and r["doc"] in dtext
            and r["ai_share"] is not None]
    y = [int(r["label"] != "Human") for r in rows]
    sh = [r["ai_share"] for r in rows]
    cp = np.array([copied_share(r["text"], dtext[r["doc"]]) for r in rows])
    held = {"n": len(rows), "not_human": sum(y),
            "least_copied": {"auroc": round(float(roc_auc_score(y, cp)), 3),
                             "spearman_share": round(float(spearmanr(cp, sh).statistic), 3)}}
    for k in ("oof", "loeo"):
        s = np.array([preds["J1"][k][r["uid"]] for r in rows])
        z = (s - s.mean()) / s.std() + (cp - cp.mean()) / cp.std()
        held[f"J1_{k}"] = {"auroc": round(float(roc_auc_score(y, s)), 3), "spearman_share": round(float(spearmanr(s, sh).statistic), 3)}
        held[f"J1_{k}_plus_copied"] = {"auroc": round(float(roc_auc_score(y, z)), 3),
                                       "spearman_share": round(float(spearmanr(z, sh).statistic), 3)}
    res["b36_rewrites_of_D"] = held
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {"explore_post_hoc": res}, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd in ("scanfiles", "record"):
        {"scanfiles": scanfiles, "record": record}[cmd](sys.argv[2])
    else:
        {"data": data, "calib_inputs": calib_inputs, "calib_prompts": calib_prompts, "calib_assess": calib_assess,
         "features": features, "linear": linear, "evaluate": evaluate, "explore": explore}[cmd]()
