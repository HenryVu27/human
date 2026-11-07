# Humanizer, attempt 2: design

Written 2026-11-06, 18:30 to about 22:00 CST, by the attempt-2 planning session. Status: **proposal for Henry.
Nothing here that costs money or Pangram credits runs before his review.** Revised once after an outside numbers
check and a red team (section 15).

Inputs:
- `docs/attempt-1-closeout.md`, the notebook, report sections 30 to 39, and both earlier specs.
- Five research reports: `results/research/a2-pangram.md`, `a2-literature.md`, `a2-base-models.md`,
  `a2-adjacent-fields.md` and `a2-measurement.md`.
- Two reviews of this design: `results/research/a2-judge-design-numbers.md` and `a2-redteam-design.md`.
- A recheck of attempt 1's load-bearing claims from raw files: `experiments/a2_rechecks.py`, output
  `results/a2_rechecks.json`.

## 0. Summary

**Where attempt 1 left the problem.**
- A whole post reads Human only when under about 10% of its words are flagged.
- Attempt 1's best rewriter left whole posts by unseen writers at an AI share of about 0.38.
- It suggested several levers but separated none of them:
  - who chose the content;
  - who wrote the words;
  - how much the rewrite copies from the AI draft;
  - how many tries you pick from.

**What the new research changes.**
1. **Pangram mainly reads who wrote the words.** IdeaLens (2026-10, checked) shows Pangram 4 flags 92% of text an
   LLM writes from a detailed human plan. Every word in the output must come from a writer that reads human, such as
   a base model, or from Henry. Claude cannot be the final writer, even as an "editor".
2. **Copying from the draft is not a general signal.** On commercial humanizers, by the literature agent's recount,
   it has no relation to Pangram's share. In Henry's own rewrites the B30 rewriter copies about half his original
   wording, and 10 of 11 such sections still read lower (B37). Inside attempt 1's rewriter it is a strong
   correlate (0.63 within a section), but whether it causes the share is open.
3. **Pangram's API may already be paid for and is finer-grained.** The pricing page (checked) lists $200 of API
   credits a month on Professional. The API returns sentence-aligned segments with offsets, so one whole-post scan
   gives per-section shares.
4. **There is a public baseline to beat.** Smaug-Humanizer (checked) is a gemma-4-12B base rewriter with a
   detector-free training recipe. Its only Pangram evidence is three examples.
5. **Rewriter v2 is cheaper than thought:** $10 to $25 of Modal against attempt 1's $40 to $55.
6. **Pangram's 4.1 model card puts Markdown, code and math-heavy text out of scope.**

**The program in one paragraph.** Phase 1 starts with the product itself: a pilot on Henry's next real post (P1),
including a cell he writes with no Claude words, which sets the bar for everything else. Beside it, two lab
experiments, each changing one lever on the same documents:
- **A1, content:** all of a writer's notes against half, at full length on unseen writers, with Smaug-Humanizer as an
  outside baseline.
- **A2-N, copying:** two strengths of a copy penalty at decoding.

Phase 1 also builds the instruments attempt 1 lacked:
- a Pangram API test;
- canaries for drift;
- an audited faithfulness check;
- Henry's blind quality read;
- one free reanalysis: does an open judge trained on Pangram labels rank tries within a section?

Gate G1 then chooses phase 2: the notes workflow, rewriter v2, or stop. A final test (A7) runs only if development
data predict it will pass.

**Henry's decisions (section 13).** These block phase 1:
1. Do Pangram Professional credits renew or expire monthly? He can see this on his billing page.
2. One API test call.
3. About 3,500 to 4,500 credits.
4. His next post for the pilot.
5. About 3 hours of blind reading at G1.

The rest are rule questions, all about where Pangram may select, plus his drafts and paid Modal.

## 1. The goal behind the goal

- **Task:** make Henry's Claude-drafted technical posts read human to Pangram 4.x and careful readers, better than the
  draft, adding nothing.
- **Goal behind it:** Henry publishes posts that are his and worth reading, written with Claude as a drafting partner,
  and readers (engineers, hiring managers) and the detectors they use do not discount them.
- **What follows from that:**
  1. **Test the product first, and cheaply.** The question that matters is what workflow gives Henry posts that read
     as his, at what cost in his time. P1 tests that on his next post for about 300 credits. The lab experiments
     explain why it works or fails, and build the parts.
  2. **Henry writing the post himself is the reference.** Human posts read Human 10 of 10 at full length (B34). Every
     tool has to beat that on Henry's time per post, or it is not worth having.
  3. **"Reads Human" is necessary, not sufficient.** The bandits rewrite read Human at 0.08 and is not publishable.
     Henry measures quality; no LLM judge can measure "better than the draft" (`a2-measurement.md`).
  4. **The goal moves.** Pangram can change the model behind its `pangram-4` name without notice, and it is asking for
     evaluations on technical writing, math and code. A genre gap is a gap Pangram is likely to close, not a lever.
     The durable lever is making the post genuinely more Henry's: his content, in a human register.

## 2. Attempt 1's claims, rechecked from raw files

Recomputed in `experiments/a2_rechecks.py` (`results/a2_rechecks.json`). The outside judge re-ran the script and
recomputed the numbers with its own code (`a2-judge-design-numbers.md`).

| Claim | Recheck | New evidence | Status |
|---|---|---|---|
| B36: whole posts by unseen writers read Human 1 of 32 (mean share 0.376); first 300 words 11 of 32 | Exact | Smaug's card: long texts fail more | Confirmed |
| B37: AI share equals the share of words flagged; Human under 10% | Largest gap between block share and AI share 0.02 | Pangram's docs: final segments are sentence-aligned, at least about 2 sentences, smoothed across 512-token windows at stride 256; Human needs under 10% of characters flagged | Confirmed for one contiguous block of 88 to 248 words in 2 posts. A 1-sentence fix inside an AI run will usually take the AI label, so rewrites work on runs of 3 or more sentences |
| B38: copying predicts the share (Spearman 0.70) | 0.699 (n 55). Partial, given length kept and claim support: 0.62. Within a section: 0.63 | Commercial humanizers: no relation (agent's recount, not mine). Henry's sections (B37): rewrites copy a median of about 0.47 of his original wording and still read lower in 10 of 11 | A correlate inside a base-model rewriter's tries, confounded with content kept. Low-copy tries are also shorter and less supported: 5 of 7 under 0.10 copying fail the claim gate (red team). Cause untested |
| New: faithfulness and Human trade off per candidate | Claim support correlates +0.46 with AI share and +0.57 with copying | Summarization research: most apparent faithfulness gains are extra copying | Finding: any pick that maximizes claim support selects copying. Faithfulness is a floor, never a maximized score |
| New: a section-triage rule (keep sections whose rewrite copies more than 30%) | B37: 11 of 12 of Henry's sections copy above 0.30, and 10 of those 11 read lower after rewriting | none | Finding: refuted with data on hand. Triage by copying is dropped |
| B5, B9: AI-sourced facts read AI even from a human-like writer | Not recomputed (passed outside judges) | IdeaLens: human prose from AI plans passes (8%), but its writers added their own specifics. Sun et al.: the content fingerprint survives paraphrase (91.4%). B5: rewording changed nothing; B6: cutting generic facts did no better than random | Stands. The leakage reading is weak, so attempt 2 does not test it (A2-O dropped, section 15) |
| B27, B28: Sonnet writing from human notes reads Mixed | Not recomputed | IdeaLens 92%; commercial instruct humanizers pass 5.8% | Strengthened: no instruct-model words in the final text |
| B30 T100: 19 of 19 Human from all the notes, 82% of length, 94% of claims | Exact | none | Confirmed for seen writers at about 640 words. The Claude judge preferred the human essay 87% of the time. Quality against the draft never measured |
| Pangram is stable enough for paired scans | 8 of 8 same-day rescans within 0.02; 6 of 7 across days, the one change at the 0.80 boundary (`a2-measurement.md`) | Tech report: deterministic decoding; minor versions change silently | Confirmed within a version. Caching by text hash not ruled out (A0) |

## 3. What changed since attempt 1, and what other fields offer

Starred items I checked on their primary pages. Everything else comes from the agents' reports and carries their
evidence tags.

### 3.1 Pangram (`a2-pangram.md`)

- **Versions and drift.** No model after 4.1 (2026-10-19). The `pangram-4` selector can serve a new minor version
  without notice, with no pinning and no changelog. Responses carry a `version` field.
- **What the API returns.** Final segments: non-overlapping, sentence-aligned, with character offsets, label, score,
  `class_probabilities` (new in 4.1) and a humanizer score. Internal windows (512 tokens, stride 256) are never
  returned. A blank line ends a sentence, so headings, list items and code lines are their own sentences.
- **Access.** \*Professional lists "$200 of API credits monthly" (pricing page, checked 2026-11-06). That is about
  4,000 to 5,000 hundred-word units a month. A July help article contradicts it. Untested.
- **Out of scope.** The 4.1 model card lists Markdown, code, technical manuals and math-heavy text. Opus 5.5 and GPT-6
  prose written with a whole paper as context was flagged only 21 to 25% of the time (arXiv 2610.21062).
- **Research grants.** Pangram offers research credit grants for evaluations in this area. Taking one discloses the
  project.
- **No independent public pass of 4.1.** The only one with per-sample data is the vendor's own (StealthGPT, 41 of 50
  essays under 10%). Only 26 of those were free of fact errors by its own checker, and its outputs are withheld.

### 3.2 Humanization and detection (`a2-literature.md`)

- **\*IdeaLens (arXiv 2610.06778).** Pangram 4 flags 92% of LLM text written from increasingly detailed human plans,
  and 8% of human stories written from AI plans.
- **AI Humanizer Benchmark (AIHB).** By the agent's recount: commercial humanizers pass 19 of 330 (5.8%). Copying has
  no relation to the share. A fact audit (arXiv 2611.00359) found commercial tools change facts in 35 to 65% of
  documents.
- **\*Smaug-Humanizer (2026-10-26).**
  - **Recipe:** gemma-4-12B base, LoRA supervised fine-tuning (SFT) on 3,676 filtered reverse pairs, then 200 steps
    of group relative policy optimization (GRPO). The reward is embedding similarity, with five deterministic gates
    and no detector.
  - **Unit:** about 500 words per call.
  - **Its own caveat:** "Pangram still flags some rewrites, more often for long texts".
- **Open judges distilled from Pangram 3.3.2 labels** (ProseLens, ProseLens-ModernBERT-L). Candidates for the local
  judge, once checked on the project's 4.x labels (Z5).
- **Detector-guided RL since late May.** Tested only on open detectors; gains come from damaged prose or do not carry
  over. Not pursued.
- **Batch homogeneity.** Some detectors catch a pipeline by how alike its outputs are. A risk if Henry publishes many
  posts through one rewriter.

### 3.3 Base models and training (`a2-base-models.md`)

- **Shortlist:**
  1. gemma-4-12B (base, Apache 2.0, 256K context);
  2. Olmo-3-7B (open data);
  3. Ministral-3-14B;
  4. Granite-4.1-8B;
  5. Qwen3.5-9B.

  OLMo-2-13B stays the anchor.
- **PC memory:** a 12 to 14B model fits the 16 GB card at 8K tokens only with offload.
- **PC generation** runs at 7.5 tokens a second, the real bottleneck there. vLLM under WSL2 or llama.cpp should be
  much faster; unmeasured.
- **Copy penalties:**
  - compare arms at matched copy rates;
  - hard bans get dodged with near-copies, so prefer a soft normalized penalty;
  - exempt code, LaTeX, names and numbers;
  - ORPO (odds ratio preference optimization) with the draft as the rejected text is free.
- **Training cost:** SFT about $8.50 on an H100 or 4 to 8 PC hours. Generation of 400 posts at 4 tries about $4.90.
  These are estimates; a calibration run costs under $1.

### 3.4 Adjacent fields (`a2-adjacent-fields.md`)

- **Content fingerprints survive paraphrase** (Sun et al., ICML 2025: 91.4%).
- **Argument Collapse (2026).** Given one writer's main argument, bio and tone, an LLM's sub-arguments are 6.8%
  unique, against 41.0% for humans. Henry's notes must reach his sub-arguments, not only his thesis.
- **Expert readers.** Five frequent LLM users voting by majority caught 99.3% of AI articles. They cite vocabulary,
  while Pangram reads content.
- **Recall methods** for capturing an author's points: the cognitive interview, the Critical Decision Method, and
  stimulated recall from the author's own repo and logs.
- These numbers were read through a summarizing page tool. They inform P1's design but enter no decision rule.

### 3.5 Measurement (`a2-measurement.md`)

- **Outcomes:** paired AI share in development; the Human rate only at the final test.
- **Unit:** the post, not the section (intraclass correlation about 0.25).
- **Final test:** "at least 50% Human" needs 32 of 50 (86% power at a true 0.70).
- **Quality:** no LLM judge measures "better than the draft". Henry's blind forced choice is the instrument.
- **Faithfulness checkers** reach about 75 to 80% balanced accuracy, so audit them first.

## 4. The arithmetic of the target

Flagged words = sum over sections of (words x the share of that section flagged). A post reads Human under about
10%.

| Lever | Evidence | Status |
|---|---|---|
| **Who writes the words** | B10, B27, IdeaLens, AIHB | Settled: base model or Henry, never Claude in the final text |
| **What the writer works from** (who chose the content) | B5, B9, B28; whole-paper result | Untested at full length on unseen writers: A1 |
| **Per-section prose** of the rewriter on unseen writers | B36: 0.29 to 0.38 per section | The gap rewriter v2 would attack (A4) |
| **Copying** inside the rewriter | Correlate 0.63 within sections, confounded with content kept | Cause untested: A2-N |
| **Selection** among tries | Gated oracle 0.213 at k = 4 | Only matters if a judge exists (Z5) or Henry lets Pangram choose in his own use (decision 6) |
| **Genre artifacts** | Math as LaTeX added 0.17 (B38) | Handled by scoring prose only; probe folded into P1 |

## 5. Candidate routes

| Route | For | Against | In attempt 2 |
|---|---|---|---|
| **R0. Henry writes; Claude comments only** | B34: human posts read Human 10 of 10 at full length | Henry's time, which the other routes are meant to save | **Reference cell in P1** |
| **R1. Henry's notes at drafting time, written up by a base-model writer** (or a Claude draft from his notes, then the rewriter) | B30 T100 19 of 19; B26 11 of 13; work-humanizer 4 of 4; whole-paper context 21 to 25% flagged; B21: capture must happen while drafting | Untested at full length; Henry's time; capture must reach sub-arguments; the notes-first writer kept 28% of length in one pass (B37) | **P1 cells; A1** for the full-length lab test |
| **R2. Rewriter v2:** many writers, long context, filtered reverse pairs, copy penalty only if A2-N is causal, optionally Smaug's detector-free RL stage | Rewriting moved every B36 post (0.81 to 0.38); a public recipe exists; $10 to $25 | Developed blind; long context closes about 0.09 of the gap; unseen-author generalization needed millions of authors in TinyStyler | **A4**, at G1 |
| **R2b. Smaug-Humanizer off the shelf** | Free; base model; Apache 2.0 | 500-word unit; three examples as evidence | **Baseline cell in A1** |
| **R3. Keep Henry's own sections verbatim; rewrite only the Claude-written ones** | Pangram adds up flagged words; Henry knows which sections he wrote, so no detector selects | He may have written few whole sections | **P1**, by Henry's own marking |
| **R4. Ground the writing in Henry's primary sources** (papers, docs, code) | B24 10 of 10 with cited human sources; whole-paper result | B24 copied 21% from sources | Phase 2 option if R1 costs Henry too much |
| **R5. Base-model content re-planning** (B7, B14, HALO) | B14 13 of 20 | Keeps about 40% of the content | Not pursued |
| **R6. Selection with a within-section judge** | Seeds differ widely | J1 equalled the free least-copying rule; gated oracle at k = 4 is 0.213 | **Z5** checks an open judge for free; A2-K only if Z5 passes or Henry allows Pangram selection in his use |
| **R7. Outline abstraction** (IdeaLens-style outlines instead of fact lists) | IdeaLens's 8% | B5 rewording did nothing; B6; Sun et al.; IdeaLens's writers added specifics | Not pursued (section 15) |
| Detector-guided RL, commercial humanizers, agent loops on Pangram | none on Pangram 4.x | No transfer, damaged prose, fact changes | Not pursued |

### Untested cells from closeout section 5

| Cell | In attempt 2 |
|---|---|
| All the notes at full length, unseen writers | A1 primary |
| Notes-first writer section by section | A1 cell L, scanned if it passes the gates; P1 |
| Gate 2b | A4, at G1 |
| A judge that ranks tries within a section | Z5 (free); A2-K conditional |
| Pangram's window size and per-window behaviour | Documented (512-token windows; segments of 2 or more sentences); A0 reads segments if the API works |
| Henry's genre | Scoring form fixed to prose only; P1 scans his post three ways |
| Quality | Protocol Q at G1, before A7, and at A7 |
| Author at drafting time | P1 |
| Other generators | Not funded (needs API keys); stated as a limit |
| Spec's held-out drafts h1, h2 | Retired: FineWeb explainers, not blogs |
| Pangram API | A0 |
| Drift | A0 canaries every session |

## 6. Experiments

### 6.0 Method rules

**Carried over from attempt 1:**
- One variable per comparison.
- Selection, exclusion and decision rules in the script docstring, committed before any scan; amendments carry the time
  from `date`.
- Blinded, shuffled scans.
- Raw transcripts saved; a notebook row and a credit-ledger row.

**New:**
- **Analysis.** Primary outcome is the paired whole-post AI share (Wilcoxon signed-rank by post; post-clustered
  bootstrap intervals). McNemar on the label is secondary. The analysis unit is the post.
- **Holm across the contrasts G1 acts on:** A1 primary, A1 S50 and A2-N.
- **Scoring form.** Reader-visible prose, Markdown markers stripped, code blocks removed, display math replaced by a
  short placeholder. Fixed in A0, logged with every scan; full-page numbers are reported beside it for Henry's posts.
- **Cross-session comparisons** (amendment to attempt 1's same-day rule). Pangram decodes deterministically within a
  version, and same-day rescans matched within 0.02. So a scan from an earlier session may be compared with a new one
  only if every canary in both sessions returned identical output. Otherwise the earlier arm is rescanned.
- **Pinned models.** Claude calls use a full model ID, not the `sonnet` alias, and log the resolved model. Cached
  calls from attempt 1 are reused only for texts generated in attempt 1.
- **Pangram's role, stated plainly.** In development, Pangram's verdicts decide between routes at G1, as attempt 1's
  gates did. They never choose a prompt, weight, checkpoint or pick within a route. The only held-out claim is A7.
  Henry ratifies this (decision 7).

### 6.1 A0: instruments (free except about 1 credit and the canaries)

- **API test** (Henry's yes): `GET /models` and one 100-word scan. This tells whether the $200 credit is live, which
  version is served, and whether segments and `class_probabilities` come back. If it works, the bulk API replaces the
  dashboard.
- **Canaries every session:**
  - **The set:** 5 frozen texts: a 300-word human post, a full human post, a B36 rewrite near the line (0.09), a Sonnet
    post, and a B37 splice at 9.5%. Plus a sixth, made fresh each session from the human post by changing one word,
    to detect caching.
  - **Cost:** about 120 credits a session.
  - **The rule:** any change in output on an unchanged text means a new model or settings. Comparisons do not cross
    that boundary, and arms are rescanned.
- **Scan harness `humanizer.eval.scan`:** blinding key committed first, then upload or API, transcript parse, shares,
  segments mapped to sections, and the ledger row.
- **Planted-error audit** of the faithfulness checks:
  - **Design:** 10 error types x 30 outputs plus 60 clean controls.
  - **Bars, deterministic types** (new number, name, date, code line, quote, non-English run, placeholder math): at
    least 29 of 30 caught.
  - **Bars, semantic types** (a wrong claim, new framing, a broken sentence): recall reported with its lower bound,
    bar 0.70.
  - **Gate threshold:** the sentence-level gate is set from the false-flag rate on the clean controls.
  - **No open-ended loop:** one fix round, then the measured recall is stated with every result.
  - **Cost:** about 400 to 700 Claude calls.

### 6.2 P1: the product pilot on Henry's next post (phase 1, first)

- **Question.** Which drafting workflow gives Henry a post that reads human, reads as his, and costs him the least
  time?
- **Precondition:** Henry picks the post and screens every input. His notes and sources go to Claude and Pangram, so
  nothing client-related goes in.
- **Cells, one post, written in this order:**

  | Cell | What |
  |---|---|
  | **H** | Henry writes his own notes per section: points, sub-arguments, examples, in his words, using a short recall checklist. Timed |
  | **C0** | Claude's draft as he drafts today (topic and sources, no notes) |
  | **CN** | Claude's draft from his notes |
  | **CNR** | B30's rewriter on CN, C1 pick |
  | **LN** | The notes-first voice writer section by section from his notes |
  | **R0** | Henry writes the post himself from his notes, with Claude allowed to comment but not to write. Timed. Optional: he decides after seeing the others |

  Sections Henry marks as his own are kept verbatim in CNR and LN (R3).
- **Measures:**
  - whole-post and per-section Pangram share in the scoring form, plus the full page with math and code for C0 and the
    best cell;
  - his blind read of the cells' sections against C0's;
  - his time per cell;
  - content kept against C0;
  - the faithfulness gates.
- **What it can show.** n = 1 post, so a feasibility result, not a test. Does any workflow other than writing it
  himself reach under 0.10 at a time cost he accepts? It is the first evidence on his genre, his drafting conditions
  and his real notes. A1 cannot provide those: A1's notes are 76 Sonnet extractions from a finished post, far denser
  than an author's.
- **Cost:** about 250 to 350 credits (5 or 6 versions of a 2,000 to 3,000-word post, plus full-page scans); Modal about
  $1; Henry's notes, reading and optionally writing time.

### 6.3 A1: does full human content choice rescue whole posts on unseen writers?

- **Question.** With all of a writer's notes, does the rewriter read Human at full length on unseen writers? B36 mixed
  content choice with prose transfer; this separates them. It is an upper bound for R1: the notes are far denser than
  an author's.
- **Documents.** B36's 32 test-A posts (development since B37), paired across cells.
- **Cells:**

  | Cell | What | Scanned |
  |---|---|---|
  | D100 | Sonnet's post from all the reworded notes (B28 pipeline; pinned model ID) | No: it is the input. B28 already measured Sonnet at 100% against 50% notes |
  | C100 | B30's rewriter on D100, section by section, C1 pick | Yes |
  | C50 | B37's C1 texts on the same posts (half the notes), same rewriter and pick | Yes (never scanned before) |
  | S50 | Smaug-Humanizer on D50 (B36's Sonnet post) in 500-word chunks, least-copying pick over 4 seeds under the same gates | Yes |
  | L | Notes-first voice writer section by section from all the notes | Only if it keeps at least 60% of the human post's length and passes the gates |

- **Exclusions and covariates, pre-registered:**
  - texts copying more than 15% from the human post are excluded (B36's rule), in every cell;
  - C1 fallback counts per cell, with a sensitivity analysis without fallback sections;
  - length kept and claim support reported per cell and used as covariates in a sensitivity model.
- **Primary contrast: C100 against C50**, paired AI share.
  - The realistic paired SD for two rewrites of two drafts is 0.15 to 0.20 (red team), so n = 32 detects 0.08 to 0.10
    at 80% power.
  - Expected effect 0.05 to 0.15 (from B30's short-length labels).
- **Bands** (pre-registered, exhaustive):

  | Result | Meaning |
  |---|---|
  | C100 lower by at least 0.10, and Holm-adjusted p under 0.05 | Large content effect: R1 is a strong lever |
  | Lower, significant, by under 0.10 | Small content effect |
  | Not significant, interval excludes a drop of 0.10 | No useful content effect at length |
  | Not significant, interval includes 0.10 | Inconclusive: stated as such, and P1 carries the content question |
  | C100 significantly higher | Content hurts: reported, and R1 is judged on quality only |

  Whole-post C100 Human count and median share are reported beside the band, not used in it.
- **S50 against C50** (secondary, Holm): a band of at least 0.05 lower means phase 2 tries Smaug's weights as R2's
  starting point. Chunk size and model are confounded here, so the band names only the weights, not the recipe.
- **Quality:** 10 C100 against D100 section pairs, and 10 S50 against D50 pairs, go to Henry's G1 read.
- **Cost:** C100 about 460, C50 457, S50 about 460, plus up to 400 for L. Total about 1,380 to 1,780 credits. Modal
  about $6 to $8: C100's 4 seeds, S50 and the claim checks.

### 6.4 A2-N: does copying cause the share?

- **Posts:** calibration posts only. B38's 4 posts (14 sections; 55 of 56 seeds scanned) plus 4 new calibration posts
  (buckets 75 to 79), about 28 sections in 8 posts.
- **Cells:** the same rewriter with a soft normalized copy penalty at two strengths, medium and strong, 2 seeds each.
  Code, LaTeX, names, numbers and the draft's own quotes are exempt. The unconstrained cell C reuses B38's scanned
  seeds where the canaries allow, and gets 2 new seeds on the new posts.
- **Manipulation check:** exact and near copying fall with strength.
- **Gate outcome, pre-registered:** if the strong cell fails the content gates on more than half its sections, that
  is the result. Copying cannot be cut without cutting content, and the copy lever is closed under the content rules.
  The medium cell is then scanned alone.
- **Primary:** dose response of the post-mean share over C, medium and strong, adjusted for length kept and claim
  support. Post-clustered bootstrap.
- **Power:** with a try SD of 0.22 and effective n about 17 posts' worth, the strong-against-C contrast detects about
  0.13 to 0.15. The causal prediction from B38's slope is about 0.18, so a null rules out the predicted effect. It
  cannot rule out a small one.
- **Bands:**
  - **Causal:** strong lower than C by at least 0.10, Holm p under 0.05, and the dose response monotone. The copy
    penalty goes into R2.
  - **Not causal:** the interval excludes 0.10. The penalty is dropped; R2 trains on filtered pairs only.
  - **Inconclusive:** otherwise. The penalty is optional in R2 and must earn its place in A4's development read.
- **Quality:** 10 strong against C pairs go to Henry's G1 read; a penalty can force clumsy paraphrase.
- **Cost:** about 140 texts at about 6 credits, about 840. Modal about $2.

### 6.5 Z5 and A2-K: is selection a lever?

- **Z5 (free; Modal under $1).** Score ProseLens-ModernBERT-L on B38's within-section tries. Compare it with the
  least-copying rule on the same pairs under the gates (the benchmark is recomputed under the gates; the 0.778 often
  quoted is over all pairs).
  - **Bar:** pair accuracy at least 0.10 above least-copying, with a section-clustered interval that excludes 0.
- **A2-K** (8 more seeds for B38's 14 sections, about 670 credits) runs only if Z5 passes, or if Henry allows Pangram
  to pick among tries in his own use (decision 6).
  - **As a judge test:** it measures how much of the oracle's gain the judge keeps at k = 12.
  - **As a product test:** it measures the ceiling of Pangram-picked best-of-12.

### 6.6 Phase 0 reanalyses, kept small

Of the zero-scan hypotheses in `a2-adjacent-fields.md`, only Z1 runs: points from the human notes per output word on
B28 and B30. It needs no new Claude calls and may separate B28's dose from length. Z2 to Z4 need 1,500 to 3,000 Claude
calls on Henry's shared account, so they are deferred until a result depends on them.

### 6.7 Gate G1

G1 is read top to bottom; the first row that matches decides.

| Order | Condition | Phase 2 |
|---|---|---|
| 1 | Henry's G1 read vetoes every candidate route (section 7) | Stop, write up |
| 2 | P1: a notes cell (CNR or LN) reads under 0.10 whole-post, passes the gates and Henry's read, at a time cost he accepts | Productize R1: a drafting tool for his posts, then A7 on his next posts |
| 3 | P1: only R0 (Henry writes) reads under 0.10 | Report: tools do not beat writing it himself yet. Henry decides whether R2 is worth building for the time it would save |
| 4 | A1 large content effect, or P1 notes cells clearly beat C0 | R1 plus R2: rewriter v2 trained on all-notes pairs |
| 5 | A1 small, none or inconclusive, and the B30 rewriter's per-section share is the gap | R2 alone, with or without the copy penalty per A2-N; Smaug's weights if S50 won |
| 6 | Z5 passes and A2-K shows the judge keeps most of the oracle's gain to under 0.10 | Add best-of-k with the judge to whichever route rows 2 to 5 chose |

R2 needs Henry's time for the A4 development read and possibly paid Modal: decision 8, asked with the measured case.

### 6.8 A4: rewriter v2 (phase 2, if G1 chooses R2)

- **PC generation first** (free): vLLM in WSL2 or llama.cpp with a merged rewriter and per-request logit bias for the
  Guard. Measured, not assumed.
- **Pairs:**
  - 3,000 posts from 600 or more sites, from a new build of the train split, with its corpus build costed first.
  - Every merged owner group touching buckets 95 to 99 is excluded, and texts are deduplicated against the reserve's
    hashes and MinHash signatures. This is computed without anyone reading the texts.
  - Notes at 50% and 100%; filtered for real rewrites, as Smaug did.
  - AI side: Sonnet (pinned) for a third, at most 4 workers, about 2,000 calls and an estimated 8 to 12 hours. An
    open instruct model on Modal for the rest.
- **Model:** a bake-off of gemma-4-12B against Olmo-3-7B, 1,000 pairs each, chosen by a rule fixed in advance on
  development measures: copy rate at matched claim support, the gates, length kept. Never Pangram.
- **Options:**
  - copy penalty (ORPO with the draft as the rejected text) only if A2-N was causal or inconclusive;
  - Smaug-style detector-free RL stage with the claim and form checks as hard gates;
  - DPO on Pangram-labelled pairs only with Henry's yes (decision 9).
- **Development:**
  - the gates and Henry's quality read of 20 section pairs before any A7 credit;
  - up to 400 Pangram credits on calibration posts as **monitoring only**: no decision rule, reported after the
    route is frozen.
- **Go rule for A7:** on 16 fresh calibration posts, the frozen route reads Human on at least 11 (0.69) and passes
  Henry's read. Otherwise A7 does not run, and the program reports development results only.
- **Cost:** Modal $10 to $25. The low end assumes PC training and generation; the high end adds claim-check compute
  and the corpus build. About $44 or more all on Modal, paid only with a yes. Credits about 300 for the go-rule scan
  plus up to 400 monitoring.

### 6.9 A7: final test (only if a route passes its go rule)

- **Set.**
  - 50 posts drawn from the B39 reserve by a seeded rule committed before any generation.
  - Henry's part 2 draft only with his yes, after he screens it. His published posts are development data and are
    not part of A7.
- **Cell:** the frozen route only. The criterion is absolute, so the input cell is not scanned. Input shares are
  estimated from the canaries' Sonnet post and B36.
- **Criteria,** each reported separately, none rounded up:
  1. **Pangram:** at least 32 of 50 Human in the scoring form (one-sided 95% bound above 0.50; 86% power at 0.70).
  2. **Faithfulness:** every output passes the audited gates; a person reads every flagged sentence.
  3. **Quality:** Henry's read, with at least 20 of 40 wins against the draft and at most 2 outputs unpublishable.
  4. **Readers:** an estimate with its interval.
- **What a pass means:** "the pipeline makes Sonnet posts built from complete notes of unseen bloggers' posts read
  Human". It does not show it works on Henry's genre or drafting conditions; P1 and his next posts carry that claim.
- **Cost:** about 800 to 1,250 credits for 50 outputs of 1,500 to 2,500 words, plus canaries.

### 6.10 Power

| Comparison | Detectable at 80% power, or n needed | Source |
|---|---|---|
| A1 primary, n = 32, paired SD 0.15 to 0.20 | 0.08 to 0.10 | Red team, recomputed |
| A2-N, about 28 sections in 8 posts, try SD 0.22 | 0.13 to 0.15 clustered | My simulation and the outside judge |
| Paired share 0.38 against 0.20 at SD 0.12 to 0.20 | n 6 to 14 | My simulation; `a2-measurement.md` |
| Final test, at least 50% Human | 32 of 50; P(pass at 0.5) 0.033; power 0.86 at 0.70, 0.34 at 0.60 | Both reviews |
| A7 go rule, 11 of 16 | P(pass) 0.92 at a true 0.80, 0.66 at 0.70, 0.11 at 0.50 | Exact binomial |

Each script reruns its power calculation with the latest measured SD before its n is committed.

## 7. Quality: protocol Q

- **Instrument: Henry's blind forced choice,** draft against output, section pairs of 400 to 700 words a side, on a
  private page (an Artifact with a shared database).
  - **Question:** which would he rather publish under his name. Flags for invented content, broken prose and "reads
    like AI".
  - **Controls:** swapped repeats and near-identical pairs measure his consistency.
  - LLM defect flags are shown only after his choice.
- **Limits, stated with every quality claim.** Henry is a frequent LLM user, and such readers spot AI text about 99%
  of the time. So his blind choice partly measures "reads less AI". One rater is the only rater. A paid second rater
  (about $60 to $100) only for A7, with his yes.
- **Reads and bars:**

  | Read | Pairs | Time | Bar |
  |---|---|---|---|
  | G1 | 30 (A1 C100 10, S50 10, A2-N 10) plus P1's sections | About 3 hours | A route is vetoed if it wins at most 2 of its 10 (a 0.30 true win rate is vetoed 38% of the time; P1 and A4's read cover the rest) |
  | A4 development, before any A7 credit | 20 | About 2 hours | Vetoed at 6 or fewer wins of 20 (0.058 at a true 0.5; 0.61 at 0.30) |
  | A7 | 40 plus 10 controls | About 4.5 hours | At least 20 of 40 wins, at most 2 unpublishable |

- **Total Henry time:** about 9.5 hours of reading if every phase runs, plus his notes and optional writing in P1. A
  minimal version cuts A7's read to 30 pairs (15 wins needed) and saves about an hour.
- **Secondary, never decisive:** a writing-quality reward model and an LLM panel, each reported as agreement with
  Henry's choices.

## 8. Faithfulness: protocol F

- **Hard gates, deterministic:**
  - new specifics (numbers, names, dates);
  - new code lines (`form.py` tightened from 2 to 0);
  - new math;
  - non-English runs;
  - new framing;
  - restart openers;
  - placeholder math and template leaks (B38 backlog).
- **Sentence-aligned entailment:** the share of unsupported sentences is gated at a threshold set from A0's
  false-flag rate on clean controls.
- **Coverage, draft against output:** reported as content kept.
- **A floor, never maximized** (section 2).
- **Confidentiality.** In the context-engineering post the client stays "diabetes coaching agent", as the post words
  it. Inputs as well as outputs are covered: nothing Henry has not screened goes to Claude or Pangram, and the part 2
  draft, which has client-domain material, is used only after his screen. Henry-arm outputs are checked for added
  client detail by a grep and a reader agent.

## 9. Infrastructure

| Reuse | Where |
|---|---|
| Modal runner, cost estimator, rewriter generation | `experiments/modal/lf_pipeline.py`, `lf_cost.py`, `lf_rewrite_hf.py` |
| B30 rewriter, B26 voice writer | `results/gpu13b/out_*`; Modal `adapters/b30-rewritepool` |
| Claim, copying, form and repeat checks | `src/humanizer/checks/` |
| C1 pick, open detectors, judge code | `experiments/b37_gate2a.py`, `experiments/modal/lf_detect.py`, `experiments/b38_judge.py` |
| Corpus with site splits, B39 reserve | Modal volume `longform`, `results/b39_reserved_testB.json` |
| Pangram API client | `src/humanizer/eval/pangram.py` (update for segments and `version`) |

| Build | Why | Cost |
|---|---|---|
| `humanizer.eval.scan` | Blinding, upload or API, transcripts, segments to sections, ledger in one place | Free |
| Canary set and scoring-form function | Drift detection and comparable scans | About 120 credits a session |
| Copy-penalty logits processor | A2-N, R2 | Free |
| Planted-error audit set | Validates F | 400 to 700 Claude calls |
| Blind-read page | Protocol Q | Free |
| P1 drafting kit: notes template with recall checklist, cell runner | P1, then the product if R1 wins | Free |
| Smaug-Humanizer on Modal | A1 baseline | About $1 to $2 |
| `.gitignore` for `results/a*_*.jsonl`, `a*_raw*/`, `z*_*.jsonl` | Public repo | Done 2026-11-06 |
| `experiments/a2_rechecks.py` | Recomputes attempt 1's load-bearing claims | Done |

## 10. Costs per phase

All figures are dashboard credits. If the API is live, scans move to the monthly API credit.

| Phase | Experiments | Pangram credits | Modal | Henry | Claude calls (shared account) |
|---|---|---|---|---|---|
| 1 | A0, P1, A1, A2-N, Z1, Z5, G1 read | About 3,500 core: canaries 4 sessions about 480, P1 about 300, A1 about 1,380, A2-N about 840, margin for rescans about 500. Plus up to 400 for L and 670 for A2-K: about 4,600 at most | About $10 to $13. November has $9.03 left, so A1 runs in November and A2-N waits for December's reset on 12-01, or runs on the PC | API yes, P1 notes and reads, about 3 hours at G1 | About 2,500 (C100 and S50 checks, D100, audit, A2-N) |
| 2 | A4, or productizing R1 | About 700 (A4 go rule and monitoring) | $10 to $25 in December's free credit; more only with a yes | About 2 hours (A4 read) | About 2,000 to 2,500 (pairs, checks) |
| 3 | A7, if a route passes its go rule | About 800 to 1,250 plus canaries | About $5 | About 4.5 hours | About 500 |
| **Total** | | **About 5,000 to 6,800 of 8,717** | **$25 to $43, inside two months of free credit unless A4 goes all-Modal** | **About 9.5 hours plus P1 writing** | **About 5,000 to 5,500** |

- **Reserve:** the reserve for A7 is set aside before phase 2. If phase 1 runs over, L and A2-K go first.
- **Unknown that matters:** whether Professional credits renew or expire monthly (decision 1). If they expire, attempt
  2 should spend on phase 1 before the renewal date. If they renew, the binding limit becomes Henry's monthly plan
  cost, not the 8,717.
- **Time:** realistic session time is 2 to 4 weeks, set by Claude-call wall time, December's Modal reset and Henry's
  reading. Not the 3 days the first draft said.

## 11. Validators and red teams

Every result gets, before it is reported:
1. **Statistics recompute** from raw files: an outside-judge agent given the artifacts and the claim, not the
   reasoning.
2. **Order audit:** git commit times against scan times, Modal times and the Claude cache.
3. **Red team:** confounds, leakage, selection, length, copy-rate matching, and whether the bands were applied as
   written.
4. **Output read:** an agent reads every output a verdict rests on.
5. **Leakage audit** for A7: IDs, hashes and 8-word overlap against all training and calibration data, including A4's
   new corpus.

Reports go to `results/research/a2-*.md`, with a search-log row each. This design already went through steps 1 and
3 (section 15).

## 12. Stop rules

- **Per experiment:** the bands above. A cell that fails its manipulation check is not scanned. A gate failure is
  reported as a result where its band says so (A2-N).
- **Program stop, write up and close:**
  - G1 row 1;
  - G1 row 3 if Henry declines R2;
  - an A4 route that fails its go rule after one revision;
  - any route vetoed by Henry's read.
- **Pause and ask Henry:**
  - a canary changes;
  - credits fall below the A7 reserve plus 300;
  - Modal spend reaches the approved amount;
  - any step would let Pangram choose a prompt, weight, checkpoint or pick within a route.

## 13. Decisions for Henry

**For phase 1:**
1. **Credit renewal:** do his Professional credits renew or expire monthly? (Billing page; I cannot see it.)
2. **API test:** one call (`GET /models` and a 100-word scan) on his key.
3. **Credits:** about 3,500 to 4,600 for phase 1, with about 1,250 reserved for A7.
4. **P1:** his next post, his notes for it (timed), screening of every input for client material, and a read of the
   cells. Writing the reference cell himself is optional.
5. **Reading time:** about 3 hours at G1.

**Rules:**

6. **Pangram as a picker in his own use:** may Pangram's per-section output, or best-of-k by Pangram, be used in his
   own publishing workflow? Research results would keep a final set Pangram never selects on. This decides whether
   A2-K runs as a product test.
7. **Pangram deciding between routes:** ratify that its verdicts on development data decide between routes at G1 and
   at A4's go rule, never within a route.
8. **Paid Modal for A4:** asked at G1 with the measured case. It may fit the free credit.
9. **DPO on Pangram-labelled pairs:** inside the 13:08 exception or not?

**Other:**

10. **Part 2 draft:** may it serve as an A7 item, after his screen?
11. **Pangram research grant:** more credits, but it discloses the project.
12. **The attempt-1 blind read** (FineWeb explainers): retire it in favour of protocol Q.

## 14. What this design could not verify

- **The API credit and credit renewal:** both untested. Decisions 1 and 2 settle them.
- **AIHB's numbers:** the copy-predictor null, the 5.8% pass rate and the fact-change rates are the literature agent's
  recount; I did not recompute them.
- **Smaug-Humanizer:** performance at length or on unseen writers is unknown beyond its card.
- **ProseLens:** trained on Pangram 3.3.2 labels; Z5 checks it on 4.x.
- **Adjacent-field numbers** (Argument Collapse, the reader study) were read through a summarizing tool. They enter
  no decision rule.
- **Modal costs and PC speedups:** estimates until a calibration run.
- **Pangram caching by text hash:** not ruled out; the fresh perturbed canary will show it.
- **Expected effect sizes for A1 and A2-N:** they come from short-text or correlational data. The bands are written to
  be informative whichever way they land.
- **P1 is one post:** it shows feasibility on Henry's real conditions, not a rate.

## 15. Revisions after review (2026-11-06, about 21:30 to 22:00)

The outside numbers check (`a2-judge-design-numbers.md`) found 11 wrong figures in the first draft. The red team
(`a2-redteam-design.md`) found structural problems. Changes:

- **Altitude.** The product pilot P1 moved to the front of phase 1, with Henry writing the post himself as the
  reference cell (red team section 7).
- **Gate G1.** Rewritten as an ordered table with a reachable stop. The first draft's bands were partly unreachable,
  overlapping and incomplete.
- **A1:**
  - bands made exhaustive and based on effect size with intervals;
  - realistic SD (detectable effect 0.08 to 0.10, not 0.06);
  - D100 not scanned (saves 544);
  - Henry arm moved to P1;
  - exclusion, fallback and length covariates pre-registered;
  - S50's band limited to "Smaug's weights" because chunk size is confounded;
  - Claude model pinned.
- **Triage by copying dropped:** B37's data refute it (section 2).
- **A2-N:** graded penalty at two strengths, a pre-registered gate-failure outcome, covariates, and post-level power
  (0.13 to 0.15, not 0.07).
- **A2-K:** conditional on Z5 or decision 6. Its first-draft band was a quarter met already, and it measured the
  oracle, not a judge.
- **A2-O dropped:** low prior given B5, B6 and Sun et al.; its "leakage" branch led to a route that loses content.
- **A3 folded into P1:** the scoring form is fixed as prose only, and B38 already measured math.
- **Z2 to Z4 deferred:** they need 1,500 to 3,000 Claude calls on Henry's shared account and change no decision.
- **A7:**
  - a go rule on development data (11 of 16 Human) replaces "median above 0.20", which contradicted the 32-of-50 bar;
  - the input cell is not scanned (saves about 850);
  - Henry's published posts removed, since they are development data;
  - the claim's scope stated.
- **A4:** Pangram development scans are monitoring only (the first draft let them choose); corpus exclusion of the
  B39 owners; Henry's read before any A7 credit.
- **Quality reads:** the G1 read is 30 pairs and about 3 hours; the A4 read was added; the limits of one non-blind
  expert rater are stated.
- **Faithfulness audit:** bars split into deterministic and semantic types, and a single fix round, so it cannot block
  phase 1 indefinitely.
- **Costs:**
  - canaries cost about 120 credits a session, not 70;
  - Henry arm costed;
  - Claude calls and session time budgeted;
  - November's Modal credit no longer double counted;
  - the credit-renewal question added.
- **Repo:** `.gitignore` now covers attempt-2 text outputs.
- **Corrected figures:**
  - the paper's range is 21 to 25%;
  - B38 scanned 55 of 56 seeds;
  - six adjacent-field hypotheses need no scans, not four;
  - detector-guided RL dates from late May.
