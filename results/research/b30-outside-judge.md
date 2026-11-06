# B30 outside judge (2026-11-06, about 02:50)

An `outside-judge` agent with a fresh context was given B30's raw files and five claims, not the reasoning behind them. It recomputed everything with its own scripts (run with `python3 -I`, kept in the main session's scratchpad). Its report, verbatim:

I recomputed everything from the raw files. Claims 1 to 4 hold. Claim 5 is partly refuted: T100 claim support is 94.4%, not 96 to 97%. The T25 tally counts a broken 33-word text as Human; it should be 2 Human, not 3.

1. Confirmed. The same 57 ids appear in verdicts.txt, b30_rewriter.json and b30_texts.jsonl, with 0 label mismatches. Tallies: T100 19/0/0, T50 13/6/0, T25 3/15/1. The uploaded .docx files match the picked texts exactly, and Pangram's word counts are 0.996 to 1.061 times the texts' own. I can't see the dashboard, so the labels themselves are unverified.

2. Confirmed. More human / less human / same: 18/0/1, 16/0/3, 17/0/2, so 51/0/6. Exact two-sided sign tests: p = 7.6e-6, 3.05e-5, 1.53e-5.

3. Confirmed, with a caveat. No bench essay shares an id, URL or title with the 660 pairs, and all 10 bench authors have 56 to 60 training pairs. However, training target e148e3340 (Kalzumeus "Rails SEO Tips") contains about 70 words of bench essay e2cfe2cb2's opening, through a scraped next-post preview. The outputs for that essay copy 0 to 1.6% from it, so no visible effect.

4. Confirmed. The pick path calls only Claude (prune, cleanup, claim check) and never imports humanizer.eval.pangram. The pick rule reproduces on all 57. The amendment commit dfc6cc0 is at 01:09:33. b30_gen.py changed once more at 01:28 (5d22dc0, GPU fallback only), before generation ran (01:46 to 01:57). The texts and results JSON were first created at 02:35:02, the scan files at 02:35:22, and verdicts.txt at 02:37:54. So the scan was 02:35 to 02:38, not "about 02:40", but the order holds.

5. Partly refuted.
- Words 640/606/658: confirmed.
- Copying from the input post 9.1/13.2/22.7%: confirmed with my own code (difference 0.0).
- Claim support 94.4/97.2/96.0%: T100 is outside "96 to 97%".

Problems:
- T25_e7b687627 is broken. Both seeds looped "1998, 1998, ..." until the token limit, and pruning left 33 words, which Pangram read as Human. The notebook's B16 row cites Pangram's 150-word floor, and B25 counted texts under 150 words as not Human. Without it, T25 is 2/15/1 of 18 and the sign test still gives p 3e-5.
- The only AI verdict, T25_e279a1d91, is a 99.8% copy of its input. It drives the T25 copying mean; the median is 14%.
- The pick rule (most supported claims) leans toward copying the input. It chose the higher-copy sample 36 of 57 times (p 0.06), and Mixed texts copy 21% against 9% for Human texts. That works against the result, not for it.
- Copying from the essay is small (1.0 to 3.5%), no higher than the S posts' own.
- The generating machine is balanced across cells (A10 11/12/9, A10G 8/6/9, PC 0/1/1). GPU type is confounded with seed.
- No other degenerate outputs. T50_e7ce7f8ef repeats "If we had no sympathy" 7 times, which reads as deliberate repetition.
- The design also pairs T with B28's L cells, but b28_dose.json records no L verdicts.
- B28's S posts and the T texts were scanned on different days, so Pangram version drift can't be ruled out.

Check next: count T25_e7b687627 as not Human (or regenerate it) and say so in the notebook, then decide whether the max-claims pick should penalize copying the input.

## What the main session changed

- Section 35 of `results/REPORT-2026-11-04-lora.md` now gives T25 as 3 Human by Pangram and 2 under B25's 150-word rule, and adds the copy, pick, leak and scan-day cautions. The table already gave T100's claim support as 94%; only a chat summary had said 96 to 97%.
- The B28 L cells are still being generated on the PC; their pairing with T comes with B28's write-up.
