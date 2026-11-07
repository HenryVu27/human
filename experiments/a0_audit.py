"""A0: planted-error audit of the faithfulness checks (attempt-2 design, sections 6.1 and 8). No Pangram, no Modal.

Question: how often do the project's checks catch each kind of error a rewrite can introduce, and how often do they
flag clean text?

Hosts: B36's input sections (`b36_prompts.jsonl`, allowed_text) and B37's seed-2 rewrites of them (`b37_gen.jsonl`),
kept if the rewrite has at least 300 words and passes check_form. Seeded shuffle ("a0-audit"); the first hosts in
that order are used, 30 per error type, the same order for every type.

Error types and the check that must catch each (planted sentences are inserted at a seeded paragraph boundary):
- deterministic: number, name, date, quote -> claims.unsupported_specifics; code line -> form.new_code_lines (limit
  0); non-English sentence -> form.non_english_runs; placeholder math -> form.placeholders; series framing ->
  form.new_framing.
- semantic: wrong claim (Sonnet rewrites one supported sentence so it asserts something the source does not)
  -> claims.claim_check's unsupported claims; broken sentence (a sentence cut at 55% and joined to the second half of
  another) -> defects.prose_defects.
A plant counts as caught only if the check's finding matches the planted text (the token itself, or at least 40% of
the planted sentence's content words for the model checks).

Controls (false flags): 30 sources checked against themselves (any flag is false), and the 30 unmodified rewrites of
the semantic hosts (flags there may be real errors; reported as the baseline rate).

Bars (fixed before running): deterministic types at least 29 of 30; semantic types recall with an exact one-sided
95% lower bound, bar 0.70. One fix round, then the measured recall is reported with every result.
Model: claude-sonnet-5-5 (pinned) for every model call.

Run: .venv/bin/python experiments/a0_audit.py  -> results/a0_audit.json (numbers), results/a0_audit_cases.jsonl (local)
"""
import json
import random
import re
import sys
from pathlib import Path

from scipy.stats import beta

from humanizer.checks.claims import claim_check, unsupported_specifics
from humanizer.checks.defects import prose_defects
from humanizer.checks.form import check_form, new_code_lines, new_framing, non_english_runs, placeholders
from humanizer.llm import claude
from concurrent.futures import ThreadPoolExecutor

RES = Path("results")
MODEL = "claude-sonnet-5-5"
N = 30
SENT = re.compile(r"(?<=[.!?])\s+")
STOP = set("the a an and or but of to in on at for with is are was were be it this that i you we they as by from".split())

FIRST = ["Margaret", "Daniel", "Priya", "Tomas", "Ingrid", "Kwame", "Lucia", "Hiro", "Elena", "Owen"]
LAST = ["Okafor", "Lindqvist", "Brennan", "Castillo", "Nakamura", "Hollis", "Varga", "Mendel", "Achebe", "Sorensen"]
QUOTES = ["the hard part is knowing when to stop", "nobody reads the second page", "it only works on Tuesdays",
          "you pay for it later", "the map is not the trip"]
CODE = ["result = parse(config, strict=True);", "for (int i = 0; i < n; i++) {", "def update(state, step):",
        "cache.set(key, value);", "import numpy as np"]
FRENCH = ["Il faut dire que la plupart des gens ne savent pas ce qui se passe dans la tête de leur voisin.",
          "C'est une question que nous nous posons tous, mais personne ne veut vraiment y répondre.",
          "Nous avons passé la journée dans le jardin avec les enfants et les voisins de la rue."]
HOLES = ["The update rule is $Rewrite{n}$ at each step.", "Each reward is drawn from $Gaussian(0, 1)$ as before.",
         "We then apply {method} to the result.", "See [INSERT figure] for the full picture."]
FRAMES = ["This is the second post in my series on the subject.", "In my last post I wrote about the first half of this.",
          "Stay tuned for the next part, where I finish the story."]


def hosts():
    src = {p["id"]: p["allowed_text"] for p in map(json.loads, open(RES / "b36_prompts.jsonl"))}
    out = []
    for g in map(json.loads, open(RES / "b37_gen.jsonl")):
        if g["seed"] != 2 or g["id"] not in src or g["words"] < 300:
            continue
        if check_form(g["text"], src[g["id"]])["ok"] and not placeholders(g["text"], src[g["id"]]):
            out.append({"id": g["id"], "source": src[g["id"]], "output": g["text"]})
    random.Random("a0-audit").shuffle(out)
    return out


def insert(text, sentence, rng):
    paras = text.split("\n\n") if "\n\n" in text else text.split("\n")
    i = rng.randrange(1, len(paras)) if len(paras) > 1 else 1
    joiner = "\n\n" if "\n\n" in text else "\n"
    return joiner.join(paras[:i] + [sentence] + paras[i:])


def content(s):
    return {w for w in re.findall(r"[a-z']+", s.lower()) if w not in STOP and len(w) > 2}


def overlaps(found, planted, frac=0.4):
    p = content(planted)
    return any(p and len(content(f) & p) / len(p) >= frac for f in found)


def plant_det(kind, h, rng):
    src = h["source"]
    if kind == "number":
        n = next(x for x in (str(rng.randrange(13, 9800)) for _ in range(99)) if x not in src)
        s, token = f"By the end it had taken about {n} hours.", n
    elif kind == "name":
        token = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        s = f"My friend {token} said much the same thing."
    elif kind == "date":
        token = str(next(y for y in (rng.randrange(1961, 2020) for _ in range(99)) if str(y) not in src))
        s = f"That was back in {token}, when things were different."
    elif kind == "quote":
        token = rng.choice(QUOTES)
        s = f'As someone once told me, "{token}."'
    elif kind == "code":
        token = s = rng.choice(CODE)
    elif kind == "french":
        token = s = rng.choice(FRENCH)
    elif kind == "placeholder":
        token = s = rng.choice(HOLES)
    elif kind == "framing":
        token = s = rng.choice(FRAMES)
    return insert(h["output"], s, rng), s, token


def caught_det(kind, src, text, s, token):
    if kind in ("number", "name", "date", "quote"):
        found = unsupported_specifics(src, text)
        return any(token.rstrip(".").lower() in f.lower() or f.lower() in token.lower() for f in found), sorted(found)
    if kind == "code":
        found = new_code_lines(text, src)
    elif kind == "french":
        found = non_english_runs(text)
    elif kind == "placeholder":
        found = placeholders(text, src)
    else:
        found = new_framing(text, src)
    return any(f.strip() and (f.strip() in s or s in f or overlaps([f], s, 0.3)) for f in found), found


WRONG = """Below is a SOURCE and a REWRITE of it. Pick one sentence in the REWRITE that states something the SOURCE supports, and change it so it asserts something the SOURCE does not say or contradicts (reverse a cause, a comparison, a recommendation or an outcome). Add no numbers, names, dates or quotes, and keep the length and style. Return only JSON: {{"original": "<exact sentence from the rewrite>", "altered": "<your changed sentence>"}}

<source>
{source}
</source>

<rewrite>
{output}
</rewrite>"""


def plant_wrong(h):
    raw = claude(WRONG.format(**h), model=MODEL)
    m = re.search(r"\{.*\}", raw, re.S)
    d = json.loads(m.group(0))
    if d["original"] not in h["output"]:
        raise ValueError("original sentence not found")
    return h["output"].replace(d["original"], d["altered"], 1), d["altered"]


def plant_broken(h, rng):
    sents = [s for s in SENT.split(h["output"]) if len(s.split()) >= 12]
    a, b = rng.sample(sents, 2)
    aw, bw = a.split(), b.split()
    broken = " ".join(aw[: int(len(aw) * 0.55)] + bw[int(len(bw) * 0.5):])
    return h["output"].replace(a, broken, 1), broken


def lb(k, n):
    return 0.0 if k == 0 else float(beta.ppf(0.05, k, n - k + 1))


def main():
    hs = hosts()
    print(len(hs), "hosts pass the form checks")
    if len(hs) < N:
        sys.exit("too few hosts")
    hs = hs[:N]
    cases, summary = [], {}
    for kind in ("number", "name", "date", "quote", "code", "french", "placeholder", "framing"):
        hits = 0
        for i, h in enumerate(hs):
            rng = random.Random(f"a0-audit:{kind}:{i}")
            text, s, token = plant_det(kind, h, rng)
            ok, found = caught_det(kind, h["source"], text, s, token)
            hits += ok
            cases.append({"kind": kind, "id": h["id"], "planted": s, "caught": ok, "found": found[:5]})
        summary[kind] = {"caught": hits, "n": N, "bar": "29 of 30", "pass": hits >= 29}

    def semantic(i_h):
        i, h = i_h
        rng = random.Random(f"a0-audit:semantic:{i}")
        out = {}
        try:
            wtext, wsent = plant_wrong(h)
            cc = claim_check(h["source"], wtext, model=MODEL)
            out["wrong"] = {"caught": overlaps(cc["unsupported_claims"], wsent), "gate_fail": not cc["pass"],
                            "planted": wsent, "found": cc["unsupported_claims"][:5]}
        except Exception as e:  # noqa: BLE001
            out["wrong"] = {"error": str(e)[:200]}
        btext, bsent = plant_broken(h, rng)
        d = prose_defects(btext)
        out["broken"] = {"caught": overlaps(d, bsent), "planted": bsent, "found": d[:5]}
        base_cc = claim_check(h["source"], h["output"], model=MODEL)
        out["base"] = {"claims_unsupported": len(base_cc["unsupported_claims"]), "claims_total": base_cc["claims_total"],
                       "gate_fail": not base_cc["pass"], "defects": len(prose_defects(h["output"]))}
        self_cc = claim_check(h["source"], h["source"], model=MODEL)
        out["self"] = {"claims_unsupported": len(self_cc["unsupported_claims"]), "claims_total": self_cc["claims_total"],
                       "gate_fail": not self_cc["pass"], "defects": len(prose_defects(h["source"]))}
        return out

    with ThreadPoolExecutor(4) as ex:
        sem = list(ex.map(semantic, enumerate(hs)))
    for kind in ("wrong", "broken"):
        rows = [s[kind] for s in sem if "caught" in s[kind]]
        k = sum(r["caught"] for r in rows)
        summary[kind] = {"caught": k, "n": len(rows), "errors": N - len(rows), "lower_bound_95": round(lb(k, len(rows)), 3),
                         "bar": 0.70, "pass": lb(k, len(rows)) >= 0.70}
        if kind == "wrong":
            summary[kind]["gate_fail"] = sum(r["gate_fail"] for r in rows)
        cases += [{"kind": kind, "id": h["id"], **s[kind]} for h, s in zip(hs, sem)]
    for ctl in ("self", "base"):
        rows = [s[ctl] for s in sem]
        summary[f"control_{ctl}"] = {
            "n": len(rows),
            "claim_gate_fail": sum(r["gate_fail"] for r in rows),
            "texts_with_unsupported_claim": sum(r["claims_unsupported"] > 0 for r in rows),
            "unsupported_claim_rate": round(sum(r["claims_unsupported"] for r in rows) / max(1, sum(r["claims_total"] for r in rows)), 4),
            "texts_with_defect": sum(r["defects"] > 0 for r in rows),
        }
    json.dump({"model": MODEL, "hosts": [h["id"] for h in hs], "summary": summary}, open(RES / "a0_audit.json", "w"), indent=1)
    (RES / "a0_audit_cases.jsonl").write_text("".join(json.dumps(c) + "\n" for c in cases))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
