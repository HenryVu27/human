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

Usage:
  uv run python experiments/b21_author.py questions    writes results/b21_questions.json
  uv run python experiments/b21_author.py page         writes results/b21_interview.html
"""

import json
import re
import sys

from humanizer import ROOT
from humanizer.llm import claude

sys.path.insert(0, str(ROOT / "experiments"))
from b19_interview import ASK  # noqa: E402

SECTIONS = ROOT / "results" / "b15_sections.jsonl"
QUESTIONS = ROOT / "results" / "b21_questions.json"
PAGE = ROOT / "results" / "b21_interview.html"  # published as Henry's private artifact; answers land in its db
PER = 3
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


if __name__ == "__main__":
    {"questions": questions, "page": page}[sys.argv[1]]()
