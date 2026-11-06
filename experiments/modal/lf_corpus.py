"""B32 corpus stage: long pre-ChatGPT blog posts from FineWeb, filtered on Modal CPU containers.

Part of the long-form program (docs/specs/2026-11-06-longform-program.md). Each container downloads one FineWeb
parquet shard (about 2.1 GB, pinned dataset revision), filters it with the rules below and writes the kept rows to
the Modal Volume "longform" (/b32/<tag>/shards/). A second CPU function deduplicates across shards, caps documents
per site, assigns the site-level split and writes /b32/<tag>/corpus.jsonl on the Volume. Locally, only metadata
(results/b32_<tag>_meta.jsonl), a pilot sample with texts (results/b32_<tag>_corpus.jsonl) and a numeric summary
(results/b32_<tag>_summary.json) are written; the jsonl files are gitignored, so texts never go into git.

  modal run experiments/modal/lf_corpus.py --dumps CC-MAIN-2021-31 --files 0 --tag probe       # yield probe
  modal run experiments/modal/lf_corpus.py --dumps CC-MAIN-2019-35,CC-MAIN-2020-40,CC-MAIN-2021-31,CC-MAIN-2022-33

Rules, fixed 2026-11-06 02:03 CST, before the first shard was read:
- Date: FineWeb's `date` is the Common Crawl capture time (WARC-Date). Only dumps that ended before 2022-11-30 are
  read (CC-MAIN-2022-40 is the last; 2022-49 straddles ChatGPT's release), and every row must have
  date < 2022-11-30. A capture before that date proves the text was online before ChatGPT.
- English with FineWeb language_score >= 0.90.
- Length: token_count 1,900 to 6,000 (GPT-2 tokens) as a cheap pre-filter, then 1,500 to 4,000 whitespace words
  after trailing comment or share blocks are cut.
- Blog-like URL: a blog platform host (BLOG_HOSTS), or a path with /blog, /post(s)/, /archives/ or a /YYYY/MM/
  date; news and magazine hosts are excluded (NEWS).
- Genre: first-person singular rate >= 1.0 per 100 words for a personal post, or >= 0.5 per 100 with a technical
  vocabulary rate >= 8 per 1,000 words for a technical post (tag `tech`, else `personal`).
- Exclusions: spam or commerce terms (2 or more hits), dialogue-heavy text (fiction), and list-like text (over half
  the lines under 6 words).
- Dedup (local): exact normalized URL, then MinHash (word 5-grams, 128 permutations, Jaccard >= 0.8) across all
  shards; the earliest capture is kept.
- Site: the author-level key (subdomain on blog platforms, first path segment on medium.com and dev.to, otherwise
  the registered domain). At most --per-site documents per site, chosen by a hash of the URL, not by content.
- Pilot sample (amendment 2026-11-06 02:10 CST, after the one-shard probe and before the pilot run): --per-site
  defaults to 1; the local sample is up to 400 documents, half `tech` and half `personal`, ordered by
  sha256("b32-sample-v1:" + id). The probe showed `tech` is about 5% of kept posts.
- Split by site: sha256("b32-split-v1:" + site) mod 100: 0 to 79 train, 80 to 89 dev, 90 to 99 test. Sites that
  appear in the project's earlier training corpora (data/human.jsonl, data/techblog.jsonl, the essay corpus) are
  forced to train, so no earlier writer has seen a dev or test site.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re

import modal

app = modal.App("b32-corpus")
VOL = modal.Volume.from_name("longform", create_if_missing=True)  # full corpus texts live here, never in git
FINEWEB = "HuggingFaceFW/fineweb"
FINEWEB_REV = "9bb295ddab0e05d785b879661af7260fed5140fc"  # main on 2026-11-06
CUTOFF = "2022-11-30"
IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("pyarrow==21.0.0", "huggingface_hub[hf_xet]", "tldextract==5.3.0")
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "HF_XET_HIGH_PERFORMANCE": "1"})
)

BLOG_HOSTS = ("blogspot.", "wordpress.com", "medium.com", "substack.com", "tumblr.com", "typepad.com",
              "livejournal.com", "ghost.io", "github.io", "svbtle.com", "posthaven.com", "bearblog.dev",
              "write.as", "dev.to", "hashnode.dev", "wixsite.com", "weebly.com", "squarespace.com")
PLATFORM_SUB = ("blogspot", "wordpress.com", "substack.com", "tumblr.com", "typepad.com", "livejournal.com",
                "ghost.io", "github.io", "svbtle.com", "posthaven.com", "bearblog.dev", "hashnode.dev",
                "wixsite.com", "weebly.com")
BLOG_PATH = re.compile(r"/blogs?(/|$|\?)|/posts?/|/archives?/|/(19|20)\d\d/[01]\d/", re.I)
NEWS = re.compile(r"news|times|herald|tribune|gazette|journal|telegraph|guardian|reuters|bloomberg|forbes|"
                  r"cnn\.|bbc\.|npr\.|huffpost|huffingtonpost|businessinsider|buzzfeed|vice\.com|wired\.|"
                  r"theverge|techcrunch|engadget|zdnet|cnet\.|slate\.|salon\.|theatlantic|newyorker|vox\.com|"
                  r"politico|usatoday|latimes|washingtonpost|wsj\.|economist|independent\.co|dailymail|"
                  r"mirror\.co|express\.co|patch\.com|yahoo\.|msn\.com", re.I)
FIRST = re.compile(r"\b(I|I'm|I've|I'd|I'll|me|my|mine|myself)\b")
TECH = re.compile(r"\b(code|coding|python|javascript|typescript|java|rust|golang|c\+\+|api|apis|algorithm|"
                  r"software|server|servers|database|sql|linux|unix|kernel|compiler|compile|function|functions|"
                  r"variable|library|libraries|framework|deploy|deployment|query|latency|cache|gpu|cpu|docker|"
                  r"kubernetes|git|github|commit|repository|bug|debug|debugging|runtime|memory|thread|"
                  r"neural|dataset|regression|gradient|model|models|script|terminal|command|config|"
                  r"configuration|install|package|module|binary|http|json|html|css|browser|frontend|backend|"
                  r"cloud|aws|network|protocol|encryption|hardware|firmware|raspberry|arduino|programming|"
                  r"programmer|developer|engineer|engineering|test|tests|testing|performance)\b", re.I)
SPAM = re.compile(r"\b(casino|viagra|cialis|porn|escort|payday|essay writing service|buy followers|replica|"
                  r"forex|cbd oil|coupon code|promo code|affiliate link|sponsored post|betting|slot machine)\b",
                  re.I)
TAIL = re.compile(r"^\s*(leave a (reply|comment)|\d+\s+(comments?|responses?|replies)|comments?\s*$|"
                  r"share this:?|like this:?|related posts?:?|you may also like|posted (by|in)\b|"
                  r"filed under|tags?:|categories?:|about the author|subscribe to)", re.I)
URL_DATE = re.compile(r"/((?:19|20)\d\d)/([01]\d)(?:/([0-3]\d))?/")


def cut_tail(text: str) -> str:
    """Cut a trailing comment, share or tag block: the first marker line in the last 40% of the text."""
    lines = text.split("\n")
    start = int(len(lines) * 0.6)
    for i in range(start, len(lines)):
        if TAIL.match(lines[i]):
            return "\n".join(lines[:i]).rstrip()
    return text


def site_key(url: str, ext) -> str:
    m = re.match(r"https?://([^/]+)(/[^?#]*)?", url)
    host = (m.group(1) if m else url).lower().split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    path = (m.group(2) or "/") if m else "/"
    seg = [s for s in path.split("/") if s]
    if host in ("medium.com", "dev.to") and seg:
        return f"{host}/{seg[0].lower()}"
    for p in PLATFORM_SUB:
        if p in host:
            sub = host.split("." + p.split(".")[0])[0] if not host.startswith(p) else host
            return f"{sub}.{p.split('.')[0]}"
    r = ext(host)
    return getattr(r, "top_domain_under_public_suffix", None) or getattr(r, "registered_domain", None) or host


def is_bloggy(url: str) -> bool:
    host = re.sub(r"^https?://", "", url).split("/")[0].lower()
    if any(h in host for h in BLOG_HOSTS):
        return True
    return bool(BLOG_PATH.search(url)) and not NEWS.search(host)


def judge(row: dict) -> tuple[str | None, dict]:
    """Return (stage that rejected the row or None, features). Pure function of the row; no randomness."""
    url, text = row["url"], row["text"]
    if not is_bloggy(url):
        return "url", {}
    text = cut_tail(text)
    words = len(text.split())
    if not 1500 <= words <= 4000:
        return "words", {}
    first = 100 * len(FIRST.findall(text)) / words
    tech = 1000 * len(TECH.findall(text)) / words
    if len(SPAM.findall(text)) >= 2:
        return "spam", {}
    lines = [ln for ln in text.split("\n") if ln.strip()]
    if sum(ln.lstrip()[:1] in "\"“'" for ln in lines) > 0.25 * len(lines):
        return "dialogue", {}
    if sum(len(ln.split()) < 6 for ln in lines) > 0.5 * len(lines):
        return "listlike", {}
    if first >= 1.0:
        genre = "tech" if tech >= 8 else "personal"
    elif first >= 0.5 and tech >= 8:
        genre = "tech"
    else:
        return "genre", {}
    m = URL_DATE.search(url)
    return None, {"text": text, "words": words, "first_per_100": round(first, 2), "tech_per_1000": round(tech, 1),
                  "genre": genre, "url_date": "-".join(g for g in m.groups() if g) if m else None}


@app.function(image=IMAGE, cpu=4, memory=16384, timeout=3600, volumes={"/vol": VOL})
def scan_shard(dump: str, file_idx: int, tag: str) -> dict:
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    import tldextract
    from huggingface_hub import hf_hub_download

    ext = tldextract.TLDExtract(include_psl_private_domains=False)
    path = hf_hub_download(FINEWEB, f"data/{dump}/000_{file_idx:05d}.parquet", repo_type="dataset",
                           revision=FINEWEB_REV, local_dir="/tmp/fw")
    counts = {"rows": 0, "date": 0, "lang": 0, "tokens": 0}
    rejects: dict[str, int] = {}
    kept = []
    pf = pq.ParquetFile(path)
    cols = ["text", "id", "dump", "url", "date", "language_score", "token_count"]
    for batch in pf.iter_batches(batch_size=20000, columns=cols):
        counts["rows"] += batch.num_rows
        m = pc.less(batch["date"], CUTOFF)
        counts["date"] += pc.sum(m).as_py() or 0
        m = pc.and_(m, pc.greater_equal(batch["language_score"], 0.90))
        counts["lang"] += pc.sum(m).as_py() or 0
        m = pc.and_(m, pc.and_(pc.greater_equal(batch["token_count"], 1900), pc.less_equal(batch["token_count"], 6000)))
        counts["tokens"] += pc.sum(m).as_py() or 0
        for row in batch.filter(m).to_pylist():
            why, feat = judge(row)
            if why:
                rejects[why] = rejects.get(why, 0) + 1
                continue
            kept.append({"fw_id": row["id"], "dump": row["dump"], "url": row["url"], "date": row["date"],
                         "site": site_key(row["url"], ext), "token_count": row["token_count"], **feat})
    out = pathlib.Path(f"/vol/b32/{tag}/shards/{dump}_{file_idx:05d}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in kept))
    VOL.commit()
    return {"dump": dump, "file": file_idx, "counts": counts, "rejects": rejects, "kept": len(kept)}


# ----------------------------------------------------------------------------------------------- local selection

def norm_url(url: str) -> str:
    u = re.sub(r"^https?://(www\.)?", "", url.lower()).split("#")[0].split("?")[0]
    return u.rstrip("/")


def split_of(site: str) -> str:
    b = int(hashlib.sha256(f"b32-split-v1:{site}".encode()).hexdigest(), 16) % 100
    return "train" if b < 80 else "dev" if b < 90 else "test"


def minhash(text: str, n_perm: int = 128) -> list[int]:
    words = re.findall(r"\w+", text.lower())
    grams = {" ".join(words[i:i + 5]) for i in range(max(1, len(words) - 4))}
    mask = (1 << 61) - 1
    hs = [int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "little") for g in grams]
    sig = []
    for k in range(n_perm):
        a, b = 2 * k + 1, k * 0x9E3779B97F4A7C15 & mask
        sig.append(min(((a * h + b) & mask) for h in hs))
    return sig


def prior_urls() -> list[str]:
    """URLs of every earlier training corpus in the project (data/*.jsonl), read locally."""
    root = pathlib.Path(__file__).resolve().parents[2] / "data"
    urls = set()
    for f in root.glob("*.jsonl"):
        for line in f.open():
            try:
                url = json.loads(line).get("url")
            except (json.JSONDecodeError, AttributeError):
                continue
            if isinstance(url, str) and url.startswith("http"):
                urls.add(url)
    return sorted(urls)


@app.function(image=IMAGE, cpu=4, memory=16384, timeout=3600, volumes={"/vol": VOL})
def select(tag: str, per_site: int, prior: list[str], sample_n: int) -> dict:
    """Dedup, site cap and split over every shard of `tag` on the Volume; writes corpus.jsonl there and returns
    metadata for all documents plus the texts of a pilot sample (sample_n, half `tech` and half `personal` where
    possible, one per site, ordered by a hash of the URL)."""
    import tldextract

    VOL.reload()
    ext = tldextract.TLDExtract(include_psl_private_domains=False)
    prior_set = {site_key(u, ext) for u in prior}
    rows = []
    for f in sorted(pathlib.Path(f"/vol/b32/{tag}/shards").glob("*.jsonl")):
        rows.extend(json.loads(line) for line in f.read_text().splitlines())
    stats = {"in": len(rows)}
    rows = sorted(rows, key=lambda r: r["date"])  # earliest capture first, so dedup keeps it
    seen, uniq = set(), []
    for r in rows:
        k = norm_url(r["url"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    stats["after_url_dedup"] = len(uniq)
    bands: dict[tuple, int] = {}
    keep = []
    for i, r in enumerate(uniq):
        sig = minhash(r["text"])
        keys = [tuple(sig[j:j + 4]) + (j,) for j in range(0, 128, 4)]  # 32 bands of 4 rows
        cand = {bands[k] for k in keys if k in bands}
        dup = any(sum(x == y for x, y in zip(sig, keep[c]["_sig"])) / 128 >= 0.8 for c in cand)
        if dup:
            continue
        r["_sig"] = sig
        for k in keys:
            bands.setdefault(k, len(keep))
        keep.append(r)
    stats["after_minhash"] = len(keep)
    by_site: dict[str, list[dict]] = {}
    for r in keep:
        by_site.setdefault(r["site"], []).append(r)
    out = []
    for site, rs in by_site.items():
        rs.sort(key=lambda r: hashlib.sha256(f"b32-pick-v1:{norm_url(r['url'])}".encode()).hexdigest())
        out.extend(rs[:per_site])
    stats["after_site_cap"] = len(out)
    stats["sites"] = len(by_site)
    for r in out:
        r.pop("_sig", None)
        r["split"] = "train" if r["site"] in prior_set else split_of(r["site"])
        r["prior_site"] = r["site"] in prior_set
        r["id"] = "p" + hashlib.sha256(norm_url(r["url"]).encode()).hexdigest()[:10]
    stats["prior_sites_forced_train"] = sum(r["prior_site"] for r in out)
    stats["prior_sites_known"] = len(prior_set)
    pathlib.Path(f"/vol/b32/{tag}/corpus.jsonl").write_text("".join(json.dumps(r) + "\n" for r in out))
    VOL.commit()
    order = sorted(out, key=lambda r: hashlib.sha256(f"b32-sample-v1:{r['id']}".encode()).hexdigest())
    sample = []
    for g in ("tech", "personal"):
        sample.extend([r for r in order if r["genre"] == g][: sample_n // 2])
    if len(sample) < sample_n:
        have = {r["id"] for r in sample}
        sample.extend([r for r in order if r["id"] not in have][: sample_n - len(sample)])
    meta = [{k: v for k, v in r.items() if k != "text"} for r in out]
    return {"stats": stats, "meta": meta, "sample": sample}


@app.local_entrypoint()
def main(dumps: str, files: str = "0", per_site: int = 1, tag: str = "pilot", sample_n: int = 400):
    import collections

    jobs = [(d, int(f), tag) for d in dumps.split(",") for f in files.split(",")]
    res_root = pathlib.Path(__file__).resolve().parents[2] / "results"
    shard_stats = []
    for res in scan_shard.starmap(jobs, order_outputs=False):
        print(json.dumps(res), flush=True)
        shard_stats.append(res)
    prior = prior_urls()
    print(f"prior corpus URLs: {len(prior)}", flush=True)
    sel = select.remote(tag, per_site, prior, sample_n)
    meta, sample = sel["meta"], sel["sample"]
    (res_root / f"b32_{tag}_meta.jsonl").write_text("".join(json.dumps(r) + "\n" for r in meta))
    (res_root / f"b32_{tag}_corpus.jsonl").write_text("".join(json.dumps(r) + "\n" for r in sample))

    def describe(docs):
        return {"docs": len(docs), "sites": len({r["site"] for r in docs}),
                "split_docs": dict(collections.Counter(r["split"] for r in docs)),
                "split_sites": {s: len({r["site"] for r in docs if r["split"] == s}) for s in ("train", "dev", "test")},
                "genre": dict(collections.Counter(r["genre"] for r in docs)),
                "dump": dict(collections.Counter(r["dump"] for r in docs)),
                "words_median": sorted(r["words"] for r in docs)[len(docs) // 2] if docs else None,
                "url_dated": sum(bool(r.get("url_date")) for r in docs)}

    summary = {"fineweb_revision": FINEWEB_REV, "shards": shard_stats, "select": sel["stats"],
               "corpus_on_volume": describe(meta), "pilot_sample": describe(sample)}
    (res_root / f"b32_{tag}_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
