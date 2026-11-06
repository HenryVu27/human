# Red team: gate 2a (B37) conclusions

Saved verbatim from the red-team agent's final report, 2026-11-06 about 12:30 CST. It was given the head session's five
conclusions and the raw files and asked to attack in both directions with its own analysis. Scripts are in the session
scratchpad `b37red/`.

## Report

All of the head's headline numbers reproduce.

**Attacks, ranked by how much they could change the gate 2b decision**

1. **MELD cannot see the improvement that matters, so conclusion 1's null tells us nothing about Pangram.**
   - On B36's C300 texts, MELD separates Pangram Human from not-Human at AUROC 0.55 (p 0.32). Its rank correlation with
     Pangram's AI share is 0.28 (p 0.12).
   - The pre-registered threshold T puts C0 on the floor: its per-window rate is 0.067. Matching Pangram's 11 of 32 needs
     a threshold at the 99.4th percentile of human windows (MELD 1.15, against T -2.25).
   - At post level, MELD does track Cfull share (rho 0.41, about 4 MELD units per unit of share). With that slope, the
     32-post paired test has 80% power only for a share drop of about 0.18.
   - B36's regression (Cfull on Dfull plus copying) predicts C1 lowers share by about 0.056. The observed MELD
     difference implies about 0.03.
   - So C1 is too small to matter, but that conclusion comes from the regression, not from MELD. The +0.10 rate bar was
     unreachable for anything short of a large effect.
   - Gate 2b would also be developed blind: B38 has no local judge that works on rewriter output.

2. **Pangram evidence that the pick matters (against conclusion 1).**
   - The context-engineering post has no LaTeX. Identical texts scanned on the two days got identical shares (s1 0.00,
     s5 0.65, s7 0.70), so day drift is nil there.
   - C1's rule changed 4 of its 7 sections, and all 4 fell: 0.28 to 0.10, 0.10 to 0.00, 0.62 to 0.49, 1.00 to 0.41. The
     whole post went from 0.40 to 0.24.
   - It was not through less copying: s6's copying rose from 0.18 to 0.60.
   - So the share varies a lot from seed to seed (up to 0.59 within one section), and selection has headroom, but no
     local judge sees it. This is one post.

3. **The additive model holds on real posts, which reframes conclusion 3.**
   - Whole-post share is close to the word-weighted mean of the section shares in all four Henry scans: 0.235 against
     0.24, 0.091 against 0.08, 0.593 against 0.53, 0.275 against 0.24.
   - The bandits rewrite reads Human although two of its sections are Mixed (0.28 and 0.30). That rules out "every window
     must read Human", the B36 red team's per-window model.
   - What the splice probe does not show is "per sentence". Its smallest block is 88 contiguous words of near-pure Sonnet
     text, from one post. Scattered or partly edited AI sentences were never tested.
   - Decomposition with B36's numbers: prefix (C300) mean share 0.29; the rest of the post 0.40; Cfull 0.376. Long
     context could at best bring the rest down to the prefix level, worth about 0.09. The remaining gap of about 0.19 is
     per-window quality on unseen authors. Nothing measured so far says whether training at scale on more diverse posts
     fixes it.

4. **L's shortness comes from looping and its trained length, which is an argument for long-context training.**
   - Raw generations have a median of 1,514 words, 70% of the target.
   - 35 of 64 run to the token limit without ending and loop (8-word self-repetition 0.73, against 0.07 for those that
     end). Those that end stop at a median of 981 words, about the length of the essays it was trained on.
   - Pruning keeps 40%, so the picked texts have a median of 520 words.
   - At that length L is close to B28's L50 setting, which read Human on 14 of 19 at 361 words. With the Pangram-matched
     MELD threshold, L's first windows read human-like at 0.65 against C0's 0.28 (paired p 4e-6).
   - But it is a different product: 28% of the post's content, and 8 of 32 texts have claim support below 0.85.

5. **The bandits Human is fragile.**
   - About 200 words are flagged against a line of 250, so one paragraph decides the label. B36's draw of the same post
     read Mixed at 0.13: one Human in two draws.
   - The scanned texts have holes where the math was stripped. The rewrite keeps some residue that the stripped original
     does not.
   - The section result survives: shares fall in 11 of 12 sections (Wilcoxon p 0.012), and shorter rewrites do not
     explain it (the bandits sections that flipped got longer, 1.08 to 1.17 times).
   - It is not an independent replication of B36: 4 of the 12 rewritten sections are the same texts as B36's.

6. **Cheapest experiment that could change the decision.**
   - Scan every seed's sections (4 seeds) for about 4 fresh calibration-split posts, roughly 400 credits and about $1 on
     Modal. If the per-section best of 4 brings whole posts to 0.10 or below, the bottleneck is the development judge,
     not the model, and gate 2b's money should not go to training first.
   - A free step first: score the open detectors on every Pangram-scored rewrite text already on hand (B30 T, B28 L,
     B36 C300 and Cfull, the Henry sections) and check whether any separates Human from not-Human within rewrites at
     AUROC 0.7 or better.

**What survives:** C1 is not a lever that matters (expected gain about 0.03 to 0.06), though for a different reason;
L fails the pre-registered bar; share is about the fraction of flagged words, and Human needs 0.10 or less; the
section-level gain; conclusion 5 holds for long context alone (about 0.09 of a 0.28 gap), but not as a judgement on
scale or data diversity, which is untested.

**Could not verify:** Pangram's segment size, and whether scattered AI sentences are counted; MELD scores on the Henry
texts; whether test-A seeds vary as much as the Henry sections do; Pangram verdicts on L; the claim-check outputs;
whether more diverse training data raises the per-window quality.
