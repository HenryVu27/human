# Research agent report: B31, base-model detectability papers (HALO, PASTA, Xu et al.) and related work

Saved verbatim from the agent's final report (2026-11-06, about 00:05). Unverified unless the report says it read
the primary source (V); my own spot checks are in `b31-claims.md`.

## Brief given to the agent

Read HALO (2609.31876), PASTA (2605.30526) and Xu et al. (2605.19516) in full and check: HALO's "OLMo-2 beat Qwen3 and
Gemma-3", its raw-continuation table (OLMo-2-7B 0.267, Qwen3-8B 0.417, Gemma-3-27B 0.085, OLMo-2-32B 0.033) and the
HealthBench 0.852 row; PASTA's 98.5% vs 9.2% and its per-model base rates; Xu's Llama-3-8B base 98.8% human. Then search
for work comparing detector scores across base-model generations or linking them to pretraining-data date, AI text in
the crawl, or synthetic or instruction data; base models self-identifying as ChatGPT; Qwen bases behaving
instruction-tuned. Read only; under 1,200 words; work at expert depth, start from raw data, verify with an external
check, report what you could not verify.

## Report

## 1. HALO (arXiv 2609.31876, read v1 from 25 Sep 2026, the only version; full HTML)

- **V, model IDs (App. B, Table 6):** every base LM is a pretrained checkpoint, not an instruct model. Llama-3-8B is meta-llama/Meta-Llama-3-8B, Qwen3-8B is Qwen/Qwen3-8B-Base, OLMo-2-7B is allenai/OLMo-2-1124-7B, Gemma-3-12B and 27B are google/gemma-3-12b-pt and 27b-pt, and OLMo-2-32B is allenai/OLMo-2-0325-32B, which is also the main HALO base LM. Table 5 gives no IDs.
- **V, detector:** the detector is "Pangram 4"; Pangram 3.3.2 appears only in Table 4. No query dates are given. The metric is the mean of the document-level fraction_ai score (Sec. 3.2), and the AI and Mixed columns are counts.
- **(a) V, Table 5:** n=30, Mythos and HealthBench only, HALO p=0.90. Each cell is Pangram (lower is better) / quality.

| Base LM | Mythos | HealthBench |
|---|---|---|
| OLMo-2-7B | 0.222 / 0.733 | 0.898 / 0.569 |
| Qwen3-8B | 0.437 / 0.700 | 0.820 / 0.555 |
| Gemma-3-27B | 0.331 / 0.833 | 0.649 / 0.624 |
| OLMo-2-32B | 0.044 / 0.931 | 0.635 / 0.613 |

  Sec. 4.4 says OLMo-2 "uses much less data for this step" (mid-training) than Gemma-3, and then "We suspect this contributes." That is a hypothesis; nothing tests it.
- **(b) V, Table 6 (App. A), n=30:**

| Base LM | fraction_AI | Labeled AI (of 30) |
|---|---|---|
| Llama-3-8B | 0.282 | 7 |
| Qwen3-8B | 0.417 | 11 |
| OLMo-2-7B | 0.267 | 8 |
| OLMo-2-7B at top-p 1.0 | 0.380 | 11 |
| Gemma-3-12B | 0.167 | 5 |
| Gemma-3-27B | 0.085 | 2 |
| OLMo-2-32B | 0.033 | 1 |

  - Sampling: T=1.05, top-p 0.95, up to 320 tokens, 4 samples per prompt, and the first sample with at least 50 words is scored.
  - The prompts are 30 that the orchestrator wrote during an earlier HALO run with OLMo-2-7B (8 Mythos, 8 HealthBench, 7 IFEval, 7 FACTS), so the genres are mixed.
  - App. A suspects Qwen3's higher score comes from "the large amount of synthetic post-training data included in its pretraining mixture", citing the Qwen3 report. The tables give no confidence intervals.
- **My computed noise check:**
  - Approximate 95% intervals for the means: OLMo-2-7B 0.11 to 0.43, Qwen3-8B 0.24 to 0.59.
  - Fisher exact test on the AI counts: Qwen3-8B vs OLMo-2-7B p=0.58, vs Llama p=0.40, vs Gemma-3-27B p=0.010, vs OLMo-2-32B p=0.003. OLMo-2-32B vs Gemma-3-27B p=1.0.
  - Table 5 Mythos, OLMo-2-7B vs Qwen3-8B: difference 0.215, approximate interval ±0.23.
- **(c) V, Table 1 and Table 11:** in the HealthBench Base LM row, quality is 0.133±0.06 and Pangram is 0.852±0.07 (bootstrap 95% CI, n=100). The model is OLMo-2-32B prompted with few-shot "physician-written references" (App. B prints "22" examples, likely a typo for 2), T=1.05.
  - The same row on Mythos, prompted with human LitBench stories, scores 0.113.
  - On IFEval, prompted with the Agent's own AI responses, it scores 0.602.

## 2. PASTA (arXiv 2605.30526, read v3 from 22 Oct 2026)

- **V, title change:** v1 is "Measuring, Localizing, and Ablating Alignment Signatures in LLMs". v3 is retitled "...Reducing the AI-Like Writing Style of Post-Trained LLMs".
- **V, the headline numbers:** Sec. 3 H2 text says "Pangram flags 98.5% of aligned outputs versus 9.2% of base outputs", and GPTZero 84.5% vs 2.9%. Flagging means fraction_ai > 0.5 (App. D.1). This is aggregated over 8 pairs, 5 domains and 100 prefixes per domain.
  - Base outputs were filtered for degeneracy and re-ranked by a Claude Sonnet 4.6 judge before scoring.
  - Aligned models got chat templates (a confound the Limitations section concedes).
- **V, models (Table 4):** the base models are Meta-Llama-3.1-8B (also the base for the Tulu-3 pairs), Qwen2.5 at 0.5B, 1.5B, 3B, 7B, 14B and 32B, gemma-2-9b, Mistral-7B-v0.3 and allenai/Olmo-3-7B.
  - The H2 test uses 8 pairs: Llama, Tulu, Gemma-2-9B, Mistral, OLMo-3-7B, and Qwen2.5 at 3B, 7B and 14B.
  - There is no Qwen3, Gemma-3 or OLMo-2. No Pangram version or date is given.
- **No per-model base table exists.** I read Figure 6 from the SVG geometry. The values are mean Pangram Δ (aligned minus base):

| Pair | Pangram Δ |
|---|---|
| Gemma-2-9B | 1.00 |
| Tulu-3 | 1.00 |
| Mistral-7B | 0.94 |
| OLMo-3-7B | 0.86 |
| Llama-3.1-8B | 0.83 |
| Qwen2.5-14B | 0.82 |
| Qwen2.5-3B | 0.81 |
| Qwen2.5-7B | 0.70 |

  So the base score is at most 1 minus Δ: about 0.30 or less for Qwen2.5-7B and 0.14 or less for OLMo-3-7B.

## 3. Xu et al. (arXiv 2605.19516, read v1 from 19 May 2026, the only version)

- **V, headline numbers (Introduction):** Pangram gives 98.8% human probability to "Llama-3-8B" base and 17.1% to instruct; GPTZero gives 96.7% and 30.3%. Prompts use human prefixes.
  - The paper never says whether this is Llama 3 or 3.1, and gives no HF IDs.
  - The measure is mean human probability (Fig. 1 axis), over 256 human and 256 AI passages from RAID and MAGE, with each prefix cut to its first sentence.
  - The 0.6B to 70B models were used for HIP, not for this test. No Pangram version or query date is given.
- **Qwen3-8B values from Fig. 1:** I read these from the SVG, calibrated against the four values stated in the text, which matched to 3 decimals. Pangram mean human probability:

| Model | Human prefix | AI prefix |
|---|---|---|
| Qwen3-Base | 0.875 ±0.041 | 0.770 |
| Qwen3-Instruct | 0.286 | 0.203 |
| Llama3-Base | 0.988 ±0.012 | 0.937 |

  Qwen3-Base vs Llama3-Base on human prefixes gives z≈5.
- **V, the post-training claim:** the paper says detectors "appear to be sensitive to the statistical effects of post-training." That is an interpretation; the paper does not test pretraining data at all.

## 4. Literature search (V = I read the primary source)

- **V. Visokay, McCormick et al., "The uneven rise of AI-generated web content", arXiv 2610.36631, 27 Oct 2026.**
  - Method: 71 Common Crawl snapshots from 2019 to 2026, scored with open Pangram plus Binoculars, and a Bayesian measurement-error model.
  - Result: about 24% of pages in Aug 2026 contain AI text (95% credible interval 22.9 to 24.4). The share rose 0.2 points a year to Feb 2023, 4.6 a year to Jan 2025, then 8.1 a year. English pages are at 32.8%.
  - Caveat: this measures the raw crawl, not filtered pretraining mixes.
- **V. Zhong, LessWrong, 30 Jul 2026.**
  - OLMo-3-32B base calls itself GPT 25.6% of the time and Claude 4.0%.
  - Across 9 base models, the effects "grow with training-data cutoff". The OLMo-3 corpus has 62.8M ChatGPT mentions (infini-gram), and Qwen3.5 base models call themselves Qwen.
  - Caveat: blog post, most numbers only in charts.
- **V. Kissane et al., Alignment Forum, 29 Sep 2024.**
  - Base models refuse about 48% of 100 harmful prompts, against about 90% for chat models.
  - LLaMA-1, trained on pre-ChatGPT data, also refuses, which cuts against H1.
- **V. Qwen3 report §3.1.** Qwen2.5, Qwen2.5-Math and Qwen2.5-Coder synthesized "trillions" of tokens, including instruction-style text. The report never says post-training data went into pretraining.
- **V. OLMo 2 Table 5.** The mid-training mix includes FLAN (17.0B tokens) plus synthetic math such as TinyGSM-MIND (6.48B) and MathCoder2 (3.87B).
- **V. OLMo 3 §2.1.** Mid-training adds "instruction data and thinking traces", and the crawl cutoff is 31 Dec 2024.
- **V. Pangram 4 report, 29 Jul 2026.** Base-model outputs are never mentioned; all evaluation generators are chat models.
- **V. HF Leaderboard discussion #941, 2024.** Qwen base models score about 40 on IFEval, against an expected 15 or less for base models; Qwen never answered.
- **U. Graphite/GPTZero:** about 50% of new web articles are AI-written. I only saw search snippets.
- **Not found:** any paper that compares detector scores across base-model release dates.

## Claims the summaries got wrong or overstated

1. **"OLMo-2 beat Qwen3 and Gemma-3":** only true on Mythos. On HealthBench, OLMo-2-32B (0.635) and Gemma-3-27B (0.649) are tied, Gemma has higher quality, and Qwen3-8B beats OLMo-2-7B (0.820 vs 0.898). The mid-training explanation is labeled "suspect".
2. **The Table 6 numbers are right, but:**
   - The 7B-scale gap is noise (p=0.58).
   - Changing top-p alone moves OLMo-2-7B from 0.267 to 0.380.
   - The prompts came from an OLMo-2-7B run.
   - The summary left out Llama 0.282 and Gemma-12B 0.167.
   - The genre is mixed, not one genre.
3. **0.852 is a Pangram AI score, not a quality score.** Also, HealthBench §7 says some physician references were edited versions of GPT-4o, o1-preview, GPT-4.1 or o3 answers. The Base LM rows suggest detection follows the style of the few-shot examples (0.113 / 0.602 / 0.852).
4. **PASTA's 98.5/9.2:**
   - The v3 Figure 3 shows 96.1/9.0, and GPTZero 82.3/3.3, so text and figure disagree.
   - The 98.5/9.2 is pooled across 8 pairs after a base-output selection step.
   - The models are Qwen2.5, not Qwen3.
   - The title has changed since v1.
5. **"Llama-3-8B":** Xu never states the exact checkpoint.

## What I could not verify

- Pangram query dates in any of the three papers. My guess that Xu, and probably PASTA v1, used a pre-v4 Pangram rests only on dates.
- Which HealthBench reference group HALO drew its few-shot examples from.
- PASTA's per-model base rates beyond the bounds above, and its total n.
- Model release dates; none of the papers state them.
- The amount of Gemma-3 mid-training data.
- Graphite's numbers.
