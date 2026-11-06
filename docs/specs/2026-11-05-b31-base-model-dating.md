# B31 design: are newer base models detectable because of what they were trained on?

Written 2026-11-05, 23:35 to 00:10 CST, by the B31 head session. The script with the binding rules is
`experiments/b31_basedate.py` (committed 7fad7fe at 23:51 on branch b31-basedate, before any text for scanning
existed; copied to master at 23:59; amendments in its docstring). Claims ledger:
`results/research/b31-claims.md`. Brief: `docs/briefs/2026-11-05-b31-head.md`.

## Why it matters

The humanizer writes with a fine-tuned OLMo-2-13B base model because base-model text reads Human to Pangram 4.x. If
newer base models already carry the chat-model signature, that route has a shelf life, and choosing a base model means
choosing a training-data date. Beyond the project, a base model that reads as AI before any chat tuning would say
something about the web (AI text in the crawl) or about pretraining practice (synthetic and instruction data added on
purpose).

Goal behind the goal: know which base models the project can use now and in a year, and why.

## What the literature check changed

Details and sources are in the claims ledger. The points that shaped the design:

1. **B1's evidence is thinner than reported.** One Qwen sample against three OLMo samples, from different documents and
   different selection rules; a fifth scanned text has no recorded verdict.
2. **HALO's base-model comparison does not show a family effect at matched size.** Its prompts were written by Claude;
   Qwen3-8B against OLMo-2-7B is within noise; size (OLMo-2 7B 0.267 against 32B 0.033) and top-p (0.267 against
   0.380) move the score as much. So B31 holds the prompt human, compares at 7 to 9B, and fixes one decoding setting.
3. **Base models copy the register of their prompt** (HALO: 0.113 on human stories, 0.602 on AI responses). Every arm
   gets the same human-written openings.
4. **Qwen documents instruction data in pretraining since 2023** and trillions of synthetic QA and instruction tokens
   in Qwen3; Xu et al.'s figure puts Qwen3-Base at 0.875 human against Llama-3-Base at 0.988. Qwen has no checkpoint
   without that data, so Qwen alone cannot separate H1 from H2.
5. **Olmo 3 can.** Its pretraining stage (crawl to CC-MAIN-2024-51) has no LLM-generated source; its mid-training stage
   is about half LLM-generated, with QA, instruction data and thinking traces; both checkpoints are published, and so
   are three mid-training ablations from a 2T checkpoint that split "QA and instruction data" from "math, code and
   thinking traces".
6. **The crawl's AI share is modest for the models we can test.** About 2% of a 2023 crawl and 5 to 9% of a 2024 to
   2025 crawl (whole-crawl estimates, Pangram family), more after chat-trained quality filters, which both OLMo 2 and
   Olmo 3 use. A model with a December 2024 cutoff trains mostly on older dumps. So B31 tests H1 at the 2024 level of
   pollution, not at 2026's.

## Question and hypotheses

Does a base model's Pangram signal on continuations of human text track:
- **H1**, the date of its web crawl (later crawls hold more AI text, concentrated by quality filters);
- **H2**, LLM-generated or instruction-format data added on purpose in pretraining or mid-training;
- **H0**, neither: family, size, decoding or noise?

## Design

Stimuli: 30 human openings written before ChatGPT, the first 120 words each: 20 FineWeb-Edu pages from
CC-MAIN-2020-50 (B1's documents h0600 to h0619) and 10 personal essays by 10 bloggers dated 2000 to 2022-11-24, picked
by a hash rule. Only the continuation is scored, cut at a sentence end to 150 to 250 words (HALO's raw-continuation
length).

Generation: plain text prompt, bf16 weights, vLLM on Modal, temperature 0.8 and top-p 0.95 (the project writer's
setting), no repetition penalty, 512 new tokens, three seeded samples per opening; the first sample that passes the
mechanical filters (length, non-prose, non-English, repetition, copying or recalling the source) is used. Every failure
is counted by reason.

| Arm | Checkpoint | Crawl to | LLM text | Instruction data | Role |
|---|---|---|---|---|---|
| human | true continuation | | | | Pangram's false-positive rate here |
| pythia-6.9b, pythia-2.8b | EleutherAI Pythia | 2020 | none | none | pre-ChatGPT anchor |
| olmo2-7b-s1 | OLMo-2-1124-7B end of stage 1 | 2022 | none | none | P2 baseline |
| olmo2-7b, olmo2-13b | OLMo-2 final (13B is B1's model) | 2022 | mid | mid (FLAN) | OLMo-2 mid-training; B1 at full precision |
| olmo3-7b-s1 | Olmo-3-1025-7B end of stage 1 (5.93T) | 2024-51 | none | none | P1 and P2 |
| olmo3-7b-s2 | end of mid-training | 2025-06 | mid (about half) | mid | P1 |
| olmo3-7b | final (long context) | 2025-06 | mid | mid | |
| olmo3-7b-2t | stage 1 at 2.0T tokens | 2024-51 | none | none | ablation start |
| olmo3-7b-genqa | 2T plus 100B Gen-QA mix | 2025-06 | mid | mid | QA and instruction data |
| olmo3-7b-mct | 2T plus 100B math-code-thinking mix | 2025-06 | mid | none | other synthetic data |
| olmo3-7b-r5 | 2T plus 100B final mix | 2025-06 | mid | mid | |
| olmo1-7b | OLMo-7B-0724 | 2023-06 | none | pre (FLAN) | 2023 crawl point |
| phi-2 | Phi-2 | 2023 | pre (GPT-3.5 textbooks) | undocumented | synthetic, old crawl |
| nemotron-9b | Nemotron-Nano-9B-v2-Base | 2025-13 | pre (33%) | pre | synthetic, new crawl |
| mistral-small-24b | Mistral-Small-24B-Base-2501 | undocumented (2025 model) | none (stated) | undocumented | new model, no synthetic data claimed |
| mistral-7b, mistral-nemo-12b | Mistral 2023, 2024 | undocumented | undocumented | undocumented | family series |
| qwen1.5-7b to qwen3.5-9b | Qwen 2024 to 2026 | undocumented | pre (from Qwen2) | pre | B1's family, release series |
| olmo2-13b-instruct, qwen3.5-9b-instruct | chat models, B1's chat prompt, 15 openings | | | | positive controls |
| olmo2-13b-q4, qwen3.5-9b-q4 | B1's own 4-bit MLX texts, 20 openings | | | | quantization and B1 replication |

## Contrasts and what each hypothesis predicts

| Contrast | H1 predicts | H2 predicts |
|---|---|---|
| P1: olmo3-7b-s1 to olmo3-7b-s2 (same crawl, add synthetic and instruction data) | small rise | rise |
| P2: olmo2-7b-s1 to olmo3-7b-s1 (pretraining only, crawl 2022 to 2024) | rise | no rise |
| olmo3-7b-mct against olmo3-7b-genqa | equal | genqa higher if the assistant register comes from QA and instruction data |
| olmo3-7b-2t against the three ablations | equal | ablations higher |
| pythia-2.8b to phi-2 (old crawls, add synthetic textbooks) | no rise | rise |
| mistral-7b to mistral-small-24b (2023 to 2025, no synthetic data stated) | rise | no rise (size works against a rise too) |
| olmo2-7b-s1 to olmo2-7b (add FLAN and synthetic math) | none | rise |

H0 predicts no contrast passes and base arms sit near the human arm.

Primary test: sign-flip permutation test on the paired difference in Pangram's AI share for P1 and P2, Holm-corrected;
a contrast supports its hypothesis at corrected p < 0.05 with a rise of at least 0.15 in mean AI share or 15 points in
share not Human. Everything else is secondary and reported uncorrected. Validity gates: the human arm reads Human on 85%
or more, each instruct arm not Human on 70% or more.

Power: with 30 paired openings, a 0.15 shift in mean AI share is detectable when most openings move the same way; a
smaller or patchier effect will show as inconclusive, and the script fixes in advance a second sample for a primary
contrast whose corrected p lands between 0.05 and 0.20.

## What B31 cannot separate

- **H1 after 2024.** Every model here with a 2025 or 2026 crawl also has deliberate synthetic data (Olmo 3 mid-training,
  Nemotron, Qwen) or no documentation (Qwen3.5, Mistral Small). Mistral Small's "no synthetic data" is a blog claim.
- **Crawl date against filter design.** Olmo 3's stage 1 differs from OLMo 2's in crawl date and in a quality filter
  trained on more chat output (UltraChat, WildChat). P2 tests the two together, which is how H1 would act in practice.
- **Data against annealing.** Mid-training also anneals the learning rate. The 2T ablations all anneal, so differences
  among them are data; the 2T-to-ablation step is data plus annealing.
- **Decoding.** One setting (temperature 0.8, top-p 0.95). HALO shows top-p alone moves a base model's score.
- **Detector.** Pangram 4.x is both the judge and, through its open model, the instrument of most web-pollution
  estimates. B31 asks what Pangram sees, not what is true about authorship.

## Budget

- Modal: about $3 to $6 of compute for 25 models (L40S at $1.95 an hour, one A100-80GB at $2.50 for Mistral Small),
  weights on a Volume within the free 1 TiB; checked with `modal app list` afterwards.
- Pangram: at most 2,100 credits for phase 1 (about 3 credits per 250-word text; priority 3 arms only if the projected
  total fits), of B31's 2,500.

## Phase 2 (only if phase 1 supports H1)

Scan the crawl itself: a few dozen FineWeb or Common Crawl documents per crawl year after filtering, to measure the AI
share the H1 mechanism needs, with the remaining credits.
