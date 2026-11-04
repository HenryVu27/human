"""Merge the 13B generations from the Windows GPU run into the B2 texts as arms.

lora13, lora13s1: OLMo-2-13B base + LoRA (trained on the RTX 5080), seeds 0 and 1, no grounding guard.
base13: the same 13B base model on the same prompts without the adapter (control).
"""

import json
import sys
import zipfile

from humanizer import ROOT

TEXTS = ROOT / "results" / "b2_dev_texts.jsonl"


def main(path: str):
    """path: the results zip (Taildrop) or a folder already copied back (scp)."""
    out = ROOT / "results" / "gpu13b"
    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            z.extractall(out)
    else:
        out = ROOT / path
    found = {p.name: p for p in out.rglob("*.jsonl")}
    rows = {r["id"]: r for r in map(json.loads, TEXTS.open())}
    for arm, name, seed in [("lora13", "dev_generations.jsonl", 0), ("lora13s1", "dev_generations.jsonl", 1),
                            ("base13", "dev_generations_base.jsonl", 0)]:
        if name not in found:
            print("missing", name)
            continue
        for g in map(json.loads, found[name].open()):
            if g.get("seed", 0) == seed and g["id"] in rows:
                rows[g["id"]][arm] = g["text"]
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows.values()))
    print("imported into", TEXTS)


if __name__ == "__main__":
    main(sys.argv[1])
