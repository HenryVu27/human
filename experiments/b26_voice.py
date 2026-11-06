"""B26: a voice writer for the notes route.

B25 cell N gives the pool writer a blogger's notes. The pool writer learned from FineWeb pages
(essay mills, SEO and health sites) and writes like them; Henry's aim is a post that sounds like a
person. Here the writer is retrained on the essay corpus's training split (humanizer.data.essaypool:
13 writers, up to 60 pre-ChatGPT essays each, the last 30 by id held out for validation; no bench
essay enters), notes to essay, with B17's QLoRA recipe (experiments/gpu/train13b.py on the PC).
Two things change from N, both chosen for the notes route: the corpus, and every note kept in
training (the pool recipe kept a random 20 to 60%, which trains the writer to write past its notes).

Fixed before training:
- Cell V: B25's N prompts unchanged (same notes, length, Guard material, prune, repeat guard,
  cleanup, most-supported-claims pick), seeds 0 to 3, adapter models/lora-13b-essaypool-mlx.
- The 13 test texts are scanned on Pangram and paired with N essay by essay. Checks as B25.
Prediction: V reads Human at least as often as N; keeps more of T (it learned to write from a
complete list, so less is pruned); first person nearer the essay's; quality against the essay above N.
Amended 17:58, during training and before any V text exists: B25's AI drafts read 8 Human, 5 Mixed,
0 AI, so B25 stopped before scanning N, and Pangram cannot show what a writer adds on this bench. V is
not scanned. It is judged on the local checks against N and D (length, claim support, copying, first
person and sentence-length spread against the essay, quality against the essay) and in a blind read.
Amended 18:08, during training and before any V text exists, after B27: Sonnet's posts from the same
notes reworded (copying from the essay down from 37% to 7%) read 1 Human, 11 Mixed, 1 AI against D's 8,
5, 0 (Fisher p = 0.011). The notes' wording, not their content, carried D. So V is written from B27's
reworded notes (Guard and prune over them, same length, seeds 0 to 3, same pick), and V is scanned
again: its 13 texts, paired essay by essay with B27's W (Sonnet from the same reworded notes). This is
the test of the local-writer route on blogs (B5 found it reads Human from reworded facts on FineWeb).
Cell M, the pool writer on the same prompts, is made for the local checks only (no credits left to scan it).
Prediction: V reads Human on 7 or more of 13 with at most 1 AI (W: 1 Human).

Usage:
  uv run python -m humanizer.data.essaypool          (Sonnet notes for the training essays)
  scp -r data/essaypool to C:/hgpu/data_essaypool, run experiments/gpu/b26.cmd on the PC under the lock,
  scp the adapter back, then: uv run python experiments/peft_to_mlx.py <adapter dir> models/lora-13b-essaypool-mlx
  uv run python experiments/b26_voice.py prompts
  for s in 0 1 2 3: uv run python experiments/gen_mlx.py results/b26_prompts.jsonl results/b26_gen_s$s.jsonl --guard --adapter models/lora-13b-essaypool-mlx --seed $s
  for s in 0 1 2 3: uv run python experiments/gen_mlx.py results/b26m_prompts.jsonl results/b26m_gen_s$s.jsonl --guard --adapter models/lora-13b-pool-mlx --seed $s
  uv run python experiments/b26_voice.py pick        (and pick_pool for M)
  uv run python experiments/b26_voice.py record V_e1234abcd=Human ...
"""

import json
import sys

from humanizer import ROOT
from humanizer.data.facts import Facts

sys.path.insert(0, str(ROOT / "experiments"))
import b25_blog  # noqa: E402

PROMPTS = ROOT / "results" / "b26_prompts.jsonl"
POOL_PROMPTS = ROOT / "results" / "b26m_prompts.jsonl"
POOL_TEXTS = ROOT / "results" / "b26m_texts.jsonl"
POOL_OUT = ROOT / "results" / "b26m_pool.json"
TEXTS = ROOT / "results" / "b26_texts.jsonl"
OUT = ROOT / "results" / "b26_voice.json"


def prompts():
    """V and M prompts from B27's reworded notes (amendment 18:08); Guard and prune material are those notes."""
    notes = {r["source"]: r["notes"] for r in map(json.loads, (ROOT / "data" / "b27_texts.jsonl").open())}
    for cell, path in (("V", PROMPTS), ("M", POOL_PROMPTS)):
        rows = [b25_blog._row(cell, r, Facts(r["topic"], notes[r["id"]]), "\n".join(notes[r["id"]])) for r in b25_blog._bench()]
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        print(len(rows), cell, "prompts")


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {v: sum(verdicts[i] == v for i in ids) for v in ("AI", "Mixed", "Human")}
    out = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "prompts":
        prompts()
    elif cmd == "pick":
        b25_blog.pick("b26", PROMPTS, TEXTS, OUT, cells=("V",))
    elif cmd == "pick_pool":
        b25_blog.pick("b26m", POOL_PROMPTS, POOL_TEXTS, POOL_OUT, cells=("M",))
    else:
        record(sys.argv[2:])
