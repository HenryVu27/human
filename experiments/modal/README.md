# Modal pipeline for the long-form program (B32 to B39)

Design and budget: `docs/specs/2026-11-06-longform-program.md`. Claims ledger: `results/research/longform-claims.md`.
Older one-off Modal scripts in this folder (`b30_gen.py`, `b31_modal.py`, `b31_gated.py`) belong to B30 and B31 and
are not part of this pipeline.

## Stages

| Stage | Script | Status | What it does |
|---|---|---|---|
| corpus | `lf_corpus.py` | working (B32 pilot) | Streams FineWeb shards (2019 to 2022 dumps) in CPU containers, filters long personal and technical blog posts captured before 2022-11-30, deduplicates, caps per site, splits by site; full texts go to the Volume `longform` |
| detect | `lf_detect.py` | working (B33) | Open-detector panel on an L40S: Binoculars, Fast-DetectGPT (Falcon pair and Llama 3.1 8B), MELD, desklib, with window rules for long texts |
| drafts | not yet written | phase 2 | Notes, reworded notes and AI posts from open instruct models on vLLM (training split); Sonnet drafts for dev and test go through `humanizer.llm` on the Mac |
| train | not yet written | phase 2 | LoRA or QLoRA on the chosen long-context base (B36 rule) |
| generate | not yet written | phase 2 | vLLM with a per-request Guard logits processor (design doc section 6), check and resample |
| checks | not yet written | phase 2 | Claim check (open judge on dev; Sonnet through `humanizer.llm` on test), copying against the human original, length |

`lf_cost.py` prices a job before it runs. `lf_pipeline.py` runs an experiment config (`experiments/configs/*.json`):
it prints each stage's estimate, refuses to start above `--budget`, runs each stage as an ephemeral `modal run`, and
lists any app still live at the end.

## How to run a new experiment

1. Write the rules (selection, exclusion, decision) into the experiment script's docstring with a time read from
   `date`, and commit them with a pathspec before anything is scanned by Pangram.
2. Write a config in `experiments/configs/` with an estimate per stage, then
   `python experiments/modal/lf_pipeline.py <config> --dry-run`.
3. Run it with `--budget` set to what is left of the approved Modal budget. Check `~/.local/bin/modal app list`
   afterwards (the runner prints anything still live).
4. Texts stay local (`results/b3[2-9]_*.jsonl` is gitignored) or on the Volume `longform`. Commit only code, configs
   and numeric summaries.

Examples:

    modal run experiments/modal/lf_corpus.py --dumps CC-MAIN-2019-35,CC-MAIN-2020-40,CC-MAIN-2021-31,CC-MAIN-2022-33 --tag pilot
    modal run experiments/modal/lf_detect.py::fetch
    uv run python experiments/b33_calibrate.py prep
    python experiments/modal/lf_pipeline.py experiments/configs/b33_calibration.json --budget 2
    uv run python experiments/b33_calibrate.py analyze
    uv run python experiments/b32_datecheck.py --tag pilot --n 30

## Storage

- Volume `b31-weights`: base and detector weights under `models/<repo>/<revision>` (B31's, reused; detector weights
  added 2026-11-06: Falcon 7B and 7B Instruct, MELD, desklib).
- Volume `longform`: `b32/<tag>/shards/*.jsonl` (filtered rows per FineWeb shard) and `b32/<tag>/corpus.jsonl`.

## Known limits (phase 1)

- The near-duplicate MinHash in `lf_corpus.select` is pure Python (about 50 ms per document); vectorize it with
  numpy before the full build (tens of thousands of documents), and re-run the pilot's dedup with it for parity.
- The `tech` genre tag is a keyword rate and needs an LLM labeller and a precision check before it defines Henry's
  genre in the test set.
- `lf_detect.py` pools per-token statistics row by row in Python (about 2,500 tokens a second for the Falcon pair on
  an L40S); a vectorized version would roughly double throughput.
