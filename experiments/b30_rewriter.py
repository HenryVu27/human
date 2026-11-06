"""B30: a learned rewriter. Can a local model turn an AI post into a human-reading post with the same ideas?

Henry asked (2026-11-05 evening) whether the project had concluded that an AI draft cannot be humanized.
It had not: every writer so far learned notes to article (B3 on), and the drafts that read Human were
rewritten from extracted notes (B14: specific facts, 40% of the length; B26: a blogger's own notes, 82%).
No writer has learned to rewrite an AI post as such. B28 gives the hard test cases: Sonnet's posts from
100%, 50% and 25% of a blogger's reworded notes read 1/18/0, 0/6/13 and 0/1/18 (Human/Mixed/AI); in the
thinner ones Sonnet chose most of the content.

Fixed before any B30 text or training pair exists (2026-11-05 20:45):
- Training pairs: the 660 essays of data/essaypool (630 train, 30 valid; no bench or bench2 essay).
  Each essay's notes (B25's NOTES prompt on the essay cut to 1,300 words, already extracted for B26) are
  put back in extraction order, reworded with B27's reword_all (Sonnet), and Sonnet writes the post from
  them with B25's DRAFT prompt (the essay's title, the cut's length), as plain text. The pair is
  "Draft:\n{post}\n\nRewrite:\n" to the essay cut. The AI post and the essay carry the same ideas; only
  the AI's way of writing them up differs. Manipulation check: the posts' copying from their essays
  (8-word runs), expected under 10% on average as in B27.
- Training: B17's QLoRA recipe on the PC (experiments/gpu/train13b.py), max length 3,584 tokens, when
  Henry frees the PC.
- Cells T100, T50, T25 on B28's 19 bench2 essays: the rewriter on B28's S100, S50 and S25 posts. Guard
  over the post; seeds 0 and 1; prune against the post (claims), template repeats dropped, cleanup; the
  sample with the most supported claims kept. Max new tokens: the post's length times 1.3 times 1.5 plus
  64, capped so prompt and output fit 4,096 tokens.
- Pangram on all 57, paired with the input posts (B28 S) and with the voice writer from notes (B28 L).
- Checks: length against the input post and the essay; claim support against the post; copying from
  the input post (a rewriter that copies its input has done nothing) and from the essay.
Amended 23:10, before any training pair is used and before any B30 text exists: Henry asked that heavy
jobs stay off the Mac, so both seeds are generated on the PC (experiments/gpu/gen13b_guard.py: the adapter
in its trained PEFT form, the same Guard file and sampling, as B28's amendment of 19:46). Nothing else
changes.
Predictions, both stated so the result decides between them: T100 reads Human on 12 or more of 19 (the
content is the blogger's, the prose local). If Pangram reads who chose the content, T25 stays mostly
not Human (5 or fewer Human of 19). If a learned rewriter re-plans an AI post enough, T25 reads Human on
10 or more.

Usage:
  uv run python experiments/b30_rewriter.py data      (Sonnet; writes data/rewritepool)
  copy data/rewritepool to C:/hgpu/data_rewritepool; train13b.py --data data_rewritepool --out out_rewritepool --max-len 3584
  uv run python experiments/b30_rewriter.py prompts
  on the PC: experiments/gpu/b30gen.cmd (gen13b_guard, seeds 0 and 1), then fetch b30_gen_s0/s1.jsonl
  uv run python experiments/b30_rewriter.py pick
  uv run python experiments/b30_rewriter.py record T100_e1234abcd=Human ...
"""

import json
import random
import re
import statistics
import sys

from humanizer import ROOT
from humanizer.checks.copying import copied_share
from humanizer.llm import claude_many

sys.path.insert(0, str(ROOT / "experiments"))
import b25_blog  # noqa: E402
from b25_blog import DRAFT, plain  # noqa: E402
from b27_reworded import reword_all  # noqa: E402

POOL = ROOT / "data" / "essaypool"
OUT_DATA = ROOT / "data" / "rewritepool"
PROMPTS = ROOT / "results" / "b30_prompts.jsonl"
TEXTS = ROOT / "results" / "b30_texts.jsonl"
OUT = ROOT / "results" / "b30_rewriter.json"
CONTEXT = 4096


def rewrite_prompt(post: str) -> str:
    return f"Draft:\n{post}\n\nRewrite:\n"


def _notes(row: dict) -> list[str]:
    """The facts in an essaypool prompt, put back in extraction order (facts_prompt shuffled them by id)."""
    items = [line[2:] for line in row["prompt"].split("\n") if line.startswith("- ")]
    idx = list(range(len(items)))
    random.Random(row["id"]).shuffle(idx)
    out = [""] * len(items)
    for i, j in enumerate(idx):
        out[j] = items[i]
    return out


def data():
    rows = [json.loads(line) | {"part": p} for p in ("train", "valid") for line in (POOL / f"{p}.jsonl").open()]
    essays = {r["id"]: r for r in map(json.loads, (ROOT / "data" / "essays.jsonl").open())}
    reworded, kept = reword_all([_notes(r) for r in rows])
    posts = claude_many([DRAFT.format(title=essays[r["id"]]["title"], words=int(round(len(r["completion"].split()), -1)),
                                      notes="\n".join(f"- {x}" for x in n)) for r, n in zip(rows, reworded)], model="sonnet")
    out = {"train": [], "valid": []}
    copies = []
    for r, p in zip(rows, posts):
        if not p or len(p.split()) < 100:
            continue
        post = plain(p)
        copies.append(copied_share(post, r["completion"]))
        out[r["part"]].append({"id": r["id"], "author": r["author"], "prompt": rewrite_prompt(post),
                               "completion": r["completion"], "post_words": len(post.split())})
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    for part, items in out.items():
        (OUT_DATA / f"{part}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in items))
    meta = {"train": len(out["train"]), "valid": len(out["valid"]), "chunks_not_reworded": kept,
            "post_copied_from_essay_mean": statistics.mean(copies), "post_copied_from_essay_max": max(copies)}
    (OUT_DATA / "meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))


def prompts():
    bench = {r["id"]: r for r in map(json.loads, (ROOT / "data" / "b28_bench.jsonl").open())}
    out = []
    for s in map(json.loads, (ROOT / "data" / "b28_sonnet.jsonl").open()):
        post, r = s["text"], bench[s["source"]]
        prompt = rewrite_prompt(post)
        room = CONTEXT - int(len(prompt.split()) * 1.5) - 32
        words = len(post.split())
        out.append({"id": "T" + s["id"][1:], "source": s["source"], "cell": "T" + s["cell"][1:], "prompt": prompt,
                    "allowed_text": post, "target_words": int(round(words, -1)),
                    "max_new_tokens": min(int(words * 1.3 * 1.5) + 64, room)})
    PROMPTS.write_text("".join(json.dumps(x) + "\n" for x in out))
    print(len(out), "prompts")


def pick():
    essays = {r["id"]: r for r in map(json.loads, (ROOT / "data" / "b28_bench.jsonl").open())}
    b25_blog.pick("b30", PROMPTS, TEXTS, OUT, cells=("T100", "T50", "T25"), seeds=(0, 1), essays=essays)
    inputs = {"T" + s["id"][1:]: s["text"] for s in map(json.loads, (ROOT / "data" / "b28_sonnet.jsonl").open())}
    per = {r["id"]: copied_share(r["text"], inputs[r["id"]]) for r in map(json.loads, TEXTS.open())}
    prev = json.loads(OUT.read_text())
    cells = {c: statistics.mean(v for k, v in per.items() if k.split("_")[0] == c) for c in ("T100", "T50", "T25")}
    OUT.write_text(json.dumps(prev | {"copied_from_input": {"mean": cells, "per_text": per}}, indent=1))
    print("copied from the input post:", cells)


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    pangram = out.get("pangram", {}) | verdicts
    summary = {c: {v: sum(1 for k, x in pangram.items() if k.split("_")[0] == c and x == v) for v in ("AI", "Mixed", "Human")}
               for c in ("T100", "T50", "T25")}
    OUT.write_text(json.dumps(out | {"pangram": pangram, "pangram_summary": summary}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "record":
        record(sys.argv[2:])
    else:
        {"data": data, "prompts": prompts, "pick": pick}[cmd]()
