"""Pangram REST client for held-out checks (never an optimization signal; see CLAUDE.md).

Async API: POST /task, then poll GET /task/{id}. Every completed response is cached
by text hash in results/pangram_cache/, so a text is never paid for twice.
The key comes from the PANGRAM_API_KEY environment variable.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

import requests

from humanizer import ROOT

URL = "https://text.external-api.pangram.com"
MODEL = "pangram-4.1"
CACHE = ROOT / "results" / "pangram_cache"
USD_PER_100_WORDS = 0.05


def _headers() -> dict:
    key = os.environ.get("PANGRAM_API_KEY")
    if not key:
        raise SystemExit("set PANGRAM_API_KEY")
    return {"x-api-key": key, "Content-Type": "application/json"}


def cached(text: str) -> dict | None:
    p = CACHE / (hashlib.sha256(f"{MODEL}\n{text}".encode()).hexdigest() + ".json")
    return json.loads(p.read_text()) if p.exists() else None


def scan(text: str, *, timeout: float = 300) -> dict:
    if (hit := cached(text)) is not None:
        return hit
    h = _headers()
    r = requests.post(f"{URL}/task", headers=h, json={"text": text, "model": MODEL}, timeout=60)
    r.raise_for_status()
    task = r.json()["task_id"]
    t0 = time.time()
    while True:
        res = requests.get(f"{URL}/task/{task}", headers=h, timeout=60).json()
        if res.get("stage") == "STAGE_SUCCESS":
            break
        if res.get("stage") == "STAGE_FAILED" or time.time() - t0 > timeout:
            raise RuntimeError(f"pangram task {task}: {res}")
        time.sleep(2)
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / (hashlib.sha256(f"{MODEL}\n{text}".encode()).hexdigest() + ".json")).write_text(json.dumps(res))
    return res


def cost(texts: list[str]) -> float:
    """Estimated USD for the texts not yet cached."""
    return sum(len(t.split()) for t in texts if cached(t) is None) / 100 * USD_PER_100_WORDS
