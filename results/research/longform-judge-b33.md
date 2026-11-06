# Outside judge: B33 calibration numbers and detector code

Saved verbatim from the outside-judge agent's final report, 2026-11-06 about 03:10 CST. It was given the raw files
(`results/b33_calib.jsonl`, `results/b33_scores_calib.jsonl`, `results/b33_scores_corpus.jsonl`,
`results/b32_pilot_corpus.jsonl`), the rules in `experiments/b33_calibrate.py`, the detector code
`experiments/modal/lf_detect.py` with the reference implementations, the claimed numbers in
`results/b33_calibration.json`, and five claims; not the head session's reasoning. Its scripts are in the session
scratchpad `v33/`. Action taken: the Spearman tie bug it found was fixed at 03:14 and the analysis re-run; the
recomputed values now match its table.

## Report

I checked the five claims with my own code (scikit-learn, scipy and my own cluster bootstrap), not the analysis
script. Four hold as stated. Claim 1 fails only on one statistic: the Spearman correlation with Pangram's AI share.
I ran no models, so the detector code is checked on its math only.

**Claim 1 (every number follows from the raw files): REFUTED for one field, verified for the rest.**
- Deduplication is right: the 1,193 scored ids are the first id of each identical-text group, and every scored input
  text equals its source text.
- Everything else matches within tolerance: all AUROCs (overall, by origin, by length), group counts, mean scores,
  thresholds, flag rates, kappas, long-post false-positive rates and inter-detector Spearman. Bootstrap bounds match
  within 0.005.
- `spearman_ai_share` is wrong. The script's spearman() ranks with argsort-of-argsort, which breaks ties by file
  order. 474 of the 680 ai_share values are 0.0 and 147 are 1.0, so ties dominate.

| Detector | Recomputed (tie-aware) | Claimed |
|---|---|---|
| binoculars | 0.237 | 0.226 |
| fdg_falcon | 0.268 | 0.247 |
| meld | 0.301 | 0.249 |
| desklib | 0.231 | 0.209 |
| panel | 0.112 | 0.099 |
| fdg_llama | 0.055 | 0.059 (within tolerance) |

Shuffling row order moves the script's MELD value between 0.18 and 0.30.

**Claim 2 (four detectors and the panel below 0.5; MELD above 0.5 everywhere): VERIFIED as point estimates.**
- Overall: 0.394, 0.411, 0.416, 0.478, panel 0.412.
- local_writer: 0.378, 0.394, 0.472, 0.407, panel 0.428.
- MELD by origin: 0.633, 0.665, 0.939. By length: 0.727, 0.654, 0.779, 0.831.
- Caveat: the source-document bootstrap intervals include 0.5 for desklib overall [0.425, 0.533], fdg_llama in
  local_writer [0.399, 0.545] and the panel in local_writer [0.352, 0.503].

**Claim 3 (human vs base AUROC 0.96 or more; Pangram calls 448 of 619 base texts Human): VERIFIED as stated.**
- AUROCs: 1.000, 0.999, 0.999, 0.992, 0.961. The 448 of 619 is confirmed.
- Caveat: the human texts are longer (median 508 vs 241 words), and 32 of the 62 come from B25 and B28. Restricting
  to B31, where 30 human continuations share their openings and length with the 615 base continuations, desklib
  drops to 0.931 and MELD to 0.986.

**Claim 4 (false positives on the 400 long human posts): VERIFIED.**
- Binoculars 0/400, MELD 0/400, desklib 48/400 (12%).
- Binoculars' lowest document score is 0.910 against the 0.8536 threshold. But 20 of 2,299 512-token windows, spread
  over 19 posts, fall below it.
- MELD's highest score is 3.29 against 3.92. That 3.92 is the strictest of 16 genre groups; the pooled 1% offset is
  1.65.

**Claim 5 (detector code computes what it claims): PARTLY VERIFIED.**
- Fast-DetectGPT: I ran `_pair_stats` on random logits on the CPU against the released analytic criterion. The
  largest difference was 5.6e-6, and the orientation (higher = more AI) is right.
- Binoculars matches the paper's formula to 2e-7 but differs from the released metrics.py. The released code averages
  cross-perplexity over all L positions, including the last one (which predicts past the text), and perplexity over
  L-1. lf_detect uses L-1 for both. On random short sequences the gap reached 4.6% relative.
- Binoculars also deviates in two other ways. The 0.8536 threshold was set with the released code. That code scores
  only the first 512 tokens, so windowing the whole text is an extension, not "the published setting".
- MELD: the sha256 matches, `flagged` equals score > 3.9196 on all 1,593 rows, and p_ai is the sigmoid of the score.
- desklib matches the model card (mean pooling, linear head, sigmoid of 0.5 or more means AI). Multi-window documents
  are the mean of their windows.
- The score files are internally consistent: Binoculars `ai` is minus the score, single-window documents equal their
  window value, and token counts fit the window counts.

**Findings that change how the detectors should be used:**
1. The overall AUROC below 0.5 comes mostly from how the sample is mixed. Inside the base stratum every detector
   agrees with Pangram's direction, with intervals above 0.5. The disagreement sits in local_writer, which I take to
   be the project's own writer outputs: Binoculars, Fast-DetectGPT on Falcon and desklib run against Pangram there.
   Their AUROCs, averaged within each experiment, are 0.33, 0.34 and 0.35, and the pattern holds in every length bin;
   MELD is 0.69. Optimizing against the panel would push three of its four members opposite to Pangram.
2. The 5% false-positive thresholds taken from the long posts do not carry over to short texts. On the 62 short human
   calibration texts, MELD's flags 16% and Binoculars' 9.7%.

**Not verified:** any real model forward pass; how big the Binoculars off-by-one is on real text; whether the Pangram
labels themselves are right.

**Most important next check:** decide whether the panel should drop or reweight Binoculars, Fast-DetectGPT and
desklib, given that they run against Pangram on the local_writer texts.
