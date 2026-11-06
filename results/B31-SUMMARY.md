# B31 in one page: do newer base models read as AI because of their training data?

For Henry, 2026-11-06, about 00:45. Full write-up: `results/REPORT-2026-11-04-lora.md` section 34. Claims ledger: `results/research/b31-claims.md`.

## The answer

**No, not at any size B31 can measure.** Neither the web crawl's date (H1) nor synthetic data added on purpose (H2) explains when a base model reads AI.

- **Every base model reads AI some of the time, whatever its vintage.** Pythia, trained only on 2020 data, reads not Human on 28% of its continuations of human text. Qwen3.5 (2026) reads not Human on 34%. The true human continuations read Human 30 of 30.
- **Synthetic mid-training changed nothing.** Olmo 3 before and after its mid-training stage, which is about half synthetic text plus QA and instruction data: 37% and 33%. The change in AI share is -0.001 (95% interval -0.17 to +0.17).
- **Crawl date: right direction, not significant.** OLMo 2 (crawl through 2022) against Olmo 3 (through December 2024), both at the end of pretraining: 20% against 37%. AI share rises 0.12 (interval -0.08 to +0.31), Holm-corrected p 0.50.
- **The opening matters more than the model.** Depending on which human opening is continued, 0% to 74% of the models' continuations read AI, four times the spread chance would give.
- **Post-training is the big effect.** The instruct models read AI on 15 of 15 texts each; their own base models read AI on 27% and 43% of the same openings.

## What this means for the project

- **The base-model route has no visible shelf life from training data.** The newest model tested (Qwen3.5, 2026) reads like the oldest (Pythia, 2020).
- **B1's Qwen against OLMo result was mostly chance.** One AI verdict against three Human ones is what sampling alone produces at these rates. At full precision on 29 openings, Qwen3.5 does read AI more often than OLMo-2-13B (34% against 14%, uncorrected p 0.03), but no more than Pythia or Olmo 3. 4-bit quantization did not cause it: 4-bit texts read Human more often.
- **Raw base-model continuations read Human only about 70% of the time.** The project's higher Human rates come from fine-tuning and human-sourced content, not from the base model alone.
- **OLMo-2-13B (17%) and Gemma-3-12B (12%) read lowest,** but most differences between models are within noise. Choosing a writer from these numbers would break the held-out rule, so a writer comparison needs its own pre-registered test.

## Claims checked (4 research agents, my own primary-source spot checks, 1 outside judge)

| Claim | Status |
|---|---|
| B1: OLMo reads Human, Qwen reads AI | Recorded correctly; the inference is refuted (sampling) |
| Newer crawls carry AI text into base models (H1) | Not established; small effects not excluded |
| Synthetic or instruction data carries it (H2) | Not supported (Olmo 3 test and across models) |
| Qwen reports describe instruction and synthetic data in pretraining | Verified, and understated |
| HALO: OLMo-2 beat Qwen3 and Gemma-3 | Partly true; at 7 to 8B the gap is noise |
| Xu, PASTA: base models look human | True in direction; no base model here is near 99% Human |
| Olmo 3 facts (release, context, Dolma 3, synthetic mid-training, checkpoints) | Verified; plus 3 ablation checkpoints nobody had noted |
| AI text is a large share of new web pages | True for new articles (35 to 50%); about 2 to 9% of whole crawls |

An outside agent recomputed every statistic from the raw verdicts and matched them. It adds three cautions. Openings, not texts, are the real sample, so per-model intervals are optimistic. The 4-bit arms cover web pages only. The filters dropped some hard openings for some models.

## Spend

| Resource | Used | Budget |
|---|---|---|
| Pangram | 1,986 credits (675 texts); dashboard 14,076 to 12,090 | 2,500 |
| Modal | $3.01 of compute posted by 00:36 against the free credit, billed $0.00; the last runs may add under $1 when they post | $30 credit |

About 680 GB of model weights remain on the Modal Volume `b31-weights`, inside the free 1 TiB. Delete it with `modal volume delete b31-weights` if no follow-up needs them.

## For you

- **Delete the Hugging Face token you pasted in chat**, at https://huggingface.co/settings/tokens. It is stored as the Modal secret `huggingface`, which you can also remove.
- **Optional next step: what makes an opening produce AI-read continuations.** Is it genre, voice or topic? It is the biggest lever B31 found.
