# Outside judge: independent recomputation of B31's statistics

Saved verbatim from the outside-judge agent (2026-11-06, about 00:40). Its only input was `results/b31_verdicts.json`;
it read no report or summary. Scripts: the session scratchpad `judge/` folder (stats1.py, stats2.py, stats3.py,
checks.py, ablate.py), not kept in the repo.

## Report

I recomputed every requested statistic from the verdict file. The pre-registered contrasts P1 and P2 are both null. Texts continuing the same opening share detector outcomes across base models far more than chance would give (about 4 times the expected spread). Pythia-6.9b is detectably above the human control. I found no internal data errors, but olmo2-13b-q4 has 17 rows where 20 were expected.

The only input was /Users/henryvu/personal/human/results/b31_verdicts.json. I read no reports. "notH" below means the label was Mixed or AI.

**1. Per arm** (n, Human/Mixed/AI, notH, exact 95% interval, mean ai_share). VERIFIED: the scipy exact interval matches the beta-quantile formula.
Method: scipy binomtest with the exact method, cross-checked against beta.ppf.
- human 30, 30/0/0, .000 [.000,.116], .000
- olmo3-7b 30, 17/3/10, .433 [.255,.626], .391
- phi-2 27, 17/3/7, .370 [.194,.576], .314
- olmo3-7b-r5 30, 19/3/8, .367 [.199,.561], .309
- olmo3-7b-s1 30, 19/4/7, .367 [.199,.561], .319
- qwen3-8b 29, 19/3/7, .345 [.179,.543], .300
- qwen3.5-9b 29, 19/3/7, .345 [.179,.543], .294
- olmo3-7b-s2 30, 20/0/10, .333 [.173,.528], .319
- olmo3-7b-2t 29, 20/2/7, .310 [.153,.508], .276
- olmo3-7b-mct 30, 21/2/7, .300 [.147,.494], .253
- nemotron-9b 30, 21/4/5, .300 [.147,.494], .246
- mistral-small-24b 28, 20/3/5, .286 [.132,.487], .226
- pythia-6.9b 29, 21/2/6, .276 [.127,.472], .235
- olmo2-7b 29, 21/2/6, .276 [.127,.472], .226
- pythia-2.8b 30, 23/2/5, .233 [.099,.423], .215
- llama3.1-8b 26, 20/0/6, .231 [.090,.436], .225
- qwen2.5-7b 27, 21/1/5, .222 [.086,.423], .209
- olmo2-7b-s1 30, 24/0/6, .200 [.077,.386], .200
- olmo3-7b-genqa 30, 24/2/4, .200 [.077,.386], .159
- olmo2-13b 30, 25/1/4, .167 [.056,.347], .154
- gemma3-12b 25, 22/1/2, .120 [.025,.312], .101
- qwen3.5-9b-q4 20, 16/1/3, .200 [.057,.437], .177
- olmo2-13b-q4 17, 16/0/1, .059 [.001,.287], .059
- both instruct arms: 15, 0/0/15, 1.000 [.782,1.000], 1.000

**2. Paired contrasts.** Method: exact sign-flip over every sign pattern of the nonzero differences (a 200k Monte Carlo run agrees); percentile bootstrap with 20k resamples (BCa also computed); McNemar as an exact binomial on the discordant pairs.
- **P1** (olmo3-7b-s2 minus olmo3-7b-s1, 30 pairs): mean -0.0006, bootstrap [-0.176, 0.173], sign-flip p=0.997. McNemar discordant 5 vs 4, p=1.000.
- **P2** (olmo3-7b-s1 minus olmo2-7b-s1, 30 pairs): mean +0.119, bootstrap [-0.074, 0.313], sign-flip p=0.251. McNemar 3 vs 8, p=0.227.
- **Holm:** P1 0.997, P2 0.503.

**3. Same-opening clustering** (19 base arms, 552 rows). Method: variance across openings of the per-opening notH rate, against 20k shuffles of labels within each arm.
- Spread across openings: observed variance 0.0433 (SD 0.208); independent outcomes would give 0.0108 (SD 0.104), a ratio of 4.0, p about 0.0001. No shuffle beat the observed value (shuffle maximum 0.026).
- Per-opening rates run from 0.00 (h0610) to 0.74 (h0611).
- The result holds when shuffling only within the same genre (ratio 3.4), using non-olmo3 arms only (2.5), olmo3 variants only (2.2), or continuous ai_share (4.5). All p about 0.0001.

**4. pythia-6.9b minus human**: 29 pairs (pythia lacks h0603), mean +0.235, bootstrap [0.097, 0.388], BCa [0.110, 0.410]. Sign-flip p=0.0039, McNemar 0 vs 8, p=0.0078.

**5. Data checks:**
- **Clean:** 675 rows reconcile (6 batches of 100, plus 49, plus 26 llama). No duplicate names and no duplicate arm-opening pairs. Each opening has one genre, and the extension flag is set only for llama.
- **Labels agree with ai_share:** the label bands do not overlap. Human tops out at 0.019, Mixed runs 0.108 to 0.798, AI starts at 0.821.
- **olmo2-13b-q4 has n=17, not 20:** h0607, h0609 and h0614 are missing.
- **The q4 arms are fineweb-only.** Base arms score lower on fineweb (notH 0.253) than on essays (0.356), so q4 rates are not comparable to overall base-arm rates.
- **Filtered-out openings are not neutral.** h0604 is missing from 4 base arms, and among the arms that kept it its notH rate is 0.60. If the filters correlate with difficulty, they bias per-arm rates.
- **No batch effect:** chi-square p=0.88.

**Could not verify:**
- The texts themselves, and whether labels match the raw detector responses.
- Whether the mechanical filters ignored detector outcomes.
- That P1 and P2 were registered before data collection.
- What s1, s2 and the other arm names refer to.
- Which bootstrap interval the write-up used.

**Check next:** opening explains most of the variance (about 4 times what independence predicts), so treat the 30 openings as the sample size. Any comparison between arms must be paired by opening. Per-arm intervals that treat texts as independent are too narrow for generalizing to new openings. On that basis P2's +0.12 is not distinguishable from zero.
