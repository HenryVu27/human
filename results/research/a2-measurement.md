# Attempt 2 measurement design: quality, faithfulness, detector statistics, drift and reader panels

Research agent report, 2026-11-06. Raw report for the session that plans attempt 2 of the humanizer project.

Tags: [primary, verified] means I read the number in the primary source (paper HTML, model card, pricing page) in
this session. [primary, unverified] means the source is primary but I saw only an abstract, a search snippet or my own
prior knowledge of it. [secondary] means a blog, aggregator or summary. "Finding" marks something new computed here
from the project's raw files, with the file it came from.

Brief given to the agent (abridged): design-grade research on how to measure attempt 2's outcomes (writing quality
better than the draft without a biased large language model (LLM) judge; faithfulness that catches additions; Pangram
4.x verdict statistics with sample sizes; detector drift; reader panels), with sample-size arithmetic, costs in
Pangram credits and Henry's reading time. Work at expert depth, start from raw data, verify with an external check,
report what could not be verified.

Scripts for every number below are in the session scratchpad
(`/private/tmp/claude-501/-Users-henryvu--claude-spares-spare-s6HQlu/cbf959c7-1fb4-4dcb-918e-c248455f5f2d/scratchpad/a2m/`:
`emp.py`, `power.py`, `power2.py`, `power3.py`, `power4.py`), run with the project's `.venv` Python (SciPy 1.18.1,
NumPy 2.5.4). They are temporary; the numbers that matter are restated here.

External checks on my own arithmetic: the Simon two-stage code reproduces Simon's (1989) published designs exactly
(p0 0.1 against p1 0.3: optimal 1/10 then 5/29, minimax 1/15 then 5/25; p0 0.2 against 0.4: optimal 3/13 then 12/43,
minimax 4/18 then 10/33). The exact McNemar power at n = 50 (0.80) matches a 20,000-run Monte Carlo (0.803). The
O'Brien-Fleming two-look bounds match the textbook values (z 2.797 and 1.977).

## Bottom line

1. **Pangram is close to deterministic within a model version (finding).** Eight texts that were scanned twice on
   2026-11-06, in batches up to three hours apart, came back with the same label 8 of 8 times and AI shares within
   0.00 to 0.02. Across days (2026-11-05 against 11-06), Henry's 7 context-engineering sections kept 6 of 7 labels;
   the one change sat at the AI boundary (AI, then Mixed at 0.78). Scan noise is negligible next to
   generation-to-generation noise. The real drift risk is a model version change (4.0 on 2026-07-29, 4.1 on
   2026-10-19), which the anchors below detect.
2. **Use the continuous AI share for development decisions and the Human rate only for the final test.** With
   attempt-1 data (B36, 32 full posts), the paired standard deviation (SD) of share differences is 0.12, so a drop
   from 0.38 to 0.20 needs about 6 to 8 posts at 80% power (12 for margin). The same decision on the binary Human
   rate (3% against 30%) needs 28 to 33 posts, and 30% against 60% needs 25 to 50 posts depending on how correlated
   the two arms are.
3. **"At least 50% Human" is expensive to prove.** A one-sided 95% Clopper-Pearson (exact binomial) lower bound
   above 0.50 needs 18 posts if the true rate is 0.80, 37 if 0.70 and 158 if 0.60. On a 50-post final set the rule
   is "at least 32 of 50 Human" (86% power if the true rate is 0.70, 34% if 0.60).
4. **Count posts, not sections.** In B38, 75% of the variance of section shares was try-to-try (resampling), 25%
   post, and about 0% section within post. The intraclass correlation (ICC) of about 0.25 gives a design effect of
   1.75 for 4 sections per post. Analyse with the post as the unit (or a cluster bootstrap by post).
5. **No LLM judge can measure "better than the draft" for this project.** Zero-shot LLMs score at or below chance on
   an expert writing-quality benchmark (GPT-4o 40.9%, o1 51.7%, DeepSeek-R1 46.0%), LLMs prefer LLM text over human
   text across families (the "AI-AI bias", PNAS 2025), and this project's own judge preferred Sonnet 20 of 20. A
   panel from other model families reduces self-preference, but not the shared preference for AI style, which is
   exactly the thing attempt 2 removes. Use LLMs only for defect checks (broken sentences, garbled math, loops).
6. **The minimum credible quality measure is Henry's blind, side-by-side read of section pairs (draft against
   output) on posts he did not write, with order randomised, decoys and repeats.** 40 pairs (about 3.5 hours) supports
   a non-inferiority claim (output not clearly worse than the draft: at least 20 of 40 wins rules out a win rate of
   0.35 or less) with 93% power if the true win rate is 0.60, but only 56% if it is 0.50. Proving superiority needs a
   true win rate of 0.70 or more (37 pairs). One paid second rater (about $60 to $100, Henry's decision) on 20 of the
   pairs would give an agreement statistic; without one, the quality claim rests on one rater and should say so.
7. **Faithfulness checkers top out near 75% to 80% balanced accuracy on human-labelled benchmarks** (LLM-AggreFact:
   Bespoke-MiniCheck-7B 77.4, Claude 3.5 Sonnet 77.2, GPT-4o 75.9, MiniCheck-Flan-T5-Large 75.0; hardest sets near
   55% to 62%). Additions need a directional, sentence-aligned check plus deterministic checks for specifics and code.
   The checker must be audited with planted errors: 30 planted errors per type with 0 misses gives a 95% lower bound
   on recall of 0.90; this costs Claude calls and no Pangram credits.
8. **A reader panel cannot show "indistinguishable" on this budget, but it can show "less detectable than the
   draft".** Proving accuracy of at most 60% needs about 158 single-reader judgments (true accuracy 0.50) or 10
   readers by 100 items. Showing that a reader flags outputs less often than drafts (93% to 60%) needs 1 reader by
   30 items (84% power) or 3 readers by 15 items (95%). Only readers who use LLMs heavily for writing are informative
   (Russell et al., ACL 2025: experts 92.7% true positive rate, 4.0% false positive rate; non-experts at chance).
9. **Recommended total: about 3,200 to 4,100 Pangram credits of the 8,717 (5,400 with an optional rescan of
   attempt 1's rewriter), and 6.5 to 8 hours of Henry's reading,**
   with no money spent unless Henry approves a second rater (section "Implications for attempt 2").

## 0. What exists in the repo, and what attempt 1's raw data say

### 0.1 Existing checks (read in `src/humanizer/checks/`)

- `claims.py`: a deterministic check that every number, quotation and multi-word capitalised name in the output
  appears in the draft (code blocks and headings excluded), plus one Sonnet call that lists the output's claims and
  marks each supported or not. Pass: no unsupported specifics and at least 95% of claims supported. The Sonnet call
  sees the whole draft and the whole output at once; there is no chunking, no sentence alignment and no audit of its
  recall.
- `quality.py`: Sonnet picks A or B in both orders; returns 1, 0.5 or 0. Known to prefer Sonnet's prose 20 of 20
  over human text (`results/judge_calibrate.json`, LABNOTEBOOK "Judge check").
- `form.py`: deterministic checks for non-English runs, new code lines (allows up to 2), new framing, extra headers
  and restart openers. Built after B36's audit found invented code, garbled French and invented framing that the
  Sonnet claim check passed.
- `copying.py`, `repeats.py`: copied 8-word runs and repeats.
- The pending blind read (`results/blind_pairs.json`, 8 items) uses FineWeb triads; item p01's first text contains a
  template loop ("1, 1, 1, ..."), so it also works as a defect probe.

### 0.2 Finding: Pangram test-retest from scans already paid for

Joined `results/b36_blind.json`, `b37_blind.json`, `b38_blind.json` with the matching `*_pangram_records.jsonl`. B36
was scanned at 10:26 to 10:42, B37 at 12:16, B38 at 13:33, all 2026-11-06, Pangram 4.1. Texts with the same input word
count and the same Pangram word count (identical text) or within 3 words (near-identical):

| Text | Scan 1 | Scan 2 | Words (input / Pangram) |
|---|---|---|---|
| HR aieng s7 | Mixed 0.70 (B36) | Mixed 0.70 (B37) | 436 / 452 both |
| HR aieng s5 | Mixed 0.65 (B36) | Mixed 0.65 (B37) | 282 / 299 both |
| HR aieng s1 | Human 0.00 (B36) | Human 0.00 (B37) | 337 / 342 both |
| HO bandits s1 | Mixed 0.66 (B36) | Mixed 0.67 (B37) | 304 / 318 both |
| HO bandits, LaTeX kept | Mixed 0.41 (B36) | Mixed 0.41 (B38) | 3,851 / 5,030 both |
| HO bandits, LaTeX stripped | Mixed 0.24 (B37) | Mixed 0.24 (B38) | 2,663 / 2,722 both |
| HO aieng, whole post | Mixed 0.55 (B36) | Mixed 0.53 (B37) | 4,481 against 4,478 |
| HR bandits s1 | Human 0.00 (B36) | Human 0.00 (B37) | 331 against 328 |

Labels agree 8 of 8; the largest share difference is 0.02, on a text that changed by 3 words. Cross-day: B15
(2026-11-05) labelled the 7 context-engineering sections AI, Mixed, Mixed, Mixed, AI, AI, AI; B37 (11-06) gave AI 1.00,
Mixed 0.39, Mixed 0.18, Mixed 0.72, Mixed 0.78, AI 1.00, AI 0.97. Agreement 6 of 7; section 5 moved from AI to Mixed at
0.78, just under the 0.80 AI threshold. Section texts match to within 2 words (`results/b15_sections.jsonl` against
B37 word counts), but B15 shares were not saved and its upload route may have differed, so this pair is weaker
evidence. B14 also reported identical verdicts on 7 of 7 rescans (LABNOTEBOOK row B14).

### 0.3 Finding: empirical variances for power calculations

From `results/b36_*` (32 test-A posts by writers the rewriter never saw):

- Full posts: drafts (D) mean AI share 0.813, SD 0.109; B30 rewrites (C) mean 0.376, SD 0.145. Paired difference
  C minus D: mean -0.437, SD 0.119; correlation 0.59. Labels: C 31 Mixed and 1 Human; D 19 AI and 13 Mixed.
- First 300 words: C mean 0.292, SD 0.282; paired difference SD 0.316; correlation 0.09. Short texts are about
  twice as noisy as whole posts, which is another reason to score whole posts.
- Human originals at full length: 10 of 10 Human, share 0.00.

From `results/b38_*` (cell K: 4 test-A posts, 4 tries, 4 sections, 54 scans of at least 150 words), a nested
method-of-moments variance decomposition of section shares: try within section 0.058 (75%), section within post about
0 (0%), post 0.019 (25%); total SD 0.28. With 4 posts this is very imprecise; treat ICC 0.25 as a planning value and
plan for 0.4 as a pessimistic case.

## 1. Writing quality without a biased LLM judge

### 1.1 What is known about LLM judges

- **AI-AI bias across families.** Laurito et al., "AI-AI bias: Large language models favor communications generated
  by large language models", PNAS 122(31) e2415697122, July 2025. GPT-3.5, GPT-4 and open-weight models prefer
  LLM-written descriptions of products, papers and films in binary choices; human raters do not show the same
  preference. [primary, unverified for the numbers; a secondary summary gives GPT-4 choosing LLM product text 87% to
  88% and abstracts 77%, humans choosing AI abstracts 60%.]
- **Self-recognition drives self-preference.** Panickssery, Bowman and Feng, NeurIPS 2024 (arXiv 2404.13076): GPT-4
  recognises its own summaries 73.5% of the time out of the box; fine-tuning shows a linear relation between
  self-recognition and self-preference. [primary, unverified beyond the abstract]
- **Familiarity (perplexity) explains self-preference.** Wataoka, Takahashi and Ri, arXiv 2410.21819 (v2 June 2025):
  LLM judges favour low-perplexity text whether or not they wrote it. [primary, unverified] Implication for this
  project: a humanised output is by design less like LLM text, so every LLM judge is pushed toward the draft.
- **Self-preference partly a quality confound.** Chen et al., "Beyond the Surface: Measuring Self-Preference in LLM
  Judgments", arXiv 2506.02592 (June 2025): proposes a self-preference score that uses gold judgments to separate bias from real quality differences.
  [primary, unverified]
- **LLMs cannot judge writing quality zero-shot.** Chakrabarty, Laban and Wu, "AI-Slop to AI-Polish?", COLM 2025
  (arXiv 2504.07532 v3, Aug 2025), Table 2, Writing Quality benchmark (4,729 pairwise judgments from five datasets,
  human-human, human-AI and AI-AI pairs): GPT-4o zero-shot 40.9%, GPT-4o five-shot 54.3%, o1 51.7%, DeepSeek-R1
  46.0%, o3 64.3%, Skywork-Reward-8B 60.5%, Pangram (as a quality proxy) 65.0%, their trained Writing Quality Reward
  Model (WQRM, ModernBERT) 74.3%. Experts agreed with WQRM 66% overall and 72.2% when the reward gap exceeded 1 point;
  individual experts preferred the higher-scored text only 55% of the time when the gap was 0.5 or less. Expert
  evaluation: 9 MFA (Master of Fine Arts) trained writers, 3 per triplet, ranking, $100 per batch of 10 triplets.
  Code, data and models: github.com/salesforce/creativity_eval. [primary, verified]
- **Expert readers penalise detectable AI text; lay readers barely do.** Chakrabarty, Ginsburg and Dhillon, "Readers
  Prefer Outputs of AI Trained on Copyrighted Books over Expert Human Writers", arXiv 2510.13939 (v4, March 2026).
  Blind forced-choice pairs, randomised order, 28 MFA readers (3 per pair) and 516 Prolific general readers (19 to 21
  per pair), 10,920 judgments. Prompted AI: MFA readers disfavoured it for quality (odds ratio 0.13); general readers
  favoured it (1.82). Agreement (Fleiss' kappa): MFA 0.41 to 0.67, general readers 0.08 to 0.26. Each unit of Pangram
  score cut MFA readers' odds of choosing a text (quality beta -2.01). Pangram flagged 97% of prompted outputs and 3%
  of fine-tuned ones (threshold 0.9); human text 0%. Analysis: logistic regression, cluster-robust (CR2) errors by
  reader, Holm correction. Pay: MFA $75 to $100 per 10-comparison batch; Prolific about $15 per hour. [primary,
  verified]
- **Style dominates judges; controlling it helps.** Length-controlled AlpacaEval (Dubois, Galambosi, Liang,
  Hashimoto, COLM 2024, arXiv 2404.04475): regression on length raises Spearman correlation with Chatbot Arena from
  0.94 to 0.98 [primary, verified]. Chatbot Arena style control (LMSYS blog, 2024-08-28): adds length and markdown
  counts to the Bradley-Terry regression; length is the dominant style term [primary, read via search summary only,
  unverified]. A 2026 preprint (arXiv 2604.23178) reports style bias 0.76 to 0.92 across judges on 225 pairs
  [primary, unverified].
- **Panels of judges.** Verga et al., "Replacing Judges with Juries" (Cohere, arXiv 2404.18796, April 2024): three
  small judges from different families (Command R, Claude Haiku, GPT-3.5) correlate better with humans than GPT-4 on
  question answering and reduce intra-model bias. [primary, unverified beyond abstract] Not tested on writing quality.
- **Can AI writing be salvaged?** Chakrabarty, Laban and Wu, CHI 2025 (arXiv 2409.14509): professional writers
  edited 1,057 LLM paragraphs (LAMP, 8,035 edits) and agreed on a seven-category taxonomy of idiosyncrasies
  (cliches, unnecessary exposition, purple prose, and others); GPT-4, Claude 3.5 Sonnet and Llama 3.1 70B did not
  differ in writing quality. [primary, unverified beyond abstract] Useful as a rubric source.

### 1.2 Debiasing methods, judged for this project

| Method | What it fixes | What it cannot fix here |
|---|---|---|
| Both orders (already in `quality.py`) | Position bias | AI-style preference |
| Style control (regress outcome on length difference, copied share, markdown counts) | Length and format confounds | Register and word choice, which are the treatment |
| Rubric scoring of named defects (binary items) | Vague holistic preference | Rubrics for "voice" or "engagement" inherit AI-style preference |
| Panel from different families (Claude, GPT-5, Gemini 2.5) | Self-preference of one family | AI-AI bias is shared across families (Laurito) |
| Reference-anchored judging against same-topic human text | Gives a human anchor | Attempt 1 scored 0.20 to 0.575 against human text; the judge still preferred Sonnet 20/20, so the anchor shows bias rather than removing it |
| Calibrate the judge on Henry's labels | Measures the bias | Needs Henry's labels first; only then can the judge be trusted where it agrees |

Verdict: an LLM judge may serve as a defect screen (a list of yes or no checks: broken or ungrammatical sentence,
garbled equation or proof, repeated or looping text, contradiction with the draft, paragraph that does not follow
from the previous one, invented example) because those are errors rather than taste. It may not serve as the
quality endpoint.

### 1.3 Validated automatic proxies

- WQRM (above): the only open quality model validated against experts on human-versus-AI pairs, 74.3% on its
  benchmark, but trained on literary and creative paragraphs; untested on technical blog posts. Worth running as a
  secondary measure and checking its agreement with Henry's labels before trusting it. [primary, verified]
- Pangram itself scores 65.0% on the same benchmark, so the detector is partly a quality proxy; the outputs being
  optimised against it makes it unusable as an independent quality measure here.
- Readability formulas and perplexity: no validation against expert preference found; do not use as quality.

### 1.4 Human raters: protocols, agreement and cost

- **Protocol (from Chakrabarty et al. 2025/2026 and Russell et al. 2025):** blind forced-choice pairs with left and
  right randomised; a short written reason (2 to 3 sentences) per choice; quality-control exclusion for very fast
  judgments (under 30 seconds); screening of raters on a test set; analysis with logistic regression and errors
  clustered by rater and item.
- **Agreement statistics:** Krippendorff's alpha (handles missing ratings and any number of raters); conventions:
  0.800 or more reliable, 0.667 to 0.800 tentative [secondary: Wikipedia and Krippendorff's bootstrap note,
  asc.upenn.edu]. Fleiss' kappa in published writing studies: experts 0.41 to 0.67, lay readers 0.08 to 0.26
  (Chakrabarty et al.). For one rater, the only reliability available is intra-rater: re-show some pairs in swapped
  order and report agreement.
- **Expert against crowd:** lay Prolific readers agree with each other at kappa about 0.1 and prefer prompted AI
  text, so they cannot detect the improvement attempt 2 is after. Experts (MFA writers, professional editors,
  frequent LLM users) agree far more and track detectability.
- **Prices (no sign-up made):**
  - Prolific: participant minimum $8.00 per hour, recommended at least $12.00; platform fee 42.8% for corporate
    customers, 33.3% for academic or non-profit; no subscription [primary, verified on prolific.com/pricing,
    2026-11-06, no effective date shown]. A 1,000-word pair takes about 5 minutes, so about $1.00 plus fee, about
    $1.45 per judgment at $12 per hour and the corporate fee.
  - Upwork: copy editors $20 to $40 per hour according to Upwork's own cost page as quoted by search results (the
    page returned HTTP 403 to me); client marketplace fee reported as 3% to 5% on the Basic plan plus a contract
    fee of $0.99 to $14.99 [secondary]. Editorial Freelancers Association 2026 medians $35 to $70 per hour
    [secondary].
  - Published rates for comparison: Russell et al. paid $2 per article under 1,000 words (about $15 to $30 per hour,
    $2.82 average with bonuses), $4.9K in all [primary, verified]; Chakrabarty et al. paid MFA readers $75 to $100
    per 10 comparisons [primary, verified].

### 1.5 Minimum credible quality measure for a one-person project

The measure: Henry reads blind pairs of the same section (draft against output), one at a time, side by side, order
randomised, and answers three questions:
1. Which would you rather publish under your name? (forced choice, with strength: slightly or clearly)
2. Is either one unpublishable as is? (a defect flag for each text, with the offending sentence pasted)
3. One line of reason.

Design rules:
- Use posts by other writers (test-A or test-B posts), not Henry's own: he wrote his posts' content and remembers
  their drafts, which breaks blinding.
- Sections of 400 to 700 words keep a pair to about 5 minutes; draw at most 2 sections per post so clustering stays
  small (design effect about 1.25 at ICC 0.25).
- Add controls: 4 repeat pairs in swapped order (intra-rater consistency), 4 pairs of human original against draft
  for the same post (the positive control; the human original should usually win, and the content differs, so these
  are not part of the endpoint), and 2 pairs where both sides are the draft with trivial edits (should split).
- Pre-register the endpoint and margin before Henry reads.

Arithmetic (exact binomial, ties dropped, one-sided alpha 0.05):

| Claim | Pairs | Rule | Power |
|---|---|---|---|
| Output not worse (win rate above 0.35) | 40 | at least 20 wins | 0.56 if true 0.50; 0.93 if 0.60 |
| Output not worse (win rate above 0.40) | 40 | at least 22 wins | 0.32 if true 0.50; 0.79 if 0.60 |
| Output not worse (above 0.35) | 30 | at least 16 wins | 0.43 if true 0.50; 0.82 if 0.60 |
| Output better (above 0.50) | 37 | at least 24 wins | 0.80 if true 0.70 |
| Output better | 23 | at least 16 wins | 0.80 if true 0.75 |
| Output better | 69 | at least 42 wins | 0.80 if true 0.65 |

Precision: 24 wins of 40 gives a 90% Clopper-Pearson interval of 0.46 to 0.73; 20 of 40 gives 0.36 to 0.64.

So with 30 to 40 pairs Henry can show "not clearly worse" if the output really is somewhat better, or "better" if it
is clearly better (win rate 0.70 or more). He cannot show "as good" (true 0.50) at any affordable n: 158 pairs for a
0.40 margin.

Second rater: the same 20 pairs read by one screened editor gives Cohen's kappa or Krippendorff's alpha with a wide
interval (20 binary items cannot pin alpha down), but it answers "is this only Henry's taste". Cost about 2 hours at
$25 to $40 per hour plus fees, $60 to $100: needs Henry's yes under the $100 cap.

## 2. Faithfulness: catching additions in long rewrites

### 2.1 Methods and their measured accuracy

- **MiniCheck** (Tang, Laban, Durrett, EMNLP 2024, arXiv 2404.10774): sentence-level checker trained on synthetic
  data. Balanced accuracy on LLM-AggreFact without threshold tuning: GPT-4 75.3, MiniCheck-Flan-T5 74.7, AlignScore
  70.4, SummaC-ZS 67.9, SummaC-CV 62.1. Long-form sets: ExpertQA about 59 for all three, LFQA 83 to 85, MeetingBank
  73 to 80. Claim decomposition changed averages by -3.3 to +1.2 points (MiniCheck-FT5 -1.4) and raised cost 2 to
  4 times; "claim decomposition is not needed in our settings". Threshold fixed at 0.5. [primary, verified]
- **LLM-AggreFact leaderboard** (llm-aggrefact.github.io, read 2026-11-06, no update date shown): best entries
  79.5 (nimble-v4-max, 27B), Bespoke-MiniCheck-7B 77.4, Claude 3.5 Sonnet 77.2, Granite Guardian 3.3 76.5, GPT-4o
  75.9, FactCG-DeBERTa-L 75.6, MiniCheck-Flan-T5-L 75.0, across 11 human-labelled datasets. [primary, verified]
  Current Claude and GPT-5 models are not listed.
- **FaithBench** (arXiv 2410.13210; NAACL 2025): summaries chosen where detectors disagree; best detectors near 50%
  to 62% balanced accuracy. [primary, unverified beyond abstract]
- **FActScore** (Min et al., EMNLP 2023): decompose into atomic facts, verify each against a knowledge source; the
  aggregate estimate tracked human scores closely, per-fact accuracy less so. [primary, unverified] Decomposition
  choices change scores (Wanner et al., arXiv 2403.11903) and VeriScore drops many informative facts (MedScore,
  arXiv 2505.18452). [primary, unverified]
- **SummaC** (Laban et al., TACL 2022) and **AlignScore** (Zha et al., ACL 2023): sentence-level natural language
  inference (NLI) with chunking and aggregation; 62 to 70 on LLM-AggreFact above. [primary, unverified except the
  numbers in MiniCheck's table]
- **Book-length faithfulness** (FABLES, Kim et al., COLM 2024, arXiv 2404.01261): 3,158 claims from summaries of 26
  books, annotated by readers of the books; claim verification against the whole book is posed as an open
  long-context problem. [primary, unverified beyond abstract]
- **This project:** the Sonnet whole-document check passed 40 lines of invented code, three paragraphs of French and
  invented series framing in B36 (`results/research/longform-judge-b36-copying.md`).

Reading: the best automated checkers make an error on roughly one in four or five labelled claims on mixed
benchmarks, and do worse on the hardest cases. Nothing published measures them on 1,500 to 3,000-word rewrites of
technical blog posts. The project's checker therefore has to be measured on its own task.

### 2.2 How to catch additions, not only contradictions

Additions are "extrinsic" content: true or false, it is not in the draft. Checks by type:

| Addition type | Check | Kind |
|---|---|---|
| Numbers, names, quotes, dates | `claims.unsupported_specifics` (exists); extend to units, version strings, URLs | Deterministic |
| Code | Every non-blank line inside output code blocks must match a draft code line after whitespace normalisation; zero tolerance (form.py now allows 2) | Deterministic |
| Math | Same rule for display and inline math after LaTeX normalisation | Deterministic |
| Framing, sign-offs, series talk | `form.new_framing`, `restart_opening` (exist) | Deterministic |
| Other languages | `form.non_english_runs` (exists) | Deterministic |
| New content words | Share of output content-word lemmas and 3-grams absent from the draft, per sentence; flag sentences above a threshold for the model check | Deterministic screen |
| New claims, examples, anecdotes, causal upgrades, scope changes ("some" to "all"), hedges removed | Sentence-aligned entailment: for each output sentence, retrieve the 3 most similar draft passages (about 200 words each) and ask whether the passage entails the sentence; a sentence passes if any passage entails it (MiniCheck-style max over chunks) | Model |
| Omissions (secondary) | Reverse direction on the draft's key claims, to report how much content was kept | Model |

Run the model check with a model from a family other than the draft's writer where possible, and at sentence level
rather than whole-document, because whole-document checks are where B36's misses happened.

### 2.3 Auditing the checker with planted errors

Design (no Pangram credits; Claude or open-model calls only):
1. Take 30 faithful outputs (outputs that passed every check and Henry's spot read) and their drafts. Use posts not
   used to tune the checker.
2. For each of 10 error types, plant one error per output, programmatically where possible (number change, name
   swap, invented statistic, invented code line, invented example sentence, polarity flip, scope change, causal
   upgrade, invented framing sentence, one foreign-language sentence). Have a different model write the free-text
   insertions so the checker's own family did not produce them. 300 planted cases.
3. Also run the checker on the 30 unmodified outputs and on 30 light paraphrases of the draft itself (should all
   pass): this gives the false-alarm rate.
4. Report recall per type with an exact one-sided 95% lower bound: 20 planted with 0 missed gives at least 0.86; 29
   with 0 missed, 0.90; 30 with 1 missed, 0.85; 59 with 0 missed, 0.95; 60 with 2 missed, 0.90.
5. Henry reads 10 flagged and 10 passed sentences to check the labels themselves (the planted labels are known, but
   natural outputs also contain unplanned additions).

Planted errors are cleaner than natural ones, so audit recall is an upper bound on real recall. Keep a few natural
B36 failures (the French, code and framing cases) in the audit as real-world positives.

## 3. Detector-outcome statistics

### 3.1 Paired binary outcomes (McNemar, exact)

Arms are scanned on the same posts. Power of the exact conditional McNemar test (two-sided alpha 0.05, rejections in
the expected direction only), computed exactly; phi is the correlation between the two arms' Human outcomes, which
sets how many pairs are discordant. p10 is the share of posts Human in the new arm only, p01 Human in the old arm only.

| Old arm | New arm | phi | p10 | p01 | n for 80% | n for 90% |
|---|---|---|---|---|---|---|
| 3% | 30% | 0 (independent) | 0.291 | 0.021 | 33 | 41 |
| 3% | 30% | 0.27 (maximum) | 0.270 | 0.000 | 28 | 33 |
| 30% | 60% | 0 | 0.420 | 0.120 | 50 | 64 |
| 30% | 60% | 0.30 | 0.353 | 0.053 | 36 | 45 |
| 30% | 60% | 0.53 (maximum) | 0.300 | 0.000 | 25 | 29 |
| 10% | 50% | 0 | 0.450 | 0.050 | 25 | 31 |
| 50% | 75% | 0 | 0.375 | 0.125 | 67 | 85 |
| 50% | 75% | 0.30 | 0.310 | 0.060 | 48 | 61 |

For comparison, independent posts per arm with Fisher's exact test (one-sided 0.025) need 33 per arm for 3% against
30% and 48 per arm for 30% against 60%, so pairing saves posts only when arms are positively correlated. In B36 the
draft and rewrite shares correlated 0.59, so the phi 0.3 rows are a reasonable planning case.

### 3.2 Proportion thresholds ("at least 50% Human")

One-sided 95% Clopper-Pearson lower bound above the threshold, exact:

| Threshold | True rate | n for 80% power | Human needed |
|---|---|---|---|
| 0.50 | 0.60 | 158 | 90 |
| 0.50 | 0.70 | 37 | 24 |
| 0.50 | 0.80 | 18 | 13 |
| 0.30 | 0.50 | 39 | 17 |
| 0.30 | 0.60 | 17 | 9 |

Rules by size: lower bound above 0.50 needs 9 of 10, 15 of 20, 20 of 30, 26 of 40, 32 of 50. On a 50-post final set,
32 of 50 has power 0.34, 0.86 and 1.00 for true rates 0.60, 0.70 and 0.80.

### 3.3 Paired continuous AI share

Effect 0.38 to 0.20 (difference 0.18). Paired t-test, two-sided 0.05, exact noncentral t:

| SD of paired differences | n for 80% | n for 90% |
|---|---|---|
| 0.10 | 5 | 6 |
| 0.12 (B36 draft against rewrite) | 6 | 7 |
| 0.15 | 8 | 10 |
| 0.20 | 12 | 16 |
| 0.28 (B36, first 300 words) | 21 | 28 |

If 0.2 is the SD of each arm rather than of the difference, the paired SD is 0.2 times the square root of 2(1 - rho):
n is 22, 16 and 10 for rho 0, 0.3 and 0.6; independent arms need 21 per arm. Smaller effects: a difference of 0.10
needs 14, 20 and 34 posts at SD 0.12, 0.15 and 0.20; a difference of 0.05 needs 48, 73 and 128.

Shares are bounded and pile up at 0 (Pangram reports 0.00 for Human-reading texts). A simulation with post effects
(SD 0.12), arm noise (SD 0.10) and clipping to [0, 1] gives, for 0.38 against 0.20, one-sided 0.025 power: n 8:
Wilcoxon signed-rank 0.81, paired t 0.86, percentile bootstrap of the mean 0.94; n 10: 0.93, 0.94, 0.98; n 12: 0.97,
0.98, 0.99. With noise SD 0.14 (difference SD about 0.2), Wilcoxon needs 15 for 0.88. The percentile bootstrap is
anti-conservative at small n (its intervals are too narrow), so pre-register the Wilcoxon signed-rank test as the
test and report the bootstrap interval of the mean difference as the estimate.

### 3.4 Several sections from one post

Design effect 1 + (m - 1) ICC for m sections per post:

| ICC | 3 sections | 4 sections | 6 sections |
|---|---|---|---|
| 0.10 | 1.20 | 1.30 | 1.50 |
| 0.25 (B38 estimate) | 1.50 | 1.75 | 2.25 |
| 0.40 | 1.80 | 2.20 | 3.00 |

Rules: (a) for the detector endpoint, scan whole posts (the spec's unit, and half the noise of short texts); (b) when
sections are scanned, aggregate to a post mean before testing, or use a mixed model or a cluster bootstrap by post;
(c) since 75% of section variance in B38 was try-to-try, resampling the same section several times and picking
needs a held-out check, and comparisons between arms should use one pre-registered try per section.

### 3.5 Multiple comparisons

- Name one primary endpoint per decision. Recommended order for the final test, tested in a fixed sequence (each at
  full alpha, stop at the first failure; this controls the familywise error without splitting alpha): (1) Human rate
  lower bound above 0.50 on the final set; (2) quality non-inferiority from Henry's read; (3) faithfulness: zero
  deterministic violations and a sentence-level unsupported rate below a pre-set bound.
- For development screens comparing k arms against one baseline, use Holm on the k paired tests; with 3 arms the
  smallest p must be below 0.0167.
- Exploratory cuts (by writer, by length, by section type) are reported as estimates with intervals, no tests.

### 3.6 Sequential designs and stop rules

- **Binary Human rate, single arm: Simon two-stage** (exact, one-sided alpha 0.05, power 0.80), computed here:

| p0 (not worth it) | p1 (worth it) | Design | Stage 1 | Total | Expected n under p0 |
|---|---|---|---|---|---|
| 0.30 | 0.60 | optimal | 8 posts, stop if 3 or fewer Human | 24, success if 11 or more Human | 11.1 |
| 0.30 | 0.60 | minimax | 10, stop if 2 or fewer | 17, success if 9 or more | 14.3 |
| 0.50 | 0.75 | optimal | 11, stop if 6 or fewer | 25, success if 17 or more | 14.8 |
| 0.50 | 0.75 | minimax | 14, stop if 7 or fewer | 23, success if 16 or more | 17.6 |
| 0.10 | 0.40 | optimal | 4, stop if 0 | 15, success if 4 or more | 7.8 |
| 0.10 | 0.40 | minimax | 8, stop if 1 or fewer | 13, success if 4 or more | 8.9 |

  The 0.10 against 0.40 design is the cheap development gate: 4 to 8 posts decide whether an arm is dead.
- **Continuous share: two-look group-sequential design** with O'Brien-Fleming bounds (one-sided 0.025): stop for
  efficacy at half the posts if z is at least 2.797 (nominal p 0.0026), else test at the end at z 1.977 (nominal p
  0.024). The maximum n grows by only 0.8%. Add a non-binding futility stop at the interim if the mean difference
  points the wrong way.
- **Rules that keep it honest:** the stop rule, n and analysis are written in the script docstring and committed
  before the first scan (as attempt 1 did); every look is a separate blinded batch with the anchors; no arm is
  modified between stages.

### 3.7 Pangram credit arithmetic

1 credit per started 100 words per file (verified on B31 raw data in `longform-pangram-length.md`). A 2,000-word post
costs 20, a 2,500-word post 25. LaTeX inflates Pangram's word count 1.31 to 1.49 times; strip it consistently in every
arm.

## 4. Drift and measurement error in commercial detectors

- **Pangram 4.1 model card** (pangram.com/research/model-card/pangram-4-1, read 2026-11-06): released 2026-10-19;
  unintended verdict flips on paired edits fell from 1.08% (Pangram 4) to 0.15% across 29,103 edits; English false
  positive rate 0.0090% (70 of 781,981), false negative rate 0.3652% (1,899 of 520,000); new per-segment
  class_probabilities; model cards listed for 3.1, 3.2, 3.3, 4.0, 4.1; nothing on determinism, version pinning or
  access to old versions; nothing on accuracy above 499 words (earlier report). [primary, verified]
- **Release cadence:** 4.0 on 2026-07-29 and 4.1 on 2026-10-19, about 12 weeks apart (dates from
  `longform-pangram-length.md`). A version change during a multi-week attempt 2 is plausible.
- **Published test-retest studies of commercial detectors:** none found. Searches turned up studies of score
  variation across different texts and tools (for example a Journal of Applied Learning and Teaching (JALT) study of Turnitin, ZeroGPT, GPTZero and Writer, and
  an International Journal for Educational Integrity study of 14 detectors), not repeated scans of identical text.
  [secondary]
- **This project's retest (section 0.2):** within a version and a day, scan noise is at most 0.02 in share and 0
  label flips in 8; across a day, 1 of 7 labels flipped at a boundary. Measurement error from rescanning is
  therefore negligible; what matters is (a) version changes, (b) preprocessing differences (LaTeX, docx conversion,
  code blocks), and (c) texts near the 0.10 and 0.80 thresholds, where a 0.02 shift flips the label.

Protocol:
1. **Anchor set in every batch (about 45 credits):** four texts already scanned, chosen to cover the thresholds:
   - HR2 bandits post (2,502 words, Human 0.08): the most sensitive anchor, just under the Human threshold (26
     credits);
   - HR aieng s1 (342 words, Human 0.00): Human floor (4 credits);
   - HR aieng s5 (299 words, Mixed 0.65): mid-range (3 credits);
   - HO aieng s7 (474 words, AI 0.97) or one test-A draft: AI ceiling (5 credits);
   - optionally one test-A human original at full length (Human 0.00, about 20 credits) to keep a long-human
     false-positive check running.
2. **Decision rule:** if every anchor label matches and every share is within 0.03 of its reference, the batch is
   comparable with earlier batches. Otherwise treat the batch as a new instrument: note the version, do not pool it
   with earlier batches, and rescan the comparison arm in the same batch.
3. **Design over adjustment:** every comparison that matters puts all arms in one blinded batch on one day, so drift
   cancels in the paired difference. Do not try a statistical correction from 4 anchors; it would be weaker than
   rescanning.
4. **Record** the model version (the API returns `version`; the dashboard may not show it), date, time, credits
   before and after, and the preprocessing commit for every batch.

## 5. Reader panels: "does this read as AI?"

### 5.1 Evidence

- **Russell, Karpinska and Iyyer, ACL 2025** (arXiv 2501.15654): 300 non-fiction articles under 1,000 words, half
  human, AI from GPT-4o, Claude 3.5 Sonnet and o1-Pro, including paraphrased and humanised versions. 9 annotators
  from Upwork; experts screened (10 candidates, 5 passed a trial, 4 passed a 60-article test at 90%). Non-experts:
  true positive rate (TPR) 56.7%, false positive rate (FPR) 51.7% (chance). Experts: TPR 92.7%, FPR 4.0% on average;
  individuals 59.3% to 97.3% TPR. Majority of 5 experts: TPR 99.3%, FPR 0%, 1 error in 300. Pangram on the same
  texts: TPR 98.0%, FPR 2.0%; on humanised o1-Pro articles TPR 90.0%, FPR 6.7%. Pay $2 per article, $2.82 average
  with bonuses, about $15 to $30 per hour, 8 to 12 articles per hour, $4.9K in all. No inter-annotator agreement
  statistic reported. Experts mostly cite "AI vocabulary", then formality, originality and clarity; one expert who
  read informality as human lost accuracy on o1-Pro. [primary, verified]
- **Wang et al., ACL 2026** ("Is Human-Like Text Liked by Humans?"): 19 annotators, 16 datasets, 9 languages, 9
  domains, 87.6% average detection accuracy; humans do not always prefer human text, especially when they cannot
  tell the source. [primary, verified abstract]
- **TURING, LREC 2026** (Kalashnikova et al.): 214 participants, 500 texts in 10 genres, 7,943 usable annotations,
  about 59% accuracy with a slight lean to "human"; two automatic detectors at 88%. [primary, read via search
  snippets, unverified]
- **Milicka et al., arXiv 2505.01877 (2025):** 254 Czech readers, paired texts, GPT-4o; immediate feedback improved
  accuracy and confidence calibration; without feedback readers were most wrong when most confident. [primary,
  unverified beyond abstract]
- **Chakrabarty, Ginsburg and Dhillon (section 1.1):** expert readers' preference falls with Pangram score; lay
  readers' barely does.

Reading: detection skill is a trait of the reader, not the crowd. Screened heavy LLM users approach Pangram's
accuracy; lay readers are at chance. Henry, a heavy Claude user, is probably an expert detector; that makes him a
useful reader and also a demanding one.

### 5.2 Sample sizes for reader endpoints

Simulations with crossed readers and items, logit-scale random effects (reader SD 0.4, item SD 0.8), standard error
from the two-way variance components:

| Endpoint | Design | Power |
|---|---|---|
| Accuracy at most 0.60 (upper 95% bound), true accuracy 0.50 | 1 reader, exact binomial | 80% needs 158 items (71 if true 0.45) |
| same | 1 reader by 40 items | 0.36 |
| same | 5 readers by 40 items | 0.51 |
| same | 5 readers by 100 items | 0.71 |
| same | 10 readers by 100 items | 0.87 |
| same, true accuracy 0.55 | 10 readers by 100 items | 0.52 |
| Outputs flagged less than drafts (0.93 to 0.60), paired by item | 1 reader by 20 items | 0.68 |
| same | 1 reader by 30 items | 0.84 |
| same | 3 readers by 15 items | 0.96 |
| same | 5 readers by 10 items | 0.96 |

Cost of an expert panel at Russell et al.'s rate scaled to length: a 500-word section about $1 to $2 per read, a
2,000-word post about $4 to $8. Three screened experts by 40 posts is 120 reads, about $500 to $1,000 plus screening;
three by 40 sections, about $150 to $250. Both exceed what is left under the $100 cap unless Henry raises it.

## What I could not verify

- Upwork's own copy-editor rate page (HTTP 403); the $20 to $40 per hour figure and the 3% to 5% client fee come from
  secondary pages.
- Full texts of Laurito et al. (PNAS), Panickssery et al., Wataoka et al., Chen et al., Verga et al., FActScore,
  SummaC, AlignScore, FaithBench, FABLES, TURING and Milicka et al.: I saw abstracts or search summaries only. The
  arXiv 2601.19913 claim (Korean essays, kappa 0.82 after calibration) that a search summary reported does not match
  the abstract I read, so I dropped it.
- The Chatbot Arena style-control coefficients (length 0.249) are from a search summary of the LMSYS blog.
- Whether Pangram's dashboard runs the same model as the API at the same time, whether results are cached by text
  hash (which would make my retest finding a cache artifact rather than determinism), and whether old versions can
  be pinned. If results are cached, the anchor set still detects version changes but says nothing about intrinsic
  noise; scanning one anchor with a single added space would distinguish the two.
- The B15 scans' upload route and exact texts; the cross-day comparison rests on word counts matching within 2 words.
- WQRM's accuracy on technical prose and on rewrites of the same content (it was validated on creative writing).
- The B38 variance components rest on 4 posts; the ICC could be anywhere from about 0 to 0.6.
- No published accuracy for any faithfulness checker on 1,500 to 3,000-word rewrites; no published test-retest
  study of any commercial AI detector.
- How Pangram labels code blocks and tables in blog posts (out of scope per its model card).

## Implications for attempt 2

### A. Quality protocol (primary quality endpoint)

1. Endpoint: Henry's blind forced choice, draft against output, on 40 section pairs (400 to 700 words a side) from
   20 posts by other writers (2 sections per post), plus 10 control pairs (4 repeats swapped, 4 human original
   against draft, 2 near-identical). Success: at least 20 of 40 output wins (rules out a win rate of 0.35 or less at
   one-sided 0.05) and no more than 2 outputs flagged unpublishable. Report the win rate with its interval, the
   repeat agreement, and the control results.
2. Defect screen before Henry reads: form checks, repeat checks, and an LLM defect checklist (yes or no items),
   with the LLM's flags shown to Henry only after his choice.
3. Secondary, reported but not decisive: WQRM score difference and a three-family LLM panel's choice, each reported
   as agreement with Henry's labels. If either agrees with Henry on at least 80% of pairs with a lower bound above
   0.65, it may be used to screen development outputs later (a judge validated against the decision it makes).
4. Optional (needs Henry's yes, about $60 to $100): one screened editor reads 20 of the same pairs; report
   Krippendorff's alpha with Henry.
5. Henry's time: 50 pairs at about 5 minutes is about 4 to 4.5 hours, in two or three sittings; plus 3 to 5 whole
   output posts read end to end (about 10 minutes each) for whole-piece coherence.

### B. Faithfulness protocol

1. Hard gates (deterministic, zero tolerance): new specifics, new code lines (tighten form.py's 2 to 0), new math,
   non-English runs, new framing, restart openers.
2. Sentence-aligned entailment for every output sentence against retrieved draft passages; report the share of
   unsupported sentences and list them; gate at a pre-set share (for example at most 2% of sentences, with every
   flagged sentence read by a human for the final set).
3. Audit before use: 10 planted error types by 30 outputs (300 cases) plus 60 clean controls; publish recall per
   type with exact lower bounds and the false-alarm rate. Target: every type at least 0.85 lower bound (30 planted, at
   most 1 missed). Zero Pangram credits; about 400 to 700 model calls.
4. Henry's time: about 30 minutes to read 20 flagged and passed sentences from the audit and 20 from real outputs.

### C. Statistics plan and sample sizes

| Stage | Question | Design | n | Pangram credits |
|---|---|---|---|---|
| Calibration | Has Pangram changed? Is the long-document false-positive rate still near 0? | Anchor set every batch | 4 to 5 texts per batch, about 8 batches | about 360 |
| Development gate (per arm) | Is the arm alive? | Simon 0.10 against 0.40 on full posts, whole posts by other writers | 4 then up to 15 posts | 100 to 375 |
| Development comparison | Does arm B lower the AI share against arm A? | Paired, same batch, Wilcoxon signed-rank, one pre-registered try per post, two-look O'Brien-Fleming | 12 posts per arm pair (80% power for 0.38 to 0.20 at difference SD up to 0.2; 14 to 20 for a 0.10 drop at SD 0.12 to 0.15) | 600 per comparison (both arms) |
| Henry's own posts | Does it work on his genre? | Descriptive, all sections and whole posts, same batch as anchors | his 2 to 4 posts | about 150 to 250 |
| Final test | At least 50% Human on held-out long posts | One sample, lower bound above 0.50, fixed sequence with quality and faithfulness | 50 posts (need 32 Human; 86% power at true 0.70) | about 1,250 at 2,500 words |
| Final test, optional comparison | Better than attempt 1's rewriter? | McNemar on the same 50 posts | 50 pairs (80% for 3% against 30%; 80% for 30% against 60% if phi about 0.3) | about 1,250 more if attempt 1's rewriter is rescanned; 0 if the attempt-1 baseline is taken as known |

Totals: calibration 360, two development gates 200 to 750, two comparisons 1,200, Henry's posts about 200, final
test 1,250: about 3,200 to 3,800 credits. A third gate brings it to about 4,100; the optional comparison adds 1,250,
for a ceiling near 5,400. That leaves 3,300 to 5,500 of the 8,717 credits as reserve for a version change
(rescanning an arm) or a second final set.

Pre-register in each script docstring: the endpoint, the test, n, the stop rule, the anchor rule, the preprocessing
commit (LaTeX and code handling) and the analysis unit (post). Scan all arms of any comparison in one blinded batch.

### D. Henry's reading time in total

| Task | Time |
|---|---|
| Quality read: 40 pairs plus 10 controls | 4 to 4.5 hours |
| Whole-post reads of 3 to 5 outputs | 0.5 to 1 hour |
| Faithfulness audit spot reads | 0.5 hour |
| Optional reader-panel task (flag AI or human on 30 drafts and outputs from other writers, paired) | 1.5 to 2 hours |
| Total | about 6.5 to 8 hours |

The reader-panel task is the cheapest credible "reads as AI" measure: Henry as one expert reader on 30 paired items
gives 84% power to show outputs are flagged less than drafts (0.93 to 0.60). The spec's "reader accuracy at most 60%"
should be reported as an estimate with its interval, not a pass or fail, unless a paid panel of about 10 readers by
100 items is approved.

## Sources

- Russell, Karpinska, Iyyer, ACL 2025: https://arxiv.org/abs/2501.15654 ; https://aclanthology.org/2025.acl-long.267
- Chakrabarty, Laban, Wu, COLM 2025: https://arxiv.org/abs/2504.07532
- Chakrabarty, Ginsburg, Dhillon 2025/2026: https://arxiv.org/abs/2510.13939
- Chakrabarty, Laban, Wu, CHI 2025: https://arxiv.org/abs/2409.14509
- Laurito et al., PNAS 2025: https://arxiv.org/abs/2407.12856 (DOI 10.1073/pnas.2415697122)
- Panickssery, Bowman, Feng, NeurIPS 2024: https://arxiv.org/abs/2404.13076
- Wataoka, Takahashi, Ri: https://arxiv.org/abs/2410.21819
- Chen et al. 2025: https://arxiv.org/abs/2506.02592
- Dubois et al., COLM 2024: https://arxiv.org/abs/2404.04475
- LMSYS style control, 2024-08-28: https://www.lmsys.org/blog/2024-08-28-style-control
- Verga et al. 2024: https://arxiv.org/abs/2404.18796
- Tang, Laban, Durrett, EMNLP 2024 (MiniCheck): https://arxiv.org/abs/2404.10774
- LLM-AggreFact leaderboard: https://llm-aggrefact.github.io/
- FaithBench: https://arxiv.org/abs/2410.13210
- FABLES: https://arxiv.org/abs/2404.01261
- Claim decomposition: https://arxiv.org/abs/2403.11903 ; MedScore https://arxiv.org/abs/2505.18452
- Pangram 4.1 model card: https://www.pangram.com/research/model-card/pangram-4-1
- EditLens (Thai, Emi, Masrour, Iyyer, ICLR 2026): https://arxiv.org/abs/2510.03154 (Pangram's continuous AI-editing
  score; relevant if the API exposes AI-assisted fractions) [primary, unverified beyond abstract]
- Wang et al., ACL 2026: https://aclanthology.org/2026.acl-long.639/
- TURING, LREC 2026: https://lrec.elra.info (paper page via search) [unverified]
- Milicka et al. 2025: https://arxiv.org/abs/2505.01877
- Prolific pricing: https://www.prolific.com/pricing (read 2026-11-06)
- Upwork copy editor cost page (403 to me): https://www.upwork.com/hire/copy-editors/cost/ [secondary figures]
- Krippendorff bootstrap note: https://asc.upenn.edu/sites/default/files/2021-03/Algorithm%20for%20Bootstrapping%20a%20Distribution%20of%20Alpha.pdf
- Simon, R. (1989), "Optimal two-stage designs for phase II clinical trials", Controlled Clinical Trials 10:1-10
  (designs reproduced by my code, see top).
