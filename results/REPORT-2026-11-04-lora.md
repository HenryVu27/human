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
