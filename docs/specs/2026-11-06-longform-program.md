# Long-form program: whole blog posts at scale on Modal (B32 to B39)

Design doc by the long-form head session, drafted 2026-11-06 from 02:16 CST and first committed after 03:17 CST.
Brief: `docs/briefs/2026-11-06-longform-head.md` (commit 9348eda). Claims ledger:
`results/research/longform-claims.md`. Pipeline: `experiments/modal/README.md`. No Pangram scan of this program has
happened. Each experiment's own selection, exclusion and decision rules go into its script docstring and are
committed before its scan. Amendments after the first commit are appended at the end with a time read from `date`.

## 1. The goal behind the goal

Henry drafts technical blog posts of 1,500 to 3,000 or more words with an AI. The outcome he wants is a post that
reads as his to Pangram and to careful readers, without anything invented. So far the project has worked on texts
of 235 to 800 words, cells of 13 to 30 documents, a 4,096-token writer and a 16 GB GPU. This program asks whether
the results hold at real length, on authors the models never saw, with powered held-out evidence, and builds the
Modal pipeline that makes the next experiment a config instead of a week of plumbing.

## 2. What phase 1 changed in the plan

Phase 1 is this doc, the claims ledger, the B32 corpus pilot, the B33 detector calibration and two outside-judge
audits. Five findings reshape the design (numbers in section 12 and the ledger):

1. **B30 (main session, 02:40) makes the rewriter the lead route.** A rewriter trained on Sonnet posts paired with
   the human essays turned B28's Sonnet posts from 0 Human of 19 into 13 of 19 (half the notes) and 19 of 19 (all
   the notes), at about 640 words, on held-out essays by authors it had trained on. The open questions are now
   unseen authors and real length, so the program tests the existing rewriter on unseen authors at length (B36)
   before it spends on new training.
2. **At length, Human is a strict bar.** Pangram labels a document Human only if 90% of its characters are labelled
   Human; AI-Assisted characters count against that, and Pangram publishes no accuracy above 499 words (ledger
   claim 6). Every scanned output is therefore also scanned as its 300-word prefix, which pairs the length effect on
   the very texts that matter, and B34 measures the false-positive rate on long human posts.
3. **The open detectors do not stand in for Pangram on the project's own outputs.** On 1,193 Pangram-labelled texts,
   Binoculars, both Fast-DetectGPT variants and desklib rank Pangram's not-Human texts as less AI-like than its Human
   ones, and inside the local-writer outputs they run against Pangram (within-experiment AUROC about 0.33). Only MELD
   agrees in every stratum (AUROC 0.63 overall, 0.67 on local-writer outputs, 0.83 above 800 words). The development
   judge is MELD alone (section 8), and development choices lean on local checks first.
4. **Separating humanizer conditions from each other needs large effects.** With B30's rates, differences between
   rewriter conditions are likely 5 to 10 points of Human rate; no affordable n detects that (section 7). The final
   test is built around the contrasts it can answer.
5. **The corpus works but the site key leaks and the genre tag is loose** (outside judge, ledger claim 12): at least
   10 of 2,997 dev and test posts share an owner with a post in another split, one test site is an earlier-corpus
   blog under a new domain, and the tags are 60 to 65% precise. Section 5.1 lists the fixes for the full build.

## 3. Questions, sharpened

Primary endpoint: Pangram's document label (Human against not Human), reported as a rate with a 95% Wilson
interval. Contrasts are tested on Pangram's AI share (continuous, paired), because the label has too little power
(section 7). Secondary: the label of the 300-word prefix, length kept, claims supported, copying from the human
original, and a blind read.

- **Q0 (length).** Does length by itself move the verdict? (a) Do human posts of 2,000 words keep reading Human?
  (b) Do outputs whose 300-word prefix reads Human keep reading Human at full length? Prediction from the 90% rule:
  (a) yes; (b) the full-length Human rate is below the prefix rate.
- **Q1 (the AI post alone, Henry's real input).** At 1,500 to 3,000 words on authors the models never saw, what
  share of rewrites of an AI post read Human (CAI), against the AI post itself (D)? Does adding the author's notes
  help (CAIN)? The notes-only writer (CN) is an optional arm (section 7).
- **Q2 (scale).** Does the long-context rewriter trained on thousands of long posts from thousands of sites (CAI-new)
  beat the existing B30 rewriter applied section by section (CAI-old) on the same documents? Development metrics
  separate the parts (base model, data size, generator families); Pangram sees only this combined contrast.
- **Q3 (generation unit).** Whole-document against section by section with carried context (development only, B38).
- **Q4 (Henry's genre).** Technical posts are a pre-registered stratum of the test set (reported, not powered), and
  Henry's own drafts are an optional descriptive arm with his notes and his blind read.

## 4. Experiments B32 to B39

| ID | Phase | Question | Conditions | Judge | Pangram credits |
|---|---|---|---|---|---|
| B32 | 1 pilot, 2 full | Corpus | Long pre-ChatGPT blog posts from FineWeb, split by site (5.1) | outside judges: leakage, dates, genre | 0 |
| B33 | 1 (done) | Detector calibration | 5 open detectors on 1,193 Pangram-labelled texts and 400 pilot posts | outside judge recompute | 0 |
| B34 | 2 | Q0a, and base text at length | H: 10 calib-split posts; B: 8 raw base continuations to 2,000 words; each at 300 words and full | Pangram (calibration use, spec section 8) | about 420 |
| B35 | 2 | Inputs | Notes and reworded notes for every post; AI posts (open instruct families for training, Sonnet for dev and test) | local checks | 0 |
| B36 | 2 | Q1 and Q0b with the existing rewriter | Test-A split, 32 documents: D and CAI-old (B30's rewriter, section by section), full and 300-word prefix | Pangram, blinded | about 1,500 |
| B37 | 2 | Q2 parts | Base-model selection (5.2), then rewriter and notes writer on the chosen base; 1,000-document data ablation | MELD and local checks only | 0 |
| B38 | 2 | Q3 | Whole document against sectional, same writer, dev split | MELD and local checks only | 0 |
| B39 | 2 final | Q1, Q2, Q0b, Q4 | Test-B split, 40 documents: D, CAI-old, CAI-new, CAIN-new, full and 300-word prefix | Pangram, once, blinded | about 3,740 |

**Conditions.**
- D: Sonnet (through `humanizer.llm`, the account Henry drafts with) writes the post from 50% of the author's
  reworded notes ("Write my blog post from these notes", the human post's length). B28's S50 read 0 of 19 Human.
- CAI-old: the B30 adapter (OLMo-2-13B, 4-bit, Volume `b31-weights`, `adapters/b30-rewritepool`) rewrites D one
  section at a time (sections of at most 1,000 words cut at headings or paragraph breaks), with B30's Guard, seeds,
  prune and pick; sections are joined in order.
- CAI-new: the long-context rewriter from B37 rewrites D whole (or by B38's winning unit).
- CAIN-new: the same rewriter given D and the same 50% notes.
- CN (optional): the notes writer from B37 given only the 50% notes.
- H: the human post (B34 measures its false-positive rate at length).
- Every output: best of 4 samples by the claim check, then deletion of unsupported sentences and repeats, never
  rewording. Length, claims supported and 8-word copying from the human original are recorded for every output.
- B36 and B39 use disjoint halves of the test split (buckets 90 to 94 and 95 to 99), so B39's documents stay
  untouched until its own scan.

## 5. Data, splits and models

### 5.1 Corpus and splits (B32)

- **Source.** FineWeb (HuggingFaceFW/fineweb, revision 9bb295dd), dumps CC-MAIN-2019-04 to CC-MAIN-2022-40.
  CC-MAIN-2022-49 is excluded (it straddles ChatGPT's release). Every row's `date` is its Common Crawl capture time
  and must be before 2022-11-30.
- **Filters** (`experiments/modal/lf_corpus.py`, rules committed in 63e43ab before the pilot): English, 1,500 to
  4,000 words after trailing comment blocks are cut, blog-like URL, first-person or technical genre, no spam,
  fiction or list pages; URL and MinHash deduplication across dumps.
- **Unit of split: the site.** sha256("b32-split-v1:" + site) mod 100: 0 to 74 train, 75 to 79 calib (B34 and
  detector thresholds; never trained on), 80 to 89 dev, 90 to 94 test-A (B36), 95 to 99 test-B (B39). The pilot used
  0 to 79 as train and 90 to 99 as test; the new buckets are carved from those with the same hash. Sites in any
  earlier training corpus (`data/*.jsonl`) are forced to train. One post per site outside train.
- **Fixes before the full build** (from the outside judge, `results/research/longform-judge-b32.md`):
  - merge site keys before hashing: the same name across country endings, wordpress.com or substack against the
    blog's own domain, redirects seen in the crawl, @user against user.medium.com; apply the earlier-corpus check
    to the merged groups (one test site, broeder10.blog, is an earlier-corpus blog that moved);
  - match blog platforms by domain ending, not substring;
  - drop listing pages (date archives, tag, category and author pages, home pages: 18.5% of pilot URLs);
  - an open instruct model labels genre and page type (personal post, technical post, company or magazine page,
    transcript, spam), with precision measured on a labelled held-out set of 100; only personal and technical posts
    by one author are kept;
  - deduplicate texts across splits over the whole corpus at Jaccard 0.5, and drop scraped copies (the same text
    on two sites goes to the earliest capture's site, or is dropped if the sites are in different splits);
  - vectorize MinHash (the pure-Python version takes about 50 ms a document).
- **Dates.** Every capture is before the cutoff (latest 2022-08-20). The B32 date audit and the outside judge
  confirmed captures against the Common Crawl index and its WARC records, and found earlier Wayback captures for
  most posts (section 12). A pre-ChatGPT date does not prove human authorship (the judge found spun spam and an
  auto-generated transcript), so the page-type filter above also drops machine-made pages.
- **Test documents stay untouched.** Apart from the automated filters, date and contamination checks, no person,
  agent or model reads a test text until its experiment's generation. Notes and AI posts for a test half are made in
  one batch right before its experiment.
- **Genre stratum.** Technical posts with code or tables are at least a quarter of each test half (by the page-type
  label), so Q4 has a stratum; the full build reads shards until train has at least 1,500 such posts.
- **Named essayists.** The 13-writer essay corpus stays a separate track; its writers are never in a test split.
- **Contamination.** If Olmo 3 is chosen, test posts are checked against Dolma 3 (open data) by streaming its mix
  and matching 13-gram shingles; OLMo-2's mix is indexed by infini-gram. Whatever the model, the 8-word copying audit
  against the human original catches recitation, which is how contamination would inflate a Human verdict.

### 5.2 Long-context base model: candidates and the selection rule (B37)

Candidates, verified on model cards and configs (`results/research/longform-base-models.md`, ledger claim 11):

| Candidate | Context | License | Data | Fits (inference 16K / LoRA 8K) |
|---|---|---|---|---|
| allenai/Olmo-3-1025-7B | 65,536 | Apache-2.0 | open (Dolma 3) | L40S / L40S |
| allenai/Olmo-3-1125-32B | 65,536 | Apache-2.0 | open | 80 GB / 80 GB |
| meta-llama/Llama-3.1-8B | 131,072 | Llama 3.1, gated (granted) | closed | L40S / L40S |
| google/gemma-3-27b-pt | 131,072 | Gemma, gated (granted) | closed | 80 GB / 80 GB |
| mistralai/Mistral-Small-3.1-24B-Base-2503 | 131,072 | Apache-2.0 | closed | 80 GB / L40S |
| Qwen/Qwen3.5-9B-Base | 262,144 | Apache-2.0 | closed | L40S / L40S |
| google/gemma-4-31B (base, not in the brief) | 262,144 | Apache-2.0 | closed | 80 GB / 80 GB |

Mistral-Small-24B-Base-2501 (the brief's candidate) has only 32,768 tokens; its 3.1 base replaces it. OLMo-2-13B
(4,096 tokens) is the reference, used section by section (CAI-old).

**Rule, fixed now, development metrics only, never Pangram:**
- **Stage A, no training.** Each candidate continues the first 300 words of 40 dev posts to 2,000 words (T 0.8, top-p
  0.95, one seed, vLLM, bf16). Excluded if more than 10% of its continuations stop under 1,500 words or repeat more
  than 20% of their 4-grams. Score: mean MELD score over the 40 (lower is more human-like). The two lowest go on; a
  24B or larger finalist needs Henry's separate budget yes first (section 10).
- **Stage B, a short fine-tune.** Each finalist gets the same LoRA (rank 64, 1 epoch, 1,500 training pairs of AI
  post to human post, 8,192 tokens) and rewrites D on the 40 dev posts. Eligible: claims supported at least 0.90 and
  mean length at least 80% of the human post. Among the eligible, the lower mean MELD score wins, unless the 95%
  bootstrap interval of the paired difference over the 40 documents includes zero, in which case the model with fewer
  parameters wins.
- If no finalist is eligible, the program stops at this gate and reports.

### 5.3 Inputs (B35)

- **Notes:** one open instruct model extracts notes from every post (B25's FACTS prompt, first person kept), then
  rewords them (B27's prompt). Manipulation check: 8-word copying from the post at most 2% of note words. One
  extractor for every split.
- **AI posts, training:** three open instruct families (for example Qwen3.5-9B-Instruct, Gemma-3-12b-it,
  Olmo-3-7B-Instruct) write from 50% of the notes, round robin by document; the rewriter learns AI post to human
  post, as B30 did with Sonnet posts.
- **AI posts, dev and test:** Claude Sonnet through `humanizer.llm` (at most 2 workers), from the same 50% notes.
  Q2c (a generator family absent from training) is optional: Mistral-Small-3.1-24B-Instruct on Modal, or GPT-5 or
  Gemini 2.5 if Henry provides keys (they cost money and need his yes).

## 6. Faithfulness at long context

The rule is unchanged: add no facts, names, numbers, dates or quotes. Three layers:

1. **Guard in vLLM.** A per-request logits processor for vLLM's V1 engine (subclass of
   `vllm.v1.worker.gpu.sample.logits_processor.LogitsProcessor`, registered at load, the request's allowed names and
   numbers passed in `SamplingParams.extra_args`). It ports `src/humanizer/pipeline/guard.py`: mid-sentence, a token
   that starts a capitalized word or contains a digit is blocked unless it extends a prefix of a name or number from
   the input; sentence starts also allow common words; quote marks are blocked when the input has none. Word
   continuation needs each request's recent tokens, so the processor keeps per-request prefix state. Acceptance test
   before any use: on 200 prompts, its masks equal the transformers `TorchGuard`'s at every step of a forced decode,
   and a run on B26's prompts reproduces the Guard's zero-new-name rate. Until it passes, generation uses the B30
   path (transformers with `TorchGuard`), which is slower but proven.
2. **Check and resample, per section.** After generation, the claim check marks unsupported sentences; a section with
   any is resampled up to 3 times (new seed, same context), then its unsupported sentences are deleted, never
   reworded.
3. **Claim check on every output.** Development: an open judge (a 27B instruct model on Modal) with the project's
   ENTAIL prompt, section by section against the input. Final tests: Sonnet through `humanizer.llm`, the project's
   existing check. The two judges are compared on 100 dev outputs; below 85% agreement on claims, the open judge is
   not used for decisions.

Copying: 8-word runs shared with the human original (which the writer never sees) are reported for every output;
above 15%, the output is flagged and excluded from the primary analysis.

## 7. Power analysis and the Pangram credit plan

`experiments/lf_power.py` (all cells in `results/b39_power.json`) simulates the paired design: each document's AI
share is expit(b_c + u_d + e_dc), with a document effect shared by its conditions (B31: the document matters more
than the model), within-document correlation 0.2 or 0.5, total spread 2 logit units, and Pangram's label rule
applied to the share (Human at or below 0.10). Holm over three contrasts, two-sided alpha 0.05, 2,000 simulations.
Two scenario sets: set 1, written before B30's verdicts (gaps of about 15 to 20 points between conditions), and the
B30-informed set (CAI 0.25, 0.50, 0.70 across pessimistic to optimistic; the next condition 10 points higher, the
one after 5 more).

| Power at n = 40 | Big gap (D 0.03 against CAI 0.30 to 0.50) | 20-point gap (set 1) | 10-point gap (B30-informed) | 5-point gap |
|---|---|---|---|---|
| Human label, McNemar | 0.85 to 1.00 | 0.16 to 0.39 | 0.05 to 0.09 | about 0.03 |
| AI share, Wilcoxon signed-rank | 1.00 | 0.53 to 0.82 | 0.13 to 0.29 | 0.05 to 0.07 |

At n = 64 the 10-point gap still has only 0.20 to 0.48 power on the AI share. So:
- **The contrasts that can be answered are big ones:** a rewriter against the AI post (CAI over D), and the scale
  contrast (CAI-new against CAI-old) if scale buys 20 points or more. Notes over no notes (CAIN against CAI) is an
  estimate with an interval, not a test, unless the gap turns out large.
- **Tests run on Pangram's AI share** (Wilcoxon signed-rank, paired by document, Holm over B39's three contrasts:
  CAI-new over D, CAI-new against CAI-old, CAIN-new against CAI-new). McNemar on the label is secondary. Each
  condition's Human rate is reported with a Wilson interval (half-width about 0.15 at n = 40, 0.16 at n = 32).
- **n = 32 for B36 and 40 for B39.** After B34 and B36 measure real AI shares at length, the script is re-run with
  the measured spread and correlation, and B39's n is fixed in its docstring before its scan (at least 40, at most
  what the credits allow).

**Credit plan, 6,000 credits** (20.4 credits per full scan at the pilot's lengths, 3 per 300-word prefix):

| Item | Scans | Credits |
|---|---|---|
| B34: H 10 and B 8, prefix and full each | 36 | about 420 |
| B36: D and CAI-old x 32 test-A documents, prefix and full | 128 | about 1,500 |
| B39: D, CAI-old, CAI-new, CAIN-new x 40 test-B documents, prefix and full | 320 | about 3,740 |
| Reserve (rescans, failed uploads) | | about 340 |
| **Total** | | **6,000** |

Optional, beyond 6,000: CN on the 40 B39 documents (about 940; Q1's notes-only condition), Q2c on 12 documents
(D' and CAI', about 490), Henry's own drafts (up to 6 posts x 3 conditions, about 450). **Recommendation: 6,000
credits for the core; 7,500 adds CN and Q2c.**

## 8. Development metrics (what selects, since Pangram never does)

- **Development detector: MELD alone** (anon-review-meld-2026/meld, pinned revision, its own scorer). B33 showed it
  is the only open detector whose ranking agrees with Pangram in every origin and length stratum of the 1,193
  calibration texts. This choice uses existing Pangram verdicts for detector calibration only (spec section 8),
  before any phase 2 text exists; nothing is trained on them. Its agreement is weak inside base and local-writer
  text (AUROC 0.63 and 0.67), so a MELD gain is a hint, not evidence, and it can be gamed: development choices
  first apply the local checks, and MELD breaks ties.
- **Zero-shot detectors (Binoculars, Fast-DetectGPT) and desklib are diagnostics only.** They measure how machine-like
  a text is under a language model, which separates human text from base-model text almost perfectly but runs
  against Pangram on fine-tuned outputs. Optimizing against them would push the writer away from Pangram's Human.
- **Local checks:** claims supported, Guard violations, length kept, 8-word copying, repetition, and first-person
  rate and sentence-length spread against the human post (B26's voice measures).
- **Quality:** an LLM panel on dev (biased toward AI style, section 17 of the report, so used only as a floor), and
  Henry's blind read on a small B39 set through ArtifactData, built as the earlier blind read was.

## 9. Validation plan

Every artifact a claim rests on gets a validator with a fresh context, given the artifact and the claim, not the
reasoning (`outside-judge` agent unless stated).

| Artifact | Validator | Check | When |
|---|---|---|---|
| B33 calibration numbers and detector code | outside judge | recompute every statistic from raw files; check formulas against reference code | phase 1, done (one bug found and fixed) |
| B32 split, dates, genre | outside judge | site leakage, earlier-corpus sites, near-duplicates, dates against Common Crawl and Wayback, tag precision | phase 1 pilot, done; again on the full build with merged keys |
| Contamination | separate agent | test posts against Dolma 3 (if Olmo 3) or the infini-gram index | before B36 and B39 |
| Guard port | test suite | identical masks to `TorchGuard` on forced decodes | before any vLLM generation |
| Claim check | second judge | Sonnet against the open judge on 100 dev outputs; Henry spot-checks 10 | before B36 |
| Pre-registration timing | outside judge | git commit times of each docstring against Pangram dashboard scan times | after B34, B36, B39 |
| Every statistic | outside judge | recompute from the raw verdict files | after B34, B36, B39 |
| Copying | outside judge | 8-word runs of every output against its human original | before each analysis |
| The final result | red-team agent | length, topic and genre confounds, Guard artifacts, selection effects, prefix against full disagreement, author leakage | after B39 |

## 10. Modal cost estimate (full program)

Prices from modal.com/pricing on 2026-11-06, including CPU and memory on GPU containers (about $0.44 an hour for 4
cores and 32 GiB); `experiments/modal/lf_cost.py` prints the table. Measured in phase 1: a FineWeb shard takes 6 to 9
minutes on 4 cores; the Falcon pair scores about 2,500 tokens a second on an L40S. Other throughputs are typical
vLLM and LoRA figures and are marked as estimates in the script.

| Phase | Work | GPU | Hours | Dollars |
|---|---|---|---|---|
| 1 (done) | Corpus probe and pilot, detector weights, smoke tests, calibration (1,593 texts) | CPU, L40S | about 0.4 L40S | about 1 (section 12) |
| 2a | Full corpus (40 shards), page-type labels, Dolma 3 contamination stream | CPU, L40S | 6 CPU container hours, 0.3 L40S | 5 |
| 2b | Notes and rewording for 7,000 posts (27B instruct); AI posts for 6,000 training posts (3 families, 8 to 12B) | H100, L40S | 1.5, 2.0 | 12 |
| 2c | B34 base continuations; B36 CAI-old generation (32 documents x 2 seeds, 4-bit, B30 path) | L40S, A10 | 0.3, 3 | 5 |
| 2d | B37 stage A (6 models), stage B (2 LoRA finalists, 8B-class), dev generation | H100, L40S | 1.2, 5.0 | 18 |
| 2e | B37 writers (12,000 pairs, about 60M tokens, 1 epoch) and the 1,000-document ablation | H100 | 5.8 | 27 |
| 2f | B38 and B39 generation with the Guard, open claim check, MELD on all outputs | L40S, H100 | 2.2, 1.2 | 11 |
| | **Total, 8B-class writer** | | | **about 78 (about 97 with 25% for smoke tests and reruns)** |
| | Total if B37 picks a 24 to 32B writer (training about 24 H100 hours) | | | about 185 (about 230) |

**Recommended budget to ask Henry for:** up to **$80 of paid Modal spend** beyond the free credit (the $97 total less
about $18 of this month's free credit left), released at three
gates: (1) 2a to 2c, about $22, which B36 needs and which mostly fits in this month's remaining free credit; (2) 2d,
about $18, only after Henry sees B36; (3) 2e and 2f, about $38. A 24 to 32B writer needs a separate yes: about $185
to $230, above the project's $100 cap. And **6,000 Pangram credits** (7,500 with the optional arms).

## 11. Workstreams, agents and gates

- **Head (this session):** plan, budget, pre-registration, sequencing, the ledger, the report.
- **Workstreams, each its own agent with the artifact paths and the rule line ("work at expert depth, start from raw
  data, verify with an external check, report what you could not verify"):** corpus (B32 full build), inputs (B35),
  training (B37), generation and evaluation (B36, B38, B39 generation and local checks), and the Pangram operator
  (B34, B36, B39 scans; own Chrome tab; one-time token on 127.0.0.1 on a port other than 8799 and B31's).
- **Gates, each with a note to the main session:** budget approved; corpus built and audited; B34 and B36 scanned
  (report to Henry before gate 2 money); base model chosen; writers trained; B39 design committed; B39 scanned; red
  team done.
- **Stop rules:** Modal spend reaching the approved gate; a validator failing a leakage, date or copying audit; no
  eligible finalist in B37.

## 12. Phase 1 results

**B33, open detectors against Pangram** (`results/b33_calibration.json`, recomputed by an outside judge,
`results/research/longform-judge-b33.md`). 1,193 unique Pangram-labelled texts (704 Human), AUROC for not Human
(95% interval, bootstrap over source documents):

| Detector | All | Base (619) | Local writer (339) | Instruct (165) | 800+ words (164) | AI share rho (680) | False positives, 400 long human posts |
|---|---|---|---|---|---|---|---|
| Binoculars (Falcon pair) | 0.39 (0.33 to 0.46) | 0.66 | 0.38 | 0.58 | 0.32 | 0.24 | 0% |
| Fast-DetectGPT, Falcon pair | 0.41 (0.35 to 0.47) | 0.69 | 0.39 | 0.57 | 0.32 | 0.27 | |
| Fast-DetectGPT, Llama 3.1 8B | 0.42 (0.37 to 0.46) | 0.59 | 0.47 | 0.80 | 0.50 | 0.06 | |
| MELD | **0.63 (0.59 to 0.68)** | 0.63 | 0.67 | 0.94 | 0.83 | 0.30 | 0% |
| desklib | 0.48 (0.42 to 0.54) | 0.58 | 0.41 | 0.91 | 0.52 | 0.23 | 12% |
| Panel (pre-registered mean) | 0.41 (0.36 to 0.47) | 0.59 | 0.43 | 0.79 | 0.47 | 0.11 | |

- Every detector separates the 62 human texts from the 619 base-model texts almost perfectly (AUROC 0.96 to 1.00),
  while Pangram calls 448 of those 619 Human: the open detectors measure machine-likeness, Pangram something closer
  to assistant-likeness.
- Inside experiments on the project's own writer outputs, the zero-shot detectors and desklib run against Pangram
  (within-experiment AUROC about 0.33 to 0.35); MELD agrees (about 0.69 to 0.73).
- Binoculars and Fast-DetectGPT on the same pair correlate at 0.92: one mechanism.
- The detector code matches the published formulas (Fast-DetectGPT to 6e-6 on random logits); Binoculars uses L-1
  positions for both terms where the released code averages one more position, so its threshold is approximate.

**B32, corpus pilot** (`results/b32_pilot_summary.json`). Four FineWeb shards (2019-35, 2020-40, 2021-31, 2022-33),
4.15M rows: 3.26M English, 195,462 in the length window, 18,975 kept (url 147,824 rejected, genre 19,204, words
6,170, dialogue 2,121, spam 1,017, list-like 151), 18,575 after deduplication, 15,132 after one post per site; split
12,135 train, 1,492 dev, 1,505 test; 683 tagged tech (4.5%); median 1,953 words; 75% have a date in the URL. 46
posts on earlier-corpus sites went to train. A 400-post sample (200 tech, 200 personal) is local; the rest is on the
Volume `longform`. Yield per shard is about 3,800 posts, so the full build needs few shards for volume and more for
the technical stratum.

**Dates** (`results/b32_pilot_datecheck.json`, 29 of 30 planned posts, and the outside judge's 10): every capture
before 2022-11-30; where the Common Crawl index answered (18 of 29; the rest were rate-limited), the capture timestamp equals
FineWeb's on 18 of 18, and the archived page contains the text on 17 of 17 that could be fetched; the Wayback Machine
has a capture before the cutoff for 29 of 29 answered, 20 of them earlier than the Common Crawl capture; all 22 URL
dates precede the capture. The judge confirmed 10 of 10 against the index and WARC records and 8 of 10 with an
independent Wayback capture (two Wayback copies came from Common Crawl itself).

**Power and spend:** section 7; Modal spend in phase 1 is in the ledger and the report to the main session.

## 13. What phase 1 could not verify

- How Pangram 4.x behaves on human or AI text above 499 words (B34 measures it).
- Whether B30's rewriter generalizes to unseen authors and to 2,000-word posts (B36).
- Real forward-pass correctness of the Binoculars and MELD runs beyond the formula checks and score consistency.
- Whether MELD's human training data overlaps FineWeb (its card does not say), which would make its zero false
  positives on the pilot optimistic.
- Author identity that URLs cannot reveal (pen names, Medium authors across publications).
- The vLLM Guard port (written as a design, not run) and vLLM 0.32's speed on Olmo 3 through the Transformers
  backend.
- Every phase 2 throughput figure not marked measured.

## Revisions before the first commit

- 02:33 CST: power section rewritten after the first simulation showed the label endpoint cannot separate humanizer
  conditions; contrasts moved to the AI share.
- 02:47 CST: power scenarios revised with B30's verdicts (sent by the main session at 02:40).
- 03:17 CST: experiments restructured around B30 (B36 is now the existing rewriter on unseen authors at length; base
  selection and training merged into B37; CN and Q2c optional), the development detector changed from the panel to
  MELD alone after B33, the test split halved into test-A and test-B, and the corpus fixes from the B32 judge added.

## Amendments

### Amendment 2026-11-06 09:07 CST: gate 1 (B34, B36 and a Henry arm), before any document is selected or scanned

Henry approved gate 1 (relayed by the main session; his words: "Up to $80 but you won't use all right? You said $22.
If you truly think this is a direction worth considering ... then go ahead"). The gate is re-sequenced: B36 does not
need the 7,000-post training data, so gate 1 runs only B34, the B32 judge's corpus fixes on the test-A and calib
splits, B35's inputs for the test-A posts, and B36. The full 40-shard build (2a) and the training data (2b) wait for
gate 2, after Henry sees B36. Rules are in the docstrings of `experiments/b34_length.py` and
`experiments/b36_transfer.py`, committed with this amendment. Changes to the design above:

- **B35 for test-A follows B28 exactly** (Sonnet NOTES, B27 rewording, the 50% dose, Sonnet's DRAFT post), not one open
  extractor: B36 then differs from B30's T50 only in the authors (never seen) and the length (whole posts of 1,500 to
  3,000 words, rewritten section by section). The open extractor of section 5.3 stays the plan for gate 2's training
  data.
- **B36 cells:** D300, Dfull, C300 and Cfull on 32 test-A posts (C is CAI-old). Primary tests, Holm over two: Cfull
  against Dfull on the AI share (Wilcoxon) and C300 against Cfull on the label (McNemar). Decision bands: transfers if
  Cfull reads Human on 16 or more of 32 with claims supported 0.90 or more and length 70% or more of D; partly 8 to
  15; not 7 or fewer.
- **Henry arm (Q4), new:** B30's rewriter on the prose sections of Henry's two published posts
  (ai-engineering/part1 and bandits/part1), section by section, scanned before and after as whole posts and as
  sections of 150 words or more, claim-checked against the original. Code, tables and figures are left out as in B15.
  Confidentiality: one post calls client work a "diabetes coaching agent" on purpose; a filter deletes any output
  sentence that introduces a health or medical term absent from its input section, and the Guard blocks new names.
- **Generation:** batched transformers generation with B30's settings on an L40S (`experiments/modal/lf_rewrite_hf.py`;
  per-row Guards, per-batch seeds). vLLM and the Guard port wait for gate 2.
- **Credits:** B34 about 420, B36 about 1,500, Henry arm about 270; the scan script stops above 2,500.
- **Modal:** about $5 estimated (B34 continuations about $0.7, B36 and Henry generation about $3 to $4), inside the
  remaining free credit; a running total is kept, and a run that would cross the free credit stops for a message.
