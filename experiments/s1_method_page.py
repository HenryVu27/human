"""S1: run the humanizer's rewriter on eukleos.app's method page (Henry, 2026-11-09: "do the same for the site's
readings"). An applied run, not a research claim; no Pangram scan decides anything here.

Input: the live page's prose by section (scratch sections.json, read from https://eukleos.app/method; section 9, the
legal attribution, is excluded). Generator: experiments/gpu/gen_fp2.py --independent --max-overlap 0.15, B30's adapter,
the P2e settings. Then P2a's repair pass per section (capped edits against the section's own text).
Only rewrites that Henry reads and accepts go on the site; numbers must be mapped back to the page's live values.

  .venv/bin/python experiments/s1_method_page.py posts <sections.json>
  (PC) s1.cmd, then copy s1_gen.jsonl to results/
  .venv/bin/python experiments/s1_method_page.py report <sections.json>
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

RES = Path("results")


def _secs(path):
    return [s for s in json.load(open(path)) if s["paras"] and not s["head"].strip().startswith("Questions")]


def posts(path):
    secs = _secs(path)
    (RES / "s1_posts.jsonl").write_text(json.dumps({"doc": "method", "sections": ["\n".join(s["paras"]) for s in secs]}) + "\n")
    print(len(secs), "sections,", sum(len(p.split()) for s in secs for p in s["paras"]), "words")


def report(path):
    from p2a_repair import repair_one

    secs = _secs(path)
    g = json.loads((RES / "s1_gen.jsonl").read_text().splitlines()[0])
    rows = []
    for s, x in zip(secs, g["sections"]):
        c = next(c for c in x["candidates"] if c["seed"] == x["chosen"])
        rows.append({"head": s["head"].strip(), "draft": "\n".join(s["paras"]), "rewrite": c["text"], "rule": x["rule"],
                     "tried": x["tried"], "copied": round(c["copied"], 3)})
    with ThreadPoolExecutor(4) as ex:
        fixed = list(ex.map(lambda r: repair_one("method", r["rewrite"], r["draft"]) if r["rewrite"].strip() else None, rows))
    for r, f in zip(rows, fixed):
        r["repaired"] = f["text"] if f else ""
        r["support_after"] = f["support_after"] if f else None
        r["edits"] = f["edits"] if f else 0
    (RES / "s1_report.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    for r in rows:
        print(f"\n## {r['head']}  [{r['rule']}, tried {r['tried']}, copied {r['copied']}, support {r['support_after']}, edits {r['edits']}]")
        print("DRAFT:\n" + r["draft"])
        print("\nREWRITE, REPAIRED:\n" + r["repaired"])


if __name__ == "__main__":
    {"posts": posts, "report": report}[sys.argv[1]](sys.argv[2])
