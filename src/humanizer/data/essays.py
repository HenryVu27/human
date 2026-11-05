"""Personal blog essays by named writers, all published before ChatGPT, for the blog track (B25 on).

The B12 benchmark drafts come from FineWeb pages (essay mills, SEO and health sites): median 0
first-person words per 100, and 7% above 1 per 100. The humanizer's main use is a personal blog post,
so this collects that genre from writers known for a personal voice, everything published before
ChatGPT's release (CUTOFF). Henry named Paul Graham, Richard Sutton, Fernando Borretti (zetalyrae)
and economists; the rest are added for range (software, rationalist and economics essayists).

Every request goes out one at a time, at least GAP seconds apart, and is cached on disk, so a rerun
sends nothing. The texts stay in data/ (gitignored); only ids, urls and counts are committed.

Selection is fixed here, before any text is read: per writer, eligible posts (400 to 3,000 words,
at most 30% quoted, not a links, open-thread or comments post) are ordered by a hash of their url;
the first 2 of 500 to 1,500 words are the benchmark split, and the next CAP of any length the
training split.

Usage:
  uv run python -m humanizer.data.essays            # writes data/essays.jsonl
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import threading
import time
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

import requests

from humanizer import ROOT

CUTOFF = "2022-11-30"  # ChatGPT's public release
CACHE = ROOT / ".cache" / "essays"
OUT = ROOT / "data" / "essays.jsonl"
UA = {"User-Agent": "humanizer-research/0.1 (personal research, low volume)"}
GAP, CAP, BENCH = 1.0, 60, 2
MIN_WORDS, MAX_WORDS, MAX_QUOTED = 400, 3000, 0.3
SKIP_TITLE = re.compile(r"open thread|^links|links for|link ?dump|highlights from|comments on|"
                        r"mailbag|meetups?\b|book club|^ot\d|bleg|assorted links|what i.m reading", re.I)
_LOCK = threading.Lock()
MONTHS = "January February March April May June July August September October November December".split()


def fetch(url: str) -> str:
    """GET one url as text: cached, serialized, GAP seconds apart, retrying 429 and 5xx."""
    p = CACHE / f"{hashlib.sha256(url.encode()).hexdigest()}.txt"
    if p.exists():
        return p.read_text()
    with _LOCK:
        for attempt in range(5):
            time.sleep(GAP)
            r = requests.get(url, headers=UA, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(float(r.headers.get("Retry-After") or 2 ** (attempt + 2)))
                continue
            break
    if r.status_code != 200:
        return ""
    CACHE.mkdir(parents=True, exist_ok=True)
    r.encoding = r.encoding if r.encoding and r.encoding.lower() != "iso-8859-1" else r.apparent_encoding
    p.write_text(r.text)
    return r.text


def text_of(page_html: str) -> tuple[str, float]:
    """Body text as paragraphs, and the share of words that sat in blockquotes (dropped).

    Code, tables, figures, scripts and quoted passages are removed: the corpus is the writer's own prose.
    """
    h = re.sub(r"(?is)<(script|style|pre|table|figure|figcaption|nav|footer|header|sup)\b.*?</\1>", " ", page_html)
    quoted = sum(len(_strip(q).split()) for q in re.findall(r"(?is)<blockquote\b.*?</blockquote>", h))
    h = re.sub(r"(?is)<blockquote\b.*?</blockquote>", "\n\n", h)
    h = re.sub(r"(?i)<br\s*/?>\s*<br\s*/?>", "\n\n", h)
    h = re.sub(r"(?i)<li\b[^>]*>", "\n\n- ", h)
    h = re.sub(r"(?i)</(p|div|h[1-6]|li|ul|ol)>|<(p|h[1-6])\b[^>]*>", "\n\n", h)
    paras = [" ".join(_strip(b).split()) for b in h.split("\n\n")]
    body = "\n\n".join(p for p in paras if p and p != "-")
    words = len(body.split())
    return body, quoted / max(1, quoted + words)


def _strip(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", fragment))


def trim(text: str) -> str:
    """Drop header lines (title, byline, date: paragraphs under 6 words) and trailing thanks-for-drafts lines."""
    paras = text.split("\n\n")
    while paras and len(paras[0].split()) < 6:
        paras.pop(0)
    while paras and re.match(r"(Thanks|Thank you)\b", paras[-1]):
        paras.pop()
    return "\n\n".join(paras)


def _post(author: str, url: str, title: str, date: str, page_html: str) -> dict:
    text, quoted = text_of(page_html)
    text = trim(text)
    return {"author": author, "url": url, "title": " ".join(_strip(title).split()), "date": date[:10],
            "words": len(text.split()), "quoted": round(quoted, 3), "text": text}


# Sources. Each yields candidate posts newest first; dates are ISO strings.

def blogger(author: str, host: str):
    for start in range(1, 5000, 150):
        d = json.loads(fetch(f"https://{host}/feeds/posts/default?alt=json&max-results=150&start-index={start}"
                             f"&published-max={CUTOFF}T00:00:00") or "{}")
        entries = d.get("feed", {}).get("entry", [])
        for e in entries:
            link = next((x["href"] for x in e["link"] if x["rel"] == "alternate"), "")
            yield _post(author, link, e["title"]["$t"], e["published"]["$t"], e.get("content", {}).get("$t", ""))
        if len(entries) < 150:
            return


def wordpress(author: str, host: str, pages: int = 12):
    for page in range(1, pages + 1):
        rows = json.loads(fetch(f"https://{host}/wp-json/wp/v2/posts?per_page=100&page={page}"
                                f"&before={CUTOFF}T00:00:00&_fields=date,link,title,content") or "[]")
        if not isinstance(rows, list) or not rows:
            return
        for r in rows:
            yield _post(author, r["link"], r["title"]["rendered"], r["date"], r["content"]["rendered"])


def substack(author: str, host: str, want: int):
    slugs = []
    for offset in range(0, 6000, 50):
        got = json.loads(fetch(f"https://{host}/api/v1/archive?sort=new&limit=50&offset={offset}") or "[]")
        got = got.get("posts", []) if isinstance(got, dict) else got
        slugs += [(x["slug"], x["post_date"]) for x in got if x["post_date"][:10] < CUTOFF and x.get("audience") != "only_paid"]
        if not got or len(slugs) >= want:
            break
    for slug, date in sorted(slugs, key=lambda s: _rank(s[0]))[:want]:
        d = json.loads(fetch(f"https://{host}/api/v1/posts/{slug}") or "{}")
        if d.get("body_html"):
            yield _post(author, d.get("canonical_url", slug), d.get("title", ""), date, d["body_html"])


def feed(author: str, url: str):
    """RSS or Atom with full content."""
    root = ET.fromstring(fetch(url))
    ns = {"a": "http://www.w3.org/2005/Atom", "c": "http://purl.org/rss/1.0/modules/content/"}
    for e in root.iter("{http://www.w3.org/2005/Atom}entry"):
        link = (e.find("a:link", ns) if e.find("a:link", ns) is not None else {}).get("href", "")
        date = (e.findtext("a:published", "", ns) or e.findtext("a:updated", "", ns))
        yield _post(author, link, e.findtext("a:title", "", ns), date, e.findtext("a:content", "", ns))
    for e in root.iter("item"):
        date = parsedate_to_datetime(e.findtext("pubDate")).isoformat()
        yield _post(author, e.findtext("link"), e.findtext("title", ""), date,
                    e.findtext("c:encoded", "", ns) or e.findtext("description", ""))


def indexed(author: str, index: str, pattern: str, want: int | None = None, url_date=None):
    """Posts linked from an index page. With url_date, dates come from urls and only `want` are fetched."""
    links = list(dict.fromkeys(urljoin(index, m) for m in re.findall(pattern, fetch(index))))
    if url_date:
        links = sorted((u for u in links if url_date(u) and url_date(u) < CUTOFF), key=_rank)[:want]
    for u in links:
        page = fetch(u)
        date = url_date(u) if url_date else _page_date(page)
        if date and date < CUTOFF:
            yield _post(author, u, (re.search(r"(?is)<title>(.*?)</title>", page) or [None, ""])[1], date, _main(page))


def _page_date(page: str) -> str | None:
    m = re.search(r'article:published_time" content="(\d{4}-\d{2}-\d{2})', page)
    if m:
        return m.group(1)
    m = re.search(r"\b(%s)\s+(?:\d{1,2},?\s+)?(\d{4})\b" % "|".join(MONTHS), _strip(page[:20000]))  # "June 2021"
    return f"{m.group(2)}-{MONTHS.index(m.group(1)) + 1:02d}-01" if m else None


def _main(page: str) -> str:
    """The article body where a page marks one; Paul Graham's essays sit in one verdana font block."""
    for pat in (r"(?is)<article\b.*?</article>", r'(?is)<div class="(?:post-content|content|entry-content)".*</div>',
                r'(?is)<font size="2" face="verdana">.*</font>'):
        m = re.search(pat, page)
        if m:
            return m.group(0)
    return page


def _url_date(u: str) -> str | None:
    m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", u)
    return "-".join(m.groups()) if m else None


def _rank(key: str) -> str:
    return hashlib.sha256(f"essays-{key}".encode()).hexdigest()


AUTHORS = {
    "Paul Graham": lambda a: indexed(a, "https://paulgraham.com/articles.html", r'href="([a-z0-9]+\.html)"'),
    "Richard Sutton": lambda a: indexed(a, "http://incompleteideas.net/IncIdeas/", r'href="([A-Za-z]+\.html)"'),
    "Fernando Borretti": lambda a: indexed(a, "https://borretti.me/article/", r'href="(/article/[a-z0-9-]+)"'),
    "Julia Evans": lambda a: indexed(a, "https://jvns.ca/", r'href="(/blog/\d{4}/\d{2}/\d{2}/[^"#]+)"', 3 * CAP, _url_date),
    "Patrick McKenzie": lambda a: indexed(a, "https://www.kalzumeus.com/archive/", r'href="(/\d{4}/\d{2}/\d{2}/[^"#]+)"',
                                          3 * CAP, _url_date),
    "Dan Luu": lambda a: feed(a, "https://danluu.com/atom.xml"),
    "Joel Spolsky": lambda a: wordpress(a, "www.joelonsoftware.com"),
    "Scott Alexander": lambda a: wordpress(a, "slatestarcodex.com"),
    "Scott Sumner": lambda a: wordpress(a, "www.themoneyillusion.com"),
    "Noah Smith": lambda a: blogger(a, "noahpinion.blogspot.com"),
    "John Cochrane": lambda a: blogger(a, "johnhcochrane.blogspot.com"),
    "Branko Milanovic": lambda a: blogger(a, "glineq.blogspot.com"),
    "Robin Hanson": lambda a: substack(a, "www.overcomingbias.com", 3 * CAP),
}


def eligible(p: dict) -> bool:
    return (MIN_WORDS <= p["words"] <= MAX_WORDS and p["quoted"] <= MAX_QUOTED and p["date"] < CUTOFF
            and not SKIP_TITLE.search(p["title"]))


def split(posts: list[dict]) -> list[dict]:
    """The fixed rule from the docstring: hash order; first BENCH of 500 to 1,500 words, then CAP for training."""
    ranked = sorted((p for p in posts if eligible(p)), key=lambda p: _rank(p["url"]))
    bench = [p for p in ranked if 500 <= p["words"] <= 1500][:BENCH]
    train = [p for p in ranked if p not in bench][:CAP]
    return [p | {"split": "bench"} for p in bench] + [p | {"split": "train"} for p in train]


def build(only: list[str] | None = None) -> None:
    rows = [json.loads(line) for line in OUT.open()] if OUT.exists() else []
    rows = [r for r in rows if only and r["author"] not in only]
    for author, source in AUTHORS.items():
        if only and author not in only:
            continue
        posts = list(source(author))
        kept = split(posts)
        rows += kept
        print(f"{author}: {len(posts)} fetched, {sum(map(eligible, posts))} eligible, "
              f"{sum(p['split'] == 'bench' for p in kept)} bench, {sum(p['split'] == 'train' for p in kept)} train",
              flush=True)
    for r in rows:
        r["id"] = "e" + _rank(r["url"])[:8]
    OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))


if __name__ == "__main__":
    build(sys.argv[1:] or None)
