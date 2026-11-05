"""Does the quality judge prefer Sonnet's style over real human writing?

For human articles h0610 to h0629 (dev, never trained on), cut each to about 400 words at a
paragraph break, then have Sonnet condense the full article to the same length (B10's prompt).
The judge compares the human cut against the Sonnet condensation in both orders. If it prefers
Sonnet nearly always, the judge rewards Sonnet's style and cannot rate base-model prose fairly.

Usage: uv run python experiments/judge_calibrate.py
"""

import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.quality import quality_pair
from humanizer.llm import claude

sys.path.insert(0, str(ROOT / "experiments"))
from b10_compress import CONDENSE  # noqa: E402


def _cut(text: str, n: int = 400) -> str:
    out, w = [], 0
    for para in text.split("\n"):
        if w >= n and out:
            break
        out.append(para)
        w += len(para.split())
    return "\n".join(out)


def main():
    human = [json.loads(line)["text"] for line in (ROOT / "data" / "human.jsonl").open()]

    def one(i):
        cut = _cut(human[i])
        condensed = claude(CONDENSE.format(n=int(round(len(cut.split()), -1)), text=human[i]), model="sonnet").strip()
        return {"id": f"h{i:04d}", "human_words": len(cut.split()), "sonnet_words": len(condensed.split()),
                "human_beats_sonnet": quality_pair(condensed, cut)}

    with ThreadPoolExecutor(2) as ex:
        rows = list(ex.map(one, range(610, 630)))
    out = {"human_win_rate_vs_sonnet_condensation": statistics.mean(r["human_beats_sonnet"] for r in rows), "rows": rows}
    (ROOT / "results" / "judge_calibrate.json").write_text(json.dumps(out, indent=1))
    print(out["human_win_rate_vs_sonnet_condensation"], [r["human_beats_sonnet"] for r in rows])


if __name__ == "__main__":
    main()
