# B31 claims ledger

Every claim B31 started from, and every claim it relies on, with its source, how it was checked and its status. Henry's
rule: treat every prior finding as a claim to test. Status is **verified**, **refuted**, **partly true** or
**unverified**. "Me" means the B31 head session read the primary source or raw file itself; "agent" means a research
agent did (raw reports: `b31-base-detectability.md`, `b31-web-pollution.md`, `b31-open-data-mixes.md`,
`b31-qwen-phi-nemotron-mistral.md`). Claims 1 to 3 are updated with B31's own data at the end.

Opened 2026-11-05 23:35 CST; last updated: see git log.

## Claims from the brief

### 1. B1: three OLMo-2-13B base continuations read Human, one Qwen3.5-9B-Base continuation read AI

- **Source:** `results/b1_pangram_free.json`, `results/b1_generations.jsonl`, `REPORT-2026-11-05.md` section 2.1.
- **Checked (me, raw files and git history):**
  - Both models ran 4-bit MLX (`mlx_lm convert -q --q-bits 4`), same code path (`local_generate`), temperature 0.8,
    top-p 0.95, repetition penalty 1.05 over the last 20 tokens (the `mlx_lm` default window), seed 0, 650 new tokens,
    the same 30 dev openings (first 120 words). So quantization and decoding were the same for both: not a confound
    between them, though both differ from full precision.
  - **The scanned texts came from different documents.** The Qwen text is h0600; the OLMo texts are h0601 to h0603.
    The comparison is across documents, not paired.
  - **Different selection rules.** Qwen: the first continuation, unselected. OLMo: the first three whose continuation
    reached 380 words (a length screen that could favour fluent continuations).
  - **A missing verdict, resolved.** At the scan commit (3329bee, 2026-11-04 01:32) `results/b1_free_probe_texts.json`
    holds two Qwen texts, h0600 and h0601, but only h0600's verdict is recorded, and the credit ledger counts 5 texts
    against 4 verdicts. Pangram's own history for 2026-11-04 (read in the dashboard, 2026-11-05 23:58) shows the
    Qwen h0600 text at 01:30 (AI), the three OLMo texts at 07:11 and 07:12 (Human), and a fifth, unrelated text at
    17:05 (AI). The Qwen h0601 continuation was prepared but never scanned. Nothing was hidden.
  - The Qwen h0600 text in the file today is byte-identical to the one at the scan commit.
- **Status:** the four recorded verdicts are **verified as recorded**; the inference "Qwen3.5 base reads AI" rests on
  **one sample** and is **unverified** pending B31 (arms `qwen3.5-9b`, `qwen3.5-9b-q4`).

### 2. The main session's reading: newer base models read AI because recent web crawls contain AI text (H1)

- **Source:** `REPORT-2026-11-05.md` short version, item 1 ("Modern base models have absorbed enough AI text from the
  web to carry the signature").
- **Checked:** no data behind it at the time; one Qwen sample against three OLMo samples on different documents (claim 1).
- **Status:** **untested hypothesis**, B31's H1. See the result section below.

### 3. The rival reading: labs add synthetic or instruction-like data on purpose, and that carries the signature (H2); "Qwen's reports describe such data"

- **Checked (agent, Qwen reports; me, Qwen3 report via the agent's quotes only):**
  - Qwen-7B report (2309.16609, section 2.1): "we have incorporated high-quality instruction data into our
    pretraining process". Qwen2 report section 3.1: "high-quality multi-task instruction data is integrated into the
    Qwen2 pre-training process" and Qwen models "utilized to synthesize high-quality pre-training data".
  - Qwen2.5 (section 3.1): synthetic math, code and knowledge data from Qwen2-72B-Instruct and Qwen2-Math-72B-Instruct;
    no instruction-data sentence.
  - Qwen3 (2505.09388, section 3.1): Qwen2.5, Qwen2.5-Math and Qwen2.5-Coder "synthesize trillions of text tokens" in
    formats "including textbooks, question-answering, instructions"; stage 2 raises the synthetic share.
  - Qwen3.5: no data report exists. The base model card says the chat tokens `<|im_start|>` and `<|im_end|>` "were
    trained", which implies chat-format text in base training (an inference).
  - Independent: Liu et al. (2503.20783) find Qwen2.5 bases answer questions with no template and suspect
    question-answer text in pretraining; HALO (Table 6 note) suspects Qwen3's score comes from "synthetic post-training
    data included in its pretraining mixture". Both are hypotheses.
- **Status:** the recollection is **verified, and understated**: Qwen documents instruction data in pretraining since
  2023 and trillions of synthetic QA and instruction tokens for Qwen3. That Qwen bases *read AI because of it* is
  **unverified** (Qwen has no checkpoint without it); B31 tests the mechanism in Olmo 3, where it does.

### 4. HALO: OLMo-2 beat Qwen3 and Gemma-3 as the base model for evading Pangram 4

- **Source:** `r1-papers-benchmarks.md`, `r2-primary-sources.md`.
- **Checked (me, HALO arXiv HTML Table 6; agent, Tables 1, 5, 6, 11):**
  - Table 6 (raw continuations, n=30, Pangram 4, mean fraction_AI): Llama-3-8B 0.282, Qwen3-8B-Base 0.417,
    OLMo-2-1124-7B 0.267, OLMo-2-7B at top-p 1.0 0.380, Gemma-3-12B 0.167, Gemma-3-27B 0.085, OLMo-2-0325-32B 0.033.
    Temperature 1.05, top-p 0.95, 4 samples per prompt, first with 50 or more words scored, about 250 words.
  - **The prompts were written by the HALO agent (Claude Opus 5)**, mixed genres (Mythos, HealthBench, IFEval, FACTS).
    So these are continuations of AI-written prefixes, not of human text.
  - At 7 to 8B the Qwen3 and OLMo-2 counts (11 vs 8 of 30 labelled AI) do not differ (Fisher p about 0.58, agent's
    computation). Changing top-p alone moves OLMo-2-7B from 0.267 to 0.380, more than the Qwen gap.
  - Table 5 (full HALO, p=0.9): OLMo-2 is better on Mythos (0.044 at 32B), but on HealthBench Gemma-3-27B (0.649) ties
    OLMo-2-32B (0.635), and Qwen3-8B (0.820) beats OLMo-2-7B (0.898).
  - Section 4.4's mid-training explanation ("We suspect this contributes") is a hypothesis.
  - The size effect is large: within OLMo-2, 7B 0.267 against 32B 0.033.
- **Status:** **partly true, overstated.** OLMo-2 beats the others on fiction and at 32B; at matched 7 to 8B size the
  Qwen3 gap is within noise, and model size and decoding move the score as much as family. B31 compares at 7 to 9B.

### 5. Xu et al. and PASTA: base models look human to Pangram (Llama-3-8B base 98.8% human); the signature comes from post-training

- **Checked (agent, both papers' HTML; figure values read from SVG geometry):**
  - Xu et al. (2605.19516): Llama-3-8B base 98.8% mean human probability on human prefixes, instruct 17.1% (stated in
    the text; the exact checkpoint is never given). Figure 1 also shows **Qwen3-Base at 0.875 against Llama-3-Base at
    0.988** on human prefixes (z about 5): Qwen3's base is measurably less human than Llama's.
  - PASTA (2605.30526, v3 retitled): "Pangram flags 98.5% of aligned outputs versus 9.2% of base outputs", pooled over
    8 pairs after a degeneracy filter and a judge re-ranking of base outputs; Figure 3 shows 96.1 and 9.0. Base models
    are Qwen2.5 (several sizes), Llama-3.1-8B, Gemma-2-9B, Mistral-7B-v0.3 and **Olmo-3-7B**; no Qwen3 or OLMo-2. From
    Figure 6, Olmo-3-7B base scores at most about 0.14 and Qwen2.5-7B base at most about 0.30.
  - Neither paper tests pretraining data; neither gives a Pangram version or query date.
- **Status:** **partly true.** Base models read far more human than their chat versions, but not equally: Qwen bases
  sit measurably closer to AI than Llama or Olmo 3 bases. "The signature comes from post-training" is the papers'
  interpretation, untested against pretraining data.

### 6. Olmo 3 32B base: released November 2025, 65,536-token context, Dolma 3, a synthetic-heavy mid-training stage, earlier-stage checkpoints published

- **Checked (me: Hugging Face API, revision hashes, model card, Olmo 3 report arXiv 2512.13961v2 sections 3 and Table 7;
  agent: Tables 4, 5, 11):**
  - `allenai/Olmo-3-1125-32B` repo created 2025-11-04; the 7B (`Olmo-3-1025-7B`) repo 2025-09-12; the report is on arXiv
    2025-12-15 (agent). "November 2025" for 32B is **verified** as the release window.
  - 65,536-token context: **verified** (agent, report).
  - Stage checkpoints: **verified** (me). 7B: `stage1-step1413814` (end of pretraining, 5.93T tokens),
    `stage2-step47684` (end of mid-training, 100B), `stage3-step11921` (end of long context, 50B). `main` has the same
    weight files as `stage3-step11921` (identical LFS hashes). 32B: `stage1-step656000`,
    `stage2-ingredient1+2-step23842`, `stage3-step11921+11000+10000-nooptim`.
  - **Not claimed before, found here:** three mid-training ablation checkpoints from a 2T-token stage-1 checkpoint
    (`stage1-step476838`, exactly 2.000T tokens at 4,194,304 tokens per step): Gen-QA mix (web, QA and instruction
    data, no math, code or thinking), Math-code-thinking mix (web, math, code and thinking traces, no QA or
    instruction data), Round 5 (the final mix). Model card and report Table 7 (me).
  - Pretraining crawl: 104 dumps, CC-MAIN-2013-20 to CC-MAIN-2024-51 (me, report text). The pretraining mix (Table 4)
    lists no LLM-generated source (me, report), though 13.6% is PDF text transcribed by olmOCR, a vision-language
    model (agent).
  - Mid-training (Dolmino, 100B): 20% code, 28% web, 19% math, 14% QA, 8% thinking, 6% instruction, 5% PDFs (me,
    model card); about half the tokens LLM-generated by the agent's sum of Table 5 rows; the mid-training web crawl
    runs to June 2025 (agent). "Synthetic-heavy" is **verified**.
  - The Dolma 3 web quality classifier's positives are OpenHermes-2.5, ELI5, UltraChat-200k and WildChat-1M (agent;
    my fetch of the report confirms UltraChat and OpenHermes in the sentence). Chat-model outputs are the positive
    class, so the filter selects web text that resembles assistant output.
- **Status:** **verified** in every part, with a correction: there is no Olmo 3.1 base model (agent, Hugging Face).

### 7. AI text has grown to a large share of new web pages since 2023

- **Checked (agent, primary sources; me, Russell et al. abstract):**
  - New article-type pages: about 35 to 50% mostly AI by 2025 (Graphite 2026 with three detectors; Dolezal et al.
    2604.26965 with Pangram v3).
  - Whole crawls: about 10% of English pages by July 2026 (Pew, open Pangram); 23.6% of all pages and 32.8% of
    English pages in August 2026 including AI-edited text (Visokay et al. 2610.36631), with growth near zero before
    2023, 4.6 points a year 2023 to 2025, 8.1 after.
  - After FineWeb filtering: 27.5% of tokens in June 2026 (Russell et al. 2609.40295; I read this in the abstract).
    The agent reports 10.1% (June 2024) and 16.1% (June 2025) from the body, and that AI documents pass DCLM's filter
    9.8 times as often as human ones; I have not seen those numbers myself.
  - Pew's page: the URL the agent gave returned 404 to me; **unverified by me**.
  - Every large estimate uses Pangram or its open model, the same detector family as B31's judge; Binoculars flags only
    8 to 13% of what Pangram flags on recent pages (Visokay).
- **Status:** **partly true.** True for new article pages; for what a base model trains on, the AI share of a whole
  crawl was about 2% in 2023 and about 5 to 9% in 2024 to 2025 by the agent's synthesis, higher after
  classifier filtering. A model whose pretraining crawl ends in December 2024 (Olmo 3) saw mostly pre-2023 dumps, so
  its exposure is small unless filtering concentrated it. This sets the scale of B31's H1 test.

## Claims B31 relies on (training-data facts per model)

| Model | Fact used in the design | Source | Checked by | Status |
|---|---|---|---|---|
| Pythia | the Pile, sources to about September 2020, no LLM text, no instruction data | Pile paper App. C | agent | verified |
| OLMo-2-1124 stage 1 | DCLM-Baseline, Common Crawl through 2022, no LLM text or instruction data | OLMo 2 report, DCLM paper ("all Common Crawl data prior to 2023") | agent | verified |
| OLMo-2-1124 stage 2 | Dolmino: FLAN 11 to 17%, synthetic math 11 to 21% (TinyGSM-MIND by Qwen2.5-7B-Instruct, others) | OLMo 2 Tables 5 and 13 | agent | verified |
| OLMo 1 0724 | Dolma 1.7, Common Crawl to CC-MAIN-2023-06 (week 6, February 2023), FLAN about 1%, anneal with FLAN | Dolma paper, 0724 card | agent | verified (anneal FLAN share unverified) |
| Olmo 3 7B | see claim 6 | report, card, Hugging Face | me and agent | verified |
| Phi-2 | 250B tokens of GPT-3.5 synthetic data plus filtered RefinedWeb and SlimPajama, 1.4T trained | card, blog | agent | verified; synthetic share and crawl dates unverified |
| Nemotron-Nano-9B-v2-Base | CC-MAIN-2013-20 to CC-MAIN-2025-13; 3.53T of 10.6T tokens synthetic; "question-answering, and alignment style data" | model card | me | verified |
| Mistral-Small-24B-Base-2501 | "Mistral Small 3 is neither trained with RL nor synthetic data" (2025-01-30) | Mistral blog | me | verified as stated; whether it covers pretraining is unverified |
| Mistral 7B v0.1, Nemo base | no data documentation | papers, cards | agent | verified (absence) |
| Qwen series | see claim 3 | Qwen reports | agent | verified |
| Gating | Llama 3.x and Gemma 3 are gated ("manual"); Mistral, Qwen, OLMo, Pythia, Phi, Nemotron are not | Hugging Face API | me | verified; B31 uses no gated model |

## New findings from the literature check

- **Base models imitate the register of their prompt.** HALO's plain base LM scores 0.113 on human stories, 0.602 on
  the agent's AI responses and 0.852 on HealthBench references (some of which were edited AI answers). Any base-model
  comparison must hold the prompt fixed and human-written; B31 does.
- **Quality filters trained on chat output select AI-like web text.** DCLM's classifier (used by OLMo 2) took
  OpenHermes-2.5 as positives; Dolma 3's (Olmo 3) took OpenHermes-2.5, UltraChat and WildChat. Russell et al. (agent)
  measure AI documents passing DCLM's filter 9.8 times as often as human ones. For OLMo 2 this did not matter (its pool
  is pre-2023); for crawls after 2023 it multiplies whatever AI text the crawl holds. In B31, H1 for Olmo 3 therefore
  means "later crawl plus a chat-trained filter", not crawl date alone.
- **Self-identification grows with data cutoff** (Zhong, LessWrong, July 2026, agent): Olmo-3-32B base calls itself
  GPT 25.6% of the time. Blog post, numbers mostly in charts; unverified by me.
- No paper found compares a detector's scores across base-model release dates or training stages. B31 would be the
  first such measurement we know of.

## Results from B31's own data

To be filled after the scan.
