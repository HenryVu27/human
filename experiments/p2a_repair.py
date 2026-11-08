"""P2a: repair test. How much Human verdict does a faithful, coherent post cost? (phase 2 amendment of 2026-11-07,
results/research/a2-redteam-phase2.md). Rules fixed before any repair is made or scanned.

Texts: A1's 30 primary C100 texts (results/a1_texts.jsonl; A1's paired set), each with its draft D100.

Flags, per text (claude-sonnet-5-5, pinned):
- unsupported claims: humanizer.checks.claims.claim_check(draft, text);
- broken sentences: humanizer.checks.defects.prose_defects(text);
- coherence: the COHERENCE prompt below (references to things never introduced, restarts as if a new post began,
  sentences cut off mid-thought, a value or stance the draft gives differently).

Repair, one call per text (REPAIR prompt): the model gets the draft, the text as numbered sentences and the flags, and
returns edits {n, action: "delete" | "replace", new}. Hard limits, applied in code:
- a replacement may change at most 10 words of its sentence (word-level diff, difflib opcodes), and may add no number,
  name, date or quote the draft lacks (claims.unsupported_specifics against the draft); a replacement over either limit
  is rejected; a rejected edit whose sentence carries an unsupported claim becomes a delete, otherwise the sentence is
  kept as it was;
- at most 25% of the text's words may change in all; if edits would exceed it, deletes are kept and the replacements
  with the most changed words are dropped until it fits.
Nothing else is rewritten. Reported per text: words changed, deleted, replaced; claim support before and after;
defects before and after.

Reader (quality): a reader agent, blind to which version is which, rates the original and repaired texts of the first
10 posts by doc id (20 texts, order shuffled by seed "p2a-read") against their draft on a fixed rubric: invented or
distorted items (each a claim, value, stance or attribution the draft does not give), garbled sentences, join defects,
and "would an editor publish this over the draft". Report: counts per version.

Scan: the 30 repaired texts plus the session's canaries, one blinded batch, at most 600 credits. Compared with A1's
C100 scan, paired, if every frozen canary returns identical output (otherwise C100 is rescanned in the batch).
Bands (a route decision on development data, design decision 7):
- repair holds: repaired Human on at least 22 of 30 and mean share under 0.10, and the reader's invented items fall to
  at most 1 per post on average with garbled sentences at most 1 per 1,000 words;
- repair costs the verdict: repaired Human under 22 of 30; report the share rise against words changed;
- repair does not fix quality: reader counts above the bars; R2 needs a faithful generator.

Run:
  .venv/bin/python experiments/p2a_repair.py repair
  .venv/bin/python experiments/p2a_repair.py scanfiles <dest>
  .venv/bin/python experiments/p2a_repair.py analyze
"""
from __future__ import annotations

import difflib
import json
import random
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from humanizer.checks.claims import claim_check, unsupported_specifics
from humanizer.checks.defects import prose_defects
from humanizer.eval import scan
from humanizer.llm import claude

RES = Path("results")
TEXTS = RES / "p2a_texts.jsonl"
OUT = RES / "p2a_repair.json"
MODEL = "claude-sonnet-5-5"
MAX_WORDS_PER_EDIT = 10
MAX_SHARE = 0.25
SENT = re.compile(r"(?:(?<=[.!?])|(?<=[.!?][\"'\u201d)]))\s+(?=[A-Z\"'\u201c(])")

COHERENCE = """Read this blog post. List every sentence that (a) refers to a person, thing, event or idea the post has not introduced before it, (b) restarts the post as if a new post began, (c) is cut off mid-thought, or (d) states a value, stance or attribution differently from the DRAFT it was rewritten from. Quote each sentence exactly and say which problem it has. Return only JSON: {{"issues": [{{"sentence": "...", "problem": "a|b|c|d"}}]}}

<draft>
{draft}
</draft>

<post>
{text}
</post>"""

REPAIR = """You are a careful copy editor making the smallest possible repairs. Below is a DRAFT, and a POST rewritten from it as numbered sentences, with a list of PROBLEMS. Fix each problem with the least change: delete a sentence that states something the draft does not support and cannot be fixed by changing a few words; otherwise replace the sentence with a version that changes at most 10 words, using the draft's facts (no new numbers, names, dates or quotes), restoring a missing introduction in a few words, or completing a cut-off thought from the draft. Do not touch sentences without a problem. Do not improve style. Return only JSON: {{"edits": [{{"n": <sentence number>, "action": "delete" or "replace", "new": "<the full new sentence, for replace>"}}]}}

<draft>
{draft}
</draft>

<problems>
{problems}
</problems>

<post>
{numbered}
</post>"""


def _load(p):
    return [json.loads(line) for line in open(p)]


def _primary():
    t = {r["id"]: r for r in _load(RES / "a1_texts.jsonl")}
    ex = {d["id"] for d in _load(RES / "a1_d100.jsonl") if d["excluded"]}
    docs = sorted(d for d in {r["doc"] for r in t.values()} - ex
                  if not t[f"C100_{d}"]["excluded"] and not t[f"C50_{d}"]["excluded"])
    d100 = {d["id"]: d["D100"] for d in _load(RES / "a1_d100.jsonl")}
    return [(d, t[f"C100_{d}"]["text"], d100[d]) for d in docs]


def split(text):
    """[(paragraph index, sentence)] keeping paragraph structure."""
    out = []
    for pi, para in enumerate(p for p in text.split("\n") if p.strip()):
        out += [(pi, s.strip()) for s in SENT.split(para.strip()) if s.strip()]
    return out


def join(units):
    paras = {}
    for pi, s in units:
        if s:
            paras.setdefault(pi, []).append(s)
    return "\n\n".join(" ".join(v) for _, v in sorted(paras.items()))


def changed_words(a, b):
    sm = difflib.SequenceMatcher(a=a.split(), b=b.split())
    return sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")


def _json(raw, key):
    m = re.search(r"\{.*\}", raw or "", re.S)
    try:
        return json.loads(m.group(0)).get(key, []) if m else []
    except json.JSONDecodeError:
        return []


def repair_one(doc, text, draft):
    cc = claim_check(draft, text, model=MODEL)
    defects = prose_defects(text)
    coh = _json(claude(COHERENCE.format(draft=draft, text=text), model=MODEL), "issues")
    problems = ([f"unsupported claim: {c}" for c in cc["unsupported_claims"]] +
                [f"broken sentence: {d}" for d in defects] +
                [f"coherence ({i.get('problem')}): {i.get('sentence')}" for i in coh if isinstance(i, dict)])
    units = split(text)
    numbered = "\n".join(f"{i}. {s}" for i, (_, s) in enumerate(units, 1))
    edits = _json(claude(REPAIR.format(draft=draft, problems="\n".join(f"- {p}" for p in problems),
                                       numbered=numbered), model=MODEL), "edits") if problems else []
    words = len(text.split())
    plan, rejected = {}, 0
    for e in edits:
        try:
            n = int(e["n"]) - 1
        except (KeyError, TypeError, ValueError):
            continue
        if not 0 <= n < len(units):
            continue
        old = units[n][1]
        if e.get("action") == "delete":
            plan[n] = ("delete", "", len(old.split()))
            continue
        new = (e.get("new") or "").strip()
        cw = changed_words(old, new)
        if new and cw <= MAX_WORDS_PER_EDIT and not unsupported_specifics(draft, new) - unsupported_specifics(draft, old):
            plan[n] = ("replace", new, cw)
        else:
            rejected += 1
            if any(old[:60] in p or p.split(": ", 1)[-1][:60] in old for p in problems if p.startswith("unsupported")):
                plan[n] = ("delete", "", len(old.split()))
    while sum(c for _, _, c in plan.values()) > MAX_SHARE * words:
        worst = max((k for k, v in plan.items() if v[0] == "replace"), key=lambda k: plan[k][2], default=None)
        if worst is None:
            break
        del plan[worst]
    repaired = text  # edits applied in place, so layout and every untouched character stay as generated
    for i in sorted(plan, reverse=True):
        old_s, (action, new_s, _) = units[i][1], plan[i]
        repaired = repaired.replace(old_s, new_s, 1)
    repaired = re.sub(r"[ \t]{2,}", " ", repaired)
    repaired = re.sub(r"(?m)^[ \t]+|[ \t]+$", "", repaired)
    repaired = re.sub(r"\n{3,}", "\n\n", repaired).strip()
    cc2 = claim_check(draft, repaired, model=MODEL)
    return {"id": f"R100_{doc}", "cell": "R100", "doc": doc, "text": repaired, "original": text,
            "problems": len(problems), "edits": len(plan), "rejected": rejected,
            "deleted": sum(v[0] == "delete" for v in plan.values()),
            "replaced": sum(v[0] == "replace" for v in plan.values()),
            "words_changed_share": round(sum(v[2] for v in plan.values()) / max(1, words), 4),
            "support_before": round(cc["claims_entailed"] / max(1, cc["claims_total"]), 4),
            "support_after": round(cc2["claims_entailed"] / max(1, cc2["claims_total"]), 4),
            "defects_before": len(defects)}


def repair():
    with ThreadPoolExecutor(4) as ex:
        rows = list(ex.map(lambda x: repair_one(*x), _primary()))
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    summ = {k: round(statistics.mean(r[k] for r in rows), 4) for k in
            ("problems", "edits", "rejected", "deleted", "replaced", "words_changed_share", "support_before",
             "support_after", "defects_before")}
    summ["n"] = len(rows)
    order = sorted(rows, key=lambda r: r["doc"])[:10]
    pack = [{"doc": r["doc"], "version": v, "text": r["text"] if v == "repaired" else r["original"]}
            for r in order for v in ("original", "repaired")]
    random.Random("p2a-read").shuffle(pack)
    key = [{"item": i, "doc": p["doc"], "version": p["version"]} for i, p in enumerate(pack)]
    (RES / "p2a_read_pack.jsonl").write_text("".join(json.dumps({"item": i, "doc": p["doc"], "text": p["text"]}) + "\n"
                                                    for i, p in enumerate(pack)))
    (RES / "p2a_read_key.json").write_text(json.dumps(key))
    OUT.write_text(json.dumps({"repair": summ}, indent=1))
    print(json.dumps(summ, indent=1))


def scanfiles(dest):
    texts = [{"key": r["id"], "cell": r["cell"], "doc": r["doc"], "text": r["text"]} for r in _load(TEXTS)]
    texts += scan.canaries()
    print(len(texts), "files, about", scan.write_batch("p2a", texts, dest, max_credits=600), "credits")


def analyze():
    from scipy.stats import wilcoxon
    rows = scan.record("p2a")
    a1 = {r["key"]: r for r in _load(RES / "a1_pangram.jsonl")}
    now = {r["key"]: r for r in rows}
    can = scan.canary_check(rows, {k: {"label": v["label"], "ai_share": v["ai_share"]}
                                   for k, v in a1.items() if v["cell"] == "CAN" and "perturbed" not in k})
    tx = {r["doc"]: r for r in _load(TEXTS)}
    docs = sorted(tx)
    diff = [now[f"R100_{d}"]["ai_share"] - a1[f"C100_{d}"]["ai_share"] for d in docs]
    hum = sum(now[f"R100_{d}"]["label"] == "Human" for d in docs)
    from scipy.stats import spearmanr
    res = {"canaries_identical": can["identical"], "canary_changes": can["changed"], "n": len(docs),
           "human_repaired": hum, "human_c100": sum(a1[f"C100_{d}"]["label"] == "Human" for d in docs),
           "mean_share_repaired": round(statistics.mean(now[f"R100_{d}"]["ai_share"] for d in docs), 4),
           "mean_diff": round(statistics.mean(diff), 4), "p": float(wilcoxon(diff).pvalue) if any(diff) else 1.0,
           "spearman_rise_vs_words_changed": round(spearmanr(diff, [tx[d]["words_changed_share"] for d in docs])[0], 3),
           "pangram_part_of_band": "holds" if hum >= 22 and statistics.mean(now[f"R100_{d}"]["ai_share"] for d in docs) < 0.10 else "costs the verdict"}
    prev = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(prev | {"analysis": res}, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"repair": repair, "analyze": analyze}.get(sys.argv[1], lambda: scanfiles(sys.argv[2]))()
