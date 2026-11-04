"""Pangram API client. Pangram is a held-out judge: never use these scores to select anything
except the B1 gate and detector calibration (see the spec, section 8).

Every result is appended to results/pangram_log.jsonl with the model version.
"""

from __future__ import annotations

import json
import os
import time

import httpx

from humanizer import ROOT

BASE = "https://text.external-api.pangram.com"
LOG = ROOT / "results" / "pangram_log.jsonl"


def is_human(result: dict) -> bool:
    """Strict: only a clean Human verdict passes. Mixed and AI both fail."""
    return result.get("prediction_short") == "Human"


class Pangram:
    def __init__(self, api_key: str | None = None, *, client: httpx.Client | None = None, poll: float = 2.0):
        key = api_key or os.environ.get("PANGRAM_API_KEY")
        if not key:
            raise RuntimeError("PANGRAM_API_KEY is not set (Henry creates it at pangram.com/apikey)")
        self.http = client or httpx.Client(base_url=BASE, timeout=60)
        self.http.headers["x-api-key"] = key
        self.poll = poll

    def models(self) -> list[str]:
        r = self.http.get("/models")
        r.raise_for_status()
        return r.json()["models"]

    def score(self, text: str, model: str, *, tag: str = "") -> dict:
        r = self.http.post("/task", json={"text": text, "model": model})
        r.raise_for_status()
        task_id = r.json()["task_id"]
        while True:
            res = self.http.get(f"/task/{task_id}").json()
            if res.get("stage") in ("STAGE_SUCCESS", "STAGE_FAILED"):
                _log(tag, model, res)
                return res
            time.sleep(self.poll)

    def bulk(self, texts: list[str], model: str, *, ids: list[str] | None = None, tag: str = "") -> list[dict | None]:
        ids = ids or [str(i) for i in range(len(texts))]
        r = self.http.post("/bulk", json={"items": [{"id": i, "text": t} for i, t in zip(ids, texts)],
                                          "model": model})
        r.raise_for_status()
        bulk_id = r.json()["bulk_id"]
        while self.http.get(f"/bulk/{bulk_id}").json()["status"] not in ("succeeded", "failed", "partial"):
            time.sleep(self.poll)
        out: dict[int, dict | None] = {}
        offset = 0
        while True:
            page = self.http.get(f"/bulk/{bulk_id}/results", params={"offset": offset, "limit": 1000}).json()
            for item in page["items"]:
                out[item["index"]] = item.get("result")
                if item.get("result"):
                    _log(tag or item["id"], model, item["result"], item_id=item["id"])
            offset += len(page["items"])
            if not page["items"] or offset >= page["total_items"]:
                break
        return [out.get(i) for i in range(len(texts))]


def _log(tag: str, model: str, res: dict, item_id: str | None = None) -> None:
    LOG.parent.mkdir(exist_ok=True)
    keep = {k: res.get(k) for k in ("version", "prediction_short", "fraction_ai", "fraction_ai_assisted",
                                     "fraction_human", "headline")}
    keep["windows"] = [{k: w.get(k) for k in ("label", "ai_assistance_score", "humanizer_score", "start_index",
                                              "end_index")} for w in res.get("windows", [])]
    with LOG.open("a") as f:
        f.write(json.dumps({"t": time.time(), "tag": tag, "id": item_id, "model": model, **keep}) + "\n")
