"""Phase 2, R2 training data: (previous human section, Sonnet draft section) -> cleaned human section.

Design: docs/specs/2026-11-07-phase2-r2-design.md, section 3. Rules fixed before any R2 pair exists.

Pool (step `select`): results/b32_pilot_full.jsonl, B36's fixes (listing pages, near duplicates by word 5-gram MinHash
at Jaccard 0.5, earlier-corpus sites); split bucket 0 to 74 only, and only posts whose merged owner group
(b36_transfer.core_name) has no post in buckets 75 to 99; no post whose MinHash matches any B39 reserve post at
Jaccard 0.5 or more (reserve texts are hashed only, never read); 1,000 to 3,000 words; one post per site. Order
sha256("r2-v1:" + id). Page type: B36's PAGE prompt (Haiku), keep personal_post or technical_post with
single_author true, labelling in order until the quota is met. Pilot: the first 40 eligible; full build: the first
400 (the pilot's 40 included).

AI side (step `ai`): B36's pipeline unchanged in code (B25 NOTES and DRAFT prompts, B27 reword_all, Sonnet through
humanizer.llm's "sonnet" alias; the resolved model is logged in the call cache and must be claude-sonnet-5-5). Dose:
posts whose sha256("r2-dose:" + id) is below a third of the hash range get B36's 50% dose, the rest all notes.

Pairs (step `pairs`): the draft is cut by B36's sections(); the human post is cut into paragraphs. Each paragraph is
assigned to a draft section by a monotone alignment (dynamic programming maximizing summed TF-IDF cosine between a
paragraph and its section, sections in order, every section at least one paragraph). Target k = its paragraphs;
context k = target k-1 as cleaned (empty for k = 0). Cleaning: B11's prune_one marks target sentences the draft section
does not support; they are deleted (nothing reworded). Filters: drop a pair if cleaning removes more than 40% of the
target's words, if the draft section copies more than 30% of the cleaned target in 8-word runs, if the cleaned target
is under 80 words, or if context + draft + target exceed 3,500 words.

Pilot report (step `report`): words deleted by cleaning, pairs dropped by each filter, alignment similarity, calls and
wall time. Stop rule (design section 8): mean deletion above 40% or more than 20% of sections failing alignment
(cosine under 0.10 with their target) stops the build for a redesign.

Run: .venv/bin/python experiments/r2_data.py select|ai|pairs|report [--n 40]
Outputs (local, gitignored): results/r2_pool.jsonl, results/r2_ai.jsonl, results/r2_pairs.jsonl; numbers in
results/r2_data.json.
"""
from __future__ import annotations

import hashlib
import json
import re
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from b11_prune import prune_one  # noqa: E402
from b25_blog import DRAFT, NOTES, plain  # noqa: E402
from b27_reworded import reword_all  # noqa: E402
from b36_transfer import PAGE, _minhash, bucket, core_name, dose, is_listing, sections  # noqa: E402

from humanizer import ROOT  # noqa: E402
from humanizer.checks.copying import copied_share  # noqa: E402
from humanizer.data.facts import parse_facts  # noqa: E402
from humanizer.llm import claude_many  # noqa: E402

RES = ROOT / "results"
FULL = RES / "b32_pilot_full.jsonl"
POOL = RES / "r2_pool.jsonl"
AI = RES / "r2_ai.jsonl"
PAIRS = RES / "r2_pairs.jsonl"
OUT = RES / "r2_data.json"


def _h(salt, key):
    return hashlib.sha256(f"{salt}{key}".encode()).hexdigest()


def _load(p):
    return [json.loads(line) for line in open(p)] if Path(p).exists() else []


def _merge(key, val):
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {key: val}, indent=1))


def select(n: int):
    rows = _load(FULL)
    reserve = set(json.loads((RES / "b39_reserved_testB.json").read_text())["ids"])
    prior = set()
    for f in (ROOT / "data").glob("*.jsonl"):
        for line in f.open():
            try:
                u = json.loads(line).get("url")
            except (json.JSONDecodeError, AttributeError):
                continue
            if isinstance(u, str) and u.startswith("http"):
                prior.add(core_name(u))
    groups = {}
    for r in rows:
        r["core"], r["bucket"] = core_name(r["url"]), bucket(r["site"])
        groups.setdefault(r["core"], set()).add(r["bucket"])
    sigs = np.stack([_minhash(r["text"]) for r in rows])
    res_idx = [i for i, r in enumerate(rows) if r["id"] in reserve]
    res_sigs = sigs[res_idx] if res_idx else np.zeros((0, sigs.shape[1]), dtype=sigs.dtype)
    bands, near = {}, set()
    for i, s in enumerate(sigs):
        hit = set()
        for j in range(0, 64, 2):
            key = (j, s[j:j + 2].tobytes())
            hit.update(bands.get(key, ()))
            bands.setdefault(key, []).append(i)
        for k in hit:
            if (sigs[k] == s).mean() >= 0.5:
                near.update((i, k))
    cands, seen_sites = [], set()
    for i, r in enumerate(rows):
        if r["bucket"] > 74 or max(groups[r["core"]]) > 74 or r["id"] in reserve:
            continue
        if is_listing(r["url"]) or i in near or r["core"] in prior or r.get("prior_site"):
            continue
        if not 1000 <= r["words"] <= 3000:
            continue
        if len(res_sigs) and ((res_sigs == sigs[i]).mean(axis=1) >= 0.5).any():
            continue
        cands.append(r)
    cands.sort(key=lambda r: _h("r2-v1:", r["id"]))
    labels = {r["id"]: r for r in _load(POOL)}
    chosen = [r for r in cands if r["id"] in labels and labels[r["id"]].get("eligible")]
    i = 0
    while len(chosen) < n and i < len(cands):
        batch = [r for r in cands[i:i + 16] if r["id"] not in labels and r["site"] not in seen_sites]
        i += 16
        got = claude_many([PAGE.format(text=" ".join(r["text"].split()[:1200])) for r in batch], model="haiku")
        for r, g in zip(batch, got):
            m = re.search(r"\{.*\}", g or "", re.S)
            try:
                d = json.loads(m.group(0)) if m else {}
            except json.JSONDecodeError:
                d = {}
            ok = d.get("type") in ("personal_post", "technical_post") and d.get("single_author") is True
            ok = ok and r["site"] not in seen_sites
            labels[r["id"]] = {"id": r["id"], "site": r["site"], "words": r["words"], "type": d.get("type"),
                               "eligible": ok, "text": r["text"], "title_hint": r.get("url")}
            if ok:
                seen_sites.add(r["site"])
                chosen.append(labels[r["id"]])
    POOL.write_text("".join(json.dumps(v) + "\n" for v in labels.values()))
    _merge("select", {"candidates": len(cands), "labelled": len(labels), "eligible": len(chosen[:n])})
    print(len(cands), "candidates;", len(chosen[:n]), "chosen")


def ai(n: int):
    pool = [r for r in _load(POOL) if r["eligible"]]
    pool.sort(key=lambda r: _h("r2-v1:", r["id"]))
    pool = pool[:n]
    done = {r["id"] for r in _load(AI)}
    todo = [r for r in pool if r["id"] not in done]
    t0 = time.time()
    raws = claude_many([NOTES.format(text=r["text"]) for r in todo], model="sonnet")
    ok = []
    for r, x in zip(todo, raws):
        try:
            p = parse_facts(x) if x and "{" in x else None
        except Exception:  # noqa: BLE001
            p = None
        if p and p.facts:
            ok.append((r, p))
    reworded, _ = reword_all([p.facts for _, p in ok]) if ok else ([], 0)
    notes = []
    for (r, p), w in zip(ok, reworded):
        half = int(_h("r2-dose:", r["id"]), 16) < (16 ** 64) // 3
        notes.append(dose(w, r["id"]) if half else w)
    posts = claude_many([DRAFT.format(title=p.topic, words=int(round(r["words"], -1)),
                                      notes="\n".join(f"- {x}" for x in nl)) for (r, p), nl in zip(ok, notes)],
                        model="sonnet")
    with AI.open("a") as f:
        for (r, p), w, nl, post in zip(ok, reworded, notes, posts):
            text = plain(post) if post else ""
            if len(text.split()) < 500:
                continue
            f.write(json.dumps({"id": r["id"], "title": p.topic, "dose": round(len(nl) / max(1, len(w)), 2),
                                "notes": nl, "D": text, "human": r["text"]}) + "\n")
    _merge("ai", {"posts": len(_load(AI)), "refused_or_short": len(todo) - len(ok), "seconds": round(time.time() - t0)})


def _paras(text):
    return [p.strip() for p in text.split("\n") if len(p.split()) >= 3]


def align(draft_secs, paras):
    """Monotone assignment of paragraphs to sections maximizing summed TF-IDF cosine; every section gets one."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    if len(paras) < len(draft_secs):
        return None, None
    vec = TfidfVectorizer(stop_words="english").fit(draft_secs + paras)
    sim = (vec.transform(paras) @ vec.transform(draft_secs).T).toarray()
    P, S = sim.shape
    best = np.full((P + 1, S + 1), -1e9)
    best[0, 0] = 0
    back = np.zeros((P + 1, S + 1), dtype=int)
    for i in range(1, P + 1):
        for s in range(1, S + 1):
            stay, move = best[i - 1, s], best[i - 1, s - 1]
            if stay >= move:
                best[i, s], back[i, s] = stay + sim[i - 1, s - 1], 0
            else:
                best[i, s], back[i, s] = move + sim[i - 1, s - 1], 1
    assign, s = [0] * P, S
    for i in range(P, 0, -1):
        assign[i - 1] = s - 1
        s -= back[i, s]
    groups = [[paras[i] for i in range(P) if assign[i] == k] for k in range(S)]
    score = [float(np.mean([sim[i, k] for i in range(P) if assign[i] == k])) for k in range(S)]
    return groups, score


def pairs():
    rows = _load(AI)
    work = []
    for r in rows:
        secs = sections(r["D"])
        groups, score = align(secs, _paras(r["human"]))
        if groups is None:
            continue
        for k, (sec, g, sc) in enumerate(zip(secs, groups, score)):
            work.append({"doc": r["id"], "k": k, "draft": sec, "target_raw": "\n".join(g), "align": sc,
                         "dose": r["dose"]})

    def clean(w):
        pruned, st = prune_one(w["target_raw"], w["draft"])
        return w | {"target": pruned, "deleted": 1 - len(pruned.split()) / max(1, len(w["target_raw"].split())), **st}

    with ThreadPoolExecutor(4) as ex:
        work = list(ex.map(clean, work))
    by = {}
    for w in work:
        by.setdefault(w["doc"], []).append(w)
    out, drops = [], {"deleted_over_40": 0, "draft_copies_target": 0, "target_under_80": 0, "too_long": 0}
    for doc, ws in by.items():
        ws.sort(key=lambda w: w["k"])
        prev = ""
        for w in ws:
            reason = None
            if w["deleted"] > 0.40:
                reason = "deleted_over_40"
            elif copied_share(w["draft"], w["target"]) > 0.30:
                reason = "draft_copies_target"
            elif len(w["target"].split()) < 80:
                reason = "target_under_80"
            elif len(prev.split()) + len(w["draft"].split()) + len(w["target"].split()) > 3500:
                reason = "too_long"
            if reason:
                drops[reason] += 1
            else:
                out.append({"id": f"{doc}_{w['k']}", "doc": doc, "k": w["k"], "dose": w["dose"],
                            "prompt": f"Previous:\n{prev}\n\nDraft:\n{w['draft']}\n\nRewrite:\n",
                            "completion": w["target"], "align": w["align"], "deleted": w["deleted"]})
            prev = w["target"]
    PAIRS.write_text("".join(json.dumps(o) + "\n" for o in out))
    rep = {"sections": len(work), "pairs": len(out), "drops": drops,
           "deleted_mean": round(statistics.mean(w["deleted"] for w in work), 3) if work else None,
           "align_mean": round(statistics.mean(w["align"] for w in work), 3) if work else None,
           "align_under_010": sum(w["align"] < 0.10 for w in work)}
    _merge("pairs", rep)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 40
    {"select": lambda: select(n), "ai": lambda: ai(n), "pairs": pairs}[sys.argv[1]]()
