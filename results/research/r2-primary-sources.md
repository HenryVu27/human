# Research agent report: r2-primary-sources

Saved verbatim from the agent's final report. Unverified unless the report says it read the primary source.

## Brief given to the agent

You are a research scout for a frontier research project. Work at expert depth, start from primary sources (full papers, tables, appendices, code), verify claims against them, and report what you could not verify.

THE GOAL BEHIND THE TASK: Henry is building a "full humanizer": take any AI-written draft and produce prose that Pangram 4.x (pangram.com; v4.0 2026-07-29, v4.1 2026-10-19) and careful readers judge human-written, without inventing facts. We need method details precise enough to replicate.

WHAT WE ALREADY KNOW: our fine-tuned OLMo-2-13B base-model writer reads Human on Pangram when its facts come from a human article and AI when they come from an AI draft, on the same topics and regardless of rewording or cutting generic facts (human-chosen 17/20 Human vs AI-chosen 1/20). Pangram seems to detect the AI's content plan. Base-model continuations of human text pass. A first survey already listed the sources below at abstract level; now we need their insides.

YOUR TASK: deep-read these primary sources and extract replicable details (use WebFetch on arxiv.org/abs, arxiv.org/html/<id> or arxiv.org/pdf/<id>, GitHub, Hugging Face; WebSearch mode "extended" to find mirrors; for taken-down pages use the Wayback Machine, e.g. https://web.archive.org/web/2026*/rosmine.ai*):
1. HALO, "Agents Can Use Base Models to Evade AI Detection", Dhingra and Pruthi, arXiv 2609.31876. Exactly how the agent works: prompts, how drafts are split, continuation length, how spans are chosen and stitched, the at-least-90%-base-tokens rule, how grounding to a source document is kept, ablations (which component matters most), per-task Pangram results, why HealthBench stays at 66%, failure examples, cost. Any released code.
2. PASTA, arXiv 2605.30526: how the instruct-minus-base direction is computed and applied at decoding, which layers, strength, results per model, whether it was tested on content that came from an AI plan.
3. Pangram 4 Technical Report (arXiv 2607.27183) and the 4.1 model card: architecture, the "where the idea came from" clause labeling, segment-level outputs, the AI-assisted/Mixed definitions, EditLens, known weak spots (short texts, interleaving, AI-assisted recall), what training data covers (base-model text? fine-tuned open models? OLMo?), and any statement about content-level vs style-level features.
4. Distribution Fine Tuning (DFT) by @rosmine (rosmine.ai, taken down July 2026; check the Wayback Machine) and its follow-on "Deft": the method (MMD on embeddings plus token-frequency distance against FineWeb), model, data, results.
5. Emulate-1 (who makes it, how it is trained, github.com/dalek2point3/emulate-write-evaluation results and method).
6. Unslopper (N8Programs/Unslopper-30B-A3B) and HIP (github.com/YixuanEvenXu/humanization-by-iterative-paraphrasing): training data construction and inference loop, and any per-round Pangram numbers.
Read only: do not sign in, create accounts, or download and run code.

Return under 1100 words: for each source, a compact block of replicable method details and the numbers that matter, flagged verified (you read it in the primary source) or unverified. Then 3 to 5 specific design ideas for our pipeline (fine-tuned OLMo-2-13B base writer with a fact-pool prompt, MLX on a 16 GB Mac, QLoRA on a 16 GB RTX 5080), ranked by expected effect on Pangram for AI-sourced content. No emojis, no em dashes.

## Report

## Source blocks (V = I read it in the primary source, U = unverified)

**1. HALO (arXiv 2609.31876, Duke and IISc). V, full HTML including appendices and prompts. No code released.**
- **Setup:** claude-opus-5 runs in the Agent SDK at effort xhigh. The base LM is OLMo-2-0325-32B on vLLM, 4k context.
- **Tools:**
  - `sample`: 30 calls per example; it returns 4 to 5 samples per call. In practice T is about 1.05, top-p 0.95, length 150 words by default (up to 400).
  - `check_copy_rate`: free and unlimited.
  - Bash, Read and Grep for reading the files.
- **No fixed splitting.** Samples are saved as `samples/gen_NNNN.txt`. The agent cites spans with `<copy gen=7 c0=120 c1=286/>` (character offsets), and a script splices them in afterwards.
- **Copy rate** is the share of o200k tokens that sit inside tags. The user prompt and any context document are also copy pools.
- **p in {0.6, 0.75, 0.9} is a soft target**, and the prompt says "DO NOT PAD".
- **Grounding:** the agent fixes a fact by splitting a span and typing the correction itself. On FACTS, about 60% of sessions copy from the document and never call the base LM.
- **Strategy:** the agent writes a fake partial document in the target register and lets the base LM continue it. Under 5% of prompts are few-shot. For Mythos, the agent's own partial stories are thrown away, so the base LM supplies the details.
- **Pangram 4 fraction_AI, Agent baseline vs HALO-32B at p=0.9:**

| Task | Agent | HALO p=0.9 | Quality change |
|---|---|---|---|
| Mythos | 1.00 | 0.061 | coherence 1.00 to 0.888 |
| FACTS | 0.130 | 0.028 | none |
| IFEval | 0.965 | 0.232 | none |
| HealthBench | 1.00 | 0.661 | rubric 0.703 to 0.620 |

- **Ablations:**
  - Copy rate is the main knob: Mythos scores 0.58, 0.28 and 0.06 at p = 0.6, 0.75 and 0.9.
  - Size matters. Raw continuations (n=30): OLMo-2-7B 0.267, Qwen3-8B 0.417, Gemma-3-27B 0.085, OLMo-2-32B 0.033. Setting top-p to 1.0 did not help.
  - Having the agent retype the text instead of using pointers gives the same Pangram score (0.226 vs 0.245) at lower cost.
  - Telling the agent to sound human ("+prompted") fails, and so does giving it 15 Pangram calls: its drafts all score near 1.0, so there is no signal to follow.
- **Why HealthBench stays at 66%:**
  - The prompt tells the agent the facts must be its own and that accuracy outranks the copy target, so it falls short of p.
  - 14 of 100 prompts are not in English.
  - Even the plain base LM, few-shot prompted with physician-written answers, scores 0.852. That points to a genre effect.
- **Humanizer flag:** Pangram 4 marks 17% of windows in the pointer version as humanized.
- **Cost:** $0.98 to $3.60 per query, 8 to 30 times the baseline. HealthBench averages 2.65M input tokens and 112 samples per query.

**2. PASTA (arXiv 2605.30526 v3). V**
- **Calibration:** 25 prompts (5 domains × 5).
  - The base model gets a document-style human prefix of 75 to 100 tokens.
  - The aligned model gets a chat instruction plus a 50-token "Begin with" opening.
  - Sampling: T 1.0, top-p 0.95, 400 tokens.
- **Direction:** for each layer, take the mean residual over generated tokens; v = normalize(mu_aligned minus mu_base).
- **Layer choice:** run every layer's direction and keep the one with the lowest Pangram rate on the calibration set.
- **Application:** that one v is projected out at every block input, attention output and MLP output. Default alpha is 1. Alpha 0.25 already gives most of the drop; alpha 2 damages quality.
- **Results:** Pangram falls 73 to 98 points on 8 of 11 models (Gemma-2-9B 100 to 2), but only 5.8 points on OLMo-3-7B-Instruct and 6.0 on Tulu-3-8B. Random directions move it at most 1.6 points. SFT carries most of the signature.
- **Never tested on AI-planned content or on rewriting a draft.** The chosen layer indices and the Pangram version are not stated in the text (U).

**3. Pangram 4 report and 4.1 model card. V**
- **Architecture:**
  - Backbone is an unnamed open-weight MoE trained with LoRA.
  - Linear heads: a 15-bucket segment f_AI, a 3-class per-token head (input repeated twice so early tokens see the whole window), a mixed-authorship head, and a humanizer probe.
  - Windows are 512 tokens with stride 256, then a calibrated CRF and a sentence-level majority vote.
- **Labeling ("where the idea came from"):** f_AI = (0.5·AI-Assisted + AI-Generated characters) / total. Haiku 4.5 splits the text into clauses. A clause that lexically matches the human source is Human; a clause that only matches in meaning is AI-Assisted; a clause with no match is AI-Generated.
- **AI training data is "synthetic mirrors":** an LLM is given only the topic of a human document and writes its own article. That gives same-topic pairs that differ in who chose the content. **This explains your 17/20 vs 1/20 result: the LLM's content plan is a trained label.**
- **Document rule:** Human if f_human ≥ 0.90; AI if f_AI ≥ 0.80; otherwise Mixed.
- **Scope rules:** AI text must have more output tokens than input tokens, so summaries of human input count as human. Minimum 50 words; 4.1 shows lower certainty under 150 words.
- **Weak spots:**
  - Recall of AI-assisted text: 55.0% and 65.7% on two edit sets.
  - Alternating single sentences: per-token recall 62.9%, document error 18%.
  - 4.1 is much more stable under small edits: verdict flips fell from 1.08% to 0.15%.
- **Training data and red team:** no mention of base-model, OLMo or fine-tuned open-model text. A red-team agent tried conditioning output on detailed source writing and found no bypass.

**4. DFT and Deft (rosmine). Read in the Wayback snapshot of 2026-05-22.**
- **Correction to the brief:** MMD (llama-embed-nemotron-8b embeddings, RBF kernel) and token L2 are evaluation metrics, not the training loss. The algorithm itself is proprietary.
- **Models:** Qwen3 instruct 4B, 8B and 14B; base models were dropped for poor instruction following. Training is a sequence of LoRAs.
- **Data:**
  - 185K FineWeb documents, cleaned line by line by Qwen3-32B.
  - Qwen3-32B writes a prompt, style and use case for each document.
  - GPT-5-mini writes an outline that includes the document's facts and quotes (25% of outlines are left empty).
  - Prompts carry flags for target length and whether em dashes are allowed.
- **Results (14B):** MMD 0.037 to 0.018, judge score 0.49 to 0.80.
- **Pangram claim:** 100/100 outputs Human, version not stated (U; Digg says 3.3.2). The outlines came from human documents, so the content plan was human.
- **Deft's 86% Human figure and the "short prompts get detected" tip:** U (the X posts are paywalled).

**5. Emulate-1 (Agape Keleta, tryemulate.ai). Training undisclosed (U).**
- **The dalek2point3 study (V):** 200 prompts sent to `/v1/write`, whose pipeline includes an internal rewrite stage. First output kept. Pangram 4.0 labels: 166 Human, 9 Mixed, 25 AI (83% Human). Coherence 3.49/5.
- **My reanalysis of its examples.jsonl:**
  - Shortest-prompt quartile: 95% Human (fraction_AI 0.04). Longest quartile: 75% (0.23).
  - Spearman 0.18, permutation p = 0.011, but within category only 0.11 (p = 0.12). Treat as suggestive.
  - 17 outputs use LaTeX-style quote marks (as in WritingPrompts-style data); all 17 read Human.

**6. Unslopper and HIP. V**
- **Unslopper:**
  - Model and training: Qwen3-VL-30B-A3B-Instruct at 6-bit; MLX LoRA rank 8, alpha 20, 1,000 iterations, lr 1e-4.
  - Data: 1,000 Gutenberg passages, each rewritten 10 times by GPT-4o-mini; it trains on rewritten-to-original.
  - Inference: single pass, T 0.8, repetition penalty 1.1.
  - Results on 100 GPT-5.2 stories: humanness 0 to 0.48 (25% Human, 45% Mixed, 30% AI); quality 8.60 to 7.96. Pangram version unknown.
- **HIP:**
  - Data: 11,757 pairs of RAID/MAGE human passages and GPT-5-nano paraphrases, re-sampled until meaning is preserved.
  - Training: plain `<source_text>`/`<target_text>` tags with loss on the target only; LoRA rank 128, alpha 128, lr 5e-5, one epoch.
  - Inference: 10 rounds at T 1.0, top-p 0.95.
  - Per-round numbers exist only in figures. On older Pangram, examples flip from 0% to 100% Human at round 2 with no loss of meaning.
  - On Pangram 4 (from HALO's table), 10 rounds give Mythos 0.728 and HealthBench 0.434, with HealthBench quality down to 0.414.
  - The version fine-tuned through the OpenAI API fails, and so does training only the output layer.

## Design ideas, ranked by expected effect on Pangram for AI-sourced content

1. **Let the base model plan; use the AI draft only as a checklist.**
   - Seed a human-register document prefix: headline, dateline, and a human-sourced first sentence.
   - Sample 8 to 16 OLMo continuations at T 1.0 to 1.1.
   - Keep only sentences that a local fact-checking model (NLI) or a judge confirms against the checklist, splice them, and fill missing facts with short continuations.
   - Log fact coverage and the share of text you wrote yourself.
   - Evidence: Mythos (base LM picks the details) reached 0.06; HealthBench (agent dictates every fact) stayed at 0.66.
2. **Re-source each AI fact to human text.** Retrieve human passages that state each fact and feed those instead of the AI's fact list; drop facts with no human source. This recreates your 17/20 condition and the FACTS result (0.13 for Opus alone, 0.028 with HALO). A 20-topic A/B test is cheap.
3. **Replace the fact-pool instruction with a continuation prefix.**
   - Train the QLoRA writer with facts written as "reporter's notes" or as earlier document text.
   - Seed generation with a human first sentence.
   - Evidence: structured and few-shot prompts score 0.60 to 0.85 against 0.03 for raw continuations, and HIP finds human prefixes make continuations look more human.
4. **Teach human fact selection.** Train on a fact pool that mixes the human article's facts with facts from an AI mirror of the same topic, with the human article as the target. The writer learns to drop AI-typical facts and order the rest the way a writer would. This reuses Pangram's own mirroring recipe as the source of negatives.
5. **Segment-level repair loop with Pangram 4.1 class_probabilities.**
   - Regenerate only the AI-labeled sentences, continuing from the preceding human-labeled text.
   - Never patch individual tokens, since 4.1 rarely flips on small edits.
   - Watch is_humanized, which fired on 17% of HALO's spliced windows.
   - Separate lever: test a 27B to 32B base model at 3 to 4 bit. Raw detection fell from 0.267 at 7B to 0.033 at 32B, though fitting it in 16 GB is uncertain.

I would skip PASTA: it needs an instruct model and failed on OLMo-3 (only 5.8 points).

## Not verified
- HALO's actual per-task copy rates (only in a figure).
- PASTA's chosen layers.
- Pangram backbone identity.
- The DFT training algorithm and the Pangram version behind its claim.
- Emulate's training method.
- The Pangram versions used by Unslopper and HIP.
- Deft's X-only claims.

All source text and my Emulate reanalysis inputs are in /private/tmp/claude-501/-Users-henryvu-personal/4e64b86d-db0b-493c-bcf7-4834f916f083/scratchpad/papers and /private/tmp/claude-501/-Users-henryvu-personal/4e64b86d-db0b-493c-bcf7-4834f916f083/scratchpad/emulate.
