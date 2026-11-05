# Humanizer lab notebook

One index of every experiment and every literature search: what was asked, how it was tested, what came out, and where the evidence lives. Detailed write-ups stay in `REPORT-2026-11-05.md` (B0 to B2, the first overnight run) and `REPORT-2026-11-04-lora.md` (LoRA writer, B3 onward). Literature findings are in `RESEARCH-2026-11-04-prior-work.md`, and the agents' raw reports are in `research/`.

## Method rules (apply to every experiment)

- **Pangram is a held-out judge.** Its verdicts never choose a prompt, weight or writer. The two exceptions in the spec are the B1 gate and detector calibration (`surrogate.py`).
- **Selection is fixed before the scan.** Which texts a test covers is set by a rule that is written into the experiment script's docstring and committed before anything is scanned. Examples: dev a0600 to a0609 by id, the first 10 validation rows, a minimum fact count. No text is swapped out after its verdict is seen.
- **One variable per comparison.** Cells differ in one factor: same writer, seed 0, same sampling (temperature 0.8, top_p 0.95, repetition penalty 1.05) and the same length rule, unless the factor under test is one of these.
- **Manipulation checks.** Before scanning, word 4-gram overlap confirms that a manipulation did what it claims. Example: rewording cut source wording from 47% to 8% in B5. When the writer moved from the PC to the Mac, validation loss confirmed the PEFT-to-MLX adapter port (a drop of 0.132 on the Mac against 0.131 on the PC).
- **Statistics.** Fisher's exact test, two-sided, on Human against not Human, with about 10 texts per cell. Treat p values as screening, not proof. Results come from a single seed, and Mac-against-PC noise is about 3 verdicts in 10 (B4 cell A against B5 cell A).
- **Scanning procedure.** Texts become .docx files (macOS textutil) and go through the Pangram dashboard upload, Individual plan. Before any upload, a one-time token served on 127.0.0.1 confirms that Claude in Chrome is driving this Mac's Chrome. Verdicts are read from the page and recorded with each script's `record` step.
- **Spend.** The $100 cap is unchanged. The only money spent is Henry's Pangram Individual plan, $20 a month on a 7-day trial, with 3,000 dashboard credits. The API key has no credit (402).

## Experiment index

| ID | Date | Question | Design | Result | Files |
|---|---|---|---|---|---|
| B0 | 11-04 | Can a weight edit remove the assistant register? | Mean-difference direction ablation on Qwen3.5-4B, scripted arm | No effect on the local detector; agent arm not run | REPORT-2026-11-05 section 2 |
| B1 | 11-04 | Do base-model continuations pass Pangram? | 3 OLMo-2-13B continuations of human openings and 1 Qwen3.5-9B base continuation, picked by a rule written before scanning | OLMo 3 of 3 Human; Qwen AI | b1_pangram_free.json |
| B2 | 11-04 | Can a prompted base model write from notes? | 20 dev drafts; arms: Claude rewrite, prompted base, guard, pruner | Judge preferred the draft 20 of 20; 46% of claims supported (88% for the Claude rewrite) | b2_dev.json |
| LoRA | 11-04 | Does fine-tuning fix control? | QLoRA 7B (Mac) and 13B (PC) on notes-to-article pairs | 13B: 96% of claims supported, on-target lengths; quality wins 7.5 to 15% (human ceiling 32.5%) | REPORT-lora sections 1 to 3 |
| B3 | 11-04 | Does the AI signal travel through the notes? | 13B writer; 10 sets of notes from AI drafts and 10 from human articles | AI notes: 10 AI. Human notes: 10 Human. p = 0.00001 | b3_notes_leak.json |
| B4 | 11-04 | Do fact-only notes remove it? | Writer retrained on shuffled fact lists; same groups as B3 | AI facts: 9 AI, 1 Mixed. Human facts: 10 Human. Facts keep about half the source's 4-grams | b4_facts.json |
| B5 | 11-04 | Wording, source or topic? | 2x2 on the same 10 topics: source (AI draft or human original) by wording (verbatim or reworded); Mac | Human-sourced 17 of 20 Human, AI-sourced 1 of 20 (p = 4e-7); rewording changes nothing | b5_matched.json |
| B6 | 11-04 | Does cutting generic facts help? | AI facts cut to the specific ones, against a random cut of the same size; 8 drafts | 3 Human, 3 Mixed, 2 AI against 2, 3, 3: no better than random; short texts confound the result | b6_selection.json |
| Surrogate | 11-04 | Can a local detector stand in for Pangram? | AUROC of detector-v1 and v2 on 96 Pangram-labelled texts | 0.83 to 0.87 overall but 0.54 to 0.67 among AI-sourced texts: not usable for selection | surrogate.json, pangram_labels.jsonl |
| B7 | 11-05 | Does a writer that plans for itself help? | Pool writer trained on partial fact lists (20 to 60%); cells H (old writer), P (specific facts), Q (random 40%) at full draft length, with the Guard | P: 6 Human, 3 Mixed, 1 AI (clean texts: 4, 3, 0); about 45% of claims supported; looping texts inflate H | b7_pool.json |
| B11 | 11-05 | Does the B7 gain survive deleting unsupported sentences? | Sonnet marks sentences the draft does not support; they and repeats are deleted, nothing reworded; all 20 P and Q texts | P pruned: 7 Human, 1 Mixed, 2 AI at 76% claim support, 419 words (p = 0.02 against B5 A) | b11_prune.json |
| B12 | 11-05 | Does the B7-P plus B11 pipeline replicate? | 20 new drafts a0610 to a0629; pipeline against Sonnet condensing the draft to the same length; quality judge | Running | b12_replicate.py |
| B8 | 11-05 | Can the writer learn to drop AI-typical facts? | Writer trained on pools that mix human facts with facts from the AI mirror of the same topic; target is the human article | Mirror facts being extracted; training on the PC next | b8_mixpool.py |
| B10 | 11-05 | Does compression fall in Pangram's blind spot? | Sonnet condenses each AI draft to 25% and 50%, adding nothing and with no instruction to sound human; 10 drafts | 20 of 20 AI: an instruct-model writer is caught whatever the compression | b10_compress.json |
| B9 | 11-05 | How much human-sourced content is needed? | Dose-response: 0, 1/3 and 2/3 human facts at a fixed count (B5 cell D is the 1 point) | Queued on the Mac after B7 | b9_dose.py |

## Literature search log

| Round | Date | Agent angle | Tools and sources | Notes | Raw report |
|---|---|---|---|---|---|
| 1 | 11-04 | Open-source humanizers on GitHub and Hugging Face | WebSearch, WebFetch; repos, READMEs, eval code, issues | Ranked 12 projects; none shows AI-sourced text passing 4.x | research/r1-github-oss.md |
| 1 | 11-04 | Papers and independent benchmarks | WebSearch, WebFetch; arXiv, ACL, NeurIPS, vendor reports | Only base-model generation is credible against 4.x | research/r1-papers-benchmarks.md |
| 1 | 11-04 | X (Twitter) | Claude in Chrome, Henry's signed-in X account, read only, own tab | 15 posts; agent loops lose their gradient on 4.x; "reasoning structure" | research/r1-x-search.md |
| 2 | 11-05 | Primary sources in depth: HALO, PASTA, Pangram 4 report, DFT, Emulate-1, HIP, Unslopper | WebFetch on full arXiv HTML, Wayback Machine for the deleted DFT page, GitHub data | Pangram's mirror labels explain B5; HALO's copy rate and model-size ablations; red-team hole | research/r2-primary-sources.md |
| 2 | 11-05 | Adjacent fields: mode collapse, content planning, stylometry, deception, distribution matching | WebSearch, WebFetch; arXiv, ACL Anthology | 5 ranked experiments, including dose-response (now B9) | research/r2-adjacent-fields.md |
| 2 | 11-05 | Reddit, Hacker News, Substack, LessWrong, GitHub issues | Hacker News Algolia API, WebFetch; Reddit and Lobsters were blocked | Independent source-effect replication; wording pipelines fail on 4.x | research/r2-forums-hn.md |
| 2 | 11-05 | X thread follow-ups | Claude in Chrome, read only, own tab | Base model in continuation mode passes; instruct-model sentence picking is caught; a base model's completion takes the label of the notes in its context; IdeaLens (arXiv 2610.06778): Pangram follows who wrote the prose | research/r2-x-followups.md |

**Spot checks against primary pages:** HALO's abstract (Pangram v4, detection 77% to 24%) and phuryn/work-humanizer's page (Pangram 4; AI drafts 4% human; writer's own notes 4 of 4) both match what the agents reported. Everything else in the agent reports is unverified unless the report says it read the primary source.

**Gaps:** no Reddit or Discord content (blocked), Indicator's paywalled audit, and Pangram's red-team success rates.

## Pangram credit ledger

| Scan | Texts | Credits |
|---|---|---|
| B1 and the first probe (Free plan) | 5 | 13 of 13 free |
| B3 | 20 | 127 |
| B4 | 20 | 218 |
| B5 | 40 | about 450 |
| B6 | 16 | 61 |
| B10 | 20 | 140 |
| B7 | 30 | about 400 |
| B11 | 20 | about 100 |
| Remaining on the Individual plan after B11 | | about 1,500 of 3,000 |

## Current hypothesis

Pangram 4 labels an instruct model's content plan for a topic as AI, because that is how it builds its training labels (synthetic mirrors). Its training data contains no base-model text and no LLM output shorter than its input. A full humanizer must therefore replace the AI draft's plan, using one of three sources:

1. The base model's own plan: B7, B8, and HALO's 90% copy rate.
2. Human-sourced content: B9, and retrieval of human sources for the draft's claims.
3. Compression of a large source into a shorter text: the red team's one admitted hole. B10 shows it does not work with an instruct-model writer.

At every step the claim check and the Guard keep the output from inventing facts.
