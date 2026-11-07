"""A0: one test of the Pangram API on Henry's Professional plan (approved with phase 1, 2026-11-06).

Calls GET /models, then one POST /task with model "pangram-4" on the first 100 words of a B34 human post
(H300 cell, already scanned Human on the dashboard). One credit unit. Nothing is selected by this call.

Run with the key loaded into the environment by the shell, never printed:
    set -a; . ./.env; set +a; .venv/bin/python experiments/a0_api_test.py

Writes the raw response to results/a0_api_raw.jsonl (local: it echoes the text) and a summary without text to
results/a0_api_test.json.
"""
import json
import os
import sys
import time

import httpx

BASE = "https://text.external-api.pangram.com"


def main():
    key = os.environ.get("PANGRAM_API_KEY")
    if not key:
        sys.exit("PANGRAM_API_KEY not in the environment")
    rows = [json.loads(line) for line in open("results/b34_texts.jsonl")]
    src = next(r for r in rows if r["cell"] == "H300")
    text = " ".join(src["text"].split()[:100])
    http = httpx.Client(base_url=BASE, timeout=60, headers={"x-api-key": key})
    out = {"t": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "doc": src["doc"], "words": len(text.split())}
    r = http.get("/models")
    out["models_status"] = r.status_code
    out["models"] = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:300]
    if r.status_code != 200:
        return finish(out, None)
    r = http.post("/task", json={"text": text, "model": "pangram-4"})
    out["task_status"] = r.status_code
    if r.status_code != 200:
        out["task_error"] = r.text[:500]
        return finish(out, None)
    task_id = r.json()["task_id"]
    for _ in range(60):
        res = http.get(f"/task/{task_id}").json()
        if res.get("stage") in ("STAGE_SUCCESS", "STAGE_FAILED"):
            break
        time.sleep(2)
    finish(out, res)


def finish(out, res):
    if res is not None:
        out["stage"] = res.get("stage")
        out["top_level_keys"] = sorted(res)
        out["version"] = res.get("version")
        out["prediction_short"] = res.get("prediction_short")
        for k in ("fraction_ai", "fraction_ai_assisted", "fraction_human"):
            out[k] = res.get(k)
        segs = res.get("windows") or res.get("segments") or []
        out["n_segments"] = len(segs)
        out["segment_keys"] = sorted(segs[0]) if segs else []
        with open("results/a0_api_raw.jsonl", "a") as f:
            f.write(json.dumps({"t": out["t"], "response": res}) + "\n")
    json.dump(out, open("results/a0_api_test.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
