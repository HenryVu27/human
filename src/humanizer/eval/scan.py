"""Attempt 2 scan harness: the scoring form, blinded batches, canaries, and the record step.

Pangram stays a held-out judge (CLAUDE.md). This module only prepares and records scans; it chooses nothing.

Dashboard flow (the API key cannot be loaded by an agent, so scans go through the dashboard unless Henry runs the
API himself):
1. `write_batch(exp, texts, dest)` writes blinded .docx files and `results/<exp>_blind.json`. Commit the key.
2. Upload on the dashboard; save the page list as `results/<exp>_pangram_transcript.txt` (one line per file:
   `name.docx|N Credits,M Words|Label`) and the AI shares read by `experiments/pangram_dashboard_read.js` as
   `results/<exp>_pangram_shares.json` ([{name, ai}], ai in percent).
3. `record(exp)` joins them into `results/<exp>_pangram.jsonl` (local) and checks every key came back.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import random
import re
import subprocess
from pathlib import Path

from humanizer import ROOT

RES = ROOT / "results"

# ------------------------------------------------------------------------------------------- scoring form

FENCE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.S | re.M)
MATH_DISPLAY = re.compile(r"\$\$.+?\$\$|\\\[.+?\\\]|\\begin\{(equation|align|gather)\*?\}.+?\\end\{\1\*?\}", re.S)
MATH_INLINE = re.compile(r"\\\((.+?)\\\)|\$([^$\n]{1,120}?)\$")
PLACEHOLDER = "[equation]"


def scoring_form(text: str) -> str:
    """Reader-visible prose: code blocks removed, display math replaced by a placeholder, inline LaTeX removed
    (never currency), Markdown markers stripped. Fixed for attempt 2 (design section 6.0)."""
    t = FENCE.sub("\n", text)
    t = re.sub(r"(?m)^(?: {4}|\t)\S.*$", "", t)                           # indented code lines
    t = MATH_DISPLAY.sub(f" {PLACEHOLDER} ", t)

    def inline(m):
        body = m.group(1) if m.group(1) is not None else m.group(2)
        if m.group(1) is not None or re.search(r"[\\^_{}]", body) or re.fullmatch(r"\s*[A-Za-z](\([^)]*\))?\s*", body):
            return " "
        return m.group(0)

    t = MATH_INLINE.sub(inline, t)
    t = re.sub(r"\\[A-Za-z]+(\{[^}]*\})?", " ", t)
    t = re.sub(r"`([^`\n]+)`", r"\1", t)                                    # inline code keeps its text
    t = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", t)                             # headings
    t = re.sub(r"(?m)^\s{0,3}>\s?", "", t)                                  # quotes
    t = re.sub(r"(?m)^\s*(?:[-*+]|\d+[.)])\s+", "", t)                      # list markers
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", t)                         # images
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)                          # links
    t = re.sub(r"(\*\*|__)(.+?)\1", r"\2", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", t)
    t = re.sub(r"(?m)^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{0,}:?\s*$", "", t)  # table rules
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r" +([.,;:])", r"\1", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def credits(text: str) -> int:
    """Dashboard charge: 1 credit per started 100 words per file."""
    return max(1, math.ceil(len(text.split()) / 100))


# ------------------------------------------------------------------------------------------------ canaries

SWAPS = {"the": "this", "a": "one", "and": "plus", "but": "yet", "very": "really", "big": "large"}


def _first(path: Path, **match) -> dict:
    for line in open(path):
        r = json.loads(line)
        if all(r.get(k) == v for k, v in match.items()):
            return r
    raise KeyError(f"{path.name}: {match}")


def canaries(session: str | None = None) -> list[dict]:
    """Five frozen texts plus a sixth perturbed fresh for each session (design section 6.1).

    Frozen: a 300-word and a full human post (B34, read Human 0.00), a B36 rewrite near the line (0.09), a Sonnet
    post (B36 D, 0.81 cell), a B37 splice at 9.5% (0.08). The perturbed copy changes one common word of the
    300-word human text at a position seeded by the session date, so a cache keyed on the text cannot answer it.
    """
    session = session or dt.date.today().isoformat()
    h300 = _first(RES / "b34_texts.jsonl", key="H300_p57ff7fc44f")
    hfull = _first(RES / "b34_texts.jsonl", key="Hfull_p57ff7fc44f")
    rew = _first(RES / "b36_texts.jsonl", id="C_p8fb3502483")
    sonnet = _first(RES / "b36_inputs.jsonl", id="pd2849dd1e5")
    splice = _first(RES / "b37_splice_scan.jsonl", key="SP_pc71cc789ec_120_middle")
    out = [
        {"key": "CAN_h300", "text": h300["text"], "expect_ai": 0.00},
        {"key": "CAN_hfull", "text": hfull["text"], "expect_ai": 0.00},
        {"key": "CAN_rewrite", "text": rew["text"], "expect_ai": 0.09},
        {"key": "CAN_sonnet", "text": sonnet["D"], "expect_ai": None},
        {"key": "CAN_splice", "text": splice["text"], "expect_ai": 0.09},
    ]
    words = h300["text"].split(" ")
    spots = [i for i, w in enumerate(words) if w.lower() in SWAPS]
    i = random.Random(f"canary:{session}").choice(spots)
    w = words[i]
    words[i] = SWAPS[w.lower()].capitalize() if w[0].isupper() else SWAPS[w.lower()]
    out.append({"key": f"CAN_h300_perturbed_{session}", "text": " ".join(words), "expect_ai": 0.00})
    for c in out:
        c.update(cell="CAN", doc=c["key"])
    return out


# ------------------------------------------------------------------------------------------- blinded batches

def write_batch(exp: str, texts: list[dict], dest: str | Path, *, max_credits: int, seed: str | None = None) -> int:
    """Write each text as <random name>.docx under dest/batchNN (100 files a batch) and the key to
    results/<exp>_blind.json. Each text needs key, cell, doc, text. Refuses to write above max_credits."""
    total = sum(credits(t["text"]) for t in texts)
    if total > max_credits:
        raise SystemExit(f"{exp}: about {total} credits, over the registered {max_credits}")
    texts = list(texts)
    rng = random.Random(seed or exp)
    rng.shuffle(texts)
    keymap, used = {}, set()
    for i, t in enumerate(texts):
        name = rng.randbytes(4).hex()
        while name in used:
            name = rng.randbytes(4).hex()
        used.add(name)
        sub = Path(dest) / f"batch{i // 100:02d}"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / f"{name}.txt").write_text(t["text"] + "\n")
        subprocess.run(["textutil", "-convert", "docx", str(sub / f"{name}.txt")], check=True)
        (sub / f"{name}.txt").unlink()
        keymap[name] = {"key": t["key"], "cell": t["cell"], "doc": t["doc"], "words": len(t["text"].split()),
                        "sha": hashlib.sha256(t["text"].encode()).hexdigest()[:16]}
    (RES / f"{exp}_blind.json").write_text(json.dumps(keymap, indent=1))
    return total


# ------------------------------------------------------------------------------------------------- record

LINE = re.compile(r"^(?P<name>[0-9a-f]{8})\.docx\|(?P<credits>\d+) Credits?,(?P<words>[\d,]+) Words?\|(?P<label>Human|Mixed|AI)\s*$")


def parse_transcript(path: str | Path) -> list[dict]:
    rows = []
    for line in Path(path).read_text().splitlines():
        m = LINE.match(line.strip())
        if m:
            rows.append({"name": m["name"], "credits": int(m["credits"]),
                         "pangram_words": int(m["words"].replace(",", "")), "label": m["label"]})
    return rows


def record(exp: str) -> list[dict]:
    """Join the blinding key, transcript and shares into results/<exp>_pangram.jsonl; fail on any gap."""
    keymap = json.loads((RES / f"{exp}_blind.json").read_text())
    trans = {r["name"]: r for r in parse_transcript(RES / f"{exp}_pangram_transcript.txt")}
    shares = {s["name"].removesuffix(".docx"): s["ai"] for s in json.loads((RES / f"{exp}_pangram_shares.json").read_text())}
    missing = sorted(set(keymap) - set(trans)) + sorted(set(keymap) - set(shares))
    if missing:
        raise SystemExit(f"{exp}: no verdict or share for {missing[:10]} ({len(missing)} in all)")
    rows = [keymap[n] | trans[n] | {"name": n, "ai_share": round(shares[n] / 100, 4)} for n in keymap]
    (RES / f"{exp}_pangram.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return rows


def canary_check(rows: list[dict], reference: dict[str, dict] | None = None) -> dict:
    """Compare this session's canaries with a reference session ({key: {label, ai_share}}). Identical output on
    unchanged text is required for cross-session comparisons (design section 6.0)."""
    can = {r["key"]: r for r in rows if r["cell"] == "CAN"}
    out = {"n": len(can), "changed": []}
    if reference:
        for k, ref in reference.items():
            r = can.get(k)
            if r and (r["label"] != ref["label"] or abs(r["ai_share"] - ref["ai_share"]) > 0.02):
                out["changed"].append({"key": k, "was": ref, "now": {"label": r["label"], "ai_share": r["ai_share"]}})
    out["identical"] = not out["changed"]
    return out
