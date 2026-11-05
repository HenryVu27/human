"""B16: the B8 mixed-pool writer with B14's input (specific facts only), best of 4.

B14 (pool writer, specific facts, best of 4) reads 13 Human, 7 Mixed, 0 AI but loses on judged
quality (0.275 against same-topic human text). B8 (mixed-pool writer, all facts, one sample)
judges better (0.575) but reads 5 Human, 10 Mixed, 5 AI: given every fact it keeps more of the
AI plan. This crosses them: mixed-pool writer, B12's specific-fact prompts, seeds 0 to 3, each
pruned and cleaned, the most supported claims kept (b14_bestof.pick). Same drafts a0610 to a0629.

Usage:
  for s in 0 1 2 3: uv run python experiments/gen_mlx.py results/b12_prompts.jsonl results/b16_gen_s$s.jsonl --guard --adapter models/lora-13b-mixpool-mlx --seed $s
  uv run python experiments/b16_mixspec.py pick
  uv run python experiments/b16_mixspec.py record X_a0610=AI ...
"""

import json
import sys

from humanizer import ROOT

sys.path.insert(0, str(ROOT / "experiments"))
import b14_bestof  # noqa: E402

TEXTS = ROOT / "results" / "b16_texts.jsonl"
OUT = ROOT / "results" / "b16_bestof.json"


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {v: sum(verdicts[i] == v for i in ids) for v in ("AI", "Mixed", "Human")}
    out = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "pick":
        b14_bestof.pick(prefix="b16", seeds=(0, 1, 2, 3), seed0_from_b13=False, cell="X")
    else:
        record(sys.argv[2:])
