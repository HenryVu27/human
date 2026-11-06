# Outside judge: B34 and B36 statistics recompute and scan-time order

Saved verbatim from the outside-judge agent's final report, 2026-11-06 about 11:05 CST. It was given the raw dashboard
transcripts, the AI-share files, the blinding key, the merged records, the analysis outputs, the rules with their
amendments, the scan times and the git history, and six claims; not the head session's reasoning. Its scripts are in
the session scratchpad (c1.py, c2.py, leak.py, raw.py). Actions taken: `analyze` now keys the Henry-arm section cells
by key (fixed 11:06, rerun); the credit figures are reported as the dashboard drop (1,715) beside the per-file
charges (1,824).

## Report

I recomputed every statistic from the raw files. The primary B36 numbers and the pre-registration order hold. The
credits claim is wrong, and the stored analysis file miscounts the Henry-arm section cells.

1. Merged records: VERIFIED. I rebuilt them from the transcript, the two shares files and the blinding key: 169 of 169
match b36_pangram.jsonl field for field, with no duplicate or missing names. Batch sizes are 100 and 69 in both. Every
key equals cell plus doc. I also went to the rawest source, the head session's browser log. All 169 transcript lines
match the dashboard page text it captured, and all 169 AI shares match its JavaScript readouts.

2. Cells: VERIFIED.
- Dfull 0/13/19, mean AI share 0.8128
- D300 0/10/22, 0.8509
- Cfull 1/31/0, 0.3759
- C300 11/19/2, 0.2916
- Hfull and H300 10/0/0 each, 0.000
No text is under 150 words (the shortest is 257), so the under-150 rule changes nothing.

3. Primary tests: VERIFIED.
- Cfull against Dfull: Dfull's AI share is higher on all 32 pairs. Mean difference 0.437; Wilcoxon p = 7.9e-7 (normal
  approximation, because 11 differences are tied; exact would be about 5e-10).
- C300 against Cfull: 11 against 1 discordant, McNemar p = 0.00635. Holm rejects both.
- Sensitivity: 30 pairs, Cfull Human 1, 9 against 1, p = 0.0215.
- Band: Cfull Human is 1 of 32, so "does not transfer".
- No C text copies over 15% from its human post (maximum 6.5%), so nothing was excluded.

4. Henry arm: VERIFIED, with a caveat.
- Whole posts: HO_aieng Mixed 0.55, HR_aieng 0.40, HO_bandits 0.41, HR_bandits 0.13, as claimed.
- Sections: 5 of 12 read Human.
- B15's sections s1 to s7 are word for word the B36 originals.
- Ordering the labels AI < Mixed < Human, 8 sections improve, 0 get worse and 4 tie; the sign test gives p = 0.0078.
- Caveat: the ai-engineering comparison uses labels from a scan made a day earlier (B15) against today's scan.
- Finding: the "cells" block of b36_transfer.json is wrong for HR_sec and HO_sec. It stores n=2 (1 Human) and n=1
  because `analyze` keys rows by `doc` ("aieng" or "bandits"), so the sections overwrite each other. The "henry" block
  (21 entries) is correct.

5. Pre-registration order: VERIFIED.
- Rule commits eca4a0d 09:07:36, b254d2e 09:42:15 and 576b465 10:24:42 all precede the batch 0 upload (10:25:50 in
  the log) and the click at 10:26:15. The Pangram page text shows "Nov 6, 2026 10:26 AM".
- `analyze` in both scripts is unchanged since eca4a0d, apart from the sensitivity lines added later.
- Sensitivity amendment: the script edit is at 10:54:42 and commit becf7ef at 10:55:02. Recording runs at 10:55:23,
  analyze at 10:55:24, B34 analyze at 10:56:28, and commit 889ca59 at 10:56:39.
- The raw transcript files were first written at 10:55:19, so file times alone cannot rule out unblinding.
- The head's log can: before 10:55:22, no tool output or message puts a blinded file name next to a cell or doc id.
  The blinding key was never printed, and no captured text contains French or code.
- The audit agent never saw Pangram data.
- Dropping the two posts also weakens the length effect, since both C300 texts read Human.
- Not ruled out: about 15 screenshots, which I could not view.

6. Credits: REFUTED. The transcript's per-file credits sum to 1,824, not 1,715: batch 0 is 1,131 against the 1,067
drop, and batch 1 is 693 against 648. The drop matches the dashboard estimates. Per-file credits follow Pangram's word
counts, which run up to 49% above ours on the bandits files. B28 showed the same pattern (371 against 355). "10282
left" appears in the captured page text; "9,634 after" appears only in the head's own note.

Could not verify: the screenshots; Pangram's "10:27 AM" stamp (only "10:26 AM" is in the log text); the 9,634
balance; the human-to-AI conversion for each file beyond what the log shows.
