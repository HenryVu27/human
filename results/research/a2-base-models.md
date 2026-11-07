# Research agent report: attempt 2 base models, long-context rewriter recipe, copy penalties, pair data, costs (2026-11-06)

Written by a research subagent for the attempt 2 planning session. Read only: no Modal runs, no PC jobs, no accounts,
no money, no .env. Arithmetic is in a scratch script (`calc.py` in the agent's scratchpad, not in the repo); its
output is pasted where used.

## Brief given to the agent (summary)

Goal behind the task: attempt 2 rewrites Henry's Claude-drafted technical posts (1,500 to 3,000+ words, 2,000 to 5,000
tokens, sometimes LaTeX and code) into prose that Pangram 4.x and careful readers judge human, adding no facts.
Attempt 1's best tool (OLMo-2-1124-13B base, 4,096-token context, NF4 (4-bit NormalFloat) QLoRA (quantized low-rank
adaptation), about 630 pairs from 13 essayists) worked on short posts by seen writers and failed on whole posts by
unseen writers (1 of 32 Human). Copying 8-word runs from the AI draft tracks the AI share (Spearman 0.70). Gate 2b
(long-context rewriter, many writers, copy penalty) was estimated at $40 to $55 of paid Modal. Questions: (1) open base
models, 7B to 32B, 8K to 32K+ context; (2) training recipes on the 16 GB RTX 5080 versus Modal GPUs; (3) copy
penalties that keep meaning; (4) cheap many-writer pairs; (5) a cost table. Rules: work at expert depth, start from raw
data, verify with an external check, report what you could not verify.

Tags: **[primary, verified]** = I read the primary source (Hugging Face (HF) API JSON, `config.json`, model card raw
markdown, arXiv API abstract, source code on GitHub, Modal pricing page, project files). HTML papers and blogs were
read through a fetch tool that extracts quoted numbers; those are tagged verified when the tool quoted the text, and
listed under "What I could not verify" where it could not. **[primary, unverified]** = primary source exists but I
could not read the relevant part or the table was ambiguous. **[secondary]** = third-party. **[estimate]** = my
arithmetic or judgment, with its basis.

Relation to earlier reports: `longform-base-models.md` (same day) already covers Olmo 3, Gemma 3 27B, Gemma 4 31B,
Llama 3.1, Mistral Small 2501 and 3.1, Ministral 3 14B, Qwen3.5 9B, Apertus v1.5 8B, contamination tools and vLLM
logits processors. `b31-*.md` covers training-data composition of open-data models. This report adds what those
missed and does not repeat their tables.

## Bottom line

1. **New base models since the last report that matter:** `google/gemma-4-12B` (pretrained, 11.96B, Apache-2.0,
   ungated, 256K context, cutoff January 2025, created 2026-05-23), IBM `granite-4.1-8b-base` and `granite-4.1-30b-base`
   (dense, Apache-2.0, released 2026-04-29, base RULER published), and the 2025 pair `Seed-OSS-36B-Base` versus
   `Seed-OSS-36B-Base-woSyn` (the same model trained with and without synthetic instruction data: a clean causal test
   of B31's H2). No new Olmo, Llama, Mistral Small or Qwen base checkpoints appeared from 2026-08 to now: Qwen3.6 and
   Qwen3.8 ship only post-trained 27B models; Granite 4.2 (2026-08-07) is post-trained from Granite 4.1 base. All
   [primary, verified].
2. **The 16 GB PC can train a 12 to 14B rewriter at 8K tokens, but only with CPU-offloaded gradient checkpoints**
   (Unsloth-style). With the project's current Hugging Face (HF) stack, the measured OLMo-2-13B peak rises 0.92 GB per
   1,024 tokens (10.96 GB at 2,560, 11.91 GB at 3,584; `results/gpu13b/*/summary.json`), which extrapolates to about
   16 GB at 8K: over the limit. 7 to 8B models fit at 16K. [primary, verified for the anchor; estimate for the rest]
3. **The binding constraint on the PC is generation, not training.** The current 4-bit HF generation path runs at
   7.5 tokens a second (closeout section 6.4). 400 posts x 4 tries would take about 250 hours. vLLM under WSL2
   (Windows Subsystem for Linux 2) or llama.cpp should be roughly 30x faster [estimate]. Fixing this is the cheapest
   lever in attempt 2.
4. **Copy penalties: the literature says use them, but measure faithfulness at matched copy rates.** Summarization
   work (Ladhak et al., ACL 2022) shows most "faithfulness" gains are just more copying, and a learned selector over
   candidates beats single-shot methods at the same abstractiveness. Hard n-gram bans are evaded by near-copies
   (Ippolito et al., 2022); B36 already shows a version of this (" ," artifacts). Soft penalties (DRY-style decoding,
   sequence-level unlikelihood on sampled spans, DPO or ORPO with high-copy rejects) are the better fit. Technical
   tokens (code, LaTeX, names, numbers) must be exempt, because copying them is what faithfulness requires.
5. **Many-writer pairs are cheap.** The back-translation pattern (an LLM writes the AI side from a human document's
   title, notes or excerpt) is exactly how Pangram builds its training negatives ("synthetic mirrors", 360,000 initial
   examples). TinyStyler shows that generalizing to unseen authors came from training over millions of authors plus a
   filtered self-distillation round (about 40,000 pairs). Attempt 1 had 13 writers; the B32 FineWeb pipeline can give
   600+ sites.
6. **Cost:** a 14B rewriter on 3,000 pairs of 6K tokens (18M tokens, 1 epoch) costs about $8.50 on a Modal H100
   (range $6.70 to $12.20) or about 5.6 hours on the PC. 400 posts x 4 tries at 3,000 words is about $4.90 on an H100.
   The full recommended recipe is about $10 to $15 of Modal with PC training, or about $44 all on Modal: inside
   gate 2b's $40 to $55, and the PC route fits this month's remaining $9 plus December's fresh $30 credit without
   paid spend. All throughput figures for Modal GPUs are estimates that a 10-minute calibration run should replace.

## 1. Open base models (7B to 36B, 8K+ native context)

### 1.1 What I checked and how

HF API listing by author, sorted by creation date, for allenai, Qwen, google, mistralai, meta-llama, swiss-ai, nvidia,
ibm-granite, microsoft, HuggingFaceTB, marin-community, LLM360, deepseek-ai, zai-org, CohereLabs, ByteDance-Seed,
baidu, LiquidAI, inclusionAI and others; then `api/models/<id>` and `config.json` for each candidate. [primary,
verified, 2026-11-06]

### 1.2 New or previously missed candidates

| Repo ID | Created | Params | Native context (config) | Licence, gating | Data cutoff | Pre- and mid-training synthetic or instruction data | Long-context evidence (base) |
|---|---|---|---|---|---|---|---|
| `google/gemma-4-12B` | 2026-05-23 | 11.96B; 48 layers (40 sliding at 1,024, 8 global); vocab 262,144, tied | 262,144; proportional RoPE (rotary position embedding) on global layers | Apache-2.0, ungated | January 2025 (card and report) | Not stated; the report mentions only filtering. "Unified" encoder-free design: image patches and audio project straight into the decoder (`Gemma4UnifiedForConditionalGeneration`) | None for the base. Instruct MRCR v2 8-needle 128K: 43.4% |
| `ibm-granite/granite-4.1-8b-base` | 2026-04-06 (release 2026-04-29) | 8.38B; 40 layers; vocab 100,352, tied | 131,072 in config; card says extended to 512K | Apache-2.0, ungated | Not stated | Phase 2 (2T tokens): synthetic about 9%. Phase 3 (2T): synthetic 8.5%, long chain-of-thought 12.5%, language instructions 7.5%, code instructions 4.5%. Phase 4 (0.5T): instructions 14%, long chain-of-thought 6%. Pretraining at 4K, then 32K, 128K, 512K stages | RULER 83.6 / 79.1 / 73.0 at 32K / 64K / 128K |
| `ibm-granite/granite-4.1-30b-base` | 2026-04-06 | 28.87B; 64 layers | 131,072 in config; card 512K | Apache-2.0, ungated | Not stated | Same recipe | RULER 85.2 / 84.6 / 76.7 |
| `ByteDance-Seed/Seed-OSS-36B-Base` and `-Base-woSyn` | 2025-08-20 | 36.15B; 64 layers; vocab 155,136 | 524,288, RoPE theta 1e7, "trained with up-to-512K long context natively" | Apache-2.0, ungated | Not stated | The two differ only in synthetic instruction data in pretraining: woSyn is "unaffected by synthetic instruction data" (card) | Card lists RULER 128K; the raw table's base columns are ambiguous [primary, unverified] |
| `mistralai/Ministral-3-8B-Base-2512` | 2025-10-31 | 8.92B | 262,144; YaRN x16 from 16,384 | Apache-2.0, ungated | Not stated | Logit distillation (forward KL) from the parent Mistral Small 3.1 at every stage; the paper reports an ablation where "the instruct teacher yields stronger performance on STEM" but does not say which teacher the release used | None for the base |
| `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Base-BF16` | 2026-08-05 | 31.6B total, 3B active; Mamba-2 plus MoE (mixture of experts) hybrid | 262,144 in config (card: up to 1M) | OpenMDW-1.1 | September 2025 | "crawled and synthetic code, math, science, and general knowledge data", pretrained in NVFP4 | Card reports RULER 256K and 1M |

All rows [primary, verified] from the HF API, configs and cards, plus: Granite phases and RULER from the
[Granite 4.1 blog](https://huggingface.co/blog/ibm-granite/granite-4-1) (2026-04-29); Gemma 4 cutoff and 12B design
from the [Gemma 4 report](https://arxiv.org/abs/2607.02770); Ministral distillation from
[arXiv 2601.08584](https://arxiv.org/abs/2601.08584).

Finding: **Granite 4.1's config says 131,072 positions while its card and blog say the final stage reached 512K.**
Either the 512K stage is not the released checkpoint or the config understates it. For attempt 2 (16K needed) it does
not matter. [primary, verified discrepancy]

Finding: **Ministral 3 base models are distilled from Mistral Small 3.1, possibly from its instruct version.** B31
found post-training is the large effect on detectability (+0.64 to +0.76 AI share). A base model that learned from an
instruct teacher's logits may carry that effect. This is a hypothesis, not tested. [primary, verified that
distillation is used; the teacher variant is unverified]

### 1.3 Checked and ruled out (2026-08 to 2026-11-06)

- **Olmo:** no base model after Olmo 3 (`Olmo-3-1025-7B`, `Olmo-3-1125-32B`). AllenAI's 2026-08-26 releases `Bwen-8B`
  and `Llama-3-Blama-8B` are byte-level conversions of Qwen3-8B-Base and Llama 3 8B (vocab 520), not new pretrains;
  Bolmo-7B is byte-level Olmo 3. [primary, verified]
- **Qwen:** `Qwen3.6-27B`, `Qwen3.6-35B-A3B` (2026-04), `Qwen3.8-27B` (2026-08-05) are post-trained only; the card says
  "Pre-training & Post-training". Qwen base checkpoints stop at Qwen3.5 (0.8B to 9B, 35B-A3B). [primary, verified]
- **Gemma 4:** base checkpoints are `gemma-4-12B`, `gemma-4-31B`, `gemma-4-26B-A4B` (MoE), E2B, E4B; the `-it` repos
  are separate. [primary, verified]
- **Mistral:** Mistral Small 4 is 119B (MoE), Mistral Medium 3.5 is 128B, Mistral Large 4 is 1T; no new base in range.
  [primary, verified]
- **Llama:** nothing after Llama 4 (2025-04, MoE). [primary, verified]
- **Granite 4.2** (2026-08-07, 3B, 8B, 30B): post-trained from Granite 4.1 base. [primary, verified]
- **Apertus v1.5 8B and 70B base** (2026-09-23): `gated: auto` now (the earlier report saw `gated: false` for the 2509
  release). [primary, verified]
- **MoE bases** (Ling 3.0 flash, LFM2.5-24B-A2B, ERNIE-5.5-Flash 286B, Nemotron 3 Super and Ultra): poor fit for QLoRA
  on one card and outside the 7B to 32B dense range.
- **Marin:** no new base since 8B and 32B (4,096 context); 2026 releases are scaling-study checkpoints. [primary, verified]

### 1.4 Synthetic and post-ChatGPT data, by shortlisted family

- **Olmo 3:** pretraining (Dolma 3 Mix, crawl to December 2024) has no LLM-generated source except 13.6% olmOCR PDF
  text; mid-training (Dolmino) is about 52.5% synthetic, including 8.3% thinking traces and 1.1% Tulu SFT
  (supervised fine-tuning) data; the long-context stage adds 16% synthetic. B31 measured the 7B before and after
  mid-training at 37% and 33% not Human: no effect. Only family with open, searchable data. [primary, verified in
  `b31-open-data-mixes.md`, `B31-SUMMARY.md`]
- **Gemma:** closed data, cutoff January 2025; Gemma 3 used distillation (Gemma 3 report); Gemma 4 does not say.
  B31: Gemma-3-12B had the lowest not-Human rate of the models tested (12%), and HALO's raw Gemma-3-27B continuations
  scored 0.085. Gemma 4 is untested. [primary, verified for Gemma 3 numbers in project files]
- **Granite 4.1:** about 20% instruction and long chain-of-thought data in phase 3 and 4 (2.5T of 15T tokens), plus
  synthetic data. Untested for detectability. [primary, verified]
- **Qwen3.5:** synthetic instruction data in pretraining (Qwen reports); B31: 34% not Human. [primary, verified in
  project files]
- **Seed-OSS:** the only matched with and without synthetic-instruction pair. [primary, verified]
- **Ministral 3:** logit-distilled; see the finding above.

B31's result (post-training is the large effect; crawl date and synthetic mid-training are not detectable at its
power) means pretraining-data differences should not drive the choice; what the B36 failure points to is capacity for
long documents and generalization across writers.

## 2. Training recipes for a document-level rewriter

### 2.1 Measured anchor on the PC [primary, verified, project files]

From `results/gpu13b/*/summary.json` (torch 2.11.0+cu128, transformers 5.22.1, peft 0.21.2, bitsandbytes 0.50.2,
RTX 5080): OLMo-2-13B, NF4 with double quantization, LoRA (low-rank adaptation) rank 16 on all linear layers, batch 1,
gradient accumulation 4, HF gradient checkpointing, SDPA attention, a chunked checkpointed loss (512-token chunks),
paged 8-bit AdamW.

- Peak allocated memory: 10.96 GB at 2,560 tokens (five runs), 11.91 GB at 3,584 (B30 rewritepool).
- B30 rewritepool: 630 rows, 7,009,318 characters (about 1.63M tokens at 4.3 characters per token), 158 steps x
  14.36 s = 38 minutes, so **about 720 training tokens a second** for a 13.7B QLoRA. [estimate from measured times]

### 2.2 Memory math for 16 GB [estimate]

Components: NF4 weights at 0.52 bytes per parameter for linear layers; embeddings and output head kept in bf16; LoRA
rank 16 with fp32 weights, gradients and 8-bit Adam (about 10 bytes per LoRA parameter); checkpointed layer
boundaries L x T x d x 2 bytes; one layer's recomputed activations T x (10d + 3I) x 2 bytes; chunked logits 1,024 x
vocab x 8 bytes. "Empirical" extrapolates the measured 0.92 GB per 1,024 tokens, scaled by layers x width. Add about
0.8 GB of CUDA context, plus whatever the Windows display and the umwelt project hold.

| Model | Weights | 8K | 8K, checkpoints offloaded | 8K empirical | 16K | 16K offloaded | 16K empirical |
|---|---|---|---|---|---|---|---|
| OLMo-2-13B (anchor) | 8.7 | 15.0 | 11.6 | 16.1 | 19.8 | 13.1 | 23.7 |
| Olmo-3-7B | 5.0 | 9.6 | 7.4 | 9.8 | 13.0 | 8.7 | 14.6 |
| Granite-4.1-8B-base | 5.0 | 10.3 | 7.6 | 11.0 | 14.3 | 8.9 | 17.0 |
| Qwen3.5-9B-Base | 7.8 | 13.7 | 11.5 | 12.6 | 17.1 | 12.8 | 17.4 |
| Gemma-4-12B | 7.7 | 14.9 | 11.9 | 14.4 | 19.3 | 13.3 | 21.2 |
| Ministral-3-14B-Base | 9.0 | 15.8 | 12.4 | 16.5 | 20.8 | 14.1 | 24.0 |

Check: the component model gives 11.62 and 12.23 GB for the anchor at 2,560 and 3,584 tokens, against 10.96 and
11.91 measured, so it overstates the fixed part and understates the per-token slope; the two columns bracket reality.

Reading it:
- **8K, 12 to 14B:** fits only with offloaded checkpoints (Unsloth's `use_gradient_checkpointing="unsloth"`), at
  about 12 to 12.5 GB.
- **16K, 12 to 14B:** borderline even with offload (13.3 to 14.1 GB by components; the empirical slope minus the
  checkpoint share gives about 15 GB for Gemma-4-12B and 17 GB for Ministral-14B). Needs a smoke test before planning on it.
- **16K, 7 to 8B:** fits with offload (8.7 to 8.9 GB) and probably without.
- **Large vocabularies** (Gemma 262,144; Qwen 248,320): full fp32 logits at 8K would be 8.6 and 8.1 GB. A fused or cut
  cross-entropy is mandatory: Cut Cross-Entropy computes the loss "without materializing the logits"
  ([arXiv 2411.09009](https://arxiv.org/abs/2411.09009)); Liger Kernel's fused linear cross-entropy reports about 60%
  lower memory ([arXiv 2410.10989](https://arxiv.org/abs/2410.10989)). The project's own chunked loss does the same job
  more slowly. [primary, verified abstracts]

### 2.3 Tooling on the RTX 5080

- **Unsloth** supports Blackwell RTX 50 GPUs with the `cu128` PyTorch build; its guide warns not to upgrade Triton on
  its own and to build xformers with `TORCH_CUDA_ARCH_LIST="12.0"`, and documents WSL setup. Whether native Windows
  works is not stated. [primary, verified;
  [guide](https://unsloth.ai/docs/basics/fine-tuning-llms-with-blackwell-rtx-50-series-and-unsloth)]
- **Unsloth context limits** (Llama 3.1 8B, QLoRA rank 32, batch 1): 40,724 tokens on 16 GB against 2,551 for HF plus
  FlashAttention-2. NVIDIA's RTX 5090 table repeats the same numbers. [primary, verified;
  [benchmarks](https://unsloth.ai/docs/basics/unsloth-benchmarks)]
- **Unsloth mirrors of bases** exist for `unsloth/gemma-4-12b`, `unsloth/gemma-4-31B-unsloth-bnb-4bit`,
  `unsloth/Ministral-3-14B-Base-2512-unsloth-bnb-4bit`, `unsloth/Qwen3.5-9B-Base`; Olmo 3 appears only as Think and
  Instruct mirrors (same architecture, so it loads), and Granite 4.1 only as post-trained mirrors. [primary, verified, HF API]
- **Recipe for long pairs:** completion-only loss (mask the draft), padding-free batching (sequences laid end to end
  with position resets, so no padding is computed), packing only if pairs are short, rank 16 to 32 on all linear
  layers, learning rate 1e-4 with cosine decay, 1 epoch (B30's setting), gradient accumulation to an effective batch
  of 8 to 16, and a resume-from-checkpoint loop, because the PC runs in at most 1.8-hour lock windows and Modal
  functions are preemptible by default (non-preemptible costs 3x). [estimate, from project practice and Modal pricing]

### 2.4 Modal GPUs and prices [primary, verified: modal.com/pricing read 2026-11-06]

Per-second list prices, converted to an hour, plus 4 cores and 32 GiB (64 GiB on 80 GB-class cards) at
$0.0000131 per core-second and $0.00000222 per GiB-second, the same convention as `experiments/modal/lf_cost.py`,
whose GPU prices match:

| GPU | Memory | GPU per hour | All-in per hour | Fits for a 14B rewriter |
|---|---|---|---|---|
| H100 SXM | 80 GB | $3.95 | $4.65 | bf16 LoRA at 16K; 32B QLoRA |
| A100 80 GB | 80 GB | $2.50 | $3.20 | bf16 LoRA at 16K |
| L40S | 48 GB | $1.95 | $2.40 | bf16 LoRA at 8K (28 GB weights), QLoRA at 16K |
| A10 | 24 GB | $1.10 | $1.55 | QLoRA only |
| L4 | 24 GB | $0.80 | $1.24 | QLoRA only, slow |
| RTX PRO 6000 (new on the page) | 96 GB | $3.03 | $3.73 | not in `lf_cost.py`; worth a calibration run |

Also on the page: B300 $7.10 and B200 $6.25 an hour, region selection 1.15 to 1.75x, non-preemptible 3x, Starter
plan $30 a month of credit. The A10G is no longer listed separately.

On rented 80 GB cards, plain bf16 LoRA beats QLoRA: no dequantization cost, and memory is not the constraint.

## 3. Penalizing copying while keeping meaning

### 3.1 What attempt 1 already shows [primary, verified, project files]

- B30's training targets copy 3.5% of their input's 8-word runs, yet on unseen writers at length the rewriter copied
  32% of D (B36). The model falls back to copying when out of distribution; nothing in standard SFT discourages it.
- Copying from the AI input is the best single predictor of Pangram's share within rewrites (Spearman 0.70, B38),
  and the free least-copying pick over 4 seeds moved section share from 0.340 (random) to 0.291 (B37 C1, B38), against
  an oracle of 0.213. The correlation is observational; copied AI wording also carries content the AI chose.

### 3.2 Literature

| Method | What it does | Evidence | Fit here |
|---|---|---|---|
| Unlikelihood training ([Welleck et al. 2019, arXiv 1908.04319](https://arxiv.org/abs/1908.04319)) | Adds a loss pushing down the probability of tokens in a negative set; the sequence-level version samples continuations from the model and penalizes tokens that complete repeats | Less repetition at the same perplexity; human raters preferred it [primary, verified abstract] | Use the sequence-level form: sample 256 to 512-token spans from the SFT model at random points of a training post, mark tokens that complete a copied word 5-gram from the draft (code, LaTeX, names, numbers masked), apply unlikelihood to them. Token-level unlikelihood on gold targets barely fires, because gold rarely copies |
| Novelty reward with policy learning ([Kryscinski et al. 2018, arXiv 1808.07913](https://arxiv.org/abs/1808.07913)) | Reinforcement learning (RL) on ROUGE plus a novel-n-gram reward | More abstraction at comparable ROUGE and human scores [primary, verified abstract] | The reward template: faithfulness term plus novelty term |
| Copy control ([Song et al. 2019, arXiv 1911.10390](https://arxiv.org/abs/1911.10390)) | One model produces "purely extractive to highly generative" outputs, controlled during training and decoding | [primary, verified abstract] | Control codes for target copy rate |
| Quality-controlled paraphrase, QCPG ([Bandel et al. 2022, arXiv 2203.10940](https://arxiv.org/abs/2203.10940)) | Conditions on target semantic similarity and lexical and syntactic distance | Higher diversity at kept meaning than the uncontrolled baseline [primary, verified abstract] | Condition the rewriter on a copy-rate bucket and pick the lowest bucket that keeps claims |
| DIPPER ([Krishna et al. 2023, arXiv 2303.13408](https://arxiv.org/abs/2303.13408)) | 11B paraphraser with lexical-diversity and reordering codes, paragraph context | Cut DetectGPT accuracy from 70.3% to 4.6% at 1% false positives "without appreciably modifying the input semantics" [primary, verified abstract]; HALO found it wrecked grounding on FACTS (`r1-papers-benchmarks.md`) | Shows control codes work; also the faithfulness risk |
| Faithfulness and abstractiveness trade-off ([Ladhak et al., ACL 2022, arXiv 2108.13684](https://arxiv.org/abs/2108.13684)) | Plots faithfulness against abstractiveness; a learned selector picks the most faithful and abstractive candidate | The MLE baseline and a faithfulness method are "both worse than the control at the same level of abstractiveness"; the selector beats the trade-off curve in human evaluation [primary, verified abstract] | The key evaluation rule: compare arms at matched copy rate. B37's pick rule is a crude selector |
| Verbatim filters are evaded ([Ippolito et al. 2022, arXiv 2210.17546](https://arxiv.org/abs/2210.17546)) | A "perfect" verbatim filter is "easily circumvented" by "minimally modified" outputs | [primary, verified abstract] | Hard n-gram bans invite near-copies (case, spacing, synonyms). Penalize normalized word n-grams, not token n-grams |
| ORPO ([Hong et al. 2024, arXiv 2403.07691](https://arxiv.org/abs/2403.07691)) | SFT plus an odds-ratio penalty on a disfavored output; no reference model | "A minor penalty for the disfavored generation style is sufficient" [primary, verified abstract] | Untested idea: chosen = human post, rejected = the input AI draft itself. Free (no sampling) and pushes the model off the draft's wording |
| MASH ([arXiv 2601.08564](https://arxiv.org/abs/2601.08564), 2026-01) | Style SFT, then DPO with chosen = gold human text, rejected = SFT samples the detector still flags, then sentence-level refinement | 92% attack success on 5 detectors (not Pangram), BERTScore about 0.90; BART-base, about 6,000 pairs, short texts [primary, verified via fetch] | Template for DPO (direct preference optimization) negatives; swap "detector flags it" for "copies most", since Pangram stays held out |
| MiniCheck ([arXiv 2404.10774](https://arxiv.org/abs/2404.10774)) | Small fact-checkers with "GPT-4-level performance" at "400x lower cost" for grounding checks | [primary, verified abstract] | Faithfulness term for rewards and preference pairs, on the Modal or PC GPU instead of Sonnet calls |

Detector-reward RL (AuthorMist, StealthRL, Adversarial Paraphrasing) is covered in `r1-papers-benchmarks.md`: it
breaks meaning and does not transfer to Pangram. Not repeated.

### 3.3 Decoding-time options [primary, verified in source code]

- HF transformers `encoder_no_repeat_ngram_size` bans any token n-gram present in the prompt and works for
  decoder-only models (the docstring example uses a causal LM). It is a token-level hard ban, so it is exposed to the
  near-copy problem above and also bans needed technical strings.
- vLLM main `SamplingParams` has presence, frequency and repetition penalties only: no n-gram ban and no DRY. Its
  repetition penalty counts prompt tokens at the unigram level, which would penalize the names and terms the post
  must keep. A copy penalty in vLLM needs a custom logits processor (interface in `longform-base-models.md`).
- llama.cpp's server has the DRY ("Don't Repeat Yourself") sampler: tokens that extend an already-seen sequence beyond
  `dry_allowed_length` get a penalty of multiplier x base^(length - allowed), with sequence breakers; the window
  `dry_penalty_last_n` defaults to 64 tokens and must be raised to cover the draft. Whether prompt tokens enter that
  window in the server path I did not confirm. [primary, verified flags; prompt coverage unverified]

### 3.4 Recommended copy-penalty design [estimate]

1. Measure copying the same way everywhere: lowercase, punctuation-stripped word 8-grams and 5-grams, with code blocks,
   LaTeX, quoted strings, numbers and capitalized names masked on both sides.
2. Training: SFT, then one preference stage. Cheapest first: ORPO with the input draft as the rejected text (no
   generation). Next: DPO on 1,000 drafts with 4 sampled 512-token spans each, chosen = gold or least-copying faithful
   span, rejected = most-copying span.
3. Decoding: a soft DRY-style penalty against the draft (normalized words, exemptions as in step 1) plus the existing
   Guard, then best of 4 by least copying among outputs that pass the claim and form checks.
4. Evaluate each arm at matched copy rate (Ladhak's control curve), never by copy rate alone.

## 4. Building many-writer (AI draft, human post) pairs cheaply

### 4.1 How others built such pairs

| Work | How the AI or source side was made | Size | Lesson |
|---|---|---|---|
| Pangram technical report ([arXiv 2402.14873](https://arxiv.org/abs/2402.14873)) | "Synthetic mirrors": an LLM writes a document matching "the topic and length of the original" from a title it extracted (essays), the rating and business (reviews), or an opening excerpt; hard negatives are human texts the classifier got wrong, each given a mirror | 40,000 per domain (360,000) at start, up to 80,000 more per round, from a 28M-document human pool [primary, verified via fetch] | Pangram learns exactly the (human document, LLM mirror) contrast. Pairs built the same way teach the rewriter the inverse of what the detector separates |
| STRAP ([Krishna et al. 2020, arXiv 2010.05700](https://arxiv.org/abs/2010.05700)) | Paraphrase target-style text into neutral text, train the inverse paraphraser | 15M sentences, 11 styles [primary, verified abstract] | The inverse-paraphrase pattern this project already uses |
| Low-resource authorship transfer ([Patel et al., arXiv 2212.08986](https://arxiv.org/abs/2212.08986)) | Target authors with only 16 Reddit posts (about 500 words each) | STRAP-style methods need "often greater than 100,000 words" per author [primary, verified abstract] | Per-writer data is never enough; the model must learn "human" from many writers |
| TinyStyler ([arXiv 2406.15586](https://arxiv.org/abs/2406.15586)) | Pegasus paraphrases of Reddit comments, reconstructed with authorship embeddings; then self-distillation over 160,000 author pairs, filtered for meaning (0.7 thresholds) and transfer, keeping about 40,000 | About 88M texts from Reddit users, each comment at most 60 tokens; self-distillation raised the joint score on unseen authors from 0.32 to 0.40 [primary, verified via fetch] | Generalization to unseen authors came from author count plus a filtered self-training round |
| LongForm-C ([arXiv 2304.08460](https://arxiv.org/abs/2304.08460)) and instruction back-translation ([arXiv 2308.06259](https://arxiv.org/abs/2308.06259)) | An LLM writes the instruction for an existing human document; curation filters the pairs | LongForm-C 27,739 pairs [primary, verified abstract; size from my memory of the paper, unverified] | Long human outputs keep "natural output" while the model learns to follow the prompt |
| LAMP ([arXiv 2409.14509](https://arxiv.org/abs/2409.14509)) and WQRM ([arXiv 2504.07532](https://arxiv.org/abs/2504.07532)) | Professional writers edited 1,057 LLM paragraphs; a writing-quality reward model trained on 4,729 judgments reached 74% and its picks were preferred by experts 66% | [primary, verified abstracts] | Not pair data at scale, but a quality judge attempt 1 lacked |
| MASH | LLM paraphrases of human texts, kept only if flagged | About 6,000 pairs | Small pair sets work for short texts |

### 4.2 Recommended pair pipeline [estimate]

1. Human side: the B32 FineWeb pipeline (2019 to 2022 dumps, captured before 2022-11-30, long personal and technical
   blog posts), capped at 5 posts per site, giving 600+ sites for 3,000 posts. Split by site; Henry's posts and test-A
   sites stay out.
2. Notes: an LLM writes reworded notes from each post (B27's prompt), at 100% and 50% doses, with the B28 manipulation
   check (8-word copying from the post at most 2% of note words).
3. AI side: at least half from Sonnet through `humanizer.llm` (it matches the test distribution: Henry drafts with
   Claude; marginal cost $0 if his plan covers it, at most 4 workers), the rest from two open instruct families on
   Modal (for example `gemma-4-31B-it` and `Qwen3.6-27B`) so the rewriter does not learn one drafter's habits.
4. Filters: drop pairs whose draft copies more than 5% of the post's 8-grams (leak), whose length ratio is outside 0.7
   to 1.4, or which fail form checks.
5. One self-distillation round after the first model (TinyStyler's lesson): generate on held-in drafts, keep outputs
   that pass the claim check and copy least, add them as extra pairs.

## 5. Cost table

### 5.1 Assumptions [estimate unless marked]

- Training FLOPs (floating-point operations) per token for LoRA with recomputed checkpoints: 6 x N (forward, recompute,
  activation gradients), x1.12 for attention at 8K; N = 14B.
- Throughput = MFU (model FLOPs utilization) x peak dense bf16 / FLOPs per token. Peaks: H100 989, A100 312, L40S 362,
  A10 125, L4 121 TFLOPS (NVIDIA datasheet values from memory, [primary, unverified]). MFU ranges: H100 and L40S 20 to
  40%, A100 25 to 45%, A10 20 to 40%, L4 15 to 30% (central values 30%, 35%, 30%, 22%).
- PC: 650 to 1,300 tokens a second for 14B at 8K (measured 720 at about 2.6K with the HF stack, minus offload and
  attention overhead, up to Unsloth's claimed 2x). RTX 5080 dense FP16 with FP32 accumulate is about 112.6 TFLOPS
  [secondary, spec sites]; the measured run implies about 59 TFLOPS, so the anchor is plausible.
- Each Modal training job adds 0.25 hours (image, weights, smoke steps, saving); each generation job 0.2 hours.
- Generation: 3,000 words x 1.4 tokens per word = 4,200 output tokens per try; decode-bound. Aggregate vLLM rates for
  a 14B model with the Guard: H100 2,200, A100 1,300, L40S 600 (FP8 weights), A10 240 and L4 120 (4-bit), PC 250
  tokens a second (vLLM in WSL2, 4-bit, 3 to 4 sequences at 16K), PC current HF stack 7.5 (measured).
- PC electricity: about 0.45 kW at $0.17 per kWh (both assumed).

### 5.2 (a) Training a 14B rewriter, 1 epoch

| Job | H100 | A100 80 GB | L40S | A10 | L4 | PC RTX 5080 |
|---|---|---|---|---|---|---|
| 2,000 pairs x 4K = 8M tokens | 1.0 h, $4.44 ($3.62 to $6.08) | 2.2 h, $6.92 | 2.2 h, $5.21 | 5.8 h, $9.01 | 8.1 h, $10.08 | 1.7 to 3.4 h, about $0.19 power |
| 3,000 x 6K = 18M | 1.8 h, $8.53 ($6.69 to $12.22) | 4.6 h, $14.58 | 4.6 h, $10.98 | 12.8 h, $19.78 | 17.9 h, $22.29 | 3.8 to 7.7 h, about $0.43 |
| 5,000 x 8K = 40M | 3.8 h, $17.54 ($13.45 to $25.73) | 9.8 h, $31.42 | 9.9 h, $23.66 | 28.1 h, $43.48 | 39.5 h, $49.14 | 8.5 to 17.1 h, about $0.94 |

Arithmetic example: 18M tokens / 3,154 tokens a second / 3,600 = 1.59 h, plus 0.25 h = 1.84 h, x $4.65 = $8.53.
The H100 is the cheapest Modal option per token at every size; A10 and L4 cost more in total despite lower hourly
prices. A 32B model roughly doubles the H100 figures (QLoRA; N x 2.3, offset by a higher MFU at larger width).

### 5.3 (b) Generating posts of 3,000 words

| Job | Output tokens | H100 | A100 80 GB | L40S | A10 | L4 | PC vLLM (WSL2) | PC current HF stack |
|---|---|---|---|---|---|---|---|---|
| 100 posts x 1 try | 0.42M | $1.18 | $0.93 | $0.94 | $1.06 | $1.46 | 0.5 h | 15.6 h |
| 100 x 4 tries, or 400 x 1 | 1.68M | $1.92 | $1.79 | $2.34 | $3.32 | $5.08 | 1.9 h | 62 h |
| 400 x 4 tries | 6.72M | $4.87 | $5.23 | $7.93 | $12.33 | $19.59 | 7.5 h | 249 h |

Arithmetic example: 6.72M / 2,200 / 3,600 = 0.85 h, plus 0.2 = 1.05 h, x $4.65 = $4.87. Claim checks, MELD and
best-of-n picking add to this; `lf_cost.py`'s "open-model claim check on about 1,100 outputs" line is $5.60 on an H100.

### 5.4 Pair generation for section 4 [estimate]

3,000 posts with half the drafts from open models: 1,500 x 4,800 output tokens (notes plus draft) = 7.2M tokens on an
H100 with a 27 to 31B instruct model in FP8 at about 1,500 tokens a second: 1.3 h + 0.2 h = about $7. Sonnet drafts
through `humanizer.llm`: $0 marginal, about 3,000 calls x 2 steps; at 4 workers and about a minute a call, about
25 hours of wall time.

## What I could not verify

- **Throughput on Modal GPUs.** No published QLoRA or LoRA throughput for 13 to 14B at 8K on H100, A100, L40S, A10 or
  L4 turned up; every Modal figure above is a FLOPs model with assumed MFU. Datacenter peak TFLOPS are from memory.
- **vLLM decode rates** for a 14B model with the Guard on each GPU, and on the PC under WSL2: estimates only.
- **Memory at 16K for 12 to 14B models on 16 GB**: my two models disagree by 2 to 4 GB; needs a smoke test.
- **Unsloth on native Windows** and on `Gemma4UnifiedForConditionalGeneration` (Gemma 4 12B's new class); PEFT and
  vLLM support for that class.
- **Granite 4.1's real context** (131,072 in config against 512K in the card).
- **Which Mistral Small 3.1 checkpoint taught Ministral 3** (base or instruct).
- **Seed-OSS base RULER** (raw card table ambiguous) and whether its two bases differ in detectability (never tested).
- **Gemma 4** pretraining synthetic share or distillation; base long-context scores (none published).
- **llama.cpp DRY** coverage of prompt tokens in the server path.
- **Fetch-tool extractions** (Granite blog, Gemma 4 report, Ministral 3 paper, Pangram report, MASH, TinyStyler, Modal
  pricing) were not cross-checked against PDFs; LongForm-C's 27,739 is from the abstract page's dataset name and my
  memory of the paper.
- **Claude CLI quota** for 3,000 to 6,000 drafting calls under Henry's plan.
- **Causality of the copy-to-AI-share link**: B38's 0.70 is across tries; no experiment has varied copying with
  content held fixed.
- **RTX 5080 tensor throughput** is from spec sites, not NVIDIA's whitepaper.

## Implications for attempt 2

### Ranked shortlist of base models

1. **`google/gemma-4-12B`** (pretrained). 12B fits the PC at 8K with offload; Apache-2.0, ungated, 256K context; the
   Gemma family read least AI among B31's raw base models (Gemma-3-12B 12%); January 2025 cutoff. Risks: new unified
   architecture (tooling support unverified), 262K vocabulary (needs fused cross-entropy), closed data, no base
   long-context scores.
2. **`allenai/Olmo-3-1025-7B`** (and `Olmo-3-1125-32B` on Modal only). Open data with contamination checks, RULER 84.1
   at 16K, fits the PC at 16K. Risks: B31 measured 33 to 37% not Human for the raw 7B (higher than OLMo-2-13B's 17%);
   7B may lack capacity; vLLM runs it through the Transformers backend.
3. **`mistralai/Ministral-3-14B-Base-2512`**. Largest model that fits the PC at 8K; Unsloth 4-bit mirror exists. Risk:
   distilled from Mistral Small 3.1, possibly an instruct teacher.
4. **`ibm-granite/granite-4.1-8b-base`** (30B on Modal). Dense, published base RULER (83.6 at 32K). Risk: about 20%
   instruction and chain-of-thought data in its last 2.5T tokens.
5. **`Qwen/Qwen3.5-9B-Base`**. Measured 34% not Human in B31; synthetic instruction data in pretraining; hybrid
   linear attention complicates tooling.

Controls and experiments rather than candidates: OLMo-2-1124-13B (attempt 1's base, 4K; the anchor), and the
**Seed-OSS-36B-Base versus -woSyn** pair on Modal as a causal test of synthetic instruction data, if that question is
still worth money after B31.

Pick between the top two or three by a rule fixed in advance on development metrics (copy rate at matched claim
support, form checks, length kept, a local quality judge), never by Pangram.

### Recommended recipe and cost

1. **Fix PC generation first** (no Modal cost): vLLM in WSL2, or llama.cpp with a merged GGUF (llama.cpp file format)
   rewriter and per-request logit bias for the Guard. Target at least 200 tokens a second. Without it, every PC arm is
   gated by a 7.5 tokens-a-second loop.
2. **Pairs:** 3,000 posts from 600+ sites (section 4.2), plus B30's 630; sequences capped at 8K (draft up to 3.5K,
   post up to 4K; longer posts split at section boundaries). Modal about $7 for the open-model half.
3. **Bake-off:** Gemma-4-12B against Olmo-3-7B, 1,000 pairs each (about 6M tokens), on the PC: about 2 x 2 hours.
4. **SFT:** winner, QLoRA rank 32, all linear layers, 1 epoch over about 18M tokens, Unsloth offloaded checkpoints and
   fused cross-entropy: PC about 3.8 to 7.7 hours, or H100 about $8.50.
5. **Copy penalty:** ORPO with the draft as the rejected text (free), against DPO on 1,000 drafts x 4 sampled 512-token
   spans (about 2M generated tokens: PC about 2 hours, or H100 about $1.50; DPO training about $7.50 on an H100 or
   about 4.5 hours on the PC).
6. **Decoding:** Guard plus a soft normalized-word copy penalty against the draft, best of 4 by least copying among
   outputs passing the claim and form checks.
7. **Generation:** dev set of 40 posts x 4 tries on the PC; final test of 100 to 400 posts x 4 tries on an H100,
   $1.90 to $4.90.

**Total:** about $10 to $15 of Modal if the PC trains and generates development sets (inside this month's remaining
$9 plus December's $30 credit, with no paid spend), or about $35 all on Modal H100s, about $44 with 25% for smoke
tests and reruns: the low end of gate 2b's $40 to $55. Before committing, spend under $1 on a 10-minute calibration
run per GPU type to replace the throughput assumptions in section 5.

Outcome-level version: the copy-rate and claim-support metrics, the memory model and the calibration run become one
script (an extension of `lf_cost.py` that reads measured tokens per second per GPU), so every later arm is priced and
checked before it runs. Missing access for that loop: a measured run per GPU type and the PC's vLLM setup.
