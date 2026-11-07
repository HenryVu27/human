# Pangram as it stands on 2026-11-06: research for attempt 2

Research agent report, written 2026-11-06 (Friday evening, CST). Read only: no account created, no API (application programming interface) call made, no money spent. Raw copies of the pages and data I read are in the session scratchpad (`pg/`, `sgpt/`) under /private/tmp/claude-501/-Users-henryvu--claude-spares-spare-s6HQlu/cbf959c7-1fb4-4dcb-918e-c248455f5f2d/scratchpad/.

Tags: [primary, verified] means I read the primary page or file myself (usually the raw HTML or Markdown, not a summary). [primary, unverified] means a primary source exists but I saw it only through a summarizer or partially. [secondary] means someone else's account.

Things the project already knew (512-token windows with stride 256, the 90% Human and 80% AI thresholds, credits per 100 words, the $200 Professional API credit, the 4.1 class_probabilities field) are confirmed below only where I re-read them; the rest of this report is new.

## Bottom line

1. **No text model after 4.1.** As of the evening of 2026-11-06 the latest text model is Pangram 4.1 (2026-10-19). Pangram's own pages all point to it. The only launch since then is image and video (Image 1.0, 2026-11-04).
2. **Drift is officially possible without notice.** The API docs now say the `pangram-4` selector can serve a different minor version "without changing the selector". Each response carries a `version` field. No changelog page exists. The post-processing settings (minimum segment length, calibration, humanizer threshold) are described as configurable and "may vary between model releases".
3. **The API's `windows` are not the 512-token windows.** They are the final segments: non-overlapping, sentence-aligned, at least about 2 sentences each, with start and end offsets, a label, a score and (in 4.1) three class probabilities. The 512-token windows are internal and never returned. Sentences end at terminal punctuation, at a blank line, or at the end of the document. That means every Markdown heading, list item and code or math line on its own line becomes its own "sentence".
4. **Markdown, code, "instructions, recipes and technical manuals" and math-dominated text are officially out of scope for 4.1.** Pangram's own call for evaluations (posted 2026-11-06) lists technical writing, math and code as open questions. An independent paper (Duke and IISc, 2026-10-15) finds Pangram 4 weak on math-heavy text and very weak on Claude Opus 5.5 and GPT-6 passages written with the full paper as context: 22 to 25% flagged on prose.
5. **One public claim with per-sample data says a content-keeping humanizer passes Pangram 4.1.** StealthGPT Super scored under 10% AI on 41 of 50 essays of 364 to 997 words. Only 26 of 50 also had zero fact errors, and that check is StealthGPT's own, unpublished one. This is vendor data: outputs are withheld and the method is undisclosed. A site that looks independent (HumanizerEval) republishes the same numbers. Nothing on technical posts.
6. **The API is probably within reach.** The pricing page today says Professional includes "$200 monthly API credits" (about 4,000 hundred-word units, or 5,000 through the bulk API). An older help article (reviewed 2026-07-24) says the opposite. The 402 error in attempt 1 came on the Individual trial, so a single retry is the only way to settle it.

## Q1. Versions after 4.1

| Claim | Source | Date | Tag |
|---|---|---|---|
| 4.1 released 2026-10-19 as "successor to Pangram 4, with improvements to overall accuracy and performance under uncertainty". Inputs, training and inference "No change from Pangram 4". The only new output is `class_probabilities`. "Model resolution: Slightly improved from Pangram 4. You may occasionally see shorter segments in the detection readout." | https://www.pangram.com/research/model-card/pangram-4-1 | 2026-10-19 | [primary, verified] |
| https://www.pangram.com/research now redirects to the 4.1 model card. The model-card version selector lists 4.1, 4.0, 3.3, 3.2 and 3.1, and nothing newer. | same, checked by HTTP redirect today | 2026-11-06 | [primary, verified] |
| Pricing page: "Text (Pangram 4.1): $0.05 per 100 words". | https://www.pangram.com/pricing | read 2026-11-06 | [primary, verified] |
| Docs repo commit "Update docs for Pangram 4.1 and current pricing page" (2026-11-02). It adds `class_probabilities` and the example version "4.1". Later commits on 2026-11-04 concern image and video only. | https://github.com/pangramlabs/docs/commit/c6daf96a1eaca903660e9a726365d2c393e2fac0 | 2026-11-02 | [primary, verified] |
| Blog since 4.1: "Is Pangram accurate?" (10-16), detection posts for Claude Haiku 5.5, GPT-6.1 Sol and Gemini 4 Argon (11-02, all on 4.1, no retraining), Pangram Image 1.0 (11-04), "A call for new Pangram evaluations" (11-06). No 4.2 or 5. | https://www.pangram.com/blog | 2026-11-06 | [primary, verified] |
| Haiku 5.5 post: 4.1 flags 2,365 of 2,372 outputs (99.70%) and says "Pangram doesn't need to be retrained for every new release". | https://www.pangram.com/blog/can-pangram-detect-claude-haiku-5-5 | 2026-11-02 | [primary, unverified] (read through summarizer) |
| 4.1 against 4.0 on the same 520,000 English AI generations: false negative rate (FNR) 0.3652% against 0.3396%. The English false positive rate (FPR) set was changed (cleaned to 781,981 documents, "non-textual features" removed) and recalibrated to "roughly 1 in 10,000". 4.1 FPR is 0.0090%, so it is not comparable with 4.0's 0.0041%. Verdict flips under small edits fell from 1.08% to 0.15% (29,103 paired edits). | 4.1 model card; 4.0 model card https://www.pangram.com/research/model-card/pangram-4 | 2026-10-19, 2026-07-29 | [primary, verified] |
| SDK 1.1.1 (2026-11-04): the `model` argument is required after 2026-09-30, and the "currently Image 0.2" default claims were removed. Text docs never state what `default` resolves to now. | https://github.com/pangramlabs/pangram-sdk (commits #38, #39); https://docs.pangram.com/api-reference/models.md | 2026-11-04 | [primary, verified] |

No X (formerly Twitter) post by Pangram staff announcing 4.2 or 5 turned up in web search. X was not read directly.

## Q2. How Pangram scores a long document

All from the Pangram 4 Technical Report, arXiv 2607.27183 v1 (2026-07-29), sections 3.5, 4.1 and 4.3, read in full HTML [primary, verified]. The S3 PDF copy has Last-Modified 2026-07-29, so it is the same version. The 4.1 card says inference and document-level outputs are "No change from Pangram 4" [primary, verified].

1. **Windows.** The context length is 512 tokens. "We divide the document into overlapping windows of at most 512 source tokens with a stride of 256; the final window is anchored to the end of the document." Each window is fed twice (Repeat2) and only the second copy is read. Each token gets logits from every window it falls in (two windows, except at the edges), averaged into one 6-vector: the 3 token-head logits plus a 3-class prior projected from the 15-bucket segment head. Sec. 4.3.2 and 4.3.3.
2. **The tokenizer is unknown.** The backbone is "a popular open-weight MoE (mixture of experts) model", anonymized (Sec. 4.1). My estimate, not checked: at about 1.3 tokens per English word, a window is about 390 words and the stride about 195. The API returns `token_length` and `word_count` per segment, so the ratio can be measured from one scan.
3. **Decoding.** Calibrated unary scores (a multinomial logistic model whose "parameters are fitted on held-out calibration data and may vary between model releases") feed a three-state linear-chain CRF (conditional random field) with a Potts smoothness penalty. Strong evidence from the mixed-authorship head relaxes that penalty, which lets labels change more easily where that head finds a mix. Viterbi gives the labels; forward-backward gives the marginals. Sec. 4.3.3.
4. **Sentence voting.** "Sentences end at terminal punctuation (including a trailing quote or bracket), a blank line, or the end of the document. Tokens are assigned to sentences by character midpoint. Every token in a sentence is replaced by the sentence's majority Viterbi label." Sec. 4.3.3.
5. **Minimum run.** Any run shorter than L_min merges into a neighbour: the only neighbour, the neighbour both sides share, or else the longer neighbour. "The value of [L_min] is a configurable postprocessing choice rather than a fixed property of the model." The 4.0 model card says it is "currently tuned to around 2 sentences". 4.1 says resolution is "slightly improved" and shorter segments may appear, which suggests L_min or the smoothing was lowered (inference, not verified).
6. **Document fractions and label.** Segment fractions are computed by character length. Human if fraction_human >= 0.90, AI if fraction_ai >= 0.80, Mixed otherwise (4.0 model card, "Discrete classification").
   - AI-Assisted characters count toward neither 0.90 nor 0.80. So "Human needs under about 10% flagged" means under 10% of characters labelled AI-Generated or AI-Assisted.
   - The project measures words. Characters and words agree for prose but not for LaTeX or code, which pack more characters per "word".
7. **Confidence** is the peakedness of the CRF marginals before sentence voting and merging: "not a recalibrated probability that the final constrained label is correct" (Sec. 4.3.5). `class_probabilities` (4.1) are segment posteriors; how they are averaged over a segment is not documented.
8. **Context effects.** "A section of a paper run in isolation may receive a different prediction than it does within the full context of the paper" (Limitations).
9. **Determinism.** "Deterministic tie-breaking is used to make the operation fully reproducible" (Sec. 4.3.3). The same text on the same version and settings should return exactly the same output. This is the basis for the drift check in the implications.
10. **Preprocessing.** "Pangram removes adversarial Unicode characters and normalizes mixed-script homoglyph attacks before tokenization" (4.0 model card, "Preprocessing"). The API "may normalize the submitted text before inference; window offsets refer to this returned value" (ai-detection docs). The returned `text` field shows exactly what was scored.
11. **The humanizer head** is a stop-gradient probe. It is not part of the CRF and does not change labels or fractions. `is_humanized` fires at `humanizer_score >= 0.91` "by default at release". The paper describes it as "applied when Pangram 4 detects evidence of AI-generated content" (Sec. 3.4).
12. **Maximum length.** The dashboard limit is 18,725 words per scan; file uploads are capped at 30 MB. "We can handle large documents via API through batching and chunking." The page was last reviewed 2026-07-24 (https://www.pangram.com/knowledge-hub/minimum-and-maximum-input-sizes) [primary, verified]. No per-text API maximum is documented.

## Q3. The API on the Professional plan

| Claim | Source | Date | Tag |
|---|---|---|---|
| "The Individual plan includes $10 in monthly API credits, while our Professional plan includes $200 monthly API credits, at no extra charge." Bulk text API 20% off. "Create keys and add credits in the API dashboard." | https://www.pangram.com/pricing | read 2026-11-06 | [primary, verified] |
| Conflict: an older help article says "Note: API access isn't part of individual plans" and offers a pay-as-you-go Developer option at $0.05 per 100 words. It predates the API-credit wording. | https://www.pangram.com/knowledge-hub/pangram-subscription-tiers (last reviewed 2026-07-24) | 2026-07-24 | [primary, verified] |
| Pangram MCP (Model Context Protocol) server: tools `check_for_ai` ("summary scores and segment-level detail"), `check_for_similarity`, `list_models`. "Usage is billed to your API credit balance, not your dashboard scan balance." | https://www.pangram.com/solutions/mcp | read 2026-11-06 | [primary, unverified] (summarizer) |
| Endpoints: `POST https://text.external-api.pangram.com/task` (body `text`, `model`, `public_dashboard_link`) returns a `task_id`; then poll `GET /task/{task_id}` until `STAGE_SUCCESS` or `STAGE_FAILED`. `GET /models` lists the selectors a key may use (example: `default`, `pangram-4`). | https://docs.pangram.com/api-reference/ai-detection.md, /models.md, /introduction.md | docs as of 2026-11-02 | [primary, verified] |
| Document fields: `text` (normalized input), `version`, `headline`, `prediction`, `prediction_short` (AI, Human, Mixed), `fraction_ai`, `fraction_ai_assisted`, `fraction_human`, `num_ai_segments`, `num_ai_assisted_segments`, `num_human_segments`, `dashboard_link`, `windows`. | same | | [primary, verified] |
| Per-`windows` fields: `text`, `label` (AI-Generated, AI-Assisted, Human Written), `ai_assistance_score` (P(AI-Generated) + 0.5 P(AI-Assisted) per the 4.0 card), `confidence` (High, Medium, Low), `start_index`, `end_index` (character offsets into the returned `text`), `word_count`, `token_length`, `is_humanized`, `humanizer_score`, `class_probabilities` (4.1 only; order Human, AI-Assisted, AI-Generated). | same; 4.0 model card | | [primary, verified] |
| The docs tooltip still says windows are "overlapping segments ... each classified independently". The 4.0 model card says the output is "a complete, non-overlapping sequence of variable-length segments covering the analyzed text". The example response shows non-overlapping offsets (0 to 21, 21 to 35). The tooltip is stale. | ai-detection docs; 4.0 card line "Pangram 4 returns a complete, non-overlapping sequence" | | [primary, verified] |
| Bulk API: `POST /bulk` with `items` (`text`, optional `id`) or `text[]`, one `model` per job. The billable unit is "one started word block per valid item: 100 words for Pangram 4"; at most 1,000 billable units per request (else 413). Results are paginated (limit up to 1,000) and kept 48 hours. Each result has the same `windows` fields; the bulk page omits `class_probabilities`, so I could not tell whether bulk returns them. SDK 1.1.x adds an idempotency key (2026-08-27). | https://docs.pangram.com/api-reference/bulk-api.md; SDK commit #34 | | [primary, verified] |
| Rate limits are not published. The 429 error is "The API key exceeds its configured rate limit". The SDK retries 429 and 5xx responses, honouring `Retry-After`. 402 means "The account has insufficient credits"; 403 means the model is not enabled for the key. | introduction.md; sdk/python.md | | [primary, verified] |
| The old synchronous `POST https://text.api.pangram.com/v3` and the sliding-window endpoint (with `max_ai_likelihood`, `avg_ai_likelihood`, `fraction_ai_content` = share of windows) are deprecated. | deprecated-endpoints.md | | [primary, verified] |
| Dashboard: segments are highlighted inline (red AI, yellow AI-assisted, green Human), and a dropdown under the score shows "a graph of segments and AI predictions throughout the text". So segment data is in the dashboard page as well. | https://www.pangram.com/knowledge-hub/what-are-ai-segments (reviewed 2026-07-24) | | [primary, verified] |

Budget arithmetic (mine): $200 at $0.05 is 4,000 hundred-word units a month, or 5,000 at the bulk rate of $0.04. A 2,500-word post costs 25 units, so 160 to 200 post scans a month through the API. The dashboard allowance on Professional is 1,500,000 words a month (help article), about 15,000 credits.

## Q4. Math, code, tables, lists, Markdown, headings

| Claim | Source | Date | Tag |
|---|---|---|---|
| 4.1 out of scope: "code, markup, or Markdown text; tables of contents and reference sections; templated or automated writing; AI translations, such as from Google Translate; instructions, recipes and technical manuals; text dominated by mathematical notation; and figure text like axis labels or tabular data." Markdown is newly named in 4.1; the 4.0 card did not mention it. | 4.1 model card, "Intended usage and limitations" | 2026-10-19 | [primary, verified] |
| 4.0 card: "For best results, human-written headers, footers, instructions, and other extraneous formatting should be removed before checking a document." Raw text or .docx are preferred to PDF. | 4.0 model card | 2026-07-29 | [primary, verified] |
| Sentence boundaries include "a blank line". Headings, list items, table rows and code or display-math lines separated by line breaks become separate sentences for voting and are then merged into neighbours if shorter than L_min. Whether a single newline (without a blank line) splits is not stated. | Tech report Sec. 4.3.3 | 2026-07-29 | [primary, verified] |
| The AI false-negative benchmark excluded "math, and coding-related inquiries" as out of scope, so there is no vendor accuracy number for them. | Tech report Sec. 5.2 | | [primary, verified] |
| 4.1's FPR set had "a selection of non-textual features" removed before scoring. | 4.1 card | | [primary, verified] |
| Huang, Pruthi and Dhingra, "Multimodal AI Detection for Math-Heavy Scientific Text", arXiv 2610.21062, submitted 2026-10-15. Pre-2022 arXiv proof and prose passages were regenerated by LLMs (large language models) given "the entire source of the paper except the target passage". Pangram 4 with its own labels (AI or Mixed counted as detected) caught 36.3% of frontier AI proofs and 79.7% of prose on LaTeX source, and 32.4% and 69.4% on PDF-extracted text. "Pangram 4 depends much more on length" (Appendix C) and degrades as math fraction rises. It "even classifies 11 human-written passage[s] as AI-assisted". Minor version not stated; 4.0 by date. | https://arxiv.org/html/2610.21062 (Table 2, Table 8, Fig. 2, App. C) | 2026-10-15 | [primary, verified] for text and the Table 8 cells; Figure 2 and 5 values not read |
| Same paper, Table 12: newer generators (n=100 pairs each), Pangram 4 own labels, share labelled AI in brackets. Claude Opus 5.5 prose: 0.250 (0.120) on LaTeX, 0.219 (0.115) on text. GPT-6 astra prose: 0.230 (0.120) and 0.211 (0.116). Proofs 0.08 to 0.15. | same, Appendix F | 2026-10-15 | [primary, verified] |
| Epoch AI (Pangram 3.3.2, pre-4): on style-imitated AI text Pangram missed 25% of scientific passages against 4% of blog passages (99 each, about 500 words, headings trimmed). | https://epoch.ai/data-insights/ai-text-detection-challenges | 2026-07-15 | [primary, unverified] |

No source tests code blocks, tables or Markdown markers directly. The project's B38 measurement remains the only data on LaTeX in Henry's posts: the share was 0.41 with LaTeX and 0.24 without, and LaTeX inflated the word count 1.31 to 1.49 times.

My reading of the two results together, as inference: the Duke paper scores whole AI passages in which math is a large share, and Pangram is unsure there, so it under-flags. In Henry's posts the LaTeX sits inside AI-labelled prose runs. Sentence voting and CRF smoothing give it the neighbours' label, and because LaTeX source is character-heavy, character weighting then inflates fraction_ai. The returned `text` and segment offsets would test this in one scan.

## Q5. Pangram's own evaluations of edited text and humanizers; third-party evaluations of 4.x

**Pangram's own figures**

| Claim | Source | Date | Tag |
|---|---|---|---|
| 4.1 on mixed-authorship sets (Human, Mixed, AI): proofreading or polish, 11,363 documents: 99.45%, 0.54%, 0.0088%. Substantial AI edits, 14,990: 41.37%, 55.01%, 3.62%. WildChat-derived editing, 4,826: 27.85%, 65.17%, 6.98%. "Out of an abundance of caution, Pangram leans human when encountering mixed text." "We deliberately tune Pangram to be more inclined to produce false negatives rather than false positives." | https://www.pangram.com/blog/is-pangram-accurate | 2026-10-16 | [primary, unverified] (summarizer; the substantial-edit row matches the tech report Table 5 exactly) |
| Length table (4.1): FPR 0.02%, 0.009% and 0.004% and FNR 1.29%, 0.41% and 0.21% at 50 to 99, 100 to 249 and 250 to 499 words. Nothing above 499 words. "We always suggest scanning the longest span of a document that is available." | same | 2026-10-16 | [primary, unverified] |
| AI-assisted labels come from Haiku 4.5 clause splitting plus "soft n-grams". A lexical match is Human, a semantic-only match AI-Assisted, no match AI-Generated. The labeller is invariant to deletions and to reordering of clauses. The schema separates "the provenance of the surface style" from "the provenance of its underlying ideas", citing StoryScope (Russell et al., arXiv 2604.03136). | Tech report Sec. 3.2, 3.5 | 2026-07-29 | [primary, verified] |
| Humanizers: "identifies AI involvement in humanized AI text 98.83% of the time" across 13 commercial humanizers (Pangram 4 technical blog). The humanizer head's per-system true positive rate is 91.52% to 99.39% (tech report Sec. 5.9, Table 14). The prior-work note's "97.7% recall on 12 humanizers" does not match these figures; I did not resolve the difference. | https://www.pangram.com/blog/pangram-4-technical; tech report | 2026-07-29 | [primary, verified] for the tech report; blog [primary, unverified] |
| Pangram's call for new evaluations offers credit grants "with no publishing terms". Open questions it lists: "high-context settings, like deep research, in an agent harness, or over multiple iterations of AI editing"; mixed authorship; and "technical writing, math equations, or code". | https://www.pangram.com/blog/a-call-for-new-pangram-evaluations | 2026-11-06 | [primary, verified] |

**Third-party evaluations of 4.x since 2026-09**

- **Huang, Pruthi and Dhingra (above)** is the only independent paper on 4.x I found that bears on technical text. Funded by a $5,000 Pangram research credit award [primary, verified].
- **StealthGPT-Labs/humanizer-benchmark** (Q6) records the resolved Pangram version per run: 4.0 on 2026-09-30, 4.1 on 2026-10-22. Vendor-run [primary, verified data file].
- **HumanizerEval**, "Pangram (Oct 2026): 11 tools tested", has the same numbers as StealthGPT's 2026-10-22 report, and its data link points to the StealthGPT-Labs repository. Not independent. https://www.humanizereval.com/detectors/pangram/ [secondary].
- **Karr et al., "Why AI Detection Fails for Academic Integrity"**, arXiv 2608.11256 v3 (2026-10-13), abstract: commercial detectors are unnamed in the abstract and no Pangram version is given, so it is not usable for 4.x [primary, unverified].
- **Wired (2026-09-02), Bloomberg (2026-10-30), Bender "Pangram is not an oracle" (2026-10-19)**: commentary without new measurements [secondary].
- **Literary false-positive disputes on long human texts** (Goncourt selection, Orelien, 2026-09-25; Caine Prize story): allegations from Pangram scans, contested by the authors, with no published scan data I could check [secondary].
- **Not found:** any independent 4.x evaluation on documents over 1,000 words, on blog posts, or on edited technical writing.

## Q6. Public reports of AI-drafted text passing Pangram 4.x with content kept

**Claims with data**

1. **StealthGPT Super, Pangram 4.1** (vendor, conflict of interest).
   - Source: https://github.com/StealthGPT-Labs/humanizer-benchmark, report `2026-10-22-humanizer-comparison`, resolved Pangram version "4.1" [primary, verified; I recomputed from `scores.csv`].
   - Inputs: 50 synthetic essays from GPT-6.1 Sol, Claude Sonnet 5.5, Gemini 4 Argon, Grok 4.7 and DeepSeek V4.1 Flash (10 each), 364 to 997 words (median 669), generic genres such as argumentative essays.
   - Pangram AI share: 41 of 50 outputs under 10%, 44 under 50%. The unhumanized sources were 0 of 50 (median AI share 100).
   - With zero fact errors, by StealthGPT's own checker: 26 of 50 under 10%.
   - Scores are bimodal: failures are mostly 100. The top and bottom halves by length pass at about the same rate, 22 of 25 against 19 of 25, so length does not hurt.
   - The same humanizer on 4.0 (2026-09-30, 50 essays of 300 to 995 words): 42 of 50 under 10%, 29 with zero fact errors.
   - Caveats:
     - The outputs and raw API responses are withheld "to prevent adversarial reuse", and the quality logic is undisclosed.
     - Detectors received text with Markdown heading, bullet and bold markers stripped.
     - The "strict bypass" rule for Pangram is "Human score above 50 percent", which counts Mixed outputs; my under-10% count is closer to Pangram's Human label.
     - We cannot tell whether content was kept or how the bypass works. It outputs about 1.0 to 1.2 times the input length.
     - The press release (PR Newswire, 2026-09-30, about 89 of 100 human on "v4") makes the same claim [primary, unverified].
2. **Huang, Pruthi and Dhingra (Q4).** About 75 to 78% of Opus 5.5 and GPT-6 prose passages (100 each) were not flagged by Pangram 4 when generated with the whole paper as context. This is new AI text written to fill a gap from a large human context, not a rewrite that keeps a draft's content. It fits Pangram's scope rule that AI output must have "more output tokens than input tokens" (tech report Sec. 3.1) [primary, verified].
3. **Gautham Srinivas, "How to use AI to not sound like AI"** (Substack, 2026-10-09, Pangram API, version not stated, 4.0 by date).
   - Prompting and five Claude Code agent loops: 100% AI. Mistral-7B base: 9 of 10 at 100%, one at 85.5%.
   - The only 0% came from an agent splicing in a pre-2022 human article: "0% AI and 37% plagiarism".
   - No lengths or content checks.
   - https://gauthamsk.substack.com/p/how-to-use-ai-to-not-sound-like-ai [primary, unverified]
4. **rawmodels/Qwen3.8-27B-antislop-pangram-joint-grpo** (Hugging Face, 2026-10-02). A model RL-trained (GRPO, group relative policy optimization) against the Pangram v3 API logit still scores mean AI likelihood 0.915 on "Pangram web detector" (24 questions by 8 generations). That is evidence that training against v3 does not transfer to the current web detector. https://huggingface.co/rawmodels/Qwen3.8-27B-antislop-pangram-joint-grpo-GGUF [primary, verified card; numbers are the author's].

**Claims without data**

- "Can my fine-tuned model pass Pangram?" (Ask HN (Hacker News), 2026-11-01, meyerdav): a small model fine-tuned 15 minutes on the poster's own writing sometimes reads 100% human. Video only. https://news.ycombinator.com/item?id=50324089 [primary, verified post; no data].
- Phrasly, Rephrasy, ultrahumanizer and similar "bypass Pangram" pages: marketing, no per-sample data [secondary].

Already known to the project and not repeated: HALO, PASTA, Xu et al., work-humanizer, Emulate-1, jialinyyzz/humanizer.

## Q7. Drift and silent updates

| Claim | Source | Date | Tag |
|---|---|---|---|
| "The minor version served within that series can change without changing the selector; for example, a request using `pangram-4` can return version `4.0` or `4.1`. Read the completed response's `version` field." No way to pin a minor version is documented. | https://docs.pangram.com/api-reference/models.md; ai-detection.md | docs 2026-11-02 | [primary, verified] |
| `default` "follows Pangram's current default model without pinning your integration to a numbered generation". | models.md | | [primary, verified] |
| Calibration parameters "may vary between model releases"; L_min is "configurable"; the humanizer threshold is 0.91 "by default at release". These are settings that can move. Nothing says whether they can change within a version string. | Tech report Sec. 4.3.3; 4.0 card | 2026-07-29 | [primary, verified] |
| No changelog: /changelog, /release-notes and /updates return 404. Model cards and blog posts are the only release record. The blog's "Product Updates" category exists. | HTTP checks today | 2026-11-06 | [primary, verified] |
| Model cards promise regression testing ("test and monitor future model releases for regressions") but no update policy. | 4.0 and 4.1 cards | | [primary, verified] |
| A 2026-07 Substack post reported the same text scoring 91% to 55% Human across entry points (website, Word upload, Google Docs). That was before 4.1 and not checked. | https://charliefinch10.substack.com/p/fooling-pangram-how-one-word-made | about 2026-07 | [secondary] |
| A StealthGPT blog post on fall 2026 detector changes finds no Pangram silent update; it notes the 3.3.2 to 4 default switch was never confirmed on a Pangram page. | https://www.stealthgpt.ai/blog/fall-2026-ai-detector-model-changes-why-before-and-after-scores-no-longer-compare | 2026-10 | [secondary] |
| StealthGPT's benchmark logs show the resolved Pangram version moving from 4.0 (09-30) to 4.1 (10-22). It is the only public longitudinal record with versions, but each run used new source texts, so it cannot measure same-text drift. | StealthGPT-Labs repo, summary.json | | [primary, verified] |

No public measurement of same-text, same-version score changes exists that I could find.

## What I could not verify

- The backbone tokenizer, so the window size in words. The value of L_min in 4.1 and whether 4.1 changed it.
- Whether a single newline (not a blank line) ends a "sentence"; how code fences, tables and inline LaTeX are tokenized or normalized; what `text` normalization does.
- What `default` resolves to today, and whether the dashboard and API serve the same version at the same moment.
- Whether Henry's Professional plan's $200 API credit applies to his existing key or must be activated in the API dashboard. Only a call (with Henry's yes) settles it. Rate-limit values.
- Whether the bulk API returns `class_probabilities`.
- How `class_probabilities` are aggregated per segment, and whether bulk and single-task results are identical for the same text.
- The Pangram minor version in Huang et al.; their Figure 2 and 5 values for math fraction and length.
- StealthGPT's outputs, mechanism and fact checker. HumanizerEval's ownership.
- The "Is Pangram accurate?" and MCP pages were read through a summarizer, not raw.
- X posts by Pangram staff: web search found none about 4.2 or updates; X itself was not read.
- Any 4.x accuracy figure on texts over 499 words, on blog posts or on technical writing.

## Implications for attempt 2's design

1. **Scan the whole post once and read the segments; do not scan sections separately.**
   - The segments carry character offsets, so per-section shares can be computed by mapping `start_index` and `end_index` onto the post's section offsets. The cost is the same as one whole-post scan (25 credits for 2,500 words).
   - It avoids the context effect Pangram itself warns about, and the per-scan rounding up to the next 100 words.
   - Section-alone scans should be a diagnostic only. If they are used, pre-register a check that compares section-alone shares with in-context shares on a few posts.
2. **Per-segment output is a finer, cheaper measure than a label count, with limits.**
   - It gives sentence-resolved labels, `class_probabilities` (a continuous signal even where the label is Human), and `humanizer_score`.
   - Its resolution floor is about 2 sentences, and labels are smoothed across about 390-word windows. Do not read single sentences.
   - Use the per-section AI-character share, and the mean P(AI-Generated) + P(AI-Assisted) per section, as the development measure.
   - The judge rule still applies: per-segment Pangram data is a held-out measurement. Using it to choose rewrites would make Pangram the selector. Henry should decide that explicitly before the API is wired in.
3. **Size edits to the decoder.**
   - Any change shorter than about 2 sentences can be absorbed by the minimum-run merge. A one-sentence human fix inside an AI run will usually inherit the AI label.
   - Rewrite units should be paragraphs or runs of 3 or more sentences.
   - The Human budget is under 10% of characters labelled AI-Generated or AI-Assisted, so on a 2,500-word post at most about one paragraph may remain flagged.
   - A cheap B37-style test would splice 1, 2 and 3 AI sentences into human posts and read the segments.
4. **Fix the scoring representation for technical posts before any comparison, and log it.**
   - Pangram calls Markdown, code and math-dominated text out of scope and splits sentences at blank lines.
   - Proposed canonical form: the reader-visible prose with Markdown markers stripped (as the StealthGPT benchmark does), code blocks removed, and display math removed or replaced with a short placeholder. Score that.
   - In one diagnostic batch, also score the same posts with code and LaTeX kept, and read the returned `text` and segment offsets. That shows whether LaTeX takes its neighbours' label and inflates the character share.
   - Report character-based and word-based shares side by side, since they diverge for LaTeX.
5. **Build a drift canary, because Pangram says it may change the minor version silently.**
   - Freeze 10 to 12 canary texts: 4 known-human posts, 4 raw AI drafts, and 4 B37 splices at about 7%, 10% and 17% AI.
   - Scan them at the start of every scan session and record `version` (API) and the exact fractions and segment offsets.
   - The tech report claims deterministic decoding, so any change on unchanged text means the model or its settings moved. Pause comparisons across that boundary.
   - Cost is about 150 to 250 credits per session. Keep same-day paired scans for key contrasts, as in attempt 1.
6. **Settle API access once, with Henry's yes.**
   - One `GET /models` and one `POST /task` with `model: "pangram-4"` on a 100-word text (1 unit) shows whether the $200 credit is live, which version is served, and whether `class_probabilities` comes back.
   - If live: the bulk API (up to 1,000 units per request, 20% cheaper, results kept 48 hours) replaces the dashboard procedure and its browser fragility, and gives about 160 to 200 post scans a month on top of 15,000 dashboard credits.
   - Pangram's 2026-11-06 call offers research credit grants for exactly this topic (technical writing, math, code, multi-step AI editing) with no publishing terms. That is a possible source of extra budget, and it would disclose the project to Pangram. Henry's call.
7. **What the new evidence says about routes.**
   - **High-context generation reads human.** AI text written from a large human context passes: Opus 5.5 prose given the whole paper was flagged only about 22 to 25% of the time. This agrees with attempt 1's finding that Pangram reads who chose the content. The attempt-2 version is to give the writer a large Henry-authored context per post (his notes, earlier posts, the code the post explains) rather than the AI draft. That needs Henry's material at drafting time, and B22's restriction on some records still applies.
   - **Do not build on StealthGPT-style passes.** The mechanism is unknown, the data is the vendor's own, half the passes had fact errors by the vendor's own check, and Pangram is explicitly asking for evaluations in this area. Treat technical writing, math and code as a gap Pangram is likely to close, not a lever.
