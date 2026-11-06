# Research agent report: long-form Pangram aggregation, length effects and base-model size

Saved from the agent's final report (2026-11-06). V means the agent read it in the primary source (section, table or page given); U means unverified. Figure values were read from the papers' SVG geometry; scratch copies are in the session scratchpad (`lenfig/`, `pgdocs/`, `lenweb/`).

## Brief given to the agent

Work at expert depth, start from raw data, verify with an external check, report what you could not verify.

GOAL BEHIND THE TASK: the humanizer project (~/personal/human, read its CLAUDE.md) is starting a long-form program: make whole AI-drafted blog posts of 1,500 to 4,000 words read human to Pangram (pangram.com, detector versions 4.0 of 2026-07-29 and 4.1 of 2026-10-19) without inventing facts. So far every test used texts of 235 to 800 words, mostly under one or two Pangram windows. Before we spend about 6,000 Pangram credits on long documents, the design must know (a) how Pangram turns a long document into a label (Human, Mixed, AI) and an AI share, and whether length by itself moves the verdict; (b) whether a bigger base model really reads more human, and at what length that was measured. Today is 2026-11-06.

WHAT EARLIER AGENTS REPORTED (treat as claims to verify against primary sources, not facts): `results/research/r2-primary-sources.md` section 3 and `results/research/b31-base-detectability.md` section 1. In short: Pangram 4 uses 512-token windows with stride 256, a calibrated CRF and a sentence-level majority vote; f_AI = (0.5 x AI-Assisted + AI-Generated characters) / total; document rule Human if f_human >= 0.90, AI if f_AI >= 0.80, otherwise Mixed; minimum 50 words, lower certainty under 150 words. HALO (arXiv 2609.31876) Table 6: raw base continuations, n=30, OLMo-2-7B 0.267 fraction_AI, Qwen3-8B 0.417, Llama-3-8B 0.282, Gemma-3-12B 0.167, Gemma-3-27B 0.085, OLMo-2-32B 0.033; up to 320 tokens; prompts written by the HALO agent.

TASKS
1. Pangram long-document aggregation. Read the Pangram 4 Technical Report (arXiv 2607.27183, full HTML including appendices), the Pangram 4.1 model card, Pangram's public docs and API reference (docs.pangram.com or wherever they live now; the v3 and v4 API endpoints and their response fields such as windows, segments, fraction_ai, fraction_ai_assisted, fraction_human, prediction labels, headline), and Pangram blog posts. Extract exactly: window size and stride; how windows map to sentences or characters; how the document label and AI share are computed from windows; whether there is a maximum document length or truncation; whether the "Mixed" label requires a share threshold; any statement or table of accuracy, false-positive rate or calibration by text length (including long documents, essays, and blog posts); how credits are charged (credits per word or per window, on the dashboard and the API; we assume about 1 credit per 100 words, verify or correct). Mark each item V (read in primary source, give the section or table) or U.
2. Length effects from third parties: any study (2025 to 2026) that measures Pangram verdicts or false-positive rates as a function of length, or on long human documents (theses, blog posts, books). Numbers and versions.
3. HALO size result. Re-read HALO's Table 5, Table 6 and Appendix A/B: confirm the numbers above, the exact continuation lengths and how a sample was chosen, prompt sources, and whether any length ablation exists. Then find every other primary source that relates base-model size to Pangram detection of raw base-model text. Important lead: PASTA (arXiv 2605.30526, v3) tested Qwen2.5 base models at 0.5B, 1.5B, 3B, 7B, 14B and 32B; extract the per-size base-model Pangram flag rates if they are reported anywhere (tables, appendices, figures; read SVG values if needed). Also Xu et al. (arXiv 2605.19516). State whether the evidence supports "bigger base model reads more human", at what lengths, and how it compares with this project's B31 result (no size trend across 2.8B to 24B, Spearman -0.30 on log parameters, p 0.21, 150 to 250-word continuations of human openings; see `results/REPORT-2026-11-04-lora.md` section 34).

RULES: read only. Use WebSearch and WebFetch (arxiv.org/html/<id>, arxiv.org/abs, docs pages, Wayback Machine if pages moved). Do not sign in anywhere, do not create accounts, do not call the Pangram API, do not download or run code. No emojis, no em dashes, spell out acronyms on first use, no blockquotes.

OUTPUT: write your full report to `/Users/henryvu/personal/human/results/research/longform-pangram-length.md`, starting with a short "Brief given to the agent" section (paste this brief) and then "## Report". Report under 1,200 words: numbered findings with V/U flags and exact citations (section, table, URL), then "Implications for a long-form design" (3 to 6 bullets), then "What I could not verify". Return the same report as your final message.

## Report

### A. How Pangram 4.x scores a long document

1. **Windows (V).** At most 512 tokens, stride 256, last window anchored to the document end; each window is fed twice (Repeat2) and logits are averaged over every window containing a token. Pangram 4 Technical Report (arXiv 2607.27183) Sec. 4.1 "Repeat2", Sec. 4.3.2; 4.0 model card "Model Inference".
2. **Windows to sentences (V).** A calibrated three-state conditional random field (CRF) labels every token; tokens join sentences by character midpoint; each sentence takes its tokens' majority label; runs shorter than L_min ("around 2 sentences", configurable) merge into the longer neighbour (Sec. 4.3.3).
3. **Label and AI share (V; corrects the earlier summary).** Document fractions are plain character shares per class (Sec. 4.3.4). Human if fraction_human >= 0.90, AI if fraction_ai >= 0.80 ("classified as AI-generated", model card), else Mixed (Sec. 5.1). The 0.5 x AI-Assisted formula is the training target of the 15-bucket segment head (Sec. 4.1 "Segment predictions"), not the reported fraction_ai. AI-Assisted characters count toward neither class. Mixed has no threshold of its own.
4. **API (V).** docs.pangram.com/api-reference/ai-detection: POST /task, model "pangram-4" (read `version`); fields prediction_short, headline, fraction_ai, fraction_ai_assisted, fraction_human, num_*_segments, windows. In 4.x `windows` are the non-overlapping output segments with per-segment labels and 4.1 class_probabilities, despite a stale tooltip calling them overlapping windows.
5. **Maximum length.** No truncation is described in the report (V). Dashboard: 18,725 words per scan (knowledge hub "minimum and maximum input sizes", reviewed 2026-07-24, V). API maximum per text: not stated (U). Bulk: at most 1,000 billable units per request (bulk-api docs, V).
6. **Accuracy by length (V, Fig. 4 SVGs).** Pangram 4 false negative rate 1.29% at 50-99 words falling to 0.19% at 300-499; false positive rate 0.020% falling to 0.0041% (Sec. 5.4). pangram.com/blog/is-pangram-accurate (2026-10-16) matches. **No Pangram figure covers anything over 499 words.** Only long-document result: Table 20, the VUB public fully-AI subset (papers over 4,000 words), 39 of 39 scored 80-100%.
7. **Context and interleaving (V).** Limitations: a section run alone "may receive a different prediction" than in full context. Table 7: one-sentence AI runs inside human text, tokenwise recall 62.9%, document error 18.3%; four sentences 85.4% and 6.8%; eight 92.3% and 3.5%.
8. **Credits (V, checked on raw data).** One credit is 100 words, rounded up per scan (knowledge hub "What is an AI detection credit?"); API unit is "one started word block per valid item", 100 words for Pangram 4 (bulk docs); $0.05 per 100 words, bulk 20% off; Professional includes "$200 of API credits monthly" (pricing page). Sum of ceil(words/100) over B31's 675 texts is 1,987 against 1,986 charged (`results/b31_verdicts.json`, ledger). A 1,500 to 4,000-word post costs 15 to 40 credits.

### B. Third-party length evidence

9. **Van Vlasselaer et al., Int. J. Educational Integrity 22:16, 29 Jun 2026.** 160 papers over 4,000 words; abstract: "All tools correctly identified fully human texts" (V, researchportal.vub.be). Pangram version unstated, pre-4.0 by date (U).
10. **Jabarian and Imas, BFI WP 2025-116 (V).** Pangram API v2025-05. Human novel excerpts average 967 words; false positive rate 0 on blogs, novels, resumes (Table 2).
11. **VeryFinePrint Substack, 15 Jul 2026 (V; pre-4.0).** 45 pre-ChatGPT books, 2,883,616 words: four flagged segments of 8,029, all OCR (optical character recognition) errors.
12. **Albrecht, LessWrong, 23 Sep 2026 (V, Pangram 4.0).** About 5,000 words of her LLM-assisted (large language model) writing: "about 30% of the passages" AI-Generated, longer excerpts Mixed. Anecdote.

Nothing measures Pangram 4.x on known-human text over 1,000 words.

### C. Base-model size

13. **HALO Table 6, App. A (V).** Brief's numbers exact. Median length 230 to 254 words; 4 samples per prompt, first with at least 50 words scored; 30 prompts written by the orchestrator (claude-opus-5) in an earlier OLMo-2-7B run. Pangram 4.0 by date. My checks: Spearman on log parameters over 6 models -0.81, p 0.05; OLMo-2 7B against 32B flagged 8/30 against 1/30, Fisher p 0.026; Gemma-3 12B against 27B 5 against 3, p 0.71. No length ablation; App. F's "a longer document is easier to detect" is an unmeasured instruction.
14. **HALO assembled answers (V).** Table 5 (n=30) Mythos: OLMo-2-7B 0.222, Gemma-3-27B 0.331, OLMo-2-32B 0.044. Table 1 (n=100, 304 to 842 words): 7B against 32B Mythos 0.165/0.061, FACTS 0.027/0.028, IFEval 0.399/0.232, HealthBench 0.740/0.661; 32B answers are also shorter.
15. **PASTA v3 (V).** No base rate for Qwen2.5 0.5B, 1.5B or 32B exists; they appear only in Table 1 (aligned models). Figure 6 (SVG): aligned-minus-base mean fraction_ai 0.81 (3B), 0.70 (7B), 0.82 (14B), so base means are at most about 0.19, 0.30, 0.18: no size trend. At most 400 tokens; Pangram version unstated.
16. **Xu et al. (V).** Raw base test at 8B only. Sizes appear only as HIP (Humanization by Iterative Paraphrasing) paraphrasers; Figure 3, Pangram human probability at round 10: Qwen3-Base 0.86, 0.88, 0.86, 0.77, 0.77 (0.6B to 14B), Llama-3 8B and 70B both 0.89. Pre-4 Pangram.
17. **Verdict.** "Bigger reads more human" holds only for 27B to 32B against 7B to 12B, on Pangram 4.0, at about 250-word continuations of AI-written prompts (n=30 each), plus HALO's 300 to 840-word answers. From 3B to 24B no source shows a trend: B31 (recomputed from `results/b31_model_level.json`: -0.30, p 0.21), PASTA, Xu. B31 does not contradict HALO: it tested no 27B or 32B model. No source measures size above about 850 words.

## Implications for a long-form design

- Target the flagged share, not the pass rate: Human needs 90% of characters labelled Human, AI-Assisted counts against it, so a 3,000-word post tolerates about 300 flagged words. Scattered single AI sentences are still caught at 63% recall.
- Inference to test (U): a long post averages over many windows, so its verdict should track the writer's mean flagged share. Every B31 base arm had a mean AI share of 0.10 or more, which predicts Mixed long posts even though 57 to 88% of short texts read Human. CRF smoothing could pull the other way.
- Calibrate first (spec section 8): cut 8 pre-2022 human blog posts and 8 pipeline outputs at 250, 500, 1,000, 2,000 and 4,000 words (78 credits each, about 1,250 total), plus sections scored alone. This also gives the missing long-document false positive rate.
- Log segments via `windows`. Check whether the Professional plan's $200 monthly API credit (4,000 to 5,000 hundred-word units) is live; the key last returned 402.
- Do not pick a larger writer on the size claim; if tested, pre-register a 27B to 32B arm against OLMo-2-13B at 250 and 2,000 words.

## What I could not verify

- API per-text maximum; L_min in tokens; length mix of the CRF calibration data.
- Pangram 4.x accuracy on human documents over 499 words; the VUB full text and its Pangram version.
- HALO's Pangram minor version and any confidence intervals; PASTA's Pangram version and base rates for 0.5B, 1.5B, 32B.
- Xu values are SVG readings (about plus or minus 0.01).
- Whether Henry's plan includes active API credit.
