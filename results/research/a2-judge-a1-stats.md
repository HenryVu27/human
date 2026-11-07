# A2 judge: A1 statistics, blinding, order and canaries (2026-11-06)

Independent recomputation from raw files (transcript, shares, blinding key) with my own code; the project's analyze() was not called. Scripts: scratchpad recompute.py, hashes.py, checks2.py, checks3.py, d100cache.py, d50cache.py.

## Claim 1: C100 reads Human on 26 of 30 included posts, mean share about 0.03
VERIFIED. Transcript parses 70 of 70 lines; key, transcript and shares cover the same 70 names, no duplicates. Labels agree with shares (Human 0 to 9%, Mixed 10 to 66%, AI 92%). Pangram word counts run 0.7% to 5.8% above key word counts on every file, so no file was mis-joined.
- C100 cell: 28 Human, 4 Mixed, 0 AI of 32; mean 0.0319, median 0.00.
- Paired set (n 30): C100 Human 26; mean 0.0340.

## Claim 2: C50 reads Human on 4 of 32, mean about 0.31
VERIFIED, with a denominator problem. C50 cell: 4 Human, 28 Mixed of 32; mean 0.3075, median 0.32. In the paired set it is 4 of 30, mean 0.3047. The claim sets 26 of 30 (paired) beside 4 of 32 (cell). Like for like, it should read either 26 of 30 against 4 of 30, or 28 of 32 against 4 of 32.

## Claim 3: paired set and exclusions
VERIFIED. No D100 under 1,000 words (minimum 1,203). Two texts copy more than 15% from the human post: C100_p35b2004659 (0.172) and C100_p61945fb568 (0.228). My own 8-word-run copy measure gives 0.170 and 0.227, so the same two are excluded. Both read Human 0.00 in C100, against C50 Mixed 0.22 and 0.48. Excluding them works against the claimed effect. All 32 pairs: mean diff -0.2756, p 1.3e-6.

## Claim 4: paired mean difference about -0.27, 95% bootstrap interval about -0.33 to -0.21
VERIFIED. Mean diff -0.2707, median -0.24; 28 negative, 1 zero, 1 positive. Bootstrap with my own implementation (Python Random("a1"), 5,000 resamples): -0.334 to -0.207, matching the project's output. numpy percentile (20,000): -0.335 to -0.209. BCa: -0.339 to -0.212. t interval: -0.337 to -0.204.

## Claim 5: Wilcoxon p about 3e-6, Holm about 6e-6
VERIFIED. scipy.stats.wilcoxon, two-sided, default zero_method (zeros dropped). Ties force the normal approximation: p = 2.83e-6. Pratt: 2.2e-6. The exact test, ignoring ties, gives 7.5e-9. Holm as coded while S50 is deferred is 2p = 5.66e-6. That is a valid upper bound on the two-contrast Holm, whatever S50's p turns out to be. Re-adjusted over three contrasts with A2-N, the worst case is 3p = 8.5e-6. McNemar (exact binomial on discordant pairs): 22 favor C100, 0 favor C50, p 4.77e-7. Paired t p 3.2e-9; sign test p 1.1e-7.

## Claim 6: band "large content effect" applied exactly as stated
VERIFIED. The rule needs C100 lower by at least 0.10 with p_adj < 0.05. Observed: -0.2707 with p_adj 5.7e-6. The coded rule (d <= -0.10, p_holm < 0.05) matches the docstring and design section 6.3. The band holds under every variant I tried:
- copy threshold 0.10: n 29, diff -0.268, p 4.2e-6
- copy threshold 0.05: n 27, diff -0.274, p 9.3e-6
- copy threshold 0.03: n 18, diff -0.281, p 3.5e-4
- dropping posts with any fallback section: n 24, diff -0.259, p 3.1e-5
Copying from the human post does not track the share. Spearman of the share difference against the copy difference is 0.03 (p 0.89).

## Claim 7: blinding key matches the texts
VERIFIED. sha256 16-hex prefixes and word counts match for 64 of 64 texts in a1_texts.jsonl and 6 of 6 canaries rebuilt with canaries('2026-11-06'). Rerunning write_batch's shuffle with seed "a1" reproduces all 70 blinded names in key order. a1_texts.jsonl mtime 21:13:21 is before the key (21:13:44), so the texts are unchanged since blinding. All 32 C50 texts are byte-identical to the B37 C1 texts. No C1 cell appears in the B36, B37 or B38 keys, which confirms "never scanned before".

## Claim 8: scan followed the pre-registered rules and order
VERIFIED on the evidence that exists, with two minor deviations.
- Rules commit 26f36b8 was at 19:47:33. The first D100 Sonnet answer is cached at 19:54:33 (32 calls, 19:54:33 to 19:57:58, about 26 seconds each). All 32 resolved to claude-sonnet-5-5, as required, and the cached text matches D100 exactly.
- The prompts were written at 19:58:04 and the generation log opened at 19:58:16.
- The amendment (a694cfd) and the Holm change (5f8089a) were committed at 20:03:37 and 20:03:52. C100 generations were written 20:28:15 to 20:32:36, pick ran 20:32:57 to 21:13:21, the key was committed at 21:13:44 and the transcript saved at 21:17:01. Both amendments came before the texts they govern.
- The rewriter, pick and copy code are unchanged since the rules commit. The rules commit moved common.json, and the sha256 of the repo copy equals the old scratchpad copy.
- The A1 posts are from unseen writers: 32 distinct sites, none among B30's 13 training authors, and no 12-word run is shared with B30's training rows.
- Deviation 1: the docstring requires scoring_form to change texts by at most 1% of words. Three texts exceed it: C100_pa2b84bf758 1.8%, C50_pae98db1f7a 1.1%, C50_pc181d8f08b 1.0%. The removed tokens are list-marker dashes, so this is harmless, but the check as written failed.
- Deviation 2: the pre-registered fallback sensitivity analysis is missing from a1_content.json. My value is given under claim 6.
- UNVERIFIED: the upload time of "about 21:14 to 21:15" is self-reported. It is consistent with the key commit at 21:13:44 and the transcript mtime of 21:17:01, but only the Pangram dashboard history can confirm it.

## Claim 9: canaries match earlier scans
VERIFIED. All five frozen canaries return identical label, share and Pangram word count:
- CAN_rewrite against B36 Cfull_p8fb3502483: Human 0.09, 1,359 words
- CAN_splice against B37 SP_pc71cc789ec_120_middle: Human 0.09, 1,347 words
- CAN_h300 against B36 H300: Human 0.00
- CAN_hfull against B36 Hfull: Human 0.00
- CAN_sonnet against B36 Dfull_pd2849dd1e5: AI 0.92
The perturbed canary reads Human 0.00.

## Side findings
- Credits: LABNOTEBOOK.md line 144 says "per-file charges sum to 966". The transcript's per-file charges sum to 996; the dashboard drop of 8,717 to 7,751 is 966. Commit 134a60b also says 966.
- UNVERIFIABLE: D50's Sonnet model. The B36 cache entries carry no model field, so "same model as D100" cannot be checked. C100 and C50 also differ in their draft sample, not only in note count. The effect is "new all-notes draft plus rewriter" against "B36 half-notes draft plus rewriter".

## Most important next check
Separate the draft from the rewriter. Score D100 against D50 (or C50 rebuilt from a fresh D50 draw) before attributing the drop to content. The 0.27 drop could come partly from a different Sonnet sample or version rather than from doubling the notes.
