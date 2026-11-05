# Research agent report: r1-papers-benchmarks

Saved verbatim from the agent's final report. Unverified unless the report says it read the primary source.

## Brief given to the agent

Goal behind the task: Henry runs a research project (~/personal/humanizer) that turns AI-written drafts into prose that Pangram (pangram.com, version 4.x, the strongest commercial AI-text detector) and careful human readers judge human-written, without inventing facts. Our finding so far: a fine-tuned OLMo-2-13B base model writes prose Pangram calls Human when the content comes from human articles, but when the content comes from an AI draft (even reduced to a shuffled fact list in the extractor's words) Pangram still says AI. We are about to test whether rewording the facts fixes it. We need to know what the research literature and independent benchmarks say works against strong detectors, especially Pangram, so we pick the right next methods.

Your task: survey academic papers (arXiv, ACL/EMNLP/NeurIPS/ICLR 2024 to 2026) and independent evaluations. Use WebSearch (mode "standard"; "extended" for recent or thin results) and WebFetch. Cover:
- Pangram's own technical reports and blog posts: what the classifier is trained on (mirror prompts, hard negatives, humanizer outputs), what it claims about robustness to humanizers and paraphrasers, and any published failure modes.
- Independent benchmarks that include Pangram (for example RAID, the University of Chicago / Becker Friedman Institute detector study, any 2025-2026 humanizer-vs-detector studies): which humanizers or attacks, if any, beat Pangram, by how much, and at what quality cost.
- Attack methods with numbers: detector-guided paraphrasing ("adversarial paraphrasing"), RL against detector rewards (e.g. StealthRL, GRPO/DPO humanizers), DIPPER, recursive paraphrasing, contrastive or proxy-tuned decoding (base minus instruct), style transfer from human corpora, and agentic rewrite loops. Note transfer: does an attack trained against one detector beat others, including Pangram?
- What signal detectors actually key on (token-level distribution, discourse structure, content selection), especially any evidence that content or structure alone carries the AI signal.

Work at expert depth: read the papers' tables, not abstracts; record detector versions and dates (Pangram retrains often, so flag claims older than about 6 months). Report what you could not verify. Read only; do not sign in, create accounts or download and run code.

Return under 1000 words: (1) the 6 to 10 most relevant papers or evaluations, each with citation, link, date, method, result against Pangram or the strongest detector tested, and a one-line caveat; (2) a short verdict on which method families have credible evidence of beating Pangram while keeping meaning and quality; (3) anything that bears on our specific finding that the signal survives fact-only notes. No emojis, no em dashes.

## Report

## (1) The most relevant evidence
Items marked OLD are older than 6 months or ran against a Pangram version before 4.

1. **Dhingra & Pruthi, "Agents Can Use Base Models to Evade AI Detection" (HALO)**, arXiv 2609.31876, posted Sep 25 2026 as a v1 draft. https://arxiv.org/abs/2609.31876
   - Method: Claude Opus 5 writes partial drafts. A local OLMo-2-32B base model continues them. The agent stitches the answer from spans so that at least 90% of tokens come from the base model.
   - Result on Pangram v4 (fraction_AI, n=100 per task): average falls from 0.774 to 0.245.
     - Mythos fiction: 1.00 to 0.06
     - FACTS: 0.13 to 0.03
     - IFEval: 0.97 to 0.23
     - HealthBench: 1.00 to 0.66
   - Quality keeps about 90% of the baseline.
   - DIPPER (0.77) and iterative base-model paraphrase (0.44) wrecked grounding (FACTS score about 0.01).
   - Giving the agent Pangram as a tool did not help, because draft scores stayed near 1.0.
   - OLMo-2 beat Qwen3 and Gemma-3 as the base model.
   - Caveats: no query dates, 8 to 30 times the cost of a normal answer, and the authors ran their own evaluation.

2. **Anand et al., "Measuring, Localizing, and Ablating Alignment Signatures in LLMs" (PASTA)**, arXiv 2605.30526, May 2026 (v3 Oct 2026).
   - Same human prefixes: Pangram flags aligned-model output 98.5% of the time and base-model output 9.2%.
   - PASTA removes the direction where instruct and base model activations differ, during decoding. This cuts Pangram detection by 73 to 98 points on 7 of 11 models. Random directions cut it by at most 1.6 points.
   - It barely works on OLMo-3-7B-Instruct (minus 5.8) or Tulu-3 (minus 6.0), and fluency drops.
   - Caveats: content comes only from human prefixes, and the Pangram version is not given.

3. **Xu, Zhong, Raghunathan, Fang, Kolter (CMU), "Base Models Look Human To AI Detectors"**, arXiv 2605.19516, May 2026.
   - Llama-3-8B continuations: Pangram gives the base model 98.8% human probability and the instruct model 17.1%.
   - Their method (HIP) fine-tunes a base model on pairs of AI paraphrase and human original, then rewrites AI text over 10 rounds. Human probability rises but meaning drifts; examples invent facts by round 10.
   - The paper says "a single pass may still retain residual features of the original text."
   - StealthRL and simple paraphrasing fail against Pangram.
   - Caveat: most numbers are only in figures.

4. **Pangram's own reports**: Emi & Spero 2402.14873 (OLD); DAMAGE 2501.03437 (OLD); Pangram 4 Technical Report 2607.27183 (Jul 29 2026); Pangram 4.1 model card (Oct 19 2026, training data unchanged from 4).
   - Training data:
     - "Mirror" AI documents, made by extracting a human document's topic and writing an article on it.
     - Hard-negative mining rounds.
     - AI-edited text labeled with their EditLens method.
     - Humanizer outputs.
   - DAMAGE labels humanized AI text as AI and humanized human text as human, explicitly "an invariance" to humanization.
   - A GPT-4o humanizer fine-tuned on Pangram's own misses was still caught 93.2% of the time.
   - Pangram 4 results: 97.7% recall on 12 commercial humanizers.
   - Pangram 4 weak spots: texts under 50 words (73% detection at 1% false positive rate), one-sentence human/AI interleaving, and AI-assisted recall of 55 to 66%.
   - Caveat: vendor-run, and no base-model or agent attacks were tested.

5. **Pham, Russell, Pham, Iyyer, "Frankentext"**, arXiv 2505.18128, ACL 2026.
   - An LLM assembles stories in which about 90% of tokens are copied from human books. Pangram labels 72% of them human; HALO measured about 10% flagged on Pangram 4.
   - Caveat: fiction only, with visible tonal seams.

6. **Karr et al. (Notre Dame), "Why AI Detection Fails for Academic Integrity"**, arXiv 2608.11256, Aug 2026.
   - After the Undetectable AI v11 humanizer, Pangram 3.2 misses 96.6 to 98.5% of AI rewrites.
   - Caveats: meaning was never checked, and Pangram 3.2 has been superseded.

7. **Humanizer audits**
   - Russell, Karpinska, Iyyer, ACL 2025 (OLD): Pangram matched expert annotators on prompt-humanized o1-pro text. Experts mostly cited vocabulary (53%), sentence structure (36%) and originality (24%).
   - Jabarian & Imas, BFI WP 2025-116 (OLD): Pangram's miss rate stayed low after StealthGPT; GPTZero missed about 50%.
   - HumanizerBench, Nov 2026: Phrasly passed 25/30, WriteHuman 20/30, StealthGPT 19/30, most others 0 to 3/30.
   - Caveat on HumanizerBench: it is operated by WriteHuman, quality was not checked, and DAMAGE rates Phrasly in the lowest quality tier.

8. **Attacks trained against open-source detectors** (none tested on Pangram)
   - Adversarial Paraphrasing (NeurIPS 2025): detection drops 88% on average across 8 open detectors, but transfer between detectors is uneven.
   - StealthRL (2602.08934, v3 Oct 2026), RL against two open detectors: detection at 1% false positive rate falls from 0.45 to 0.024, but meaning consistency (NLI) is 0.32, perplexity 149, and judged quality 2.5 out of 5.
   - AuthorMist, HUMPA (ICLR 2025) and CoPA contrastive decoding (EMNLP 2025): no Pangram results.

## (2) Verdict
- **Credible against Pangram 4 with quality kept:** only base-model generation, where a base model writes the surface and the plan stays loose (items 1, 2, 3 and 5). Even HALO leaves 24% flagged on average and 66% on HealthBench.
- **Not credible:**
  - Paraphrasers (DIPPER, recursive paraphrasing).
  - Commercial humanizers at decent quality.
  - Supervised fine-tuning guided by the detector.
  - RL against open detectors: transfer to Pangram is unshown, and the HIP paper found StealthRL fails against it.
- **Untested:** RL with Pangram itself as the reward. HALO suggests the reward would be flat near 1.0.

## (3) Bearing on the fact-notes finding
- **It is predicted by design.** Pangram labels humanized AI text as AI, so whatever survives rewriting is exactly what it learned to use: which facts are chosen, their order, their density and the document's structure. Its mirrors control for topic but not for selection within a topic.
- **Idiosyncrasies (Sun et al., ICML 2025).** Classifiers can still tell which LLM wrote a text after word shuffling (88.9%) and after an LLM summarizes it (58%, chance 20%). This is model attribution, not human versus AI.
- **ARB (Perrone & Romano, 2607.29539, Jul 2026).** The same LLM rewriting LLM text stays detected 78 to 83% of the time, against 15 to 31% when it rewrites human text. Tested on zero-shot detectors only.
- **Sem-Detect (ICML 2026).** AI peer reviews converge on the same points. Human reviews polished by an LLM keep their human signal.
- **HALO's pattern matches yours.** FACTS, grounded in a human document, drops to 3% flagged. HealthBench, with AI-structured advice, stays at 66%.
- **Implication.** Rewording the facts alone will likely fail. Ablations worth running:
  - Let the base model choose which facts to use and in what order, HALO-style, instead of feeding it a complete list.
  - Drop or subsample AI facts and mix in facts from human sources.
  - Read Pangram 4's segment output and is_humanized flag to see where the signal sits.

## What I could not verify
- Pangram query dates in every academic paper.
- The BFI paper's exact numbers: the PDF would not render.
- HIP's numbers for AI-written prefixes, and HumanizerBench's quality columns.
- RAID leaderboard entries for Pangram.
- Any paper testing adversarial paraphrasing, or RL with a Pangram reward, against Pangram.
