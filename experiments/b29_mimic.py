"""B29: does imitating one particular writer make the post read Human, and sound like that writer?

Henry asked (2026-11-05 evening) whether we had tried mimicking a particular writer. We had not: B17
trained on a genre and B26 on 13 essayists pooled. B26 then showed the pooled voice writer turns a
blogger's reworded notes into posts that read 11 Human, 2 Mixed, 0 AI, where Sonnet from the same notes
(B27 W) reads 1, 11, 1. This adds single-writer imitation, first with Sonnet in context (cell Y), and a
local measure of "sounds like the writer": an authorship classifier.

Fixed before any B29 text exists (2026-11-05 20:38):
- The 13 B25 test essays and B27's reworded notes for them (paired with W and V).
- Cell Y: Sonnet gets three of the same writer's posts and is asked, as that writer, to write the next
  one: B25's DRAFT prompt (title, first person, the essay's length T, markdown) with "Here are three
  posts I wrote" and "in my voice" added; nothing else changes from W. The examples are the writer's
  training-split posts of 400 to 1,200 words, first three in url-hash order (no bench essay). They are
  given unnamed, as Henry's own posts would be. Scanned as plain text.
- Authorship classifier: character 2-to-5-gram TF-IDF and logistic regression over the 660 training
  essays, 13 writers. Reported: its accuracy on the 13 real test essays (H), and for W, V and Y the share
  attributed to the right writer and the mean probability of the right writer.
- Copying (8-word runs) from the target essay and from the three examples.
- Pangram on the 13 Y texts, paired with W and V.
Prediction: Y reads like W (Mixed mostly; at most 3 Human): in B27 Sonnet's prose kept a Mixed signal
under human content, and examples change style more than the AI's way of expanding notes. Y is
attributed to the right writer more often than W. If Y reads Human on 7 or more, in-context imitation
is a cheap humanizer and a local base-model and per-writer fine-tune follow.

Usage:
  uv run python experiments/b29_mimic.py write
  uv run python experiments/b29_mimic.py attribution
  uv run python experiments/b29_mimic.py record Y_e1234abcd=Human ...
"""

import json
import statistics
import sys

from humanizer import ROOT
from humanizer.checks.copying import copied_share
from humanizer.data.essays import OUT as ESSAYS, _rank
from humanizer.llm import claude_many

sys.path.insert(0, str(ROOT / "experiments"))
from b25_blog import DRAFT, _bench, plain, voice  # noqa: E402

TEXTS = ROOT / "data" / "b29_texts.jsonl"
OUT = ROOT / "results" / "b29_mimic.json"
MIMIC = "Here are three posts I wrote.\n\n{examples}\n\n" + DRAFT.replace("First person,", "First person, in my voice,")


def examples(author: str, k: int = 3) -> list[dict]:
    rows = [r for r in map(json.loads, ESSAYS.open()) if r["author"] == author and r["split"] == "train"
            and 400 <= r["words"] <= 1200]
    return sorted(rows, key=lambda r: _rank(r["url"]))[:k]


def write():
    notes = {r["source"]: r["notes"] for r in map(json.loads, (ROOT / "data" / "b27_texts.jsonl").open())}
    rows = _bench()
    ex = {r["id"]: examples(r["author"]) for r in rows}
    prompts = [MIMIC.format(examples="\n\n".join(f"<post>\n{e['text']}\n</post>" for e in ex[r["id"]]),
                            title=r["title"], words=int(round(r["words"], -1)),
                            notes="\n".join(f"- {x}" for x in notes[r["id"]])) for r in rows]
    posts = claude_many(prompts, model="sonnet")
    out, per = [], {}
    for r, p in zip(rows, posts):
        t = plain(p or "")
        out.append({"id": f"Y_{r['id']}", "source": r["id"], "author": r["author"], "text": t,
                    "examples": [e["id"] for e in ex[r["id"]]]})
        per[f"Y_{r['id']}"] = {"author": r["author"], "words": len(t.split()), "over_essay": len(t.split()) / r["words"],
                               "copied_from_essay": copied_share(t, r["text"]),
                               "copied_from_examples": copied_share(t, "\n".join(e["text"] for e in ex[r["id"]])),
                               "voice": voice(t), "essay_voice": voice(r["text"])}
    TEXTS.write_text("".join(json.dumps(x) + "\n" for x in out))
    keys = ("over_essay", "copied_from_essay", "copied_from_examples")
    OUT.write_text(json.dumps({"checks": {k: statistics.mean(v[k] for v in per.values()) for k in keys},
                               "per_text": per}, indent=1))
    for k, v in per.items():
        print(k, v["author"][:16], v["words"], f"copy essay {v['copied_from_essay']:.2f} examples {v['copied_from_examples']:.2f}")


def attribution():
    """Which of the 13 writers a classifier trained on the training essays assigns to each text."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    train = [r for r in map(json.loads, ESSAYS.open()) if r["split"] == "train"]
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True, max_features=200000)
    clf = LogisticRegression(max_iter=2000, C=10).fit(vec.fit_transform([r["text"] for r in train]), [r["author"] for r in train])
    bench = {r["id"]: r for r in _bench()}
    sets = {"H": {k: r["text"] for k, r in bench.items()},
            "D": {k: r["draft"] for k, r in bench.items()},
            "W": {r["source"]: r["text"] for r in map(json.loads, (ROOT / "data" / "b27_texts.jsonl").open())},
            "V": {r["source"]: r["text"] for r in map(json.loads, (ROOT / "results" / "b26_texts.jsonl").open())}}
    if TEXTS.exists():
        sets["Y"] = {r["source"]: r["text"] for r in map(json.loads, TEXTS.open())}
    classes = list(clf.classes_)
    out = {}
    for cell, texts in sets.items():
        keys = [k for k in texts if texts[k].strip()]
        prob = clf.predict_proba(vec.transform([texts[k] for k in keys]))
        right = [classes.index(bench[k]["author"]) for k in keys]
        out[cell] = {"texts": len(keys), "right_writer": sum(int(p.argmax() == j) for p, j in zip(prob, right)) / len(keys),
                     "p_right_writer": statistics.mean(float(p[j]) for p, j in zip(prob, right))}
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.write_text(json.dumps(prev | {"attribution": out}, indent=1))
    print(json.dumps(out, indent=1))


def record(pairs: list[str]):
    verdicts = dict(p.split("=") for p in pairs)
    ids = [json.loads(line)["id"] for line in TEXTS.open()]
    assert set(verdicts) == set(ids), "need a verdict for every text"
    summary = {v: sum(verdicts[i] == v for i in ids) for v in ("AI", "Mixed", "Human")}
    out = json.loads(OUT.read_text())
    OUT.write_text(json.dumps(out | {"pangram_summary": summary, "pangram": verdicts}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "record":
        record(sys.argv[2:])
    else:
        {"write": write, "attribution": attribution}[cmd]()
