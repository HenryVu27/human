# Humanizer: fine-tuned writer report, 2026-11-04

This follows the overnight report (`REPORT-2026-11-05.md`, misdated by a day; it was written on 2026-11-04). That report's next step was a writer fine-tuned on (notes, human article) pairs. It now exists at two sizes. Spend so far: still $0. Pangram: one free dashboard scan (section 6); 3 credits left on your free plan.

## The short version

1. **Fine-tuning fixed control.** The fine-tuned OLMo-2-13B follows its notes in order, writes to the requested length (median 1.0 times the target) and stops on its own (38 of 40 generations). The same 13B model without the adapter, on the same prompts, gave seven empty or near-empty outputs and four runaways.
2. **It is the most faithful writer tested.** 96% of its claims are supported by the draft, against 88% for a Claude rewrite. Choosing the more faithful of two samples, a choice the pipeline can make by itself, raises that to 97.5% and the share of outputs where every claim passes to 45%, against 20% for Claude.
3. **The writer passes Pangram; the AI draft's notes do not.** Same fine-tuned 13B, same prompt format, same seed: 10 of 10 outputs written from notes of held-out human articles read Human on Pangram, and 10 of 10 written from notes of AI drafts read AI (section 7; Fisher exact p = 0.00001). The AI signal travels through what the notes carry over from the draft, not through the writer's register.
4. **Quality is the open problem.** The judge prefers the fine-tuned 13B over the AI draft 7.5% to 15% of the time, depending on the sample. Real human articles on the same topics win 32.5% against the same drafts, and the Claude rewrite wins 42.5%. Reading the outputs, the losses come from logic slips that contradict the notes, a repeated paragraph now and then, and a flat textbook register.
5. **13B beats 7B on every measure.** The 7B, trained on this Mac, never beat the draft and supports 92% of its claims.
6. **The unguarded 13B still invents some names.** The 13B ran without the decode-time grounding guard, which exists only for MLX (Apple's machine learning framework on this Mac). Of 40 samples, 7 added real organizations or people (NASA, USGS, the American Heart Association, Carnegie Mellon, Marty Becker, Mark Sisson) or web boilerplate ("Updated April"). Porting the guard to the PC fixes most of this.

## 1. What was built

- **Training data** (`src/humanizer/data/lora.py`): dense notes for 648 human corpus articles (indices 0 to 599 and 850 to 899; the dev, H1 and H2 splits are held out). Notes cover every point of the article, written by Claude Sonnet. 618 rows train and 30 validate. Each sequence is notes, then the human article, then the end-of-text token; loss is on the article only.
- **Inference matches training** (`src/humanizer/pipeline/lora_writer.py`): the draft gets the same dense notes, then Claude Opus selects and orders note numbers following the editor's plan. It never rewords a note. The selected notes go to the fine-tuned model.
- **7B on the Mac** (`experiments/train_lora.py`): OLMo-2-7B base, 4-bit, low-rank adaptation (LoRA) on all 32 layers, 600 iterations (about one epoch), 3.8 hours. Validation loss 1.101 to 0.970. 13B ran out of memory on 16 GB.
- **13B on the Windows PC** (`experiments/gpu/`): OLMo-2-13B base, 4-bit quantized LoRA (QLoRA), rank 16, one epoch of 155 steps on the RTX 5080. 24 minutes, 9.3 seconds per step, 11 GB peak. Validation loss 1.014 to 0.903. I drove it over SSH through Tailscale; results came back by `scp` (`results/gpu13b/`).

## 2. Results (20 dev drafts)

| Arm | Words | Quality: beats the draft | Claims supported | No new names or numbers | All claims pass | Local P(AI) |
|---|---|---|---|---|---|---|
| Draft (AI) | 1,060 | | | | | 1.00 |
| Human article, same topic | 627 | 32.5% | | | | |
| claude (rewrite) | 699 | 42.5% | 88% | 65% | 20% | 1.00 |
| sec2p (prompted 13B, best of overnight) | 580 | 0% | 62% | 55% | 0% | 0.91 |
| base13 (13B, no adapter, same notes) | 374 | 0% | 43% | 20% | 0% | 0.50 |
| lora (7B fine-tuned, guarded) | 510 | 0% | 92% | 45% | 15% | 0.00 |
| lora13, seed 0 (13B fine-tuned) | 510 | 7.5% | 96% | 50% | 30% | 0.00 |
| lora13, seed 1 | 508 | 15% | 95% | 45% | 30% | 0.00 |
| lora13, more faithful of the two | 522 | 7.5% | 97.5% | 55% | 45% | 0.00 |

Sources: `results/b2_dev.json`, `results/b2_dev_rows.jsonl`, `results/judge_ceiling_dev.json`. The human row's word count is the median over the 100 dev topics.

## 3. Findings, with evidence

### 3.1 The quality judge is a fair bar, and a hard one

Before reading the quality numbers as a verdict, I checked whether the judge simply prefers AI polish. I ran the same pairwise judge on the real human article against the AI draft written on its topic (`experiments/judge_ceiling.py`). Human articles won 21% across all 100 dev topics and 32.5% on the 20 used here. So the judge does not reject human writing outright, but human writing loses to a polished AI draft most of the time. A realistic target for a writer that sounds human is the human rate, about a third, not Claude's 42.5%.

### 3.2 Why the fine-tuned 13B loses on quality

From reading outputs against their notes (example: draft a0610, a piece on tort law):

- **Logic slips.** The notes say intent to act is enough for liability; the output says "you would not be liable for the fact that their arm was broken". It also calls defamation a "cyber tort". The claim check flags these as unsupported claims (37 of 39 supported), so a selection step can catch them.
- **Repetition.** "There is a distinction between intentional and unintentional torts" appears twice, two paragraphs apart.
- **Register.** The prose is plain and correct but flat: textbook sentences with little emphasis. The Claude rewrite frames an argument; the fine-tuned model lists points.

### 3.3 Claim check: false positives from plain-text headings

The fine-tuned model writes section headings as plain lines, as its human training articles do. The claim check reads title-case lines such as "Consensus Matters" or "How Often Should You Measure Your Blood Pressure" as new names. In 8 of the 23 flagged 13B samples, every flag is a heading or a list number ("6."). The "no new names or numbers" column understates the 13B arms somewhat; the real inventions are the ones in finding 6. I have not changed the check: a fix must not let a real name through in a heading.

## 4. What I needed from you (done: one scan, section 6)

- **A Pangram probe of the fine-tuned 13B.** This is the question everything else depends on: does fine-tuning keep the human verdict that untuned OLMo earned? Three outputs fit one day of the free dashboard's scans. I would pick three by a rule fixed in advance (the first three dev drafts where every claim passes) and scan nothing else. This is a held-out check, not a selection step.

## 5. Next steps

If Pangram says human, the fine-tuned 13B becomes the writer, and the work is quality:

1. **Port the grounding guard to PyTorch** so the 13B blocks names and numbers the draft lacks, as the 7B already does.
2. **Write section by section with best-of-k sampling** on the PC: k samples per section, keep the one whose claims are all supported and that does not repeat an earlier section. This targets the logic slips and repetition directly, uses only checks the pipeline already has, and costs PC time only.
3. **Render known headings as Markdown** (the selected notes name them), which also removes the claim-check false positives.
4. **Then train longer or on more data.** The 7B validation loss was still falling slowly at the end of its epoch (0.981, 0.978, 0.970 over the last 200 iterations); the 13B was measured only before and after.

If Pangram says AI, the fine-tune taught the assistant register through the notes format, and the next step is to look at which features of the outputs carry it before training further.

## 6. Pangram probe (added after your yes)

**Result: the one scan came back "AI Generated, 100%".** Pangram 4.1, free dashboard. The text was dev draft a0601 (seed 1, 445 words), the first output chosen by the rule fixed in section 4. The local detector gave the same text P(AI) 0.000005, so it fails here as it did on the Qwen base text. Record: `results/b3_pangram_probe.json`.

Only one of the three texts was scanned. Credits are charged by length: this scan used 5 of the 8 credits, and the next text under the rule (403 words) does not fit in the 3 left. I did not swap in a shorter text, because that would break the rule.

One scan is thin evidence, but it fits a clear hypothesis: **the AI signal travels through the notes, not the writer's register.** The notes come from an AI draft, and the fine-tuned model reproduces what they give it. The scanned text keeps the draft's AI structure almost line for line: headings such as "Community Ownership: Built With, Not For", "not just treated as service users; they are also treated as partners", label-colon paragraphs ("Early parenthood: ..."), and an argument laid out as problem, then response, then why it lasts. Untuned OLMo passed Pangram when it continued human openings, where nothing came from an AI text.

The test that separates the two explanations, at $5 of API credits:

- **Arm A:** 10 fine-tuned 13B outputs written from notes of AI drafts (the dev drafts, as here).
- **Arm B:** 10 outputs from the same model written from notes of held-out human articles (the 30 validation articles; the PC can generate these at $0).

If B passes and A fails, the notes carry the signal, and the fix is in the editor: notes that keep facts and drop the draft's structure and framing. If both fail, the fine-tune itself learned an AI register, and the writer needs work first. Until this is settled, the quality work in section 5 should wait.

## 7. B3: does the signal travel through the notes? (Pangram, 20 texts)

**Result: yes, decisively.** Same model (OLMo-2-13B plus the adapter), same notes format and sampling (seed 0), selection by file order fixed before scanning:

| Group | Notes made from | Pangram: Human | Pangram: AI | Mean words |
|---|---|---|---|---|
| A | AI drafts (dev a0600 to a0609) | 0 | 10 | 534 |
| B | held-out human articles (first 10 validation rows, never trained on) | 10 | 0 | 631 |

Fisher exact test, two-sided: p = 0.00001. Source: `results/b3_notes_leak.json`, texts in `results/b3_notes_leak_texts.jsonl`.

How it ran: the API key returned 402 Payment Required, because the Individual plan's 7-day trial carries no API credit, so nothing was charged there. The same 20 texts went through the dashboard's file upload instead (.docx made with macOS textutil; Pangram's word counts match ours to within a few percent). This used 127 of the plan's 3,000 monthly dashboard credits. The dashboard gives verdicts, not per-window scores, for uploads.

What this rules out and what it does not:

- **It rules out the writer.** The fine-tuned model can write from notes and pass Pangram. Fine-tuning did not teach it the assistant register.
- **The signal is in the content plan.** A dense note list taken from an AI draft carries the draft's structure, framing and choice of points, and a faithful writer reproduces them. Pangram detects that even in human-register prose. One sentence of the a0601 output shows it: "not just treated as service users; they are also treated as partners", a contrast that came straight from the draft.
- **Caveats.** Group B is longer, which gives Pangram more text to find AI in, so it works against this result rather than for it. Group B's notes come from articles in the training distribution (held out, but similar sources and era), and Group A's topics come from AI mirrors of the same corpus. Ten texts per group.

What this changes: the editor stage, not the writer, is now the bottleneck. A human editor cutting an AI draft keeps the facts and throws away the draft's architecture. The notes must do the same:

1. **Fact-only notes.** Extract atomic facts from the draft (claims, numbers, names, examples) with no headings, no order, no framing, no contrasts.
2. **Train the writer on the same shape.** Rebuild the 648 training pairs with fact-only notes from the human articles, so the writer learns to choose structure itself. One more 24-minute run on the PC.
3. **Test the same way.** 10 fine-tuned outputs from fact-only notes of AI drafts versus 10 from fact-only notes of human articles, on the dashboard (about 120 credits).

If fact-only notes from AI drafts pass, the humanizer works end to end, and the quality work in section 5 follows. If they still fail, the signal is in the choice of facts itself, and the editor has to add what a human writer would: a point of view the draft lacks. That cannot happen without inventing, and would change the project's premise.

## 8. B4: fact-only notes (Pangram, 20 texts)

**Result: the signal survives fact-only notes.** The 13B adapter was retrained on 620 pairs of shuffled, standalone facts (no headings, order or contrasts) and the article they came from: validation loss went from 1.10 to 0.97 in 155 steps on the PC. It then wrote 20 texts with seed 0. Group selection was the same as B3 and was fixed before the scan.

| Group | Facts extracted from | Pangram: Human | Mixed | AI | Mean words |
|---|---|---|---|---|---|
| A | AI drafts (dev a0600 to a0609) | 0 | 1 (a0604) | 9 | 1,126 |
| B | the same 10 held-out human articles as B3 | 10 | 0 | 0 | 913 |

Fisher exact test, two-sided (AI or Mixed against Human): p = 0.00001. The scan used 218 dashboard credits, leaving about 2,657. Source: `results/b4_facts.json`, texts in `results/b4_texts.jsonl`.

Group A on the other checks (vs the source draft, as in section 2): claim check pass 3 of 10, no new specifics 6 of 10, entailed share 0.93, quality wins against the draft 0 of 10. The writer is worse on fact lists than on section notes:

- **Repetition loops.** On average 29% of a group A text's sentences are repeats (B: 10%). Four group A texts ran past their length target into loops (a0601 1,514 words against a target of 910). This should bias Pangram toward Human, if anything. Group B also loops in places and still reads Human, so the loops do not explain the verdicts.
- **The new specifics are mostly headings** the writer made up from the topic ("Our Curriculum"). One is a real addition: "American Heart Association" in a0608.

**Finding: fact-only notes still carry the source's wording.** I measured word 4-gram overlap, which costs nothing to compute:

| | A (AI source) | B (human source) |
|---|---|---|
| Output 4-grams found in the fact list | 50% | 41% |
| Fact-list 4-grams copied verbatim from the source | 47% | 35% |
| Output 4-grams found in the source text | 37% | 26% |
| Output 4-grams found in the source but not in the facts | 3% | 4% |
| A only: output 4-grams found in the human article the AI draft was mirrored from | 0.6% | |

The extractor keeps about half of the source's phrasing inside the facts, and the writer copies about half its text from the facts. So more than a third of each group A output is the AI draft's own wording. B3's conclusion that the signal is in the content plan still holds, but B4 cannot tell apart two explanations: Pangram reads the AI phrasing that passes through the facts, or it reads which facts an AI chooses to state.

**Confound in both B3 and B4: topic.** Groups A and B are about different subjects. Each AI draft is a mirror of a human article on the same subject (a0600 comes from h0600), and h0600 to h0609 were never trained on. That gives a matched control.

### Next: B5, a 2 by 2 on the same 10 topics

| | Facts kept in the source's words (as B4) | Facts reworded (only names, numbers and quotes kept verbatim) |
|---|---|---|
| AI draft a0600 to a0609 | A (done, B4) | C |
| Its human original h0600 to h0609 | D | E |

- D against A isolates the source with the topic held fixed. If D reads Human, the signal comes from the AI draft, not from the subject.
- C against A isolates the wording. If C reads Human, rewording the facts is the editor's fix and the humanizer works end to end. If C stays AI while E reads Human, the signal is in which facts the AI chose, and the editor has to cut or replace the AI's choice of points.
- Rewording uses the same extractor on both sources, so its own style is the same in C and E.
- Writer: the B4 adapter, unchanged, seed 0. About 30 texts and 330 dashboard credits, inside the plan.

The PC is offline for an Ubuntu install, so B5 generation waits for it, or for a port of the writer to the Mac.

## 9. B5: same topics, wording against source (Pangram, 40 texts)

**Result: the signal is in which facts the AI chose, not in their wording or the topic.** All four cells were written on the Mac by the B4 adapter, converted from PEFT (Parameter-Efficient Fine-Tuning) to MLX format. The conversion matches the PC: validation loss falls by 0.132 with the adapter on the Mac and by 0.131 on the PC. Seed 0. Topics are dev 600 to 609; each AI draft a06xx is a mirror of human article h06xx. Selection was fixed before the scan.

| Cell | Facts from | Wording | Pangram: Human | Mixed | AI | Mean words |
|---|---|---|---|---|---|---|
| A | AI draft | extractor's (as B4) | 1 | 3 | 6 | 1,316 |
| C | AI draft | reworded | 0 | 3 | 7 | 1,229 |
| D | human original, same topic | extractor's | 10 | 0 | 0 | 758 |
| E | human original, same topic | reworded | 7 | 3 | 0 | 822 |

Fisher exact tests (Human against not Human), two-sided:

| Comparison | p |
|---|---|
| A vs D (source, topic fixed) | 0.0001 |
| C vs E (source, topic fixed) | 0.003 |
| A vs C (wording) | 1.0 |
| D vs E (wording) | 0.21 |
| AI source vs human source, all 40 | 0.0000004 |

The scan used about 450 credits. Source: `results/b5_matched.json`, texts in `results/b5_generations.jsonl`.

- **Topic is not the cause.** On the same 10 subjects, human-chosen facts read Human 17 of 20 times and AI-chosen facts 1 of 20.
- **Wording is not the cause.** Rewording cut the AI source's 4-grams in the output from 28% to 6%, and the verdicts did not move. Rewording human facts added three Mixed verdicts, probably from the rewording model's own style.
- **Length does not explain it.** The longest human-source text (D h0601, 1,862 words) reads Human, and a 756-word AI-source text (A a0604) reads Mixed.
- **Machine noise.** Cell A uses the same prompts as B4 group A. It went from 9 AI and 1 Mixed on the PC to 6 AI, 3 Mixed and 1 Human on the Mac. That is the size of the difference from quantization and sampling.

**What AI-chosen facts look like.** On the same topics, AI drafts give 53 facts per document against 35 for the human articles:

| Share of facts that... | AI draft | Human original | Human training set |
|---|---|---|---|
| contain a number | 16% | 25% | 19% |
| name someone or something | 28% | 43% | 37% |
| hedge or generalize ("can", "helps", "important", "typically") | 18% | 12% | 16% |

The AI pads with general claims and advice. The mirrors share only 0 to 11 of their roughly 50 facts with the human original on the same topic, because they were written from the topic alone.

This matches the outside evidence (`results/RESEARCH-2026-11-04-prior-work.md`). Pangram 4 is trained to label text by where its ideas came from, and to keep calling humanized AI text AI. Independent practitioners report the same split: their own notes pass, AI drafts do not.

**Next: B6 (running).** Keep only the AI draft's specific facts (names, numbers, places, studies, concrete examples), against a random subset of the same size. If the specific-only cell reads Human and the random one does not, cutting generic padding is an editor's move that needs no human source.

## 10. B6: cut the AI draft's generic facts (Pangram, 16 texts)

**Result: cutting to specific facts is no better than cutting at random. Fewer facts helps a little either way.** Same adapter, Mac, seed 0.

- **Cell F:** the AI draft's specific facts only (names, numbers, places, studies, concrete examples), as classified by Sonnet.
- **Cell G:** a random subset of the same size.
- **Rule:** fixed before generation, a draft needed at least 9 specific facts. That dropped a0602 (8) and a0605 (2).

| Cell | Pangram: Human | Mixed | AI | Mean words |
|---|---|---|---|---|
| F, specific only | 3 | 3 | 2 | 284 |
| G, random, same count | 2 | 3 | 3 | 380 |
| B5 cell A, all facts (for reference) | 1 | 3 | 6 | 1,316 |

**Caveats:**
- These texts are short (99 to 601 words). Pangram says it is less certain under 150 words, and F a0603 came out at 99 words although its target was 160.
- The gain from cutting may be length rather than content.
- The first design, an oracle that kept only the AI facts the human original also states, could not run. The mirrors share only 0 to 11 of about 50 facts with their human original.

## 11. Can the local detector stand in for Pangram? Not yet

I collected every text Pangram has judged so far into `results/pangram_labels.jsonl`: 96 texts, from B3, B4, B5 and B6. Then I scored them with the local ModernBERT detectors, which were trained on the mirror corpus and never on these labels. Code: `experiments/surrogate.py`, output: `results/surrogate.json`.

| | detector-v1 | detector-v2 |
|---|---|---|
| AUROC (area under the ROC curve, against "not Human") on B3 to B5, 80 texts | 0.84 | 0.87 |
| Same, all 96 texts including B6 | 0.78 | 0.83 |
| B6 only (short texts) | 0.42 | 0.47 |
| **Texts written from AI drafts only, 56 texts (6 Human, 13 Mixed, 37 AI)** | **0.54** | **0.67** |

The high overall numbers come from separating AI-source content from human-source content, which the content makes easy. Among outputs written from AI drafts, the comparison a best-of-N selector or a preference reward would need, the detectors are close to chance. A usable stand-in has to learn the content-plan signal itself. One way to get that without Pangram labels: train on writer outputs labelled by where their facts came from. B5 shows Pangram's verdict follows the source almost exactly.

## 12. B10: instruct-model compression (Pangram, 20 texts)

Sonnet condensed each AI draft (dev a0600 to a0609) to about 25% (K1) and about 50% (K2) of its length, adding nothing and with no instruction to sound human. **Result: 20 of 20 read AI.** Pangram's red team named compression of a large source as its one bypass, but with an instruct model doing the writing it does not work. Source: `results/b10_compress.json`.

## 13. B7: let the base model plan (Pangram, 30 texts)

**Result: AI drafts moved toward Human for the first time.** The writer got only part of the draft's facts and the draft's full length, so it had to plan and fill most of the article itself. The Guard was on (names, numbers and quotes only from the draft). Dev a0600 to a0609, Mac, seed 0.

- **Pool writer:** the 13B adapter retrained on prompts that list a random 20 to 60% of a human article's facts, with the full article as the target. Validation loss 1.68 to 1.63.
- **Cells:**
  - H: the B4 writer with the draft's specific facts.
  - P: the pool writer with the same specific facts.
  - Q: the pool writer with a random 40% of the draft's facts.

| Cell | Human | Mixed | AI | Clean texts (under 20% repeated sentences) |
|---|---|---|---|---|
| H | 5 | 4 | 1 | 6 clean: 1 Human, 4 Mixed, 1 AI |
| P | 6 | 3 | 1 | 7 clean: 4 Human, 3 Mixed, 0 AI |
| Q | 3 | 6 | 1 | 5 clean: 1 Human, 3 Mixed, 1 AI |
| B5 A (all facts, B4 writer) | 1 | 3 | 6 | |

Fisher exact tests:

| Comparison | p |
|---|---|
| P vs B5 A, Human | 0.057 |
| H, P and Q vs B5 A and C, Human | 0.002 |
| H, P and Q vs B5 A and C, AI | 0.0001 |

**Caveats:**
- **Looping text fools Pangram.** All of H's Human verdicts are looping texts. This matches Max Spero's list of where Pangram does not generalize ("degraded output"), so the looping verdicts are not a usable win. P is the only cell that holds up on clean text.
- **The cost is faithfulness.** Only about 45% of P's claims are supported by the draft (B4: 93%). The rest is the base model's own generic content. The Guard kept out invented names and numbers, apart from a few slips: "1080", the length number from the prompt, is allowed by mistake.

Source: `results/b7_pool.json` (verdicts and claim rows), texts in `results/b7_generations.jsonl`.

## 14. B11: write freely, then delete what the draft does not support (Pangram, 20 texts)

**Result: the gain survives pruning.** For every P and Q text from B7, Sonnet marked the sentences whose content the draft does not support. Those sentences, and exact repeats, were deleted. No word was changed or added.

| Cell | Human | Mixed | AI | Mean words | Claims supported |
|---|---|---|---|---|---|
| P pruned | 7 | 1 | 2 | 419 | 76% |
| Q pruned | 4 | 4 | 2 | 565 | 78% |
| B5 A, for reference | 1 | 3 | 6 | 1,316 | 93% |

P pruned against B5 A, Human: p = 0.02. One P text is 86 words; leaving it out gives 6 of 9 Human. At about the same length, B6's cut fact lists reached 3 of 8 Human, so length alone does not explain the result. Source: `results/b11_prune.json`, texts in `results/b11_texts.jsonl`.

**What this suggests the humanizer looks like:**
1. Extract the draft's specific facts.
2. A base-model writer trained on partial fact pools writes the full piece, planning it itself, with the Guard on.
3. Delete every sentence the draft does not support.

The base model's plan survives the cuts, and most of what remains is supported by the draft.

**Next: B12 (running).** A replication on 20 new drafts (a0610 to a0629), with a length-matched control: Sonnet condenses each draft to the same word count as the pipeline's output. It also runs the quality judge against the draft. Ten texts per cell is too few to trust on their own.

## 15. B9: how much human-sourced content is needed? (Pangram, 40 texts)

**Result: a clean dose-response with a threshold between one third and two thirds.**
- **Design:** each topic got a fixed number of facts, equal to the human article's fact count. A share s came from the human article and the rest from the AI draft, shuffled.
- **Writer:** the B4 facts adapter on the PC, seed 0, no Guard.
- **Topics:** dev 600 to 609.

| Human-sourced share | Human | Mixed | AI |
|---|---|---|---|
| 0 | 0 | 3 | 7 |
| 1/3 | 1 | 8 | 1 |
| 2/3 | 7 | 3 | 0 |
| 1 (B5 cell D, regenerated on the PC) | 10 | 0 | 0 |

Spearman correlation between share and verdict (AI, Mixed, Human as 0, 1, 2): 0.86, p = 2e-12. The 1/3 cell is almost all Mixed. That fits Pangram's document rule: Human needs at least 90% of characters labelled Human, AI needs at least 80% labelled AI, and anything between is Mixed. A third of AI content keeps a text out of Human, and two thirds of human content is enough most of the time. The PC's 100% cell matches B5 cell D on the Mac (10 of 10 both times), so the machine does not change this result. Source: `results/b9_dose.json`, texts in `results/b9_generations.jsonl`.

**What this opens: a second route to a full humanizer, retrieval.**
1. Keep the draft's main claims as about a third of the content.
2. Source the other two thirds from real human documents on the same topic: news, forums and pre-2023 web pages, found by search.
3. The base-model writer writes from the mix.
4. The claim check runs against the draft plus the cited sources, so nothing is invented. What is added comes from a named human source.

This changes what the draft says, so it is a product decision for Henry. Route one (B7 to B12: the base model plans, then unsupported sentences are deleted) keeps to the draft's content but drops some of it.

## 16. B12: the pipeline replicates on 20 new drafts (Pangram, 40 texts)

**Pipeline, fixed from B7 cell P and B11 before any B12 text existed:**
1. Sonnet extracts the draft's facts and keeps the specific ones.
2. The pool writer writes the draft's full length, Guard on.
3. Sentences the draft does not support, and repeats, are deleted.

**Control:** Sonnet condenses the same draft, adding nothing. **Drafts:** dev a0610 to a0629, by id.

| Cell | Human | Mixed | AI | Mean words | Claims supported |
|---|---|---|---|---|---|
| R, pipeline | 12 | 4 | 4 | 393 | 81% |
| K, Sonnet condensation | 0 | 0 | 20 | 642 | 100% |

| Comparison | p |
|---|---|
| Human, R vs K | 0.00005 |
| AI, R vs K | 0.0000002 |

- **Length:** Sonnet overshot its length targets, so K is longer. Every K text reads AI, including those of 76, 210 and 332 words, so length does not explain the gap.
- **Pooled:** with B11 P, the pipeline is 19 Human, 5 Mixed and 6 AI on 30 AI drafts.
- Source: `results/b12_replicate.json`.

## 17. The quality judge is biased toward Sonnet's style

The pipeline lost every quality comparison: the judge preferred the AI draft 39 of 40 times and Sonnet's own condensation 20 of 20. To test the instrument, I cut 20 held-out human articles (h0610 to h0629) to about 400 words at a paragraph break, and had Sonnet condense each full article to the same length. **The judge preferred Sonnet's condensation over the real human article 20 of 20.** So the Sonnet quality judge rewards Sonnet's style and cannot tell whether base-model prose is good. Source: `results/judge_calibrate.json`.

Fairer reference: the human article on the same topic, cut to the same length.

| Text | Win rate against same-topic human text (parity = 0.5) |
|---|---|
| B12 pipeline (R) | 0.20 |
| B13 cleaned pipeline (C) | 0.325 |

## 18. B13: deletion-only cleanup (Pangram, 20 texts)

Reading the B12 texts showed real defects:
- the same point made two or three times;
- list lead-ins left with nothing after them ("These behaviors may include:");
- Guard fragments such as "(S.D.)" where an acronym was blocked.

For each B12 R text, Sonnet marked repeats, empty lead-ins and headings, and broken fragments. Those were deleted, with nothing reworded.

| | Human | Mixed | AI | Mean words | Claims supported | Quality vs same-topic human text |
|---|---|---|---|---|---|---|
| B12 R | 12 | 4 | 4 | 393 | 81% | 0.20 |
| B13 cleaned | 12 | 5 | 3 | 309 | 80% | 0.325 |

The cleanup keeps the verdicts and narrows the quality gap. Source: `results/b13_cleanup.json`.

## Where this stands (2026-11-05, about 02:30)

**The humanizer now works on AI drafts as Pangram 4.1 judges them**, in 30 drafts over two independent sets:
- **Pipeline:** specific facts, then the pool writer plans and writes, then unsupported sentences and repeats are deleted.
- **Pangram:** 19 or 20 Human of 30, depending on cleanup. Every instruct-model baseline on the same drafts reads AI.
- **Faithfulness:** about 80% of claims are supported by the draft. The Guard blocks invented names, numbers and quotes. The rest are generic statements from the base model that the pruner judged supported or harmless; this needs a stricter check.
- **Quality:** the main gap. The texts are short (about 300 words from 1,100-word drafts) and, against same-topic human writing, win 32.5% where parity is 50%. A blind read by a person is needed, because the LLM judge is biased.

**Next experiments, by expected value:**
1. **Keep more of the draft.**
   - Best-of-N samples per draft, picked by claim support before pruning (local checks, never Pangram).
   - The B8 mixed-pool writer (training on the PC), which should keep more draft facts in its own plan.
2. **A bigger base model.** HALO found raw OLMo-2-32B continuations at 0.03 AI against 0.27 for 7B. It does not fit 16 GB at 4 bits, so this needs a 3-bit build or rented compute, which would cost money.
3. **The retrieval route (B9).** Two thirds of the content from human sources, kept as citations.
4. **Henry's own posts**, through the pipeline, read blind by Henry.

## 19. B14: best of 4 samples, picked by the claim check (Pangram, 20 texts)

**Result: no AI verdicts.** For each B12 draft, the pool writer wrote 3 more samples (seeds 1 to 3) on the same prompt. Each sample was pruned (B11) and cleaned (B13). The one with the most claims supported by the draft was kept; ties went to the highest supported share. The pick used the local claim check only, never Pangram.

| Same 20 drafts (a0610 to a0629) | Human | Mixed | AI | Words | Claims supported |
|---|---|---|---|---|---|
| Sonnet condensation (B12 K) | 0 | 0 | 20 | 642 | 100% |
| Pipeline, seed 0 (B12 R) | 12 | 4 | 4 | 393 | 81% |
| Plus cleanup (B13 C) | 12 | 5 | 3 | 309 | 80% |
| Plus best of 4 (B14) | 13 | 7 | 0 | 408 | 86% |

- **Significance:** against the condensation, Human p = 0.00001 and AI p = 1e-11.
- **Quality against same-topic human text:** 0.275, in line with B13's 0.325.
- **Repeatable scans:** seed 0 was picked 7 times. Those texts are identical to B13's and were scanned again, and Pangram gave the same verdict all 7 times.

Source: `results/b14_bestof.json`, texts in `results/b14_texts.jsonl`.

**The humanizer as it stands:**
1. Sonnet extracts the draft's facts and keeps the specific ones.
2. The pool writer (OLMo-2-13B base, QLoRA on partial fact pools, run on the Mac in MLX) writes the draft's full length 4 times, with the Guard on.
3. Each sample loses every sentence the draft does not support, then repeats, empty lead-ins and fragments. Nothing is reworded.
4. The sample that keeps the most supported claims wins.

**On 20 held-out AI drafts:** Pangram 4.1 gives 13 Human, 7 Mixed and 0 AI. 86% of claims are supported, and the output is about 40% of the draft's length.

## 20. B8: a writer trained to drop AI-typical facts (Pangram, 20 texts)

- **Writer:** the 13B adapter retrained on pools that mix a random 20 to 60% of a human article's facts with facts from the AI mirror of the same topic (on average 44% of the pool), with the human article as the target. Validation loss 1.69 to 1.63.
- **Test:** each B12 draft gets all of its facts, the draft's full length, the Guard, seed 0, then B11's pruning and B13's cleanup.

| Same 20 drafts | Human | Mixed | AI | Words | Claims supported | Quality vs same-topic human text |
|---|---|---|---|---|---|---|
| B14 (pool writer, specific facts, best of 4) | 13 | 7 | 0 | 408 | 86% | 0.275 |
| B8 (mixed-pool writer, all facts, 1 sample) | 5 | 10 | 5 | 452 | 86% | 0.575 |

**Result: a trade-off, not a win.** Given every fact, the writer keeps more of the AI's plan. The judge rates it as better quality, but Pangram reads it as more AI. Across these 40 texts, judged quality and Pangram humanness are weakly anti-correlated (Spearman -0.24, p = 0.13). That fits section 17: the Sonnet judge partly rewards AI style.

**Next, B16 (queued):** the mixed-pool writer with B14's input (specific facts only), best of 4. This tests whether the better planner keeps B14's Pangram result. Source: `results/b8_mixpool.json`.

## 21. B15: Henry's own post (Pangram, 14 texts)

The B14 pipeline ran on the 7 prose sections of `~/personal/blog/series/ai-engineering/part1.html` ("context engineering"). Code, tables and figures were left out.

| | Human | Mixed | AI | Words |
|---|---|---|---|---|
| Original sections | 0 | 3 | 4 | 4,481 |
| Pipeline | 4 | 1 | 2 | 1,498 |

- **The original is not uniformly AI.** "Seven Components", "Write / Select / Compress / Isolate" and "How Context Fails" read Mixed. The opening, the token budget, measurement and the lesson read AI.
- **The pipeline moves the post toward Human but damages it as an essay.** It keeps a third of the words. Lists come out as fragments ("- Context windows have grown to 200 K tokens"), and the writer refers to "the author" in the third person.
- **Why:** the writer was trained on general web articles (FineWeb-Edu style). It has never seen a first-person technical essay with lists, code and a series structure.
- **Claims supported:** 85%.

Source: `results/b15_blog.json`, texts in `results/b15_texts.jsonl`.

**What this means for Henry's blog:** the method transfers, but the writer has to be trained on the target genre. The fix is a pool writer fine-tuned on first-person technical blog posts by human authors: engineering blogs, personal ML blogs, older posts from before 2023. Their facts come from the same extractor. This is a data-collection task. The PC trains it in about 25 minutes.

## 22. B18: write, check and resample one paragraph at a time (Pangram, 6 texts)

**Question:** can the pipeline keep the draft's length? B14's pieces are about 40% of the draft because pruning deletes whole stretches the draft does not support.

**Design:**
1. A paragraph server on the PC runs the pool writer (13B, NF4, Guard on). The Mac reaches it over an SSH tunnel, under the shared GPU lock.
2. Each step asks for 4 candidate next paragraphs. Sonnet marks the sentences in each that the draft does not support.
3. The step keeps the candidate with the most supported words, with its unsupported sentences and repeats deleted. The article grows only from checked text.
4. The piece stops at the draft's length, at the article's end, after 2 steps that keep nothing, or after 40 steps.

**What happened to the run:**
- The first server stopped at its 1.9-hour limit with 2 of 20 drafts done. Claude calls had slowed about tenfold for an hour.
- Before any scan, B18 was cut to the 6 drafts the blind read needs (a0610 to a0615).
- A second JSON object in one Sonnet reply crashed a0615. The parser now reads only the first object, and a0615 was rerun.

| Same 6 drafts (a0610 to a0615) | Human | Mixed | AI | Words | Share of draft length |
|---|---|---|---|---|---|
| B14 (whole piece, best of 4, pruned) | 4 | 2 | 0 | 373 | about 35% |
| B18 (paragraph by paragraph) | 4 | 2 | 0 | 347 | 31% |

- **Claims supported:** 82%.
- **Coverage:** the pieces state 17% of the draft's facts (9% to 23%).
- **Verdicts:** a0610, the longest piece at 687 words, reads Human.

**Result: resampling does not add length.** The step logs show the mechanism:
- For the first 10 to 15 steps, each step keeps 20 to 35 words.
- Once the writer has used the ~6 facts in its prompt, its paragraphs shrink to 7 to 11 words. They state things the draft does not say, the check deletes them, and the loop stalls.
- The length limit therefore comes from how few facts the prompt carries, not from how the output is chosen. B20 tests this directly.

**A cost found on the way:** each step slowed from about 10 to 60-80 seconds as the article grew. Four candidates at once filled the PC's 16 GB of GPU memory. B20 shows the writer only the last ~500 words to avoid this.

Source: `results/b18_resample.json`, texts in `results/b18_texts.jsonl`, step logs in `results/b18_steps.jsonl`.

## 23. Asking the author: B19 (simulated) and B21 (real), neither scanned

B9 says pieces read Human once about two-thirds of their content comes from a human source. For a real user, that human source would be the author.

**B19, simulated.**
- Setup: Sonnet, playing an editor, asked 5 questions about each of 10 AI drafts. Sonnet, playing the author, answered only from the human original.
- Result: 7 of 10 "authors" answered none of the questions, and 13 of 50 questions got an answer in all.
- Why: the editor asks for first-hand experience (what happened, what you saw, real numbers). The human originals are mostly third-person articles that have none.
- Verdict: the simulation cannot stand in for an author, so its write step was not run.

**B21, real.**
- Henry got 21 questions (3 per section) about his context-engineering post on a private page.
- He wrote the post months ago and cannot recall the specifics the questions ask for. Not run.
- Finding: the interview route needs the author at the time of writing, while the material is fresh.

**Using the author's project records instead.** The project behind the post is client work, so its records stay out of third-party tools. Not run.

**Henry's objection to the interview route:** the questions are chosen by an AI, so part of the plan stays AI's. There is evidence on both sides:
- Against the objection: in B5 and B9, Sonnet chose which facts to pull from human articles, and those pieces read Human 10 of 10. AI selection over human material does not by itself read AI.
- For the objection: questions written from the AI draft steer the answers toward the draft's outline.
- Status: untested.

## 24. B20: full length written section by section (Pangram, 3 usable texts and 1 probe)

**Question:** at B14's fact density but full length, does B14's verdict hold? The drafts state about 5 facts per 100 words and B14's pieces about 1.5, so a full-length piece at B14's density carries about a third of the draft's facts.

**Design:**
1. Split the piece into k = round(length / 400) sections, each given 6 of the draft's facts. The facts are evenly spaced through the draft and kept in its order.
2. Write each section with B18's step (4 candidate paragraphs, Sonnet's check, keep the most supported words). The writer sees only the last ~500 words written.
3. Prediction, fixed before any scan: if Pangram judges each 512-token window on its own, pieces read mostly Mixed with AI at B14's level (0 to 1 of 10). If it judges the article's overall plan, AI verdicts approach B9 S0 (7 of 10).

**What happened to the run:** the PC server stopped at its 1.9-hour cap with 4 of 10 drafts written. Before any scan, B20 was stopped there, for two reasons.
- **Length precondition failed.** The 3 usable pieces reached 23 to 36% of the draft's length, B18's range. After pruning, a step keeps about 20 words: candidates are about 25 words and 41% of their sentences are unsupported. A section gets at most 10 steps. Reaching full length would take about 55 steps a draft, about 5 more GPU hours for the other 6.
- **One piece is degenerate.** In a0612, after 5 paragraphs the writer looped on "What words would you use to explain your X to someone?" for 13 paragraphs, and every check passed it. Questions state no facts, and the repeat filter catches only exact repeats, not repeated templates. It was scanned only as a probe and is not counted.

| Same 3 drafts (a0610, a0611, a0613) | Human | Mixed | AI | Words |
|---|---|---|---|---|
| B14 (best of 4, pruned) | 1 | 2 | 0 | 350 |
| B18 (paragraph by paragraph, one prompt) | 3 | 0 | 0 | 424 |
| B20 (sections spread across the draft) | 0 | 3 | 0 | 327 |

- **Claims supported:** 74%, lower than B18's 82%. **Coverage:** 15% of the draft's facts.
- **Degenerate probe (a0612, 963 words):** Mixed. Pangram did not call content-free repetition Human, but it did not call it AI either.

**Result:** B20 does not answer its question, because it never reached full length. What it does show, on only 3 drafts:
- Walking through the draft's facts in order, a section at a time, read worse than B18 on the same drafts at the same length (0 Human against 3).
- No piece read AI, which fits the per-window reading, but 3 pieces of about one window each cannot separate the two readings.
- This fits the B5 finding that the AI signal is the content plan. Following the draft's sequence of points brings back the draft's outline, even at low density.

**A gap in the checks:** the claim check and the repeat filter pass a writer stuck in a template loop. Any full-length writer needs a template-repeat guard. `humanizer.checks.repeats` now deletes a sentence when more than 60% of its word trigrams already appear in the piece. It catches 63 of a0612's 64 loop sentences (the first is new) and flags 0.8% of the 38,089 sentences in the human corpus, mostly lists and parallel phrasing. The threshold cannot go higher: each loop sentence reuses about two-thirds of its trigrams, so at 70% the guard catches none.

Source: `results/b20_sectional.json`, texts in `results/b20_texts.jsonl`, step logs in `results/b20_steps.jsonl`.

## 25. B23: what the prune deletes (no scan; the prediction failed)

**Question:** B14's writer writes full length (raw median 1,218 words against a 1,065-word target), and the prune keeps about 385. The prune prompt deletes any "fact, number, claim, example, recommendation or explanation" the draft lacks, which is stricter than the project's rule (no new facts, numbers, names, dates or quotes). If most of what it deletes is the writer's own elaboration, a narrower rule could keep both length and the writer's plan.

**Design (fixed before any output):**
1. Use B14's seed-1 raw generations for all 20 drafts: one fixed seed, not B14's pick.
2. Sonnet labels every sentence against the draft:
   - **S:** restates the draft.
   - **N:** a new specific.
   - **C:** a new general claim that could be checked.
   - **E:** the writer's elaboration, with no new checkable fact.
3. The template-repeat guard labels repeats **X**, before Sonnet.
4. Prediction: E is 30% or more of raw words, and keeping S and E reaches 60% of the draft's length.
5. Scan condition: 10 texts are scanned only if that prediction holds.

| Label | Share of raw words (repeats first) | Sonnet's labels alone |
|---|---|---|
| S, supported | 24% | 32% |
| N, new specifics | 15% | 27% |
| C, new general claims | 16% | 22% |
| E, elaboration | 12% | 19% |
| X, template repeats | 33% | |

- **Keeping S and E** reaches 43% of the draft's length on average. The upper bound, counting repeated sentences by Sonnet's label, is 61%. B14's prune keeps 38%.
- 5 of 20 drafts reach 60%.
- **Prediction failed:** E is 12%, not 30%. No scan, as fixed in advance.

**Result: the length is in new facts, not in elaboration.**
- Given about 6 facts and asked for 1,000 words, the pool writer spends about half its words on facts the draft does not have (27% specifics, 22% general claims).
- A third of its raw words restate points it already made. The guard over-counts a little, because a first statement can share topic phrases, but the sentences checked by hand are mostly real restatements.
- A narrower prune would add about 5 points of length, not 25.

## 26. B16: the mixed-pool writer with specific facts only (Pangram, 20 texts)

**Question:** B14 (pool writer, the draft's specific facts, best of 4) reads Human 13 of 20 but judges poorly against same-topic human text (0.275). B8 (mixed-pool writer, all facts) judges better (0.575) but reads 5 Human, 5 AI. Does B8's writer with B14's input keep B14's verdicts and gain B8's quality?

**Design:** the mixed-pool writer on B12's specific-fact prompts, seeds 0 to 3, each pruned and cleaned, with the most supported claims kept (B14's pick rule). Same 20 drafts.

| Same 20 drafts | Human | Mixed | AI | Words | Quality against human cut |
|---|---|---|---|---|---|
| B14 (pool writer) | 13 | 7 | 0 | about 385 | 0.275 |
| B16 (mixed-pool writer) | 14 | 4 | 2 | 394 | 0.25 |

- **Per draft:** same on 11, better on 5, worse on 4. That is no difference.
- **The 2 AI pieces:** one (a0624) is 69 words, below Pangram's 150-word floor.
- **Claims supported:** 86%.

**Result:** the writer does not matter once the input is specific facts only. B8's quality came from having all the facts, not from its writer, and all the facts bring the AI plan back.

## 27. B17: a writer trained on first-person technical blogs, on Henry's post (Pangram, 7 sections)

**Question:** B15 ran the pipeline on the 7 prose sections of Henry's post. It read 4 Human, 1 Mixed, 2 AI, but it kept a third of the words and turned "I" into "the author". Does a writer retrained on about 670 pre-2022 first-person technical blog posts fix that?

| Henry's 7 sections | Human | Mixed | AI | Words kept | First person per 100 words |
|---|---|---|---|---|---|
| Original post | 0 | 3 | 4 | 4,481 | 1.2 |
| B15 (pool writer) | 4 | 1 | 2 | 1,498 | 1.9 |
| B17 (technical-blog writer) | 3 | 1 | 3 | 1,861 | 3.5 |

- **Per section:** same on 5, worse on s2 (Human to Mixed) and s7 (Mixed to AI).
- **Section s6:** 83 words, below Pangram's floor.
- **Voice:** "the author" is gone, but first person now runs at 3 times the original's rate. The writer imitates first-person blogs rather than Henry.
- **Claims supported:** 82%.

**Result:** genre-matched training fixes voice, not verdicts.
- **The same sections fail with both writers:** s3 and s5 read AI in B15 and B17. The failure follows the section, not the writer.
- **Why those sections fail is open.** Their share of specific facts (36 to 40%) overlaps the sections that read Human (38 to 54%), so fact type does not explain it.

## 28. B24: cited human sources at full length (Pangram, 10 texts)

**Question.** Henry chose this route at about 13:30. Does a piece read Human at full length when about two-thirds of its content comes from cited human sources, none of which is the draft's own original?

**Design** (`experiments/b24_cited.py`, committed before any source or text existed):
- **Drafts:** a0610 to a0619, paired with B14.
- **Sources:** for each draft, Sonnet named Wikipedia articles a writer would read. Each was fetched as its last revision before 2022, and the first 3 usable ones were kept (for example Tort, Product liability and Strict liability for a0610; Albert Mehrabian, Body language and Nonverbal communication for a0613). Each piece cites the revision permalinks.
- **Facts:** one per 17.87 words of target length, as in B9. A third are the draft's facts (its specific ones first). Two-thirds are source facts, which Sonnet chose to fit the draft's topic.
- **Writing and selection:** pool writer with Guard, 4 seeds. Each sample was pruned against the draft plus sources, cleared of template repeats and cleaned up; the sample with the most supported claims was kept.
- **Scan:** bodies only, without citation markers.

| Measure | B24 (cell R) | B14 cell B, same drafts |
|---|---|---|
| Pangram | 10 Human, 0 Mixed, 0 AI | 7 Human, 3 Mixed, 0 AI |
| Words, share of the draft's length | 707, 66% (5 of 10 at 70% or more) | about 40% |
| Claim support (draft plus sources) | 92% | |
| Words attributed to sources, to the draft (Sonnet) | 55%, 30% | |
| Coverage of the draft's facts | 22% | |
| Quality against the human cut (Sonnet judge) | 0.30 | 0.275 (mean over B14's 20) |
| Words copied verbatim from the sources (8-word runs) | 21% (8 to 27%) | 0% |
| Of which beyond the prompt | 2% | |

**Prediction.** At least 6 Human and at most 1 AI: met (10 and 0). At 70% or more of the length: missed (66% on average). Against B14, 10 of 10 versus 7 of 10 is not significant (Fisher p = 0.21). But it comes at two-thirds of the length instead of 40%.

**Finding: verbatim copying.** About a fifth of each piece's words sit in 8-word runs copied from Wikipedia. Almost all of it arrives through the facts, whose extraction keeps the source's wording; the writer adds only 2% on its own. This was checked before the scan and recorded as an amendment.
- **Earlier experiments had it too:** B5's verbatim human cell copied 8 to 57% (10 of 10 Human) and B9's two-thirds cell 5 to 62%.
- **B5 isolates it:** with the facts reworded, copying fell to a median of about 3% and the pieces still read Human 7 of 10. Texts with no copying at all read Human. So copied wording is not what drives the human-sourced result, though it may add to it. The least-copied B24 text (8%) also reads Human.
- **For a product,** source sentences reproduced without quotation marks are plagiarism. Before this route ships, the source facts should be reworded (B5's REWORD prompt) and anything kept word for word should be quoted.

**What the pieces are.** Only 22% of the draft's facts survive, and 55% of the words come from Wikipedia. The result is a cited article on the draft's topic, not the draft made human. That fits explainers, which is what the FineWeb drafts are. It does not fit a personal blog post, where the content is the author's own; see section 29.

## 29. The blog track: B25 (Pangram, 26 texts)

**Henry's point (17:00),** checked against the raw data: every draft through B24 came from FineWeb pages, the 900 human texts in `data/human.jsonl` (essay mills, SEO sites, health sites). Their median first-person rate is 0 per 100 words, and 7% exceed 1 per 100. The humanizer's real use is a personal blog post that should sound like a person.

**Corpus** (`humanizer.data.essays`): 686 posts by 13 named writers, all published before ChatGPT's release (2022-11-30).
- **Henry's picks:** Paul Graham, Richard Sutton, Fernando Borretti, and economists Noah Smith, John Cochrane, Scott Sumner, Branko Milanovic and Robin Hanson.
- **Added for range:** Dan Luu, Julia Evans, Joel Spolsky, Scott Alexander and Patrick McKenzie.
- **Split:** fixed by URL hash before any text was read: 2 benchmark essays per writer (500 to 1,500 words) and 660 training essays (827,000 words). Texts stay out of git.
- **X:** Borretti's profile confirmed borretti.me. X search was not useful for finding further writers.

**Design** (`experiments/b25_blog.py`). B25 copies how a blogger uses AI: the blogger has the ideas, the AI writes the post.
- **Input:** for each benchmark essay, Sonnet writes the notes (the FACTS prompt, first person kept), then writes the post from them ("Write my blog post from these notes", same title, same length). That post is cell D.
- **Cells,** on each writer's test essay:
  - H: the essay itself (calibration);
  - D: the AI post;
  - P: the current pipeline on the AI post;
  - N: the pool writer from the notes.
- **Stop rule:** if 6 or more D posts read Human, P and N are not scanned.

| Cell | Human | Mixed | AI | Credits |
|---|---|---|---|---|
| H, the 13 essays | 13 | 0 | 0 | 115 |
| D, Sonnet's post from the essayist's notes | 8 | 5 | 0 | 114 |

**Reading.** The essays calibrate cleanly. The AI posts read mostly Human, which tripped the stop rule, so P and N were not scanned. At first sight this said Sonnet's own prose reads Human when a human chose the content.

**But the posts copy the essays.** 11 to 64% of each post's words sit in 8-word runs copied from the essay (mean 33%).
- **Source:** almost all of it comes through the notes, which keep 20 to 65% of their words in the essay's own wording.
- **Pattern:** the Human posts copy more (mean 37%) than the Mixed ones (21%).
- **Memorization:** Sutton's "The Bitter Lesson" post copies 48% from outside its notes, so Sonnet has memorized that essay.
- **Next test:** this is the confound B5 handled on FineWeb, so B27 removes the wording.

## 30. B27: the same notes, reworded (Pangram, 13 texts)

**Design** (`experiments/b27_reworded.py`):
- **Notes:** B25's notes were reworded with B5's prompt (no run of 3 or more words from the original apart from names, numbers and quotes).
- **Posts:** Sonnet wrote each post again from the reworded notes with the same prompt (cell W).
- **Manipulation check:** passed. Notes copying from the essay fell from 40% to 8%, and the posts' copying from 37% to 7%; Sonnet's recall of Sutton fell from 48% to 2%. The exception is Scott Alexander's post (51%): it is a list of quoted puns, and quotes are kept exactly by design.

| Cell | Human | Mixed | AI | Words copied from the essay |
|---|---|---|---|---|
| D (B25), notes in the essay's wording | 8 | 5 | 0 | 33% |
| W, the same notes reworded | 1 | 11 | 1 | 7% |

Fisher's exact test on Human, D against W: p = 0.011. The one W post that reads Human is the quote-heavy Scott Alexander post.

**Finding.** The essay's wording, carried through the notes, made Sonnet's posts read Human. With the wording removed, a post whose content is entirely the blogger's reads Mixed, not Human. Content and prose each carry part of the signal:
- **Topic-only AI drafts read AI** (B12 and the calibration drafts), and B9 S0 shows AI-chosen content reads AI even through the local writer.
- **Human content in Sonnet's prose reads Mixed** (this experiment).
- **Human content in the local writer's prose read Human** on FineWeb (B5 reworded, 7 of 10).

So the blog route is the local writer working from the blogger's own notes. B26 is now that test.

**B26, amended before any of its texts existed** (`experiments/b26_voice.py`):
- **Writer:** the pool writer retrained on the 630 training essays (notes to essay, all notes kept; the PC run is in progress).
- **Input:** B27's reworded notes, then the Guard, prune and pick pipeline.
- **Scan:** 13 texts, paired with W.
- **Prediction:** 7 or more Human, at most 1 AI.
- **Cell M:** the pool writer on the same prompts, made for local checks only, since about 75 credits remain.

## Where this stands (2026-11-05, about 13:05)

**The full-length problem now has a clear shape.** Five results fit together. B16 and B17 add that neither the writer's training mix nor its genre changes the verdicts once the input is fixed:

| Result | What it shows |
|---|---|
| B9 S0 | Every draft fact, shuffled, reads AI 7 of 10. Order is not the signal; the AI's choice of content is. |
| B12 and B14 | Only the draft's ~6 specific facts reads Human 13 of 20, but at about 40% of the length. |
| B18 and B20 | Writing paragraph by paragraph or section by section does not add length. Feeding the draft's facts in order reads worse (0 Human of 3). |
| B23 | The writer fills length with new facts (about half its words). The project's rule forbids that, and elaboration is only 12 to 19%. |
| B9 dose-response | Pieces read Human once about two-thirds of their content comes from a human source. |

**Conclusion:** a full-length rewrite of an AI draft that adds nothing has to carry the AI's choice of content. Pangram's training label is exactly that choice. Faithful, full length and Human-reading cannot all hold for an AI draft with no other source.

**What can hold:**
1. **Condensing.** About 40% of the length, Human 13 of 20 (B14). This works today.
2. **The author as the source, at writing time.** An interview while the material is fresh (B21 failed only because the post is months old).
3. **Cited human sources.** Pull specifics from real pre-2022 human writing on the topic, with citations, so about two-thirds of the content is human-sourced (the B5 and B9 mechanism, 10 of 10 Human). Nothing is invented, but the piece then says things the draft did not.

The choice among these is a product decision, not an experiment.

## 31. B28: note density, Sonnet's cells (Pangram, 76 texts; local-writer cells overnight)

**Question.** A blogger's real prompt is far sparser than notes taken from a finished essay. How does Sonnet's post read as the notes thin, and can the voice writer do better from the same notes?

**Design** (`experiments/b28_dose.py`, committed before any text existed). Pangram is Professional now (15,000 credits), so every cell is scanned.
- **Essays:** 20 fresh essays (`bench2`: 2 per writer from 10 writers, never in the voice writer's training). One Hanson essay, on deliberate COVID infection, was dropped because Sonnet refused to take notes on it, leaving 19.
- **Notes:** reworded, then cut to 100%, 50% and 25% (nested subsets).
- **S cells:** Sonnet's post from those notes.
- **L cells:** the voice writer from the same notes.
- **R cell:** the voice writer working only from the reworded facts of Sonnet's full-notes post.

| Cell | Human | Mixed | AI |
|---|---|---|---|
| H, the 19 essays | 19 | 0 | 0 |
| S100, Sonnet from all the notes | 1 | 18 | 0 |
| S50, Sonnet from half | 0 | 6 | 13 |
| S25, Sonnet from a quarter | 0 | 1 | 18 |

**Reading.** The prediction (AI rising as notes thin) held far more steeply than expected. As the notes thin, Sonnet fills the same length with its own content, and Pangram reads that content as AI. Full notes replicate B27 on new essays: human content in Sonnet's prose reads Mixed. For a blogger who hands Sonnet a few bullet points (a quarter of an essay's notes is still 7 to 17 points), the post reads AI 18 of 19.

**Voice writer.** Trained on 630 essay pairs in 43 minutes on the PC. Validation loss fell from 1.19 to 1.03, and 276 of the 630 pairs were truncated at 2,560 tokens. Its B26 and B28 cells generate overnight.

## 32. B26: the voice writer on the blogger's reworded notes (Pangram, 13 texts)

**Design** (`experiments/b26_voice.py`):
- **Writer:** the pool writer retrained (QLoRA on OLMo-2-13B, PC, 43 minutes) on 630 essays by the 13 writers, notes to essay, with all notes kept.
- **Input:** B27's reworded notes for the 13 test essays, with the same Guard, prune and best-of-4 pick as before.
- **Comparison:** paired with W, Sonnet's post from the same notes.

| Cell (same reworded notes) | Human | Mixed | AI | Length, share of the essay | Claims supported |
|---|---|---|---|---|---|
| W, Sonnet (B27) | 1 | 11 | 1 | 97% | (not checked) |
| M, pool writer (FineWeb pages) | 6 | 7 | 0 | 62% | 92% |
| V, voice writer | 11 | 2 | 0 | 82% | 92% |

- **Significance:** Fisher's exact test on Human gives p = 0.0002.
- **Paired by essay:** V reads Human where W does not on 10 of 13, and the reverse never happens.
- **Copying:** V copies 7% of its words from the essay in 8-word runs, and 2% from outside the notes.
- **Prediction:** 7 or more Human, at most 1 AI. Met.

**Reading.** This is the first full-length, faithful, Human-reading result on blogs. Given the blogger's own notes, the local writer trained on essayists produces a post of about four-fifths the essay's length that Pangram reads as human, where Sonnet from the same notes reads Mixed. The pool writer's notes route kept only 54% of the length (B25 N, original notes, not scanned). Keeping all notes in training, so the writer does not invent past them, is what restored the length.

**Voice.** First person is close to the essays' (1.8 per 100 words against 1.7). Sentence length varies less than in the essays: the median spread is 8 to 10 words against the essays' 10 to 20.

**Cell M: what the training corpus adds** (scanned 22:07, after the amendment of 18:26). M is the earlier pool writer, trained on FineWeb pages with a random 20 to 60% of the notes kept, on the same prompts with the same Guard, prune and pick.
- **Nested on every essay:** V is at least as Human as M, and M at least as Human as W, on all 13. V reads Human where M does not on 5 essays, M where W does not on 5, and never the reverse (sign test p = 0.0625 each).
- **Length:** M keeps 62% of the essay against V's 82%, so V is both longer and more often Human. Shortness does not explain V's readings.
- **Copying:** M copies 8% of its words from the essay in 8-word runs, 3% from outside the notes, as V does.

So both changes count. A local writer on human notes beats Sonnet on the same notes (M against W), and training it on essayists with every note kept adds both readings and length (V against M).

## 33. B29: imitating one writer with Sonnet (Pangram, 13 texts)

**Henry's question:** have we tried mimicking a particular writer? We had not.

**Design** (`experiments/b29_mimic.py`):
- **Prompt:** Sonnet gets three of the same writer's training posts, unnamed ("Here are three posts I wrote"), and writes the next post "in my voice" from the same reworded notes. Nothing else changes from W.
- **Authorship classifier:** character n-grams with logistic regression, trained on the 660 training essays, measures who the text sounds like.
- **Recited essay excluded:** given three of Sutton's posts and notes on "The Bitter Lesson", Sonnet recited the essay verbatim (100% copied). That text read Human but is left out by an amendment made before the scan.

| Cell, 12 counted essays | Human | Mixed | AI | Attributed to the right writer (13 texts) |
|---|---|---|---|---|
| The real essays (H) | 12 | 0 | 0 | 85% |
| W, Sonnet | 1 | 10 | 1 | 38% |
| Y, Sonnet imitating the writer | 3 | 8 | 1 | 46% |
| V, voice writer | 10 | 2 | 0 | 69% |

**Reading.** In-context imitation barely moves Sonnet, on Pangram or on the authorship test, as predicted. The local voice writer is attributed to the right writer more often than either Sonnet cell, although it is never told who the writer is. It picks the voice up from the notes' subject alone, and it saw these writers in training, so the classifier result is partly circular.

**Next:**
- **Single-writer imitation in a local model:** the base model prompted with the writer's own posts, and a fine-tune on one writer.
- **A learned rewriter:** trained on pairs of an AI post and the human essay with the same ideas. It is the most direct test of humanizing an AI draft.

## Where this stands (2026-11-05, about 18:10)

**Two routes work on the FineWeb explainer drafts.**
1. **Condensing:** B14 keeps about 40% of the length and reads Human 13 of 20.
2. **Cited human sources:** B24 keeps 66% of the length and reads Human 10 of 10. But the result is a Wikipedia-backed article on the draft's topic, and a fifth of its words are copied from Wikipedia through the facts. A product must reword or quote that.

**The blog track changes the question.** Henry's use is a personal blog post, where the content is the author's.
- **B25 and B27:** human content written up by Sonnet reads Mixed (11 of 13), not Human. Earlier Human readings came from the essay's own wording leaking through the notes.
- **B5, on FineWeb:** the local writer reads Human from reworded human facts (7 of 10).
- **So the candidate blog humanizer is:** the blogger's own notes, reworded, then written by a local writer trained on real essayists (B26), with nothing added beyond the notes.

B26 is running. It also measures whether the voice sounds like a person (first person and sentence-length spread against the real essay), and a blind read follows.

**Open problems:**
- **Note density:** how dense a blogger's notes must be. The essay notes here run 4 to 8 per 100 words, far denser than a typical prompt to an AI. A dose test is next.
- **Credits:** about 75 Pangram credits remain, enough for B26's scan and nothing after it.

## 34. B31: are newer base models detectable because of what they were trained on? (Pangram, 675 texts)

**Question.** B1 found three OLMo-2-13B base continuations read Human and one Qwen3.5-9B-Base continuation read AI, and the overnight report read that as "modern base models have absorbed AI text from the web". B31 asks whether a base model's Pangram signal tracks the date of its web crawl (H1), synthetic or instruction data added on purpose in pretraining or mid-training (H2), or neither (H0). Design, predictions and decision rules were committed before any text was scanned (`experiments/b31_basedate.py`, first as 7fad7fe; `docs/specs/2026-11-05-b31-base-model-dating.md`); every prior claim is checked in `results/research/b31-claims.md`.

**Design.**
- **Stimuli:** 30 human openings written before ChatGPT (20 FineWeb pages from 2020, B1's documents; 10 essays by 10 bloggers), first 120 words each. Only the continuation is scored, cut at a sentence end to 150 to 250 words.
- **Generation:** plain text prompt, 16-bit weights, vLLM on Modal, temperature 0.8, top-p 0.95, three seeded samples per opening, the first that passes fixed filters (length, non-prose, non-English, repetition, copying the source) is scanned. No model reproduced its document's true continuation.
- **Arms:** 19 base checkpoints in the main scan, including Olmo 3's end-of-pretraining, end-of-mid-training and final checkpoints and its three published mid-training ablations; the true human continuations; two instruct models; B1's own 4-bit texts; Llama 3.1 8B as an extension scanned in a separate batch (access came after the first upload). Five lower-priority arms (Qwen1.5, Qwen2, OLMo 1, Mistral 7B, Mistral Nemo) were generated but not scanned, by the pre-registered credit cap.
- **Scan:** blinded file names, one shuffled order, 7 batches of up to 100; Pangram 4.1 label and AI share per text.

| Arm | Crawl to | LLM text | Instruction data | n | Human / Mixed / AI | Not Human (95% CI) | Mean AI share |
|---|---|---|---|---|---|---|---|
| human (true continuation) | | | | 30 | 30 / 0 / 0 | 0% (0 to 12) | 0.00 |
| pythia-2.8b | 2020 | none | none | 30 | 23 / 2 / 5 | 23% (10 to 42) | 0.21 |
| pythia-6.9b | 2020 | none | none | 29 | 21 / 2 / 6 | 28% (13 to 47) | 0.23 |
| phi-2 | 2023 | pretraining | undocumented | 27 | 17 / 3 / 7 | 37% (19 to 58) | 0.31 |
| olmo2-7b-s1 (end of pretraining) | 2022 | none | none | 30 | 24 / 0 / 6 | 20% (8 to 39) | 0.20 |
| olmo2-7b (final) | 2022 | mid-training | mid-training | 29 | 21 / 2 / 6 | 28% (13 to 47) | 0.23 |
| olmo2-13b (B1's model) | 2022 | mid-training | mid-training | 30 | 25 / 1 / 4 | 17% (6 to 35) | 0.15 |
| olmo3-7b-2t (2T tokens) | 2024-51 | none | none | 29 | 20 / 2 / 7 | 31% (15 to 51) | 0.28 |
| olmo3-7b-genqa (2T + QA and instruction mix) | 2025-06 | mid-training | mid-training | 30 | 24 / 2 / 4 | 20% (8 to 39) | 0.16 |
| olmo3-7b-mct (2T + math, code, thinking mix) | 2025-06 | mid-training | none | 30 | 21 / 2 / 7 | 30% (15 to 49) | 0.25 |
| olmo3-7b-r5 (2T + final mix) | 2025-06 | mid-training | mid-training | 30 | 19 / 3 / 8 | 37% (20 to 56) | 0.31 |
| olmo3-7b-s1 (end of pretraining) | 2024-51 | none | none | 30 | 19 / 4 / 7 | 37% (20 to 56) | 0.32 |
| olmo3-7b-s2 (end of mid-training) | 2025-06 | mid-training | mid-training | 30 | 20 / 0 / 10 | 33% (17 to 53) | 0.32 |
| olmo3-7b (final) | 2025-06 | mid-training | mid-training | 30 | 17 / 3 / 10 | 43% (26 to 63) | 0.39 |
| nemotron-9b | 2025-13 | pretraining (33%) | pretraining | 30 | 21 / 4 / 5 | 30% (15 to 49) | 0.25 |
| mistral-small-24b | undocumented | none stated | undocumented | 28 | 20 / 3 / 5 | 29% (13 to 49) | 0.23 |
| gemma3-12b | 2024 | distillation | undocumented | 25 | 22 / 1 / 2 | 12% (2 to 31) | 0.10 |
| llama3.1-8b (extension, own batch) | 2023 | none stated | undocumented | 26 | 20 / 0 / 6 | 23% (9 to 44) | 0.23 |
| qwen2.5-7b | undocumented | pretraining | undocumented | 27 | 21 / 1 / 5 | 22% (9 to 42) | 0.21 |
| qwen3-8b | undocumented | pretraining | pretraining | 29 | 19 / 3 / 7 | 34% (18 to 54) | 0.30 |
| qwen3.5-9b (B1's model) | undocumented | undocumented | undocumented | 29 | 19 / 3 / 7 | 34% (18 to 54) | 0.29 |
| olmo2-13b, B1's 4-bit texts | | | | 17 | 16 / 0 / 1 | 6% (0 to 29) | 0.06 |
| qwen3.5-9b, B1's 4-bit texts | | | | 20 | 16 / 1 / 3 | 20% (6 to 44) | 0.18 |
| olmo2-13b-instruct | | | | 15 | 0 / 0 / 15 | 100% (78 to 100) | 1.00 |
| qwen3.5-9b-instruct | | | | 15 | 0 / 0 / 15 | 100% (78 to 100) | 1.00 |

Both validity gates pass: the human texts read Human 30 of 30, and each instruct model reads AI 15 of 15.

**Primary contrasts** (paired by opening; sign-flip test on AI share, Holm-corrected):

| Contrast | Not Human | Mean AI share change (95% CI) | p (Holm) | Verdict by the fixed rule |
|---|---|---|---|---|
| P1, H2: Olmo 3 end of pretraining to end of mid-training (about half synthetic, plus QA and instruction data) | 37% to 33% | -0.001 (-0.17 to +0.17) | 1.00 | Not supported. A rise above 0.17 is excluded; the strict refutation bound (0.15) is not quite reached |
| P2, H1: OLMo 2 to Olmo 3, both at end of pretraining (crawl through 2022 against through December 2024) | 20% to 37% | +0.12 (-0.08 to +0.31) | 0.50 | Inconclusive: right direction, not significant, below the extension band |

**What else the data say** (uncorrected, 21 secondary contrasts):
- **A pre-ChatGPT model already reads AI.** Pythia 6.9B, trained on 2020 data with no synthetic or instruction text, reads not Human on 28% of texts; its AI share is 0.24 (0.10 to 0.39) above the human continuations of the same openings. A fifth to a third of any base model's continuations read AI, whatever its training date.
- **Mid-training content does not matter here.** From the same 2T checkpoint, the QA-and-instruction mix reads lowest (20%), the math-code-thinking mix 30%, the final mix 37%, the checkpoint itself 31%; no pair differs (smallest p 0.26). Across all base arms, models that saw LLM-generated text and models that did not have the same opening-adjusted AI share (-0.004 against -0.004, Mann-Whitney p 1.00); likewise for instruction data (p 0.85).
- **A weak date trend, confounded.** Opening-adjusted AI share rises with crawl year (Spearman 0.42, p 0.12, 15 arms) and release date (0.45, p 0.05, 19 arms), but seven of those arms are Olmo 3 checkpoints, so the points are not independent, and Pythia (2020) sits above OLMo 2 (2022).
- **The opening matters more than the model.** Per-opening not-Human rates across base arms run from 0% to 74%; their spread is four times what independent outcomes would give (permutation p < 0.001). Essay openings draw AI readings more often than FineWeb pages (36% against 25%, pooled over the main base arms).
- **Post-training dwarfs everything:** instruct against base on the same openings, +0.76 (OLMo 2 13B) and +0.64 (Qwen3.5) in AI share.
- **B1, re-read.** Qwen3.5 reads not Human more often than OLMo-2-13B on the same openings (34% against 14%, McNemar p 0.03, uncorrected, one of 21), but no more than Pythia or Olmo 3. B1's 4-bit Qwen text on h0600 reads AI again when cut to 250 words, while the 16-bit Qwen sample on h0600 reads Human, and 16-bit OLMo-2-13B reads AI on two of the three openings where B1's OLMo texts read Human. B1's one-against-three result is within what sampling alone produces.
- **Quantization is not the cause:** 4-bit texts read Human more often than 16-bit ones in both families (OLMo 6% against 24% not Human on the same 17 openings, p 0.38; Qwen 21% against 32% on 19, p 0.56). They also differ in repetition penalty and random seed.

**Verdict.** The data support H0 over H1 and H2 at the strength B31 can measure. H2 is not supported: the cleanest causal test (Olmo 3 mid-training, about half synthetic data plus QA and instruction data) moved nothing, and synthetic exposure does not track the signal across models. H1 is not established: the one clean crawl-date contrast points the right way (+0.12) but is within noise, and a 2020 model reads AI about as often as 2025 ones. What B31 does establish: base-model text reads AI a fifth to a third of the time regardless of vintage, the opening being continued matters more than the model, and post-training is the large effect. An outside-judge agent recomputed every number above from the raw verdict file alone and matched them (`results/research/b31-outside-judge.md`); it adds three cautions. The 4-bit arms cover FineWeb openings only, which read Human more often than essays. The filters drop some hard openings for some models (h0604, not Human for 60% of the arms that kept it, is missing from four), which can bias a model's rate. And because the opening dominates, per-arm intervals understate uncertainty about new openings: the unit of generalization is 30 openings, not 30 texts. What B31 cannot separate: a real crawl-date effect of 0.10 or less, effects of crawls after 2024 (every such model also has synthetic data or no documentation), decoding (one setting), and detector versions after 4.1.

**For the project.**
- No sign that newer base models are closing the route: Qwen3.5 (2026) reads like Pythia (2020).
- Raw continuations of human text read Human only two thirds to four fifths of the time, so the project's Human rates come from more than the choice of a base model.
- OLMo-2-13B and Gemma-3-12B read lowest, but most base-model differences are within noise, and choosing a writer by these Pangram numbers would break the held-out rule; a writer comparison would need its own pre-registered test on new openings.
- The opening effect is the biggest lever found: what about an opening (genre, voice, topic) makes every model's continuation read AI is the natural next question.

**Spend.** Pangram 1,986 credits (1,909 main scan, 77 Llama extension; dashboard 14,076 at 23:55 to 12,090 at 00:31, matching the per-file charges exactly). Modal $3.01 of compute against the free credit (billed $0.00), weights on a Volume inside the free 1 TiB. Phase 2 (scanning the crawl itself) was conditional on H1 and was not run.

**Files:** `experiments/b31_basedate.py`, `experiments/modal/b31_modal.py`, `experiments/modal/b31_gated.py`, `results/b31_summary.json`, `results/b31_model_level.json`, `results/b31_verdicts.json`, `results/b31_exclusions.json`, `results/b31_blind.json`, `results/research/b31-*.md`. Texts and openings stay local (`results/b31_*.jsonl`, gitignored).

## 35. B30: a learned rewriter from an AI post to a human one (Pangram, 57 texts)

**Question.** Can a local model turn an AI post itself, not notes taken from it, into a post that reads Human, with the same ideas? Every earlier writer learned notes to article. B28's Sonnet posts give the hard inputs: from 100%, 50% and 25% of a blogger's reworded notes they read 1/18/0, 0/6/13 and 0/1/18 (Human/Mixed/AI).

**Design.** Fixed 2026-11-05 20:45, before any pair or text existed. Amended 23:10 and 2026-11-06 01:08, each before any B30 text was read. All in `experiments/b30_rewriter.py`.
- **Training pairs:**
  - Source: 630 essays by 13 bloggers (`data/essaypool`; no test essay).
  - For each essay, Sonnet wrote a post from the essay's reworded notes. The pair is that post to the essay, cut to 1,300 words.
  - The posts copy 3.5% of their essay's words (8-word runs), so the rewriter has to learn the human version rather than copy it.
- **Training:** QLoRA on OLMo-2-13B (4-bit), 3,584 tokens, 158 steps, on the PC (00:11 to 00:53).
- **Test:**
  - Inputs: B28's 19 bench2 essays, none in training. T100, T50 and T25 are the rewriter on Sonnet's S100, S50 and S25 posts.
  - Generation: the Guard over the post, seeds 0 and 1, pruning against the post, and the sample with the most supported claims kept.
  - Pangram selected nothing.
- **Generation hardware:**
  - The PC wrote 3 samples. Modal wrote the other 111 on A10 and A10G GPUs, with the same script, 4-bit weights, adapter, Guard and seeds.
  - It took 30 minutes and about $6, against an estimated 5 hours on the PC.

| Same 19 essays | Human | Mixed | AI | Words | Claims supported | Copied from the input post |
|---|---|---|---|---|---|---|
| S100, Sonnet post from all the notes (B28) | 1 | 18 | 0 | 787 | | |
| **T100, rewriter on S100** | **19** | 0 | 0 | 640 | 94% | 9% |
| S50, from half the notes (B28) | 0 | 6 | 13 | 798 | | |
| **T50, rewriter on S50** | **13** | 6 | 0 | 606 | 97% | 13% |
| S25, from a quarter of the notes (B28) | 0 | 1 | 18 | 857 | | |
| **T25, rewriter on S25** | 3 (2 by the 150-word rule) | **15** | 1 | 658 | 96% | 23% (median 14%) |
| H, the essays themselves (B28) | 19 | 0 | 0 | | | |

**Result: the rewriter moves every post toward Human and never away from it.**
- **Paired by essay:** the rewrite reads more human than its input on 51 of 57 pairs and less human on none (ordering Human < Mixed < AI). Two-sided sign tests: p = 8e-6 (100), 3e-5 (50), 2e-5 (25).
- **The pre-registered predictions:**
  - T100 reads Human on 12 or more of 19: met, 19 of 19.
  - T25 reads Human on 3. One of those is a broken 33-word text, which B25's rule (under 150 words counts as not Human) makes 2; the rule was applied after the scan and can only lower the count. Either way that is inside the "Pangram reads who chose the content" band (5 or fewer), not the re-planning band (10 or more).
  - But the AI verdicts on that thinnest cell fall from 18 to 1. The rewriter shifts each input about one label toward Human, and content chosen by Sonnet still holds it at Mixed.
- **Copying rises as the notes thin:** 9%, 13% and 23% of the output repeats the input post in 8-word runs. With less human content the rewriter keeps more of Sonnet's sentences, which fits the Mixed verdicts.

**Cautions.**
- **Held-out essays, not held-out writers.** Every bench author has about 60 essays in the training pairs, so the rewriter may have learned these bloggers' voices. A new writer, Henry included, is untested. The long-form program's split by author tests it.
- **One degenerate text.** In T25_e7b687627 both seeds repeated a year until the token limit, and pruning left 33 words. Its Human verdict carries no weight. Without it, T25 is 2/15/1 of 18 (sign test p 3e-5).
- **The one AI verdict is a copy.** T25_e279a1d91 repeats its input post at 99.8%: the rewriter handed back Sonnet's post.
- **The pick leans toward copying.** Keeping the sample with the most supported claims chose the sample that copies the input more often in 36 of 57 cases (p 0.06). Mixed texts copy 21% of their input against 9% for Human ones. That works against the result, not for it, but a future pick should penalize copying the input.
- **A small leak.** One training target (e148e3340) carries about 70 words of test essay e2cfe2cb2's opening, through a scraped next-post preview. The outputs for that essay copy 0 to 1.6% of it.
- **Two scan days.** The S posts were scanned on 11-05 and the T texts on 11-06, so a change in Pangram's model between scans cannot be ruled out.
- **Contamination is possible.** OLMo-2's pretraining data likely holds some of these well-known bloggers' essays. The outputs repeat the essay beyond what the input post explains in 2.2% (T100), 0.5% and 0.4% of words: small, but not zero.
- **Not long-form yet.** The outputs average 600 to 660 words, 77 to 82% of the target length, from a model limited to 4,096 tokens.
- **Quality.** The language-model judge prefers the original essay to the rewrite in 87 to 95% of pairs. That comparison is against the human original; the rewrite against the Sonnet post was not judged.

**Outside check.** An outside-judge agent recomputed every number from the raw files and confirmed the tallies, the pairing and sign tests, the split and the order of commits and scans (`results/research/b30-outside-judge.md`). The cautions on the 33-word text, the copy, the pick and the leak are its findings.

**What it means.** This is the first time the project has turned an AI post itself, rather than notes, into Human-reading text: all 19 when the content is the blogger's, and 13 of 19 with no AI verdict when Sonnet chose half of it. Pangram still reads who chose the content, but a learned rewriter moves each level about one label. The next tests are whether this holds on unseen writers, at full length, and on Henry's own drafts. Those are in the long-form program (`docs/briefs/2026-11-06-longform-head.md`).

**Spend.** Pangram 386 credits (dashboard 12,090 to 11,704; per-file charges sum to 401). Modal about $6.

**Files:** `experiments/b30_rewriter.py`, `experiments/modal/b30_gen.py`, `experiments/gpu/train13b.py`, `experiments/gpu/gen13b_guard.py`, `results/b30_rewriter.json`. Texts stay local (`results/b30_*.jsonl`, gitignored).

## 36. B28's local-writer cells, beside B30 (Pangram, 76 texts)

**Question.** Section 31 left B28's local cells for the night:
- **L:** the voice writer from the same reworded notes Sonnet got.
- **R:** the voice writer from facts extracted from Sonnet's full-notes post.

Section 35's rewriter (T) works on Sonnet's posts for the same 19 essays, so all four ways of using a blogger's notes can now be compared on the same essays.

**Design.**
- Fixed 2026-11-05 18:28 in `experiments/b28_dose.py`.
- The voice writer was trained before B26's scan, with the Guard, pruning against the notes, 2 seeds, and the most supported claims kept.
- Samples came from the Mac (37) and the PC (115), under the amendments of 19:46 to 23:10.
- Amended 2026-11-06 04:07, after the pick and before the scan: a text under 150 words counts as not Human (B25's rule). Two L25 texts fall under it.

| Same 19 essays | Human | Mixed | AI | Words | Share of the essay's length | Claims supported |
|---|---|---|---|---|---|---|
| S100, Sonnet from all the notes | 1 | 18 | 0 | 787 | | |
| L100, voice writer from all the notes | 11 | 8 | 0 | 541 | 67% | 90% |
| T100, rewriter on S100 (B30) | 19 | 0 | 0 | 640 | 82% | 94% |
| R, voice writer from the S100 post's facts | 13 | 6 | 0 | 509 | 66% | 93% |
| S50, Sonnet from half | 0 | 6 | 13 | 798 | | |
| L50, voice writer from half | 14 | 5 | 0 | 361 | 45% | 85% |
| T50, rewriter on S50 (B30) | 13 | 6 | 0 | 606 | 78% | 97% |
| S25, Sonnet from a quarter | 0 | 1 | 18 | 857 | | |
| L25, voice writer from a quarter | 17 (15 by the 150-word rule) | 2 | 0 | 280 | 35% | 72% |
| T25, rewriter on S25 (B30) | 3 (2 by the rule) | 15 | 1 | 658 | 77% | 96% |

**Paired by essay** (Human < Mixed < AI; two-sided sign tests):
- **L against S:** L reads more human at every dose. It wins 10 to 0 (p 0.002), 19 to 0 and 19 to 0 (p 4e-6 each).
- **T against L:**
  - With all the notes, T100 is more human than L100 on 8 essays and less on none (p 0.008).
  - At half, they tie (3 against 4).
  - At a quarter, L25 is more human on 15 essays and T25 on 1 (p 5e-4; 14 against 1, p 0.001, under the 150-word rule).
- **R:** R against L100 is 4 against 2 (p 0.69). R is more human than S100 on 12 essays and less on none (p 5e-4). T100 is more human than R on 6 and less on none (p 0.03).

**Against the predictions fixed at 18:28:**
- **Met:**
  - H 19 of 19 Human.
  - S at most 3 Human per dose, with AI rising as the notes thin.
  - L beats S on Human count at every dose.
  - L's length falls with dose.
- **Missed:**
  - L100 reads Human on 11 of 19, one short of the predicted 12 or more.
  - L does not fall with dose; it rises: 11, 14, then 15 by the rule.
  - R does not read Human less often than L100 (13 against 11).

**Reading.**
- **The L dose trend may be a length trend, and B28 cannot tell.** With fewer notes the voice writer writes less: 541, 361 and 280 words, or 67%, 45% and 35% of the essay. Its claim support also falls, from 90% to 72%, so more of each text is the base model's own generic material. Pooled over L, texts under 300 words read Human 17 of 20, 300 to 449 words 16 of 20, and 450 and over 9 of 17. But in a logistic model neither log words nor dose is significant. Within 300 to 449 words the cells read 5/5, 5/8 and 6/7. Paired L100 against L25 is 0 to 6 as scanned (p 0.03) and 2 to 6 under the 150-word rule (p 0.29). A length-matched control would separate the two: cut each L100 text to its L25 partner's length and scan both with a few S100 texts rescanned as an anchor. B34 measures Pangram against length directly.
- **With the blogger's full content, rewriting Sonnet's post beats writing from the notes.** T100 reads 19 of 19 Human and is longer and better supported than L100. Given the whole AI post, the rewriter keeps more of the content than the notes writer does, and reads more human.
- **With thin notes, the AI post is the problem.** T25 starts from a post in which Sonnet chose about three quarters of the content, and stays Mixed. L25 starts from the blogger's few notes and stays Human, but it is a third of the length and holds less of what the post said.
- **R shows that extracting facts from an AI post works about as well as having the notes,** at about two thirds of the essay's length. B30's rewriter does better on the same input.

**Further cautions** (from the outside judge, `results/research/b28-outside-judge.md`).
- **Loops.** 15 of the picked raw samples loop (R_e2408017e repeats a number until the token cap), and 14 never reached end of text. Pruning removes the loops and no duplicate sentences survive. These 15 read Human 7 of 15, so they do not inflate the count.
- **Machines.** 18 picks come from the Mac and 58 from the PC. Both read Human 72% of the time.
- **Note order.** L's prompts shuffle the notes while S got them in order, although the docstring says "the notes' own order".
- **A trace of the essay in R.** R's Topic line comes from the essay's notes, so R carries a trace of the blogger's content beyond the S100 post.
- **Essay clustering.** Mixed labels cluster by essay: Sumner's e26077b9a is Mixed in all 4 local cells.
- **Two scan days.** S was scanned on 11-05 and L and R on 11-06, with no rescanned anchor texts.

**For Henry's use.** If his drafts carry his own content, rewriting the AI draft directly (B30) is now the strongest route, and it keeps the most length. Whether it holds on a writer the rewriter never saw is the open question, and the long-form program's B36 tests it.

**Spend.** Pangram 355 credits (dashboard 11,704 to 11,349; per-file charges sum to 371).

**Outside check.** An outside-judge agent recomputed every count, test and length from the raw files and the commit and file times, and confirmed them (one rounding slip, 68% for 67%). The length and caution paragraphs above are its findings.

**Files:** `experiments/b28_dose.py`, `results/b28_dose.json`, `results/research/b28-outside-judge.md`. Texts stay local (`results/b28_*.jsonl`, gitignored).

## 37. B34 and B36: whole posts by writers the rewriter never saw (Pangram, 169 texts)

**Question.** B30's rewriter turned Sonnet's posts from half a blogger's notes into Human-reading posts 13 times in 19,
at about 640 words, on held-out essays by the 13 bloggers it trained on. Does it transfer to writers it never saw, and
to whole posts of 1,500 to 3,000 words? And does length by itself move Pangram's verdict (B34)? Long-form program
gate 1, approved by Henry; rules committed before any selection, text or scan (eca4a0d 09:07, b254d2e 09:42, blinding
key 576b465 10:24; first upload 10:26).

**Design** (`experiments/b36_transfer.py`, `experiments/b34_length.py`; design doc amendments of 09:07, 09:41, 10:54).
- **Posts:** 32 long blog posts from B32's test-A split (sites never in any training corpus of the project, owner
  groups merged, listing pages and near-duplicates dropped, single-author personal or technical posts by a Haiku
  label), captured by Common Crawl before 2022-11-30. An independent audit removed 3 posts that were not single-author
  blog posts before any rewrite; 3 more were replaced by the pre-registered rule (Sonnet's post under 1,000 words).
  7 are technical.
- **D:** B28's pipeline unchanged: Sonnet notes, reworded, half kept, Sonnet's post (the human post's length).
- **C:** B30's rewriter, unchanged, on D section by section (600 to 1,000 words; the model has 4,096 tokens), the
  Guard, two seeds, prune, cleanup and claim check, most supported claims kept; sections joined.
- **Cells:** each text scanned whole (full) and as its first 300 words (300), blinded, one shuffled scan.
- **B34:** 10 human posts from the calib split at 300 words and in full. Its second arm (raw OLMo-2-13B continuations
  to 2,000 words) produced no usable text: in 6 tries per post across two settings, every continuation either looped
  (35 to 90% of its 4-grams repeated) or stopped short, so it was excluded by its rules.
- **Henry arm:** the same rewriter on the prose sections of Henry's two published posts (ai-engineering part 1,
  bandits part 1), scanned whole and by section, claim-checked against the originals; nothing medical or client-related
  was introduced (audited).

| Cell (32 posts) | Human | Mixed | AI | Mean AI share | Words |
|---|---|---|---|---|---|
| Dfull, Sonnet's post | 0 | 13 | 19 | 0.81 | 1,681 |
| D300 | 0 | 10 | 22 | 0.85 | about 290 |
| **Cfull, the rewrite** | **1** | **31** | **0** | **0.38** | 1,398 |
| C300 | 11 | 19 | 2 | 0.29 | about 290 |
| B34: 10 human posts, full / 300 words | 10 / 10 | 0 | 0 | 0.00 / 0.00 | 2,333 / 283 |

- **Primary tests** (Holm over two, both rejected): Cfull against Dfull, the AI share falls on all 32 posts (mean 0.44;
  Wilcoxon p about 1e-6); C300 against Cfull, 11 posts read Human only as the prefix, 1 only in full (McNemar p
  0.006). Sensitivity without the two texts the audit found faithless (one part French, one with invented code):
  1 of 30 in full, 9 against 1 (p 0.02).
- **Pre-registered band:** "does not transfer" (Cfull Human on 7 or fewer of 32; observed 1, 95% interval 0.6 to 16%).
- **Checks:** C keeps 83% of D's length and 71% of the human post's, claims supported 96%, copies 1.6% from the human
  post (none over 15%) and 32% from D (B30's T50: 13%).

**Henry's posts.** Whole posts stay Mixed (ai-engineering AI share 0.55 to 0.40; bandits 0.41 to 0.13). By section,
5 of 12 rewritten sections read Human against 0 of 12 originals; 8 improve and none get worse (sign test p 0.008).
Cautions: 7 of the 12 baselines are B15's scans from a day earlier; the rewrites are shorter; much of the ai-engineering
rewrite is Henry's own wording (66% copied from the original).

**Reading.**
1. **The rewriter does not transfer to whole posts by unseen writers.** It moves every post toward Human and removes
   every AI verdict, but at full length almost nothing clears Pangram's bar (Human needs 90% of characters labelled
   Human; the rewrites keep 38% AI on average).
2. **The bottleneck is per-window quality, and length multiplies it** (red team, `research/longform-redteam-b36.md`).
   If each 300-word stretch reads Human with probability p, a 1,400-word post reads Human with roughly p to the power
   4.6: at the observed p of 0.34 that predicts 1.7 of 32 (observed 1); at B30's implied 0.83 it would predict about
   18 of 32. So whole posts are within reach only if the per-window rate rises to about 0.8. A longer context does not
   change that arithmetic by itself.
3. **What the leftover AI share tracks:** the input post's own AI share (Spearman 0.59) and how much of it the rewrite
   copies (0.35); prefixes that read Human copy 19% of their words from D, the others 36%. The pick rule (most supported
   claims) prefers the seed that copies more in 57 of 84 sections.
4. **Length does not create false positives:** 10 human posts read Human at 300 words and in full, with AI share 0.00.
5. **What B36 cannot separate:** unseen authors from genre and fame (B30's writers are well-known essayists; B36's are
   obscure bloggers), and length from section joins (12 of 52 later sections restart as a new post, an artifact of
   section-by-section rewriting). The length effect's significance is fragile (7 against 1 once the French text and
   three texts with a spacing quirk are set aside).

**Faithfulness findings** (copying audit, `research/longform-judge-b36-copying.md`): the claim check passed one text
with about 40 lines of invented code and one with three paragraphs of garbled French; section restarts ("This is the
second of three articles") are framing the input lacks. Language, code and format checks must join the pick step.

**Outside checks.** Selection audit (`research/longform-judge-b36-selection.md`), copying audit, statistics recompute
and scan-time order (`research/longform-judge-b36-stats.md`: every number reproduced from the raw transcripts and the
browser log; the dashboard dropped 1,715 credits while per-file charges sum to 1,824), and a red team. The sensitivity
amendment came after the scan but before any verdict was unblinded (checked against the session log).

**Spend.** Pangram 1,715 credits (dashboard 11,349 to 9,634). Modal about $3.7 (two B34 continuation runs $0.52,
rewriter generation $3.20), inside the free credit.

**Files:** `experiments/b36_transfer.py`, `experiments/b34_length.py`, `experiments/modal/lf_rewrite_hf.py`,
`experiments/modal/lf_continue.py`, `results/b36_transfer.json`, `results/b34_length.json`, `results/b36_blind.json`,
`results/b36_pangram_transcript.txt`, `results/b36_pangram_shares_b*.json`, `results/LONGFORM-GATE1.md`. Texts stay
local (`results/b3[2-9]_*.jsonl`, gitignored).

## 38. B37, gate 2a: cheap levers, Henry's posts on one day, and how Pangram adds up AI text (Pangram, 48 texts)

**Question.** B36's rewrites of 32 posts by unseen writers read Human on 1 of 32 in full. Can cheap changes raise how
human each part reads before Henry pays for training at scale (gate 2b)? Rules committed before any generation (c6928c0
11:16; decision and blinding key 4b74f50 12:14:59; scan 12:16).

**Step 0, form checks** (`src/humanizer/checks/form.py`, 7 tests): non-English runs, new code, new framing, extra
headers, and restarts at the start of later sections. On B36's picked sections they catch the French text, the invented
code and 7 of the 13 posts the red team found restarting (10 of 84 sections; 150 of 168 raw samples pass). The six
missed restarts are content-level ("I spent Christmas with my family this year") and need a model check.

**Development arms on test-A** (development only now; MELD per-window rate against a threshold set on 720 windows of
100 human train-split posts):

| Arm | Per-window rate (MELD) | Copying from D | Length (of the human post) | Claims supported | Form checks pass |
|---|---|---|---|---|---|
| C0, B36's pick | 0.067 | 32% | 71% | 96% | 93% of sections |
| C1, least copying over 4 seeds | 0.066 (p 0.81) | 20% | 70% | 95% | 100% |
| L, notes-first writer at full length | 0.25 (p 4e-5) | not applicable | 28% | 89% | 91% of texts |

No arm met the pre-registered bar for a Pangram test on fresh test-B posts (C1: no change; L: too short, under the
claim and form floors), so none was run.

**MELD is not a usable development judge for rewrites** (both validators): on B36's 300-word rewrites it calls 1 of 32
human-like where Pangram calls 11, and it separates Pangram's Human from not-Human at AUROC 0.55. C1's null on MELD
therefore says little; B36's regression predicts C1 would lower Pangram's share by only about 0.03 to 0.06.

**Splice probe** (20 texts: 2 human posts that read Human, each with one Sonnet block of 88, 126 or 248 words at the
start, middle or end):

| Block, share of words | AI share (both bases, all positions) | Label |
|---|---|---|
| none | 0.00 | Human |
| 6.8% | 0.06 to 0.07 | Human |
| 9.5% | 0.08 to 0.09 | Human |
| 17% | 0.15 to 0.17 | Mixed |

Pangram's AI share is the share of words it flags, wherever they sit, and the Human line is 10%. Henry's whole posts
confirm the additive reading (whole-post share is the word-weighted mean of its sections', within 0.06), and his bandits
rewrite reads Human with two Mixed sections. So the target for a whole post is under 10% of words flagged, not a high
Human rate per window. B36's rewrites carry 38%.

**Henry's posts, same day, LaTeX stripped from both versions** (rewrites by C1's rule):

| Unit | Original | Rewrite |
|---|---|---|
| Sections (12 pairs) | 1 Human | 6 Human; 8 better, 1 worse (sign p 0.039); shares fall in 11 of 12 |
| Bandits post (about 2,600 words) | Mixed, 0.24 | **Human, 0.08** |
| Context-engineering post (about 4,500 words) | Mixed, 0.53 | Mixed, 0.24 |

Cautions: the bandits Human sits near the line (about 200 flagged words against 250 allowed) and B36's draw of the same
post read Mixed at 0.13; stripped math leaves holes in both versions; 4 of the 12 rewritten sections are B36's texts;
one pair moving to a tie would put p at 0.07. The context-engineering post had no math, and on it C1 changed 4 of 7
sections and all 4 fell (whole post 0.40 to 0.24 against B36's pick): seeds differ a lot, so selection has headroom
that no local judge can see yet. Nothing medical or client-related was added (audited).

**Reading.**
1. No cheap lever moved the development measure, and the development measure cannot see what matters.
2. Pangram adds up flagged words; a whole post needs under 10% flagged. The per-window model of B36's red team was too
   strict.
3. Long context alone would remove about 0.09 of the 0.28 gap between B36's rewrites and the line (red team); the rest is
   how human each part reads for unseen writers.
4. On Henry's own posts the rewriter works by section and once for a whole post.

**Gate 2b is not worth paid money yet.** Training would be developed blind (no local judge that tracks Pangram within
rewrites) against a gap that long context only partly addresses. Two cheaper steps come first: (a) free: score the open
detectors and simple features on every Pangram-scored rewrite already on hand and keep any judge that separates
Pangram's Human from not-Human within rewrites at AUROC 0.7 or more; (b) about 400 credits and $1: scan all 4 seeds'
sections of about 4 fresh calibration posts, to measure how far best-of-n selection can push whole posts toward 0.10.

**Outside checks.** Statistics, pick rule (all 84 sections rebuilt from the cached checks), order and confidentiality
(`research/longform-judge-b37-stats.md`); red team (`research/longform-redteam-b37.md`). Process flags: the
out-of-memory fallback in the generation script was committed after use (it only splits a batch), batch sizes were 12
and 8 rather than the docstring's 16, and per-file charges sum to 569 against the dashboard's 555.

**Spend.** Pangram 555 credits (dashboard 9,634 to 9,079). Modal about $6 (generation of 264 samples, two failed
containers, MELD scoring), $19.6 to $20.2 of the month's $30 free credit used, $0.00 billed.

**Files:** `experiments/b37_gate2a.py`, `src/humanizer/checks/form.py`, `tests/test_form.py`,
`experiments/modal/lf_rewrite_hf.py`, `results/b37_gate2a.json`, `results/b37_blind.json`,
`results/b37_pangram_transcript.txt`, `results/b37_pangram_shares.json`, `results/LONGFORM-GATE2A.md`. Texts stay local.

## 39. B38: a local judge trained on Pangram's labels, and what best-of-4 with it buys (Pangram, 57 texts)

**Question.** Can a judge trained on the project's own Pangram verdicts track Pangram on rewrites well enough to pick the
best of several tries and to develop the rewriter, so that Pangram is spent only on the final test? Henry's decision
(13:08, CLAUDE.md f578571); final-test reserve of 798 test-B posts by ID and text hash first (a99a393, 13:10); rules,
splits, metrics, the bar and the choice rule committed before any training, scoring or generation (58bf80d, 13:13);
blinding key before the scan (4fdc84e, 13:31; scan 13:33).

**Data.** 1,534 Pangram-labelled texts from B1 to B37 (561 rewrites, 273 of them not Human), grouped by author, site or
"henry" into 5 folds; a leave-one-experiment-out split trains without B36 and B37. Document level, not windows: B37
showed Pangram adds up flagged words, so a window cannot inherit its document's label. New labels: B30's rewriter, 4
seeds for each of 14 sections of 4 fresh calibration posts (sites in buckets 75 to 79), scanned blind with Henry's
bandits post with the math kept and stripped.

**Judges.** J1: logistic regression on five open detectors (MELD, Binoculars, Fast-DetectGPT on two model pairs,
desklib) and log words. J2: ModernBERT-base fine-tuned to regress Pangram's share (Modal, one L40S).

**Registered result.**

| | J1 | J2 |
|---|---|---|
| Rewrites, out-of-fold AUROC (Human against not Human) | **0.735** (group bootstrap 0.686 to 0.782) | 0.722 |
| Rewrites, Spearman with AI share (n 90) | 0.40 | 0.29 |
| Rewrites, leave-one-experiment-out AUROC (n 89) | 0.62 | 0.62 |
| Calibration sections: pair accuracy (63 pairs) | 0.746 | 0.587 |
| Best-of-4 AI share (random 0.337, oracle 0.163) | **0.215** | 0.299 |

J1 clears the 0.70 bar and is chosen (J2 is within 0.02 and not simpler). Best-of-4 with J1 cut the mean section share
by 0.122 against a random pick (section bootstrap 0.05 to 0.20), about 70% of the oracle's gain.

**What the validators and the post hoc checks found** (none of this changes the registered choice; all of it changes the
reading):

1. **The picks drop content.** J1's picks keep 60% of the input's words against 77% for all candidates; 8 of its 14
   picks fail B37's C1 gates (form checks, claim support at least 0.90, at least half the words); 7 of 14 fall below the
   claim floor. Pangram itself rewards this: candidates under the claim floor average 0.195, those above 0.376. Even the
   oracle picks 7 of 14 that fail the gates. J1's true first choice in one section was a 32-word candidate that was
   never scanned (the scan's 50-word floor; a deviation from "every candidate is scanned"), so 0.215 scores its second
   choice there; with that pick at its section's mean the figure is 0.242.
2. **Under the project's own content gates, J1 is no better than the existing rule or an untrained detector.**

   | Best-of-4 among C1-eligible candidates (all 14 sections have one) | AI share |
   |---|---|
   | Random | 0.340 |
   | J1 | 0.288 |
   | C1, least copying from the input (B37's rule) | 0.291 |
   | J2 | 0.275 |
   | Raw MELD score, no training | 0.261 |
   | Oracle | 0.213 |

   J1 against C1: +0.003 (95% interval -0.07 to +0.08, clustered by post).
3. **The bar measured the wrong thing.** The training data hold no within-section contrasts (no rewrite cell has two
   tries of the same document), and the pooled AUROC mostly separates experiments: a score that sees no text, only each
   row's experiment and cell, reaches 0.78. Within experiment and cell J1 drops to 0.669. Raw MELD alone reaches 0.6995
   on the same 561 rewrites (the 0.55 of section 38 was B36's 300-word rewrites only). The leave-one-experiment-out 0.62
   is the better forecast for a new rewriter; the newest experiments score 0.66 (B36) and 0.57 (B37) when held out.
4. **Copying from the AI input is the strongest cheap signal.** Across the 55 scanned candidates, the share copied from
   the input section in 8-word runs correlates 0.70 with Pangram's share (J1: 0.61) and has the best pair accuracy
   (0.778). On B36's 64 rewrites of Sonnet's posts it separates Human at AUROC 0.74 against J1's 0.67. This is not a
   held-out discovery: B37 had already noted it and built C1 on it.
5. **Whole posts (derived from section shares, which B37 showed add up within 0.06):** J1's picks give one Human post of
   four (p7dd69444fe, 0.0), the same post a random pick makes Human 87.5% of the time. The oracle leaves the other three
   at 0.157, 0.202 and 0.249. On these posts, best-of-4 cannot reach the 10% line even with a perfect judge.
6. **Math, same day (step 6):** Henry's bandits post with the math kept reads Mixed 0.41 (Pangram counted 5,030 words
   for 3,851 of ours); stripped, Mixed 0.24, the same as B37's scan of the stripped text. So the gap between B36's 0.41 (math
   kept) and B37's 0.24 (math stripped) was the math, not scan-to-scan noise.

**Leakage and order** (outside judges): test-B and the calibration candidates are clean (IDs, text hashes, 8-word
overlap; the reserve's combined hash recomputes, `b38_judge.py reserve_check`). One cross-fold text leak: the splice
texts carry sentences from one test-A post's Sonnet draft in another group; refitting without them moves J1 by at most
0.002. The leave-one-experiment-out test set shares text with its training data (splice bases, Henry's originals), which
lowers that figure rather than raising it (without the overlap: 0.66). Every number reproduces from raw files; J1
refits to a difference of 0.0. Order verified from git, Modal's server times and the Claude call cache. Judge
predictions on the candidates were computed after the labels were read; J1 is deterministic from inputs fixed before
the scan, and J2 was not chosen.

**Reading.**
1. A judge cleared the registered bar, but in use it adds nothing over B37's free C1 rule or the raw MELD score, and
   left unconstrained it buys share by picking texts that break the claim rule.
2. Selection is not the lever at k = 4: the gated oracle is 0.213, far above 0.10. The rewriter has to write sections
   that read more human; copying less from the AI draft is the clearest direction the data show.
3. A judge for developing the rewriter needs within-section training contrasts and copied share as a feature, and its
   bar should be pair accuracy within sections under the content gates, against C1, not pooled AUROC.

**Next, if Henry wants the judge pursued** (red team's cheapest test): 4 seeds for sections of about 16 more
calibration posts (about $1 to $2 of Modal), scanning only candidates where J1, C1 and MELD disagree under the gates
(about 350 to 500 credits) to settle whether any judge beats C1. The B39 reserve stays untouched.

**Backlog (not B38):** the form checks should catch stray placeholder math and template leaks such as "$Rewrite{n}$"
and "$Gaussian(0, 1)$" (HR2_bandits read Human at 0.08 but is not publishable: broken sentences and a garbled proof).

**Spend.** Pangram 362 credits (dashboard 9,079 to 8,717; per-file charges sum to 386). Modal about $1.6 (candidate
generation, detector scoring, J2's six trainings and the full model), the month's free credit at $20.99 of $30, $0.00
billed.

**Files:** `experiments/b38_judge.py`, `experiments/modal/lf_judge.py`, `results/b38_judge.json`,
`results/b38_j1_preds.json`, `results/b38_j2_preds.json`, `results/b38_blind.json`, `results/b38_pangram_transcript.txt`,
`results/b38_pangram_shares.json`, `results/b38_scan_times.txt`, `results/b39_reserved_testB.json`,
`results/LONGFORM-JUDGE.md`; validators `research/longform-judge-b38-stats-order.md`,
`research/longform-judge-b38-leakage.md`, `research/longform-redteam-b38.md`. Texts stay local.
