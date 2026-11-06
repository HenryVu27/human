# Outside judge: B37 (gate 2a) statistics, pick rule, order and confidentiality

Saved verbatim from the outside-judge agent's final report, 2026-11-06 about 12:30 CST. It was given the rules, the
development and Pangram raw files, the blinding key, scan times, git history and six claims; not the head session's
reasoning. Its scripts are in the session scratchpad `verify37/`.

## Report

B37 gate 2a check: all six claims hold on the raw files. The Henry-arm p value (claim 3) is fragile and there are some
process deviations (claim 5).

1. Development numbers: VERIFIED.
- Threshold T is -2.2506 (numpy gives -2.249), taken from 720 reference windows across 100 posts.
- Per-window rates: C1 10/152 = 0.066, C0 10/150 = 0.067, L 15/60 = 0.25.
- Mean score differences: C1 -0.119 (Wilcoxon p 0.814), L -1.684 (p 3.9e-5).
- All 1,082 non-calibration windows rebuild identically, and no reference post is a test-A post.
- Copying from D: C1 0.196, C0 0.322. L is 0.277 of the human length, claim support 0.894 (0.892 pooled), form 29/32
  on my own recheck.
- C1 fails only the rate and Wilcoxon conditions; L fails length, support and form. The blinding key holds no test-B
  texts.
- Moving T to the 90th or 97.5th percentile still leaves C1 within 0.014 of C0.
- Caveat: on B36's C300 texts MELD calls 1/32 human-like where Pangram called 11/32.

2. C1 pick rule: VERIFIED on all 84 sections, not just a sample.
- I reassessed all 464 candidates with the Claude CLI disabled, so only cached answers could be used (0 cache misses),
  then applied my own coding of the rule.
- C1 matches 32/32 (seeds and texts), with 77 eligible and 7 form-only picks and no copying ties. L matches 32/32, the
  Henry sections 13/13, and C0 equals B36's texts.
- This rests on the cached Claude prune, cleanup and claim verdicts, which I did not judge independently.

3. Henry arm: VERIFIED.
- The raw page matches the transcript. Transcript, shares and key join 48/48, and the scanned files, converted back to
  text, match the rebuilt texts 48/48.
- 12 pairs: 8 better, 1 worse, 3 ties, p 0.039 (two-sided). Human sections go from 1 to 6. The four whole-post results
  are exactly as stated.
- Finding: LaTeX stripping leaves math in both arms. Original HO2_bandits_s5 keeps 7 inline spans. Rewrite
  HR2_bandits_s6 (the one "worse" pair) keeps broken residue.
- If one "better" pair became a tie, p would be 0.070.

4. Splice probe: VERIFIED.
- The splice texts rebuild identically, 20/20.
- The blocks are 88, 126 and 248 words (share of words 0.068, 0.095, 0.17); the "60, 120, 240" labels are nominal
  sizes.
- AI shares are 0.06-0.07, 0.08-0.09 and 0.15-0.17, labelled Human, Human, Mixed at every position in both bases. Both
  bases read Human at 0.0 in B36.
- Only one AI block and two bases were used.

5. Order: VERIFIED for the core sequence, with flags.
- Rules committed 11:16:43. Generations launched 11:17:13. A partial warm-up pick ran at 11:34 and was overwritten. The
  final pick ran 11:49 to 12:12:18. Splice texts were built at 11:49:13.
- MELD inputs first crashed on the window tail-merge bug. The fix went in at 12:12:43 and was committed at 12:12:56;
  scores followed at 12:14:19.
- Commit 4b74f50 and the key both came at 12:14:59, before the 12:16:14 click. Pick, dev, decision and key are
  unchanged since.
- Flag a, out-of-memory fallback: edited 11:23:12, used for the 100 rows regenerated at 11:33:38, committed 12:19:15.
  It only splits and reseeds a batch on out-of-memory, which is triggered by memory, not content. It can change
  individual draws but not their distribution. It prints nothing, so whether it fired is unknown. L used the earlier
  code and the b26-essaypool adapter.
- Flag b: the docstring says batch 16; the runs actually used 12 and 8 (B36 itself used 8).
- Flag c: the spec's splice threshold says 150 credits, the docstring says 280. Both are met: the Henry arm used 285
  credits.
- Flag d: per-file credits sum to 569 against the dashboard's 555.
- Flag e: there is no B37 row in LABNOTEBOOK.md, which the project rules require (added afterwards).

6. Confidentiality: VERIFIED.
- None of the 13 rewrites adds a term from the HEALTH list.
- The new capitalized tokens are sentence starts, headings and math symbols.
- Client work appears as "diabetes management coaching agent/assistant", the original's own wording.
- HR1_bandits_s6 also contains "$Rewrite{n}$", a leak from the prompt template; it was stripped before the scan.

Not verifiable from here: the Pangram verdicts and the click time (both self-recorded), the cached Claude verdicts,
and whether the out-of-memory split fired.
