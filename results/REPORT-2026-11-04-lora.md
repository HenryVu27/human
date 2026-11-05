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

## Where this stands (2026-11-05, about 14:00)

**The full-length problem now has a clear shape.** Five results fit together:

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
