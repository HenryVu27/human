# Outside judge: B38 split-leakage audit

Saved verbatim from the outside-judge agent's final report, 2026-11-06 about 13:55 CST. It was given the data,
prediction and reserve files and asked to find any path from evaluation data into training; not the head session's
reasoning. Its scripts (c1.py to c9.py) are in the session scratchpad.

## Report

B38 split-leakage audit (read-only; scripts are in the session scratchpad, run with `uv run python` from /Users/henryvu/personal/human)

Bottom line: no leak moves J1's out-of-fold (OOF) rewrite AUROC (area under the ROC curve) of 0.735 by a material amount. Test-B and the calibration candidates are clean. There is one real cross-fold text leak, the splice texts. Its measured effect on J1 is 0.002 at most, and its worst-case bound for any judge is 0.0073. The leave-one-experiment-out (LOEO) test set does share text with LOEO training, but that pulls LOEO down, not up, and LOEO does not enter the choice. The biggest issue I found is not a leak; it is in "Most important next check" at the end.

1. Group folds: PASS
- Script: c1.py. I recomputed `_folds` from b38_judge.py and `folds` from lf_judge.py; the second was pulled out by text so Modal never had to be imported.
- The two functions are identical apart from their names. The fold maps stored in the J1 and J2 prediction files are equal to each other and to the recomputed maps for all 1,534 uids.
- No group falls in two folds, for either judge. Fold sizes are 307, 307, 308, 306 and 306. Every uid has exactly one out-of-fold prediction.
- The group key itself is sound (c1b.py, plus doc-to-group mapping):
  - All 191 documents map to exactly one group, and no row fell through to a "doc:" key.
  - All 20 draft/source pairs (a06NN and h06NN) share a group.
  - Each site group maps to a single host, and each author to a single site (for example Paul Graham to paulgraham.com, Noah Smith to noahpinion.blog). No essayist's site shows up as a "site:" group.
  - The only registrable domains shared by two groups are blogspot.com and wordpress.com, which host separate blogs.
  - All 61 of Henry's rows (B15, B17, B36, B37) sit in the single group "henry".

2. Near-duplicates across folds: FAIL, small (c2.py, c2b.py)
- Method: 8-word shingles, measuring how much of each row is contained in rows from other folds.
- Rows with more than 2% containment: 23. Of these, 22 trace to the suspect and the 23rd is boilerplate (0.021).
- The leak: the AI block in the splice texts is drawn from p827b1c285d's Sonnet post D.
  - 18 splice rows carry the D block: 9 in fold 2 (site:uncensored) and 9 in fold 3 (site:jinpeili), with 60, 120 or 240 words of D.
  - The 4 rows of p827b1c285d itself are in fold 0 (site:whyigame): D300, Dfull, C300 and Cfull.
  - Containment values: D300 0.85, Dfull 0.106, C300 0.174, Cfull 0.024. The splices themselves score 0.063 to 0.167. The 6 splices with 240-word blocks are labelled Mixed; the other 12 are Human.
- Only 2 rewrites are touched: C300 and Cfull of p827b1c285d.
- Other overlap measures:
  - Identical first 300, 100, 50 or 25 words across folds: 0.
  - Rewrites, 5-gram containment against other folds: median 0.004, 95th percentile 0.017, maximum 0.247 (the same C300).
  - Rewrites, 13-gram containment: every rewrite except those two scores 0.
- C300 and Cfull, and D300 and Dfull, always share a group because a document never maps to two groups.
- Effect on the numbers (c6.py):
  - J1 refit with all 20 splice rows dropped from training: 0.7350.
  - J1 refit with the splices moved into whyigame's fold: 0.7359.
  - Leaving the 2 affected rewrites out of the metric: J1 0.7334, J2 0.7207 (reported 0.7216).
  - Worst case for any judge: 2 positives out of 273, times 288 negatives, bounds the shift at 0.0073.

3. Test-B reserve: PASS on IDs and texts; combined hash COULD NOT VERIFY (c3a.py to c3e.py)
- Membership reproduces exactly from the stated rule (bucket = sha256('b32-split-v1:'+site) mod 100, merged by `core_name`): 798 posts, equal to the file.
- Per-text sha256 values match the raw text in b32_pilot_full.jsonl for 798 of 798.
- The file is byte-identical to commit a99a393 (13:10:59), which comes before the rules commit 58bf80d (13:13:54).
- Training and calibration against the reserve:
  - Training documents with a reserved ID: 0.
  - Candidate or calibration-input IDs that are reserved: 0.
  - Exact text-hash matches: 0 training rows, 0 candidates.
  - Highest 8-gram containment of a training row in reserved texts: 0.016 (2 stock phrases). Candidates: 0.0036. Calibration D and human texts: 0.
- Site level:
  - No training site group shares a core name with a reserved post.
  - The training pilot documents sit only in buckets 75 to 79 and 90 to 94, and none falls in a merged group that touches buckets 95 to 99.
- Combined hash: I could not recompute it. I tried about 2,600 constructions (separators, orders, JSON forms, binary digests, the file without that field) and none matched. No script in the repo builds it.
- Aside: 19 reserved IDs appear in b33_corpus_inputs.jsonl and b33_scores_corpus.jsonl. B33 ran the open detectors over them before the reserve existed. No labels were involved, and b38_judge.py reads only b33_scores_calib.jsonl, so the judge is unaffected.

4. Calibration candidates: PASS (c4.py)
- None of the 4 source IDs appears as a training document or inside any uid.
- Candidate texts found in training: 0, whether matched exactly or with whitespace normalized.
- Highest 8-gram containment of a candidate in training: 0.0046 (1 phrase). 5 of 56 candidates share any 8-gram at all.
- The source posts' human texts share nothing with training. Their D posts reach at most 0.0008.
- The core names (sifter-writes-bikes, sanlorenzoriverblog, kateharding, rohanmaitzen) are not training groups.
- The candidate keys in the J1 and J2 prediction files equal the 56 candidate IDs and never overlap the out-of-fold keys.
- J1's candidate predictions reproduce exactly (maximum difference 0.0) from a model fit on all 1,534 rows (c6b.py).
- Pangram's labels for the candidates are read only in `_pick_metrics`, `_post_metrics` and `explore`. `data`, `linear` and lf_judge.py are unchanged since 3761e03 (13:14:45), well before the scan commit 5b389b0 (13:36:25).

5. Leave-one-experiment-out: the literal claim PASSES; train/test disjointness FAILS (c5.py, c8.py)
- The claim:
  - LOEO training holds 0 rows from B36 or B37.
  - The loeo_test flag matches the experiment name on every row.
  - The LOEO keys equal the 188 test uids for both judges.
  - J1's LOEO predictions reproduce exactly.
- The overlap: 37 of 188 test rows have more than 1% 8-gram containment in LOEO training, 29 more than 50%, 16 more than 90%.
  - All 20 B37 splices are built on B34's Hfull human posts. Those 20 B34 rows were scanned in the B36 batch but carry the name B34, so they sit in LOEO training. The 2 "none" splices are 100% contained.
  - Henry's originals (B36 HO, B37 HO2) are near-copies of B15's O sections, which are in LOEO training (0.99 to 1.0).
  - 13 of the 89 LOEO test rewrites are Henry rewrites of those sections (containment 0.05 to 0.79).
  - Separately, exact-text deduplication dropped 9 B37 rows, 6 of them as copies of B15 rows. For HO2_aieng_s5 it kept B15's label (AI), while the B37 rescan of the same text said Mixed. That is label noise, not leakage.
- Effect: leaving out the overlapping rewrites raises LOEO rewrite AUROC, so the overlap does not inflate it.
  - J1: 0.620 to 0.660 (n = 76).
  - J2: 0.620 to 0.673.
  - LOEO across all rows barely moves: J1 0.816 to 0.810, J2 0.819 to 0.824.

6. Other leaks: PASS (c6.py, c6b.py; reading the code for J2)
- J1 reproduces exactly: the OOF maximum difference is 0.0 and the rewrite AUROC is 0.7351317 from the committed code.
- The StandardScaler sits inside the pipeline, fit on each training fold only, and class weights are computed per fit. A counterfactual with the scaler fit on all rows gives 0.7352, so even that would have been immaterial.
- The features are raw detector `ai` scores plus log words. lf_detect.py fits nothing to labels, and the B33 scores are raw values, not calibrated ones.
- In J2 the label touches only the target. The 3 epochs are fixed, with no early stopping and no use of the test fold before predicting. The token cache is harmless.
- I could not rerun J2 (no Modal), so its training behaviour is verified only by reading the code.

Provenance aside, not a leak
- The working copy of b38_judge.py has uncommitted edits to the post-hoc timestamps in the docstrings: `_post_metrics` "13:42" becomes "13:41", and `explore` "13:50" becomes "13:43".
- The committed "13:50" is later than its own commit time (13:44:09), so the edit looks like a correction, but it should be committed with that explanation.

Most important next check
The 0.735 measures mostly between-cell differences, not ranking within a section. That is a blind spot, not a leak (c9.py).
- A baseline that sees no text, only each row's experiment and cell (scored with that cell's label rate in the training folds), reaches a rewrite AUROC of 0.781. That beats J1's 0.735.
- Counting only pairs inside the same experiment and cell, J1 drops to 0.669 and J2 to 0.639.
- The judge's actual job is picking among the 4 seeds of one section. The only direct test of that is the calibration pick accuracy: 0.746 on 63 pairs from 14 sections, and that set is clean.
- Next step: report AUROC within cell (or within section) alongside the pooled figure, and grow the within-section labelled set before relying on the 0.70 bar.

## Head session's notes (added after the report)

- Combined hash: verified by the head session. The construction (from the a99a393 session) is: for each reserved ID in
  sorted order, feed sha256 the ID's UTF-8 bytes, a zero byte, then the 32-byte binary sha256 of the post text.
  Recomputed from the file's per_text_sha256 values it gives af7fd710...9154, equal to the stored value. The new
  `reserve_check` step in experiments/b38_judge.py recomputes it from the per-text hashes without reading any text.
- The timestamp edits were committed with the explanation.
