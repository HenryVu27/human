"""P2c: does regenerating without deletion, with forced-prefix continuation, fix dropped content and joins, and does
the Human verdict survive? (phase 2 step 3; docs/specs/2026-11-07-phase2-r2-design.md, amendments of 2026-11-07.)
Rules fixed before any P2c text exists.

Posts: A1's 30 primary posts, their D100 drafts (results/a1_d100.jsonl). Drafts are cut into sections of about 400 to
600 words (b36_transfer.sections with lo 350, hi 600, tail 150) so that two draft sections, the previous output and
the continuation fit OLMo-2's 4,096 tokens.

Cell F (forced prefix): experiments/gpu/gen_fp.py on the PC, B30's adapter unchanged, seeds 0 and 1 per section,
deterministic per-section pick (form checks with new code at most 0, at least half the section's words, least copying
from the section), no prune, no cleanup. Then P2a's repair pass unchanged (experiments/p2a_repair.repair_one: flags,
capped minimal edits) on each assembled post: cell FR.
Smaug-Humanizer is not in this batch (PC has no runtime for it; it waits for Modal credit).

Measures:
- Reader (the decisive quality measure): a blind reader with P2a's rubric (invented, garbled, joins, dropped,
  publish) on the 10 posts the P2a reader read, FR against P2a's R100, 20 items shuffled by seed "p2c-read".
- Pangram: FR's 30 posts plus the session's canaries in one blinded batch (at most 600 credits), paired with A1's
  C100 and P2a's R100 scans if every frozen canary is identical.
Bands:
- quality: FR's dropped items at most half of R100's and invented items no higher than R100's (reader totals over
  the 10 posts), and at least 5 of 10 publish yes -> regeneration fixes coverage; otherwise report the counts.
- Pangram: FR Human at least 22 of 30 with mean share under 0.10 -> the verdict survives; otherwise report the drop.
Development data only; Pangram chooses nothing within the cell (design decision 7).

Run:
  .venv/bin/python experiments/p2c_bakeoff.py posts            -> results/p2c_posts.jsonl (copy to the PC)
  (PC) python gen_fp.py --adapter out_rewritepool/lora-13b-v1 --posts p2c_posts.jsonl --out p2c_gen.jsonl --seeds 0,1
  .venv/bin/python experiments/p2c_bakeoff.py assemble          -> F and FR texts, reader pack
  .venv/bin/python experiments/p2c_bakeoff.py scanfiles <dest>
  .venv/bin/python experiments/p2c_bakeoff.py analyze
"""
import json
import random
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from b36_transfer import sections  # noqa: E402
from p2a_repair import _primary, repair_one  # noqa: E402

from humanizer.checks.copying import copied_share  # noqa: E402
from humanizer.eval import scan  # noqa: E402

RES = Path("results")
POSTS = RES / "p2c_posts.jsonl"
GEN = RES / "p2c_gen.jsonl"
TEXTS = RES / "p2c_texts.jsonl"
OUT = RES / "p2c_bakeoff.json"


def _load(p):
    return [json.loads(line) for line in open(p)]


def posts():
    rows = [{"doc": d, "sections": sections(draft, lo=350, hi=600, tail=150)} for d, _, draft in _primary()]
    POSTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "posts,", sum(len(r["sections"]) for r in rows), "sections")


def assemble():
    gen = {g["doc"]: g for g in _load(GEN)}
    prim = {d: draft for d, _, draft in _primary()}
    F = []
    for doc, draft in prim.items():
        if doc not in gen:
            continue
        secs = gen[doc]["sections"]
        text = "\n\n".join(next(c for c in s["candidates"] if c["seed"] == s["chosen"])["text"] for s in secs)
        F.append({"doc": doc, "text": text, "draft": draft, "fallbacks": sum(s["rule"] != "eligible" for s in secs),
                  "truncated": sum(not next(c for c in s["candidates"] if c["seed"] == s["chosen"])["hit_eos"]
                                   for s in secs)})
    with ThreadPoolExecutor(4) as ex:
        FR = list(ex.map(lambda f: repair_one(f["doc"], f["text"], f["draft"]), F))
    rows = []
    for f, r in zip(F, FR):
        rows.append({"id": f"F_{f['doc']}", "cell": "F", "doc": f["doc"], "text": f["text"],
                     "words": len(f["text"].split()), "fallbacks": f["fallbacks"], "truncated": f["truncated"],
                     "copied_from_draft": copied_share(f["text"], f["draft"])})
        rows.append(r | {"id": f"FR_{f['doc']}", "cell": "FR"})
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    read_docs = sorted({k["doc"] for k in json.loads((RES / "p2a_read_key.json").read_text())})
    r100 = {r["doc"]: r["text"] for r in _load(RES / "p2a_texts.jsonl")}
    fr = {r["doc"]: r["text"] for r in rows if r["cell"] == "FR"}
    pack = [{"doc": d, "version": v, "text": (fr if v == "FR" else r100)[d]} for d in read_docs if d in fr
            for v in ("FR", "R100")]
    random.Random("p2c-read").shuffle(pack)
    (RES / "p2c_read_pack.jsonl").write_text("".join(json.dumps({"item": i, "doc": p["doc"], "text": p["text"]}) + "\n"
                                                    for i, p in enumerate(pack)))
    (RES / "p2c_read_key.json").write_text(json.dumps([{"item": i, "doc": p["doc"], "version": p["version"]}
                                                        for i, p in enumerate(pack)]))
    fcell = [r for r in rows if r["cell"] == "F"]
    summ = {"posts": len(fcell), "F_words": round(statistics.mean(r["words"] for r in fcell)),
            "F_fallback_sections": sum(r["fallbacks"] for r in fcell),
            "F_truncated_sections": sum(r["truncated"] for r in fcell),
            "F_copied_from_draft": round(statistics.mean(r["copied_from_draft"] for r in fcell), 3),
            "FR_words_changed": round(statistics.mean(r["words_changed_share"] for r in rows if r["cell"] == "FR"), 4),
            "FR_support_after": round(statistics.mean(r["support_after"] for r in rows if r["cell"] == "FR"), 4)}
    OUT.write_text(json.dumps({"assemble": summ}, indent=1))
    print(json.dumps(summ, indent=1))


def scanfiles(dest):
    texts = [{"key": r["id"], "cell": r["cell"], "doc": r["doc"], "text": r["text"]} for r in _load(TEXTS)
             if r["cell"] == "FR"]
    texts += scan.canaries()
    print(len(texts), "files, about", scan.write_batch("p2c", texts, dest, max_credits=600), "credits")


def analyze():
    from scipy.stats import wilcoxon
    rows = scan.record("p2c")
    now = {r["key"]: r for r in rows}
    a1 = {r["key"]: r for r in _load(RES / "a1_pangram.jsonl")}
    p2a = {r["key"]: r for r in _load(RES / "p2a_pangram.jsonl")}
    can = scan.canary_check(rows, {k: {"label": v["label"], "ai_share": v["ai_share"]}
                                   for k, v in a1.items() if v["cell"] == "CAN" and "perturbed" not in k})
    docs = sorted(r["doc"] for r in rows if r["cell"] == "FR")
    res = {"canaries_identical": can["identical"], "canary_changes": can["changed"], "n": len(docs),
           "human": {"FR": sum(now[f"FR_{d}"]["label"] == "Human" for d in docs),
                     "R100": sum(p2a[f"R100_{d}"]["label"] == "Human" for d in docs),
                     "C100": sum(a1[f"C100_{d}"]["label"] == "Human" for d in docs)},
           "mean_share": {"FR": round(statistics.mean(now[f"FR_{d}"]["ai_share"] for d in docs), 4),
                          "R100": round(statistics.mean(p2a[f"R100_{d}"]["ai_share"] for d in docs), 4)}}
    diff = [now[f"FR_{d}"]["ai_share"] - p2a[f"R100_{d}"]["ai_share"] for d in docs]
    res["FR_minus_R100"] = {"mean": round(statistics.mean(diff), 4),
                            "p": float(wilcoxon(diff).pvalue) if any(diff) else 1.0}
    res["pangram_band"] = ("verdict survives" if res["human"]["FR"] >= 22 and res["mean_share"]["FR"] < 0.10
                           else "verdict drops")
    prev = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(prev | {"analysis": res}, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"posts": posts, "assemble": assemble, "analyze": analyze}.get(sys.argv[1], lambda: scanfiles(sys.argv[2]))()
