# Humanizer Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build every free piece of the humanizer: the corpus, the synthetic mirrors, the local detector, the checks, the editor, the base-model writer, the Pangram client and the CLI. Then run the free experiments (B1 on the local detector, B2, B0 baseline).

**Architecture:** A Python package `humanizer` with three layers.
- `llm` wraps every model call: headless Claude Code and local MLX models, both cached on disk.
- `data`, `detect` and `checks` produce and measure text.
- `pipeline` chains the editor, writer and checks behind a `humanize` CLI.

Experiments are scripts in `experiments/` that write JSON results to `results/`.

**Tech Stack:** Python 3.13 managed by uv, mlx-lm 0.32+, PyTorch (MPS) with Hugging Face transformers for the detector, datasets (streaming), httpx, pytest.

**Spec:** `docs/specs/2026-11-04-humanizer-design.md`

## Global Constraints

- No spending. No account creation. No API keys typed or copied by Claude. Pangram calls are code paths only until Henry supplies `PANGRAM_API_KEY`.
- Pangram scores never select a prompt, weight or writer. Only the B1 gate and calibration may use them.
- Output must not contain numbers, dates, proper nouns or quotations absent from the input draft.
- Must run on an M2 Pro with 16 GB: at most one model of about 9 GB or more in memory at a time.
- Bulk Claude calls stay moderate (shared account): at most 4 concurrent `claude -p` calls, and every call is cached so nothing is paid twice.
- Writing style for docs and reports: no em dashes, no emojis, acronyms spelled out on first use.

## Review Focus

1. **Empty or very short drafts (under 50 words).** The CLI should refuse with a clear message, not crash or emit garbage. Test: `test_cli_rejects_short_input`.
2. **A `claude -p` failure or rate limit mid-batch.** The batch should resume from cache on re-run without redoing finished calls. Test: `test_claude_cache_hit_skips_subprocess`.
3. **Drafts that contain markdown (headers, lists, code blocks).** The claim check must not count code identifiers as invented proper nouns. Test: `test_specifics_ignores_code_blocks`.
4. **Base model rambles past the planned section or starts a new document.** The writer must stop at section boundaries. Test: `test_truncate_at_document_break`.
5. **Detector scoring of texts longer than its context.** Score by averaging windows, never by silent truncation. Test: `test_score_long_text_uses_windows`.

---

### Task 1: Scaffold and LLM layer

**Files:**
- Create: `pyproject.toml`, `CLAUDE.md`, `.gitignore`, `.env.example`
- Create: `src/humanizer/llm.py`
- Test: `tests/test_llm.py`

**Interfaces:**
- Produces:
  - `claude(prompt: str, *, model: str = "haiku", system: str | None = None) -> str`. Runs `claude -p --model {model} --output-format json`, parses `.result`, and caches by the SHA-256 of `(model, system, prompt)` under `.cache/claude/`.
  - `claude_many(prompts: list[str], *, model: str, system: str | None = None, workers: int = 4) -> list[str]`
  - `local_generate(model_id: str, prompt: str, *, max_tokens: int, temp: float = 0.8, top_p: float = 0.95) -> str`. Uses mlx-lm, keeps one model loaded at a time, and caches like `claude`.

- [ ] Write the tests:
  - `test_claude_cache_hit_skips_subprocess`: pre-seed the cache, monkeypatch `subprocess.run` to raise, and assert the cached value comes back.
  - `test_claude_parses_result_field`: fake stdout `{"result":"hi"}` returns `"hi"`.
- [ ] Run `uv run pytest tests/test_llm.py -v`. Expected: FAIL (module missing).
- [ ] Implement `llm.py`.
- [ ] Run the tests. Expected: PASS. Run a live smoke test: `claude("Say OK", model="haiku")` returns text containing "OK".
- [ ] Commit `feat: llm layer with cached claude and mlx calls`.

### Task 2: Human corpus

**Files:**
- Create: `src/humanizer/data/corpus.py`
- Test: `tests/test_corpus.py`

**Interfaces:**
- Produces:
  - `keep_doc(row: dict) -> bool`
  - `build_corpus(n: int, out: Path) -> int`
  - Output file `data/human.jsonl` with rows `{id, text, url, dump, words}`.

Filters:
- Source: FineWeb-Edu (`HuggingFaceFW/fineweb-edu`, streaming).
- Crawl dump: `dump` year before 2022.
- Length: 350 to 1,500 words.
- Educational score: `int_score >= 3`.
- Boilerplate: drop documents containing "cookie" or "subscribe" in their first 200 characters.

- [ ] Write the tests:
  - `test_keep_doc_rejects_2023_dump`
  - `test_keep_doc_rejects_short`
  - `test_keep_doc_accepts_2019_long_edu`
- [ ] Implement it. Then run `uv run python -m humanizer.data.corpus --n 900`. Expected: `data/human.jsonl` with 900 rows.
- [ ] Commit `feat: pre-2022 human corpus from FineWeb-Edu`.

### Task 3: Synthetic mirrors and test drafts

**Files:**
- Create: `src/humanizer/data/mirror.py`
- Test: `tests/test_mirror.py`

**Interfaces:**
- Consumes: `claude_many` and `local_generate`.
- Produces:
  - `topic_prompt(doc: dict) -> str`
  - `mirror_prompt(topic: str, words: int) -> str`
  - `build_mirrors(human: Path, out: Path, generators: list[str]) -> int`
  - Output files:
    - `data/ai.jsonl` with rows `{id, source_id, generator, text}`
    - `data/drafts/{dev,h1,h2}.jsonl` with rows `{id, source_id, generator, text}`

Generators:
- Mirrors: `claude:haiku`, `claude:sonnet` and `mlx:mlx-community/Qwen3.5-4B-MLX-4bit`, round-robin.
- Drafts: `claude:sonnet` and `claude:opus`, using a "write a blog post about X" prompt of 600 to 1,000 words.

Splits:
- Human documents 0 to 599 are detector pairs.
- 600 to 699 are dev drafts.
- 700 to 799 are H1.
- 800 to 849 are H2.

- [ ] Write the test `test_mirror_prompt_requests_length_and_topic_only` (the prompt contains the topic and the word count, and does not contain any of the source text).
- [ ] Implement it, run it, and check row counts and that no AI text repeats a 12-word span of its source.
- [ ] Commit `feat: synthetic mirrors and frozen draft splits`.

### Task 4: Local detector

**Files:**
- Create: `src/humanizer/detect/train.py`, `src/humanizer/detect/score.py`
- Test: `tests/test_detect.py`

**Interfaces:**
- Produces:
  - `Detector.load(path: Path) -> Detector`
  - `Detector.score(text: str) -> float`, the probability of AI, averaged over windows of 512 tokens with stride 256.
  - Saved checkpoint `models/detector-v1/` (frozen once calibrated).

Training:
- Encoder: `answerdotai/ModernBERT-base`, fine-tuned for binary classification on the Mac's GPU (MPS).
- Splits: by `source_id`, 80/10/10, so a topic never appears in two splits.
- Report: AUROC overall and cross-generator (train without Qwen, test on Qwen) in `results/detector_v1.json`.

- [ ] Write the test `test_score_long_text_uses_windows`: with a stub model that returns a constant per window, a 2,000-token text calls the model at least 7 times.
- [ ] Implement and train it. Expected: AUROC at least 0.95 on the test split. Report the cross-generator AUROC whatever it is.
- [ ] Commit `feat: local detector v1`.

### Task 5: Claim check and quality judge

**Files:**
- Create: `src/humanizer/checks/claims.py`, `src/humanizer/checks/quality.py`
- Test: `tests/test_checks.py`

**Interfaces:**
- Produces:
  - `specifics(text: str) -> set[str]`: numbers, years, quoted strings and capitalized multi-word names, ignoring fenced and inline code.
  - `unsupported_specifics(draft: str, output: str) -> set[str]`
  - `claim_check(draft: str, output: str) -> dict` returning `{unsupported_specifics, claims_total, claims_entailed, pass}`, where `pass` means there are no unsupported specifics and the entailed share is at least 0.95.
  - `quality_pair(draft: str, output: str) -> float`: 1.0 if the output wins both position orders, 0.5 for a split, 0.0 for a loss.

- [ ] Write the tests:
  - `test_unsupported_specifics_flags_new_number`
  - `test_specifics_ignores_code_blocks`
  - `test_same_text_has_no_unsupported`
- [ ] Implement it. The entailment and judge prompts use `claude(model="sonnet")`.
- [ ] Commit `feat: claim check and pairwise quality judge`.

### Task 6: Editor, base writer, pipeline and CLI

**Files:**
- Create: `src/humanizer/pipeline/editor.py`, `src/humanizer/pipeline/writer.py`, `src/humanizer/pipeline/run.py`, `src/humanizer/cli.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Produces:
  - `edit_plan(draft: str) -> Plan`. `Plan` holds `title` and `sections: list[Section]`. A `Section` holds `heading: str | None`, `points: list[str]` (each tied to a draft quote), `target_words: int` and `cut: list[str]`.
  - `write_section(plan: Plan, i: int, prior: str, *, model_id: str) -> str`
  - `truncate_at_document_break(text: str) -> str`
  - `humanize(draft: str, *, writer: str) -> Result`, where `Result` holds `text`, `plan`, `checks`, `detector` and `retries`.
  - CLI: `humanize INPUT -o OUT [--writer mlx:<id>|claude:<model>]`, which writes `OUT` and `OUT.report.json`.

Writer prompt layout:
- A document prefix made of two pre-2022 human texts from the corpus (dev split only).
- Then the plan rendered as "Notes for the next post".
- Then the title and section heading.
- The base model continues.

Retries: at most 2 per failed check.

- [ ] Write the tests:
  - `test_truncate_at_document_break` (cuts at a new `# ` title or at the end-of-text token).
  - `test_cli_rejects_short_input` (under 50 words exits with code 2 and a message).
- [ ] Implement it. Run the CLI on one dev draft with `--writer mlx:<Qwen3.5-9B-Base 4-bit>` and check the report.
- [ ] Commit `feat: editor, base writer, humanize CLI`.

### Task 7: Pangram client (offline-tested)

**Files:**
- Create: `src/humanizer/eval/pangram.py`
- Test: `tests/test_pangram.py`

**Interfaces:**
- Produces:
  - `Pangram(api_key: str | None = None)`, which reads `PANGRAM_API_KEY` by default.
  - `.models() -> list[str]`
  - `.score(text: str, model: str) -> dict`, which polls `/task/{id}`.
  - `.bulk(texts: list[str], model: str) -> list[dict]`
  - `is_human(result: dict) -> bool`, true only when `prediction_short == "Human"`.

Every result is appended to `results/pangram_log.jsonl` with its `version`.

- [ ] Write the tests:
  - `test_is_human_mixed_is_false`
  - `test_score_polls_until_success` (use an httpx mock transport).
- [ ] Implement it and commit `feat: pangram client`.

### Task 8: Free experiments

**Files:**
- Create: `experiments/b1_probe.py`, `experiments/b2_dev.py`, `experiments/b0_ablate.py`
- Output: `results/b1_local.json`, `results/b2_dev.json`, `results/b0_baseline.json`

**B1:** Take the first 120 words of 30 dev human texts. Continue each with the 9B base model (4-bit) and the 9B instruct model (4-bit) to about 450 words. Score only the continuations with the local detector, and record the mean and distribution per model. Prepare `results/b1_pangram_batch.jsonl` (10 base, 5 instruct, 5 human) for the $5 Pangram probe, but do not send it.

**B2:** Run `humanize` on 20 dev drafts. Record:
- local detector: before and after
- claim check pass rate
- quality win rate

**B0, scripted arm:** Load the Qwen3.5-4B base and instruct models one at a time.
- Collect mean residual activations per layer on 200 human texts and 200 mirrors.
- The direction is the mean AI activation minus the mean human activation.
- Project it out of each layer's MLP down-projection and attention output weights for layers chosen by separation strength.
- Generate 20 mirror-prompt outputs before and after, and score them with the local detector plus a format/instruction check.
- Save the edited weights only if the score improves.

- [ ] Run each experiment, write its JSON, and commit `exp: phase 1 free experiments`.

### Task 9: Morning report

**Files:**
- Create: `results/REPORT-2026-11-05.md`

Contents: what was built, numbers from every `results/*.json` file, what failed, and what needs Henry (a Pangram key, $5 credits, panel readers, and the open questions in spec section 8).
