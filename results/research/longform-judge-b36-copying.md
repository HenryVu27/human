# Outside judge: B36 copying and faithfulness audit

Saved verbatim from the outside-judge agent's final report, 2026-11-06 about 10:50 CST (after the scan, before any
verdict was unblinded or analysed). It was given the inputs, human posts, rewrites, prompts and raw generations, the
rules in `experiments/b36_transfer.py` and five claims; not the head session's reasoning. Scripts are in the session
scratchpad. Action taken: a sensitivity analysis that drops C_p0f92b38ac3 and C_p40c33738de was added to the B36
docstring at 10:54, before the analysis ran; the primary analysis is unchanged.

## Report

Two claims hold and three fail in part. Copying is clean, the seed pick reproduces exactly, and the Henry arm adds no
medical terms or names. But two C texts carry invented content that the claim check passed. All checks used local
files only: no Modal, Pangram or Claude CLI.

1. Copying from the human post: VERIFIED.
- copied_share rerun on all 32 C texts matches the stored values exactly (largest difference 0.0).
- Distribution: median 1.03%, mean 1.65%, 0 texts over 15%.
- Worst 5: C_p61945fb568 6.5%, C_p35b2004659 5.2%, C_pe9ea594c27 4.2%, C_pa5fd792f87 3.9%, C_p4ad56d5750 3.1%.
  Normalizing curly apostrophes gives a maximum of 6.1%; with 5-word runs the maximum is 10.9%.
- Copying from D: mean 32.2%, range 5.6% to 67.7% (C_pd3f07c3e66).
- Beyond what D already shares with the human post: mean 0.38%, maximum 1.47% (C_p3a84b9ccbc). The longest such run is
  14 words (C_p4ad56d5750); D has the same fact, worded "2 pairs ... 87 dollars".
- Finding: there is a small real drift back toward the human wording. Of C's 5-word runs not in D, 0.78% appear in the
  post's own human original against 0.01% in the other posts (own higher in 28 of 32). Example: D's "murdered 49"
  became the human post's "shot and killed 49".
- The test posts share at most 0.05% of their 8-word runs with data/rewritepool (train and valid), so the rewriter
  did not train on them.

2. No added facts: REFUTED in part.
- Sample of 5 texts, 10 sentences each: 46 of 50 fully supported. The 4 mild drifts: C_p01004974c5 "culture of
  engagement" and "choices about where they want to work"; C_p3bfd623027 "equal to" where D says "parallel", and
  "11 centuries".
- A scan of all 32 C texts found:
  - C_p40c33738de: about 40 lines of invented Arduino code, found in neither D nor the human post. The claim check
    scored that section 29 of 34; the section ends inside the code.
  - C_p0f92b38ac3: three paragraphs of garbled French and a "last frontier" quote. Both seeds produced French.
  - C_p8e28b03c67: "41:13", where D says "41 minute mark".
  - C_p9ae3b6a467: invented "11)" list labels, and the wording inside quotation marks was changed.
  - C_p89e48932f5: "night in the French Alps".
- No new person names in any C text.

3. Henry arm: VERIFIED for health terms and names.
- Every health term in the rewrites traces to an original sentence. The only new hit is "heart", in "At the heart of
  RL". Diabetes appears 3 times in the original and 2 in the rewrite, same phrasing.
- No capitalized word is absent from the originals ("Manus" became "Manually").
- Copying is 66.43% and 36.84%, matching the head's figures exactly.
- Number and format problems: "120,000" became "120,0 0 0"; 7 invented "15)" labels in HR_aieng; and HR_bandits_s4 has
  invented markdown headings, one of them "### Gaussian and Bounded Draft" (a leaked "Draft" token).
- Several section cells are mostly Henry's own words: HR_aieng_s3 89%, s4 90%, s2 76%, HR_bandits_s6 84%.

4. Seed pick: VERIFIED.
- Prune, repeat drop, cleanup and claim check replayed for all 200 generations from the on-disk Claude cache, with
  subprocess blocked: 0 cache misses.
- The pick rule reproduces all 32 C texts, both HR posts and all seed lists byte for byte.
- Spot checks (kept seed: kept claims vs other seed's claims): C_p4ad56d5750_2 seed 0: 29/30 vs 9/18. C_p61945fb568_2
  seed 0: 27/27 vs 24/25. C_p2a4982704f_0 seed 1: 20/20 vs 18/18. HR_bandits_1_0 seed 1: 23/23 vs 15/15.
  C_p8e28b03c67_2 seed 1: 19/19 vs 15/17.
- Because the rule counts claims, it keeps the longer text in 78 of 100 sections. There is 1 exact tie.

5. Things that would mislead a Pangram Human verdict: REFUTED for specific texts.
- No "Draft:" or "Rewrite:" lines in any C text or raw generation, and no repeated paragraphs.
- Problems: C_p0f92b38ac3 is part French and only 54% of D's length; C_p40c33738de ends in code; C_pae98db1f7a has 11
  bullet lines; C_pe9ea594c27 has markdown links, and C_p61945fb568 a ">" quote marker (both also in D);
  C_pce9bcaba2a has "Bat tub".
- Spaces before punctuation (" ,", " .") appear 24 times in 14 C texts, against 0 in D and 4 in the human posts. This
  rewriter quirk could look like human noise to Pangram.
- B25's plain() leaves code fences in D (C_p40c33738de's D).
- The inputs summary in results/b36_transfer.json is stale: D_copied_from_post is 0.0125 there, 0.0147 now (from
  before the amendment).

Could not verify: whether the cached Sonnet verdicts are correct; that the adapter trained only on data/rewritepool;
client names (only that nothing capitalized is new); Pangram labels.

Most important next check: decide before the analysis whether to exclude or flag C_p0f92b38ac3 (French) and
C_p40c33738de (invented code), and HR_bandits_s4. Then add language, code and markdown checks to the pick step,
because the claim check passed both texts.
