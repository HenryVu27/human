"""Merge the 13B generations from the Windows GPU run into the B2 texts as arms.

lora13: OLMo-2-13B base + LoRA (trained on the RTX 5080), seed 0, no grounding guard.
base13: the same 13B base model on the same prompts without the adapter (control).
"""

import json
import sys
import zipfile

from humanizer import ROOT

TEXTS = ROOT / "results" / "b2_dev_texts.jsonl"


def main(zip_path: str):
    out = ROOT / "results" / "gpu13b"
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(out)
    found = {p.name: p for p in out.rglob("*.jsonl")}
    rows = {r["id"]: r for r in map(json.loads, TEXTS.open())}
    for arm, name in [("lora13", "dev_generations.jsonl"), ("base13", "dev_generations_base.jsonl")]:
        if name not in found:
            print("missing", name)
            continue
        for g in map(json.loads, found[name].open()):
            if g.get("seed", 0) == 0 and g["id"] in rows:
                rows[g["id"]][arm] = g["text"]
    TEXTS.write_text("".join(json.dumps(r) + "\n" for r in rows.values()))
    print("imported into", TEXTS)


if __name__ == "__main__":
    main(sys.argv[1])
