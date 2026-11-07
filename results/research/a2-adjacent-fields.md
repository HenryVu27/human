# Research agent report: a2-adjacent-fields

Written 2026-11-06 by a research subagent for the attempt 2 planning session. Raw report, saved as written.

## Brief given to the agent

Borrow methods from fields that bear on attempt 2's open questions and report what each field actually does (its instruments and results). Fields: (1) stylometry, authorship attribution and verification, obfuscation and imitation; (2) content selection and discourse planning; (3) editing practice and author-in-the-loop capture; (4) human perception of AI text; (5) any field that keeps the draft's information while changing who "chose" it. Read `results/research/r2-adjacent-fields.md` and `results/RESEARCH-2026-11-04-prior-work.md` first and add rather than repeat. Goal behind the goal: Henry's blog should sound like him and be worth reading, with an AI drafting partner; outputs must read Human to Pangram 4.x and careful readers, be better than the draft and add no facts.

Rule passed down: work at expert depth, start from raw data, verify with an external check, report what you could not verify.

## How to read the tags

- [primary, verified]: I fetched the paper's own page (arXiv HTML or the publisher's page) and read the numbers quoted here from its tables or text. The fetch tool summarizes pages with a small model, so a number can still be misread; the ones that matter are flagged for a recheck under "What I could not verify".
- [primary, unverified]: I reached the primary source but only its abstract or listing, so numbers or details come from the abstract or a search summary.
- [secondary]: trade sources, press releases, review sites or my own background knowledge of a classic work. Not checked against the primary source in this session.

Items already covered in r2 (Verbalized Sampling, Spangher et al. 2024, Padmakumar and He, BARE, pyramid method, Kim et al. 2024 Rhetorical Structure Theory motifs, discriminator rejection sampling, Anthology, the verifiability approach) are not repeated except where a new source changes how to read them.

## Bottom line

1. **Content carries a model fingerprint that survives rewording, and only partly survives summarization.** A classifier that names which chat model wrote a text keeps 91.4% accuracy after an external LLM paraphrases it and 58.1% after it summarizes it (chance 20%) (Sun et al., ICML 2025). This is attempt 1's B5 result seen from outside: rewording does not change who chose the content.
2. **Giving the AI the author's thesis is not enough.** In 23,381 LLM essays against 1,487 human ones, 65.3% of human main arguments were unique within a debate against 3.4% for LLMs; 41.0% of human sub-arguments were unique against 9.1%. When the model was given one human writer's main argument, bio and tone, sub-argument uniqueness was 6.8% (Kim, Chang, Pham, Iyyer, "Argument Collapse", arXiv 2606.01736, 2026). The model fills in its own sub-points under the human's thesis. Capture has to reach the sub-argument level.
3. **Human arguments chain; LLM arguments jump to proposals.** Human paragraph transitions are support to support 50.5% of the time against 36.0% for LLMs, and support to proposal 12.3% against 29.4% (same paper). LLM explanations use elaborative connectives for 56 to 66% of discourse markers against 38% for humans (Baloni and Rettinger, WNUT 2026). Both are cheap, measurable plan signatures that attempt 1 never measured.
4. **LLM revision of human text normalizes the features stylometry and naive readers use for "human":** fewer function words, contractions and first-person pronouns, more vocabulary diversity and longer words. Voice-preserving prompts shrink the change but do not reverse it (van Nuenen, arXiv 2604.22142, 2026). Any LLM pass over Henry's own sentences should be expected to cost both voice and Pangram share.
5. **Expert readers and Pangram agree on raw AI text and read different cues.** Five frequent LLM users by majority vote caught 99.3% of AI articles with 0% false positives; Pangram caught 98.0% with 2% false positives. Nonexperts were at chance (56.7% true positives, 51.7% false positives). Experts cite vocabulary in 53.1% of explanations (Russell, Karpinska, Iyyer, ACL 2025). Readers judge mostly words; Pangram judges mostly content. A text can pass one and fail the other, so attempt 2 needs both judges and a measure of their agreement.
6. **Editors and ghostwriters do not choose the author's content; they extract it.** Professional editing of LLM text is 74% replacements, 18% deletions and 8% insertions (Chakrabarty, Laban, Wu, CHI 2025, 18 writers, 8,035 edits). Ghostwriting practice is recorded interviews and transcripts. Memory research supplies the instruments for interviews: the cognitive interview and the Critical Decision Method, plus stimulated recall from the work's own artifacts. These are the fix for B21's failure (Henry could not recall a months-old post).
7. **A human picking from an AI menu is probably still AI choice.** People who co-wrote with an opinionated assistant were about twice as likely to write the assistant's view and shifted their own attitudes, mostly without noticing (Jakesch et al., CHI 2023, n = 1,506). Pangram's mirror labels are an instruct model's plan for a topic. Together these predict that "AI proposes points, Henry picks" will read AI. That is Henry's B21 objection, and it is directly testable.
8. **Kreminski's "dearth of the author" gives a single axis that may unify attempt 1's dose results:** the ratio of authorial intent to output length. B28 could not separate dose from length; intent per output word is exactly dose divided by length. It can be refit on existing Pangram labels at zero scan cost.

## 1. Stylometry, authorship attribution and verification

### 1.1 What separates human and LLM text, 2025 to 2026

**Reinhart, Markey, Laudenbach et al., "Do LLMs write like humans? Variation in grammatical and rhetorical styles", PNAS 122(8), 2025-02-25, arXiv 2410.16107.** [primary, verified]
- Instrument: Biber's 66 lexical, grammatical and rhetorical features on parallel corpora (same prompt, human continuation versus Llama 3 base and instruct variants and GPT-4o).
- Results, GPT-4o against humans: present participial clauses 5.3 times the human rate (paired Cohen's d = 1.38); nominalizations 2.1 times (d = 1.23); "that" clauses as subjects 2.6 times (d = 0.77); phrasal coordination 1.9 times (d = 0.81); agentless passives about half the human rate. Instruction-tuned models in general: participial clauses 2 to 5 times, nominalizations 1.5 to 2 times.
- Llama 3 base models (8B and 70B) use these features at near-human rates.
- Classifier: random forest on Biber features, human versus one specific LLM, 93 to 98% accuracy, holding across corpora; about 75% for Llama base models with lasso.
- What it adds to r2: r2 cited this paper from its abstract; the numbers above are from the paper. The features are the grammar of the assistant register, they are cheap to compute, and base models do not carry them.

**Sun, Yin, Xu, Kolter, Liu, "Idiosyncrasies in Large Language Models", ICML 2025, arXiv 2502.12150.** [primary, verified]
- Instrument: fine-tuned text-embedding classifier naming which of five chat models (ChatGPT, Claude, Grok, Gemini, DeepSeek) wrote a response. Chance 20%.
- Accuracy after transformations (chat models): original 97.1%; formatting removed 95.1%; words shuffled 88.9%; paraphrased by GPT-4o-mini 91.4%; translated to Chinese 91.8%; summarized 58.1%. Letters shuffled 39.1%. With Qwen2.5-7B-Instruct as the rewriter, summary retains 71.5%.
- Reading: word order hardly matters (shuffled words keep 88.9%), rewording hardly matters, and even a summary keeps a large share of the signal. The fingerprint lives in which words and therefore which content the model chose.
- Mapping: independent support for attempt 1's finding 1 (rewording facts changes nothing). Also a ready instrument: a "who chose this content" classifier that sees only a summary or fact list of a text.

**van Nuenen, "Voice Under Revision: Large Language Models and the Normalization of Personal Narrative", arXiv 2604.22142, 2026-04-24.** [primary, unverified: abstract only]
- Design: 300 personal narratives rewritten by three frontier LLMs under three prompts (generic improvement, rewrite only, voice-preserving revision), 13 stylometric markers.
- Results (directions only, no effect sizes on the abstract page): function words, contractions and first-person pronouns fall; vocabulary diversity, word length and punctuation elaboration rise; narration moves from embedded to distanced and from explicit causal reasoning to compressed abstraction. Voice-preserving prompts reduce the size of the change but not its direction. Rewritten texts converge in feature space and become harder to match to their source author.
- Mapping: an LLM "polish" pass on Henry's sentences is an authorship obfuscator pointed at the assistant register.

**Wang et al., "Catch Me If You Can? Not Yet: LLMs Still Struggle to Imitate the Implicit Writing Styles of Everyday Authors", arXiv 2509.14543, Findings of EMNLP 2025.** [primary, verified tables; venue from the ACL Anthology listing]
- Design: 400+ real authors in news (CCAT50), email (Enron), Reddit and blogs; 40,000+ generations per model; 5 writing samples plus a GPT-4.1 content summary, no style instructions; temperature 0. Judges: authorship attribution and verification models (Longformer, ModernBERT), LIWC and WritePrints style models, GPTZero.
- Blogs, 5-shot, authorship verification accuracy: GPT-4o 19.37%, GPT-4o-mini 17.93%, Gemini-2.0-Flash 21.25%, Gemma-3-27B 16.72%, DeepSeek-V3 20.77%, Llama-4-Maverick 17.61%. Real held-out blog text by the same authors: 91.4%.
- Blogs, share judged human by GPTZero: GPT-4o 0.47%, Gemini-2.0-Flash 18.74%, Gemma-3-27B 7.58% (human text 99.5%).
- Prompt variants on blogs (average of three models): baseline 5-shot 9.0% human; length-matched exemplars 27.5% human but style score falls from 82.7 to 68.6; topic-matched exemplars cut verification accuracy to 10.3%; giving the first 50 words of the real text 21.7% human.
- More examples (2 to 10) changed little.
- Mapping: blogs are the hardest domain for imitation, and note the content was fixed by a GPT-4.1 summary of the human text, so this measures prose imitation with human-derived content. Even then, a general detector catches most of it. This agrees with attempt 1's finding 2 (human content written up by Sonnet reads Mixed). It also gives a voice meter: an authorship verification model trained on Henry's own writing separates his text from imitation at roughly 91% against 20%.

**O'Sullivan, "Stylometric comparisons of human versus AI-generated creative writing", Humanities and Social Sciences Communications, 2025.** [secondary]
- Burrows' Delta on most-frequent-word profiles: GPT-3.5, GPT-4 and Llama-70B outputs cluster tightly by model; human texts spread widely.
- Mapping: the spread itself (between-text variance of function-word profiles) is a population-level signature, the stylometric twin of Wenger and Kenett's idea-diversity result in section 2.

**Herbold et al., "A large-scale comparison of human-written versus ChatGPT-generated essays", Scientific Reports 13, 2023.** [primary, unverified]
- ChatGPT essays: fewer discourse and epistemic markers, more nominalizations, greater lexical diversity; rated higher quality by teachers.

**Baloni and Rettinger, "Discourse-Structural Noise in LLM-Generated Explanations", WNUT 2026 (aclanthology.org/2026.wnut-1.5).** [primary, verified from the abstract page]
- Instrument: Penn Discourse Treebank (PDTB) connective analysis over five relation types; 300 ELI5 (Explain Like I'm Five) questions; Llama-3.1-8B, Gemma-2-9B, Mistral-7B against human answers.
- Elaborative connectives are 56 to 66% of discourse markers in model text against 38% in human text (11 to 20 points after sense disambiguation). Causal, contrastive and conditional relations are suppressed. This correlates weakly with semantic similarity (r squared below 0.08), so it is a separate dimension.
- Caveat: small instruct models, not frontier models.

**Information density and surprisal: GPT-who (Venkatraman, Uchendu, Lee, arXiv 2310.06202, Findings of NAACL 2024) and DivEye (Basani and Chen, arXiv 2509.18880, Transactions on Machine Learning Research 2026).** [primary, unverified]
- GPT-who: uniform information density features (mean and variance of token surprisal and related statistics) with logistic regression detect machine text and attribute it among models.
- DivEye: features describing how surprisal changes along the text (the authors report human text has richer variability in lexical and structural unpredictability); up to 33.2% better than other zero-shot detectors, robust to paraphrase per the authors; useful as an auxiliary feature (up to +18.7%).
- Mapping: "surprise" in the requested sense is measurable as surprisal variance under a base model. It is a candidate local feature for the within-rewrite selection problem where attempt 1's judges failed, but nothing shows it tracks Pangram 4.x.

### 1.2 Authorship obfuscation and imitation, and how well they hold up

**StyleRemix, Fisher, Hallinan, Lu, Gordon, Harchaoui, Choi, EMNLP 2024, arXiv 2408.15666.** [primary, verified]
- Instrument: low-rank adapters, one per style axis (sentence length, function-word use, grade level, formality, sarcasm, active or passive voice, writing intent). For each author it picks the axes where the author deviates most from the domain average and pushes them back, weighting adapters by the number of standard deviations.
- Results: on AuthorMix (14 authors: presidential speeches, early-1900s novels, scholarly articles, blogs), human-rated obfuscation 83.0% and overall 69.9% (next best Llama-3-Instruct-8B 66.3%); up to 12% higher drop in authorship-classifier accuracy than baselines; picking axes by deviation beats random picks by about 6%; changing five or more axes cut grammaticality about 16%.
- How it holds up: it defeats a RoBERTa authorship classifier, which reads surface style. No evaluation against AI detectors.

**Gao, Li et al., "When Personalization Tricks Detectors: The Feature-Inversion Trap in Machine-Generated Text Detection", arXiv 2510.12476, ACL 2026 (StyloBench).** [primary, unverified]
- Detectors become unstable on text that imitates a specific author (literary imitation by continued pretraining, blog imitation by few-shot prompting); features that separate human from machine text in general flip direction in personalized text. Reported example (from a secondary summary): Fast-DetectGPT 98.78% area under the curve in general, 8.71% on personalized literary imitation.
- How it holds up against Pangram: not tested. The detectors studied are zero-shot or open ones.

**Liu, Bahja, Kovatchev, Lee, "Capturing Classic Authorial Style in Long-Form Story Generation with GRPO Fine-Tuning", arXiv 2512.05747, CoNLL 2026.** [primary, unverified]
- Instrument: a sentence-transformer trained with authorship verification supervision becomes the reward for Group Relative Policy Optimization on an 8B generator. Average style score 0.893 across Twain, Austen, Dickens, Hardy. No AI-detection results.

**PAN 2025 "Voight-Kampff" generative AI detection task.** [secondary]
- Subtask 1 judges possibly obfuscated texts; subtask 2 classifies human and AI collaboration types. The top team fine-tuned Qwen3-14B and Qwen3-4B. Organizers' later summaries say obfuscated and collaborative texts stay hard. I did not read the overview's numbers.

**What the field's track record says.** Obfuscation succeeds against the classifiers it targets because those classifiers read surface style (function words, sentence length, punctuation). Pangram 4.x is trained on topic mirrors and humanizer outputs and, per attempt 1, reads content. Sun et al. show content survives paraphrase. So surface obfuscation should transfer poorly to Pangram, which is what attempt 1's wording-level pipelines found (0.996 on Pangram 4). Imitation research points the other way for Henry's second goal: an authorship verification model is a working "sounds like Henry" meter, and frontier models imitating blogs fail it badly.

### 1.3 Feature table

| Feature | Human versus LLM direction | Survives paraphrase? | Source |
|---|---|---|---|
| Present participial clauses, nominalizations | LLM 2 to 5 times human | Unknown | Reinhart 2025 |
| Function words, contractions, first person | LLM revision lowers them | Is what revision changes | van Nuenen 2026 |
| Elaborative connective share | LLM 56 to 66%, human 38% | Unknown | Baloni and Rettinger 2026 |
| Discourse and epistemic markers | Fewer in ChatGPT essays | Unknown | Herbold 2023 |
| Surprisal variability | Higher in human text | Yes, per DivEye authors | Basani and Chen 2026 |
| Function-word profile spread across texts | LLM clusters tight | Not tested | O'Sullivan 2025 |
| Model identity from content | 97% to 91% after paraphrase, 58% after summary | Mostly | Sun et al. 2025 |
| Rhetorical Structure Theory top-level relations | More Elaboration and Background in LLM text | Partly (r2) | Kim et al. 2024 |

## 2. Content selection and discourse planning

### 2.1 How LLMs choose and order points

**Kim, Chang, Pham, Iyyer, "Argument Collapse: LLMs Flatten Long-Form Public Debate", arXiv 2606.01736, v1 2026-06-01, v4 2026-09-02.** [primary, verified, first half of the HTML]
- Data: 1,039 human responses from 195 New York Times debates, 448 from 61 Boston Review forums, 23,381 essays from GPT-5.5, Gemini-3.1-Pro-Preview, Claude Opus 4.7, Minimax M2.7, DeepSeek V4 Pro.
- Instruments, worth copying exactly:
  - A judge model (Gemini-3-Flash-Preview) extracts one main argument and the supporting sub-arguments per essay with a Toulmin-style scheme. Author check on 30 human essays: 30 of 30 main arguments right, 134 of 134 sub-arguments present in the text.
  - Pairwise overlap labels within a debate (equivalent, strong overlap, weak overlap, different). Two authors agreed at Cohen's kappa 0.61 on four labels and 0.80 on the binary "substantial overlap"; the judge matched them on 93% of binary labels.
  - Unique rate U_m: expected fraction of arguments with no substantial overlap in a random sample of size m, so groups of different size compare fairly.
  - Paragraph roles (support, proposal and others) and discourse modes (argumentation, narration and others), with transition rates.
- Results:
  - Main arguments unique within a debate: human 65.3%, LLM 3.4%.
  - Sub-arguments unique among essays sharing a main argument: human 41.0%, LLM 9.1%, LLM asked for diverse essays 22.9%.
  - "Position-guided" generation (the model gets one human writer's main argument, bio and tone): sub-argument uniqueness 6.8% for a fixed writer, 18.4% when the writer varies.
  - Diverse prompting recovers about half of human main-argument clusters per model (Claude 50%, Gemini 55%), 73.9% pooling five models; human arguments made by several people are recovered 98.1% of the time, one-off human arguments 67.8%. Only 47.6 to 60.3% of the diversified LLM arguments overlap any human argument at all.
  - Structure: support to support transitions, NYT human 50.5% against LLM 36.0% (Boston Review 54.5% against 29.7%); support to proposal 12.3% against 29.4% (7.2% against 17.7%). Argumentation is 89% of LLM paragraphs under diverse prompting against 71.5% for humans: humans spend more paragraphs narrating or explaining.
  - Qualitative: LLM sub-arguments are generalized frameworks, generic citations and hedged generalities; human ones are specific cases, concrete interventions and direct positions. Human-preference evaluators favor the common arguments and the LLM essays.
- Mapping: this is the strongest new evidence on "who chose the content". Three points matter for attempt 2. The idiosyncratic one-off human points are the ones an LLM cannot recover. Thesis-level human input leaves the sub-arguments typical. And the structural signature (support chains versus jumps to proposals, share of non-argument paragraphs) is measurable with a judge model whose agreement with people has been checked.

**Wenger and Kenett, "Large language models are homogeneously creative", PNAS Nexus 5(3), 2026-03-24.** [primary, verified]
- 102 people against 22 API models on three divergent-thinking tasks. Individual originality is similar or higher for LLMs, but population variability is far lower (Alternative Uses Task 0.459 against 0.699 cosine distance).
- Creative system prompts raised variability only to 0.551. Temperature 2.0 reached the human level (p = 0.19) but most outputs were unusable.
- Mapping: one LLM output can look original; the set of LLM outputs on one topic is narrow. Pangram's mirrors sample exactly that narrow set, so a draft's plan sits inside it.

**Moon, Green, Kushlev, preregistered studies of 2,200 admissions essays (2025).** [secondary]
- Each added human essay contributes more new ideas than each added GPT-4 essay, and the gap widens with more essays; prompt and parameter changes did not close it.

**Inoshita et al., "Does AI Homogenize Student Thinking?", arXiv 2603.21228, 2026-03.** [primary, unverified]
- 6,875 essays in five conditions (human, AI, three human plus AI strategies). "Cohesion architecture lost 70 to 78% of its variance" under AI help, while perspective plurality rose; specific prompts reversed homogenization of argument depth.

**Tian, Huang et al., "Are Large Language Models Capable of Generating Human-Level Narratives?", EMNLP 2024, arXiv 2407.13248.** [primary, unverified]
- 1,638 paired human and GPT-4 movie synopses analyzed for story arcs, turning points, arousal and valence. LLM stories are uniformly positive and lack tension; models under-develop setbacks and climaxes. Feeding explicit discourse features improved diversity, suspense and arousal by over 40%.
- Mapping for technical blogs: the analogue of a setback is the failed attempt, the wrong first guess, the bug. Henry's drafting-time memory is where those live; a draft from a model has few of them.

**Spangher follow-ups.** [secondary] A 2025 KnowledgeNLP workshop paper turns journalist source selection into a retrieval benchmark; NewsAgent (arXiv 2509.00446, 2025) reports that agent journalists adopt perspectives unlike human journalists and do not explore alternatives. I did not open either.

### 2.2 Instruments from natural language generation content planning

- **Question-answering blueprints, Narayan et al., TACL 11, 2023, arXiv 2207.00397.** [primary, unverified] The plan is a sequence of question-answer pairs; generation conditioned on the blueprint is more factual and more controllable than unplanned generation. Mapping: a plan expressed as questions with the author's answers is both a content plan and a provenance record.
- **Classic content selection** (Reiter and Dale's pipeline; Barzilay and Lapata 2005, "collective content selection" learned from human-written documents). [secondary] Content selection is learned by aligning facts in a database to what human writers chose to mention. Mapping: attempt 1's corpus of 900 human articles with AI mirrors is the training set for exactly this: a model of which facts humans keep.
- **STORM, Shao et al., NAACL 2024, arXiv 2402.14207.** [primary, unverified] Perspective-guided question asking builds Wikipedia-style outlines; editors judged them 25% more organized and 10% broader than a baseline, and flagged "source bias transfer" and over-association of unrelated facts. Mapping: a counterexample. Question asking by an LLM still lets the LLM choose the content, and the editors' complaint (associating loosely related facts) is the LLM plan signature.

### 2.3 Measurable signatures of AI content choice, collected

| Signature | Instrument | Source |
|---|---|---|
| Main-argument and sub-argument unique rate against a pool of AI drafts on the same topic | Toulmin extraction plus pairwise overlap judge, U_m | Argument Collapse 2026 |
| Support to support versus support to proposal transitions | Paragraph role tagging | Argument Collapse 2026 |
| Share of non-argument paragraphs (narration, explanation) | Discourse mode tagging | Argument Collapse 2026 |
| Elaborative connective share | PDTB connective sense tagging | Baloni and Rettinger 2026 |
| Elaboration and Background share at the top of the discourse tree | Rhetorical Structure Theory parser | Kim et al. 2024 (r2) |
| Generalized and hedged sub-arguments | Judge or specificity classifier | Argument Collapse 2026; Russell 2025 |
| Few setbacks and turning points | Turning-point tagging | Tian et al. 2024 |
| Narrow spread across outputs on one topic | Pairwise embedding distance | Wenger and Kenett 2026 |
| Fact typicality across several AI drafts | Pyramid weight | r2 |

## 3. Editing practice and author-in-the-loop capture

### 3.1 How editors work on a draft

**Levels of edit (trade sources: Editorial Freelancers Association definitions as reported by editors' blogs).** [secondary]
- Developmental (structural or substantive) editing reads the whole manuscript and returns an editorial letter plus inline comments: what is missing, what to cut, what to move. The author does the rewriting. Line editing works sentence by sentence on the quality of the prose. Copyediting is mechanics and consistency. Boundaries are soft, especially between developmental and line editing.
- Mapping: the developmental editor's output is questions and structural decisions for the author, not new content. That is the division of labor the Pangram evidence asks for: the AI may diagnose and ask; the author supplies the points.

**Chakrabarty, Laban, Wu, "Can AI writing be salvaged? Mitigating Idiosyncrasies and Improving Human-AI Alignment in the Writing Process through Edits", CHI 2025, arXiv 2409.14509.** [primary, verified]
- 18 writers with Master of Fine Arts training edited 1,057 LLM paragraphs (GPT-4o, Claude-3.5-Sonnet, Llama-3.1-70B; literary fiction about 80%, plus travel, food, personal essay and advice writing). The LAMP corpus.
- Seven idiosyncrasies: awkward word choice and phrasing 28% of edits, poor sentence structure 20%, unnecessary or redundant exposition 18%, cliché 17%, purple prose, lack of specificity and detail, tense inconsistency.
- Edit operations: 74% replacements, 18% deletions, 8% insertions; about 70% of non-deletion edits preserved meaning. About 8 edits per 205-word paragraph; low-rated paragraphs needed about 10, top-rated about 2.4.
- Preference: writer-edited above LLM-edited above unedited, significant trend. No model family wrote better than the others.
- Mapping: a professional edit of AI prose is mostly substitution and cutting, with few insertions. "Unnecessary exposition" (18%) is the same thing the Pangram humanization lab called "explanatory aftercare", whose deletion restored Human (prior-work file).

**Chakrabarty, Laban, Wu, "AI-Slop to AI-Polish? Aligning Language Models through Edit-Based Writing Rewards and Test-time Computation", COLM 2025, arXiv 2504.07532.** [primary, unverified]
- Writing Quality Benchmark of 4,729 preference judgments from five datasets; most LLM judges, including reasoning models, score near chance on it; their Writing Quality Reward Model (WQRM), trained on LAMP edit pairs, reaches 74%. Nine experienced writers preferred WQRM-selected outputs 66% of the time (72.2% when the reward gap exceeds 1 point). Code and models: github.com/salesforce/creativity_eval.
- Mapping: attempt 1 never validated quality, and its LLM judge preferred Sonnet over human text 20 of 20. WQRM is an external quality instrument with a published agreement rate with experts. It was trained on creative paragraphs, so its validity on technical blog prose must be checked against Henry's own rankings before use.

### 3.2 How ghostwriters keep an author's voice

[secondary, practitioner blogs and ghostwriting firms; no controlled studies found]
- Start with recorded interviews and transcribe them; keep the audio because rhythm and emphasis are lost in transcripts; read the client's emails, posts and talks; offer two phrasings and note which the client adopts; the client's way of building an argument matters more than surface features.
- The working rule in all of them: the content and its order come from the client's own telling; the ghostwriter's job is selection among the client's material and sentence craft.
- Pangram evidence for the same route: the 4.0 technical report's red team found one bypass, role-played dictated notes, which Pangram dismissed because the model was given more context than it wrote (prior-work file, verified there). One blogger's Pangram tests (Eric Dodds, 2026-08-05, n = 1 per cell) [primary, verified page, anecdotal]: show notes written by GLM from a podcast transcript, unedited, read AI 45%, AI-assisted 55%; the same with a light human edit 53% AI, 47% human; a hand-written version from an AI summary and outline of the transcript read 100% human; Sonnet show notes with a light edit read 100% AI.

### 3.3 Ownership and influence studies (human-computer interaction)

- **Jakesch, Bhat, Buschek, Zalmanson, Naaman, "Co-Writing with Opinionated Language Models Affects Users' Views", CHI 2023.** [primary, unverified; numbers from the Cornell press release] n = 1,506 wrote about social media with an assistant set to argue one side; 500 judges coded the posts. Participants were about twice as likely to write a paragraph agreeing with the assistant and shifted their survey attitudes; most did not notice. The authors call it latent persuasion.
- **Draxler et al., "The AI Ghostwriter Effect", ACM Transactions on Computer-Human Interaction 31(2), 2024.** [primary, unverified] Two studies (n = 30, 96): users do not feel ownership of AI text yet still sign it; more influence over the text raised ownership.
- **Hwang, Liao, Blodgett, Olteanu, Trischler, "It was 80% me, 20% AI", CSCW 2025, arXiv 2411.13032.** [primary, unverified] 19 professional writers and 30 avid readers. Writers locate authenticity in the process of building their own voice; readers could not tell AI-assisted work from solo work.
- **Kreminski, "The Dearth of the Author in AI-Supported Writing", In2Writing workshop 2024, arXiv 2404.10289.** [primary, unverified] Defines the dearth of the author as a small ratio of authorial intent to output length; tools that make decisions for the user shrink it, producing homogenization and weak ownership.
- **Knowledge telling versus knowledge transforming (Bereiter and Scardamalia, 1987).** [secondary] Novices write by retrieving what they know on a topic cue and writing it down in order; experts transform knowledge to fit a goal and reader. An AIED 2025 trial (n = 90) found chat-style assistants pushed students toward passive acceptance (telling) and an integrated tool toward transforming. [secondary] Mapping: walking a draft's facts in order (attempt 1, "brings back its outline") is knowledge telling performed on the AI's knowledge.

### 3.4 Capturing the author's points: instruments from memory and knowledge elicitation

- **Cognitive interview (Fisher and Geiselman).** [secondary for numbers] Mnemonics: reinstate context, report everything, change order, change perspective. Meta-analysis (Köhnken et al. 1999): correct details up, d = 0.87; incorrect details up slightly (d about 0.24 to 0.28, sources disagree); accuracy about 85% against 82%. Memon, Meissner and Fraser (2010) replicated the large gain in correct details with a small rise in errors and no rise in confabulation.
- **Critical Decision Method (Klein, Calderwood, MacGregor 1989; Crandall, Klein, Hoffman, "Working Minds" 2006).** [secondary] A retrospective interview about one specific incident in several passes: pick the incident, build a timeline, mark decision points, then probe each (what cues you noticed, what options you weighed, what a novice would have missed, what you expected), then "what if" hypotheticals. Built for experts recalling non-routine events after the fact.
- **Stimulated recall (Gass and Mackey 2000, 2nd edition 2016).** [secondary] The participant reviews a record of their own activity (video, logs, drafts) and reports what they were thinking. The method's literature treats delay as the main validity threat. I could not verify the often-repeated "within 48 hours" guideline.
- **Design rationale capture (IBIS, Issue-Based Information System, Kunz and Rittel 1970; QOC, Questions Options Criteria).** [secondary] Software engineering's long experience: rationale is rarely captured because of the cost of capture, its intrusiveness and the scrutiny it invites; lightweight annotation of existing artifacts (emails, commits) costs less than building a separate representation. Architecture Decision Records are the lightweight form that survived in practice.
- Mapping to B21: Henry failed a free-recall interview months after writing, with AI-chosen questions. The fields above say three things. Ask content-free probes about an incident (Critical Decision Method), not topic questions an AI derived from the draft. Cue memory with the work's own artifacts (stimulated recall from the repo, notebook and evaluation logs; B22 was blocked only because those records are client work). And capture at decision time, in the cheapest form (voice memo, commit message), not afterwards.

## 4. Human perception of AI text

**Russell, Karpinska, Iyyer, "People who frequently use ChatGPT for writing tasks are accurate and robust detectors of AI-generated text", ACL 2025, arXiv 2501.15654.** [primary, verified tables]
- 300 non-fiction articles. Nonexperts: true positive rate 56.7%, false positive rate 51.7% (chance), confidence 4.03 of 5. Experts (frequent LLM users for writing): 92.7% and 4.0%, confidence 4.39.
- Per condition, true positive rate (false positive rate): expert majority vote GPT-4o 100 (0), Claude 100 (0), paraphrased GPT-4o 100 (0), o1-pro 96.7 (0), humanized o1-pro 100 (0), overall 99.3 (0). Pangram overall 98.0 (2.0), humanized o1-pro 90.0 (6.7). GPTZero overall 85.3, humanized 46.7. Binoculars at low false positive rate 40.0 overall.
- Individual experts vary: annotator 3 scored 0% on humanized o1-pro and 16.7% on o1-pro, while the others stayed at 86.7 to 100%. Majority vote is what makes the panel robust.
- Clues in explanations: vocabulary 53.1%, sentence structure 35.9%, grammar and punctuation 24.8%, originality 23.7%, quotes 22.3%, clarity 19.5%. On humanized text, vocabulary mentions fell from 57.1% to 42.3% and confidence dropped; residual clues included titles such as "Dr." and "Prof.". Vocabulary was also cited in 31% of false-positive explanations.
- What this adds to r2: the nonexpert baseline, the spread across experts, and the per-condition table. Five experts by majority vote are about as accurate as Pangram on these conditions, and their cues are mostly lexical while Pangram's are content.

**Jakesch, Hancock, Naaman, "Human heuristics for AI-generated language are flawed", PNAS 120(11), 2023.** [primary, unverified]
- Six experiments, 4,600 participants, AI versus human self-presentations: accuracy near chance. People treat first-person pronouns, contractions and family topics as human cues, and warm tone as human; these heuristics can be exploited to make AI text seem "more human than human".
- Mapping: the cues naive readers use for "human" are the same features LLM revision removes (van Nuenen). Readers who are not frequent LLM users are the wrong panel.

**Milička et al., "Humans can learn to detect AI-generated texts, or at least learn when they can't", arXiv 2505.01877, 2025 (journal DOI with a PLOS ONE prefix).** [primary, unverified]
- 254 Czech speakers, GPT-4o texts across registers, immediate feedback against none. Feedback improved accuracy and calibration; without feedback, errors were most common when participants were most confident; initial beliefs about AI text (rigid style, readability) were wrong.

**Dugan et al., "Real or Fake Text?", AAAI 2023.** [primary, unverified] 21,000+ annotations of where a text switches from human to machine. Skill varies a lot between annotators; with incentives they improve over time.

**Other.** A 2025 study in Advances in Simulation reported 19% overall human accuracy on mixed AI forms (chance level), and a training study reported that training raised detection along with false positives. [secondary]

**Agreement with detectors.** Only Russell et al. compare an expert panel and Pangram on the same texts: both near ceiling on raw AI text, diverging slightly on humanized text (experts 100%, Pangram 90%). I found no study of agreement on texts whose content is human but whose prose is AI, or the reverse, which is the case attempt 2 lives in.

## 5. Keeping the information while changing who chose it

1. **Pangram's own labeling rules** (prior-work file, verified there): a clause with a lexical match to the human source is Human; a semantic-only match is AI-assisted; AI training text must have more output tokens than input tokens, so summaries of human input count as human. Two levers follow: keep the author's own words (lexical match), and make the output shorter than the author's raw material (compression).
2. **As-told-to writing and oral history.** [secondary] The subject talks; the writer selects and orders from the transcript, keeping the subject's phrasing. Under rule 1 this is the route where Pangram's labels point to Human by construction, and it matches the red team's dictated-notes bypass.
3. **Argument mapping (Toulmin, IBIS).** Extract the draft's argument into a map of claims, grounds and warrants (Argument Collapse's extraction is the validated instrument). The author then re-roots it: picks the main claim, deletes sub-arguments he would not make, and adds the ones he would, especially failed attempts and one-off specifics. The draft's information stays available as a menu, but the map records which nodes the author chose and which he added. Caution from Jakesch 2023: a menu persuades, so the author should write his own map first and see the draft's second.
4. **Question-driven planning with author answers** (question-answering blueprints, Narayan 2023; Critical Decision Method probes). The plan is a list of questions with Henry's answers. Henry's B21 objection was that AI-chosen questions keep part of the plan AI's. Content-free incident probes ("what broke first", "what did you expect", "what would a newcomer miss") avoid smuggling the draft's outline back in, unlike questions derived from the draft.
5. **Stimulated recall from artifacts.** Re-derive the structure from the author's own records of the work (commit history, notebook, evaluation logs, chat history with the drafting model), so recall months later has cues. This is the route for back-catalog posts.
6. **Design rationale capture at decision time.** Make capture a byproduct of the work: a two-minute voice memo when a decision is made, or a commit message, rather than a later interview.
7. **What does not work here.** Raising sampling diversity (Wenger and Kenett: usable temperatures do not reach human spread; Argument Collapse: diverse prompting recovers half the human arguments and invents arguments no human made). Diversity is not provenance.

## What I could not verify

- WebFetch summarizes pages with a small model, so even [primary, verified] numbers should be rechecked before they go into a spec. The ones that matter most: Argument Collapse's 3.4% against 65.3%, 6.8% position-guided and the transition rates (I read only the first half of its HTML); Sun et al.'s summarize row (58.1%); Russell's Table 1 false positive rates (the paper's text gives 52.5% and 3.3%, its table 51.7% and 4.0%).
- None of the methods above has been tested against Pangram 4.x except Russell et al. (an older Pangram) and the anecdotal Dodds tests (version unstated). Every mapping to Pangram is my inference.
- Van Nuenen 2026: directions only; no effect sizes on the abstract page.
- Feature-inversion trap: the Fast-DetectGPT 98.78% to 8.71% figure comes from a summary site.
- The cognitive interview effect sizes come from search summaries of the 1999 and 2010 meta-analyses, not the papers; the "within 48 hours" stimulated recall guideline is not verified; the Critical Decision Method's pass structure comes from secondary descriptions.
- Ghostwriting practice comes from practitioner and vendor blogs; I found no controlled study of ghostwriter voice capture. Editorial Freelancers Association definitions were not read on the association's site.
- Moon et al. 2025, O'Sullivan 2025, the AIED 2025 trial, the Advances in Simulation study and the PAN 2025 overview were not opened.
- I found no study of human-AI collaborative technical blog posts specifically, and none of reader-detector agreement on human-content, AI-prose texts.
- Whether Henry has a corpus of his own writing from before he drafted with LLMs, which the authorship verification meter in H9 needs, is unknown to me.

## Implications for attempt 2

Each item: hypothesis, method, measurement, and cost class (R = reanalysis of existing attempt 1 data, no scans; S = needs Pangram scans; P = needs people). Existing data: `results/b38_data.jsonl` has 1,534 Pangram-labelled texts with `origin`, `exp`, `cell` and `ai_share` fields.

**H1. Intent ratio unifies dose and length (Kreminski; field 3). Cost R.**
- Hypothesis: Pangram's verdict on attempt 1 outputs is predicted better by author-sourced content units per 100 output words than by dose and length separately.
- Method: for B9, B26, B28 and B30, count human-sourced facts kept in each output (claim check output) and divide by output words. Fit logistic regression of Human on intent ratio, against dose plus length, compare by Akaike information criterion with topic-clustered errors.
- Measurement: difference in information criterion; the fitted threshold (intent units per 100 words where P(Human) crosses 0.5). If the threshold is reachable for a 2,000-word post, it gives the capture budget: how many of Henry's own points per section a post needs.

**H2. A content-only "who chose this" judge (Sun et al.; fields 1 and 2). Cost R, then S on a reserved set.**
- Hypothesis: a classifier that sees only a fact list or neutral summary of a text separates human-sourced from AI-sourced content as well as Pangram does, and tracks Pangram within rewrites better than attempt 1's surrogates (AUROC 0.54 to 0.67 among AI-sourced texts).
- Method: summarize every labelled text with one fixed model into a neutral fact list; train on `origin` with topics held out; also train on Pangram labels.
- Measurement: AUROC on held-out topics; Spearman with Pangram `ai_share` within the tries of one section (B38). If it beats "copies least from the draft", it becomes the local selection judge allowed by Henry's 2026-11-06 exception.

**H3. Plan signatures predict Pangram beyond copying (Argument Collapse, Baloni and Rettinger; field 2). Cost R.**
- Hypothesis: support to support transition rate, share of non-argument paragraphs, elaborative connective share and sub-argument uniqueness against a pool of five AI drafts per topic each predict `ai_share` after controlling for 8-word copy rate.
- Method: replicate Argument Collapse's extraction and paragraph-role tagging on attempt 1 outputs and on Henry's posts; validate the judge on 30 texts against Henry's own labels (target Cohen's kappa of 0.6 or more on binary labels).
- Measurement: partial Spearman with `ai_share` controlling for copy rate. Features that survive become checks in the pipeline and writer training targets; features that do not are dropped.

**H4. The prose residual is the assistant register (Reinhart, van Nuenen; field 1). Cost R.**
- Hypothesis: among human-sourced texts only, the Mixed verdicts of Sonnet writers (B27 W, B28 S100) against the Human verdicts of the base writer (B26, B28 L) are explained by Biber features (participial clauses, nominalizations), function-word and contraction rates and first-person rate.
- Method: compute Biber features (an open Biber tagger) on the human-sourced subset; logistic regression of Human on features, cross-validated by experiment.
- Measurement: AUROC and the sign of each coefficient. If this explains finding 2 ("prose carries signal too"), the fix is a constrained surface pass on those features, kept separate from content work.

**H5. Thesis-only capture fails; sub-argument capture is needed (Argument Collapse, position-guided result). Cost S.**
- Hypothesis: at a fixed writer and length, Pangram's Human rate rises with the level at which Henry supplies content: thesis only, thesis plus section claims, thesis plus section claims plus his supporting specifics.
- Method: 3 levels on 10 sections or short posts, same local base writer, paired by topic; pre-register the scoring rule and the 150-word rule.
- Measurement: Human rate per level with a paired exact test; the expected pattern is the thesis-only level reading like AI-sourced content.

**H6. Picking from an AI menu is AI choice (Jakesch 2023; Pangram's mirror labels; Henry's B21 objection). Cost S plus Henry's time.**
- Hypothesis: posts built from points Henry picked out of an AI-proposed list read AI at about the rate of AI-chosen posts; posts built from points Henry generated before seeing any list read Human; the B9 result (AI selection over human material reads Human) is the mirror case.
- Method: on 6 to 10 topics, Henry first writes his own point list (blind), then picks from an AI list; same writer for both; record which picked points also appear in his blind list.
- Measurement: Pangram Human rate per arm, paired; pyramid weight of the chosen points against five AI drafts; overlap between picked and blind lists (a direct measure of latent persuasion).

**H7. Drafting-time capture beats months-later interview (cognitive interview, Critical Decision Method, stimulated recall; field 3). Cost P, then S.**
- Hypothesis: a 10 to 15 minute voice memo recorded while Henry drafts, answering content-free incident probes with the repo and notebook open, yields more specific, verifiable, non-typical points than a later interview, and posts built from it read Human.
- Method: for the next 2 or 3 posts Henry drafts, run the protocol (timeline of the work, decision points, what broke, what surprised him, what a newcomer would miss, what he would do differently). For one back-catalog post, run stimulated recall from its artifacts instead.
- Measurement: specifics per minute (numbers, names, verifiable details), the share of memo points absent from five AI drafts on the topic (pyramid weight zero), and Pangram on posts written from the memo. Compare against B21 (no usable recall).

**H8. Lexical carry-over from the author's transcript predicts Human (Pangram's lexical-match rule; as-told-to practice). Cost S.**
- Hypothesis: the 8-word copy rate that predicted AI share when copying from the AI draft (Spearman 0.70) predicts Human share when copying from Henry's own transcript.
- Method: from one memo transcript, produce versions that keep 10%, 30% and 50% of the transcript's 8-gram runs (writer instructed to keep his phrasing), same length.
- Measurement: Spearman between transcript copy rate and `ai_share`; quality via WQRM and Henry's read, since transcript prose can be worse writing.

**H9. A voice meter for "sounds like Henry" (Wang et al. 2025, StyleRemix; field 1). Cost R if a corpus exists.**
- Hypothesis: an authorship verification model trained on Henry's own writing (ideally pre-LLM) scores his human posts well above Claude imitations, and Henry's preferences between versions track its score.
- Method: fine-tune or use an off-the-shelf authorship verification embedding on Henry's corpus against same-genre blogs; score attempt 1 outputs and his posts.
- Measurement: verification accuracy (published gap: about 91% for real text against 17 to 21% for imitation on blogs); Spearman with Henry's pairwise preferences. This is a second objective, alongside Pangram, that matches the goal behind the goal.

**H10. LLM polish of Henry's sentences raises the AI share (van Nuenen; field 1). Cost S, small.**
- Hypothesis: a "light edit, preserve my voice" Sonnet pass over Henry-written paragraphs that read Human lowers function-word, contraction and first-person rates and raises Pangram's share.
- Method: 10 Henry paragraphs or sections, original against edited, paired.
- Measurement: feature deltas and `ai_share` deltas. If confirmed, the tool's rule is that the model may flag and suggest but never rewrites the author's sentences.

**H11. Quality needs an external instrument; edits should look like LAMP (Chakrabarty 2025; field 3). Cost P, small.**
- Hypothesis: WQRM agrees with Henry on technical prose at least as well as it agrees with writers on creative prose (about 66%); an editing pass restricted to replacements and deletions in the seven LAMP categories improves WQRM score without changing the Pangram verdict.
- Method: Henry ranks 20 pairs blind; compare with WQRM; then run the restricted edit pass on attempt 1 outputs.
- Measurement: agreement rate with Henry; WQRM delta; Pangram verdict change (expected near zero, which separates quality work from detection work).

**H12. A reader panel of frequent LLM users, with measured agreement with Pangram (Russell 2025, Milička 2025; field 4). Cost P.**
- Hypothesis: a 5-person majority vote of daily LLM writers agrees with Pangram on pure AI and pure human texts, and disagrees in a predictable direction on attempt 2's hybrid texts: it passes AI-planned texts with clean vocabulary that Pangram fails, and fails human-planned texts with assistant vocabulary that Pangram passes.
- Method: 40 texts (20 attempt 2 outputs, 10 Henry human posts, 10 raw drafts), short feedback training round first (Milička), cue explanations coded with Russell's categories.
- Measurement: per-reader true and false positive rates, majority vote, Cohen's kappa with Pangram, and the disagreement cells. This replaces the spec's single 60% accuracy threshold with a measured relation between the two judges.

**H13. Surprisal variability as a cheap local feature (DivEye, GPT-who; field 1). Cost R.**
- Hypothesis: variance and first and second differences of token surprisal under OLMo-2-13B base track `ai_share` within rewrites.
- Method: compute on B36 and B38 texts on the PC.
- Measurement: within-section Spearman with `ai_share`, compared with the copy-rate baseline. Low cost; worth running because attempt 1 had no local judge that worked within rewrites.

**Outcome-level reading.** Taken together, the fields describe a tool shaped like a ghostwriter rather than a humanizer. Capture the author at drafting time with incident probes and his own artifacts. Build the plan as his own argument map, with the AI draft as a reference he consults after writing his own list. Write from his transcript with a base-model writer, keeping his phrasing. Let the AI only flag and cut. Judge the result three ways: Pangram for provenance, a voice meter for "sounds like Henry", and WQRM plus a panel of frequent LLM users for quality and human reading. H1 to H4, H9 and H13 cost no scans and can run first to decide which of the scanned tests are worth their credits.

## Sources

- Reinhart et al., PNAS 2025: https://arxiv.org/html/2410.16107v2
- Sun et al., ICML 2025: https://arxiv.org/html/2502.12150v2
- van Nuenen 2026: https://arxiv.org/abs/2604.22142
- Wang et al., Findings of EMNLP 2025: https://arxiv.org/html/2509.14543v1
- O'Sullivan 2025: https://research.ucc.ie/en/publications/stylometric-comparisons-of-human-versus-ai-generated-creative-wri/
- Herbold et al. 2023: https://arxiv.org/abs/2304.14276
- Baloni and Rettinger, WNUT 2026: https://aclanthology.org/2026.wnut-1.5/
- GPT-who: https://arxiv.org/abs/2310.06202 ; DivEye: https://arxiv.org/abs/2509.18880
- StyleRemix: https://arxiv.org/abs/2408.15666
- Feature-inversion trap: https://arxiv.org/abs/2510.12476
- GRPO authorial style: https://arxiv.org/abs/2512.05747
- PAN 2025: https://pan.webis.de/clef25/pan25-web/generated-content-analysis.html
- Argument Collapse: https://arxiv.org/abs/2606.01736
- Wenger and Kenett, PNAS Nexus 2026: https://academic.oup.com/pnasnexus/article/5/3/pgag042/8529001
- Inoshita et al. 2026: https://arxiv.org/abs/2603.21228
- Tian et al., EMNLP 2024: https://arxiv.org/abs/2407.13248
- Narayan et al., TACL 2023: https://arxiv.org/abs/2207.00397
- STORM: https://arxiv.org/abs/2402.14207
- NewsAgent: https://arxiv.org/abs/2509.00446
- Chakrabarty et al., CHI 2025: https://arxiv.org/html/2409.14509v5
- WQRM, COLM 2025: https://arxiv.org/abs/2504.07532
- Jakesch et al., CHI 2023: https://arxiv.org/abs/2302.00560
- Draxler et al., TOCHI 2024: https://arxiv.org/abs/2303.03283
- Hwang et al., CSCW 2025: https://arxiv.org/abs/2411.13032
- Kreminski 2024: https://arxiv.org/abs/2404.10289
- Russell et al., ACL 2025: https://arxiv.org/html/2501.15654v2
- Jakesch et al., PNAS 2023: https://arxiv.org/abs/2206.07271
- Milička et al. 2025: https://arxiv.org/abs/2505.01877
- Dugan et al., AAAI 2023: https://arxiv.org/abs/2212.12672
- Eric Dodds Pangram tests, 2026-08-05: https://ericdodds.com/blog/testing-pangram-ai-detection-on-substack
- Cognitive interview meta-analyses: https://researchportal.port.ac.uk/en/publications/the-cognitive-interview-a-meta-analysis/ (Köhnken et al. 1999); https://repository.royalholloway.ac.uk/items/2f9938b0-c01b-7310-9ec8-e0aee92c9d17/2 (Memon et al. 2010, not opened)
- Critical Decision Method: https://www.gary-klein.com/cdm
- Ghostwriting practice (practitioner sources): https://www.lifebookmemoirs.com/en-gb/when-ghostwriters-hear-voices/ ; https://www.writeraccess.com/blog/nailing-the-ghostwriting-interview/
