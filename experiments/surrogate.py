"""Can a local detector stand in for Pangram? Calibration on every text Pangram has judged.

Collects the Pangram-labelled texts from B3 onward into results/pangram_labels.jsonl (text, verdict,
experiment, cell) and scores them with the local detectors. AUROC is against "not Human"
(AI or Mixed). The spec allows Pangram labels here: detector calibration (section 8). No local
detector is used to pick a writer until it tracks Pangram on texts it was not tuned on.

Usage: uv run python experiments/surrogate.py [--cpu]
"""

import argparse
import json

from humanizer import ROOT
from humanizer.detect.train import auroc

R = ROOT / "results"
LABELS = R / "pangram_labels.jsonl"


def collect() -> list[dict]:
    rows = []
    b3 = {(r["group"], r["id"]): r for r in map(json.loads, (R / "b3_notes_leak_texts.jsonl").open())}
    for r in json.loads((R / "b3_notes_leak.json").read_text())["rows"]:
        v = r["pangram"]
        rows.append({"exp": "B3", "cell": r["group"], "id": r["id"], "text": b3[(r["group"], r["id"])]["text"], "verdict": v})
    b4 = {(r["group"], r["id"]): r["text"] for r in map(json.loads, (R / "b4_texts.jsonl").open())}
    for r in json.loads((R / "b4_facts.json").read_text())["pangram_rows"]:
        rows.append({"exp": "B4", "cell": r["group"], "id": r["id"], "text": b4[(r["group"], r["id"])], "verdict": r["pangram"]})
    for exp, gens, res in (("B5", "b5_generations.jsonl", "b5_matched.json"), ("B6", "b6_generations.jsonl", "b6_selection.json"),
                           ("B7", "b7_generations.jsonl", "b7_pool.json")):
        if not (R / res).exists() or "pangram" not in json.loads((R / res).read_text()):
            continue
        v = json.loads((R / res).read_text())["pangram"]
        for g in map(json.loads, (R / gens).open()):
            rows.append({"exp": exp, "cell": g["id"][0], "id": g["id"], "text": g["text"], "verdict": v[g["id"]]})
    LABELS.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpu", action="store_true", help="keep off the GPU while an MLX job runs")
    a = ap.parse_args()
    rows = collect()
    y = [r["verdict"] != "Human" for r in rows]
    print(len(rows), "labelled texts;", sum(y), "AI or Mixed")
    from humanizer.detect.score import Detector

    out = {"n": len(rows), "positives": sum(y)}
    for name in ("detector-v1", "detector-v2"):
        det = Detector.load(ROOT / "models" / name)
        if a.cpu:
            det.model.to("cpu")
            det.device = "cpu"
        s = [det.score(r["text"]) for r in rows]
        out[name] = {"auroc": auroc(y, s), "by_exp": {e: auroc([yy for yy, r in zip(y, rows) if r["exp"] == e],
                                                               [ss for ss, r in zip(s, rows) if r["exp"] == e])
                                                     for e in sorted({r["exp"] for r in rows})
                                                     if len({yy for yy, r in zip(y, rows) if r["exp"] == e}) == 2}}
        for r, ss in zip(rows, s):
            r[name] = ss
        print(name, json.dumps(out[name]))
    (R / "surrogate.json").write_text(json.dumps(out | {"scores": [{k: v for k, v in r.items() if k != "text"} for r in rows]},
                                                indent=1))


if __name__ == "__main__":
    main()
