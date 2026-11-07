# Red team of A1 (C100 against C50)

Date: 2026-11-06, after the A1 scan. Reviewer: red-team agent, working from the raw files only. Nothing was run on
Modal or Pangram, no repo file was edited, no .env was read.

The claim under attack: "With all of a writer's notes (C100), the rewriter makes whole posts by unseen writers read
Human on 26 of 30 (mean AI share 0.03), against 4 of 32 with half the notes (C50, 0.31): who chose the content is a
large lever at full length."

## Verdict in one paragraph

The number holds. I reproduced the primary contrast exactly from the raw files, every join checks, and the effect
survives every leakage, exclusion, fallback and covariate cut I could make (paired difference -0.26 to -0.28 in all of
them). What does not hold is the label "who chose the content." In both cells the human chose every point: the 50%
dose is a random half of the same notes (`b28_dose.dose`, seed "b28<id>"). What differs is how much of a
1,600-word draft Sonnet had to invent to reach the same target length. In D100, note words make up 75% of the draft;
in D50, 36%. On top of that, C100's input is exactly the kind of input the B30 rewriter was trained on, and C50's is
not. So A1 shows that a rewrite of a draft that is mostly a sentence-by-sentence paraphrase of a human post reads
Human. It does not show that Henry's own notes would do this, or that selection rather than AI padding is the lever.
It also does not show that the rewriter is needed, because D100 was never scanned. For the product decision, A1
supports the dense-notes workflow only at a note density close to writing the post. The cheapest way to tell the two
readings apart is a length-matched density test (section 1).

## Verification done first (external to the A1 code)

- Primary contrast recomputed from `a1_pangram.jsonl` and `a1_texts.jsonl` with my own script: n 30, mean
  difference -0.2707, bootstrap 95% interval -0.334 to -0.207, Wilcoxon p 2.8e-6, Human 26 against 4. These match
  `a1_content.json` exactly.
- Joins: the `sha` of all 64 scanned texts matches the hash of the text in `a1_texts.jsonl` (64 of 64). Shares in
  `a1_pangram_shares.json`, labels in the transcript and keys in `a1_blind.json` agree for all 70 rows.
- Same blinded batch for both cells (key 21:13, verdicts 21:17). Canaries: the Sonnet canary reads AI at 0.92, and
  the human canaries read 0.00.
- Scripts: `rt_a1.py`, `rt_a1_norm.py` and `rt_mem_norm.py` in the session scratchpad
  (`/private/tmp/claude-501/-Users-henryvu--claude-spares-spare-s6HQlu/cbf959c7-1fb4-4dcb-918e-c248455f5f2d/scratchpad/`).
  That folder is temporary. Each method is described below so the checks can be rebuilt.

## Findings, ranked by how much they should change the reading

### 1. A1 varies how much of the draft Sonnet invented, not who chose the content (changes the reading most)

- `dose50` is a fixed random half of the reworded notes, kept in order (checked: a subset in order for 32 of 32;
  `b28_dose.py` line 95, "the first round(d * n) notes of a fixed random order"). Nothing in C50's input was chosen by
  Sonnet except what it added to fill the length.
- Both drafts target the human post's length (B25's DRAFT prompt, "about {words} words"): D100 is 1,604 words and
  D50 is 1,681.
- How much of each draft is the notes:

  | | D100 | D50 |
  |---|---|---|
  | Note words / draft words | 0.75 | 0.36 |
  | Draft words in 8-word runs copied from its notes | 54.5% | 23.7% |
  | Draft sentences with a note at TF-IDF cosine 0.5 or more | 69% | 32% |

  (TF-IDF is term frequency times inverse document frequency, here on word unigrams and bigrams.)
- Dose and response inside C100, where every note was given: posts whose D100 is above the median share of
  note-backed sentences read Human 16 of 16 (mean 0.000). Posts below the median read 12 of 16 (mean 0.064).
  Spearman between note-backed share and C100 share is -0.51 (p 0.003). Note density (notes per 100 human words)
  tracks lower share in both cells: C50 -0.37 (p 0.04), C100 -0.34 (p 0.054).
- Why this matters for the product: two different workflows fit A1 equally well.
  - (a) Henry writes notes that add up to about three quarters of the draft's length. That is about 1,200 ordered,
    sentence-level notes for a 2,000-word post, close to writing it.
  - (b) Henry writes whatever notes he writes, and Claude drafts no longer than the notes support, so little of the
    draft is Claude's elaboration.

  These differ a lot in Henry's time. A1 cannot separate them, and neither could B28, where dose and fill were also
  confounded at fixed length.
- Test that separates them, cheap and local except the scan:
  - Sonnet writes from `dose50` at half the target length (no padding).
  - The rewriter runs on that draft with C1's pick.
  - Compare against C100 cut at section ends to the same word count, in one blinded batch.

  If the short-from-half drafts read like C100, the lever is AI elaboration, not note count. The comparison is length
  matched because Pangram's verdict is the flagged share of words, and shorter texts have fewer windows that can fail
  (B36, B37).

### 2. C100 is in the rewriter's training distribution; C50 is not

- B30's training pairs are "Sonnet writes the post from [all the essay's notes, in extraction order, reworded]" to
  the essay (`b30_rewriter.py` docstring). So D100 is built the same way as the training inputs. D50, two thirds of it
  Sonnet's fill, is not.
- The rewriter changes D50 less than D100:
  - It copies 22.0% of D50 against 14.0% of D100 (8-word runs, apostrophes normalized; see finding 6).
  - Sentence similarity to the input is 0.43 against 0.39.
  - Copying from the AI input is the best predictor of share in this project: B38 0.70. Within C100 it is +0.42
    (p 0.02).
- So "Pangram reads who chose the content" and "the rewriter works better on inputs shaped like its training data"
  are confounded in A1. Attempt 1 already showed the second effect at short length on seen writers: T100 19 of 19
  against T50 13 of 19 Human.
- Consequence for G1 row 4 ("rewriter v2 trained on all-notes pairs"): that only helps if Henry's real drafts look
  like all-notes drafts. If his notes are sparse, his drafts look like D50, and A1's C50 (0.31, Mixed) is the
  relevant prediction.

### 3. D100 was not scanned, so the rewriter's share of the effect is unknown

- What attempt 1 predicts for D100:
  - D100 copies 3.4% of its words from the human post (8-word runs, normalized; 3.2% unnormalized in
    `a1_content.json`).
  - That is the B28 S100 regime: 3.5% copying, 1 Human, 18 Mixed, 0 AI. A correction to the brief: S100 averaged 787
    words (`b28_dose.json` sonnet_checks). About 500 words is not right; L100 was 541.
  - B27 W (Sonnet from reworded notes, about 7% copying, 777 words) read 1 Human, 11 Mixed, 1 AI.
  - The regime that read Human is B25 D (raw notes, 11 to 64% copying): 8 of 13 Human. D100 is not in that regime.
  - Prediction: D100 reads mostly Mixed, about 0 to 2 Human of 32.
  - B25 to B28 recorded labels only, never AI shares, so D100's mean share cannot be predicted. It could be 0.2 or 0.7.
- How much this matters:
  - If D100 sits near 0.15, most of C100's result comes from the notes. The rewriter then mainly does the last step
    under 0.10, and its quality cost (G1 read) weighs more.
  - If D100 sits near 0.6, the rewriter does most of the work.
  - Either way, the product needs this number.
- The reason given for skipping it ("saves 544" credits) no longer binds: credits renew monthly (amendment 20:37,
  "Credits stop being the scarce resource"). Scan D100 in the S50 batch (about 520 credits).

### 4. C100 is a paraphrase of the human post in structure and content, but not in wording, and lexical leakage does not explain the effect

- Overlap with the human post (apostrophes normalized). The null is the same text against a different post in the
  set:

  | | D50 | D100 | C50 | C100 | null (C100) |
  |---|---|---|---|---|---|
  | words in 3-word runs | 12.3% | 19.7% | 14.6% | 24.6% | 2.0% |
  | 5-word runs | 3.7% | 7.5% | 3.8% | 9.2% | 0.0% |
  | 8-word runs | 1.6% | 3.4% | 1.1% | 3.9% | 0 |
  | sentence closeness (mean best TF-IDF cosine) | 0.142 | 0.199 | 0.149 | 0.222 | 0.049 |
  | sentence order against the human post (Spearman) | 0.79 | 0.85 | 0.80 | 0.87 | n/a |

- The notes follow the post's order (Spearman 0.82 between note index and the best-matching human sentence), and
  quoted speech passes through the reword step verbatim: 6% of reworded notes contain quotes, up to a third in one
  post. So D100 is Sonnet's sentence-by-sentence paraphrase of the post with headings added. C100 moves further
  toward the human post than its own input: 5-gram 9.2% against 7.5%, sentence closeness 0.222 against 0.199. That is
  what the rewriter was trained to do (paraphrase back to essay). The answer to the brief's question is yes: C100 is
  effectively a rewrite of a Sonnet paraphrase of the human post.
- Closeness tracks the share inside C100 but not inside C50:
  - Inside C100: sentence closeness -0.50 (p 0.004), 5-gram coverage -0.39 (p 0.03), and human 5-grams the rewriter
    produced beyond its input -0.53 (p 0.002).
  - Inside C50: none of these is significant (-0.30, -0.01, +0.15).
  - On the paired differences, the change in closeness does not track the change in share (-0.04). The paired
    difference is almost entirely C50's own share: Spearman -0.91.
- The effect survives every leakage cut:

  | Subset | n | Mean difference | 95% interval | Human C100/C50 |
  |---|---|---|---|---|
  | Pre-registered primary | 30 | -0.271 | -0.334 to -0.207 | 26/4 |
  | No exclusions | 32 | -0.276 | -0.338 to -0.215 | 28/4 |
  | C100 copies 5% or less of the human post | 26 | -0.276 | -0.347 to -0.207 | 22/4 |
  | D100 copies 3% or less of the human post | 22 | -0.280 | -0.361 to -0.202 | 19/4 |
  | No post with a fallback section (pre-registered) | 24 | -0.259 | -0.320 to -0.199 | 20/3 |

- Ordinary least squares (OLS) on the 60 paired texts:
  - The cell coefficient is -0.271 alone and -0.200 with sentence closeness and 5-gram coverage added, so about a
    quarter of the gap goes with closeness to the human post.
  - With length kept, claim support and copying from input added instead (the pre-registered covariates), it is
    -0.229.
  - Verbatim leakage does not break the claim. The structural paraphrase is the treatment itself, and that is why
    finding 1 matters.

### 5. Memorization: small, not seed-stable, cannot explain the effect, and not ruled out

- C100 produces human 8-word runs that are absent from its input on 1.34% of its words. C50 does so on 0.41%, and the
  null is 0. Across all 4 seeds of every section the figures are 0.96% and 0.43%. Of the 120 such 8-grams in the
  picked C100 texts, 61 are also absent from the raw (unreworded) notes.
- Reading the examples:
  - Most are the plain wording that Sonnet's rewording had replaced ("the main reason why knowledge workers are not
    engaged").
  - Some are world knowledge: the other two Korean kingdoms, the Arduino authors' names, the LiquidCrystal library.
  - A few are dialogue lines.
- No sign of seed-stable recall. Human 6-grams beyond the input that recur in all 4 seeds of a section: 4 in C100, 9
  in C50. Memorized text tends to come back across samples.
- Rare post-specific words: words that appear in at most 2 of the 93 B36 posts, are absent from the input and absent
  from the reworded notes. C100 has 4.4 per post (null 0.13) and C50 2.5 (null 0.16). Most are ordinary English that
  is rare in this corpus ("unemployed", "microphone"), so this test cannot separate recall from undoing synonyms.
- Even if every restored run were recalled, 1.3% of words cannot account for a 0.27 difference in flagged share.
- Not verified: a direct probe needs the OLMo-2-13B base model, for example exact-match continuation from human-post
  prefixes, or perplexity of the human post against a paraphrase. That needs Modal, which this review was not allowed
  to use.

### 6. Instrument defect: the copying tokenizer splits curly apostrophes and not straight ones

- `humanizer.checks.copying.WORD` is `[a-z0-9']+`. "I'm" with a straight apostrophe becomes one token, and "I’m"
  becomes two ("i", "m").
- Who uses which:
  - Human posts: 1,202 curly against 90 straight, curly in 29 of 32 posts.
  - Rewriter outputs: curly in all 32 C100 and all 32 C50 texts.
  - Sonnet drafts and notes: 0 curly.
- So every copy measure between a rewrite and its Sonnet input undercounts runs that contain contractions:
  copied_from_input, the C1 pick's "least copying", and B38's Spearman 0.70. So does every Sonnet-to-human measure.
  Rewrite-to-human measures (the 15% exclusion rule) are mostly unaffected.
- Size here, measured against the published numbers:
  - copied_from_input: C100 0.128 to 0.140, C50 0.196 to 0.220.
  - D100 from the human post: 0.032 to 0.034.
  - C100 beyond-input human 8-grams: 1.73% to 1.34%.
- It does not change A1. It does bias the C1 pick, which favors candidates whose copied stretches contain
  contractions. Fix: map ’ and ‘ to ' before tokenizing.

### 7. Pipeline differences between the cells: none that favors C100

- Code path:
  - C50 comes from `b37_gate2a.pick`. C100 comes from `a1_content._cell`. Both use the same `_assess` and
    `_pick_c1`.
  - The fallbacks differ only when no candidate passes the form checks: B36's pick for C50, the most supported
    candidate for C100. That never happened: C100 had 80 eligible and 2 form_only sections, C50 77 and 7.
- Generator:
  - The only change to `lf_rewrite_hf.py` between B37 and A1 is the path of the Guard's common-word list (sha1
    599c4afd, identical at both paths) and the batch halving on out-of-memory added for B37.
  - Batch sizes differ (C50 seeds 2 and 3 at 16, C100 at 8). Padding changes the draws, not their distribution.
  - All runs used the L40S on Modal.
  - C100 hit EOS (end of sequence) less often (78% of samples against 85%), so more C100 samples ran to the token
    cap before pruning.
- Covariates:
  - Length: 0.668 against 0.696 of the human post.
  - Claim support: 0.956 against 0.950.
  - Fallback sections: 2 against 7. Dropping those posts gives -0.259.
  - Seeds picked: both lean to seed 3 (28 and 29 sections).
- Time of day: C50 was generated and assessed on the morning of 11-06, and C100 that evening. The claim check calls
  Claude through the "sonnet" alias. I could not check which model answered each call (the cache was not read).
- Sectioning: C100's sections are cut from D100, a different draft, so section boundaries differ between cells (82
  against 84 sections). This is part of the treatment and has no direction.
- Not done by `analyze()`: the pre-registered fallback sensitivity analysis and the covariate model are absent from
  `a1_content.json`. My results are in the tables above, and both hold.

### 8. Exclusions and the paired set do not bias toward the claim, but the claim's numbers mix denominators

- The 2 excluded posts (C100 copies 22.8% and 17.2% of the human post) read C100 0.00 against C50 0.48 and 0.22.
  Excluding them shrinks the effect (-0.276 to -0.271). Their leak came through D100 itself (15% copied, quoted
  political speech kept verbatim by the reword step).
- The claim says "26 of 30 (0.03)" against "4 of 32 (0.31)". Paired on the same 30 posts it is 26 against 4, with
  means 0.034 against 0.305.
- Ceiling: 25 of 32 C100 posts read exactly 0.00. The paired difference is about equal to C50's share (Spearman
  -0.91). So the size, 0.27, measures how badly C50 did, not how much room C100 has. A1 cannot rank variants of C100.

### 9. External validity for Henry: what A1 licenses

- A1's notes and Henry's notes differ:

  | | A1's notes | Henry's notes |
  |---|---|---|
  | Source | Sonnet extractions of finished pre-2022 posts (Common Crawl 2019 to 2022) | Written before the post exists |
  | Genre | 25 of 32 personal posts, 7 technical, no code or math by selection | Technical research syntheses |
  | Amount | 76 notes, 1,196 words per post (61% of the human post, 75% of the draft) | Unknown, likely far sparser |
  | Order and wording | The post's own order, quotes verbatim | His own |

- Henry's own evidence is the closest to his use, and it is mixed:
  - His two posts rewritten by the same rewriter read 0.08 Human (not publishable) and 0.24 Mixed (B37).
  - Math as LaTeX adds about 0.17 (B38).
  - The technical subset of A1 is small: C100 6 of 7 Human, C50 shares 0.00 to 0.58.
- Training-data exposure, not testable from the repo: the human posts may be in OLMo-2's pretraining data, and
  possibly in Pangram's human training data. Henry's new posts are in neither.
- Quality: not measured. Claim support (0.956) is measured against D100, not against the human post or a reader. The
  G1 blind read is pending.
- A1 licenses this: at a fixed length near the human post's, an AI draft whose sentences are about 70% paraphrases
  of a writer's own sentences reads Human after B30's rewriter on 26 of 30 unseen pre-2022 bloggers. A draft that is
  two-thirds Sonnet fill reads Human on 4 of 30. This holds against leakage, exclusion, fallback and covariate checks.
- A1 does not license:
  - that Henry's realistic notes reach that regime;
  - that selection, rather than AI elaboration per word, is the lever;
  - that the rewriter is needed or how much it adds;
  - anything on technical posts with math or code;
  - anything about quality.
  - G1 row 4 should be read with this scope. P1 (Henry's next post) stays the decisive test, and it should log the
    density of note words to draft words so it can be placed on A1's curve.

## Recommended next checks, cheapest first

1. Scan D100 with the S50 batch (about 520 credits). This measures the rewriter's marginal effect at full notes.
2. Run the length-matched density test from finding 1 (Sonnet from `dose50` at half length, then the rewriter,
   against C100 cut to the same length). This separates "Henry writes more" from "Claude pads less".
3. In P1, record note words per draft word and the share of draft sentences backed by notes, with the same TF-IDF
   rule as here.
4. Fix the apostrophe tokenization in `copying.py`. Then recompute the C1 picks and B38's 0.70 to see whether
   anything moves.
5. When Modal credit allows: a memorization probe with the OLMo-2-13B base on the 32 test-A posts (prefix
   continuation exact match).

## What I could not verify

- D100's Pangram share (not scanned; prediction only).
- Whether the base model or Pangram saw these posts in training.
- The Claude model that answered the claim checks for each cell.
- Semantic (embedding) similarity: there is no sentence-embedding model in the venv, so closeness here is lexical
  (TF-IDF) and understates paraphrase.
- Quality of C100 against D100.
