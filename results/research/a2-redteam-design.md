# Red team and reviewer #2: attempt 2 design (2026-11-06)

Artifact: `docs/specs/2026-11-06-attempt-2-design.md` (line numbers below refer to it unless a file is named).
Reviewer: general-purpose agent, 2026-11-06, briefed as reviewer #2 and red team. I read the design, the attempt-1
closeout, `CLAUDE.md`, the notebook, report sections 37 to 39, the five `a2-*` research reports, the B36 to B38
scripts, and the raw result files. Every number marked "recomputed" comes from a local script run on
`results/b36_*`, `results/b37_*`, `results/b38_*` and `results/a2_rechecks.json` with the project's `.venv` Python.
Nothing ran on Modal or Pangram, no `.env` was read, and no repo file other than this report was written.

Goal behind the task: Henry should publish posts that are his and worth reading. The design spends about 6,000 to
7,500 Pangram credits, several hours of his reading and possibly paid compute. This report asks where that would be
wasted, misleading or against the project's rules.

## Bottom line, ranked by how much it should change Henry's decision

1. **Gate G1 can barely stop, and the one experiment that tests the real product sits behind a band that is close to
   unreachable.**
   - A1's top band (lines 323) is unreachable under the design's own expected effect.
   - A2-K's band is already one quarter met by data on hand.
   - The Stop row needs four conditions at once.
   - A5, the pilot on Henry's own post, runs only from G1 rows 1 and 2.
   - Phase 1's roughly 4,000 credits therefore mostly confirm a phase 2 that would happen anyway, and the product test
     probably never runs.
2. **Free checks on existing data already answer or undercut four cells.**
   - The Henry-arm triage rule is refuted by B37's own scans: it would revert 11 of 12 sections, and 10 of those 11
     rewrites read lower than the originals.
   - The A2-N copy ban will probably fail the claim gate, and a cell that fails the gate is not scanned (line 545).
     When that happens, G1 has no row for it.
   - D100's scan and A7's D cell drive no decision; together they cost about 1,400 credits.
3. **The budget is understated, and the binding limits are not the ones the design tracks.**
   - Canaries cost about 2x the design's figure, the A1 Henry arm is not costed, and phase 1 lands near 5,000 credits
     rather than 4,100.
   - At full scope the program exceeds 8,717 credits.
   - Whether Pangram's Professional credits renew or expire monthly is never asked, and it changes the whole budget
     picture.
   - The most likely overruns are 4,000 to 6,000 Sonnet calls on Henry's shared Claude account, which means 17 to 25
     hours of wall time, and Modal's November credit, which is counted twice.
4. **Rule problems.**
   - A4's 600-credit Pangram "development budget" makes Pangram choose among weights and configurations. That is
     outside the 13:08 exception, and it is not on Henry's decision list.
   - Henry's two published posts are development data but are listed in the final test.
   - The unpublished part 2 draft carries client-domain material and would go to Pangram and Claude.
   - Attempt-2 output files (`results/a1_*`, `a2_*`) are not gitignored in a public repo.
   - A4's training corpus has no stated exclusion of B39 reserve owners.
5. **The stop rule and the final-test criterion contradict each other.**
   - Phase 2 continues to A7 unless the median share is above 0.20.
   - A7 needs 32 of 50 posts Human, which needs a median near 0.05.
   - A route at a median of 0.12 to 0.20 would spend 1,450 to 2,300 credits on a predictable failure.

The design is careful in many places: paired same-day scans, pre-registration, a planted-error audit and a reserve
held back. The problems are in how the decision rules fit together and in the costs, more than in the individual
experiments.

## 1. Decisiveness: does every outcome change what happens next?

### 1.1 A1's top band is unreachable under the design's own prior

- Band (line 323): C100 median share at most 0.15 **and** Human on at least 10 of 32 means "content route open".
- The design's expected effect is 0.05 to 0.15 (line 313).
  - C0 on these posts had a median of 0.365 (recomputed from `b36_pangram.jsonl`); C1 is likely 0.30 to 0.35.
  - A drop of 0.05 to 0.15 lands C100 at a median of about 0.15 to 0.30, so it fails the median half of the band.
- Per-window model. B37's red team found that per-window Human rate drives whole posts. This is a model estimate,
  not a measurement.
  - C50's measured 300-word Human rate is 11 of 32 (0.34).
  - Getting 10 of 32 whole posts Human (posts of about 5 windows) needs a per-window rate of about 0.80: 0.8^5 is 0.33,
    which gives 10.5 of 32 (recomputed).
  - At short length B30 went from T50 13 of 19 to T100 19 of 19. Scaled by the observed unseen-writer penalty
    (0.34 / 0.68 = 0.5), C100's per-window rate would sit near 0.5. That gives about 1 whole post Human of 32.
- Consequence: A1 in practice chooses between "helps, not enough" and "does not help". Those two outcomes differ at G1
  mainly in whether A5 runs and which notes doses go into R2's training pairs. Answering that costs 1,888 credits plus
  up to 400 for L.
- Bands not covered:
  - C100 median at most 0.15 with fewer than 10 Human. A median of 0.14 with 8 posts under 0.10 is plausible.
  - C100 significantly **worse** than C50.

### 1.2 A2-K's band is one quarter met, and passing it does not show a judge is worth building

- Recomputed on B38's data, gated oracle at k = 4 per post:

  | Post | Share |
  |---|---|
  | p7dd69444fe | 0.040 |
  | pdcbac3657f | 0.203 |
  | pf688f8ab80 | 0.244 |
  | p3f93342833 | 0.271 |

  One post of the four is already under 0.10. "At least 2 of 4 under 0.10 at k = 12" (line 351) therefore reduces to
  "one of the other three crosses".
- Zero-share tries are common but mostly break the gates. 13 of 55 candidates read 0.04 or less, but only 5 of the 41
  gate-passing candidates do. Within-section try standard deviation (SD) is 0.19 (pooled, recomputed). The minimum of
  12 draws from a distribution like that falls a long way, so a pass is driven by order statistics.
- A pass measures the oracle, not a judge.
  - B38: J1 captured about 40% of the gated oracle's gain (0.288 against random 0.340 and oracle 0.213), and no better
    than the free least-copying rule (`b38_judge.json`, `best_of_4_c1_gates`).
  - Derived post shares carry about 0.06 of error (report section 39, item 5), right at the 0.10 line.
- So the band routes toward building a judge on evidence that does not bear on whether a judge can be built.
- What A2-K does measure well: the product ceiling **if Henry lets Pangram choose in his own use** (decision 4).
  Framed that way it is informative, but that decision has to come first.

### 1.3 G1 is incomplete, overlapping, and its Stop row is almost unreachable

Table at lines 375 to 382.

- **Uncovered:** "content helps, not enough" combined with an A2-N null and no judge (ceiling above 0.10 and Z5
  failing) matches no row.
- **Uncovered:** A2-N not scanned because it failed the gates (section 2.1). The table only has "causal" and "null".
  A2-N's intermediate outcomes are also undefined: a drop of 0.08 or more with p of 0.05 or more, or a significant drop
  under 0.08.
- **Overlaps:**
  - "Content route open" with an A2-N null and a judge matches both row 1 (A5) and row 5 (judge).
  - "Content does not help" with a null, a judge and leakage matches both row 3 and row 5.
  - No precedence is stated.
- **Row 5's "or":** "ceiling under 0.10, **or** Z5 passes" lets a noisy Z5 pass send phase 2 to a judge even when
  A2-K shows the oracle itself cannot reach 0.10. That contradicts R6's own condition (line 232: "built only if the
  ceiling is under 0.10").
- **Stop row:** it needs "content does not help", an A2-N null, A2-K failing, Z5 failing and "plan" all together.
  Given 1.1 and 1.2, it is close to unreachable, so the program has no practical exit at G1.
- **Undefined term:** the table says "ceiling under 0.10", but A2-K's band is "2 of 4 posts", and it does not say
  which one the table means.

### 1.4 Cells whose outcome changes nothing

| Cell | Credits | Why it does not decide anything |
|---|---|---|
| D100 scan (secondary contrast) | 544 | Appears in no band and no G1 row. B28 already measured Sonnet at 100% against 50% notes (1/18/0 against 0/6/13). Also a cross-day comparison against B36's D50 (line 318) |
| A7 D cell | about 850 | The A7 criterion is absolute (32 of 50). D's share (about 0.81 in B36) is not needed for pass or fail |
| Z1 to Z4 | 0 credits, thousands of Claude calls | The design says they "do not change phase 1's design" (line 259) |
| A3 genre probe | about 450 to 650 | The scoring form is already fixed as prose-only before A3 runs (line 253). B38 already showed the math effect (0.41 against 0.24, same day). A3 changes reporting, not a route |
| A2-O | about 200 | "Markedly more Human" (line 357) has no threshold and no measure (label count or share?). Arm (b) has no content-retention gate, so a "leakage" result would promote R7, which fails "keep the content" for the same reason R5 was rejected (line 219) |
| Caching canary | about 14 a session | The perturbed copy is fixed (line 281), so from session 2 on it is as cacheable as the others. Whitespace may also be normalized away. Section 5.4 |
| A1 Henry arm, original and C1 | about 120 | Repeats B37's same-day C1 scan of both posts (bandits 0.08, context-engineering 0.24). Only triage is new, and section 2.2 refutes it for free |

## 2. Confounds and one-variable violations

### 2.1 A2-N: the copy ban changes length and claim support too, and will probably fail the gates

Recomputed on B38's 55 scanned candidates, binned by 8-word copying from the input:

| Copied | n | Mean share | Words over input | Claim support | Gate-passing n | Gated share |
|---|---|---|---|---|---|---|
| under 0.10 | 7 | 0.059 | 0.66 | 0.84 | 2 | 0.205 |
| 0.10 to 0.20 | 9 | 0.101 | 0.70 | 0.90 | 6 | 0.152 |
| 0.20 to 0.30 | 14 | 0.399 | 0.73 | 0.91 | 10 | 0.426 |
| 0.30 to 0.45 | 10 | 0.282 | 0.88 | 0.96 | 9 | 0.277 |
| 0.45 and over | 15 | 0.584 | 0.83 | 0.97 | 14 | 0.554 |

- In natural variation, low copying comes with shorter text and lower claim support (copying and claims correlate
  +0.57, `a2_rechecks.json`). Pangram rewards that: section 39 found candidates under the claim floor average 0.195.
  So "copying causes share" and "dropping content causes share" are not separated.
- A forced ban to under 0.05 (line 339) pushes outputs into the regime where 5 of 7 natural candidates fail the
  gates. Line 545 then says the cell is not scanned. The likeliest outcome is that A2-N is never scanned, and G1 has
  no row for that (1.3).
- B38's within-section slope (0.61) comes from copying between 0 and 0.94 (mean 0.34). The "0.18 if causal"
  expectation extrapolates to 0.05, the region where only 2 gate-passing points exist.
- Fixes:
  - Pre-register what happens if the cell fails the gates.
  - Match N against C on length and claim support: report both and add them as covariates.
  - Use a graded penalty with 2 or 3 strengths, so there is a dose-response rather than one extreme cell.
  - Or replace the ban with ORPO-style training later. The base-models report itself prefers a soft penalty and
    matched copy rates.

### 2.2 The triage cell is refuted by data already on hand

- Rule (line 310): keep verbatim any section whose C1 rewrite copies more than 30% of the original.
- B37 scanned the same C1 rule on the same posts. Recomputed from `b37_texts.jsonl` and `b37_pangram.jsonl`:
  - Copying from the original is above 0.30 on 11 of 12 scanned sections. Only context-engineering s1 (0.25) and
    bandits s5 (0.01) fall under it.
  - On 10 of those 11 the rewrite read lower than the original. Examples: context-engineering s6 1.00 to 0.41,
    s7 0.97 to 0.70, s2 0.39 to 0.10; bandits s1 0.67 to 0.00, s4 0.32 to 0.00. The one exception is bandits s6
    (0.00 to 0.30).
- So the rule would put most of the AI-reading original text back. It costs credits to confirm something the data
  already show.
- The selector that is legitimate and free is Henry himself: he knows which sections he wrote and which Claude
  drafted. Keeping his own sections verbatim uses no Pangram.

### 2.3 A1: what differs between C100 and C50 besides the notes dose

- **Generation dates and instruments.**
  - C50 (B37's C1) was generated and picked on 2026-11-06; C100, its claim checks and D100 are new.
  - `humanizer.llm` passes the alias `--model sonnet` and keys its cache on the alias (`src/humanizer/llm.py` lines
    38 to 44). C50's prune and claim calls come from the cache (the old Sonnet), while C100's call whatever the alias
    resolves to on the day.
  - If the alias moved, the drafter and the checkers differ between cells.
  - Fix: pin a full model ID and log the resolved model per call.
- **Pick fallbacks.** C1 fell back to "most supported claims" on 7 of 84 sections for C50 (recomputed). With all the
  notes there are more claims to support, so the 0.90 floor will bind more often for C100. The fallback favours
  copying, which raises share. Report fallback counts per cell and run a sensitivity test without fallback sections.
- **Length.** Shorter reads more human (a lesson of attempt 1). The primary contrast has no length rule or covariate.
  Pre-register the length ratio against D and against the human post as a reported covariate.
- **Copying from the human original.**
  - At dose 50, C copies a median 1% from the human post (maximum 6.5%) and that does not track share (Spearman 0.01,
    recomputed).
  - At dose 100, B30 copied more from the essay (3.5% against 1.3%, `a2_rechecks.json`).
  - Both base models (OLMo 2 and Gemma 4) trained on Common Crawl, which may contain these FineWeb posts, so
    memorization is possible. Keep B36's exclusion rule (more than 15% copied from the human post) and apply it to
    S50 too. The design does not restate it.
- **Construct.**
  - "All the notes" means 76 Sonnet-extracted notes per post on average (`b36_inputs.jsonl`), taken from the finished
    human post. That is far denser than anything an author writes before drafting; B21 found Henry could not recall
    his specifics.
  - So A1 is an upper bound. A negative is informative; a positive overstates A5's prospects.
- **What A1 tests.** The primary contrast tests a rewriter on a Sonnet draft. The product section 1 favours is
  "base-model writer from Henry's points" (line 76), which is cell L, and L is scanned only if it reaches 60% of
  length. B37's L reached 28%.

### 2.4 S50 against C50 is a package comparison, but the band reads it as a recipe verdict

- S50 differs from C50 in four ways:
  - the model (Gemma-4-12B against OLMo-2-13B);
  - the unit (500-word chunks against sections of at least 600 words), which also gives more pick opportunities per
    post;
  - the Guard, which is not specified for Smaug;
  - the prompt format.
- The band (line 327) concludes "phase 2 starts from Smaug's weights or recipe". If S50 wins because of chunk size,
  the right lesson is "use smaller chunks", which costs nothing.
- Fix: either add C50 at 500-word chunks (about 450 credits), or have the band name only "Smaug's weights as the
  starting point".

### 2.5 Comparisons across days that the method rules forbid

- Line 248 requires same-day scans of every arm of a comparison. Three comparisons break it:
  - A2-N reuses B38's scanned unconstrained seeds for 14 of its 28 sections. The 500-credit figure only fits if they
    are not rescanned.
  - A2-K mixes 8 new seeds with 4 scanned on 11-06.
  - D100 against D50 compares a new scan with B36's scan.
- The canaries make this defensible, but the design should say it is an amendment, or budget the rescans: about 170
  credits for A2-N and about 550 for D50.

### 2.6 A2-O's premise is weaker than the summary claims

- Summary item 1 (lines 27 to 28) says attempt 1's "AI-sourced facts read AI" is "more likely AI wording and generic
  detail leaking". Two attempt-1 results it does not cite here argue against that:
  - B5: rewording the AI facts changed nothing (notebook row B5).
  - B6: cutting generic facts was no better than a random cut.
- Sun et al. (adjacent-fields report) also finds the content fingerprint survives paraphrase (91.4%).
- Its own section 3.4 says the opposite of the summary: "Experts cite vocabulary, while Pangram reads content"
  (line 177).
- IdeaLens's 8% result comes from human writers who added their own specifics. The literature report itself flags
  this, and the Guard forbids it here.
- So A2-O has a low prior, and its "leakage" branch leads to a route (R7) that loses content.

## 3. Rules

1. **A4 makes Pangram a selector outside the 13:08 exception.**
   - Line 404: "Otherwise the gates, plus a fixed development budget of 600 credits on calibration posts only."
   - If Pangram scans are A4's development measure, they decide among checkpoints, the RL stage, ORPO settings or
     decoding. That is Pangram choosing weights.
   - The exception covers a local judge trained on Pangram labels, not Pangram scans steering training.
   - The design flags DPO on Pangram labels as Henry's call (decision 5), but not this, and it is not in section 13.
   - Fix: define the 600 credits as monitoring only, with no decision rule attached, or list it as a decision for
     Henry.
2. **G1 itself chooses routes, and so writers, by Pangram on development data.**
   - Attempt 1's gates did the same, so it has precedent. But the rule's wording ("never select a prompt, weight or
     writer") does not allow it.
   - Say so plainly in the design, and have Henry ratify it: Pangram decides among routes on development data, and the
     only held-out claim is A7.
3. **Henry's published posts are development data, not test data.**
   - They were scanned in B15, B36, B37 and B38. They are in the 1,534 labels behind J1 and Z5 ("grouped by
     author/site/henry", `b38_judge.json`). The A1 Henry arm scans them again.
   - Listing them in A7 (line 423) invites reading them as held out.
   - The only fresh Henry text is `blog/series/ai-engineering/part2.draft.html`, about 9,000 words after stripping
     the HTML (`part2.html` is a 29-word stub).
   - Fix: reserve the draft for A7 only, with Henry's yes, and never use it in development.
4. **Confidentiality of the part 2 draft.**
   - A grep count, without reading the content, finds 32 client-domain terms in `part2.draft.html` (38 in the
     published part 1).
   - Decision 7 (line 570) would send it, plus Henry's "research notes", to Pangram (a third party) and to Claude.
   - The design's confidentiality check (line 488) covers outputs only. B22's precedent: Henry keeps that project's
     records out of third-party tools.
   - Fix: decision 7 should say inputs go to Pangram and Claude. Henry should screen the draft and his notes before
     any scan.
5. **The public repo.**
   - `.gitignore` covers `/results/b25_*.jsonl` to `/results/b3[2-9]_*.jsonl` only. `git check-ignore` confirms that
     `results/a1_texts.jsonl` and `results/a2_texts.jsonl` are **not** ignored.
   - Under attempt 2's naming, rewrites of Henry's posts, corpus-derived texts and B39 outputs would be committable to
     the public GitHub repo.
   - Fix: add `/results/a[0-9]*_*.jsonl` (and raw folders) to `.gitignore` before the first A-series file exists.
6. **The B39 reserve and A4's corpus.**
   - A4 needs "3,000 posts from 600 or more train-split sites" (line 393). The pilot has one post per site, so this
     needs a new build or the extra kept posts. That build is not costed.
   - The base-models report's pipeline says "Henry's posts and test-A sites stay out" (`a2-base-models.md` line 291)
     and is silent on test-B.
   - B32's judge found owners shared across splits. The reserve file covers pilot IDs and their merged groups only.
   - Fix: pre-register that A4's corpus excludes every merged owner group touching buckets 95 to 99, and dedupes
     against reserve text hashes or MinHash signatures, computed without a person or judge reading the texts.

## 4. Statistics

1. **The A1 power figure borrows a standard deviation from a different contrast.**
   - The 0.12 is the SD of C minus D on the same post, where the two are correlated at 0.59 (`a2-measurement.md`
     section 0.3).
   - C100 minus C50 are two rewrites of two different drafts, each with try-to-try noise. B38 alone gives an SD of
     0.11 to 0.17 for the difference between two random picks of the same post (recomputed).
   - With a realistic SD of 0.15 to 0.20, the minimum detectable effect at n = 32 and 80% power is 0.076 to 0.101
     (recomputed), not 0.06. The low half of the expected 0.05 to 0.15 is underpowered.
2. **A2-N's unit contradicts section 3.5.**
   - The design says "count posts, not sections" (line 185), then analyses 28 sections in 8 posts (line 342).
   - With an intraclass correlation of 0.25 and 3.5 sections per post, the effective n is about 17.
   - Try SD is 0.19, and with two seeds a side the difference SD stays about 0.19. The minimum detectable effect is
     about 0.13, not 0.07.
   - The band (drop of at least 0.08 at p under 0.05) catches a true effect of 0.08 only 42% of the time, 0.12 75% of
     the time, and 0.18 98% (recomputed by simulation).
3. **Z5's benchmark is the wrong number.**
   - 0.778 is the least-copying rule's pair accuracy over **all** 63 within-section pairs (`b38_judge.json`,
     `explore_post_hoc.best_of_4.least_copied`), not under the gates as line 267 says.
   - The 63 pairs come from 55 candidates in 14 sections, so they are not independent.
   - "Beats" has no margin and no interval, so a coin-flip win sends phase 2 to the judge route through row 5's "or".
4. **Multiple comparisons.**
   - G1 conditions on about five contrasts, each at 0.05 with no correction: A1, the S50 band, A2-N, A2-K and Z5.
   - Under all nulls, the chance of at least one false "effect" is about 23%. Most errors are cheap, but the S50 band
     changes the phase 2 base model.
5. **The final criterion.**
   - The arithmetic is right: P(at least 32 of 50 | 0.5) is 0.033, with power 0.86 at 0.70 and 0.34 at 0.60
     (recomputed).
   - What it measures is not Henry's product:
     - B39 posts are 2019 to 2022 FineWeb blogs, only 4.5% tagged technical (notebook row B32).
     - The drafts come from notes Sonnet extracted from the finished human post.
     - Henry's genre (code and math) and his real drafting conditions are absent.
   - A pass would say "the pipeline humanizes Sonnet posts built from complete notes of unseen bloggers' posts".
     Report it as that, and pair it with a product measure (section 7).
6. **The stop rule contradicts the final bar.**
   - Phase 2 proceeds to A7 unless the development median is above 0.20 (line 547).
   - 32 of 50 Human means a true Human rate of about 0.65 to 0.70, which needs most posts under 0.10, so a median
     near 0.05.
   - Set the go rule for A7 from the A7 bar, for example a development Human rate of at least 0.65 on calibration
     posts, or A7 will spend 1,450 to 2,300 credits on a foreseeable failure.

## 5. Quality and faithfulness

1. **A veto-only G1 read stops little.**
   - The bar (line 464) is that an arm is out if it loses at least 8 of 10.
   - Recomputed, the chance of a veto is:

     | True win rate | Chance of veto |
     |---|---|
     | 0.50 | 0.055 |
     | 0.40 | 0.17 |
     | 0.30 | 0.38 |
     | 0.20 | 0.68 |

   - A route Henry clearly dislikes (winning 30%) passes G1 62% of the time.
   - G1 also reads outputs of the **old** B30 rewriter (C100, C50, N). The phase 2 route (R2, A4) is first read at
     A7, after about 2,000 or more credits.
   - Fix: add a quality read on A4's development outputs before any A7 credits are spent.
2. **The pair counts disagree.**
   - A1 sends 20 pairs (line 328) and A2-N 10 (line 347): 30 pairs plus controls.
   - Protocol Q budgets 20 pairs at G1, 1.5 to 2 hours (line 562).
   - At 400 to 700 words a side, 30 pairs is about 33,000 words, so 2.5 to 3.5 hours.
3. **The read is not truly blind.**
   - Frequent LLM users spot AI articles about 99% of the time (adjacent-fields report, Russell et al.), and Henry is
     one.
   - Draft against rewrite will mostly be identifiable, so his choice partly measures "reads less AI", the thing
     already measured.
   - One rater is the only rater, and the controls measure consistency, not validity.
   - Say this in every quality claim. Consider the paid second rater (about $60 to $100) only for A7.
4. **The faithfulness gates may reject clean text, and the audit may stall A1.**
   - The sentence-level gate allows at most 2% unsupported sentences (line 484). A 1,500-word output has about 80
     sentences, so a checker with a 3% per-sentence false-flag rate fails most clean outputs.
   - The measurement report puts checkers at 75 to 80% balanced accuracy.
   - The audit bar is at least 29 of 30 per type (line 290) for every one of 10 types, including semantic types
     ("a wrong claim", "new framing"). That is likely unreachable, and "failing types are fixed and re-audited before
     A1" can block phase 1 open-endedly.
   - Fix: set the gate threshold from the audit's measured false-positive rate on the 60 clean controls. Apply the 29
     of 30 bar to the deterministic types, and a stated lower bar to the semantic ones.

### 5.4 The canary protocol (A0)

- A fixed perturbed copy is cacheable after its first scan. Use a fresh perturbation each session, such as a
  session-specific token-level change; a whitespace edit may be normalized by `textutil` or by Pangram.
- If Pangram caches by hash, frozen canaries would hide a model change. That is exactly the failure the canaries are
  for.
- The "0.02 or any label change" rule (line 284) already fired across days on Henry's context-engineering s5 (AI on
  11-05, then Mixed at 0.78 on 11-06; `a2-measurement.md` section 0.2). Canaries chosen to sit near the boundaries
  (0.09, 0.19, 9.5%) will trip it the most. Pre-register what a trip means for comparisons that are already same-day.

## 6. Budget realism

### 6.1 Pangram credits

Recomputed from B36 to B38 per-file charges.

| Item | Design | Re-estimate | Basis |
|---|---|---|---|
| Canaries per session | about 70 | 116 to 135 | Human posts of 2,040 to 2,789 Pangram words, rewrites 1,359 and 1,628, Sonnet post about 1,727, splice 1,333, perturbed copy |
| Phase 1 canaries (4 sessions) | 280 | 470 to 540 | |
| A1 Henry arm | not costed (A1's 1,890 is exactly D100 + C100 + C50 + S50) | about 150 to 250 | Context-engineering 4,481 words, bandits 2,663 stripped, plus rewrites and triage |
| A3 | 450 | 450 to 650 | 5 math posts x 3 forms plus 4 code posts x 2. The bandits post with LaTeX alone is 51 credits |
| Same-day rescans (2.5) | 0 | 170 to 720 | If the rule is kept |
| **Phase 1** | about 4,100 (the listed items actually sum to 3,990, or 4,510 with L and A2-S) | **about 4,900 to 5,600** | |
| **Program, full scope** | 6,200 to 7,500 | **about 7,000 to 9,000**, including canaries for later sessions | Above 8,717 at the top |

Savings that cost no decision: D100 (544), the A7 D cell (about 850), the Henry arm's original and C1 re-scan (about
120), the triage cell, and A3 cut to Henry's two posts in three forms (about 150). That is about 1,600 to 1,900
credits, enough to cover the overruns.

**Unasked and possibly decisive: do Professional credits renew or expire monthly?**
- The Pangram report cites a dashboard allowance of 1,500,000 words a month, about 15,000 credits
  (`a2-pangram.md` line 68).
- The notebook records 15,000 credits on the upgrade (2026-11-05).
- If the allowance renews around 12-05, then 8,717 is not a lifetime pool. The real constraints become:
  - unused credits may expire before A7, since A2 and A4 slip into December;
  - each extra month of Professional is Henry's money.
- Either way, the design's "of 8,717" framing and its cut order rest on an assumption nobody checked. Check the billing
  page before approving.

### 6.2 Other resources

| Resource | Design | Likely | Why |
|---|---|---|---|
| Modal, November | about $9 for phase 1 (of $9.03 left) | $10 to $13 | C100's 4 seeds at B36/B37 scale ($3.7 for 2 seeds, $6 for 2 seeds plus L) about $5 to $7; S50 $1 to $2; A2 $3; Z5 under $1. The base-models report also counts November's $9 toward A4 (`a2-base-models.md` lines 411 to 412): double counted |
| Modal, December ($30) | A4 $10 to $15 | $15 to $25 plus A2 and A7 | The $10 to $15 excludes claim-check compute ($5.60 line in `lf_cost.py`, per the same report) and the corpus build for 3,000 posts (uncosted) |
| Claude calls on Henry's shared account | not budgeted | 4,000 to 6,000 Sonnet calls, about 17 to 25 hours of wall time at 4 workers | C100 about 670, S50 about 870, L about 200, planted audit 400 to 700, A2 about 400, Z2 and Z3 1,500 to 3,000. A4 adds about 6,000 more (base-models report: 25 hours). This competes with Henry's work usage |
| Session time | phases 0 and 1 in about 3 working days (line 554) | 2 to 4 weeks | A2 may wait for December's Modal reset (line 521), 25 days away; the Claude-call wall time; the audit's re-audit loop |
| PC | A4 only | | Phase 1 generation could run on the PC for free (C100 at 7.5 tokens a second is about 11 hours), but the PC is shared with umwelt; not considered |
| Henry's hours | 5 to 10 | 8 to 12 | 30 pairs at G1 rather than 20; A5's notes plus read; reading every flagged sentence at A7 (line 429), which is uncosted |

**Most likely to overrun: the Claude-call wall time and the session time box, then Modal November.** Pangram credits
come next, but they have the cheapest fixes (the cuts above).

## 7. Altitude: does the program serve the goal behind the goal?

- **A cheaper, more direct program:** the A5 product pilot first, on Henry's next real post, with two additions.
  - (a) A reference cell: Henry writes the post himself, with Claude only commenting, no Claude words. Human posts read
    Human 10 of 10 (B34), so this cell sets the bar every tool has to beat on Henry's time per post.
  - (b) The R1 cells from line 412.
  - Cost: about 150 to 300 credits and his drafting time.
  - It tests the actual goal (posts that are his) rather than a lab proxy. Its biggest risk, that Henry will not
    write per-section notes, is one A1 cannot reveal.
  - Section 1.4 of the design already says the durable lever is "his content, in a human register". The plan's
    structure gates that lever last.
- **Decide whether Pangram passing is the right target, and in which role, before phase 1.**
  - In Henry's own use, Pangram as a final acceptance check ("regenerate until it reads Human, then he reads it") is a
    legitimate product design. Decision 4 is close to this.
  - If he allows it, the product criterion becomes the per-try pass rate times quality times cost per try. A2-K's
    oracle at k = 12 then measures it directly.
  - The research rule (Pangram held out) still governs claims about the method, but the product question changes
    which experiments matter.
- **"The detectors they use"** (line 69) is broader than Pangram. A free check of the final outputs on one or two
  other detectors would test the goal's wording. It needs Henry's yes for any account.
- **Moving target.** Pangram can change the model behind `pangram-4` silently (line 113). A multi-week program tuned
  to 4.1 should front-load whatever is durable (Henry's content and workflow) and leave detector-specific tuning
  (judge, selection) last. The current order does the reverse.

## 8. Evidence quality: weak inputs that carry weight

| Input | Weakness | Where it carries weight |
|---|---|---|
| IdeaLens: 92% flagged from human plans; 8% for human stories from AI plans | Numbers came through a WebFetch summarizer and were not cross-checked to raw files (`a2-literature.md` line 169; the design stars it as checked). GPT-5.6, about 500-word stories; human writers added specifics | "Claude cannot do the writing, even as an editor" (line 26) closes routes; A2-O's premise. Contradicted by B5 and by the design's own section 3.4 |
| arXiv 2610.21062, "Opus 5.5 with a whole paper flagged 22 to 25%" | Pangram 4.0 by date; passages "many under 100 words"; the paper says Pangram "depends much more on length" | Supports the drafting-workflow product (lines 73 to 74). Also conflicts with IdeaLens's 92%; the design uses each for a different conclusion without reconciling them |
| Smaug-Humanizer | Three screenshots, Pangram version unstated | 448 credits for S50, and a band that can switch phase 2's base model |
| AIHB copy null (Spearman -0.02) | Agent's recount; operator unknown; commercial instruct tools at about 290 words | Sets A2-N's "near 0" expectation. Different regime; it should carry no weight |
| $200 monthly API credit | Pricing page against a July help article; untested | Turns the budget into a "dashboard reserve" (line 515); A7 cost (line 432) |
| Monthly dashboard renewal | Never examined | The whole credit framing (section 6.1) |
| vLLM about 30x on the PC | Estimate | A4's feasibility: otherwise about 250 hours of PC generation |
| Paired SD 0.12; 75% try-to-try variance | One contrast (C against D); 14 sections in 4 posts | A1 and A2-N power claims (section 4) |
| Expected effects (A1 0.05 to 0.15, A2-N 0.18) | Short, seen-writer data; a slope extrapolated outside the gated data | Band thresholds |
| Argument Collapse, reader study | Summarizer read, first half of the HTML (`a2-adjacent-fields.md` line 242) | A5's protocol and A7's reader estimate. Low stakes, as the design says |

## 9. Recommended changes, in order

1. Decide decision 4 (Pangram's role in Henry's own use) and check Pangram's monthly renewal and expiry before
   anything else. Both change which experiments matter.
2. Run A5 with a Henry-writes-himself cell on his next post, unconditionally and early. Gate the heavy R2 work on what
   it shows about his time and willingness.
3. Rebuild G1:
   - make it exhaustive with precedence;
   - add rows for "A2-N not scanned" and for intermediate results;
   - drop the "or Z5" override;
   - make Stop reachable;
   - set the A7 go rule from the A7 bar.
4. Cut D100, the A7 D cell, the triage cell and Z1 to Z4, and shrink A3. Recost canaries at about 130 a session and
   cost the Henry arm.
5. Fix A2-N: graded penalty strengths, length and claim covariates, and a pre-registered rule for gate failure. Move
   its unit to the post or report the effective n.
6. Fix the rules:
   - make A4's 600 credits monitoring only, or make it decision 11;
   - ratify G1 route choice by Pangram;
   - treat Henry's published posts as development;
   - reserve the part 2 draft and screen it with Henry;
   - extend `.gitignore` before any A-series file;
   - pre-register A4's corpus exclusions against B39 owners.
7. Pin the Claude model ID. Budget and schedule Claude calls explicitly, given the shared account.
8. Rescan the C50 and D50 baselines on the same day if those comparisons stay, or record the deviation as an
   amendment.

## What I could not verify

- Whether Pangram Professional credits renew, roll over or expire, and whether the $200 API credit is live. Both need
  Henry's account pages.
- Whether the `sonnet` alias has moved since 2026-11-06. I did not call the Claude CLI.
- The per-window projection in 1.1 is a model built from B36's C300 rate and B30's seen-writer rates, not a
  measurement. The A2-K pass probability in 1.2 is a rough independence estimate.
- Actual Modal costs for C100, S50 and A4. I used B36 to B38's reported spend as anchors.
- Claude-call counts are estimates from cell sizes. Whether `prune_one` makes exactly one Sonnet call per candidate
  was not checked line by line.
- I did not read the IdeaLens paper, arXiv 2610.21062 or Smaug's card myself. Their weaknesses above come from the
  research reports' own tags.
- I did not read the content of `part2.draft.html`, only a term count, and so cannot say what its client material is.
