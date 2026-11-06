"""B36: does B30's rewriter transfer to writers it never saw, and to whole posts at full length?

Long-form program, gate 1 (design doc docs/specs/2026-11-06-longform-program.md, amendment of 2026-11-06 09:07 CST).
B30's rewriter (OLMo-2-13B QLoRA, 630 pairs of a Sonnet post to the human essay, 13 bloggers) turned B28's Sonnet
posts from half the notes (S50, 0 of 19 Human) into 13 of 19 Human, at about 640 words, on held-out essays by
authors it trained on. B36 asks the two open questions on new material: authors it never saw (B32's test-A split,
sites never in any training corpus of the project) and posts of 1,500 to 3,000 words, rewritten section by section
because the model has 4,096 tokens. A Henry arm (Q4) runs the same rewriter on Henry's own published posts.

Rules, fixed 2026-11-06 09:07 CST, before any document is selected or labelled and before any B36 text exists.

Documents (step `select`)
- Pool: the B32 pilot corpus (results/b32_pilot_full.jsonl, 15,132 posts). The B32 outside judge's fixes are applied
  first (results/research/longform-judge-b32.md): (1) blog platforms are matched by domain ending, not substring;
  (2) merged site keys: a site's core name (the subdomain on a blog platform, otherwise the registered domain without
  its public suffix) groups wordpress.com, substack, blogspot and other platform blogs with own domains and country
  endings of the same name; (3) listing pages are dropped (paths with /page/N, /tag/, /tags/, /category/,
  /categories/, /author/, /archive, /search, a bare /YYYY/ or /YYYY/MM/ date path, or an empty path); (4) scraped
  copies and near-duplicates are dropped (word 5-gram MinHash Jaccard 0.5 or more with any other pilot post).
- Test-A: posts whose v1 split bucket (sha256("b32-split-v1:" + site) mod 100) is 90 to 94, whose merged group has
  no post outside buckets 90 to 94 and no earlier-corpus site (data/*.jsonl), 1,500 to 3,000 words.
- Calib (B34): bucket 75 to 79, same fixes, not an earlier-corpus site, 1,800 to 3,000 words.
- Page type: Claude Haiku (humanizer.llm) labels each candidate in the order sha256("b36-v1:" + id) (B34's calib
  candidates in the order sha256("b34-v1:" + id)) from its first 1,200 words with the PAGE prompt below; a post is
  eligible if the type is personal_post or technical_post and single_author is true. Labelling stops when the
  quotas are met.
- B36 takes the first 32 eligible test-A posts in order, with at least 8 technical posts: if the first 32 hold fewer,
  the last personal posts are replaced by the next technical ones. B34 takes the first 10 eligible calib posts as H
  and the next 8 as openings for B.
- A post whose notes Sonnet refuses, or whose D post comes back under 1,000 words, is replaced by the next eligible
  post before any generation; replacements are reported.

Inputs, B35 for test-A (step `inputs`), B28's pipeline unchanged except the source of the posts
- Notes: B25's NOTES prompt (Sonnet) on the whole post; B27's reword_all (Sonnet); the 50% dose: a fixed random order
  of the reworded notes (seed "b36" + id), the first round(0.5 n) kept in the notes' order. Title: the topic the
  NOTES prompt returns.
- D: Sonnet writes the post with B25's DRAFT prompt (title, first person, about the human post's words rounded to 10)
  from the 50% notes; converted to plain text with B25's plain().

CAI-old, the rewriter (steps `prompts`, Modal experiments/modal/lf_rewrite_hf.py, `pick`)
- Sections of D: paragraphs (lines) accumulated until a section has at least 600 words; a final section under 300
  words joins the previous one; a single paragraph over 1,000 words stands alone.
- Per section: B30's prompt ("Draft:\\n{section}\\n\\nRewrite:\\n"), the Guard over the section, max new tokens
  min(round(1.3 x 1.5 x words) + 64, 4,096 - 1.5 x prompt words - 32); B30's adapter (Volume b31-weights,
  adapters/b30-rewritepool) on 4-bit NF4 OLMo-2-1124-13B, temperature 0.8, top-p 0.95, repetition penalty 1.05; seeds
  0 and 1, batched on Modal (lf_rewrite_hf.py docstring).
- Per section and seed: prune against the section (B11's prune_one), template repeats dropped (B24), cleanup (B13's
  clean_one), claim check against the section; the seed with the most supported claims is kept (B30's rule). The
  kept sections are joined in order.

Henry arm (Q4), the same rewriter on Henry's published posts
- Posts: ~/personal/blog/series/ai-engineering/part1.html and ~/personal/blog/series/bandits/part1.html. Prose
  sections by B15's rule (each h2 section's paragraphs, list items, h3 and blockquotes; code, tables, figures,
  "Contents", "References" and the series navigation left out); sections under 50 words dropped; sections over 1,000
  words split by the section rule above. Rewritten and picked exactly as CAI-old, against the original section.
- Confidentiality: one post names its client work as a "diabetes coaching agent" on purpose. Before the claim check,
  any output sentence containing a health-condition or medical term from HEALTH below that its input section lacks is
  deleted. Client and person names are blocked by the Guard (capitalized words must come from the input).
- Cells: HO_post and HR_post (the original and rewritten prose of each post, sections joined in order), HR_<post>_sN
  (each rewritten section of 150 words or more), HO_bandits_sN (each original bandits section of 150 words or more).
  The ai-engineering originals were scanned in B15 (O_s1 to O_s7, 0 Human, 3 Mixed, 4 AI) and are not rescanned.

Cells, scan and exclusions
- Per test-A post: D300, Dfull, C300, Cfull (C is CAI-old). A 300 cut ends at the last sentence end at or before 300
  words (at least 250 words, else a hard cut at 300); full is the whole text.
- B34's texts and these go into one blinded scan: 8-hex-character file names, one shuffled order (seed "b36"),
  batches of up to 100 .docx files, Pangram label and AI share read from the dashboard.
- A text under 150 words counts as not Human (B25's rule); it is still scanned. A C text copying more than 15% of
  its words from the human post in 8-word runs is excluded from the primary analysis and reported. Credits: B36 about
  1,500, the Henry arm about 270, B34 about 420; stop before 2,500.

Analysis (step `analyze`)
- Primary, Holm over two: (1) Cfull against Dfull, Wilcoxon signed-rank on Pangram's AI share, paired by post, two
  sided (McNemar on Human against not Human reported as secondary); (2) C300 against Cfull, McNemar on Human (the
  length effect on the same texts). Human rates with Wilson 95% intervals.
- Checks per C text: length against D and the human post, claims supported, copying from D and from the human post
  (8-word runs), first person and sentence-length spread.
- Decision bands, fixed now. B30's rewriter transfers to unseen writers at full length if Cfull reads Human on 16 or
  more of 32 with claims supported 0.90 or more and length 70% or more of D; partly if 8 to 15; not if 7 or fewer.
- Predictions: Dfull Human on at most 3 of 32 (B28 S50 0 of 19). Cfull Human on fewer posts than C300 (the 90% rule).
  Henry arm: rewritten sections read more human than the originals on most sections; no claim on the whole posts.
- What it implies for the gates (fixed now): transfers, then gate 2 should go to Henry's genre, drafts and quality,
  not base-model scale; does not, then gate 2's long-context training is the next step; partly, then both, with the
  300-word against full comparison deciding whether length or authors is the bottleneck.

Usage:
  uv run python experiments/b36_transfer.py select
  uv run python experiments/b36_transfer.py inputs
  uv run python experiments/b36_transfer.py prompts
  modal run experiments/modal/lf_rewrite_hf.py --prompts results/b36_prompts.jsonl --out results/b36_gen.jsonl --seeds 0,1
  uv run python experiments/b36_transfer.py pick
  uv run python experiments/b36_transfer.py scanfiles DIR      (after B34's pick)
  uv run python experiments/b36_transfer.py record FILE        (lines {"name", "label", "ai_share"})
  uv run python experiments/b36_transfer.py analyze
"""

from __future__ import annotations

import hashlib
import html
import json
import random
import re
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.copying import copied_share
from humanizer.data.facts import parse_facts
from humanizer.llm import claude, claude_many

sys.path.insert(0, str(ROOT / "experiments"))
from b11_prune import prune_one  # noqa: E402
from b13_cleanup import clean_one  # noqa: E402
from b24_cited import _drop_repeats  # noqa: E402
from b25_blog import DRAFT, NOTES, plain, voice  # noqa: E402
from b27_reworded import reword_all  # noqa: E402

RES = ROOT / "results"
FULL = RES / "b32_pilot_full.jsonl"
DOCS = RES / "b36_docs.jsonl"
B34_DOCS = RES / "b34_docs.jsonl"
LABELS = RES / "b36_labels.jsonl"
INPUTS = RES / "b36_inputs.jsonl"
PROMPTS = RES / "b36_prompts.jsonl"
GEN = RES / "b36_gen.jsonl"
TEXTS = RES / "b36_texts.jsonl"
OUT = RES / "b36_transfer.json"
BLIND = RES / "b36_blind.json"
PANGRAM = RES / "b36_pangram.jsonl"
CONTEXT = 4096
HENRY_POSTS = {"aieng": Path.home() / "personal/blog/series/ai-engineering/part1.html",
               "bandits": Path.home() / "personal/blog/series/bandits/part1.html"}
SKIP = {"Contents", "References", "AI Engineering"}
PLATFORMS = ("blogspot.com", "wordpress.com", "substack.com", "tumblr.com", "typepad.com", "livejournal.com",
             "ghost.io", "github.io", "svbtle.com", "posthaven.com", "bearblog.dev", "hashnode.dev", "wixsite.com",
             "weebly.com", "medium.com", "home.blog", "netlify.app")
LISTING = re.compile(r"/page/\d+|/tags?/|/categor(y|ies)/|/author/|/archives?(/|$)|/search|^/(19|20)\d\d/?$|"
                     r"^/(19|20)\d\d/[01]\d/?$|^/?$", re.I)
HEALTH = ("cancer", "diabet", "obes", "hypertens", "asthma", "depress", "anxiety", "adhd", "autis", "alzheimer",
          "dementia", "parkinson", "epilep", "arthrit", "hiv", "aids", "hepatit", "covid", "insulin", "kidney", "renal",
          "cardiac", "heart disease", "stroke", "copd", "celiac", "crohn", "lupus", "migraine", "schizophren",
          "bipolar", "ptsd", "eating disorder", "anorexi", "bulimi", "addict", "opioid", "chemo", "tumor", "tumour",
          "oncolog", "pregnan", "fertility", "ivf", "menopaus", "thyroid", "cholesterol", "apnea", "insomnia",
          "glucose", "a1c", "blood sugar", "weight loss", "patient", "clinic", "hospital", "disease", "disorder",
          "syndrome", "diagnos", "therapy", "medication", "prescri")
PAGE = """Classify this web page. Return only JSON: {{"type": "...", "single_author": true or false}}.

Types:
- personal_post: one person's blog post about their own life, experience, opinions or hobbies, in their own voice.
- technical_post: one person's blog post explaining or discussing a technical subject (software, data, engineering, science, tools).
- company_or_marketing: written for a business, to promote or sell.
- news_or_magazine: a reported article or a magazine piece.
- transcript_or_interview: a transcript, question-and-answer or interview.
- listing_or_archive: a page that joins several posts, teasers or excerpts.
- spam_or_machine_made: spun, keyword-stuffed or auto-generated text.
- fiction_or_poetry, or other.

single_author: true if one person wrote the whole page in their own voice.

<page>
{text}
</page>"""


def _h(salt: str, key: str) -> str:
    return hashlib.sha256(f"{salt}{key}".encode()).hexdigest()


def bucket(site: str) -> int:
    return int(_h("b32-split-v1:", site), 16) % 100


def _host_path(url: str) -> tuple[str, str]:
    m = re.match(r"https?://([^/?#]+)([^?#]*)", url)
    host = (m.group(1) if m else url).lower().split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    return host, (m.group(2) if m else "") or "/"


SUFFIXES = {"blog", "info", "online", "site", "website", "space", "tech", "life", "world", "today", "xyz", "club",
            "media", "news", "page", "live", "studio", "design", "art", "photo", "travel", "net", "org", "com", "edu"}


def core_name(url: str) -> str:
    """The judge's merged key: the blog's own name, without platform or public suffix."""
    host, path = _host_path(url)
    for p in PLATFORMS:
        if host == p or host.endswith("." + p):
            if p == "medium.com" and host == p:
                seg = [s for s in path.split("/") if s]
                return seg[0].lstrip("@").lower() if seg else "medium"
            sub = host[: -len(p) - 1] if host != p else p
            return sub.split(".")[-1]
    parts = host.split(".")
    if "blogspot" in parts and parts.index("blogspot") > 0:
        return parts[parts.index("blogspot") - 1]
    while len(parts) > 1 and (len(parts[-1]) <= 3 or parts[-1] in SUFFIXES):
        parts = parts[:-1]
    return parts[-1]


def is_listing(url: str) -> bool:
    return bool(LISTING.search(_host_path(url)[1]))


def _minhash(text: str, n_perm: int = 64):
    import numpy as np

    words = re.findall(r"\w+", text.lower())
    grams = {" ".join(words[i:i + 5]) for i in range(max(1, len(words) - 4))}
    hs = np.array([int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "little") for g in grams],
                  dtype=np.uint64)
    a = (np.arange(n_perm, dtype=np.uint64) * np.uint64(2) + np.uint64(1)) * np.uint64(0x9E3779B97F4A7C15)
    b = np.arange(n_perm, dtype=np.uint64) * np.uint64(0xBF58476D1CE4E5B9)
    return (hs[None, :] * a[:, None] + b[:, None]).min(axis=1)


def select():
    import numpy as np

    rows = [json.loads(line) for line in FULL.open()]
    prior = set()
    for f in (ROOT / "data").glob("*.jsonl"):
        for line in f.open():
            try:
                u = json.loads(line).get("url")
            except (json.JSONDecodeError, AttributeError):
                continue
            if isinstance(u, str) and u.startswith("http"):
                prior.add(core_name(u))
    groups: dict[str, set[int]] = {}
    for r in rows:
        r["core"] = core_name(r["url"])
        r["bucket"] = bucket(r["site"])
        groups.setdefault(r["core"], set()).add(r["bucket"])
    stats = {"pilot": len(rows), "listing": sum(is_listing(r["url"]) for r in rows), "prior_cores": len(prior)}
    sigs = np.stack([_minhash(r["text"]) for r in rows])
    bands: dict[tuple, list[int]] = {}
    near = set()
    for i, s in enumerate(sigs):  # 32 bands of 2 rows: a pair at Jaccard 0.5 shares a band with probability 0.9999
        hit = set()
        for j in range(0, 64, 2):
            key = (j, s[j:j + 2].tobytes())
            hit.update(bands.get(key, ()))
            bands.setdefault(key, []).append(i)
        for k in hit:
            if (sigs[k] == s).mean() >= 0.5:
                near.update((i, k))
    stats["near_duplicate_posts"] = len(near)
    pools = {"testA": [], "calib": []}
    for i, r in enumerate(rows):
        if is_listing(r["url"]) or i in near or r["core"] in prior or r.get("prior_site"):
            continue
        if 90 <= r["bucket"] <= 94 and groups[r["core"]] <= set(range(90, 95)) and 1500 <= r["words"] <= 3000:
            pools["testA"].append(r)
        if 75 <= r["bucket"] <= 79 and 1800 <= r["words"] <= 3000:
            pools["calib"].append(r)
    stats |= {f"pool_{k}": len(v) for k, v in pools.items()}
    stats["testA_dropped_for_merged_group"] = sum(1 for r in rows if 90 <= r["bucket"] <= 94
                                                  and not groups[r["core"]] <= set(range(90, 95)))
    labels = {json.loads(line)["id"]: json.loads(line) for line in LABELS.open()} if LABELS.exists() else {}

    def label_until(cands, salt, need, tech_min):
        cands = sorted(cands, key=lambda r: _h(salt, r["id"]))
        chosen, i = [], 0
        while i < len(cands):
            batch = [r for r in cands[i:i + 8] if r["id"] not in labels]
            if batch:
                got = claude_many([PAGE.format(text=" ".join(r["text"].split()[:1200])) for r in batch], model="haiku")
                with LABELS.open("a") as f:
                    for r, g in zip(batch, got):
                        m = re.search(r"\{.*\}", g or "", re.S)
                        try:
                            d = json.loads(m.group(0)) if m else {}
                        except json.JSONDecodeError:
                            d = {}
                        lab = {"id": r["id"], "type": d.get("type"), "single_author": d.get("single_author")}
                        labels[r["id"]] = lab
                        f.write(json.dumps(lab) + "\n")
            for r in cands[i:i + 8]:
                lab = labels[r["id"]]
                if lab["type"] in ("personal_post", "technical_post") and lab["single_author"] is True:
                    chosen.append(r | {"page_type": lab["type"]})
            i += 8
            tech = sum(r["page_type"] == "technical_post" for r in chosen)
            if len(chosen) >= need and (tech_min == 0 or tech >= tech_min):
                break
        return chosen, i

    a, seen_a = label_until(pools["testA"], "b36-v1:", 40, 8)
    eligible = a
    first = eligible[:32]
    tech = [r for r in first if r["page_type"] == "technical_post"]
    if len(tech) < 8:
        extra = [r for r in eligible[32:] if r["page_type"] == "technical_post"][: 8 - len(tech)]
        pers = [r for r in first if r["page_type"] == "personal_post"]
        drop = {r["id"] for r in pers[len(pers) - len(extra):]}
        first = [r for r in first if r["id"] not in drop] + extra
    reserve = [r for r in eligible if r["id"] not in {x["id"] for x in first}]
    c, seen_c = label_until(pools["calib"], "b34-v1:", 18, 0)
    keep = ("id", "url", "site", "core", "bucket", "date", "dump", "words", "genre", "page_type", "text")
    DOCS.write_text("".join(json.dumps({k: r[k] for k in keep} | {"role": "test"}) + "\n" for r in first)
                    + "".join(json.dumps({k: r[k] for k in keep} | {"role": "reserve"}) + "\n" for r in reserve))
    B34_DOCS.write_text("".join(json.dumps({k: r[k] for k in keep} | {"role": "H" if i < 10 else "B"}) + "\n"
                                for i, r in enumerate(c[:18])))
    stats |= {"testA_labelled": seen_a, "testA_eligible_seen": len(eligible), "b36_docs": len(first),
              "b36_tech": sum(r["page_type"] == "technical_post" for r in first), "b36_reserve": len(reserve),
              "calib_labelled": seen_c, "b34_docs": len(c[:18]),
              "label_types": {t: sum(1 for x in labels.values() if x["type"] == t) for t in
                              sorted({x["type"] or "none" for x in labels.values()})}}
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {"select": stats}, indent=1))
    print(json.dumps(stats, indent=1))


def dose(notes: list[str], key: str, d: float = 0.5) -> list[str]:
    order = list(range(len(notes)))
    random.Random(f"b36{key}").shuffle(order)
    keep = sorted(order[:max(1, round(d * len(notes)))])
    return [notes[i] for i in keep]


def inputs():
    docs = [json.loads(line) for line in DOCS.open()]
    test, reserve = [d for d in docs if d["role"] == "test"], [d for d in docs if d["role"] == "reserve"]
    out, replaced = [], []
    queue = list(test)
    while queue and len(out) < 32:
        batch, queue = queue[: 32 - len(out)], queue[32 - len(out):]
        raws = claude_many([NOTES.format(text=d["text"]) for d in batch], model="sonnet")
        ok = []
        for d, x in zip(batch, raws):
            try:
                p = parse_facts(x) if x and "{" in x else None
            except Exception:  # noqa: BLE001
                p = None
            if p and p.facts:
                ok.append((d, p))
            else:
                replaced.append({"id": d["id"], "why": "notes refused or unparsable"})
                if reserve:
                    queue.append(reserve.pop(0) | {"role": "test"})
        if not ok:
            continue
        reworded, kept = reword_all([p.facts for _, p in ok])
        halves = [dose(w, d["id"]) for (d, _), w in zip(ok, reworded)]
        posts = claude_many([DRAFT.format(title=p.topic, words=int(round(d["words"], -1)),
                                          notes="\n".join(f"- {x}" for x in h)) for (d, p), h in zip(ok, halves)],
                            model="sonnet")
        for (d, p), w, h, post in zip(ok, reworded, halves, posts):
            text = plain(post) if post else ""
            if len(text.split()) < 1000:
                replaced.append({"id": d["id"], "why": f"D under 1,000 words ({len(text.split())})"})
                if reserve:
                    queue.append(reserve.pop(0) | {"role": "test"})
                continue
            out.append({"id": d["id"], "title": p.topic, "words": d["words"], "page_type": d["page_type"],
                        "notes": p.facts, "reworded": w, "dose50": h, "D": text,
                        "notes_copied": copied_share("\n".join(p.facts), d["text"]),
                        "reworded_copied": copied_share("\n".join(w), d["text"]),
                        "D_copied": copied_share(text, d["text"])})
    INPUTS.write_text("".join(json.dumps(r) + "\n" for r in out))
    summ = {"docs": len(out), "replaced": replaced,
            "notes_per_100_words": statistics.mean(100 * len(r["notes"]) / r["words"] for r in out),
            "notes_copied": statistics.mean(r["notes_copied"] for r in out),
            "reworded_copied": statistics.mean(r["reworded_copied"] for r in out),
            "D_copied_from_post": statistics.mean(r["D_copied"] for r in out),
            "D_words": statistics.mean(len(r["D"].split()) for r in out),
            "D_over_post": statistics.mean(len(r["D"].split()) / r["words"] for r in out)}
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {"inputs": summ}, indent=1))
    print(json.dumps(summ, indent=1))


def sections(text: str, lo: int = 600, hi: int = 1000, tail: int = 300) -> list[str]:
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    out, cur = [], []
    for p in paras:
        if len(p.split()) > hi:
            if cur:
                out.append(cur)
                cur = []
            out.append([p])
            continue
        cur.append(p)
        if sum(len(x.split()) for x in cur) >= lo:
            out.append(cur)
            cur = []
    if cur:
        if out and sum(len(x.split()) for x in cur) < tail:
            out[-1] = out[-1] + cur
        else:
            out.append(cur)
    return ["\n".join(s) for s in out]


def henry_sections(path: Path) -> list[dict]:
    """B15's extraction: each h2 section's prose, code, tables and figures left out."""
    s = path.read_text()
    parts = re.split(r"(<h2[^>]*>.*?</h2>)", s)
    out = []
    for i in range(1, len(parts), 2):
        title = re.sub(r"^\d+", "", html.unescape(re.sub("<[^>]+>", "", parts[i])).strip()).strip()
        if title in SKIP:
            continue
        body = re.sub(r"(?s)<(script|style|pre|code|nav|header|footer|table|figure|svg)[^>]*>.*?</\1>", "", parts[i + 1])
        paras = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", p))).strip()
                 for p in re.findall(r"(?s)<(?:p|li|h3|blockquote)[^>]*>(.*?)</(?:p|li|h3|blockquote)>", body)]
        text = "\n".join(p for p in paras if p)
        if len(text.split()) >= 50:
            out.append({"title": title, "text": text})
    return out


def _prompt_row(pid: str, section: str) -> dict:
    prompt = f"Draft:\n{section}\n\nRewrite:\n"
    words = len(section.split())
    room = CONTEXT - int(len(prompt.split()) * 1.5) - 32
    return {"id": pid, "prompt": prompt, "allowed_text": section, "words": words,
            "max_new_tokens": min(int(round(words * 1.3 * 1.5)) + 64, room)}


def prompts():
    rows = []
    for r in map(json.loads, INPUTS.open()):
        for k, s in enumerate(sections(r["D"])):
            rows.append(_prompt_row(f"C_{r['id']}_{k}", s) | {"doc": r["id"], "part": k, "arm": "C"})
    for post, path in HENRY_POSTS.items():
        k = 0
        for si, sec in enumerate(henry_sections(path), 1):
            for sub in sections(sec["text"]):
                rows.append(_prompt_row(f"HR_{post}_{si}_{k}", sub) | {"doc": post, "part": k, "section": si, "arm": "HR"})
                k += 1
    PROMPTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(len(rows), "section prompts;", sum(r["arm"] == "C" for r in rows), "C,", sum(r["arm"] == "HR" for r in rows),
          "Henry; tokens requested", sum(r["max_new_tokens"] for r in rows))


SENT = re.compile(r"(?<=[.!?])\s+")


def confidential(text: str, source: str) -> tuple[str, int]:
    """Delete sentences that bring in a health or medical term the source section lacks."""
    low = source.lower()
    banned = [t for t in HEALTH if t not in low]
    keep, dropped = [], 0
    for para in text.split("\n"):
        sents = [s for s in SENT.split(para) if s]
        ok = [s for s in sents if not any(t in s.lower() for t in banned)]
        dropped += len(sents) - len(ok)
        if ok:
            keep.append(" ".join(ok))
    return "\n".join(keep), dropped


def pick():
    prm = {p["id"]: p for p in map(json.loads, PROMPTS.open())}
    gens = [json.loads(line) for line in GEN.open()]

    def one(g):
        p = prm[g["id"]]
        text, dropped = confidential(g["text"], p["allowed_text"]) if p["arm"] == "HR" else (g["text"], 0)
        pruned, _ = prune_one(text, p["allowed_text"])
        cleaned, _ = clean_one(_drop_repeats(pruned))
        cc = claim_check(p["allowed_text"], cleaned)
        return g["id"], {"seed": g["seed"], "text": cleaned, "raw_words": g["words"], "hit_eos": g["hit_eos"],
                         "confidential_dropped": dropped, "claims_entailed": cc["claims_entailed"],
                         "claims_total": cc["claims_total"], "unsupported_specifics": cc["unsupported_specifics"]}

    samples: dict[str, list] = {}
    with ThreadPoolExecutor(4) as ex:
        for key, s in ex.map(one, gens):
            samples.setdefault(key, []).append(s)
    best = {k: max(v, key=lambda c: (c["claims_entailed"], c["claims_entailed"] / max(1, c["claims_total"])))
            for k, v in samples.items()}
    inputs_ = {r["id"]: r for r in map(json.loads, INPUTS.open())}
    docs = {r["id"]: r for r in map(json.loads, DOCS.open())}
    texts = []
    for doc in inputs_:
        parts = sorted((p for p in prm.values() if p["arm"] == "C" and p["doc"] == doc), key=lambda p: p["part"])
        if not all(p["id"] in best for p in parts):
            continue
        t = "\n\n".join(best[p["id"]]["text"] for p in parts)
        ce = sum(best[p["id"]]["claims_entailed"] for p in parts)
        ct = sum(best[p["id"]]["claims_total"] for p in parts)
        human, d = docs[doc]["text"], inputs_[doc]["D"]
        texts.append({"id": f"C_{doc}", "cell": "C", "doc": doc, "text": t, "words": len(t.split()),
                      "D_words": len(d.split()), "human_words": docs[doc]["words"], "sections": len(parts),
                      "claims_entailed": ce, "claims_total": ct, "copied_from_D": copied_share(t, d),
                      "copied_from_human": copied_share(t, human), "D_copied_from_human": copied_share(d, human),
                      "voice": voice(t), "D_voice": voice(d), "human_voice": voice(human),
                      "seeds": [best[p["id"]]["seed"] for p in parts]})
    for post, path in HENRY_POSTS.items():
        secs = henry_sections(path)
        parts = sorted((p for p in prm.values() if p["arm"] == "HR" and p["doc"] == post), key=lambda p: p["part"])
        by_sec: dict[int, list] = {}
        for p in parts:
            by_sec.setdefault(p["section"], []).append(best[p["id"]]["text"])
        orig = "\n\n".join(s["text"] for s in secs)
        rew = "\n\n".join("\n".join(v) for _, v in sorted(by_sec.items()))
        ce = sum(best[p["id"]]["claims_entailed"] for p in parts)
        ct = sum(best[p["id"]]["claims_total"] for p in parts)
        texts.append({"id": f"HO_{post}", "cell": "HO_post", "doc": post, "text": orig, "words": len(orig.split())})
        texts.append({"id": f"HR_{post}", "cell": "HR_post", "doc": post, "text": rew, "words": len(rew.split()),
                      "claims_entailed": ce, "claims_total": ct, "copied_from_original": copied_share(rew, orig),
                      "confidential_dropped": sum(best[p["id"]]["confidential_dropped"] for p in parts),
                      "voice": voice(rew), "original_voice": voice(orig)})
        for si, v in sorted(by_sec.items()):
            t = "\n".join(v)
            if len(t.split()) >= 150:
                texts.append({"id": f"HR_{post}_s{si}", "cell": "HR_sec", "doc": post, "section": si, "text": t,
                              "words": len(t.split()), "original_words": len(secs[si - 1]["text"].split())})
            if post == "bandits" and len(secs[si - 1]["text"].split()) >= 150:
                texts.append({"id": f"HO_{post}_s{si}", "cell": "HO_sec", "doc": post, "section": si,
                              "text": secs[si - 1]["text"], "words": len(secs[si - 1]["text"].split())})
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in texts))
    c = [r for r in texts if r["cell"] == "C"]
    summ = {"C_texts": len(c), "C_words": statistics.mean(r["words"] for r in c),
            "C_over_D": statistics.mean(r["words"] / r["D_words"] for r in c),
            "C_over_human": statistics.mean(r["words"] / r["human_words"] for r in c),
            "C_claim_support": statistics.mean(r["claims_entailed"] / max(1, r["claims_total"]) for r in c),
            "C_copied_from_D": statistics.mean(r["copied_from_D"] for r in c),
            "C_copied_from_human": statistics.mean(r["copied_from_human"] for r in c),
            "C_over_15pct_copied_from_human": sum(r["copied_from_human"] > 0.15 for r in c),
            "henry": {r["id"]: {k: r.get(k) for k in ("words", "claims_entailed", "claims_total", "copied_from_original",
                                                     "confidential_dropped")} for r in texts if r["cell"] == "HR_post"}}
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {"checks": summ}, indent=1))
    print(json.dumps(summ, indent=1))


def cut300(text: str, n: int = 300, lo: int = 250) -> str:
    words = text.split()
    if len(words) <= n:
        return text
    head = " ".join(words[:n])
    ends = [m.end() for m in re.finditer(r"[.!?][\"')\]]?(?=\s|$)", head)]
    good = [e for e in ends if len(head[:e].split()) >= lo]
    return head[:good[-1]] if good else head


def scan_texts() -> list[dict]:
    """Every text of the B34 and B36 scan, with its cell and doc."""
    out = []
    for r in map(json.loads, INPUTS.open()):
        out += [{"key": f"D300_{r['id']}", "cell": "D300", "doc": r["id"], "text": cut300(r["D"])},
                {"key": f"Dfull_{r['id']}", "cell": "Dfull", "doc": r["id"], "text": r["D"]}]
    for r in map(json.loads, TEXTS.open()):
        if r["cell"] == "C":
            out += [{"key": f"C300_{r['doc']}", "cell": "C300", "doc": r["doc"], "text": cut300(r["text"])},
                    {"key": f"Cfull_{r['doc']}", "cell": "Cfull", "doc": r["doc"], "text": r["text"]}]
        else:
            out.append({"key": r["id"], "cell": r["cell"], "doc": r["doc"], "text": r["text"]})
    b34 = RES / "b34_texts.jsonl"
    if b34.exists():
        for r in map(json.loads, b34.open()):
            out.append({"key": r["key"], "cell": r["cell"], "doc": r["doc"], "text": r["text"]})
    return out


def scanfiles(dest: str):
    import math

    texts = scan_texts()
    for t in texts:
        t["words"] = len(t["text"].split())
    credits = sum(math.ceil(t["words"] / 100) for t in texts)
    print(len(texts), "texts,", credits, "credits")
    if credits > 2500:
        sys.exit("over the 2,500-credit cap; stop")
    rng = random.Random("b36")
    rng.shuffle(texts)
    d = Path(dest)
    keymap, used = {}, set()
    for i, t in enumerate(texts):
        name = rng.randbytes(4).hex()
        while name in used:
            name = rng.randbytes(4).hex()
        used.add(name)
        sub = d / f"batch{i // 100:02d}"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / f"{name}.txt").write_text(t["text"] + "\n")
        subprocess.run(["textutil", "-convert", "docx", str(sub / f"{name}.txt")], check=True)
        (sub / f"{name}.txt").unlink()
        keymap[name] = {"key": t["key"], "cell": t["cell"], "doc": t["doc"], "words": t["words"], "batch": i // 100}
    BLIND.write_text(json.dumps(keymap, indent=1))


def record(path: str):
    keymap = json.loads(BLIND.read_text())
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    out = [keymap[r["name"]] | r for r in rows]
    PANGRAM.write_text("".join(json.dumps(r) + "\n" for r in out))
    print(len(out), "verdicts of", len(keymap))


def _wilson(k: int, n: int) -> list[float]:
    z = 1.96
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / (1 + z * z / n)
    return [round(c - h, 3), round(c + h, 3)]


def analyze():
    from scipy.stats import binomtest, wilcoxon

    rows = [json.loads(line) for line in PANGRAM.open()]
    texts = {r["doc"]: r for r in map(json.loads, TEXTS.open()) if r["cell"] == "C"}
    for r in rows:
        r["human"] = r["label"] == "Human" and r["words"] >= 150
    by = {}
    for r in rows:
        by.setdefault(r["cell"], {})[r["doc"]] = r
    cells = {}
    for c, d in sorted(by.items()):
        k = sum(v["human"] for v in d.values())
        cells[c] = {"n": len(d), "human": k, "human_ci": _wilson(k, len(d)),
                    "labels": {x: sum(v["label"] == x for v in d.values()) for x in ("Human", "Mixed", "AI")},
                    "mean_ai_share": round(statistics.mean(v["ai_share"] for v in d.values()), 3)}
    excl = {doc for doc, t in texts.items() if t["copied_from_human"] > 0.15}

    def paired(a, b, docs=None):
        docs = sorted((set(by.get(a, {})) & set(by.get(b, {}))) - excl if docs is None else docs)
        ya = [by[a][x]["human"] for x in docs]
        yb = [by[b][x]["human"] for x in docs]
        up = sum(p and not q for p, q in zip(ya, yb))
        down = sum(q and not p for p, q in zip(ya, yb))
        diffs = [by[b][x]["ai_share"] - by[a][x]["ai_share"] for x in docs]
        pw = float(wilcoxon(diffs, zero_method="zsplit").pvalue) if any(diffs) else 1.0
        pm = float(binomtest(up, up + down, 0.5).pvalue) if up + down else 1.0
        return {"pairs": len(docs), "a_only_human": up, "b_only_human": down, "p_mcnemar": round(pm, 5),
                "mean_ai_share_b_minus_a": round(statistics.mean(diffs), 3), "p_wilcoxon": round(pw, 6)}

    prim = {"Cfull_vs_Dfull": paired("Cfull", "Dfull"), "C300_vs_Cfull": paired("C300", "Cfull")}
    ps = [prim["Cfull_vs_Dfull"]["p_wilcoxon"], prim["C300_vs_Cfull"]["p_mcnemar"]]
    order = sorted(range(2), key=lambda i: ps[i])
    holm = [False, False]
    for rank, i in enumerate(order):
        if ps[i] <= 0.05 / (2 - rank):
            holm[i] = True
        else:
            break
    prim["Cfull_vs_Dfull"]["holm_reject"], prim["C300_vs_Cfull"]["holm_reject"] = holm
    prim["D300_vs_Dfull"] = paired("D300", "Dfull")
    cf = cells.get("Cfull", {}).get("human", 0)
    band = "transfers" if cf >= 16 else "partly" if cf >= 8 else "does not transfer"
    out = {"cells": cells, "primary": prim, "excluded_copying": sorted(excl), "band_by_human_count": band,
           "henry": {r["key"]: {k: r[k] for k in ("label", "ai_share", "words")} for r in rows if r["cell"].startswith("H")
                     and r["cell"] not in ("H300", "Hfull")}}
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {"pangram": out}, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd in ("scanfiles", "record"):
        {"scanfiles": scanfiles, "record": record}[cmd](sys.argv[2])
    else:
        {"select": select, "inputs": inputs, "prompts": prompts, "pick": pick, "analyze": analyze}[cmd]()
