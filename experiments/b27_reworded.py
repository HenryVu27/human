"""B27: is it the blogger's content or the essay's wording?

B25: Sonnet's posts from the essayists' notes read 8 Human, 5 Mixed, 0 AI (the essays 13 Human).
Those notes keep the essay's wording (20 to 65% of their words sit in 8-word runs from the essay), and
the posts copy 11 to 64%. The Human posts copy more (mean 37%) than the Mixed ones (21%). B5 separated
the same two on FineWeb with the local writer: reworded human facts still read 7 of 10 Human. This
repeats that test with Sonnet as the writer, on blog essays, which is how a blogger would use AI.

Fixed before any B27 text exists (2026-11-05 17:58):
- The 13 B25 test essays and their B25 notes.
- Notes reworded with B5's REWORD prompt (humanizer.data.facts.REWORD: no run of three or more words
  from the original apart from names, numbers and quotes; same meaning; one for one), in chunks of 20.
  A chunk whose count comes back wrong is asked again up to twice, then kept unreworded (reported).
- Manipulation check: the notes' 8-word copying from the essay, before and after.
- Cell W: Sonnet writes the post from the reworded notes with B25's DRAFT prompt (same title, same
  length T, notes in the same order). Checks: copying from the essay, overall and beyond the notes;
  length against the essay; first person and sentence-length spread against the essay.
- Pangram on all 13, as plain text (B25's `plain`), paired with D essay by essay.
Prediction: if the blogger's content drives the verdict, W reads like D (6 or more Human, at most 1
AI). If the essay's wording carried it, W falls to mostly Mixed or AI.
Credits: about 115 of the 186 left.

Usage:
  uv run python experiments/b27_reworded.py write
  uv run python experiments/b27_reworded.py record W_e1234abcd=Human ...
"""

import json
import re
import statistics
import sys

from humanizer import ROOT
from humanizer.checks.copying import copied_share
from humanizer.data.facts import REWORD, parse_facts
from humanizer.llm import claude, claude_many

sys.path.insert(0, str(ROOT / "experiments"))
from b25_blog import DRAFT, _bench, plain, voice  # noqa: E402

TEXTS = ROOT / "data" / "b27_texts.jsonl"  # reworded notes stay with the bench, out of git
OUT = ROOT / "results" / "b27_reworded.json"
CHUNK = 20


def _parse(raw: str | None, n: int) -> list[str] | None:
    m = re.search(r"\{(.*)\}", raw or "", re.S)
    try:
        out = parse_facts('{"topic": "", ' + m.group(1) + "}").facts if m else []
    except (json.JSONDecodeError, KeyError, ValueError):
        return None
    return [x.removesuffix(".") for x in out] if len(out) == n else None


def _prompt(chunk: list[str], attempt: int) -> str:
    listing = "\n".join(f"{i}. {x}" for i, x in enumerate(chunk, 1))
    return REWORD.format(n=len(chunk), facts=listing) + ("" if attempt == 0 else f"\n\n(Attempt {attempt + 1}.)")


def reword_all(notes: list[list[str]]) -> tuple[list[list[str]], int]:
    """Every note list reworded chunk by chunk; returns the lists and the number of chunks kept as is."""
    chunks = [(i, n[j:j + CHUNK]) for i, n in enumerate(notes) for j in range(0, len(n), CHUNK)]
    got = [_parse(raw, len(c)) for (_, c), raw in zip(chunks, claude_many([_prompt(c, 0) for _, c in chunks], model="sonnet"))]
    kept = 0
    for k, ((_, c), g) in enumerate(zip(chunks, got)):
        for attempt in (1, 2):
            if g is not None:
                break
            g = _parse(claude(_prompt(c, attempt), model="sonnet"), len(c))
        kept += g is None
        got[k] = g if g is not None else c
    out = [[] for _ in notes]
    for (i, _), g in zip(chunks, got):
        out[i] += g
    return out, kept


def write():
    rows = _bench()
    reworded, kept = reword_all([r["notes"] for r in rows])
    drafts = claude_many([DRAFT.format(title=r["title"], words=int(round(r["words"], -1)),
                                       notes="\n".join(f"- {x}" for x in n)) for r, n in zip(rows, reworded)], model="sonnet")
    per, texts = {}, []
    for r, n, d in zip(rows, reworded, drafts):
        d = plain(d)
        texts.append({"id": f"W_{r['id']}", "source": r["id"], "notes": n, "text": d})
        per[f"W_{r['id']}"] = {"author": r["author"], "words": len(d.split()), "over_essay": len(d.split()) / r["words"],
                               "notes_copied_before": copied_share("\n".join(r["notes"]), r["text"]),
                               "notes_copied_after": copied_share("\n".join(n), r["text"]),
                               "copied_from_essay": copied_share(d, r["text"]),
                               "essay_beyond_notes": copied_share(d, r["text"], beyond="\n".join(n)),
                               "voice": voice(d), "essay_voice": voice(r["text"])}
    TEXTS.write_text("".join(json.dumps(t) + "\n" for t in texts))
    keys = ("over_essay", "notes_copied_before", "notes_copied_after", "copied_from_essay", "essay_beyond_notes")
    summary = {k: statistics.mean(p[k] for p in per.values()) for k in keys} | {"chunks_not_reworded": kept}
    OUT.write_text(json.dumps({"checks": summary, "per_text": per}, indent=1))
    print(json.dumps(summary, indent=1))
    for k, p in per.items():
        print(k, p["author"][:16], f"notes {p['notes_copied_before']:.2f} -> {p['notes_copied_after']:.2f}",
              f"post copied {p['copied_from_essay']:.2f} beyond notes {p['essay_beyond_notes']:.2f}")


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {v: sum(verdicts[i] == v for i in ids) for v in ("AI", "Mixed", "Human")}
    out = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    write() if sys.argv[1] == "write" else record(sys.argv[2:])
