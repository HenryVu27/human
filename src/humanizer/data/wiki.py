"""Pre-2022 English Wikipedia text, for cited human sources (B24).

Every article is read as its last revision before 2022-01-01, written before ChatGPT, and that
revision's permalink is the citation. API responses are cached on disk, so a rerun makes no requests.
"""

import hashlib
import html
import json
import re
import urllib.parse
import urllib.request

from humanizer import ROOT

API = "https://en.wikipedia.org/w/api.php"
BEFORE = "2022-01-01T00:00:00Z"
CACHE = ROOT / ".cache" / "wiki"
UA = {"User-Agent": "humanizer-research/0.1 (personal research, low volume)"}
MARKER = re.compile(r"\[(\d+|[a-z]|citation needed|note \d+|clarification needed|when\?|who\?)\]")


def _get(params: dict) -> dict:
    params = {**params, "format": "json", "formatversion": 2}
    p = CACHE / f"{hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()}.json"
    if p.exists():
        return json.loads(p.read_text())
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers=UA)
    d = json.load(urllib.request.urlopen(req, timeout=30))
    CACHE.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d))
    return d


def search(query: str, n: int = 3) -> list[str]:
    return [x["title"] for x in _get({"action": "query", "list": "search", "srsearch": query, "srlimit": n})["query"]["search"]]


def revision(title: str) -> dict | None:
    """The last revision of `title` (redirects followed) before 2022, or None if there is none."""
    d = _get({"action": "query", "prop": "revisions", "titles": title, "redirects": 1, "rvlimit": 1,
              "rvstart": BEFORE, "rvdir": "older", "rvprop": "ids|timestamp"})
    page = d["query"]["pages"][0]
    if page.get("missing") or not page.get("revisions"):
        return None
    r = page["revisions"][0]
    return {"title": page["title"], "revid": r["revid"], "timestamp": r["timestamp"], "url": permalink(r["revid"])}


def _paras(page_html: str) -> list[str]:
    """Body paragraphs as plain text: tags, entities and footnote markers removed, fragments dropped."""
    out = []
    for p in re.findall(r"<p>(.*?)</p>", page_html, re.S):
        t = " ".join(MARKER.sub("", html.unescape(re.sub(r"<[^>]+>", "", p))).split())
        if len(t.split()) >= 12:
            out.append(t)
    return out


def paragraphs(revid: int) -> list[str]:
    return _paras(_get({"action": "parse", "oldid": revid, "prop": "text"})["parse"]["text"])


def permalink(revid: int) -> str:
    return f"https://en.wikipedia.org/w/index.php?oldid={revid}"
