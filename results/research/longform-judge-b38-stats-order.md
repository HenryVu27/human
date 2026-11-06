# Outside judge: B38 statistics recompute and order audit

Saved verbatim from the outside-judge agent's final report, 2026-11-06 about 13:55 CST. It was given the raw files,
the claimed numbers, the git history and the required order, not the head session's reasoning. Its scripts
(recompute.py, refit.py, boot.py, copy_check.py, pangram_check.py, secboot.py) are in the session scratchpad.

## Report

B38 audit: (A) independent recompute of the statistics, (B) order of events against the pre-registration. Everything was read-only. I made no Pangram calls, launched no Modal jobs and ran no `claude -p`; `modal app list --json` was the only Modal command.

Scripts (my own code: rank-based AUROC with ties counted as half, Spearman on average ranks, no imports from b38_judge.py), all in the session scratchpad:
- recompute.py: all metrics
- refit.py: rebuilds J1 from the raw detector scores
- boot.py: bootstraps and baselines
- copy_check.py: copied-share heuristic and the B36 check
- pangram_check.py: Pangram records and credits
- secboot.py: section bootstrap

Each was run with `.venv/bin/python -I <script>` from /Users/henryvu/personal/human.

PART A. STATISTICS

Every reported number reproduces. The credit rule in the brief does not.

Data and judge metrics:
1. Data counts (1,534 rows, 561 rewrites, 273 not Human, 888 with a share, 96 groups): reproduced (recompute.py).
2. J1 out-of-fold (OOF) rewrite AUROC 0.735 (n 561, 273 not Human), Spearman with share 0.40 (n 90): reproduced, 0.7351 and 0.4018. All 90 rows with a share come from B36 (78), B37 (11) and Probe13B (1).
3. J1 OOF on all rows, 0.786 and 0.330: reproduced.
4. J1 leave-one-experiment-out (LOEO) rewrite AUROC 0.62 (n 89): reproduced, 0.6199.
5. J2 OOF rewrite AUROC 0.722: reproduced, 0.7216. J2 LOEO is 0.6202, also reproduced.
6. J1 predictions come from the registered recipe: reproduced exactly (refit.py). Rebuilding the folds from the registered sha256 rule matches the stored folds; no group or document spans two folds. Refitting the logistic regression on the B38 detector scores plus B33 scores matched by text gives a maximum absolute difference of 0.0 against the stored OOF, LOEO and candidate predictions.

Calibration candidates (14 sections, 63 pairs whose shares differ by more than 0.05; recompute.py):
7. J1 pair accuracy 0.746, best-of-4 0.215, random 0.337, oracle 0.163: reproduced (0.7460, 0.2150, 0.3369, 0.1629).
8. J2 0.587 and 0.299: reproduced (0.5873, 0.2986).
9. Proxy gaps: J1 0.215 and 0.292, J2 -0.112 and -0.041: reproduced.
10. Whole-post figures in evaluation.judges.J1.calib_posts (and J2's): all four posts reproduced to 3 decimals.

Post hoc (explore_post_hoc):
11. Least-copied best-of-4 0.243 with pair accuracy 0.778: reproduced (0.2429, 0.7778).
12. 80% length floor, J1 0.283 against random 0.348: reproduced (0.2829, 0.3477).
13. Shortest-candidate rule (0.276, 0.619) and oracle at the floor (0.234): reproduced.
14. Spearman correlations on candidates (0.61, 0.37, 0.08, 0.70): reproduced (0.608, 0.373, 0.078, 0.699).
15. Section bootstrap of J1's gain over random, 0.122 [0.052, 0.196]: reproduced with my own resampling, 0.122 [0.054, 0.197]. J1 minus least-copied: 0.028 [-0.049, 0.113].
16. On 64 B36 rewrites, copied-share AUROC 0.74 against J1 OOF 0.673: reproduced with my own 8-word copy measure (0.7404 and 0.6731; J1 LOEO 0.6426; combined scores 0.718 and 0.707). The candidates' copied_from_input values recompute exactly from the prompts.

Pangram records (pangram_check.py):
17. Records match the transcript and shares file: reproduced. All 57 blind names agree across the transcript, shares file, blind key, records and b38_pangram.jsonl, with zero mismatches in label, share, Pangram word count, key, cell, document or local word count. The blind mapping also reproduces exactly from the committed seed (`random.Random("b38")`).
   - Pangram's word count is 1.00 to 1.07 times the local count for every candidate (1.31 for the bandits post with math), so no names were swapped.
   - The blind key is byte-identical to the 4fdc84e version; the transcript, shares and scan_times files are byte-identical to 5b389b0.
18. Credit ledger: differs. 9,079 minus 8,717 is 362, and 9,079 equals B37's closing balance, so the ledger is internally consistent. But the transcript's per-file credits, which equal ceil(Pangram words/100) for all 57 files, add up to 386, not 362. The same gap appears in earlier batches (B37 listed 569 against 555 charged; B36 1,824 against 1,715). No simple rule fits all three batches: per-file ceil, ceil of the batch total and rounding each fail somewhere. Rounding happens to give 362 for B38 but gives 546 for B37. So "1 credit per started 100 Pangram-counted words" describes the per-file display, not what was charged. Budget is unaffected (362 is under the 600 cap).

Uncertainty (boot.py, 10,000 resamples):
19. J1 OOF rewrite AUROC, 95% interval from resampling the 86 groups: [0.686, 0.782]. 0.70 is inside, and 7.8% of resamples fall below 0.70. Resampling rows instead gives [0.693, 0.776].
20. J1 minus J2 by group: [-0.048, 0.071]. The choice of J1 holds either way, because the simpler model wins within 0.02.

New findings, each with its evidence:
- F1. An untrained baseline almost clears the bar. Raw MELD's own score, with no training, reaches AUROC 0.6995 on the same 561 rewrites. J1 beats it by 0.036 (group bootstrap [0.008, 0.065]). The amendment's "MELD cannot rank rewrites (0.55)" refers to a narrower set; on these rows raw MELD scores 0.578 on the LOEO rewrites. The 0.70 bar was set after B33 had already reported MELD at about 0.67 on local-writer text.
- F2. On the candidates, raw MELD picks as well as J1. MELD's best-of-4 is 0.213 against J1's 0.215 (difference -0.002, section bootstrap [-0.054, 0.037]); its pair accuracy is 0.667 against J1's 0.746 (copy_check.py, secboot.py).
- F3. J1's gain shrinks once B37's existing eligibility rule is applied (form passes, at least 50% of the words, claims supported at least 0.90). Best-of-4 becomes J1 0.288, raw MELD 0.261, J2 0.275, least-copied 0.291, random 0.340, oracle 0.213. This is post hoc and based on 14 sections.
- F4. Two of J1's 14 picks are degenerate texts:
  - In section K_pf688f8ab80_3, J1's top pick is the unscanned 32-word candidate (prediction 0.03, input 530 words). The metric quietly used J1's second choice instead (165 words, share 0.0).
  - In section K_pdcbac3657f_1, the pick is the 85-word candidate (13% of its input) whose share of 0 was read from a screenshot saying "Possibly human (short text)".
  - The registered docstring says "every candidate is scanned, whatever its checks", but the registered scanfiles code drops texts under 50 words.
  - If the 32-word pick had scored its section's mean, J1's best-of-4 would be 0.242; if it had scored 1.0, 0.286. Dropping both sections gives J1 0.251, random 0.359, oracle 0.190.
- F5. Pooled AUROC mostly compares texts from different experiments: only 1,391 of 78,624 positive/negative pairs share an experiment and cell. Within experiment and cell, J1 scores 0.669 and raw MELD 0.646.
- F6. The B36 check of the copied-share heuristic is not truly held out. B37's docstring (11:16) already says B36's leftover AI share "tracks how much of Sonnet's post it copies", and B37's pick rule C1 already was "least copying". The explore() docstring says the heuristic is checked "on texts it was not found on"; that is inaccurate.
- F7. The LOEO split shares groups with its training data. 60 of 188 LOEO test rows (25 of the 89 rewrites) are in groups that also appear in training ("henry" plus two sites). This makes LOEO slightly optimistic.

PART B. ORDER AUDIT

Sources: git commit times; file modification times; `modal app list --json`, whose timestamps are set on Modal's servers; the Claude call cache under .cache/llm; and b38_scan_times.txt.

1. f578571 (13:09:01; CLAUDE.md last modified 13:09:00) came before a99a393 (13:10:59; reserve file 13:10:45), which came before 58bf80d (13:13:54). Verified. The reserve is unchanged since a99a393, and none of the calibration posts or data documents are in it.
2. Nothing B38 ran before the rules commit. Verified as far as traces exist:
   - Modal shows no app between B37's lf-detect (stopped 12:14:21) and lf-judge, J2's evaluation run (13:14:47 to 13:21:15).
   - The Claude cache has no entries between 12:20 and 13:14; the first is at 13:14:21 (calib_inputs).
   - The data step's output was last written at 13:14:03.
   - Candidate generation ran 13:16:53 to 13:23:39; detector scoring 13:31:46 to 13:37:16.
   - Could not verify: local CPU work leaves no trace, so a local J1-style fit before 13:13 cannot be ruled out. Since the stored J1 output reproduces exactly from the committed code, any such run changed nothing.
3. The blind key (4fdc84e, 13:31:45) predates the scan click (13:33:07): verified. Modal's lf-detect app was created at 13:31:46, which corroborates the commit clock. The 13:33:07 click time is only the author's own note; Pangram's dashboard history would confirm it.
4. 3761e03 is not a rule change. It reuses B33 detector scores matched by exact text; lf_detect.py has not changed since 63e43ab (02:12), and the B33 scores date from 02:18. It also splits J2 into an evaluation run and a later full-data run, with a merge that keeps the earlier out-of-fold predictions. Splits, metrics, the bar and the choice rule are untouched, and the change landed 2 seconds before the first training app started.
5. 79975d4 keeps the post hoc work apart from the choice rule. `_metrics`, `_pick_metrics`, `linear` and the choice code are unchanged; the choice reads only OOF rewrite AUROC. No choice depended on the calibration candidates or LOEO. Three caveats:
   - The post-scan addition calib_posts is stored under evaluation.judges in the JSON with no post hoc tag; only explore_post_hoc is labelled.
   - The committed explore() docstring says "added 13:50", which is impossible for a 13:44:09 commit, and _post_metrics says 13:42.
   - The working tree changes these to 13:43 and 13:41 but is uncommitted (file modified 13:44:20). There is also no LABNOTEBOOK row for B38 yet.
6. Predictions after the labels were read do not matter for J1, and matter little for J2:
   - J1 is deterministic and reproduces to 0.0 from inputs fixed before the scan: data at 13:14:03, candidates at 13:31:20, detector inputs at 13:31:45, all produced by one detector run.
   - J2's full-data run (13:37:17 to 13:38:36) came after the labels and may not be bit-reproducible on a GPU. But Modal shows only one such run, J2 was not chosen, and its OOF predictions come from the run that ended at 13:21:15, before the scan.
   - Could not verify the J2 numbers themselves: rerunning needs Modal. `modal app logs` was not used.

Most important next check: before any test-B credits go to J1-picked outputs, run the next pick test with raw MELD and a length/eligibility floor as baselines. Raw MELD already reaches AUROC 0.6995 on these rewrites and matches J1's best-of-4 on the candidates (0.213 against 0.215). Under B37's eligibility floor, J1 no longer beats MELD, J2 or least-copied.

## Head session's notes (added after the report)

- Caveats 5a and 5b are fixed: the key is now `calib_posts_post_hoc`, and the docstring times read 13:41 and 13:43
  (both edits before the 13:44:09 commit; the wrong times were typed into the docstrings, not the times of the work).
  The explore() docstring now says the copied-share comparison is not held out (F6).
- F4: the 85-word candidate's verdict is recorded as Human with AI share 0 (transcript line `a84b4605.docx|1 Credit,85
  Words|Human`); the panel read "Possibly human" for short text. The 50-word floor in scanfiles is a deviation from the
  docstring's "every candidate is scanned" and is listed as one.
- Item 18 (credit rule): recorded in the notebook's credit ledger; the dashboard difference (362) is what counts.
