# Long-form program head brief: humanizing whole blog posts, at scale, on Modal

Written 2026-11-06 01:20 by the main humanizer session, for a separate session that owns this program end to end.
Henry asked for it (2026-11-06 01:00): "now you have access to modal, maybe we can go through that route instead.
Actual long text, actual large scale experimental setup handled by agents with its own contexts so they can be
validated correctly."

## The goal behind the task

Henry's real use is his own blog posts: technical posts of 1,500 to 3,000 or more words (for example
`~/personal/blog/series/ai-engineering/part1.html`) drafted with an AI. The project (`~/personal/human`; read
`CLAUDE.md`, `results/LABNOTEBOOK.md`, the "Where this stands" section and sections 30 to 34 of
`results/REPORT-2026-11-04-lora.md`, and `results/B31-SUMMARY.md`) has so far worked small and short:
- **Short texts.** Outputs of 300 to 800 words; B31's texts were about 235 words, under one 512-token Pangram window.
- **Small samples.** Cells of 13 to 30 documents, and B31 showed that the document being continued matters more
  than the model, so the document, not the text, is the unit of generalization.
- **Short context.** The writer is OLMo-2-13B, which has a 4,096-token context, so essays were cut to 1,300 words.
- **Small hardware.** It runs in 4 bits on a 16 GB GPU at about 7.5 tokens a second.

The program's job: find out, with powered, held-out evidence at real length, whether and how an AI-drafted long
post can be made to read human to Pangram and to careful readers without inventing anything. Along the way, build
the reusable Modal pipeline that does it, so the next experiment is a config and not a week of plumbing.

## Treat everything below as claims to test, not facts

Henry's standing instruction: do not take the project's findings as facts. Be research-oriented, and be as ready
to refute as to confirm. Keep a claims ledger (`results/research/longform-claims.md`) with each claim, its source,
how you checked it and its status. Claims to start it:

1. **Content source is the signal.** Posts written from human-sourced facts read Human 17 of 20; from AI-sourced
   facts, 1 of 20 (B5). The human share needed is between a third and two thirds (B9). These are short texts in
   small samples.
2. **The pipeline.** The B14 pipeline (specific facts, then the pool writer, pruning and best of 4) reads 13 Human,
   7 Mixed and 0 AI on 20 drafts. Its output is about 40% of the draft's length and 86% of its claims are supported.
3. **B28 and B30 (pending, about 03:00).** B28 is the dose of a blogger's own notes. B30 is a learned rewriter from
   an AI post to the essay, its first direct test. The main session sends you both results when they are scanned.
   They bear directly on question 1 below.
4. **B31.**
   - Raw base-model continuations read not Human 12 to 43% of the time, whatever the model's vintage.
   - The opening matters more than the model.
   - Post-training is the large effect.
5. **HALO** (`results/research/r1-papers-benchmarks.md`): raw OLMo-2-32B continuations read 0.03 AI against
   0.27 for 7B. B31 found no size trend (Spearman -0.30 on log parameters, p 0.21). Which holds, and at what length?
6. **Long documents in Pangram.** How Pangram aggregates its windows into a document label (Mixed, AI share), and
   whether length by itself moves the verdict. Read Pangram's technical report and documentation, then test it.

## Questions (yours to sharpen in the design doc)

- **Q1.** At real length (1,500 to 3,000 words, whole posts), what share of outputs read Human, by input
  condition: an AI post alone; an AI post plus the author's notes; notes only?
- **Q2.** What does scale buy?
  - A larger or long-context base model.
  - Much more training data: thousands of long pre-ChatGPT posts from many authors.
  - AI drafts from several generator families, not only Sonnet.
- **Q3.** Whole-document generation against section by section with carried context.
- **Q4.** Does it hold on Henry's genre (technical posts with code and tables) and on Henry's own AI drafts? Ask
  him for drafts through the main session, or directly when it is time.

## Design requirements

- **Held-out judge.** Pangram never selects a model, prompt, weight or writer (CLAUDE.md).
  - Develop against off-the-shelf open detectors run on Modal (for example Binoculars and Fast-DetectGPT; find
    what is strongest in 2026), plus the local checks: claim support, copying and length.
  - You may measure how well the open detectors agree with Pangram on the roughly 2,000 Pangram-labelled texts
    from B1 to B31. That counts as detector calibration.
  - Do not train any detector on Pangram labels without Henry's yes.
- **Splits.**
  - Split by author or site: no test author appears in training.
  - Human text must be published before 2022-11-30, with the date verified (Common Crawl dump or Wayback).
  - Test documents stay untouched until the final scan.
  - Run a power analysis on documents before fixing n, and use paired designs.
- **Long context.** OLMo-2 has 4,096 tokens.
  - Candidate base models (verify each): Olmo 3 32B and 7B (65,536 tokens; open data, so test documents can be
    checked for training-set contamination), Gemma 3 27B (gated, access granted in B31), Llama 3.1 (gated, access
    granted), Mistral Small 24B, Qwen3.5 base.
  - Choose by a rule fixed in advance on development metrics, never Pangram.
- **Faithfulness.**
  - Add no facts, names, numbers, dates or quotes. The Guard (`src/humanizer/pipeline/guard.py`) does this today
    through a Hugging Face logits processor.
  - Long-context generation needs an equivalent: a vLLM logits processor, or a check-and-resample loop.
  - Run the claim check on every output.
- **Quality.** Blind reads: an LLM panel, whose known bias toward AI style is noted in section 17. Henry also
  blind-reads a small set; build it the way the existing blind read was built, through ArtifactData.

## Agents and validation (the core of Henry's request)

- **You are the head.** You own the plan, the budget, pre-registration and sequencing.
- **Workstreams.** Give each workstream its own context, as subagents or sessions: corpus, draft generation,
  training, generation and evaluation.
- **Independent validation.** Every artifact that a claim rests on gets a validator with a fresh context. Give it
  the artifact and the claim, never your reasoning; the `outside-judge` agent fits. At minimum:
  - an author and site leakage audit of the splits;
  - a publication-date audit of the human texts;
  - a contamination check of test documents against the open training data where possible;
  - a recompute of every statistic from the raw verdict files;
  - an audit that every design commit precedes the scans it governs (git times against scan times);
  - a copying audit.
- **Red team.** One red-team agent attacks the final result, looking for length, topic and genre confounds, Guard
  artifacts and selection effects.
- **Pass this line to every agent:** work at expert depth, start from raw data, verify with an external check,
  report what you could not verify.

## Resources and rules

- **Modal.**
  - Account: workspace `vuducdung28`, Starter, $30 monthly free credit. Client: `~/.local/bin/modal` 1.6.3.
  - Spent so far: B31 about $3; B30's generation tonight about $5.
  - **Budget: stay inside the remaining free credit (about $20) until Henry approves more.** Before any run,
    estimate its cost and log it. Before a run that would cross the line, stop and ask, through the main session
    (SendMessage) or Henry directly.
  - Write a phase-by-phase cost estimate early so Henry can set a budget.
  - Use ephemeral `modal run`, and check `modal app list` afterwards so nothing stays idle.
  - Existing assets:
    - The Volume `b31-weights` holds about 680 GB of base weights, including OLMo-2-13B and Olmo 3 7B, which you
      can reuse.
    - `experiments/modal/b31_modal.py` (vLLM 0.32.0) and `experiments/modal/b30_gen.py` (Hugging Face and PEFT,
      4-bit, Guard) are working patterns.
    - The Hugging Face token is stored as the Modal secret `huggingface`; Henry may rotate it.
- **Pangram.**
  - Henry's dashboard, Professional plan: 12,090 credits after B31, and B28 and B30 will use about 1,100.
  - **Budget for this program: 6,000 credits.** A 2,000-word post costs about 20 credits, so this is about 300
    document scans. Plan the final test inside it.
  - Procedure as in B31's brief (`docs/briefs/2026-11-05-b31-head.md`): your own Claude in Chrome tab, and a
    one-time token on 127.0.0.1 on a port other than 8799 and B31's.
- **Claude.** Bulk `claude -p` calls go through `humanizer.llm` (cached, at most 4 workers; the account is shared
  with Henry's work computer). Keep to 2 while the main session runs B28 and B30 picks. Use open models on Modal
  for bulk generation. Keep Claude for test-set drafts, since Henry's real drafts come from Claude.
- **Other machines.** Never run heavy jobs on the Mac. The Windows PC belongs to the main session; do not use it.
- **Numbering.** Use experiments B32 to B39 for this program (the main session uses B40 and on). Each gets a
  notebook row, a report section and a literature search log row with the raw agent report under
  `results/research/`.
  - Fix selection, exclusion and decision rules in the script docstring and commit them before any scan.
  - Amendments carry a time read from `date`.
- **Public repo** (HenryVu27/human). Corpus texts, drafts and outputs stay local: add their patterns (for example
  `/results/b32_*.jsonl`) to `.gitignore`. Commit only code, docs and numeric summaries. Do not push.
- **Shared checkout.**
  - The checkout is shared with the main session. Commit only your own files, with a pathspec
    (`git commit -m ... -- <paths>`). Never use `git add -A`, stash, reset or switch branches in
    `~/personal/human`. Use your own worktree for anything bigger.
  - Do not edit B28, B30 or `experiments/gpu/` files.
  - End commit messages with "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>".
- **Writing.** Docs and reports: no em dashes, no emojis, acronyms spelled out on first use, no blockquotes.
- **Autonomy.** Work without waiting for Henry. Stop only for money beyond the budget, his accounts, or his drafts.

## Done looks like

1. **Claims ledger,** each claim marked verified, refuted or unverified with its evidence.
2. **Program design doc** (`docs/specs/2026-11-06-longform-program.md`), including the power analysis and the
   phase cost estimate. It is committed before any scan, and each experiment's rules are in its script docstring.
3. **Reusable Modal pipeline** (corpus, drafts, training, generation, checks), with a README saying how to run a
   new experiment.
4. **Results** with every exclusion counted and each validator's report saved under `results/research/`.
5. **Report section and notebook rows** saying what the data support, how strongly, and what they could not
   separate.
6. **A one-page summary for Henry,** opened or sent to him, with Modal and Pangram spend.
7. **Phase-gate notes** to the main session (SendMessage) at each gate: design committed, corpus built, model
   chosen, final scan done.
