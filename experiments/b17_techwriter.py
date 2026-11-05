"""B17: a genre-matched pool writer on Henry's post.

B15 ran the B14 pipeline on the 7 prose sections of Henry's context-engineering post: originals
read 0 Human, 3 Mixed, 4 AI; the pipeline 4 Human, 1 Mixed, 2 AI, but it kept a third of the words
and mangled the genre (lists into fragments, "I" into "the author"). The writer had never seen a
first-person technical blog post. Here the pool writer is retrained on about 670 pre-2022
first-person technical blog posts from FineWeb-Edu (humanizer.data.techblog, data/techpool, same
partial-pool recipe), and runs on B15's exact prompts (specific facts, 4 seeds, Guard, prune, clean,
most supported claims kept). Cell T; compare with B15 cell B section by section.

Usage:
  uv run python -m humanizer.data.techblog && uv run python -m humanizer.data.techpool   (then train on the PC: gpu/b17.cmd)
  for s in 0 1 2 3: uv run python experiments/gen_mlx.py results/b15_prompts.jsonl results/b17_gen_s$s.jsonl --guard --adapter models/lora-13b-techpool-mlx --seed $s
  uv run python experiments/b17_techwriter.py pick
  uv run python experiments/b17_techwriter.py record T_s1=AI ...
"""

import json
import sys

from humanizer import ROOT

sys.path.insert(0, str(ROOT / "experiments"))
import b15_blog  # noqa: E402

TEXTS = ROOT / "results" / "b17_texts.jsonl"
OUT = ROOT / "results" / "b17_blog.json"


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {v: sum(verdicts[i] == v for i in ids) for v in ("AI", "Mixed", "Human")}
    out = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    b15_blog.pick(prefix="b17", cell="T") if sys.argv[1] == "pick" else record(sys.argv[2:])
