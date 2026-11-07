# Humanizer

**Attempt 1 is closed (2026-11-06). Start from `docs/attempt-1-closeout.md`: findings, dead ends, open questions and how to set up the Mac, the PC, Modal and Pangram.**

**Attempt 2 design: `docs/specs/2026-11-06-attempt-2-design.md` (proposal, waiting for Henry's decisions in its section 13; nothing run).**

Research project: turn any AI draft into prose that Pangram 4.x and blind expert readers judge human-written, editing like a human editor and inventing nothing. Spec: `docs/specs/2026-11-04-humanizer-design.md`. Plan: `docs/plans/2026-11-04-humanizer-phase1.md`. Index of every experiment and search: `results/LABNOTEBOOK.md`. Latest status: `results/REPORT-2026-11-04-lora.md` (the overnight report `REPORT-2026-11-05.md` is misdated; it came first).

## Rules

- Total spend is capped at $100. Nothing that costs money, and no account or API key creation, without Henry's explicit yes.
- Pangram is a held-out judge. Its scores never select a prompt, weight or writer, except the B1 gate and detector calibration (spec section 8).
  - Exception (Henry, 2026-11-06 13:08): a local judge may be trained on the project's Pangram labels and used to pick and develop outputs. A final test set it never sees (not in training, calibration or any pick) stays reserved, and only Pangram scores that set. Stay inside the Modal free credit for this.
- Output must add no facts, numbers, names, dates or quotes. The claim check enforces this.
- No heavy jobs on the Mac (Henry, 2026-11-05: it makes the Mac unusable). Training and local-model generation run on the PC (`experiments/gpu/`, under the `C:\gpu-lock` folder lock via `gpu_job.cmd`, logged in `C:\gpu-schedule.txt`); the Mac only copies files, builds prompts and runs the Claude-based checks.
- 16 GB Mac: keep one large model in memory at a time (`humanizer.llm.load_mlx` does this within a process). Never run two GPU jobs (MLX or PyTorch MPS) in parallel processes; on 2026-11-04 that crashed both with a Metal out-of-memory error. Chain them in one background command.
- Bulk `claude -p` calls go through `humanizer.llm` (cached, lean flags, at most 4 workers). The Claude account is shared with Henry's work computer.
- Before using Claude in Chrome, confirm it is the Chrome on this Mac (serve a one-time token on 127.0.0.1 and load it).
- Every experiment gets a row in `results/LABNOTEBOOK.md` (question, design, result, files) and every literature search a row in its search log, with the agent's raw report saved under `results/research/`. Fix the selection rule in the script docstring and commit it before scanning.
- Docs and reports: no em dashes, no emojis, acronyms spelled out on first use.

## Commands

- `.venv/bin/python -m pytest -q` runs the tests (`uv run pytest` fails: the console script is missing from `.venv/bin`).
- `uv run python -m humanizer.data.corpus --n 900` builds `data/human.jsonl`.
- `uv run python -m humanizer.data.mirror [--only claude|mlx]` builds mirrors and draft splits.
- `uv run python -m humanizer.detect.train --name detector-v1` trains the local detector.
- `uv run humanize draft.md -o out.md [--writer mlx:<path>|claude:<model>]` runs the pipeline.
- `experiments/fetch_models.sh` downloads and converts the local models.
