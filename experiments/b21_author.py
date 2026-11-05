"""B21: a real author interview. Does Henry's own material carry his post to Human?

B9: with 2/3 or more of the content from a human source, 7 to 10 of 10 pieces read Human. B19's
simulation could not stand in for an author (7 of 10 "authors" had nothing to say, because the
editor asks for first-hand experience). Here the author is real: Henry answers questions about his
own AI-rewritten post (B15's 7 sections of "context engineering", originals 0 Human, 3 Mixed, 4 AI).

Fixed before Henry answers anything:
- Questions: B19's editor prompt, 3 per section (21 in all, about 20 minutes), Sonnet, one call per
  section. Henry answers in his own words on a private page; any question may be skipped. His
  answers are used as written.
- Cell F: B15's pipeline (pool writer, the section's specific facts, 4 seeds, prune, clean, keep the
  most supported claims) with the facts of Henry's answers added to the prompt; a sentence counts as
  supported when the section or his answers support it. One variable against B15 cell B: his answers.
- Cell A: Henry's answers for each section, joined as written (his own words, the control).
- All 7 sections of each cell scanned. Pangram only scores.
Amended 09:25, before any answer was read: Pangram is unreliable under 150 words, so cell A is one
text per section only where that section's answers reach 150 words, plus one text of all his answers
in order. Sections with no answers still get an F text (then the same as B15 cell B's input).
- Machine: the Mac (MLX), as B15, after B17's generation; B15's pick (prune and claim check against
  the section plus his answers, keep the most supported claims).

Usage:
  uv run python experiments/b21_author.py questions    writes results/b21_questions.json
  uv run python experiments/b21_author.py page         writes results/b21_interview.html
  (Henry's answers, read from the page's store, saved as results/b21_answers.json {"s1-q1": "..."})
  uv run python experiments/b21_author.py prompts
  for s in 0 1 2 3: uv run python experiments/gen_mlx.py results/b21_prompts.jsonl results/b21_gen_s$s.jsonl --guard --adapter models/lora-13b-pool-mlx --seed $s
  uv run python experiments/b21_author.py pick
  uv run python experiments/b21_author.py record F_s1=AI ...
"""

import json
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.data.facts import Facts, extract, facts_prompt
from humanizer.data.lora import MAX_WORDS
from humanizer.llm import claude

sys.path.insert(0, str(ROOT / "experiments"))
from b6_selection import specific  # noqa: E402
from b11_prune import prune_one  # noqa: E402
from b13_cleanup import clean_one  # noqa: E402
from b19_interview import ASK  # noqa: E402

SECTIONS = ROOT / "results" / "b15_sections.jsonl"
QUESTIONS = ROOT / "results" / "b21_questions.json"
PAGE = ROOT / "results" / "b21_interview.html"  # published as Henry's private artifact; answers land in its db
ANSWERS = ROOT / "results" / "b21_answers.json"
PROMPTS = ROOT / "results" / "b21_prompts.jsonl"
TEXTS = ROOT / "results" / "b21_texts.jsonl"
OUT = ROOT / "results" / "b21_author.json"
PER, MIN_A = 3, 150
TITLES = {"s1": "From prompt engineering to context engineering", "s2": "The seven components",
          "s3": "Write, select, compress, isolate", "s4": "How context fails",
          "s5": "The diabetes coaching agent's token budget", "s6": "Measuring it", "s7": "The lesson"}


def questions():
    out = []
    for line in SECTIONS.open():  # one call at a time: other experiments hold the Claude workers
        s = json.loads(line)
        raw = claude(ASK.replace("5 short questions", f"{PER} short questions").format(draft=s["text"]), model="sonnet")
        qs = [str(q).strip() for q in json.loads(re.search(r"\{.*\}", raw, re.S).group(0))["questions"]][:PER]
        out.append({"id": s["id"], "title": TITLES[s["id"]], "opening": " ".join(s["text"].split()[:45]) + " ...",
                    "questions": qs})
        print(s["id"], *qs, sep="\n  ")
    QUESTIONS.write_text(json.dumps(out, indent=1))


def page():
    data = json.dumps(json.loads(QUESTIONS.read_text())).replace("</", "<\\/")
    PAGE.write_text((ROOT / "experiments" / "b21_interview_page.html").read_text().replace("__SECTIONS__", data))
    print("wrote", PAGE)


def _answered(sid: str) -> str:
    got = json.loads(ANSWERS.read_text())
    return "\n".join(got[k].strip() for k in sorted(got) if k.startswith(sid + "-") and got[k].strip())


def _support(sec: dict) -> str:
    a = _answered(sec["id"])
    return sec["text"] + ("\n\nThe author's answers to the editor:\n" + a if a else "")


def prompts():
    secs = [json.loads(line) for line in SECTIONS.open()]

    def one(sec):
        f = extract(sec["text"])
        spec = [f.facts[j] for j in specific(f)]
        a = _answered(sec["id"])
        author = extract(a).facts if a else []
        words = min(MAX_WORDS, sec["words"])
        return {"id": f"F_{sec['id']}", "source": sec["id"], "allowed_text": _support(sec),
                "prompt": facts_prompt(Facts(f.topic, spec + author), words, sec["id"]),
                "target_words": int(round(words, -1)), "max_new_tokens": int(words * 1.3 * 1.5) + 64,
                "n_facts": len(spec), "n_author_facts": len(author)}

    with ThreadPoolExecutor(4) as ex:
        rows = list(ex.map(one, secs))
    PROMPTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print([(r["id"], r["n_facts"], r["n_author_facts"], r["target_words"]) for r in rows])


def pick():
    secs = {r["id"]: r for r in map(json.loads, SECTIONS.open())}
    gens = [(s, json.loads(line)) for s in (0, 1, 2, 3) for line in (ROOT / "results" / f"b21_gen_s{s}.jsonl").open()]

    def one(item):
        s, g = item
        support = _support(secs[g["id"][2:]])
        pruned, _ = prune_one(g["text"], support)
        text, _ = clean_one(pruned)
        cc = claim_check(support, text)
        return g["id"][2:], {"seed": s, "text": text, "claims_entailed": cc["claims_entailed"], "claims_total": cc["claims_total"]}

    cands = {}
    with ThreadPoolExecutor(4) as ex:
        for key, r in ex.map(one, gens):
            cands.setdefault(key, []).append(r)
    rows = []
    for key, sec in secs.items():
        best = max(cands[key], key=lambda c: (c["claims_entailed"], c["claims_entailed"] / max(1, c["claims_total"])))
        rows.append({"id": f"F_{key}", "title": sec["title"], "seed": best["seed"], "text": best["text"],
                     "words": len(best["text"].split()), "claims_entailed": best["claims_entailed"],
                     "claims_total": best["claims_total"]})
        a = _answered(key)
        if len(a.split()) >= MIN_A:
            rows.append({"id": f"A_{key}", "title": sec["title"], "text": a, "words": len(a.split())})
    every = "\n".join(a for a in map(_answered, secs) if a)
    rows.append({"id": "A_all", "title": "All answers", "text": every, "words": len(every.split())})
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    f = [r for r in rows if r["id"][0] == "F"]
    summary = {"sections": len(f), "words_output": sum(r["words"] for r in f), "words_answers": len(every.split()),
               "claim_support": statistics.mean(r["claims_entailed"] / max(1, r["claims_total"]) for r in f)}
    OUT.write_text(json.dumps({"checks": summary}, indent=1))
    print(json.dumps(summary, indent=1))


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {c: {v: sum(verdicts[i] == v for i in ids if i[0] == c) for v in ("AI", "Mixed", "Human")} for c in "FA"}
    out = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    step = sys.argv[1]
    {"questions": questions, "page": page, "prompts": prompts, "pick": pick}.get(step, lambda: record(sys.argv[2:]))()
