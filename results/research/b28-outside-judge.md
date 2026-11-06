# B28 local-writer cells: outside judge (2026-11-06, about 04:30)

An `outside-judge` agent with a fresh context was given B28's raw files, B30's results and five claims, not the reasoning behind them. It recomputed everything with its own scripts (kept in the main session's scratchpad, `verify/`). Its report, verbatim:

All five claims check out, apart from one rounding slip in claim 3. The weak spot is the dose trend inside the local writer (L): length explains it as well as dose does.

Claims
1. Confirmed. verdicts.txt has 76 unique ids and all 76 labels match b28_dose.json. Counts are L100 11/8/0, L50 14/5/0, L25 17/2/0, R 13/6/0. Only two texts are under 150 words, L25_e2cddaea8 (Pangram 114 words, whitespace count 110) and L25_e2cfe2cb2 (118/117). Both read Human, so L25 drops to 15. The docx and txt files match b28_texts.jsonl exactly. Pangram word counts track text length (r 0.999), and credits equal words/100 rounded up on all 76, so no rows are swapped. The H and S verdicts are identical to commit 5ced2ac (11-05 18:45), 19 per cell. I could not check the dashboard itself.
2. Confirmed as scanned, exact two-sided binomial: 10/0 p .002; 19/0 twice, p 3.8e-6; T100 over L100 8/0 p .008; T50 against L50 3/4; L25 over T25 15/1 p 5.2e-4; R against L100 4/2 p .69; R over S100 12/0 p 4.9e-4. With the 150-word rule (it also catches T25_e7b687627, 33 words), L25 against T25 becomes 14/1, p .001.
3. Confirmed, with one rounding slip. L100's length ratio is 0.6747, which is 67%, not 68%. Words 540.6, 361.2, 280.2; claim support .901, .848, .719; R 509.1 words, .927.
4. Confirmed. Commit c0c9bc2 is at 04:07:47; the reflog and the object file time agree. b28_texts.jsonl was created at 04:07:17, the docx files at 04:07:47 to 04:07:50, and verdicts.txt at 04:10:07. The commit shares a second with the first docx, and the scan cannot come before the docx exist. Only scratchpad/b28lr holds L or R files.
5. Confirmed by code reading plus a reproduction. The pick path imports no Pangram or detector code. Recomputing "most supported claims" from the stored candidates matches all 76 picks. Final texts only delete from the raw samples; no words are added. I could not rerun the pick because it calls Claude.

Problems
- Pre-registered predictions mostly failed.
  - L100 got 11 of 19 Human; the bar was 12 of 20.
  - L's Human count rises as notes thin (11, 14, 17), the opposite of "L falls with dose".
  - R read Human more often than L100 (13 vs 11), the opposite of the prediction.
  - Length came out at 67/45/35% of T, against a predicted 50/35/25%.
  - Met: H, the S Human ceilings, S25's rise in AI, and L beating S at every dose.
- Length can explain the L dose trend. Pooled L Human rate: under 300 words 17/20, 300 to 449 words 16/20, 450 and over 9/17. Inside 300 to 449 words: L100 5/5, L50 5/8, L25 6/7. In a logistic model, neither log words nor dose is significant. Paired L100 against L25: 0/6, p .03 as scanned; 2/6, p .29 under the 150-word rule. Length does not explain L against S, since T100 at 640 words reads 19/19 Human.
- Looping: 15 picked raw samples loop (6-word-sequence repeat share above 0.2, up to 0.79; R_e2408017e repeats "1160." until the token cap). 14 picks never reached end of text. Pruning removes the loops: L25 keeps 37% of raw words, and no duplicate sentences survive. These 15 read Human 7/15, so they do not inflate the Human count.
- Machine split: seed 0 has 37 Mac rows, all in one block of consecutive prompts (27 to 63); seed 1 is all PC. 18 picks are from the Mac (L100 5, L50 3, L25 5, R 5). Human rate is 13/18 on the Mac and 42/58 on the PC, both 72%.
- Copying: 8-word copying from the essay is 3.4/2.5/0.9% for L and 3.1% for R, similar to S. Human-labelled texts copy a little more (2.9% vs 1.2%, Mann-Whitney p .056). The first ~96 tokens of essay e2cfe2cb2 appear in training document e148e3340.
- R inputs: R's facts are S100's extracted facts and its Guard text is S100, but the Topic line comes from the essay's notes.
- L prompts shuffle the notes; S gets them in order, while the docstring says "the notes' own order".
- Mixed labels cluster by essay: e26077b9a (Sumner) 4 of 4.
- S was scanned on 11-05 and L/R on 11-06, with no rescanned anchor texts in the same session and no record of Pangram's model version.

Check next: whether the L dose trend survives a length-matched control. Cut each L100 text to its L25 partner's length by sentence deletion, and scan those alongside a few rescanned S100 texts as a same-session anchor.
