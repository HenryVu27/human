# Long-form program claims ledger (B32 to B39)

Every claim the long-form program starts from or relies on, with its source, how it was checked and its status.
Henry's rule: treat every prior finding as a claim to test, as ready to refute as to confirm. Status is **verified**,
**refuted**, **partly true** or **unverified**. "Me" means the long-form head session read the raw file or primary
source itself; "agent" means a research agent did (raw reports in this folder: `longform-pangram-length.md`,
`longform-open-detectors.md`, `longform-base-models.md`; the calibration set's build report is summarized in
claim 9). Recomputations use the raw verdict files in `results/`, not the reports' tables.

Opened 2026-11-06 02:09 CST; last updated: see git log.

## Claims from the brief

### 1. Content source is the signal (B5, B9)

- **Claim:** posts written from human-sourced facts read Human 17 of 20, from AI-sourced facts 1 of 20 (B5); the
  human share needed lies between a third and two thirds (B9).
- **Checked (me, raw files):** `results/b5_matched.json` per-text verdicts: cell D (human facts, verbatim) 10 Human;
  E (human facts, reworded) 7 Human, 3 Mixed; A (AI facts, verbatim) 1 Human, 3 Mixed, 6 AI; C (AI facts, reworded)
  0 Human, 3 Mixed, 7 AI. So 17 of 20 against 1 of 20, as recorded. `results/b9_dose.json`: Human 0, 1, 7, 10 of 10 at
  0, 1/3, 2/3 and all human facts. The calibration agent matched all 70 report table cells, these included, to the
  scanned files (claim 9).
- **Limits found:** texts of 300 to 1,300 words, one writer (OLMo-2-13B LoRA), FineWeb explainer pages, 10 topics in
  B5, single seed. B27 and B28 show the prose also carries signal: human content written up by Sonnet reads Mixed
  (B27 W 1 Human, 11 Mixed, 1 AI; B28 S100 1, 18, 0), so content source is not the only signal.
- **Status:** **verified as recorded**; "the" signal is **partly true** (content and the writer's prose both
  matter); at 1,500 to 3,000 words **unverified**.

### 2. The B14 pipeline: 13 Human, 7 Mixed, 0 AI on 20 drafts, about 40% of the length, 86% of claims supported

- **Checked (me):** `results/b14_bestof.json`: 13 / 7 / 0, mean 408 words, claim support 0.857. The 20 drafts
  (a0610 to a0629 in `data/drafts/dev.jsonl`) average 1,078 words, so the output is 38% of the draft.
- **Status:** **verified.** Caveats: 20 drafts, one seed per draft, the claim check is a Sonnet judge (not
  independently audited), and it is a condensation, not a full-length post.

### 3. B28 and B30

- **B28 (me):** `results/b28_dose.json` holds only the H and S cells (H 19 Human; S100 1 / 18 / 0, S50 0 / 6 / 13,
  S25 0 / 1 / 18), which match the report. The L and R cells come later from the PC.
- **B30 (main session's message at 02:40 and report section 35; me, recomputed from `results/b30_rewriter.json` and
  `results/b28_dose.json` at 02:45):** the rewriter (OLMo-2-13B QLoRA on 630 Sonnet-post-to-essay pairs) reads T100
  19 / 0 / 0, T50 13 / 6 / 0, T25 3 / 15 / 1 on the 19 bench2 essays; paired against S100, S50 and S25 it reads more
  human on 51 of 57 pairs, less on none, the same on 6. Outputs about 640 words, 77 to 82% of target length; copying
  from the input post 9%, 13%, 23%. One T25 text is 33 words.
- **Status:** **verified as recorded** (and confirmed by the main session's outside judge, notebook commit de73e9d;
  under B25's 150-word rule T25 has 2 Human). The
  generalization the program needs is **unverified**: every bench author has about 60 essays in the training pairs
  (held-out essays, seen authors), and the outputs are a third of a long post's length. These two gaps define B36.

### 4. B31: raw base continuations read not Human 12 to 43% whatever the vintage; the opening matters more than the model; post-training is the large effect

- **Checked (me, `results/b31_verdicts.json`, 649 main-scan rows):** across the 19 main base arms the per-arm
  not-Human rate runs 12% (gemma3-12b) to 43% (olmo3-7b); per-opening not-Human rates across base arms run 0% to 70%
  on the 30 openings (the report's 74% counts arms differently; same conclusion). Instruct arms 15 of 15 AI each; the
  human arm 30 of 30 Human. An outside judge had already recomputed every B31 statistic
  (`b31-outside-judge.md`).
- **Limits:** continuations of 150 to 250 words, under one Pangram window; one decoding setting; 30 openings.
- **Status:** **verified at 150 to 250 words**; at length **unverified**. The agent's inference (claim 6c below)
  predicts that a writer whose texts are flagged on a fifth of short samples will read Mixed at length, because
  Human needs 90% of characters labelled Human. B34 tests this.

### 5. HALO: raw OLMo-2-32B continuations read 0.03 AI against 0.27 for 7B; B31 found no size trend. Which holds, and at what length?

- **Checked (agent, HALO arXiv 2609.31876 Table 6 and Appendix A; me, the B31 file):**
  - HALO's numbers are exact: Llama-3-8B 0.282, Qwen3-8B 0.417, OLMo-2-7B 0.267, Gemma-3-12B 0.167, Gemma-3-27B 0.085,
    OLMo-2-32B 0.033 (n = 30 each). Median continuation 230 to 254 words; four samples per prompt, the first of 50 or
    more words scored; prompts written by HALO's Claude agent in mixed genres; Pangram 4.0 by date.
  - Agent's tests on HALO's table: Spearman on log parameters over 6 models -0.81 (p 0.05); OLMo-2 7B against 32B,
    8 of 30 against 1 of 30 flagged, Fisher p 0.026; Gemma-3 12B against 27B, 5 against 3, p 0.71.
  - B31 (me, recomputed with tie-aware ranks from `results/b31_model_level.json`): Spearman of opening-adjusted AI
    share on log parameters -0.30, p 0.21, 19 arms from 2.8B to 24B, most at 7 to 9B.
  - PASTA (agent, v3 Figure 6 read from SVG): Qwen2.5 base at 3B, 7B, 14B, base fraction AI at most about 0.19, 0.30,
    0.18, no trend; no base rows for 0.5B, 1.5B or 32B. Xu et al.: raw base test at 8B only.
- **Status:** **partly true for both, not in conflict.** The size effect is supported only between 27 to 32B and
  7 to 12B, at about 250 words, on AI-written prompts, n = 30 per model. Between 3B and 24B no source shows a trend.
  B31 tested no 27B or larger model. No source measures size above about 850 words. A larger writer must therefore
  be chosen, if at all, by the pre-registered development rule (design doc section 5), not by this claim.

### 6. How Pangram aggregates long documents, and whether length by itself moves the verdict

- **6a. Windows and aggregation. Verified** (agent read the Pangram 4 Technical Report arXiv 2607.27183, sections
  4.1, 4.3.2 to 4.3.4 and 5.1, and the 4.0 model card; me, the same sections on 2026-11-06): windows of at most 512
  tokens with stride 256, logits averaged over every window containing a token, a calibrated three-state conditional
  random field (CRF) labels tokens, sentences take their tokens' majority label, short runs merge into neighbours.
  Document fractions are plain character shares per class. Label: Human if fraction_human >= 0.90, AI if
  fraction_ai >= 0.80, otherwise Mixed.
- **6b. "f_AI = 0.5 x AI-Assisted + AI-Generated" (earlier agent, `r2-primary-sources.md`). Refuted** as a
  description of the reported AI share: it is the training target of the segment head (section 4.1). The reported
  fraction_ai is the share of characters labelled AI-Generated; AI-Assisted characters count toward neither Human
  nor AI, so they push a document toward Mixed.
- **6c. Does length move the verdict? Unverified; no primary source covers it.** Pangram's own accuracy-by-length
  figure (section 5.4, Figure 4) stops at 499 words (false negatives 1.29% at 50 to 99 words to 0.19% at 300 to 499;
  false positives 0.020% to 0.0041%). The only long-document result is 39 of 39 fully-AI papers over 4,000 words
  flagged (Table 20). Third-party evidence on long human text exists only for pre-4.0 versions (books, theses).
  The report's limitations section says a section scored alone "may receive a different prediction" than in full
  context. Inference to test (B34): at length the label tracks the per-window flagged share, so texts flagged on
  10% or more of their windows should read Mixed even when most short samples read Human.
- **6d. Credits: about 1 credit per 100 words. Verified:** the dashboard charges one credit per started 100 words
  per scan (knowledge hub page, agent); me: the sum of ceil(words / 100) over B31's 675 texts is 1,987 against
  1,986 charged. A 1,500 to 4,000-word post costs 15 to 40 credits.
- **6e. Maximum length:** 18,725 words per dashboard scan (agent, knowledge hub, V); no truncation described in the
  report. API per-text maximum not stated.

## Claims the program relies on (new)

### 7. Open detectors can stand in for Pangram during development

- **Source:** the brief's design (develop against Binoculars, Fast-DetectGPT and similar; Pangram held out).
- **Checked (agent, `longform-open-detectors.md`):** no paper reports an open detector against Pangram 4 per
  document. Open Pangram (Pangram's own small model) agrees with Pangram 3.3 at kappa 0.61 (Pew); Binoculars' and
  open Pangram's hits correlate only at phi 0.27 on RAID (Visokay et al.). Binoculars and Fast-DetectGPT flag 64 to
  92% of sampled base-model text on RAID, where Pangram flags about 9% of base outputs (PASTA). On 2026 generators
  at 1% false-positive rate, zero-shot methods recall 0.6 to 17% (MELD paper), supervised MELD 99.7%.
- **B33 (me, recomputed by an outside judge, `longform-judge-b33.md`):** on the project's 1,193 unique
  Pangram-labelled texts, AUROC for Pangram's not-Human verdict: Binoculars 0.39 (0.33 to 0.46), Fast-DetectGPT 0.41
  (Falcon pair) and 0.42 (Llama 3.1 8B), desklib 0.48, the pre-registered panel 0.41, MELD 0.63 (0.59 to 0.68). Inside
  the project's own writer outputs the zero-shot detectors and desklib run against Pangram (within-experiment AUROC
  about 0.33 to 0.35); MELD agrees in every origin and length stratum (local writer 0.67, instruct 0.94, above 800
  words 0.83). Every detector separates human text from base-model text almost perfectly (0.96 to 1.00) while
  Pangram calls 72% of the base texts Human. Spearman with Pangram's AI share 0.06 to 0.30.
- **Status:** **refuted for Binoculars, Fast-DetectGPT, desklib and the panel; partly true for MELD** (right
  direction everywhere, weak inside base and writer text). They measure machine-likeness under a language model;
  Pangram measures something closer to assistant-likeness. The design now uses MELD alone as the development
  detector, behind the local checks.

### 8. Binoculars and Fast-DetectGPT are two detectors

- **Checked (agent and me, both code bases):** on the same model pair both are functions of the same per-token
  quantities (observer probabilities, performer log-probabilities): one forward pass yields both; on B33's texts
  their scores correlate at Spearman 0.92. **Refuted as independent mechanisms** on a shared pair. B33 therefore runs Fast-DetectGPT a second time on a different model
  (Llama 3.1 8B, white-box) and counts the Falcon-pair version as a dependent check.

### 9. The project has about 2,000 Pangram-labelled texts for calibration (brief)

- **Checked (separate agent, raw files and the uploaded .docx and .txt files still in the scratchpads):** 1,201
  verdicts B1 to B31, all joined to the exact scanned text, 1,200 exact and 1 probable (B1's pasted Qwen text);
  1,196 match the uploaded file byte for byte after whitespace trimming; label counts match all 70 report table
  cells and 67 summary-file cells; 15 of 15 random rows confirmed. 8 identical texts were scanned twice (equal
  verdicts). AI share is recorded only for B1 and B31 (680 rows). Origins: base 619, local writer 347, instruct 165,
  human 62, edited human 7, recited human 1.
- **Status:** **refuted as a count** (about 1,200, not 2,000), **verified as a joined set**. Gap: only 62 human texts
  and none over 1,922 words, so long-document behaviour must come from the B32 corpus (no Pangram labels) and B34.

### 10. vLLM can carry the Guard to long-context generation

- **Checked (agent, vLLM 0.32.0 docs and code):** custom per-request logits processors exist in the V1 engine
  (subclass `LogitsProcessor`, per-request state through `SamplingParams.extra_args`), registered at load;
  `bad_words` and `allowed_token_ids` cannot express "not in this input". vLLM 0.32.0 runs Olmo 3 through the
  Transformers backend, not native code.
- **Status:** **unverified in practice** (the sketch was not run). Phase 2's first generation job must include a
  unit test of the processor against `src/humanizer/pipeline/guard.py` on the same prompts.

### 11. Long-context base candidates (brief list)

- **Checked (agent, Hugging Face API, configs, model cards, Olmo 3 report Table 12):** Olmo 3 7B and 32B base
  (65,536 tokens, Apache-2.0, open data Dolma 3 with `cc_dump` per row, cutoff December 2024); Gemma 3 27B pt
  (131,072, gated); Llama 3.1 8B (131,072, gated; on the Volume already); Mistral-Small-24B-Base-2501 is only 32,768
  tokens, the 3.1 base (2503) has 131,072; Qwen3.5 base only up to 9B dense (262,144). New, not in the brief:
  google/gemma-4-31B base (Apache-2.0, ungated, 262,144), swiss-ai/Apertus-v1.5-8B-base (gated, public data).
  Olmo 3 mid-training contains 8% thinking and 6% instruction data, so "open data" does not mean "no assistant
  prose".
- **Status:** **verified with corrections** (Mistral Small 2501 is not long-context). My spot check: Llama 3.1 8B is
  on the Volume at `models/meta-llama/Llama-3.1-8B/main`.

## Findings from phase 1 runs

### 12. The B32 pilot corpus is split by site without leakage, and its posts predate ChatGPT

- **Source:** `experiments/modal/lf_corpus.py` (rules committed in 63e43ab), `results/b32_pilot_summary.json`.
- **Checked (outside judge, `longform-judge-b32.md`; me, `experiments/b32_datecheck.py`):**
  - Split: recomputed site keys and hashes for all 15,132 posts, 0 mismatches, no site in two splits. **Verified.**
  - Leakage the key misses: at least 10 of 2,997 dev and test posts share an owner with a post in another split
    (wordpress.com or substack against an own domain, country endings), and one test site (broeder10.blog) is an
    earlier-corpus blog under a new domain. **Refuted as "no author leakage"**; fixes listed in design doc 5.1.
  - Dates: all captures before 2022-11-30 (latest 2022-08-20). Judge: 10 of 10 confirmed in the Common Crawl index and
    WARC records, 8 of 10 with an independent earlier Wayback capture. Me: 18 of 18 index answers match FineWeb's
    timestamp, the text is in 17 of 17 archived pages fetched, 29 of 29 have a Wayback capture before the cutoff
    (20 earlier than Common Crawl's), and 22 of 22 URL dates precede the capture. **Verified.** But a pre-2022 date
    does not prove human authorship: the judge found spun spam and an auto-generated transcript page.
  - Genre tags: `tech` 12 of 20 real technical posts, `personal` 13 of 20 real personal posts; 18.5% of URLs look
    like listing pages. **Refuted as a clean genre filter**; a model-based page-type label is required before the
    full build.

### 13. The open detectors do not flag long human posts

- **Checked (me, B33; outside judge recomputed):** at shipped thresholds, Binoculars 0 of 400 and MELD 0 of 400 long
  pre-2022 posts flagged; desklib 48 of 400 (12%). MELD's score rises with length on human posts (Spearman 0.33) but
  its maximum (3.29) stays under its threshold (3.92, the strictest genre's 1% offset; the pooled offset is 1.65).
  Thresholds set on long posts do not carry to short texts (MELD flags 16% of the 62 short human texts at the
  long-post 5% threshold).
- **Status:** **verified** for these 400; MELD's human training data is undocumented, so overlap with FineWeb (which
  would flatter it) is **unverified**.

### 14. The final test can separate a rewriter from the AI post, not rewriter variants from each other

- **Checked (me, `experiments/lf_power.py`, `results/b39_power.json`):** with B30-informed rates, a 10-point gap
  between conditions has 0.13 to 0.29 power on the AI share at n = 40 and 0.20 to 0.48 at n = 64; the label has
  0.05 to 0.09. A rewriter against the AI post has power 1.00 on the share and 0.74 to 1.00 on the label at n = 40.
- **Status:** **a modelling result, not data**; its spread and correlation are assumptions until B34 and B36 measure
  AI shares at length.

## Gate 1 results (2026-11-06, B34 and B36)

### 15. B30's rewriter transfers to writers it never saw and to whole posts (the open question of claim 3)

- **Checked (B36, 32 test-A posts; statistics recomputed by an outside judge; red team):** Cfull reads Human on 1 of
  32 (Mixed 31), against Sonnet's posts 0 of 32 (AI 19); the AI share falls on all 32 (0.81 to 0.38). The first 300
  words of the same rewrites read Human on 11 of 32.
- **Status:** **refuted at full length** (pre-registered band "does not transfer"). The direction is verified (every
  post moves toward Human). Unseen authors and length cannot be separated from genre (obscure bloggers against famous
  essayists) and from section-by-section rewriting.

### 6c, updated. Length by itself moves the verdict

- **Checked (B34, B36):** human posts read Human at 300 words and at 1,800 to 3,000 words, 10 of 10 each (AI share
  0.00); rewrites read Human 11 of 32 as 300-word prefixes and 1 of 32 in full (McNemar p 0.006; 9 against 1 without
  the two faithless texts).
- **Status:** **verified in direction for partly AI text, refuted for human text**: length does not make human posts
  read AI, but it turns partly AI text from Human to Mixed, consistent with the 90% character rule (a per-window Human
  rate of 0.34 predicts 1.7 of 32 whole posts; observed 1). The significance is fragile.

### 16. The claim check catches invented content in long rewrites

- **Checked (copying and faithfulness audit):** it passed a section with about 40 lines of invented code and one with
  three paragraphs of garbled French, and missed framing such as "This is the second of three articles" in 12 of 52
  later sections.
- **Status:** **refuted** for long, section-by-section rewrites. Language, code and format checks must be added to the
  pick step before gate 2.

## Gate 2a results (2026-11-06, B37)

### 17. Pangram labels a long document by the share of words it flags, so whole posts need under 10% flagged

- **Checked (B37 splice probe, 20 texts; Henry's four whole-post scans):** a Sonnet block of 6.8%, 9.5% or 17% of a
  human post's words gives an AI share of 0.06 to 0.07, 0.08 to 0.09 and 0.15 to 0.17 at the start, middle or end, and
  the labels Human, Human, Mixed. Whole-post shares equal the word-weighted mean of the section shares within 0.06.
- **Status:** **verified for contiguous blocks** (2 bases, one Sonnet block). Scattered or partly edited AI sentences
  are untested. This replaces the per-window model of the B36 red team: a post with Mixed sections can still read
  Human if under 10% of its words are flagged.

### 18. MELD can serve as the development judge for the rewriter

- **Checked (B37 validators):** on B36's 300-word rewrites, MELD separates Pangram's Human from not-Human at AUROC 0.55
  and calls 1 of 32 human-like where Pangram calls 11.
- **Status:** **refuted for rewriter output.** MELD agreed with Pangram across strata in B33 but cannot rank rewrites.
  Gate 2b needs a judge that works within rewrites before it can be developed without Pangram.

### 19. A copy-penalized pick or the notes-first writer at full length closes the gap cheaply

- **Checked (B37):** C1 cut copying from 32% to 20% with no change on MELD (0.066 against 0.067); on Henry's
  context-engineering post it changed 4 of 7 sections and all 4 fell on Pangram (whole post 0.40 to 0.24). L read far
  more human to MELD but kept 28% of the post and 89% claim support.
- **Status:** **not shown** on the development judge; **suggestive** on one Pangram-scanned post (selection has
  headroom). Henry's bandits rewrite reads Human at full length (0.08), near the line.

## B38 results (2026-11-06)

### 18, updated. MELD can serve as the development judge for the rewriter

- **Checked (B38 statistics audit):** the 0.55 of B37 was B36's 300-word rewrites only. On all 561 Pangram-labelled
  rewrites the raw MELD score reaches AUROC 0.6995 (0.646 within experiment and cell; 0.578 on B36 and B37's rewrites),
  and as a best-of-4 picker on B38's 14 calibration sections it matches the trained J1 (0.213 against 0.215; among
  gate-passing tries 0.261 against 0.288).
- **Status:** **partly true.** Weak across new rewriters, but no trained judge does better yet.

### 20. A judge trained on Pangram's labels tracks Pangram on rewrites (AUROC at least 0.70)

- **Checked (B38, registered; recomputed by an outside judge):** J1 out-of-fold rewrite AUROC 0.735 (group bootstrap
  0.686 to 0.782, 7.8% of resamples under 0.70); leave-one-experiment-out 0.62. A score that sees only each row's
  experiment and cell reaches 0.78, and within experiment and cell J1 is 0.669.
- **Status:** **partly true.** True as registered, but the pooled number mostly separates experiments; the newer the
  rewriter, the weaker the judge (B36 0.66, B37 0.57 held out).

### 21. Best-of-n with a local judge moves rewrites toward Human on Pangram

- **Checked (B38, 14 held-out sections, 55 scanned tries):** ungated, J1's pick averages 0.215 against random 0.337
  (gain 0.122, 95% interval 0.05 to 0.20). But 8 of 14 picks fail the content gates and keep 60% of the words. Among
  gate-passing tries J1 0.288, C1 (least copying) 0.291, raw MELD 0.261, random 0.340, oracle 0.213. Whole posts
  (derived): the oracle leaves 3 of 4 above 0.10.
- **Status:** **refuted as a lever at k = 4 with the content rules kept.** Selection has some headroom (oracle 0.213
  against random 0.340) that no judge yet captures better than C1, and none reaches the line.

### 22. Copying from the AI draft is what Pangram still flags in rewrites

- **Checked (B38 post hoc, and B37's earlier note):** share copied from the input in 8-word runs correlates 0.70 with
  Pangram's share across 55 tries and separates Human at AUROC 0.74 on B36's 64 rewrites (J1 0.67). Not held out: B37
  had already proposed it.
- **Status:** **suggestive, consistent across B36, B37 and B38.** A test would fix a copy limit before generation and
  scan fresh posts.

### 23. Math in a post raises Pangram's AI share

- **Checked (B38 step 6, same batch):** Henry's bandits post with LaTeX kept reads Mixed 0.41 (Pangram counts 5,030
  words for our 3,851); stripped, Mixed 0.24, equal to B37's scan of the stripped text earlier the same day.
- **Status:** **verified on one post.** The gap between B36's 0.41 (math kept) and B37's 0.24 (stripped) was the math,
  not scan noise. Compare like with like (math handled the same way) in every Henry-arm test.
