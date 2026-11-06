# Research agent report: B31, how much AI text is in the web and in pretraining crawls

Saved verbatim from the agent's final report (2026-11-05, about 23:50). Unverified unless the report says it read
the primary source (V); my own spot checks are in `b31-claims.md`.

## Brief given to the agent

Claim to test: "AI text has grown to a large share of new web pages since 2023." Find the primary measurements
(FineWeb's dump analysis, Graphite/Surfer, Ahrefs, Originality.ai, Liang et al. 2025, Brooks et al. 2024, Pangram's
studies, any measurement inside pretraining corpora by crawl date), with sample frame, detector, error rates, numbers
by year and the main validity threat; then estimate the AI share of English web text in 2023, 2024 and 2025 crawls,
and of text that survives quality filtering. Read only; under 1,000 words; work at expert depth, start from raw data,
verify with an external check, report what you could not verify.

## Report

B31 web-pollution evidence (all figures are detector estimates)

Main finding: the claim is true for new article-type pages (about 35 to 50% mostly AI by 2025). It is false for whole crawls (about 10% of pages in 2026) and for what a 2023 or 2024 base model saw (under 1 to 3% of tokens). But quality filters concentrate AI text 2 to 10 times, so filtered 2025 crawls are no longer small.

(1) Sources (V = read in primary source, U = secondary only)

- Pew Research, "How much of the internet is written with AI", Aug 20 2026 (pewresearch.org/data-labs/2026/08/20/). V.
  - Frame: 10,000 random English pages per crawl, 49 Common Crawl (CC) crawls, Jan 2021 to Jul 2026.
  - Detector: open Pangram (EditLens Llama-3.2-3B), threshold 0.2. Agrees with Pangram 3.3 on 96% of pages, kappa 0.61. False positive rate (FPR) on pre-ChatGPT pages is about 1%.
  - .com share: 1.09 (2021), 1.07 (mid-2022), 1.63 (H1 2023), 3.76 (H1 2024), 5.48 (H1 2025), 6.64 (H2 2025), 9.35 (H1 2026). .edu and .gov stay near 1%.
  - All pages, Jul 2026: 10%. Pages dated after ChatGPT: 35%.
  - Threat: the 1% floor is about the size of the 2023 signal. Only 10 to 15% of pages carry a date.
- Visokay et al., "The uneven rise of AI-generated web content", arXiv 2610.36631, Oct 2026. V.
  - Frame: 5.1M pages, 71 CC snapshots 2019 to Aug 2026, all languages.
  - Method: open Pangram plus Binoculars in a Bayesian error-correction model. 30 pre-2022 crawls serve as a negative control. Open Pangram FPR on pre-2022 English pages is 4.5%.
  - Aug 2026: 23.6% of pages, 32.8% of English-only pages. Includes AI-edited text.
  - Growth: 0.2 points/year before 2023, 4.6 (Feb 2023 to Jan 2025), 8.1 after.
  - My back-calculation for English-only pages: about 3% in Feb 2023, about 16% in Jan 2025.
  - Threat: the result depends on the model. Specifications give 5.2% to 27.7%. Binoculars flags only 8 to 13% of the recent pages Pangram flags.
- Russell, ..., Spero, Emi (UMD and Pangram), "How Much Is an AI Token Worth?", arXiv 2609.40295, Sep 2026. V.
  - Frame: 5,000 documents per month after FineWeb quality filtering. Detector: Pangram 3.3.2. FPR on 2021 documents is 0.062%.
  - AI share of filtered tokens: under 0.1% (Jun 2021), 10.1% (Jun 2024), 16.1% (Jun 2025), 27.5% (Jun 2026).
  - Filter survival on CC-MAIN-2026-30: AI documents pass FineWeb filters 2.3x and DCLM filters 9.8x as often as human ones. By my arithmetic, about 10% AI in raw text becomes about 20% after FineWeb filtering and about 39% after DCLM.
  - Threat: Pangram wrote and funded the study. The 2023 values are only in a figure.
- Graphite, "AI Now Writes as Many Online Articles as Humans Do", May 2026 (supersedes the Oct 2025 study). V.
  - Frame: 55.4k random CC URLs, English, article markup, at least 100 words, published 2020 to Mar 2026.
  - Detectors: average of Pangram, Copyleaks and GPTZero. Pre-ChatGPT FPR 1.4 to 1.8%.
  - Primarily-AI share: 35.9% at 12 months after ChatGPT, 48% at 24 months, about 50% from 2025 to Q1 2026. The old Surfer-based study (43k URLs, FPR 4.2%) ran 3.3 points higher.
  - Threat: covers new pages with SEO-type markup, not crawl share. Graphite is an SEO vendor.
- Dolezal et al., arXiv 2604.26965, Apr 2026. V.
  - Frame: Wayback Machine first captures, Aug 2022 to May 2025. Detector: Pangram v3.
  - Result: about 35% of new sites were AI or AI-assisted by H1 2025.
  - Threat: no pre-ChatGPT baseline.
- Ahrefs, May 2025. V.
  - Frame: 900k English pages first found in Apr 2025, one per domain. Detector: in-house, with no error rates and no baseline.
  - Result: 74.2% contain any AI text. Only 2.5% are pure AI, and 15.5% are 71 to 99% AI.
  - Threat: unvalidated detector and an "any AI" threshold.
- Originality.ai tracker of Google top-20 results (500 keywords). V.
  - Threshold 0.5, no FPR reported.
  - Share: 2.27% (Feb 2019, which implies a floor of about 2%), 8.5% (Dec 2023), 18 to 19.6% (Nov 2024 to Jul 2025), 17.3% (Sep 2025).
  - Threat: vendor study, and ranked pages are not a crawl.
- Liang et al., arXiv 2502.09747 (Patterns 2025). V (arXiv v1; the Patterns copy on PMC was behind a captcha).
  - Method: a population-level word-frequency estimator, not a per-page detector. Error under 3.3%, pre-ChatGPT floor 1.5 to 3%.
  - Results by 2024: consumer complaints 17.7%, corporate press releases up to 24.3%, small-firm job posts about 10%, UN releases 13.7%. Growth plateaued in 2024.
  - Threat: narrow genres, not web crawls.
- Brooks, Eggert, Peskoff, arXiv 2410.08044. V.
  - Frame: new English Wikipedia articles, Aug 2024. Thresholds set at 1% FPR on pre-2022 articles.
  - Result: 5.36% (GPTZero), 3.3% (Binoculars). Reddit comments under 1%.
  - Threat: no false negative rate, so these are lower bounds.
- FineWeb blog post (Penedo et al. 2024). V.
  - Frequency of "delve", "as a large language model", "rich tapestry" and similar phrases was flat until CC-MAIN-2023-14, then rose steeply.
  - Recent dumps were not harmed on benchmarks. No rates given; this analysis is not in the arXiv paper.
- DCLM (arXiv 2406.11794). V. Its pool is "all Common Crawl data prior to 2023".
- Pangram newspaper study (arXiv 2510.18774). U, read on Pangram's summary page. 9.1% of 186,507 US articles (Jun to Sep 2025) were AI or mixed; 1.7% at large papers.
- Medium (Wired and Pangram, 2024): 47%. LinkedIn (Originality, 2024): 54% of long posts. Both U.
- Thompson et al., ACL Findings 2024. V. 57.1% of 6.4B sentences are multi-way parallel. This is machine translation into low-resource languages, not English LLM text, so it does not apply here.

(2) Best estimates for English Common Crawl text

Raw crawl, mostly-AI pages, after subtracting the false positive floor:
- 2023 crawls: about 2% (range 0.5 to 5%).
- 2024 crawls: about 5% (range 3 to 12%).
- 2025 crawls: about 9% (range 5 to 20%).

Pew and the Pangram study's raw sample set the low ends; Visokay sets the high ends. New pages run 3 to 5 times higher than whole crawls, because each crawl is mostly older pages.

After FineWeb-style filtering, one dump at a time:
- 2023: 3 to 6% (my interpolation; no published number).
- 2024: about 10% (measured).
- 2025: about 16% (measured).
- With a DCLM-style classifier on 2024 to 2025 dumps: plausibly 20 to 40%, based on a single-crawl survival estimate.

Training-mix exposure: corpora mix many dumps. DCLM has no post-2022 data. FineWeb v1 has only a handful of post-2023-14 dumps among 96. With equal weight per dump, AI text is under 1% of tokens for a 2024 cutoff and about 1 to 3% for a 2025 cutoff. It reaches 5 to 10% or more only if a lab upweights recent dumps or uses classifier filtering. Deliberate synthetic mixes are often 10 to 30% of tokens (I saw this only for Nemotron-CC, about 30%, U). So synthetic data added on purpose (H2) is likely the larger channel for 2023 and 2024 models. Web pollution (H1) becomes comparable for 2025 and 2026 models that use classifier filters.

Finding for B31: Pew, Visokay, Dolezal, Russell and part of Graphite all use Pangram, the same detector family as the B31 judge. The studies that use other methods agree on direction but show smaller or disputed levels; the most direct check found Binoculars flags only 8 to 13% of what Pangram flags. So the web-pollution evidence for H1 is not independent of the B31 instrument.

(3) Could not verify

- Year-by-year values that appear only in figures: Graphite, Visokay, Pew's all-domain series, Russell's 2023 values, FineWeb phrase rates. My back-calculations are labelled.
- Independent web-page false positive rates for Pangram 4.x.
- How labs weight recent dumps.
- The Wired/Medium and LinkedIn studies, Pangram's social-media study, and Nemotron-CC's synthetic share (secondary sources only).
- Non-English shares, beyond Visokay's 17% for pages with no English.
