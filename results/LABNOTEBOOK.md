# Humanizer lab notebook

One index of every experiment and every literature search: what was asked, how it was tested, what came out, and where the evidence lives. Detailed write-ups stay in `REPORT-2026-11-05.md` (B0 to B2, the first overnight run) and `REPORT-2026-11-04-lora.md` (LoRA writer, B3 onward). Literature findings are in `RESEARCH-2026-11-04-prior-work.md`, and the agents' raw reports are in `research/`.

## Method rules (apply to every experiment)

- **Pangram is a held-out judge.** Its verdicts never choose a prompt, weight or writer. The two exceptions in the spec are the B1 gate and detector calibration (`surrogate.py`).
- **Selection is fixed before the scan.** Which texts a test covers is set by a rule that is written into the experiment script's docstring and committed before anything is scanned. Examples: dev a0600 to a0609 by id, the first 10 validation rows, a minimum fact count. No text is swapped out after its verdict is seen.
- **One variable per comparison.** Cells differ in one factor: same writer, seed 0, same sampling (temperature 0.8, top_p 0.95, repetition penalty 1.05) and the same length rule, unless the factor under test is one of these.
- **Manipulation checks.** Before scanning, word 4-gram overlap confirms that a manipulation did what it claims. Example: rewording cut source wording from 47% to 8% in B5. When the writer moved from the PC to the Mac, validation loss confirmed the PEFT-to-MLX adapter port (a drop of 0.132 on the Mac against 0.131 on the PC).
- **Statistics.** Fisher's exact test, two-sided, on Human against not Human, with about 10 texts per cell. Treat p values as screening, not proof. Results come from a single seed, and Mac-against-PC noise is about 3 verdicts in 10 (B4 cell A against B5 cell A).
- **Scanning procedure.** Texts become .docx files (macOS textutil) and go through the Pangram dashboard upload, Individual plan. Before any upload, a one-time token served on 127.0.0.1 confirms that Claude in Chrome is driving this Mac's Chrome. Verdicts are read from the page and recorded with each script's `record` step.
- **Spend.** The $100 cap is unchanged. The only money spent is Henry's Pangram Individual plan, $20 a month on a 7-day trial, with 3,000 dashboard credits. The API key has no credit (402). On 2026-11-05 at about 18:15 Henry upgraded to Pangram Professional (15,000 credits, his spend, not counted against the cap); credits stop being the binding constraint.

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
| B12 | 11-05 | Does the B7-P plus B11 pipeline replicate? | 20 new drafts a0610 to a0629; pipeline against Sonnet condensing the draft (overshot to 642 words against 393) | Pipeline 12 Human, 4 Mixed, 4 AI at 81% claim support; condensation 20 of 20 AI (p = 0.00005) | b12_replicate.json |
| Judge check | 11-05 | Is the quality judge fair to non-Sonnet prose? | 20 human articles cut to about 400 words against Sonnet condensations of the same articles | Judge prefers Sonnet 20 of 20: biased; use same-topic human text as the reference | judge_calibrate.json |
| B14 | 11-05 | Does best of 4 (picked by claim check) keep more of the draft? | 3 more pool-writer seeds per B12 draft, each pruned and cleaned; keep the most supported claims | 13 Human, 7 Mixed, 0 AI at 86% claim support, 408 words; rescans of identical texts gave the same verdict 7 of 7 | b14_bestof.json |
| B13 | 11-05 | Does a deletion-only cleanup help quality? | Delete repeats, empty lead-ins and fragments from B12 output | 12 Human, 5 Mixed, 3 AI; quality against same-topic human text 0.20 to 0.325 | b13_cleanup.json |
| B8 | 11-05 | Can the writer learn to drop AI-typical facts? | Writer trained on pools mixing human facts with AI-mirror facts on the same topic; tested with all draft facts, 1 sample, prune and clean, B12 drafts | 5 Human, 10 Mixed, 5 AI at 86% support; judged quality 0.575 against same-topic human text (B14: 0.275): a trade-off | b8_mixpool.json |
| B15 | 11-05 | Does the pipeline work on Henry's own post? | B14 pipeline on the 7 prose sections of the context-engineering post; originals scanned too | Originals 0 Human, 3 Mixed, 4 AI; pipeline 4, 1, 2 at a third of the length; poor quality on technical prose (writer never saw the genre) | b15_blog.json |
| B16 | 11-05 | Mixed-pool writer with specific facts only, best of 4 | Crosses B8's writer with B14's input | 14 Human, 4 Mixed, 2 AI at 394 words (one AI piece is 69 words, below Pangram's 150-word floor); B14 13, 7, 0. Per draft: same 11, better 5, worse 4. Quality against the human cut 0.25 (B14 0.275): the mixed-pool writer adds nothing once the input is specific facts only | b16_mixspec.py |
| B17 | 11-05 | Does a genre-matched writer fix technical prose? | Pool writer retrained on 670 pre-2022 first-person technical blog posts from FineWeb-Edu (validation loss 1.823 to 1.765); B15's prompts, best of 4 | 3 Human, 1 Mixed, 3 AI on the 7 sections (B15 cell B 4, 1, 2; worse on s2 and s7, same on 5). Keeps more of the post (1,861 of 4,481 words against 1,498) and its voice (no "the author"; first person 3.5 per 100 words against the original's 1.2 and B15's 1.9, so it overshoots). Genre-matched training fixes voice, not verdicts | b17_techwriter.py |
| B18 | 11-05 | Can the pipeline keep the draft's length? | Paragraph-level write, check, resample: 4 candidate paragraphs per step from a PC paragraph server, Sonnet marks unsupported sentences, the most supported words are kept; B12 drafts to full length; adds a coverage measure (share of the draft's facts stated) | 6 texts (a0610 to a0615; the first run's server cap and a JSON-parse crash, both fixed): 4 Human, 2 Mixed, 0 AI at 347 words, 31% of the draft's length, 17% of its facts covered, 82% of claims supported. B14 on the same 6 drafts: also 4, 2, 0 at 373 words. Resampling one paragraph at a time does not add length: once the prompt's facts are used, new paragraphs are unsupported and the loop stalls | b18_resample.py |
| B19 | 11-05 | Can a simulated author interview supply the human-sourced content B9 says is needed? | Sonnet as editor asks 5 questions on each AI draft; Sonnet as author answers only from the human original; answers' facts join the draft's specific facts; 10 drafts | Interview step only: 7 of 10 authors answered none of the 5 questions (13 of 50 answered in all). The editor asks for first-hand experience and the human originals are third-person articles, so the simulation cannot stand in for a real author. Write step not run; a real test needs a real author (Henry on his own post) | b19_interview.py, b19_interview.jsonl |
| B20 | 11-05 | At B14's fact density but full length, does B14's verdict hold? | Drafts state 40 to 68 facts (about 5 per 100 words), B14 carries about 1.5 per 100, so full length at that density carries about a third of the facts: k = round(length / 400) sections of 6 evenly spaced draft facts, each written with B18's check-and-resample step; 10 drafts | Stopped at 4 of 10 before any scan: pieces reached only 23 to 36% of length (a step keeps about 20 words; 10 steps per section), so the full-length question is untested. 3 usable pieces: 0 Human, 3 Mixed, 0 AI at 327 words; B18 on the same drafts 3 Human. a0612 looped on a question template that every check passed (probe: Mixed). Walking the draft's facts in order brings back its outline | b20_sectional.py |
| B23 | 11-05 | What does the prune delete, and would a narrower rule keep length? | B14 seed-1 raw generations (20); Sonnet labels each sentence S supported, N new specific, C new general claim, E elaboration; template repeats X first; scan only if E is 30% or more and SE keeps 60% of length | Prediction failed, no scan: of raw words S 24%, N 15%, C 16%, E 12%, X 33% (Sonnet alone: S 32, N 27, C 22, E 19). Keeping S and E reaches 43% of length (upper bound 61%) against the prune's 38%. The writer fills length with new facts, not elaboration | b23_prune_tiers.py |
| B24 | 11-05 | Full length with cited human sources: does two-thirds retrieved human content read Human? | Henry's chosen route. 10 drafts (a0610 to a0619); 3 pre-2022 Wikipedia revisions per draft (titles from Sonnet, permalinks cited); B9's dose: a third draft facts (specific first), two thirds source facts chosen by Sonnet, n = length / 17.87; pool writer, Guard, 4 seeds; prune against draft plus sources, template repeats deleted, cleanup, most supported claims kept; attribution of every sentence; Pangram on the bodies | 10 Human, 0 Mixed, 0 AI at 66% of T (B14 on the same drafts 7, 3, 0 at about 40%); claims 92%; 55% of words from sources, 30% from the draft, 22% of draft facts covered. Found before the scan: 21% of words sit in 8-word runs copied verbatim from Wikipedia, nearly all through the extracted facts (2% beyond the prompt); B5 and B9 copied as much, and B5 reworded (about 3% copied) still read 7 of 10 Human. A product must reword or quote source text | b24_cited.py |
| B25 | 11-05 | The blog track: does the humanizer work on personal blog essays, its real genre? | Finding that prompted it (Henry's point, checked on the raw data): every draft to B24 came from FineWeb pages, median 0 first-person words per 100, 7% above 1. New corpus `humanizer.data.essays`: 13 named writers (Graham, Sutton, Borretti, Noah Smith, Cochrane, Sumner, Milanovic, Hanson, Luu, Evans, Spolsky, Scott Alexander, McKenzie), pre-2022-11-30 posts, hash split fixed before reading: 2 bench essays (500 to 1,500 words) and up to 60 training essays per writer. Per bench essay: Sonnet notes (FACTS prompt, first person kept), then Sonnet's post from the notes (the blogger's AI draft). Cells on the 13 test essays: H essays, D drafts, P B14's pipeline on the draft, N pool writer from the notes only; Pangram on all four | H 13 Human. D 8 Human, 5 Mixed, 0 AI, so the stop rule held P and N back (generated from seed 0 for local checks only). D copies 11 to 64% of its words from the essay in 8-word runs, through the notes; see B27 | b25_blog.py, essays.py |
| B26 | 11-05 | Does a local writer trained on essayists, writing from the blogger's reworded notes, read Human and sound like a person? | Pool writer retrained (B17's QLoRA recipe, PC) on 630 essay training pairs, notes to essay, all notes kept; amended before any text: written from B27's reworded notes, Guard and prune over them, 4 seeds, most supported claims; 13 texts scanned, paired with B27 W; cell M (pool writer, same prompts) local only | V 11 Human, 2 Mixed, 0 AI at 82% of essay length, claims 92% (W, Sonnet from the same notes: 1, 11, 1; Fisher p = 0.0002; paired, V wins 10 of 13, never loses). Validation loss 1.19 to 1.03. M (pool writer) pending | b26_voice.py, essaypool.py |
| B27 | 11-05 | Did the notes' wording, not their content, make B25's AI posts read Human? | B25's notes reworded with B5's prompt (notes copying 40% to 8%, posts 37% to 7%); Sonnet rewrites each post from them (cell W); 13 scanned | 1 Human, 11 Mixed, 1 AI against D's 8, 5, 0 (Fisher p = 0.011). Human content in Sonnet's prose reads Mixed; the wording carried D. The one Human W is a post of quoted puns (51% copied) | b27_reworded.py |
| B28 | 11-05 | How sparse can a blogger's notes be, and what can a humanizer do with only the AI post? | 20 fresh essays (bench2, never in training); notes reworded; doses 100, 50, 25% (nested); S = Sonnet post from the dose notes, L = voice writer from the same notes (Guard, prune, 2 seeds), R = voice writer from the reworded facts of the S100 post (prune against that post), H = essays; all 140 scanned | 19 essays (one Hanson essay dropped: Sonnet refused its notes). H 19 Human. Sonnet from 100, 50, 25% of the notes: 1/18/0, 0/6/13, 0/1/18 (Human/Mixed/AI). L and R overnight | b28_dose.py |
| B29 | 11-05 | Does imitating one writer make the post read Human and sound like that writer? | Henry's question. Sonnet with three of the writer's own posts (unnamed) writes from B27's reworded notes "in my voice" (cell Y); authorship classifier (character n-grams, 660 training essays) | Y 3 Human, 8 Mixed, 1 AI on 12 (W 1, 10, 1; V 10, 2, 0); one recited Sutton essay excluded by amendment. Right writer: H 85%, W 38%, Y 46%, V 69% | b29_mimic.py |
| B21 | 11-05 | Does a real author's own material carry his post to Human? | Henry answers 21 editor questions (3 per section, B19's prompt) about his context-engineering post on a private page; cell F = B15's pipeline plus the facts of his answers; cell A = his answers as written; all 7 sections of each scanned | Not run: Henry wrote the post months ago and cannot recall the specifics the questions ask for. Finding: the interview route needs the author at drafting time, or the author's own records (repo, eval results, notes) in place of memory. Henry's objection, recorded: the questions are AI-chosen, so part of the plan stays AI's; B9 (Sonnet chose which human facts to extract, 10 of 10 Human) suggests AI selection over human material does not by itself read AI, but this is untested | b21_author.py, b21_questions.json |
| B22 | 11-05 | Can the author's project records stand in for an interview? | Proposed: facts from the design docs of the project the post describes, as the human-sourced share | Not run: the project is client work, so Henry chose to keep its records out of third-party tools | none |
| Blind read | 11-05 | Does the pipeline's prose hold up for a human reader? | 6 triads (human original, B14 B, B18 W on a0610 to a0615) and 2 controls (B12 K against the human original); Henry picks the best read and labels each text person or machine; titles, bylines and scraping debris removed from all texts | Published (https://claude.ai/artifact/BYd8PmoSMAKfcLhs7qMpGP); waiting for Henry | blind_read.py, blind_key.json |
| B10 | 11-05 | Does compression fall in Pangram's blind spot? | Sonnet condenses each AI draft to 25% and 50%, adding nothing and with no instruction to sound human; 10 drafts | 20 of 20 AI: an instruct-model writer is caught whatever the compression | b10_compress.json |
| B9 | 11-05 | How much human-sourced content is needed? | Dose-response: 0, 1/3, 2/3 and 1 human-sourced facts at a fixed count, all on the PC | Human 0, 1, 7, 10 of 10; AI 7, 1, 0, 0; Spearman 0.86, p = 2e-12; threshold between 1/3 and 2/3 | b9_dose.json |

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
| B9 | 40 | about 330 |
| B12 | 40 | about 220 |
| B13 | 20 | about 70 |
| B14 | 20 | 87 |
| B8 | 20 | 94 |
| B15 | 14 | 70 |
| B18 | 6 | 23 |
| B20 | 4 | 21 |
| B16 | 20 | 91 |
| B17 | 7 | 22 |
| Remaining on the Individual plan after B17 | | 492 (dashboard) |
| B24 | 10 | 77 |
| Remaining after B24 | | 415 |
| B25 (H and D) | 26 | 229 |
| B27 | 13 | 111 |
| Remaining after B27 | | 75 |
| Plan upgraded to Professional (about 18:15) | | 15,000 |
| B28 (H and S) | 76 | 677 |
| B26 V | 13 | 97 |
| B29 Y | 13 | 108 |
| Remaining | | 14,118 |

## Current hypothesis

Pangram 4 labels an instruct model's content plan for a topic as AI, because that is how it builds its training labels (synthetic mirrors). Its training data contains no base-model text and no LLM output shorter than its input. A full humanizer must therefore replace the AI draft's plan, using one of three sources:

1. The base model's own plan: B7, B8, and HALO's 90% copy rate.
2. Human-sourced content: B9, and retrieval of human sources for the draft's claims.
3. Compression of a large source into a shorter text: the red team's one admitted hole. B10 shows it does not work with an instruct-model writer.

At every step the claim check and the Guard keep the output from inventing facts.
