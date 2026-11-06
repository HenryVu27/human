# Research agent report: open AI-text detectors for the long-form program (2026-11-06)

## Brief given to the agent

Work at expert depth, start from raw data, verify with an external check, report what you could not verify.

GOAL BEHIND THE TASK: the humanizer project (~/personal/human) makes AI-drafted blog posts read human to Pangram 4.x without inventing facts. Pangram is a held-out judge: it may never select a model, prompt or writer. So development needs a panel of strong off-the-shelf open AI-text detectors, run on Modal GPUs (L4 24 GB, A10G 24 GB, L40S 48 GB, A100 40/80 GB, H100), on texts of 200 to 4,000 words written by base models, fine-tuned base models, instruct models (Claude Sonnet, GPT-5, Gemini 2.5, open instruct models) and humans (pre-2022 blogs and essays). We will measure each detector's agreement with Pangram on about 1,300 Pangram-labelled texts; we will NOT train any detector on Pangram labels. The panel must be cheap (a few dollars per thousand long documents) and diverse in mechanism. Today is 2026-11-06.

TASK: find what is strongest and practical in late 2026, from primary sources (papers, official repos, model cards, leaderboards):
1. Zero-shot detectors: Binoculars (Hans et al. 2024, which observer/performer pair, thresholds, max tokens), Fast-DetectGPT (Bao et al.; sampling and scoring model choices, analytic criterion; which pair the authors now recommend), and anything newer with credible evidence of beating them on modern LLM text (for example Glimpse, Lastde/Lastde++, AdaDetectGPT, DNA-DetectLLM, Binoculars with newer model pairs, or 2026 methods). For each: exact models (Hugging Face IDs), VRAM in bf16, tokens per text it handles, how it scales to long texts (windowing), license.
2. Supervised open checkpoints: for example desklib/ai-text-detector-v1.01, RADAR, the RAID leaderboard leaders, Fakespot, SuperAnnotate, any 2026 open releases, and DetectAnyLLM/DDL. For each: Hugging Face ID, base architecture, training data and its date (does it include Claude or GPT-5 era text?), max length, license, whether it is open-weights usable offline.
3. Current state of the RAID leaderboard (raid-bench.xyz) and any 2025 to 2026 benchmark on modern generators (e.g. DetectRL, MAGE, M4GT, any 2026 benchmark) that compares these methods, especially on long texts, humanized or paraphrased text, and Claude-family output.
4. Any published agreement or correlation between an open detector and Pangram (e.g. papers that report both).
5. Known failure modes relevant to us: false positives on non-native or formulaic human text, sensitivity to length, sensitivity to code and tables in technical posts, and base-model text (do zero-shot detectors built on base-model likelihood call base-model text AI?).

Then RECOMMEND a panel of 2 to 4 detectors to run now, with exact recipes: model IDs, scoring formula, threshold conventions, window length and stride for long texts, GPU type and an estimate of seconds per 1,000 tokens, and code repos to copy from. Prefer diversity: at least one likelihood-ratio zero-shot method and at least one supervised classifier.

RULES: read only. WebSearch and WebFetch (arXiv HTML, GitHub READMEs and code, Hugging Face model cards and API at https://huggingface.co/api/models/<id>). Do not sign in, create accounts, or download and run code. No emojis, no em dashes, spell out acronyms on first use, no blockquotes.

OUTPUT: write your full report to `/Users/henryvu/personal/human/results/research/longform-open-detectors.md`, starting with a "Brief given to the agent" section (paste this brief), then "## Report". Report under 1,200 words, every item marked V (read in primary source) or U, with links. End with "What I could not verify". Return the same report as your final message.

## Report

V = I read it in the primary source (code, paper, model card, Hugging Face (HF) API, leaderboard files). U = unverified or my own estimate. FPR = false-positive rate; TPR = true-positive rate; AUROC = area under the ROC curve.

**Bottom line**
- No paper reports an open detector against Pangram 4 per document. Closest: open Pangram vs Pangram 3.3, kappa 0.61 (V).
- Finding (V, from both codebases): Binoculars and analytic Fast-DetectGPT on one model pair use identical per-token inputs (base-model probabilities, instruct-model log-probabilities). One mechanism; one forward pass gives both.
- Open detectors call much base-model text AI; Pangram mostly calls it Human. Measure agreement per stratum (human, base, fine-tuned base, instruct).

### 1. Zero-shot detectors
- **Binoculars** (V, [detector.py](https://github.com/ahans30/Binoculars/blob/main/binoculars/detector.py), [paper](https://arxiv.org/abs/2401.12070)): observer `tiiuae/falcon-7b`, performer `tiiuae/falcon-7b-instruct` (Apache-2.0; 7.2B parameters each, about 29 GB together in bf16). Score = performer log-perplexity / cross-entropy of observer probabilities against performer log-probabilities. AI if below 0.8536 (low-FPR mode) or 0.9015 (F1 mode). Truncates to 512 tokens; thresholds tuned on 512-token prefixes. BSD-3; last commit May 2024, no newer pair.
- **Fast-DetectGPT** (V, [README](https://github.com/baoguangsheng/fast-detect-gpt), [code](https://github.com/baoguangsheng/fast-detect-gpt/blob/main/scripts/fast_detect_gpt.py)): since 31 Jan 2026 the authors rank "Llama3-8B/Llama3-8B-Instruct > falcon-7b/falcon-7b-instruct >> gpt-j-6B/gpt-neo-2.7B" (sampling/scoring). Gaussian parameters for the Llama pair were added 5 Feb 2026 (human mean 0.160, AI mean 2.469). HF IDs not in the code (U: `meta-llama/Meta-Llama-3-8B` and `-Instruct`, manually gated). Analytic criterion = Σ(ll − μ)/sqrt(Σ var), which grows with the square root of length. MIT.
- **Newer, small or unproven gains (V):**
  - DNA-DetectLLM ([2509.15550](https://arxiv.org/abs/2509.15550)): Falcon pair; AUROC 98.3 vs Binoculars 97.4 on GPT-4 Turbo, Gemini-2.0 and Claude-3.7 texts; 1,024-token cap.
  - AdaDetectGPT ([2510.01268](https://arxiv.org/abs/2510.01268)): gemma-2-9b pair; +0.002 to 0.004 AUROC over Fast-DetectGPT on GPT-4o and Claude-3.5 texts of 200 tokens or less.
  - Lastde++ trails Binoculars on DetectRL, 75.4 vs 83.2 (DNA-DetectLLM Table 2). Glimpse needs a proprietary API.
  - DetectAnyLLM ([2509.14268](https://arxiv.org/abs/2509.14268)): trained GPT-Neo-2.7B scorer; AUROC 0.92 to 0.95 on polished or rewritten text (90 to 220 words) vs 0.55 to 0.57 for Fast-DetectGPT. Checkpoint `fjc2005/DetectAnyLLM` is not public (HF API error).

### 2. Supervised open checkpoints (V: HF API and cards, read today; all open weights, usable offline)
| HF ID | Base | Training data | Tokens | License |
|---|---|---|---|---|
| `anon-review-meld-2026/meld` ([paper](https://arxiv.org/abs/2605.06903)) | Ettin-1B encoder | 10.3M texts, 78 generator tags incl. claude-sonnet-4.6, gpt-5-chat, gemini-3 | 2,046 windows, cap 16,384 | MIT |
| `nakas/gpttrace-v8s-1b` | Ettin-1B | RAID, MAGE, pre-2022 FineWeb, Claude and GPT-6.x humanizer rewrites | 512 | CC BY-SA |
| `desklib/ai-text-detector-v1.01` | DeBERTa-v3-large | RAID only (2023 generators) | 768 | MIT |
| `SuperAnnotate/ai-detector` | RoBERTa-large | 14 models incl. Anthropic (2024), plus RAID | 512 | custom |
| `fakespot-ai/roberta-base-ai-text-detection-v1` | RoBERTa-base | not stated | U | Apache-2.0 |
| `TrustSafeAI/RADAR-Vicuna-7B` | RoBERTa-large | Vicuna-7B, 2023 | U | non-commercial |
| `pangram/editlens_Llama-3.2-3B` (open Pangram) | Llama-3.2-3B | GPT-4.1, Claude Sonnet 4, Gemini 2.5 Flash | 1,024 | CC BY-NC-SA, gated |

MELD's [meld.py](https://huggingface.co/anon-review-meld-2026/meld) strips markdown, pools token scores by a top-quantile mean and ships 1% FPR thresholds (3.92 worst stratum, 1.65 pooled) (V). It is an anonymous-review repo that may change or vanish.

### 3. Benchmarks
- **RAID** (V, my recomputation of all 63 `results.json` files in [liamdugan/raid](https://github.com/liamdugan/raid/tree/main/leaderboard/submissions)): saturated. Twenty systems reach about 0.996 or more (accuracy at 5% FPR, no attacks); the open ones trained on RAID's train split, on 2023-era generators (GPT-4, ChatGPT, Llama-2-chat, Mistral, MPT, Cohere). Open: GPTTrace-1B 1.000, MELD 0.998, desklib v1.01 0.949, Binoculars 0.790, RADAR 0.656. No Pangram entry; it cannot rank detectors on 2026 text.
- **MELD-eval** (V, MELD paper): GPT-5.4-mini, Gemini-3-Flash, Claude-Haiku-4.5 and Qwen-3.6, clean plus attacked. TPR at 1% FPR: MELD 99.7, ModernBERT 95.5, Fast-DetectGPT 17.0, Binoculars 0.6. The [Pangram 4 report](https://arxiv.org/abs/2607.27183) (Table 25) repeats these and adds open Pangram 61.7.
- **Peer reviews by 2026 models** (V, [2603.20450](https://arxiv.org/abs/2603.20450)), thresholds at 0% FPR: Pangram TPR 93 to 99, Fast-DetectGPT 63 to 72, Binoculars 14 to 22. After humanization the zero-shot methods flag almost nothing.
- **Claude, short texts** (V): Binoculars AUROC 0.944 on Claude-3.5-Haiku (AdaDetectGPT), 95.3 on paraphrased Claude-3.7 (DNA-DetectLLM). Zero-shot methods rank well but fail at strict thresholds. No benchmark above about 1,000 tokens found.

### 4. Agreement with Pangram (V)
- Pew: open Pangram (threshold 0.2) vs Pangram 3.3 on 62,370 pages, 96% agreement, kappa 0.61 ([methodology](https://www.pewresearch.org/data-labs/2026/08/20/methodology-ai-content/)).
- Visokay et al. ([2610.36631](https://arxiv.org/abs/2610.36631), Table B.3): false positives of open Pangram and Binoculars-Falcon on pre-2022 pages are independent (phi −0.002). On RAID AI text, hits correlate at phi 0.27 (Binoculars vs open Pangram) and 0.43 (Pangram 4 vs open Pangram). On co-written text, open Pangram flags 94.2% and Binoculars 34.1%.
- Pangram 4 report (Tables 24 to 28): vendor-run baselines, no correlations.

### 5. Failure modes
- **Base-model text** (V, RAID files; RAID samples purely at random): at 5% FPR, Binoculars flags 64 to 74% of sampled base Mistral, MPT and GPT-2 text vs 99 to 100% of sampled Mistral-chat, MPT-chat, Llama-2-chat and ChatGPT text, and 0 to 1% with repetition penalty 1.2. Fast-DetectGPT flags 71 to 92%, desklib 76 to 98%. Pangram flags 9% of base outputs (PASTA, `b31-base-detectability.md`). Use a scoring model outside the writer families (U: a same-family scorer should make writer text look more AI).
- **Non-native text** (V): on Liang et al. essays at F1-tuned thresholds, FPR is 0.56 for Binoculars, 0.67 for Fast-DetectGPT and 0.055 for open Pangram ([vendor post](https://www.pangram.com/blog/introducing-open-pangram)). The Binoculars paper gets 99.67% right on ESL essays (EssayForum) at its own threshold. DeBERTa-ConPara's card reports 13 to 67% FPR on academic prose.
- **Length** (V): Binoculars' FPR on pre-2022 pages is 6.9% under 900 characters and 1.3% over 1,800 (Visokay Table B.4). MELD's FPR reaches 5.5% at 192 words or fewer.
- **Code and tables:** Binoculars never tested code (paper Sec. 6). Pangram 4 excludes code from its benchmark (V). No measured FPR on technical posts found.

### Recommended panel
Pre-register: thresholds at 1% and 5% FPR on our own pre-2022 human set, not the shipped ones; AUROC and Spearman correlation against Pangram's AI fraction, per stratum.
1. **Likelihood pair, zero-shot:** Falcon-7B plus Falcon-7B-Instruct, bf16, on an L40S (too big for L4 or A10G). Use 512-token windows with stride 256, scoring each token once.
   - Emit document Binoculars = Σ(−ll)/Σ(−μ), and the share of windows below 0.8536.
   - Emit Fast-DetectGPT as the mean per-window z over each window's scored tokens.
   - Copy `detector.py`, `metrics.py` and `fast_detect_gpt.py`. About 0.5 s per 1,000 tokens (U, at about 35% of peak bf16).
2. **MELD, supervised and modern:** the repo's `Scorer` unchanged, at a pinned revision, on an L4. Under 0.1 s per 1,000 tokens (U).
3. **GPTTrace v8s, supervised, humanizer-aware:** 512-token windows with stride 256; mean logit; the card's 1% FPR threshold is a logit of 9.3. L4, about 0.1 s per 1,000 tokens (U). Keep it only if its FPR on our human set is 5% or less.
4. **Optional:** desklib v1.01 (768-token windows) as an old-data control.

Cost (U): about $1 to $2 per 1,000 documents of 3,000 tokens, nearly all from member 1 (L40S $1.95 an hour, V, [Modal pricing](https://modal.com/pricing)).

**Decision for Henry:** open Pangram tracks Pangram best, but it is Pangram's own model, so selecting with it weakens the held-out judge. I would use it as a diagnostic only.

### What I could not verify
- Clean-text MELD-eval numbers for Binoculars and Fast-DetectGPT; which pair RAID ran for Fast-DetectGPT (Appendix F truncated).
- MELD and GPTTrace training claims; neither is independently replicated, and GPTTrace v8s is five days old.
- Whether Henry's Llama access covers the Meta-Llama-3 repositories.
- Any detector on 2,000 to 4,000-word documents, or on code and tables.
- Throughput and cost figures (arithmetic, not measured).
- An earlier note's "Binoculars flags only 8 to 13% of what Pangram flags"; not found in Visokay et al.
