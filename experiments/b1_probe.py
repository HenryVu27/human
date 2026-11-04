"""B1: do base-model continuations of human openings look human?

generate: 30 dev human texts, first 120 words as the opening, continued to about
450 words by the 9B base and 9B instruct models (4-bit MLX).
score:    local detector on the continuations only (opening removed), plus the
          human remainders as a reference. Also writes the 20-item batch for the
          $5 Pangram probe (10 base, 5 instruct, 5 human); it is NOT sent.
"""

import argparse
import json
import statistics

from humanizer import ROOT
from humanizer.llm import local_generate

BASES = {"qwen": str(ROOT / "models" / "qwen3.5-9b-base-4bit"), "olmo": str(ROOT / "models" / "olmo2-13b-base-4bit")}
INSTRUCT = "mlx-community/Qwen3.5-9B-MLX-4bit"
OUT = ROOT / "results" / "b1_generations.jsonl"
OPEN_WORDS = 120


def docs():
    rows = [json.loads(line) for line in (ROOT / "data" / "human.jsonl").open()]
    return rows[600:630]  # dev split


def generate(base: str):
    existing = [json.loads(line) for line in OUT.open()] if OUT.exists() else []
    rows = [r for r in existing if r["model"] != base]
    plan = [(BASES[base], False, base)] + ([] if any(r["model"] == "instruct" for r in rows) else [(INSTRUCT, True, "instruct")])
    for model, chat, name in plan:
        for d in docs():
            opening = " ".join(d["text"].split()[:OPEN_WORDS])
            prompt = (f"Continue the following text. Output only the continuation.\n\n{opening}" if chat else opening)
            cont = local_generate(model, prompt, max_tokens=650, temp=0.8, chat=chat)
            rows.append({"source_id": d["id"], "model": name,
                         "opening": opening, "continuation": cont.strip()})
            print(rows[-1]["model"], d["id"], len(cont.split()), flush=True)
    OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))


def score(detector_path):
    from humanizer.detect.score import Detector

    det = Detector.load(detector_path)
    rows = [json.loads(line) for line in OUT.open()]
    res = {}
    for kind in sorted({r["model"] for r in rows}):
        s = [det.score(r["continuation"]) for r in rows if r["model"] == kind and len(r["continuation"].split()) > 50]
        res[kind] = {"n": len(s), "mean_p_ai": statistics.mean(s), "share_above_0.5": sum(x > 0.5 for x in s) / len(s)}
    human = [" ".join(d["text"].split()[OPEN_WORDS:OPEN_WORDS + 450]) for d in docs()]
    hs = [det.score(t) for t in human]
    res["human_remainder"] = {"n": len(hs), "mean_p_ai": statistics.mean(hs),
                              "share_above_0.5": sum(x > 0.5 for x in hs) / len(hs)}
    (ROOT / "results" / "b1_local.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))

    base = [r for r in rows if r["model"] == "olmo"][:10]
    inst = [r for r in rows if r["model"] == "instruct"][:5]
    batch = ([{"id": f"base-{r['source_id']}", "text": r["continuation"]} for r in base]
             + [{"id": f"instruct-{r['source_id']}", "text": r["continuation"]} for r in inst]
             + [{"id": f"human-{d['id']}", "text": t} for d, t in list(zip(docs(), human))[:5]])
    (ROOT / "results" / "b1_pangram_batch.jsonl").write_text("".join(json.dumps(b) + "\n" for b in batch))
    print("pangram batch words:", sum(len(b["text"].split()) for b in batch))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["generate", "score"])
    ap.add_argument("--base", default="olmo", choices=list(BASES))
    ap.add_argument("--detector", default=str(ROOT / "models" / "detector-v1"))
    a = ap.parse_args()
    generate(a.base) if a.step == "generate" else score(a.detector)
