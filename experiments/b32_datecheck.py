"""B32 publication-date audit on a sample: was each post really online before ChatGPT (2022-11-30)?

Long-form program (docs/specs/2026-11-06-longform-program.md). FineWeb's `date` field is the Common Crawl capture
time, so the corpus filter already requires a capture before the cutoff. This audit checks that claim against
sources outside FineWeb, for a random sample of the pilot corpus:

1. Common Crawl index (index.commoncrawl.org, the row's own dump): the URL has a capture in that crawl, and its
   timestamp equals FineWeb's date and is before 2022-11-30.
2. The archived page itself (data.commoncrawl.org, a byte-range read of the WARC record): the WARC-Date header is
   before the cutoff, and the FineWeb text is in the archived HTML (at least 4 of 6 evenly spaced 8-word runs of
   the text are found in the page after tags are stripped).
3. Wayback Machine CDX (web.archive.org): the earliest capture date of the URL, as a second, independent archive.
4. The URL's own date path (/YYYY/MM/), when it has one, as the stated publication month.

Sample rule (fixed before the audit ran): 30 pilot documents ordered by sha256("b32-date-v1:" + id), first 30.
Light HTTP only (about 90 requests); runs on the Mac. First run (2026-11-06 02:28 to 03:19 CST): 29 rows logged; the
30th page hung the HTML stripping (fixed since by capping the page at 1 MB), and the summary in
results/b32_pilot_datecheck.json was written from the 29 logged rows. An index count of 0 there means the query
failed after retries (rate limiting), not a missing capture.

  uv run python experiments/b32_datecheck.py --tag pilot --n 30
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import json
import pathlib
import re
import time
import urllib.parse

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
CUTOFF = "2022-11-30"
UA = {"User-Agent": "humanizer-research-date-audit (contact: repository owner)"}


def get(url: str, tries: int = 4, **kw) -> requests.Response | None:
    for k in range(tries):
        try:
            r = requests.get(url, headers=UA | kw.pop("headers", {}), timeout=60, **kw)
            if r.status_code in (200, 206):
                return r
            if r.status_code == 404:
                return r
        except requests.RequestException:
            pass
        time.sleep(3 * (k + 1))
    return None


def cc_lookup(dump: str, url: str) -> list[dict]:
    q = f"https://index.commoncrawl.org/{dump}-index?url={urllib.parse.quote(url, safe='')}&output=json"
    r = get(q)
    if r is None or r.status_code != 200:
        return []
    return [json.loads(line) for line in r.text.splitlines() if line.strip()]


def warc_text(rec: dict) -> tuple[str | None, str]:
    start = int(rec["offset"])
    end = start + int(rec["length"]) - 1
    r = get(f"https://data.commoncrawl.org/{rec['filename']}", headers={"Range": f"bytes={start}-{end}"})
    if r is None or r.status_code not in (200, 206):
        return None, ""
    raw = gzip.decompress(r.content).decode("utf-8", errors="replace")
    m = re.search(r"WARC-Date: (\S+)", raw)
    body = raw.split("\r\n\r\n", 2)[-1][:1_000_000]  # cap: a multi-megabyte page hung the regex on 2026-11-06
    body = re.sub(r"(?is)<script\b.*?</script>|<style\b.*?</style>", " ", body)
    body = html.unescape(re.sub(r"(?s)<[^>]+>", " ", body))
    return (m.group(1) if m else None), norm(body)


def norm(t: str) -> str:
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", re.sub(r"[^\w' ]+", " ", t.lower())).strip()


def runs(text: str, k: int = 6, n: int = 8) -> list[str]:
    w = norm(text).split()
    if len(w) < n:
        return []
    idx = [int(i * (len(w) - n) / max(1, k - 1)) for i in range(k)]
    return [" ".join(w[i:i + n]) for i in idx]


def wayback_first(url: str) -> str | None:
    q = f"https://web.archive.org/cdx/search/cdx?url={urllib.parse.quote(url, safe='')}&limit=1&output=json&fl=timestamp"
    r = get(q, tries=2)
    if r is None or r.status_code != 200:
        return None
    try:
        rows = r.json()
    except ValueError:
        return None
    return rows[1][0] if len(rows) > 1 else None


def main(tag: str, n: int) -> None:
    docs = [json.loads(line) for line in (ROOT / "results" / f"b32_{tag}_corpus.jsonl").read_text().splitlines()]
    docs.sort(key=lambda r: hashlib.sha256(f"b32-date-v1:{r['id']}".encode()).hexdigest())
    out = []
    for d in docs[:n]:
        recs = cc_lookup(d["dump"], d["url"])
        fw_ts = re.sub(r"\D", "", d["date"])[:14]
        rec = next((r for r in recs if r.get("timestamp") == fw_ts), recs[0] if recs else None)
        row = {"id": d["id"], "dump": d["dump"], "fineweb_date": d["date"], "url_date": d.get("url_date"),
               "cc_captures_in_dump": len(recs), "cc_timestamp": rec.get("timestamp") if rec else None}
        if rec:
            wd, body = warc_text(rec)
            hits = sum(r in body for r in runs(d["text"]))
            row |= {"warc_date": wd, "text_runs_found": hits, "text_in_page": hits >= 4}
        row["wayback_first"] = wayback_first(d["url"])
        row["before_cutoff"] = bool(row.get("warc_date") and row["warc_date"][:10] < CUTOFF)
        out.append(row)
        print(json.dumps(row), flush=True)
        time.sleep(1)
    summ = {"n": len(out),
            "cc_capture_found": sum(r["cc_captures_in_dump"] > 0 for r in out),
            "cc_timestamp_equals_fineweb": sum(r["cc_timestamp"] == re.sub(r"\D", "", r["fineweb_date"])[:14] for r in out),
            "warc_before_cutoff": sum(r["before_cutoff"] for r in out),
            "text_in_archived_page": sum(bool(r.get("text_in_page")) for r in out),
            "wayback_capture_found": sum(bool(r["wayback_first"]) for r in out),
            "wayback_first_before_cutoff": sum(bool(r["wayback_first"]) and r["wayback_first"][:8] < "20221130" for r in out),
            "url_dated": sum(bool(r["url_date"]) for r in out),
            "url_date_before_capture": sum(bool(r["url_date"]) and r["url_date"][:7] <= r["fineweb_date"][:7] for r in out)}
    (ROOT / "results" / f"b32_{tag}_datecheck.json").write_text(json.dumps({"summary": summ, "rows": out}, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="pilot")
    ap.add_argument("--n", type=int, default=30)
    a = ap.parse_args()
    main(a.tag, a.n)
