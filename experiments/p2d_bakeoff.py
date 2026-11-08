"""P2d: P2c rerun with loop protection (docs/specs/2026-11-07-phase2-r2-design.md, amendment of 2026-11-08). Rules fixed
before any P2d text exists; Henry's go on 2026-11-08 ("could you continue please").

Same question, posts, sections, adapter and bands as experiments/p2c_bakeoff.py: does regenerating without silent
deletion, each section continuing from the previous one, fix dropped content and joins, and does the Human verdict
survive? The generator is experiments/gpu/gen_fp2.py, which differs from P2c's in its stated ways only: stops at a
loop, up to 4 seeds per section, a clean-candidate gate (stopped, no loop, form checks, 0.5 to 1.6 times the section's
words) before least copying, a lower token cap, and no looped text carried forward as the prefix.

Gate before any Claude call or scan (step `check`): forced prefix counts as failed, and the cell stops there, if more
than 20% of the 132 sections have no clean candidate after 4 seeds (rule other than "eligible"), or if any final post
is a loop by loops.is_loop, or if the mean post is over 1.4 times its draft's words. The raw per-candidate loop rate
at k > 0 is reported beside it. A failed gate means going back to independent sections with the loop gate.

If the gate passes, unchanged from P2c: P2a's repair pass gives cell FR; a blind reader with P2a's rubric compares FR
with P2a's R100 on the same 10 posts; FR's 30 posts and the canaries go in one blinded batch (at most 600 credits).
Bands: quality holds if FR's dropped items are at most half R100's, invented items are no higher, and at least 5 of 10
get a publish yes; the verdict survives if FR reads Human on at least 22 of 30 with mean share under 0.10.

Run:
  .venv/bin/python experiments/p2d_bakeoff.py check
  .venv/bin/python experiments/p2d_bakeoff.py assemble
  .venv/bin/python experiments/p2d_bakeoff.py scanfiles <dest>
  .venv/bin/python experiments/p2d_bakeoff.py analyze
"""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import p2c_bakeoff as b  # noqa: E402

from humanizer.checks.loops import is_loop, repeat_share  # noqa: E402

RES = Path("results")
b.EXP = "p2d"
b.GEN = RES / "p2d_gen.jsonl"
b.TEXTS = RES / "p2d_texts.jsonl"
b.OUT = RES / "p2d_bakeoff.json"


def check():
    gen = b._load(b.GEN)
    posts = {p["doc"]: p for p in b._load(b.POSTS)}
    secs = [(x["doc"], s) for x in gen for s in x["sections"]]
    chosen = lambda s: next(c for c in s["candidates"] if c["seed"] == s["chosen"])
    raw = [c for _, s in secs if s["k"] > 0 for c in s["candidates"]]
    post_loops, ratios = 0, []
    for x in gen:
        text = "\n\n".join(chosen(s)["text"] for s in x["sections"] if chosen(s)["text"])
        post_loops += is_loop(text)
        ratios.append(len(text.split()) / sum(len(t.split()) for t in posts[x["doc"]]["sections"]))
    rules = {r: sum(s["rule"] == r for _, s in secs) for r in ("eligible", "cut", "short")}
    not_clean = (rules["cut"] + rules["short"]) / max(1, len(secs))
    res = {"posts": len(gen), "sections": len(secs), "rules": rules, "share_not_clean": round(not_clean, 3),
           "tried_mean": round(statistics.mean(s["tried"] for _, s in secs), 2),
           "raw_candidate_loop_rate_k_over_0": round(statistics.mean(c["loop"] for c in raw), 3),
           "final_posts_looping": post_loops, "post_words_over_draft": round(statistics.mean(ratios), 3),
           "post_words_over_draft_range": [round(min(ratios), 2), round(max(ratios), 2)],
           "mean_repeat_share_chosen": round(statistics.mean(repeat_share(chosen(s)["text"]) for _, s in secs), 3),
           "empty_sections": sum(not chosen(s)["text"] for _, s in secs)}
    res["gate"] = "pass" if not_clean <= 0.20 and post_loops == 0 and statistics.mean(ratios) <= 1.4 else "fail"
    b.OUT.write_text(json.dumps({"check": res}, indent=1))
    print(json.dumps(res, indent=1))


def _keep_check(fn):
    prev = json.loads(b.OUT.read_text())
    fn()
    new = json.loads(b.OUT.read_text())
    b.OUT.write_text(json.dumps(prev | new, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "check":
        check()
    elif cmd == "assemble":
        _keep_check(b.assemble)
    elif cmd == "analyze":
        b.analyze()
    else:
        b.scanfiles(sys.argv[2])
