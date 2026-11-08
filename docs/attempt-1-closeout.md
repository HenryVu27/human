# Humanizer, attempt 1: closeout

Written 2026-11-06, about 17:30 CST, by the main humanizer session, at Henry's request ("Close it out... Make sure
everything, exploration, setup, results are written"). It is the entry point for the session that plans attempt 2.
Every statement here points to its evidence. Henry's standing rule applies to all of it: treat each finding as a
claim to test, and be as ready to refute it as to confirm it.

**Reading order:**
1. This file.
2. `results/LABNOTEBOOK.md`: one row per experiment and per literature search, plus the Pangram credit ledger.
3. `results/REPORT-2026-11-04-lora.md`: full write-ups, sections 1 to 39, and the dated "Where this stands" sections
   (the last is 2026-11-06, about 16:50). `results/REPORT-2026-11-05.md` covers B0 to B2.
4. `docs/specs/2026-11-04-humanizer-design.md` (the original design) and `docs/specs/2026-11-06-longform-program.md`
   (the long-form program, with its dated amendments).
5. `results/RESEARCH-2026-11-04-prior-work.md` and `results/research/` (literature, claims ledgers, validator and
   red-team reports).
6. `docs/private/machines.md` (local only, gitignored): machine addresses and account names.

## 1. The goal, and how attempt 1 ended

**Goal (design spec, 2026-11-04).** A tool that takes any AI-written draft and returns a piece that careful human
readers and Pangram 4.x both judge to be human-written. The piece must be better writing than the input, and it must
add no facts, numbers, names, dates, quotes or anecdotes. Henry's real use is his own blog (henryvu.blog): technical
posts of 1,500 to 3,000 or more words, drafted with Claude, which keep reading as AI.

**Success criteria (spec section 6.4) and where attempt 1 left each one:**

| Criterion | Status at close |
|---|---|
| At least 50% of held-out outputs labelled Human by Pangram 4.x | Never tested on the spec's held-out set (`data/drafts/h2.jsonl`, 50 drafts, and `h1.jsonl`, 100, both untouched). On development sets it was met for outputs of about 100 to 1,100 words whose content is human-sourced (B26 11 of 13, B28 L 11 to 17 of 19, B30 T100 19 of 19), or is the draft's specific facts planned by the base model (B14 13 of 20). Not met at full length on writers the rewriter never saw: B36 1 of 32 |
| Claim check passes on every output | Not met. Average claim support runs 72 to 97% by cell, and the Sonnet claim check missed invented code, garbled French and invented framing (B36); form checks were added in B37 |
| Quality judge win rate against the input of at least 50% | Not met. The LLM judge prefers Sonnet's prose over human text 20 of 20 (judge check), so it cannot measure this; against same-topic human text, quality scored 0.20 to 0.575 |
| Reader-panel accuracy of no more than 60% | Not measured. A blind read was published (https://claude.ai/artifact/BYd8PmoSMAKfcLhs7qMpGP) and is still waiting for Henry |

**How it ended.** The long-form program (B32 to B39) was paused by Henry on 2026-11-06 at about 16:45, after B38.
Henry then closed attempt 1. Nothing is running, nothing is billed, and the B39 final-test reserve is untouched
(section 7).

## 2. Bottom line: what attempt 1 established

1. **Pangram 4 reads who chose the content, not only the wording.**
   - The same local writer on the same 10 topics reads Human 17 of 20 from human-sourced facts and 1 of 20 from
     AI-sourced facts. Rewording the facts changes nothing (B5, p = 4e-7).
   - Dose response: Human 0, 1, 7 and 10 of 10 at 0, a third, two thirds and all human-sourced facts (B9).
   - In B28, Sonnet's posts read more AI as Sonnet chooses more of the content: from 100%, 50% and 25% of a
     blogger's notes they read AI 0, 13 and 18 of 19.
   - The prior work found the same split (`results/RESEARCH-2026-11-04-prior-work.md`): every credible public pass of
     Pangram 4.x has human-chosen content or changed meaning.
2. **The prose carries signal too.**
   - Human content written up by Sonnet reads Mixed, not Human: B27 W 1 Human, 11 Mixed, 1 AI; B28 S100 1, 18, 0.
   - Earlier Human readings of Sonnet posts came from the essay's own wording leaking through the notes (B25 against
     B27).
   - An instruct-model writer is caught however much it compresses: B10 20 of 20 AI; Sonnet condensation in B12
     20 of 20 AI.
3. **A local base-model writer trained on human text, writing from human content, reads Human.**
   - OLMo-2-13B with QLoRA adapters (quantized low-rank adaptation) trained on notes-to-article pairs.
   - B26: the essayist-trained voice writer from a blogger's reworded notes, 11 of 13 Human.
   - B28 L, the same writer at three note doses, 11, 14 and 17 of 19. The rise goes with shorter outputs, and dose and
     length cannot be separated there.
4. **A learned rewriter (AI post to human post) works on short posts when the content is the author's, and does not
   transfer.**
   - B30 trained it on 630 pairs from 13 essayists. On held-out essays by those same writers: T100 19 of 19, T50 13 of
     19, T25 3 of 19 Human, against Sonnet's inputs at 1, 0 and 0.
   - On whole posts by writers it never saw: 1 of 32 Human, AI share 0.81 to 0.38 (B36). The input drafts there came
     from half of each author's notes.
   - The first 300 words of the same rewrites read Human 11 of 32, so how human each stretch reads is the
     bottleneck, and length multiplies it.
5. **Pangram's AI share is the share of words it flags, wherever they sit. A document reads Human when under about
   10% is flagged.**
   - B37 spliced Sonnet blocks into human posts: 6.8%, 9.5% and 17% of the words gave shares of 0.06 to 0.07, 0.08 to
     0.09 and 0.15 to 0.17, labelled Human, Human and Mixed, at any position.
   - Pangram's documentation says Human needs at least 90% of characters labelled human
     (`results/research/longform-pangram-length.md`).
   - Human posts read Human at full length, 10 of 10 (B34).
6. **Content kept and Human verdict trade off.**
   - Every route that reads Human keeps less of the input: condensing (B14) about 40% of the draft's length; the
     notes-first writer at full length 28%; the B38 judge's unconstrained picks about 60%.
   - B36's rewriter keeps 71% of the length with 96% of claims supported, and its whole posts read 0.38 flagged. Even
     the best of 4 tries per section, under the content rules, leaves sections at 0.21 (B38).
   - How much a text copies from the AI draft (8-word runs) is the best single predictor of Pangram's share:
     Spearman 0.70 across B38's tries.
7. **No local judge tracks Pangram within rewrites.**
   - The surrogate detector: AUROC (area under the receiver operating characteristic curve) 0.78 and 0.83 on 96
     Pangram-labelled texts (`results/surrogate.json`). By the notebook's account it was 0.54 to 0.67 among AI-sourced
     texts, too low to select with.
   - Open detectors: MELD 0.63 overall (B33).
   - MELD on rewrites: 0.55 on B36's short rewrites, 0.70 on all 561.
   - A judge trained on 1,534 Pangram labels reached 0.735 on rewrites, but that number mostly separates experiments,
     and within the tries of one section it picks no better than "copies least from the draft" (B38).
8. **B31 found no clear effect of a base model's crawl date or of synthetic mid-training.**
   - Crawl date moved the AI share +0.12 (interval -0.08 to +0.31, Holm p 0.50), so small effects are not excluded.
   - Every base model, Pythia (2020 data) included, reads not Human 12 to 43% of the time.
   - Post-training is the large effect (+0.64 to +0.76 AI share).
   - The opening being continued matters more than the model (`results/B31-SUMMARY.md`).
9. **Henry's own posts.**
   - The context-engineering post's sections read 0 Human, 3 Mixed and 4 AI (B15).
   - Rewritten section by section, with the math stripped, the bandits post reads Human at 0.08 (original 0.24) and
     the context-engineering post Mixed at 0.24 (original 0.53); sections 6 of 12 Human against 1 of 12 (B37).
   - The Human-reading bandits rewrite is not publishable: broken sentences, a garbled proof.
   - Math as LaTeX raises the share: the bandits original reads 0.41 with it and 0.24 without, in one batch (B38).

## 3. What works, and under which conditions

| Route | Input | Pangram result | Length kept | Claims supported | Main caveat | Where |
|---|---|---|---|---|---|---|
| B14 pipeline (specific facts, pool writer, prune, best of 4 by claim check) | AI draft of a web explainer | 13 Human, 7 Mixed, 0 AI of 20 | about 40% of the draft | 86% | A condensation, not a full post; FineWeb explainers, not blogs; quality judged poor on technical prose (B15) | b14_bestof.py |
| B24 cited human sources | AI draft plus 3 pre-2022 Wikipedia revisions | 10 of 10 Human | 66% of target | 92% | Becomes a Wikipedia-backed article; 21% of words copied verbatim from Wikipedia through the facts | b24_cited.py |
| B26 voice writer | Blogger's own notes, reworded | 11 of 13 Human | 82% of the essay | 92% | Needs the author's notes; seen writers' genre | b26_voice.py |
| B28 L voice writer | Blogger's notes at 100, 50 and 25% | 11, 14 and 17 of 19 Human (L25 15 under the 150-word rule) | 67%, 45%, 35% of the essay | 90%, 85%, 72% | Human rises as length falls; dose and length cannot be separated | b28_dose.py |
| B30 rewriter | Sonnet's post from the blogger's notes at 100, 50 and 25% | T100 19, T50 13, T25 3 of 19 Human (T25 2 under the rule) | 82%, 78%, 77% of the essay | 94%, 97%, 96% | Seen writers, about 640 words; fails on unseen writers at length (B36) | b30_rewriter.py |

The 150-word rule: a text under 150 words counts as not Human (B25; applied to B28 by the amendment of 04:07 in
`experiments/b28_dose.py`).

## 4. Dead ends and negative results

| ID | What was tried | What happened | Where |
|---|---|---|---|
| B0 | Remove the assistant-register direction from Qwen3.5-4B's weights | No effect on the local detector | REPORT-2026-11-05 section 2 |
| B2 | Prompted base model writing from notes | Judge preferred the draft 20 of 20; 46% of claims supported | b2_dev.py |
| B3, B4 | Notes or fact lists from AI drafts | The AI signal travels through notes (10 of 10 AI) and through fact lists (9 AI, 1 Mixed) | b3_notes_leak.py, b4_facts.py |
| B6 | Cut generic facts, keep specific ones | No better than a random cut of the same size | b6_selection.py |
| B10 | Sonnet compresses the draft to 25% or 50% | 20 of 20 AI | b10_compress.py |
| Surrogate | Local detector as a stand-in for Pangram | Not usable among AI-sourced texts (AUROC 0.54 to 0.67) | surrogate.py |
| B8 | Writer trained to drop AI-typical facts | 5 Human, 10 Mixed, 5 AI; a quality trade-off | b8_mixpool.py |
| B17 | Writer trained on first-person technical blogs, on Henry's post | Fixes voice, not verdicts (3 Human of 7 against B15's 4) | b17_techwriter.py |
| B18 | Write, check and resample one paragraph at a time | Does not add length (31% of the draft) | b18_resample.py |
| B19 | Simulated author interview | Simulated authors could not answer first-hand questions | b19_interview.py |
| B20 | Full length written section by section from the draft's facts in order | Never reached full length (23 to 36%); walking the draft's facts brings back its outline (0 of 3 Human) | b20_sectional.py |
| B21 | Henry answers editor questions about his post | Not run: he could not recall specifics months later. The interview route needs the author at drafting time | b21_author.py |
| B22 | The project's design docs as human content | Not run: Henry keeps that project's records out of third-party tools | none |
| B23 | Narrower prune to keep length | Prediction failed: the writer fills length with new facts, not elaboration | b23_prune_tiers.py |
| B29 | Sonnet imitating one writer from three of their posts | 3 Human, 8 Mixed, 1 AI of 12 | b29_mimic.py |
| B34 B arm | Raw OLMo-2-13B continuations to 2,000 words | Every continuation looped or stopped short; arm excluded | b34_length.py |
| B36 | B30's rewriter on whole posts by unseen writers | 1 of 32 Human | b36_transfer.py |
| B37 | Least-copying pick over 4 seeds; notes-first writer at full length | No movement on the development measure; the notes-first writer kept 28% of the length | b37_gate2a.py |
| B38 | Judge trained on Pangram labels, best of 4 | No better than the free least-copying rule under the content rules; even the best possible pick of 4 leaves sections at 0.213 | b38_judge.py |

## 5. Open questions and untested cells

These are inputs for attempt 2's planning, not a plan.

- **The all-notes condition at full length.** B36 gave Sonnet half of each author's notes (B30's 13-of-19 condition).
  All the notes (B30's 19-of-19 condition) was never tested at full length or on unseen writers. It is the case that
  matches a workflow where Henry writes his own notes per section before Sonnet drafts.
- **The notes-first writer, section by section.** At full length in one pass it wrote 28% of the length (B37). Per
  section generation may fix that; untested.
- **Gate 2b.** A long-context rewriter trained on many writers with a copying penalty, estimated at $40 to $55 of
  paid Modal. The B37 red team estimated long context alone closes about 0.09 of a 0.28 gap; the case for it is the
  unseen-writer gap, not length.
- **A judge that ranks tries within a section.** B38's lesson: the training data must contain several tries of the
  same section with Pangram labels, copied share should be a feature, and the bar should be pair accuracy within
  sections under the content rules, against the least-copying rule, not pooled AUROC.
- **Pangram's window size and per-window behaviour.** The word-share rule is measured; the window size and how
  boundaries are drawn are not.
- **Henry's genre.** Math as LaTeX raises the share (B38); code blocks and tables are untested. How a detector would
  see his published pages (rendered math or LaTeX source) is unknown.
- **Quality.** No validated quality measure: the LLM judge is biased toward Sonnet, and the blind read is waiting.
  The anti-goal "worse than the input" has never been measured by a human.
- **The author at drafting time.** B21 found that an interview after the fact fails on memory. Capturing Henry's own
  points while he drafts is untested.
- **Generators.** Every AI draft came from Claude. The FineWeb dev drafts are half Sonnet and half Opus
  (`data/drafts/dev.jsonl`); the blog-track and long-form drafts are Sonnet. Other model families are untested.
- **The spec's held-out drafts.** `data/drafts/h1.jsonl` (100) and `h2.jsonl` (50, the spec's final set) were never
  used.
- **The Pangram API.** The key returned HTTP 402 on 2026-11-04, on the Individual trial. The Professional plan
  advertises monthly API credits, and nobody has retried. One retry, with Henry's yes, could replace the dashboard
  procedure.
- **Pangram drift.** Pangram 4.1 shipped 2026-10-19. Day-to-day drift was never measured; attempt 1 relied on
  same-day paired scans for key comparisons.

## 6. Setup: how to run everything

### 6.1 Repository and environment

- Repo: `~/personal/human` on Henry's Mac (Apple M2 Pro, 16 GB). Public GitHub repo `HenryVu27/human`, branch
  `master`; 46 or more local commits are not pushed (push only when Henry asks).
- Python environment: `uv` with `.venv` (Python 3.13). `uv sync` installs it.
- Tests: `.venv/bin/python -m pytest -q` (67 pass on 2026-11-06). `uv run pytest` fails because the `pytest`
  console script is missing from `.venv/bin`.
- Git: a fresh clone lacks `data/`, `models/`, the adapters and `docs/private/` (all gitignored or local), so work
  from this Mac's checkout. A leftover branch `b31-basedate` exists; B31's results are on `master`. There are no
  other worktrees.
- Commands (also in `CLAUDE.md`):
  - `uv run python -m humanizer.data.corpus --n 900` builds `data/human.jsonl`;
  - `uv run python -m humanizer.data.mirror [--only claude|mlx]` builds mirrors and draft splits;
  - `uv run humanize draft.md -o out.md [--writer mlx:<path>|claude:<model>]` runs the pipeline;
  - `experiments/fetch_models.sh` downloads and converts the local models.
- Code map (`src/humanizer/`):
  - `checks/`: claim check (`claims.py`), 8-word copying (`copying.py`), form checks (`form.py`: language, new code,
    framing, headers, restarts), template repeats (`repeats.py`), quality (`quality.py`).
  - `pipeline/`: the Guard (`guard.py`, a logits processor that blocks tokens for numbers, names and dates not in the
    allowed text), prune, editor, writers, sectional writing.
  - `data/`: corpus builders (FineWeb explainers, essays, technical blogs, pools for each writer).
  - `detect/`: the local detector. `eval/pangram.py`: Pangram API client. Its key returned HTTP 402 on 2026-11-04 on
    the Individual trial and was not retried on Professional, so attempt 1 used the dashboard.
  - `llm.py`: Claude CLI wrapper with a cache in `.cache/llm` and at most 4 workers. `claude()` defaults to Haiku;
    the claim check and prune use Sonnet; the editor's plan uses Opus.
- Experiments: one script per experiment in `experiments/` (`bN_*.py`), each with its rules in the docstring.
  `experiments/gpu/` holds the PC scripts; `experiments/modal/` the Modal scripts (`README.md` explains the long-form
  pipeline runner `lf_pipeline.py` and cost estimator `lf_cost.py`).

### 6.2 Data

All under `data/` (gitignored; local to the Mac):
- `human.jsonl` (900 FineWeb explainer pages), `ai.jsonl`, `ai_hard.jsonl`, `topics.jsonl`.
- `drafts/`:
  - `dev.jsonl`: 100 AI drafts, half Sonnet and half Opus; experiments used a0600 to a0629.
  - `h1.jsonl` (100) and `h2.jsonl` (50, the spec's final held-out set): never used.
- `essays.jsonl`: pre-2022-11-30 posts by 13 named essayists (`humanizer.data.essays`), with bench and training
  splits fixed by hash.
- `techblog.jsonl`: 700 first-person technical posts (B17 trained on about 670).
- Training pools, one folder per writer: `lora`, `facts`, `pool`, `mixpool`, `techpool`, `essaypool`, `rewritepool`.
- B25 to B29 inputs: `b25_bench.jsonl`, `b27_texts.jsonl`, `b28_bench.jsonl`, `b28_sonnet.jsonl`, `b29_texts.jsonl`.
- Long-form corpus (B32 pilot): 15,132 posts, one per site, on the Modal Volume `longform` (`b32/pilot/corpus.jsonl`).
  The full pilot is also local in `results/b32_pilot_full.jsonl` (gitignored), including the 798 B39 reserve posts.
  Do not read those unless attempt 2 decides on purpose to retire the reserve. Split by `sha256("b32-split-v1:" + site) mod 100`: 0 to 74 train, 75 to 79 calib,
  80 to 89 dev, 90 to 94 test-A (used by B36 and B37, now development data), 95 to 99 test-B.
- **The B39 reserve:** 798 test-B posts listed by ID and text hash in `results/b39_reserved_testB.json`. Untouched by
  any judge, pick, calibration or scan. Keep it untouched unless attempt 2 decides otherwise, on purpose.
- Texts derived from the essays or the corpus stay local: see `.gitignore` (`/results/b25_*.jsonl` and on,
  `/results/b3[2-9]_*.jsonl`).

### 6.3 Models and adapters

- Base writer: OLMo-2-1124-13B (4,096-token context), 4-bit NF4 with QLoRA adapters, trained on the PC with
  `experiments/gpu/train13b.py` (B17's recipe).
- Adapters (weights gitignored, local on the Mac): `results/gpu13b/out*/lora-13b-v1` for `out` (notes writer),
  `out_facts`, `out_pool`, `out_mixpool`, `out_techpool`, `out_essaypool` (the B26 voice writer) and
  `out_rewritepool` (the B30 rewriter). Copies sit on the PC in `C:\hgpu`.
- MLX conversions for the Mac in `models/` (20 GB): `lora-13b-*-mlx`, `olmo2-13b-base-4bit`, detectors.
- On Modal, Volume `b31-weights` (641 GiB): base weights from B31 under `models/<repo>/<revision>` (OLMo 1 to 3,
  Olmo 3 7B stage checkpoints, Mistral, Qwen, Gemma 3, Nemotron, Pythia and others), detector weights (Falcon 7B pair,
  MELD, desklib) and the B30 adapter under `adapters/b30-rewritepool`.

### 6.4 Machines

- **Mac:** no heavy jobs (Henry, 2026-11-05: training and local-model generation make it unusable). It copies files,
  builds prompts, runs Claude-based checks and drives scans. One large model in memory at a time; never two GPU jobs
  in parallel processes (a Metal out-of-memory crash on 2026-11-04).
- **Windows PC:** RTX 5080, 16 GB, reached over SSH through Tailscale. Address, user and key:
  `docs/private/machines.md`.
  - **Python and files.** Python lives at `C:\hgpu\.venv`. Training pools go to `C:\hgpu\data_<pool>` with `scp`,
    and adapters come back from `C:\hgpu\out_<pool>\lora-13b-v1`. `experiments/peft_to_mlx.py` converts a PC adapter
    for MLX on the Mac; `experiments/import_gpu.py` merged early PC generations.
  - **Jobs.** They are .cmd files in `experiments/gpu/`. For example, `b30gen.cmd` calls `gen_loop.cmd`, which runs
    `gen13b_guard.py` in passes of at most 1.8 hours through `gpu_job.cmd`, 2 minutes apart so umwelt can take a
    turn.
  - **The lock.** `gpu_job.cmd` takes the folder lock `C:\gpu-lock`, writes its owner and releases it even on failure.
    Jobs are logged in `C:\gpu-schedule.txt` by hand; no script writes it.
  - **Status.** `status.ps1` shows processes, GPU use and the run log. Run it as `powershell -File`; the SSH shell is
    cmd.
  - **Sharing.** The GPU is shared with Henry's umwelt project. Never touch its processes, its lock or
    `C:\gpu-pause`, which belongs to umwelt.
  - **Speed.** About 7.5 tokens a second for the 13B writer in 4 bits.
  - **Launching detached (recorded 2026-11-07, attempt 2).**
    1. Check Tailscale first: `tailscale status` must show `henryspc` active. "Offline" means the PC's Tailscale
       client is disconnected even when the PC is on.
    2. Copy files with `scp -O` (the legacy protocol). Plain `scp` fails with "Connection closed" on this Windows
       OpenSSH.
    3. Give .cmd files CRLF line endings.
    4. Append a line to `C:\gpu-schedule.txt`.
    5. Launch with a scheduled task, which survives the SSH session:
       `schtasks /create /tn <name> /tr "cmd /c C:\hgpu\<job>.cmd > C:\hgpu\<job>_run.log 2>&1" /sc once /st 23:59 /f`,
       then `schtasks /run /tn <name>`.
    6. Check `C:\gpu-lock\owner` and the run log.

    Always check `status.ps1` and the lock before starting anything.

### 6.5 Modal

- **What it is used for:** batch generation (B30, B36, B37, B38), vLLM base-model sampling (B31), the corpus build
  (B32), the open-detector panel (B33) and judge training (B38).
- **Account:** Henry's workspace on the Starter plan (name in `docs/private/machines.md`): $30 a month of free compute
  credit and 1 TiB a month of free Volume storage; the credit resets each month. Henry approved up to $80 of paid use
  for the long-form program, staged, and none was spent. Any paid use needs Henry's yes, and possibly a payment
  method he adds.
- **Setup on this Mac (done):**
  - The client is a uv tool at `~/.local/bin/modal` (version 1.6.3), authenticated in `~/.modal.toml`. It is not
    installed in `.venv`.
  - On a new machine: `uv tool install modal`, then `modal token new` (Henry signs in).
  - The Hugging Face token is the Modal secret `huggingface` (key `HF_TOKEN`). The rotation command is in
    `docs/private/machines.md`.
  - Henry's Hugging Face account has gated access to Gemma 3 and Llama 3.1.
- **Day to day:**
  - Run ephemeral apps: `~/.local/bin/modal run experiments/modal/<script>.py`.
  - Afterwards check `~/.local/bin/modal app list`; stop strays with `modal app stop -y <app-id>`.
  - Spend: `~/.local/bin/modal billing summary` (month to date, credits applied, billed cost).
  - Volumes: `modal volume ls <name> <path>`; sizes through the Python client (`Volume.iterdir(recursive=True)`).
  - Estimate before running: `experiments/modal/lf_cost.py`. Run `python experiments/modal/lf_pipeline.py <config>`
    with plain `python`, because it shells out to `modal run`. `--dry-run` prints the estimates, and `--budget`
    (default $5) refuses to start above the budget.
- **Patterns that work** (see `experiments/modal/b30_gen.py`):
  - Resolve the repo root with `modal.is_local()`: inside the container the script lives at `/root`.
  - Give a GPU fallback list (`["L4", "A10G", "L40S"]`): L4 capacity ran short on 2026-11-06.
  - Keep weights on the Volume and symlink them to the hub id the script loads, with `HF_HUB_OFFLINE=1`.
  - Shard longest-first and use `starmap(..., order_outputs=False, return_exceptions=True)`.
- **Spend at close:** about $21 of the month's $30 free credit used (B30, B31 and the long-form program), $0.00
  billed. The 641 GiB on Volumes sits inside the free 1 TiB, so keeping it costs nothing.

### 6.6 Pangram

- **Account:** Henry's Pangram Professional plan (bought 2026-11-05, his own spend). 8,717 dashboard credits on
  2026-11-06 at 13:34. Cost: 1 credit per started 100 words per file; the dashboard balance difference runs slightly
  below the per-file sum, and the balance difference is what the ledger records. The API key (in `.env`, which
  sessions never read) returned HTTP 402 on 2026-11-04, on the Individual trial. The Professional plan advertises
  monthly API credits, but nobody has retried, so every scan went through the dashboard. Ask Henry before trying the
  API.
- **Judge rules:**
  - Pangram is a held-out judge: its scores never select a prompt, weight or writer, except the B1 gate and detector
    calibration.
  - Exception (Henry, 2026-11-06 13:08): a local judge may be trained on Pangram labels and used to pick outputs, as
    long as a final test set it never sees stays reserved (`CLAUDE.md`).
  - Selection, exclusion and decision rules go in the script docstring and are committed before any scan.
- **Scan procedure.** The dashboard route was used from B3 on. Blinded random file names came in with B31; saved
  transcripts and share files with B36. The steps as of B38:
  1. Write each text to `<random id>.txt` and convert: `textutil -convert docx <file>.txt`. Commit the blinding key
     (id to cell) before uploading.
  2. Confirm the browser is this Mac's Chrome, not Henry's work computer's (both run Claude in Chrome on one
     account). Write a one-time token to a scratch folder, serve it with
     `python3 -m http.server <port> --bind 127.0.0.1 --directory <folder>` on a port no other session uses, open
     `http://127.0.0.1:<port>/token.txt` in a new tab of your own, and compare. `list_connected_browsers`' isLocal flag
     is only a weak hint.
  3. Open https://www.pangram.com/dashboard in your own new tab (never another session's). Note the credit balance.
  4. Choose the Upload tab, find the file input, upload up to 100 .docx files with the `file_upload` tool, and
     click "Check for AI".
  5. Wait 30 to 60 seconds (longer for big batches), then read the list with `get_page_text`. Each row gives the file
     name, credits, words and label (Human, Mixed or AI). Save it as the raw transcript
     (`results/bNN_pangram_transcript.txt`, one line per file in the form `name.docx|N Credits,M Words|Label`).
  6. Read each file's AI share with `experiments/pangram_dashboard_read.js` through `javascript_tool`, then
     `JSON.stringify(window.__pangram)`. The script returns `{name, pct, kind, legend_ai, words}`. Convert to the
     saved format `{name, ai}`: `ai = pct` when `kind` is AI, else `legend_ai`, else `100 - pct`. Save it as
     `results/bNN_pangram_shares.json`. The file was assembled at close from the code B37 and B38 ran, and has not
     been run as a file: check it on the first batch.
  7. Note the balance after, add a row to the notebook's credit ledger, and close your tab.
- **What the verdicts mean:**
  - Human needs under about 10% of words flagged.
  - Mixed covers roughly 0.10 to 0.80 AI share.
  - Pangram 4.1's model card gives a 50-word minimum and lower certainty under 150 words. An 85-word text came back
    "Possibly human (short text)" (B38).
  - The project counts any text under 150 words as not Human.
  - LaTeX inflates Pangram's word count 1.31 to 1.49 times and raises the share.
  - Pangram publishes no accuracy data above 499 words (`results/research/longform-pangram-length.md`).

### 6.7 Claude

- The Claude command-line tool is installed at `~/.local/bin/claude` and logged in to Henry's account.
- Bulk `claude -p` calls go through `humanizer.llm` (cached; at most 4 workers in total), because Henry's Claude
  account is shared with his work computer.
- Use open models on Modal for bulk generation, and keep Claude for test-set drafts, since Henry's real drafts come
  from Claude.

### 6.8 Method conventions

- **Pre-registration.** Each experiment's selection, exclusion and decision rules sit in its docstring and are
  committed before any scan. Amendments carry a time read from `date` and say what was and was not yet seen.
- **Paired designs.** The same documents across cells, blinded scans, and Fisher, sign, Wilcoxon and McNemar tests
  as fits. Treat p values as screening, not proof.
- **Validators with fresh contexts:** the `outside-judge` agent and general-purpose agents, given the artifacts and
  the claims, never the reasoning. Every long-form gate had:
  - a statistics recompute from raw files;
  - an order audit (git times against scan times);
  - a red team.

  B36 and B38 also had selection or leakage audits.

  Reports are saved under `results/research/`. The red teams changed the reading of B36, B37 and B38.
- **Write-ups.** Every experiment gets a notebook row, a report section, and a credit-ledger row if scanned. Every
  literature search gets a search-log row with the agent's raw report under `results/research/`.
- **Subagents** get the line "work at expert depth, start from raw data, verify with an external check, report what
  you could not verify", and the goal behind their task.

### 6.9 Repo rules

- **Public repo.** Texts derived from essays or corpora stay gitignored; commit code, docs and numeric summaries
  only.
- **Shared checkout.** Commit only your own files with a pathspec. Never use `git add -A`, stash, reset or switch
  branches. End commit messages with the `Co-Authored-By` line. Push only when Henry asks.
- **Confidentiality.** Henry's context-engineering post describes a project whose details stay private. Keep the
  post's own wording about it (for example "diabetes management coaching agent"). Add nothing about the project, its
  owner or its users, in any file, the public repo or a third-party tool.
- **Credentials.** Never read `.env`. Never write a secret value into a file.
- **Writing.** Docs and reports use no em dashes and no emojis, and spell out acronyms on first use.

## 7. Resources and state at close

| Resource | State |
|---|---|
| Money against the $100 cap | Modal $0.00 billed (everything inside the free credit). Pangram plans are Henry's own spend |
| Pangram | 8,717 credits. The long-form program used 2,632 of its 6,000 budget; full ledger in the notebook |
| Modal | About $21 of $30 free credit used this month; Volumes `b31-weights` (641 GiB) and `longform` (0.4 GiB), inside the free 1 TiB; no app running |
| PC | No humanizer job running or queued |
| Git | All attempt-1 work committed on `master`, more than 46 commits ahead of GitHub, not pushed |
| B39 reserve | 798 test-B posts, untouched |

**Open items for Henry:**
- Rotate the Hugging Face token he pasted in chat, then update the Modal secret.
- Do the blind read.
- Decide whether to retry the Pangram API key on the Professional plan.
- Decide whether to push to GitHub.

**Housekeeping left as is:**
- Untracked and left alone:
  - `S.pkl`, `w.pkl` and the `*.log` files in the repo root;
  - `experiments/gpu/b8.cmd`;
  - `results/b16_*.jsonl` and `results/b17_*.jsonl`. These are now gitignored; B17's hold rewrites of Henry's post.
- Adapter folders under `results/gpu13b/out_*` show as untracked (their weights are gitignored).
- Session scratchpads under `/private/tmp` (upload folders, validators' scripts) are temporary. Every number a report
  cites comes from a committed file.

## 8. Lessons

**Process:**
- Same-day, blinded, paired scans with rules committed first held up under every audit. Keep them.
- Shorter text reads more human. Any comparison must control length, or record it and test it.
- A pooled AUROC across experiments mostly measures which experiment a text came from (B38). Measure judges on the
  decision they will make.
- The Sonnet claim check passes invented code, other languages, template loops and invented framing. Use the form
  and repeat checks too, and read outputs.
- "Reads Human" is not "publishable". Read the outputs a verdict rests on; the bandits rewrite showed why.

**Technical gotchas:**
- A file in a scratch folder named like a standard module (for example `copy.py`) breaks Python run from that
  folder. Run scripts with `python -I` from a clean folder.
- Over SSH the PC's shell is cmd: run PowerShell files with `powershell -File`.
- `modal app stop` needs `-y` outside an interactive terminal.
- The harness blocks long foreground `sleep`. Wait with a background until-loop or a monitor.
- Untracked new files need `git add <path>` before a pathspec commit.

## 9. File map

| What | Where |
|---|---|
| Experiment index, search log, credit ledger | `results/LABNOTEBOOK.md` |
| Full write-ups B3 to B38, status snapshots and the long-form pause (B39 never ran) | `results/REPORT-2026-11-04-lora.md` |
| B0 to B2 | `results/REPORT-2026-11-05.md` (misdated; it came first) |
| One-page summaries | `results/B31-SUMMARY.md`, `results/LONGFORM-GATE1.md`, `results/LONGFORM-GATE2A.md`, `results/LONGFORM-JUDGE.md` |
| Literature | `results/RESEARCH-2026-11-04-prior-work.md`; raw reports `results/research/r1-*.md`, `r2-*.md`, `b31-*.md`, `longform-*.md` |
| Claims ledgers | `results/research/longform-claims.md`, `results/research/b31-claims.md` |
| Specs, plans, briefs | `docs/specs/`, `docs/plans/2026-11-04-humanizer-phase1.md`, `docs/briefs/` |
| Experiment scripts | `experiments/bN_*.py`; PC `experiments/gpu/`; Modal `experiments/modal/` |
| Pangram page script | `experiments/pangram_dashboard_read.js` |
| Raw verdicts and shares | `results/bNN_*.json`, `results/bNN_pangram_transcript.txt`, `results/bNN_pangram_shares*.json` |
| Machines and accounts | `docs/private/machines.md` (local only) |
