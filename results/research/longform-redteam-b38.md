# Red team: B38 judge conclusion

Saved verbatim from the red-team agent's final report, 2026-11-06 about 13:55 CST. It was given the conclusion "J1
clears the bar and is useful for best-of-4 picking" and the raw files, and asked to attack it with its own analysis.
Scripts (load.py, a1.py to a17.py) are in the session scratchpad.

## Report

Red team on B38 J1: "clears the 0.70 bar and is useful for best-of-4 picking"

Short verdict. Both numbers reproduce exactly from the raw files. J1's out-of-fold (OOF) predictions match the script with a maximum difference of 0, and I recomputed 0.215 / 0.337 / 0.163 and the pair accuracy of 0.746. No training row comes from the 4 calibration posts or their sites. The gain over random is real: a random-ranking permutation gives p = 0.003. But the claim credits J1 for something several free rules already do, and J1's picks break the project's invent-nothing rule. Once the project's own content gates apply, J1 is the same as the existing pick rule.

All analysis is read-only, with scripts in the session scratchpad (load.py, a1.py to a17.py). Terms: AUROC is the area under the receiver operating characteristic curve. LOEO is leave-one-experiment-out. CI is confidence interval. C1 is B37's existing pick rule: among candidates that pass the form checks, have claim support of at least 0.90 and keep at least 50% of the words, take the one that copies least from its input.

### Ranked objections

**1. J1's picks select invented content and break the project's claim rule. Fatal for any unconstrained use, including driving the rewriter.**
- 7 of J1's 14 picks have claim support (entailed / total) below the project's 0.90 floor. Random picking would give about 3.2, and C1 gives 0.
- 8 of 14 picks fail at least one C1 gate.
- Candidates below the floor average a Pangram share of 0.195. Those above it average 0.376.
- Within sections, J1 correlates -0.43 (Spearman) with the count of unsupported claims, and Pangram correlates -0.41. Both rank texts with more unsupported claims as more human.
- explore's "claims_entailed 0.86" is precision (the share of the output's own claims that are supported), not how much content was kept. A retention proxy (claims entailed divided by the best candidate in the section) gives J1 0.67, random 0.82 and C1 0.91. J1's picks keep 60% of the input words, against 79% for C1.
- J1's actual first choice in section K_pf688f8ab80_3 was the 32-word candidate. It had J1 = 0.030, 6% of the input words, passed the form checks and had 4 of 4 claims supported. It was never scanned, so the 0.215 silently scores J1's second choice.
- This is a property of the target, not only of J1. Even the oracle picks 6 of 14 candidates below the floor and keeps 69% of the words. Pangram share rewards deleting and drifting from the source.
- Resolve: make the gates part of the objective, so the judge picks only among gated candidates. Objection 2 then applies.

**2. Once you compare against the existing rule or a free baseline, nothing is left. Fatal to "J1 is useful" as a decision; not fatal to "better than random".**
- Under C1's gates, J1 gets 0.288 and C1 gets 0.291. The difference is +0.003 (95% CI -0.07 to +0.08, clustered by post).
- With a 70% length floor plus the gates, J1 and least-copied pick the same candidate in 11 of 14 sections.
- Ungated, raw MELD (untrained, and rejected by gate 2a at AUROC 0.55) gets 0.213 against J1's 0.215 (difference CI -0.07 to +0.05). MELD's picks keep 75% of the words against J1's 60%. Weighted by words, MELD gets 0.208 and J1 gets 0.248.
- Other free rules: Fast-DetectGPT (Falcon), with its direction taken from the training data, gets 0.244. Least-copied gets 0.243 (J1 minus least-copied +0.028, CI -0.057 to +0.121).
- Within sections, copied share alone explains 35% of the share variance when each section is held out in turn. J1 alone explains 14%. Adding J1 to copied share raises that to 36 to 37%.
- The pre-registered comparison was against random, but the decision-relevant comparison is against C1.
- Resolve: the discordant-pick experiment at the end.

**3. The pre-registered bar does not measure the property being used. Serious.**
- J2 also clears the bar (0.722, within 0.013 of J1). Yet its within-section pair accuracy is 0.587 and its pick share 0.299, close to random's 0.337. Two judges that tie on the bar differ by 0.16 in pair accuracy.
- The training data contain no within-section seed contrasts at all. Not one of the 561 rewrite (document, experiment, cell) groups has two rows.
- The 0.735 is largely "which condition produced this text". A score built from no text at all, each experiment-cell's not-Human rate taken from the other folds, gets OOF AUROC 0.782. That beats J1.
- Within experiment-cells, J1 drops to 0.669.
- Short texts are not what drives the number: J1 gets 0.739 on rewrites under 500 words and 0.729 on 500 words and over.
- Resolve: define the bar on within-section pairs, which means scanning more seed sets.

**4. 0.62 is the better forecast for the next rewriter. Serious.**
- I ran LOEO on all 20 rewrite experiments: 11 of 20 fall below 0.70. The newest are B36 at 0.662 and B37 at 0.567, against B3 to B5 at 0.86 to 0.95.
- On B36/B37 rewrites, log words alone gets 0.641 (LOEO) and 0.651 (OOF). J1 gets 0.620 and 0.625.
- A group bootstrap of the 0.735 gives 0.685 to 0.782, with an 8% chance of falling below 0.70.
- In J1's favour: within B36's C300 and Cfull cells, its Spearman correlation with share is 0.42 to 0.44, against MELD's 0.28 to 0.30. It does carry some between-document signal.
- Resolve: report the newest experiment's LOEO as the forecast, and recheck each new rewriter on a small scanned within-section set.

**5. At the post level, best-of-4 cannot reach the goal even with a perfect judge, and the post shares are derived. Serious.**
- J1 makes 1 of 4 posts read Human. That is the same post random picking makes Human 87.5% of the time.
- The oracle leaves the other 3 posts at 0.157, 0.202 and 0.249, all above the 0.10 line. At k = 4 a perfect judge gains zero posts on this sample.
- I checked derived shares against scanned ones on the 6 Henry posts that have both. Derived minus scanned ranged from -0.046 to +0.063. For HR_bandits, the derived share is 0.084 (Human) but the scan read 0.13 (Mixed).
- Short texts score coarsely:
  - Candidates under 300 words came out 0, 0, 0, 0, 0.32 and 1.0.
  - Training rows under 200 words are exactly 0 in 81% of cases.
  - 4 of J1's 6 picks under 0.10 are short (85, 165, 233 and 284 words).
  - J1's section mean of 0.215 becomes 0.248 when weighted by words.
- Resolve: scan the assembled posts, and size k (or add repair) for the 0.10 line.

**6. Small n leaves every comparison that matters unresolved. Serious as a whole.**
- The gain over random holds up: post-clustered CI 0.042 to 0.205.
- Against the baselines, nothing is settled: versus MELD -0.002, versus least-copied +0.028, versus ungated C1 +0.076 (CI -0.016 to +0.188).
- There are effectively 3 informative posts, because every candidate of p7dd69444fe sits near 0.
- The 63 pairs are not independent. A Wilson interval on 47 of 63 gives 0.63 to 0.84.

**7. The pre-registered proxy gap is meaningless as specified. Minor.**
- J1's mean on the candidates is 0.628 against a mean share of 0.336. 8 of the 14 Human-labelled candidates have J1 above 0.5.
- Picking the minimum mechanically lowers the gap. Shuffling J1 within sections gives a gap reduction of -0.198 (95% -0.30 to -0.11); the observed value is -0.077.
- I calibrated J1 to the share scale with isotonic regression on the 90 rewrites that have a measured share. Predicted gain is then 0.107 against a realized 0.122, so there is no sign of over-optimism at best-of-4.
- Calibrated on all 888 rows instead, the predicted gain is 0.201 against 0.122 realized (61%). The answer depends on the calibration set.

**8. The explicit length feature is not the culprit. Minor; this refutes part of the brief.**
- Refitting without log words gives 0.209, with picks at 65% of the input words.
- Fixing words at the input length gives 0.196.
- The preference for short texts comes through the detectors and through Pangram itself. Removing the feature does not stop the content loss.

**9. Label details. Minor; partly unverified.**
- I found no "Possibly human" label anywhere in the B38 records, only Human, Mixed and AI, so I could not test that point.
- Pangram test-retest: one point. The stripped bandits original (2,663 words) scanned 0.24 in both B37 and B38.
- There is no retest of any short text.

### What I would require before using J1 to drive rewriter development

1. A pre-registered within-section test with the gates applied (form, support at least 0.90, length at least 0.70). Compare J1 against C1 and raw MELD with a margin of 0.05, on at least 60 sections from fresh calibration posts, with a post-clustered bootstrap.
2. Scans of the assembled posts, not derived shares.
3. If J1 becomes a training reward, a pressure test: scan the best-of-16 J1 pick against a random pick, and check realized against calibrated predicted gain, claim support and length.
4. The objective defined as share subject to the content gates.
5. Copied share added as a feature. It is free, and its candidate-level AUROC is 0.911.

### Cheapest experiment for the biggest doubt (does J1 beat C1 under the gates?)

- Generate 4 seeds for sections of about 16 more calibration-split posts (about $1 to $2 on Modal).
- Scan only the candidates on which J1-gated, C1 and MELD-gated disagree. J1 and C1 disagreed in 6 of 14 sections.
- The per-section SD of 0.146 implies about 67 sections for 80% power at a 0.05 difference. That comes to roughly 350 to 500 credits.
- The free alternative is 6 Henry section pairs (B36 HR against B37 HR2). J1 gets 3 of 6 right and MELD gets 3 of 6, which is uninformative.

### Not verified

- Pangram's handling of short texts and its test-retest noise.
- Whether the claim checker (a Sonnet judge) is right about the unsupported claims.
- That the derived post shares hold near the 0.10 line.
- MELD's tie with J1 may be luck on 14 sections. I tested about 12 rules, but MELD and C1 were both declared before B38, so those two are not chosen after seeing the data.

## Head session's notes (added after the report)

- Point 9: the 85-word candidate (a84b4605) is recorded as Human, share 0; the dashboard's detail panel said "Possibly
  human" for short text and the list label said Human. So the "Possibly human" reading is in b38_scan_times.txt, not in
  the label field.
- Accepted: objections 1, 2, 3 and 5 change the conclusion. B38 is reported as "J1 clears the registered bar, but in
  use it is no better than the existing C1 rule or raw MELD, and unconstrained it picks texts that break the claim
  rule". The registered numbers stand as registered.
