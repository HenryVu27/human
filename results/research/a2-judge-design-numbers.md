# Outside judge: numbers in the attempt-2 design (2026-11-06)

Artifact: `docs/specs/2026-11-06-attempt-2-design.md`. Judge: outside-judge agent, 2026-11-06. Scope: every number in
sections 0, 2, 3, 4 and 6.10; power claims in 6.3, 6.4, 6.9 and 7; credit arithmetic in 6.3, 6.4, 6.9 and 10; the
existence of the texts the design relies on; Modal spend. Strategy was not judged. Nothing was scanned, nothing run on
Modal except `modal billing summary`, and no repo file was edited (this report is the only new file).

## Method

- Re-ran `experiments/a2_rechecks.py`: output byte-identical to the committed `results/a2_rechecks.json`.
- Independent recompute from raw files with my own code (python -I), in `/private/tmp/a2judge/`:
  `recompute.py` (B36, B37), `b38.py` (B38 correlations, slope, gated oracle), `thresh.py` (label thresholds, C1 texts,
  credits), `power.py`, `a2n.py`, `mcn.py` (power, exact binomial and simulation).
- Credit rule calibration: per file ceil(our words / 100) reproduces the dashboard drops within 0.6%
  (B36 1,726 vs 1,715; B37 557 vs 555; B38 364 vs 362). Ceil of Pangram's own word count overstates (1,824, 569, 386,
  the "per-file charges" in the ledger). I use ceil(our words / 100).
- Primary pages fetched: Pangram pricing, arXiv 2610.06778 abstract, arXiv 2610.21062 HTML (Table 12), Smaug-Humanizer
  model card.

## Verdict table

| # | Claim | Location | Verdict | Evidence |
|---|---|---|---|---|
| 1 | Human only under about 10% flagged | 0, 2 | VERIFIED | All 1,846 scan rows in `results/*pangram*.jsonl`: Human max share 0.10, Mixed min 0.10, AI min 0.81. Splice: 9.5% block Human, 17% Mixed |
| 2 | Best rewriter left whole posts at about 0.38 | 0 | VERIFIED | B36 Cfull mean 0.3759, n 32 |
| 3 | B36: 1 of 32 Human in full, 11 of 32 at 300 words | 2 | VERIFIED | Cfull labels 1/31/0; C300 11/19/2 |
| 4 | B36 Dfull 0.81 to Cfull 0.38, every post moved | 1, 5 | VERIFIED | Cfull < Dfull on 32 of 32, smallest drop 0.21; paired SD 0.119 |
| 5 | B37 splice: largest block-share vs AI-share gap 0.02; blocks 88 to 248 words in 2 posts | 2 | VERIFIED | Bases 1,207 and 1,201 words; blocks 88, 126, 248; max abs error 0.020 (248/1,455 = 0.170 vs 0.15) |
| 6 | Canary splice "at 9.5%" | 6.2 | VERIFIED | 126/1,327 = 0.095, 126/1,333 = 0.0945 |
| 7 | Canary B36 rewrites at 0.09 and 0.19 exist | 6.2 | VERIFIED | Cfull p8fb3502483 0.09; p35b2004659 and p3bfd623027 0.19 |
| 8 | B38 copying Spearman 0.70 (0.699, n 55) | 0, 2, 4 | VERIFIED | 0.6986 |
| 9 | Partial given length and claims 0.62 | 2 | VERIFIED | 0.6196 (rank residuals) |
| 10 | Within-section 0.63, slope 0.61 | 0, 2, 4 | VERIFIED | Demeaned Pearson 0.6255; OLS slope 0.608. Note: section 0 sets this within-section Pearson beside AIHB's Spearman -0.02; the pooled Spearman comparator is 0.70 |
| 11 | Claim support +0.46 with share, +0.57 with copying | 2 | VERIFIED | 0.4577, 0.5727 |
| 12 | Copying about 0.34 | 4, 6.4 | VERIFIED | Mean copied_from_input 0.337 (56 cands), 0.338 (55 scanned); observed range 0.00 to 0.94, so 0.05 is inside the data |
| 13 | 0.61 x (0.34 - 0.05) is about 0.18; 0.38 to about 0.20 | 4 | VERIFIED (arithmetic) | 0.608 x 0.29 = 0.176; 0.376 - 0.176 = 0.200. Caveat: applies a section-level, within-B38 correlational slope to B36 whole posts |
| 14 | Gated oracle 0.213 at k = 4 | 4, 5 | VERIFIED | Gate = form_ok, claims >= 0.90, words >= half input: section mean 0.213 (word-weighted 0.205). C1 0.291, random 0.337 |
| 15 | Math as LaTeX added 0.17 on bandits | 4 | VERIFIED | B38 M_kept 0.41, M_stripped 0.24, same batch |
| 16 | B30 T100 19 of 19, 82% length, 94% claims, about 640 words, judge preferred essay 87% | 2 | VERIFIED | b30_rewriter.json: 19/0/0; 0.818; 0.944; 640.5 words; quality_vs_essay 0.132 so essay preferred 86.8% |
| 17 | Rescans 8 of 8 within 0.02 same day; 6 of 7 across days, change at 0.80 line | 2 | VERIFIED | All 8 pairs found in b36/b37/b38 raw (largest gap 0.02, aieng whole post 0.55 vs 0.53, 3-word text change). B15 labels (b15_blog.json O_s1..s7) vs B37 HO2_sec: 6 of 7 agree, s5 AI to Mixed 0.78 |
| 18 | Henry's originals 0.24 to 0.53; B36 Sonnet drafts 0.81 | 1 | VERIFIED | B37 HO2_post bandits 0.24, aieng 0.53 (LaTeX stripped); Dfull 0.813 |
| 19 | 1,534 Pangram labels; 561 rewrites | 3.2, 6.1 | VERIFIED | b38_data.jsonl 1,534 rows; origin local_writer 561 |
| 20 | C1 pair-accuracy benchmark 0.778 | 6.1 | VERIFIED (report) | REPORT section 39 item 4 |
| 21 | No model after 4.1 (2026-10-19); docs updated 11-02; 512 tokens, stride 256 | 3.1 | VERIFIED (report) | a2-pangram.md Q1 rows, primary-verified tags |
| 22 | $200 API credit on Professional; $0.05 per 100 words; 4,000 to 5,000 units; 160 to 200 post scans | 0, 3.1 | VERIFIED | Pricing page fetched today: "$200 monthly API credits", "$0.05 per 100 words", bulk 20% off. 200/0.05 = 4,000; 200/0.04 = 5,000; at 25 units (2,500-word post) 160 to 200. At B36's 1,681-word drafts it would be about 230 to 290 |
| 23 | Opus 5.5 and GPT-6 prose with whole paper flagged 22 to 25% | 3.1 | WRONG (minor) | arXiv 2610.21062 Table 12 (fetched): GPT-6 astra 0.230 LaTeX, 0.211 text; Opus 5.5 0.250, 0.219. Range is 21 to 25%. Opus alone (section 1) is 22 to 25%, correct. Also: model 4.0 by date, and "detected" counts AI or Mixed |
| 24 | StealthGPT 41 of 50 under 10%; 26 also free of fact errors | 3.1 | VERIFIED (report) | a2-pangram.md lines 15, 116 to 117 |
| 25 | IdeaLens 92% and 8% | 0, 3.2 | VERIFIED | arXiv 2610.06778 abstract (fetched): "still flags 92%", 8% on human stories from AI plans; 2026-10-05; Iyyer last author |
| 26 | IdeaLens: Pangram 4 idea-provenance accuracy 25.9% | 2, 3.2 | UNVERIFIABLE here | Not in the abstract; a2-literature.md cites the HTML |
| 27 | AIHB 19 of 330 (5.8%), 3 of 60 blogs, StealthGPT 6 of 33, Spearman -0.02 | 0, 2, 3.2 | VERIFIED (report only) | a2-literature.md line 82. Pass criterion there is Pangram human probability >= 0.5, not share < 0.10. Agent recount; I did not refetch the dataset |
| 28 | Fact audit 35 to 65% of documents | 3.2 | VERIFIED (report) | a2-literature.md line 84 |
| 29 | Smaug: 2026-10-26, Apache 2.0, gemma-4-12B base, 3,676 pairs, 200 GRPO steps, 5 gates, about 500 words, three examples, "more often for long texts" | 0, 3.2 | VERIFIED | Model card fetched: all match; date only from the blog URL |
| 30 | ProseLens on 1M Pangram 3.3.2 labels | 3.2 | VERIFIED (report) | a2-literature.md: WildOutlines 1,001,145 docs |
| 31 | Detector-guided RL "since June" | 3.2 | WRONG (minor) | DEPO, the first listed, is arXiv 2606.00392 dated 2026-05-29 (a2-literature.md line 88) |
| 32 | Base-model shortlist facts: gemma-4-12B 256K, Jan 2025 cutoff, Apache; Olmo-3-7B RULER 84.1 at 16K | 3.3 | VERIFIED (report) | a2-base-models.md lines 33 to 34, 78, 380 |
| 33 | PC memory 0.92 GB per 1,024 tokens; 12 to 14B at 8K only with offload; 7 to 8B at 16K | 3.3 | VERIFIED (report) | a2-base-models.md lines 40 to 43, 173 to 177 |
| 34 | 7.5 tok/s, about 250 h for 400 posts x 4; about 30x faster | 3.3 | VERIFIED | 6.72M tokens / 7.5 / 3,600 = 249 h; report table 249 h vs 7.5 h (33x, an estimate) |
| 35 | SFT about $8.50 on H100 over 18M tokens; 4 to 8 h PC; generation $4.90; $10 to $15 / about $44 vs $40 to $55 | 0, 3.3 | VERIFIED (report) | a2-base-models.md: $8.53, 3.8 to 7.7 h, $4.87, totals lines 414 to 417. All estimates |
| 36 | Sun et al. 91.4%; Argument Collapse 65.3/3.4, 6.8 vs 41.0; connectives 56 to 66 vs 38; readers 99.3% | 3.4 | VERIFIED (report) | a2-adjacent-fields.md lines 21 to 25, 121 to 123. The report itself flags these as read through a summarizer |
| 37 | "Thirteen hypotheses. Four of them (H1 to H4) need no scans" | 3.4 | WRONG | a2-adjacent-fields.md tags six as cost R (no scans): H1, H2, H3, H4, H9 ("if a corpus exists") and H13; line 321 says "H1 to H4, H9 and H13 cost no scans" |
| 38 | ICC about 0.25; 75% of variance try to try | 3.5 | VERIFIED (report) | a2-measurement.md lines 42, 123. Caveat in report: 4 posts, ICC anywhere 0 to 0.6 |
| 39 | Final test: 37 posts at 0.70, 158 at 0.60 | 3.5, 6.10 | VERIFIED | Exact binomial, one-sided 0.05: first n with 80% power is 37 and 158. Sawtooth: n = 38, 39, 41 fall below 80% at 0.70; all n >= 42 pass |
| 40 | 32 of 50, one-sided 95% bound above 0.50, 86% power at 0.70 | 3.5, 6.9 | VERIFIED | P(X >= 32 / p 0.5) = 0.0325 (31 gives 0.0595); Clopper-Pearson one-sided lower 0.514; power at 0.70 = 0.859 (0.62 at 0.65) |
| 41 | 20 of 40 wins rules out a win rate of 0.35 or less | 3.5, 6.9, 7 | VERIFIED | P(X >= 20 / 40, 0.35) = 0.036; one-sided 95% lower bound 0.361 |
| 42 | 15 of 30 rules out 0.30 or less (minimal protocol) | 7 | VERIFIED | P(X >= 15 / 30, 0.30) = 0.017; lower bound 0.339 |
| 43 | G1 veto: true 0.5 gives at least 8 of 10 losses 5.5% of the time | 7 | VERIFIED | P(wins <= 2 / 10, 0.5) = 56/1,024 = 0.0547 |
| 44 | 40 pairs plus 10 controls about 4 to 4.5 hours | 3.5 | VERIFIED (report) | a2-measurement.md line 573: 50 pairs at about 5 minutes |
| 45 | A1: paired SD 0.12, n 32 gives 80% power at about 0.06 | 6.3 | VERIFIED | Paired t MDE 0.061; Wilcoxon power 0.75 at 0.06, 0.79 at 0.061. SD 0.119 is B36 draft vs rewrite; C100 vs C50 (two rewrites) has not been measured |
| 46 | A1 expected effect 0.05 to 0.15 from B30 T100 vs T50 | 6.3 | UNVERIFIABLE | b30_rewriter.json stores labels only (no shares), so the share effect cannot be derived from raw data. It is a judgment |
| 47 | A2-N: n = 28 gives 80% power at about 0.07 | 6.4 | WRONG | Holds only if paired SD is 0.12 (MDE 0.066). The unit is a section mean of 2 seeds vs 2 seeds; the project's own B38 data give within-section seed SD 0.211 (pooled from raw; a2-measurement.md: try variance 0.058, SD 0.24). Paired SD of 2-vs-2 means is therefore about 0.18 to 0.24 (empirical 2-vs-2 split SD 0.176). MDE at n 28: 0.10 to 0.12 unclustered; with the design's own clustering by post (8 posts, design effect about 1.6) about 0.15. Still powered for the 0.18 "causal" expectation, not for 0.07 or for the 0.08 band edge |
| 48 | 6.10: 0.38 vs 0.20 needs 6 to 14 (SD 0.12 to 0.20) | 6.10 | VERIFIED | Paired t: 6 at SD 0.12, 12 at 0.20; Wilcoxon (sim): 7 and 13 |
| 49 | 6.10: 0.10 drop needs 14 to 20 (SD 0.12 to 0.15) | 6.10 | VERIFIED | t: 14 and 20; Wilcoxon: 15 and 21 |
| 50 | 6.10: 3% vs 30% McNemar 28 to 40 | 6.10 | VERIFIED (range); upper end not reproduced | Exact McNemar, two-sided 0.05, simulation: 29 (max positive correlation), 33 (independence), 36 (most negative correlation the marginals allow). 40 is more conservative than any case I can build; harmless |
| 51 | 6.10: 30% vs 60% needs 25 to 50 | 6.10 | VERIFIED | 25 (max positive correlation) to 50 (independence) |
| 52 | 6.9: 30 reader items, 84% power | 6.9 | VERIFIED (report only) | a2-measurement.md line 618 (0.93 vs 0.60); not recomputed, effect assumptions are the report's |
| 53 | A1 cost: D100 544, C100 448, C50 448, S50 448 = about 1,890 | 6.3 | WRONG (small, under) | Sum of the four is 1,888, but the per-cell figures use mean words, not per-file ceilings. Actual: C50's texts exist and cost 457 (b37_texts.jsonl C1, mean 1,376 words). Dfull-length posts cost 554, Cfull-length 464. Realistic A1 core: about 1,930 to 2,030 |
| 54 | A1 cost omits the Henry arm | 6.3, 10 | WRONG (omission) | Henry arm = 2 posts x 3 versions (original, C1, triage) in scoring form. From B37's stripped scans: originals 27 + 45, rewrites 26 + 37, triage similar: about 200 credits, in no line of section 10 |
| 55 | Canaries about 70 credits a session | 6.2, 10 | WRONG (likely under) | 7 texts: 2 human posts, 2 Cfull rewrites (13 + 14 to 16), 1 Sonnet post (12 to 17), splice (14), perturbed copy (13 or more). With B34 human posts (1,975 to 2,767 words) the minimum is about 107; with the splice bases as the human posts about 92. 70 fits only if the "human posts" are 300-word excerpts. Phase 1's 280 (4 sessions) becomes about 370 to 480 |
| 56 | A2-N about 500; A2-K about 670; A2-O about 200; A2-S about 120 | 6.4 | VERIFIED as plausible | B38 candidates average 5.34 credits (ceil). A2-K 112 cands: 598 at B38 lengths, 784 if candidates reach input length (mean 642 words). A2-N: 448 if B38's scanned seeds serve as C on 14 sections, 598 if C is rescanned same day as the method rules require. A2-O 40 x 5 to 6 = 200 to 240. A2-S depends on scan count (6 to 9 posts of about 1,250 words: 78 to 117) |
| 57 | Phase 1 "about 4,100 (canaries 280, A1 1,890 plus up to 400 for L, A2 1,370 plus 120 if A2-S, A3 450)" | 10, 13 | WRONG (arithmetic) | Listed parts sum to 3,990 without L and A2-S and 4,510 with both; 4,100 is neither. Section 0 says "about 4,000". A2 sub-sum 500 + 670 + 200 = 1,370 is correct. With items 53 to 55 added, a realistic phase 1 is about 4,300 to 4,900 |
| 58 | A3 about 450 | 6.5, 10 | UNVERIFIABLE (likely low) | Texts not yet chosen. Bandits three ways about 39 + 35 + 27 = about 100; 4 math posts x 3 and 4 code posts x 2 at 1,500 to 2,500 words: 300 to 500; scoring-form probe extra. About 400 to 600 |
| 59 | A7: 1,300 route + 150 Henry = 1,450; plus 850 D cell = 2,300 | 6.9, 10, 13 | VERIFIED (arithmetic); assumptions inconsistent | Sums are right. D cell 850 = 50 x 17 (B36 draft length, per-file mean 17.3 gives 866). Route 1,300 = 26 per post, i.e. 2,500-word outputs (a2-measurement.md line 596) or two scoring forms per output; rewrites are about 83% of D's length, so one form would be about 700 to 750 |
| 60 | Total about 6,200 to 7,500 of 8,717 | 10 | WRONG (range) | 8,717 remaining VERIFIED (ledger, dashboard 9,079 to 8,717 after B38). Design's own parts give 3,990 + 600 + 1,450 = 6,040 to 4,510 + 1,000 + 2,300 = 7,810. With items 53 to 55, about 6,400 to 8,300, leaving 400 or less at the top end, which trips the "A7 reserve plus 300" pause rule |
| 61 | G1 read: 20 pairs, 1.5 to 2 hours | 0, 7, 10, 13 | WRONG (internal) | 6.3 sends 10 C100 and 10 C50 pairs and 6.4 sends 10 N vs C pairs: 30 pairs, about 2.5 hours at the 5 minutes per pair the hour figures use. 7 says "10 pairs per arm", also 3 arms |
| 62 | Full protocol Q "about 6.5 to 10 hours" | 7, 13 | WRONG (minor) | a2-measurement.md line 615: full protocol about 6.5 to 8 hours; adding G1 (1.5 to 2.5 h) gives about 8 to 10.5. The low end should move |
| 63 | Modal: about $9.03 of $30 left, month to date $20.97 | 10 | VERIFIED | `modal billing summary --json` (2026-11-06): credits -20.97, ephemeral apps 20.967, volumes 1.71 covered by free storage, egress 0.71 covered by allowance, billed $0.00. 30 - 20.97 = 9.03. Phase 1's A1 $5 + A2 $3 + Smaug about $1 = $9, plus phase 0 under $1: over the remaining credit, as the design says |
| 64 | B37 C1 texts exist for all 32 B36 test-A posts | 6.3 | VERIFIED | b37_texts.jsonl cell C1: 32 rows, doc set equals B36 Dfull docs; 84 sections; 687 to 2,133 words; never in any *pangram*.jsonl |
| 65 | B38: 14 sections, 4 seeds each already scanned | 6.4 | WRONG (minor) | 56 candidates (14 x 4) exist but 55 were scanned; K_pf688f8ab80_3_s1 (32 words) was below the scan floor (REPORT section 39 item 1). One section has 3 scanned seeds; A2-K's k = 12 there is 11 unless it is rescanned |
| 66 | B39 reserve with 798 entries | 9, 6.9 | VERIFIED | b39_reserved_testB.json: n 798, 798 unique ids; no overlap with B36 test-A or B38 calibration docs |
| 67 | B38 posts are calibration, not test data | 6.4 | VERIFIED | B38 docs share none with B36 test-A or the reserve; REPORT 39: buckets 75 to 79. Note: a2-measurement.md line 121 calls them "4 test-A posts", a slip in that report, not in the design |

## What I could not verify

- IdeaLens's 25.9% idea-provenance figure (not in the abstract), the AIHB recount (dataset not refetched), Argument
  Collapse and reader-study numbers (agent read through a summarizer), all Modal throughput and cost estimates
  (no calibration run exists), and whether the $200 API credit is live (needs a call, outside my remit).
- A3, A2-S, L and A7 route-cell credits depend on texts not yet chosen; I give ranges from comparable raw lengths.
- The A1 expected effect (0.05 to 0.15): B30 saved labels, not shares.

## Most important thing to check next

The A2-N power line. It uses the whole-post draft-vs-rewrite SD (0.12) for a comparison of 2-seed section means,
where the project's own B38 data put the paired SD near 0.2 and the design clusters by post. At n 28 the experiment
detects about 0.10 to 0.15, not 0.07, so its "at least 0.08" band edge and a null result are not informative at the
stated precision. Either raise seeds per section, add sections, or restate the band before committing it.
