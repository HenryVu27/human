# Red team: B36's conclusion

Saved verbatim from the red-team agent's final report, 2026-11-06 about 11:05 CST. It was given the conclusion under
attack (the head session's reading), the rules, verdicts, texts, the B30 and B28 results and the earlier audits, and
asked to attack in both directions with its own analysis. Its scripts are in the session scratchpad `b36red/`.

## Report

**Strongest attacks, ranked by how much they change the gate-2 reading**

1. **"Length is the bottleneck" misreads the arithmetic.** Under the 90% rule, the full-length Human rate is roughly
   the per-window rate raised to the number of windows. A simulation draws independent 300-word windows from the C300
   share distribution and sizes each post by its Cfull length (about 4.6 windows).
   - At C300's rate of 0.34 it predicts 1.7 Human of 32. Observed: 1.
   - A per-window rate of 0.8 gives 18 of 32. B30's implied rate is about 0.83 (13 of 19 at about 606 words, about 2
     windows). So B30-level quality would reach the "transfers" band even at these lengths.
   - The deficit is per-window quality, 0.34 against about 0.83, and it already shows in section 0, the part most
     like B30's training. Length only multiplies it.
   - A long-context model does not change this arithmetic. It must lift the per-window Human rate to about 0.8.
   - Caveat: Pangram's window size is unknown. With 500-word windows the prediction is 3.5.

2. **The leftover AI share comes from D and from copying, and the pick rule adds to it.**
   - Cfull's share tracks Dfull's (Spearman 0.59, p 0.0004). A linear fit of Cfull on Dfull plus copying gives slopes
     0.89 and 0.44 (R squared 0.56, against 0.35 for Dfull alone).
   - C300's share tracks how much of the prefix is copied from D (rho 0.58, p 0.0005). Human prefixes copy 19% of
     their words from D, others 36%.
   - C copies 32% of D, against 13% for B30's T50.
   - In 57 of 84 sections, the most-claims pick keeps the seed that copies more (29% against 20%, p 0.0004).
   - So a copy-penalized pick, or more seeds, is an untested lever that needs no training.

3. **Prefix against full is not a pure length test.**
   - Subtraction estimate: C's share beyond the first 300 words is 0.40 against 0.29 in the prefix, while D goes from
     0.85 to 0.81. The difference in differences is +0.16 (p 0.028). This is model-dependent.
   - About 12 of 52 later sections restart as a new post, with framing found in neither D nor the human post
     (for example "This is the second of three articles", "This is a continuation of my last post"). The claim check
     missed these.
   - Posts with restarts do not read more AI (0.39 against 0.37). So sectioning hurts coherence and faithfulness,
     which supports long context on quality grounds, not on Pangram grounds.

4. **The length evidence is weaker than stated.**
   - All 10 human posts score 0.00 at both lengths, so any aggregation rule leaves them Human. The control that tests
     mixed text, B34's B arm, lost all 8 texts to its filters in both runs.
   - C300's 11 includes the garbled French prefix, scored Human at 0.00.
   - 3 of 11 Human prefixes carry the space-before-punctuation quirk, against 0 of 21 non-Human prefixes (Fisher p
     0.033).
   - McNemar goes from 11 against 1 (p 0.006) to 9 against 1 when the French and code posts are dropped (p 0.021),
     and to 7 against 1 when the quirk posts are also dropped (p 0.07). The direction holds; the significance is
     fragile.
   - The only Cfull Human scores 0.09, just under the 0.10 line, and a 0.10 share appears with both labels.

5. **B30 is not a clean "seen authors" baseline.** B30 rewrote whole posts of about 800 words by 10 famous essayists.
   Each had about 60 essays in the training pairs, and they are likely in OLMo-2's pretraining. B36's writers are
   obscure 2009 to 2022 blogs: race recaps, game reviews, food round-ups. "Unseen" is confounded with fame, genre and
   sectioning, so B30's 13 of 19 may be the optimistic outlier. The technical posts do no better: Cfull 0.37 against
   0.38, C300 Human 2 of 7.

6. **The Henry arm's 8 of 12 is confounded.**
   - 7 of the 12 baselines are B15 scans from an earlier day.
   - The bandits originals contain raw LaTeX. Pangram counted 1.31 to 1.49 times our word count, and these sections
     hold 116 to 157 digits against 20 to 67 in the rewrites.
   - The rewrites are shorter: bandits s6 has 364 words against 1,180, aieng s2 643 against 1,244. Shorter text
     favours Human by the head's own rule.
   - HR_aieng_s3 is 89% Henry's words yet flips from Mixed to Human at 0.10.
   - Copying does not drive the result: the low-copy sections (13% and 18%) went to Human.
   - A minor bug: analyze() keyed Henry sections by post (since fixed).

**What survives**
- Does not transfer at full length: 1 of 32, far below the band of 7. The sensitivity analysis agrees.
- The rewriter moves every post toward Human: Cfull is below Dfull on 32 of 32.
- Full-length Human is rarer than prefix Human, in direction.
- Pure human posts do not get false positives at length.
- Selection is clean. The 6 replacements are no different from the rest (Cfull 0.35, C300 Human 1 of 6). Pangram
  labels match the shares: Human at 0.10 or below, Mixed from 0.10 to 0.79, AI at 0.81 or above.

**Could not verify:** Pangram's window size and aggregation, and whether its AI share includes AI-assisted text;
per-section Pangram shares (the position result is a subtraction estimate); whether the spacing quirk causes Human
verdicts; drift between scan days for the B15 baselines; OLMo-2 pretraining contents; claim-check outputs, which were
not rerun.

**For gate 2:** before funding, test a copy-penalized or multi-seed pick on B36's existing generations with the MELD
development judge. That is free and could raise the per-window Human rate.
