"""Check text files with the Pangram API and show which passages it flags. Henry runs this himself, because the
credential guard (rightly) stops agents loading .env:

    cd ~/personal/human && set -a && . ./.env && set +a && .venv/bin/python experiments/pangram_check.py FILE [FILE ...]

Prints each file's label and AI share, then every segment with its label. Costs 1 API unit per started 100 words.
The summary (no text) is appended to results/pangram_log.jsonl by humanizer.eval.pangram.
"""
import sys

import httpx

from humanizer.eval.pangram import Pangram


def segments(res):
    return res.get("windows") or res.get("segments") or []


def main(paths):
    try:
        client = Pangram()
    except RuntimeError as e:
        sys.exit(f"{e}\nLoad the key first: set -a && . ./.env && set +a")
    for path in paths:
        text = open(path, encoding="utf-8").read().strip()
        print(f"\n=== {path} ({len(text.split())} words)")
        try:
            res = client.score(text, "pangram-4", tag=f"check:{path.rsplit('/', 1)[-1]}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP {e.response.status_code}: {e.response.text[:300]}")
            if e.response.status_code == 402:
                print("402 means the API has no credit on this key: paste into the dashboard instead.")
            return
        print(f"verdict: {res.get('prediction_short')}  AI share: {res.get('fraction_ai')}  "
              f"AI-assisted: {res.get('fraction_ai_assisted')}  model: {res.get('version')}")
        for seg in segments(res):
            start, end = seg.get("start_index"), seg.get("end_index")
            body = text[start:end] if isinstance(start, int) and isinstance(end, int) else seg.get("text", "")
            print(f"\n[{seg.get('label')}] {' '.join(body.split())}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
