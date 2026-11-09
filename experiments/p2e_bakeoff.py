"""P2e: independent sections with the loop gate and no silent deletion (phase 2 amendment of 2026-11-09). Rules fixed
before any P2e text exists; P2d's gate failed, and its pre-registered consequence is this cell.

P2d's forced-prefix continuation failed its gate: 4 of 30 final posts repeat themselves, because a later section
sometimes re-writes an earlier one (4-gram overlap with earlier chosen sections up to 1.0).

Posts and sections: A1's 30 primary posts and A1's own section prompts (results/a1_prompts_c100.jsonl, B36's 600 to
1,000-word sections), so the only differences from A1's C100 are in generation and picking.
Generator: experiments/gpu/gen_fp2.py --independent --max-overlap 0.15 on the PC with B30's adapter unchanged: each
section alone in B30's own prompt shape; early stop at a loop; seeds 0 and 1, then 2 and 3 if neither is clean. Clean:
stopped by itself, not a loop, form checks (new code at most 0, restarts for later sections), 0.5 to 1.6 times the
section's words, and at most 15% of its word 4-grams in the post's earlier chosen sections (the largest overlap among
P2d's clean posts' typical values is under 0.02 at the median; 0.15 passes 21 of its 26 non-flagged posts). Pick: least
copying among clean candidates. No prune, no cleanup, no deletion except P2d's cut of a failed candidate's loop.

Gate before any Claude call or scan, as P2d's: at most 20% of sections without a clean candidate, no final post a
loop by loops.is_loop, mean post at most 1.4 times its draft's words. A failed gate stops the cell; no change of
threshold after seeing data.

If the gate passes, as P2c: P2a's repair pass (cell FR); a blind reader with P2a's rubric on the same 10 posts, FR
against P2a's R100; FR's 30 posts plus canaries in one blinded batch, at most 600 credits. Bands: quality holds if FR's
dropped items are at most half R100's, invented items no higher, and at least 5 of 10 publish yes; the verdict survives
if FR reads Human on at least 22 of 30 with mean share under 0.10.

Run:
  .venv/bin/python experiments/p2e_bakeoff.py posts
  (PC) p2e.cmd
  .venv/bin/python experiments/p2e_bakeoff.py check | assemble | scanfiles <dest> | analyze
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import p2d_bakeoff as d  # noqa: E402
from p2a_repair import _primary  # noqa: E402

b = d.b
RES = Path("results")
b.EXP = "p2e"
b.POSTS = RES / "p2e_posts.jsonl"
b.GEN = RES / "p2e_gen.jsonl"
b.TEXTS = RES / "p2e_texts.jsonl"
b.OUT = RES / "p2e_bakeoff.json"


def posts():
    prm = [json.loads(line) for line in open(RES / "a1_prompts_c100.jsonl")]
    rows = []
    for doc, _, _ in _primary():
        parts = sorted((p for p in prm if p["doc"] == doc), key=lambda p: p["part"])
        rows.append({"doc": doc, "sections": [p["allowed_text"] for p in parts]})
    b.POSTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "posts,", sum(len(r["sections"]) for r in rows), "sections")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "posts":
        posts()
    elif cmd == "check":
        d.check()
    elif cmd == "assemble":
        d._keep_check(b.assemble)
    elif cmd == "analyze":
        b.analyze()
    else:
        b.scanfiles(sys.argv[2])
