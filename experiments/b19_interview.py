"""B19: the author answers five questions. Does their material carry the piece past the detector?

B9 showed the verdict follows the share of human-sourced content: with 2/3 or more of the facts
from the human original, 7 to 10 of 10 pieces read Human. For Henry's real use the human source is
Henry: the humanizer can ask the author a few questions and write from the draft's specific facts
plus the answers. This simulates that loop on drafts whose human source exists:

1. Sonnet, as the editor, reads the AI draft and asks the author 5 questions whose answers would
   add first-hand specifics the draft lacks.
2. Sonnet, as the author, answers each one only from the human original article (the author's
   own knowledge); "No answer." when the original has nothing.
3. The answers' facts (FACTS extraction) join the draft's specific facts in the writer's prompt,
   at the draft's length.
4. B18's write, check, resample loop on the PC, where a sentence counts as supported when the
   draft or the author's answers support it; then B13's cleanup.

Fixed before any B19 text exists:
- Drafts: a0610 to a0619 (the first 10 of B12's), so B18 cell W is a paired comparison.
- Cell I: one text per draft, all 10 scanned. Pangram only scores.
- Checks: claim support against draft plus answers, coverage of the draft's facts (B18's
  measure), the share of the prompt's facts from the answers, quality against the human cut.
Limit: the "author" here is the human article's writer, read by Sonnet; a real author's answers
will be shorter, rougher and in their own words.

Usage (paragraph server running and tunnelled, as for B18):
  uv run python experiments/b19_interview.py interview
  uv run python experiments/b19_interview.py write
  uv run python experiments/b19_interview.py record I_a0610=AI ...
"""

import json
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

from humanizer import ROOT
from humanizer.checks.claims import claim_check
from humanizer.checks.quality import quality_pair
from humanizer.data.facts import Facts, extract, facts_prompt
from humanizer.data.lora import MAX_WORDS
from humanizer.llm import claude

sys.path.insert(0, str(ROOT / "experiments"))
from b6_selection import specific  # noqa: E402
from b12_replicate import _drafts  # noqa: E402
from b13_cleanup import clean_one  # noqa: E402
from b18_resample import _coverage, write_one  # noqa: E402
from judge_calibrate import _cut  # noqa: E402

IDS = [f"a{n:04d}" for n in range(610, 620)]
INTERVIEW = ROOT / "results" / "b19_interview.jsonl"
TEXTS = ROOT / "results" / "b19_texts.jsonl"
OUT = ROOT / "results" / "b19_interview.json"

ASK = """You are the editor of the draft article below. Ask its author 5 short questions whose answers would add first-hand specifics the draft lacks: concrete examples, numbers, names, what happened, what they saw or did. Each question must stay on the draft's own topic.

Return only JSON: {{"questions": ["...", "...", "...", "...", "..."]}}

<draft>
{draft}
</draft>"""

ANSWER = """You are the author of the notes below. Your editor asked you the questions that follow. Answer each in one to three plain sentences, using only what your notes say: no fact, number, name or example that is not in them. If the notes do not answer a question, write "No answer."

Return only JSON: {{"answers": ["...", "...", "...", "...", "..."]}}

<notes>
{notes}
</notes>

<questions>
{questions}
</questions>"""


def _json(raw: str, key: str) -> list[str]:
    m = re.search(r"\{.*\}", raw, re.S)
    return [str(x).strip() for x in json.loads(m.group(0))[key]] if m else []


def _support(draft: str, qa: list[dict]) -> str:
    lines = [f"Q: {x['q']}\nA: {x['a']}" for x in qa if not x["a"].lower().startswith("no answer")]
    return draft + "\n\nThe author's answers to the editor:\n" + "\n".join(lines)


def interview():
    drafts = _drafts()
    human = [json.loads(line)["text"] for line in (ROOT / "data" / "human.jsonl").open()]

    def one(k):
        qs = _json(claude(ASK.format(draft=drafts[k]), model="sonnet"), "questions")[:5]
        listing = "\n".join(f"{i}. {q}" for i, q in enumerate(qs, 1))
        ans = _json(claude(ANSWER.format(notes=human[int(k[1:])], questions=listing), model="sonnet"), "answers")
        qa = [{"q": q, "a": a} for q, a in zip(qs, ans)]
        answered = "\n".join(x["a"] for x in qa if not x["a"].lower().startswith("no answer"))
        f = extract(drafts[k])
        spec = [f.facts[j] for j in specific(f)]
        author = extract(answered).facts if answered else []
        words = min(MAX_WORDS, len(drafts[k].split()))  # as B12
        prompt = facts_prompt(Facts(f.topic, spec + author), words, k)
        return {"id": f"I_{k}", "source": k, "qa": qa, "n_draft_facts": len(spec), "n_author_facts": len(author),
                "prompt": prompt, "target_words": int(round(words, -1))}

    with ThreadPoolExecutor(4) as ex:
        rows = list(ex.map(one, IDS))
    INTERVIEW.write_text("".join(json.dumps(r) + "\n" for r in rows))
    for r in rows:
        print(r["id"], "answered", sum(not x["a"].lower().startswith("no answer") for x in r["qa"]), "of", len(r["qa"]),
              "facts", r["n_draft_facts"], "+", r["n_author_facts"])


def write():
    rows = [json.loads(line) for line in INTERVIEW.open()]
    done = {json.loads(line)["id"] for line in TEXTS.open()} if TEXTS.exists() else set()
    drafts = _drafts()
    human = [json.loads(line)["text"] for line in (ROOT / "data" / "human.jsonl").open()]

    def one(item):
        i, r = item
        support = _support(drafts[r["source"]], r["qa"])
        w = write_one(r, 100 + i, support=support, cell="I")
        text, _ = clean_one(w["raw"])
        cc = claim_check(support, text)
        out = w | {"text": text, "words": len(text.split()), "target_words": r["target_words"],
                   "claims_entailed": cc["claims_entailed"], "claims_total": cc["claims_total"],
                   "coverage": _coverage(drafts[r["source"]], text),
                   "author_share": r["n_author_facts"] / max(1, r["n_author_facts"] + r["n_draft_facts"]),
                   "quality_vs_human_cut": quality_pair(_cut(human[int(r["source"][1:])], len(text.split())), text)}
        with TEXTS.open("a") as f:
            f.write(json.dumps(out) + "\n")
        print(out["id"], out["words"], "/", r["target_words"], f"{out['claims_entailed']}/{out['claims_total']}",
              f"coverage {out['coverage']:.2f}", flush=True)

    with ThreadPoolExecutor(4) as ex:
        list(ex.map(one, [(i, r) for i, r in enumerate(rows) if r["id"] not in done]))
    res = [json.loads(line) for line in TEXTS.open()]
    summary = {"texts": len(res), "words": statistics.mean(r["words"] for r in res),
               "length_ratio": statistics.mean(r["words"] / r["target_words"] for r in res),
               "claim_support": statistics.mean(r["claims_entailed"] / max(1, r["claims_total"]) for r in res),
               "coverage": statistics.mean(r["coverage"] for r in res),
               "author_share": statistics.mean(r["author_share"] for r in res),
               "quality_vs_human_cut": statistics.mean(r["quality_vs_human_cut"] for r in res)}
    OUT.write_text(json.dumps({"checks": summary}, indent=1))
    print(json.dumps(summary, indent=1))


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {v: sum(verdicts[i] == v for i in ids) for v in ("AI", "Mixed", "Human")}
    out = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    step = sys.argv[1]
    {"interview": interview, "write": write}.get(step, lambda: record(sys.argv[2:]))()
