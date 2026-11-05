# Research agent report: r2-adjacent-fields

Saved verbatim from the agent's final report. Unverified unless the report says it read the primary source.

## Brief given to the agent

You are the "range" member of a frontier research crew: bring methods from adjacent fields that the AI-detection community has not used yet. Work at expert depth, read primary papers (tables, not abstracts), verify, and report what you could not verify.

THE GOAL BEHIND THE TASK: Henry is building a "full humanizer": take any AI-written draft and produce prose that Pangram 4.x (the strongest commercial AI-text detector, trained on topic-matched human/AI "mirror" pairs, hard negatives and humanizer outputs; it labels text by where its ideas came from) and careful readers judge human-written, without inventing facts.

KEY FINDING TO EXPLAIN AND BEAT: a fine-tuned OLMo-2-13B base-model writer reads Human when given facts extracted from a human article, and AI when given facts extracted from an AI draft on the same topic, regardless of rewording or cutting to specific facts (17/20 vs 1/20 Human). AI drafts state about 50% more facts per topic, more generic claims and hedges (18% vs 12%), fewer numbers (16% vs 25%) and names (28% vs 43%), and share almost no facts with the human article on the same topic. Base-model text conditioned on human context passes. So the detectable signal is the content plan: which points, how many, how typical. Restated as verbs, the task is: "make a machine's choice of what to say indistinguishable from a person's choice, while saying only what the source supports".

YOUR TASK: survey fields that have studied exactly that verb, and turn their methods into concrete experiments. Use WebSearch (mode "extended" where needed) and WebFetch. Fields and leads (go beyond these):
1. Mode collapse and typicality bias in aligned LLMs: why RLHF models choose the most typical content; fixes such as Verbalized Sampling (Zhang et al. 2025), base-model planning, "creativity/diversity" decoding, min-p, temperature on the plan only; measurements of homogenization of content (e.g. idea diversity studies).
2. Natural language generation content selection and document planning (data-to-text, Rhetorical Structure Theory planners, "what to say" vs "how to say"): learned content selectors trained on human documents; entity-grid coherence models.
3. Authorship obfuscation and stylometry (PAN shared tasks, adversarial stylometry): what survives obfuscation, and how obfuscators change content-level signals.
4. Cognitive and editorial practice: how human writers and editors choose and order points (journalism inverted pyramid, information density, specificity, anecdote rate), and any corpus statistics on human vs LLM topic coverage, specificity, hedging, discourse moves (e.g. Reinhart et al. PNAS 2025 on grammatical profiles; Russell et al. ACL 2025 cues: equal coverage, balanced hedging, safe examples, recap conclusions).
5. Distribution matching and density-ratio methods: using a discriminator between human and AI content plans as a learned prior (classifier-guided sampling, rejection sampling, importance weighting, GAN-style or energy-based reranking), applied at the plan level instead of the token level.
6. Retrieval of human structure: borrowing a real human document's plan (outline, discourse moves, proportions) as a template for new content, as in template-based or retrieval-augmented generation.

Return under 1000 words: (1) the 8 to 12 most useful methods or findings, each with citation, link, date, the core idea in one line, evidence, and how it maps onto our pipeline; (2) a ranked list of 5 concrete experiments for our setup (fine-tuned OLMo-2-13B base writer fed a fact pool, Claude available as an editor, 16 GB Mac and 16 GB RTX 5080, Pangram dashboard scans of about 20 texts per test, a corpus of about 900 human articles with AI mirrors on the same topics), each with the hypothesis, the manipulation, the control, and what result would change our plan; (3) what you could not verify. No emojis, no em dashes.

## Report

The strongest finding is that the content-plan signal has been seen before outside AI detection. Instruction-tuned models choose the most typical points, and they miss the idiosyncratic choices that real writers make. Below are 9 method groups, two findings that cut against our assumptions, 5 ranked experiments and what I could not verify. I read the Russell and Spangher tables directly. The Verbalized Sampling, Kim and Muñoz-Ortiz numbers came through a page fetch, and anything weaker is listed in section 3.

**1. Methods and findings**

1. **Verbalized Sampling (VS).** Zhang et al., arxiv.org/abs/2510.01171, Oct 2025.
   - Idea: preference data rewards typical text.
   - Evidence: on 6,874 HelpSteer pairs rated equally correct, raters still favoured the answer a base model finds more likely (alpha 0.57 +/- 0.07).
   - Asking for 5 answers with stated probabilities and sampling the tail (p < 0.10) gives 1.6 to 2.1 times the diversity. It keeps 66.8% of the base model's diversity after direct preference optimization; plain prompting keeps 23.8%.
   - Mapping: the base model's log-likelihood of a fact is a ready typicality meter.
   - Artificial Hivemind (arxiv.org/abs/2510.22954, NeurIPS 2025) finds 70+ models share the same modes. So no instruct model's tail is a human tail.

2. **Spangher et al., "Do LLMs Plan Like Human Writers?"** aclanthology.org/2024.emnlp-main.1216, EMNLP 2024.
   - Evidence: a fine-tuned large language model (GPT-3.5) matches journalists' angles at 63.6 F1 and their sources at 27.9. Zero-shot GPT-4 scores 56.3 and 21.2, and few-shot examples did not help.
   - The human ideas the model did match were the less creative ones.
   - Mapping: this is the closest published precedent to B5.

3. **Alignment, not pretraining, homogenizes content.**
   - Padmakumar and He, arxiv.org/abs/2309.05196, ICLR 2024: essays co-written with InstructGPT lose content diversity; with base GPT-3 they do not.
   - Reinhart et al., PNAS, Feb 2025: instruction tuning produces the dense, noun-heavy style, while base Llama tracks human rates.
   - BARE, arxiv.org/abs/2502.01697, Feb 2025: a base model drafts for diversity (pairwise cosine 0.313 vs 0.421 for instruct), then an instruct model refines.
   - Mapping: the base model plans; Claude only checks support.

4. **Pyramid method and atypical combinations.**
   - Nenkova and Passonneau, aclanthology.org/N04-1019, 2004: weight each content unit by how many independent writers include it.
   - Uzzi et al., Science 2013: high-impact papers pair a conventional core with an atypical tail.
   - Mapping: a fact's weight across several AI drafts on one topic is a typicality score. Test whether human plans carry a low-weight tail that AI plans lack.

5. **Deception detection.**
   - Verifiability approach (Nahari, Vrij, Fisher 2014): liars avoid details that can be checked; counting them classified 79% of statements. An independent replication found a smaller effect (d 0.49 vs 1.14).
   - Ott et al., arxiv.org/abs/1107.4557, ACL 2011: fake reviews read like imaginative writing.
   - Mapping: an AI draft is written from a general script rather than a source. "Verifiable details per claim" fits our names and numbers gap.

6. **Russell, Karpinska, Iyyer**, arxiv.org/abs/2501.15654, ACL 2025.
   - Expert cues: vocabulary 53.1%, sentence structure 35.9%, "safe" originality 23.7%, quotes 22.3%; their guide also flags recap conclusions.
   - o1-pro was told to add specific people, places and metrics and to skip summary conclusions. Pangram's humanizer model still caught 96.7% (n = 30).
   - Mapping: asking for specifics without a new source fails.

7. **Discourse motifs.** Kim et al., arxiv.org/abs/2402.10586, ACL 2024.
   - In Rhetorical Structure Theory trees, machine text has more Elaboration and Background relations; human text has more Joint relations and more variety.
   - Motif features add 0.08 F1 out of domain but only 0.02 under paraphrase. Paraphrase changes low-level segments more than the top of the tree.
   - Mapping: the top-level plan survives rewording, as in B5.

8. **Distribution matching.**
   - Generation with Distributional Control, Khalifa et al., arxiv.org/abs/2012.11635, ICLR 2021: meet target statistics while staying close to the base model.
   - Discriminator Rejection Sampling (DRS), Azadi et al., arxiv.org/abs/1810.06758, ICLR 2019: accept each sample with a probability set by the calibrated density ratio D/(1-D).
   - Mapping: use a plan-level human-vs-AI classifier as a sampling prior that matches human statistics, never one to maximize. Detector-proxy loops already fail on Pangram 4.x.

9. **Survey science.**
   - Bisbee et al., Political Analysis 2024: ChatGPT matches survey averages but with less variance.
   - Anthology, arxiv.org/abs/2407.06576, NeurIPS 2024: conditioning on concrete backstories improves the match to human answer distributions by up to 18%.
   - Mapping: aim for one draw from the human distribution, not its average.

**Findings that cut against our assumptions**
- **Numbers:** base models put more numbers into news leads than humans do (Muñoz-Ortiz et al., AI Review, Aug 2024). Our base writer will therefore push numbers in, so keep the guard.
- **Hedging:** studies that count hedge words find large language models hedge less than humans (Jiang and Hyland; arxiv.org/abs/2505.09662). Our 18% vs 12% is probably generic claims rather than hedge words, so count the two separately.

**2. Ranked experiments**

1. **E1. Plan typicality audit (no Pangram scans).**
   - Hypothesis: AI fact lists are more typical than human ones, and plan features alone can separate them.
   - Manipulation:
     - Score each fact by its weight across 5 extra AI drafts per topic, and by OLMo-2-13B base log-likelihood given the topic.
     - Add counts: facts per 100 words, generic claims, numbers, names, verifiable details.
     - Fit a logistic regression with topics held out, then test it on the existing B4 to B7 Pangram labels (calibration).
   - Control: a counts-only model and shuffled labels.
   - What changes the plan: if typicality wins, it becomes the prior for E3 to E5. If nothing predicts the Pangram labels, the signal is where the facts came from, so go to E2.

2. **E2. Human-source dose-response (20 scans).**
   - Hypothesis: the Human rate rises with the share of facts from a human source, with a threshold.
   - Manipulation: 5 topics at 0, 33, 67 and 100% of facts taken from the human article (standing in for a retrieved source), the rest from the draft. Fact count, writer, seed and length are held the same.
   - Control: the 0% and 100% cells replicate B5.
   - What changes the plan: if 33% flips most texts, build a retrieve-and-cite step where the claim check accepts the cited source. If 67% or more is needed, the user's-own-notes route stays the product.

3. **E3. Plan-level DRS (20 scans).**
   - Hypothesis: sampling plans by calibrated density ratio beats B6's specific-fact rule.
   - Manipulation: 64 candidate plans per draft (random subsets plus B7 pool plans). Pick plans for 10 drafts by DRS and for 10 by taking the top-scoring plan.
   - Control: B6 cell F on the same drafts (3 of 8 Human).
   - What changes the plan: 7 of 10 or better from DRS means the prior goes into the pipeline. If top-scoring does worse than DRS, maximizing the classifier overfits. A tie means picking subsets of the draft's facts has hit its ceiling.

4. **E4. Borrowed human skeleton (20 scans).**
   - Hypothesis: the order and proportions of paragraph types carry signal apart from which facts are used.
   - Manipulation: Claude tags paragraphs in human articles by type (anecdote, nut graf, data, quote, counterpoint, kicker). Retrieve the nearest skeleton from another topic and slot the draft's facts into it, leaving slots empty rather than inventing.
   - Control: the same facts in the draft's order.
   - What changes the plan: 3 or more extra Human verdicts out of 10 means adding a skeleton-retrieval step. No change means dropping outline work.

5. **E5. Tail plans: VS against base-model planning (20 scans).**
   - Hypothesis: an aligned model's tail plans stay typical; base-model plans do not.
   - Manipulation:
     - 10 drafts use a VS angle from Claude (p < 0.10).
     - 10 use an OLMo base outline written after 3 human outlines (temperature 1.0 and min-p 0.1 on the plan stage only).
     - Unsupported items are dropped in both arms.
   - Control: B6 cell F.
   - What changes the plan: if base planning beats VS, plans must come from a base model, as in B7 and HALO. If both tie B6, where the facts come from is the lever, not plan diversity.

**3. Not verified**
- The figures for Hivemind, Reinhart, Uzzi, the verifiability approach, Bisbee and Anthology come from abstracts or search summaries only.
- Russell et al. tested a Pangram version older than 4.x. None of these methods has been tested against Pangram 4.x, so every mapping above is my inference.
- One study reports fewer named entities in AI-assisted news (arxiv.org/abs/2508.06445), but its units are unstated and its AI labels come from detectors, so I left it out.
