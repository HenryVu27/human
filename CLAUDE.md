# Humanizer

Research project: turn any AI draft into prose that Pangram 4.x and blind expert readers judge human-written, editing like a human editor and inventing nothing. Spec: `docs/specs/2026-11-04-humanizer-design.md`. Plan: `docs/plans/2026-11-04-humanizer-phase1.md`. Latest status: newest `results/REPORT-*.md`.

## Rules

- Total spend is capped at $100. Nothing that costs money, and no account or API key creation, without Henry's explicit yes.
- Pangram is a held-out judge. Its scores never select a prompt, weight or writer, except the B1 gate and detector calibration (spec section 8).
- Output must add no facts, numbers, names, dates or quotes. The claim check enforces this.
- 16 GB Mac: keep one large model in memory at a time (`humanizer.llm.load_mlx` does this within a process). Never run two GPU jobs (MLX or PyTorch MPS) in parallel processes; on 2026-11-04 that crashed both with a Metal out-of-memory error. Chain them in one background command.
- Bulk `claude -p` calls go through `humanizer.llm` (cached, lean flags, at most 4 workers). The Claude account is shared with Henry's work computer.
- Before using Claude in Chrome, confirm it is the Chrome on this Mac (serve a one-time token on 127.0.0.1 and load it).
- Docs and reports: no em dashes, no emojis, acronyms spelled out on first use.

## Commands

- `uv run pytest -q` runs the tests.
- `uv run python -m humanizer.data.corpus --n 900` builds `data/human.jsonl`.
- `uv run python -m humanizer.data.mirror [--only claude|mlx]` builds mirrors and draft splits.
- `uv run python -m humanizer.detect.train --name detector-v1` trains the local detector.
- `uv run humanize draft.md -o out.md [--writer mlx:<path>|claude:<model>]` runs the pipeline.
- `experiments/fetch_models.sh` downloads and converts the local models.
