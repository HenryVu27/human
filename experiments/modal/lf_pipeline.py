"""Long-form pipeline runner: an experiment is a JSON config of stages, each an ephemeral `modal run`.

Every stage states its estimated cost (experiments/modal/lf_cost.py) before it runs; the runner refuses to start
when the config's total estimate exceeds --budget, and checks `modal app list` afterwards so nothing stays idle.

  python experiments/modal/lf_pipeline.py experiments/configs/b33_calibration.json --dry-run
  python experiments/modal/lf_pipeline.py experiments/configs/b33_calibration.json --budget 2

Config shape:
  {"experiment": "B33", "stages": [
     {"name": "score calib", "script": "experiments/modal/lf_detect.py::score",
      "args": {"inp": "results/b33_calib_inputs.jsonl", "out": "results/b33_scores_calib.jsonl"},
      "estimate": {"gpu": "L40S", "hours": 0.15, "cores": 4, "gib": 32}}]}

Stages and their status (phase 1, 2026-11-06):
- corpus   lf_corpus.py   working (B32 pilot)
- detect   lf_detect.py   working (B33 calibration)
- drafts   notes, rewording and AI posts with open instruct models on vLLM       phase 2
- train    LoRA or QLoRA on the chosen long-context base                         phase 2
- generate vLLM with the per-request Guard logits processor, check and resample phase 2
- checks   claim check (open judge on dev, Sonnet on test), copying, length      phase 2
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lf_cost import cost  # noqa: E402

MODAL = str(pathlib.Path.home() / ".local" / "bin" / "modal")
ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--budget", type=float, default=5.0, help="refuse if the estimate exceeds this many dollars")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cfg = json.loads(pathlib.Path(a.config).read_text())
    total = 0.0
    for st in cfg["stages"]:
        e = st["estimate"]
        st["_usd"] = cost(e["gpu"], e["hours"], e.get("cores", 4), e.get("gib", 32), e.get("containers", 1))
        total += st["_usd"]
        print(f"{cfg['experiment']} | {st['name']}: estimate ${st['_usd']:.2f}")
    print(f"{cfg['experiment']} total estimate ${total:.2f} (budget ${a.budget:.2f})")
    if total > a.budget:
        sys.exit("over budget: stop and ask Henry (through the main session) before running")
    if a.dry_run:
        return
    for st in cfg["stages"]:
        cmd = [MODAL, "run", st["script"]] + [x for k, v in st.get("args", {}).items()
                                              for x in (f"--{k.replace('_', '-')}", str(v))]
        print("+", " ".join(cmd), flush=True)
        r = subprocess.run(cmd, cwd=ROOT)
        if r.returncode:
            sys.exit(f"stage {st['name']} failed ({r.returncode})")
    apps = subprocess.run([MODAL, "app", "list"], capture_output=True, text=True).stdout
    live = [ln for ln in apps.splitlines() if "ephemera" in ln or "deployed" in ln]
    print("apps still listed as live:" if live else "no live apps", *live, sep="\n")


if __name__ == "__main__":
    main()
