# Phase 2: R2, a rewriter that stays faithful and coherent

Written 2026-11-07 by the attempt-2 session, after Henry's go for phase 2 ("Start phase 2"). It extends
`docs/specs/2026-11-06-attempt-2-design.md` (sections 6.6 to 6.8 and the amendments of 2026-11-06), which still holds.
Money rule: free Modal credit and the PC only, until a paid step is brought to Henry with its measured case.

## 1. Goal

**Keep A1's Pangram result and make the output publishable.**
- **A1:** B30's rewriter turns Sonnet drafts written from all of a writer's notes into whole posts that read Human
  26 of 30 times.
- **But:** in the 10 posts the output reader read in full:
  - 7 invent or distort content;
  - 8 have garbled sentences;
  - 6 have abrupt section joins;
  - an editor would publish the draft rather than the rewrite in 9.

R2 has to fix those without losing the Human rate.

## 2. Diagnosis: what produces the defects

| Defect | Likely cause | Evidence | How R2 attacks it |
|---|---|---|---|
| Invented or distorted content | The rewriter learned to add: its training targets (the human essays) carry content their Sonnet drafts lack | 30 random B30 training pairs: target claims supported by the draft 0.929 on average, 6 of 30 under 0.90 (`results/a2_diag_trainpairs.json`). C100's outputs sit at 0.956 support, with fabrications inside the remainder | Clean the targets: delete every target sentence its draft does not support (deletion only, so the target stays human writing) |
| Abrupt section joins, restarts, names that were never introduced | Sections are rewritten blind to each other; B30 was trained on one section at a time | Reader: 6 of 10; B36: 12 of 52 later sections restart | Context: train on (previous target section, draft section) to target section; at inference, the previous output section is the context |
| Garbled sentences, swapped values | 4-bit OLMo-2-13B with a 4,096-token window, and possibly the Guard, which blocks name and number tokens the draft lacks and can force odd substitutes | Reader: 8 of 10; attempt 1's bandits rewrite | Base-model bake-off (gemma-4-12B, Smaug's base, against the OLMo-2-13B anchor); Guard on and off as a development ablation |
| Dropped content (a post lost all 6 code blocks) | Pruning plus a rewriter that skips what it cannot write | Reader, p40c33738de | A coverage check (draft against output) and fixed blocks: code and math are cut out before rewriting and put back in place |

## 3. Data

- **Pool:** B32's pilot corpus (`results/b32_pilot_full.jsonl`), split "train" (site buckets 0 to 74). Removed:
  - every post in a merged owner group (B36's core-name rule) that touches buckets 75 to 99;
  - every post whose text hash or MinHash signature (word 5-grams, Jaccard 0.5) matches the B39 reserve;
  - B36's listing-page and near-duplicate rules;
  - posts outside 1,000 to 3,000 words.

  Order: sha256("r2-v1:" + id). Take the first 400 posts, at most one per site.
- **AI side**, B36's pipeline with pinned models:
  - notes (B25's NOTES prompt) and rewording (B27) with claude-sonnet-5-5;
  - Sonnet's post (B25's DRAFT prompt) from all the reworded notes for two thirds of the posts, and from half
    (B36's dose rule) for one third, assigned by the hash order.
- **Pairs:** the draft and the human post are both cut into sections with B36's rule. Draft section k is paired with
  the human text it covers: the human paragraphs whose content the draft section expresses. Alignment is by sentence
  similarity, monotone, with paragraph ends only. Each pair carries the previous human section as context.
- **Target cleaning:** B11's prune (claude-sonnet-5-5) marks target sentences the draft section does not support.
  They are deleted, and nothing is reworded.
- **Filters:**
  - pairs losing more than 40% of the target's words are dropped;
  - pairs whose draft copies more than 30% of the target in 8-word runs are dropped (not real rewrites, Smaug's
    filter);
  - so are pairs over 3,500 tokens in all.
- **Size:** about 400 posts, about 1,000 section pairs, plus B30's 630 pairs cleaned the same way.
- **Claude calls:** about 5 per post (notes, rewording, draft, and pruning about 2.5 sections), about 2,000 at 4
  workers, roughly 8 to 10 hours of wall time on Henry's shared account. A 40-post pilot runs first and reports its
  deletion rate, alignment quality and call time before the rest.

## 4. Models and training

- **Prompt format:**

  ```
  Previous:
  {prev}

  Draft:
  {section}

  Rewrite:
  ```

  The first section has an empty Previous block.
- **Arms of the bake-off:** 1,000 pairs each, same data, one variable at a time.
  - **R2-O:** OLMo-2-13B QLoRA, B30's recipe, with the new data and the context format (4,096 tokens).
  - **R2-G:** gemma-4-12B QLoRA at up to 8,192 tokens.
- **The winner** is trained on all pairs. It is chosen by the development rule in section 5, never by Pangram.
- **Compute:**
  - the PC when it is reachable (free; under `C:\gpu-lock`; a 12B model at 8K needs offload);
  - otherwise December's Modal free credit (about $3 to $9 per arm on an H100 or L40S, estimated; a calibration run
    of under $1 comes first).
  - Either way the generation path is batched transformers on Modal, or vLLM or llama.cpp on the PC.

## 5. Development evaluation: quality first, no Pangram

- **Development set:** 12 calibration posts (buckets 75 to 79), not B38's 4 and not B34's 10, ordered by
  sha256("r2-dev:" + id). D100 drafts are made as in A1. These posts never enter training or the final test.
- **Cells:** R2 candidates and the A1 rewriter (B30 with C1's pick) on the same drafts, 4 seeds each, C1's pick. Guard
  on and off is an ablation on the winner only.
- **Measures, per post:**

  | Measure | Instrument | Gate for a Pangram scan |
  |---|---|---|
  | Invented or distorted content per post | A reader agent, blind to cell, with a fixed rubric (every claim not in the draft, every changed value or stance), plus the flagged claims of the claim check | Mean at most 1 per post, and at most 2 in any post |
  | Garbled sentences per 1,000 words | Reader agent plus `prose_defects` | At most 1 |
  | Section-join defects per post | Reader agent (restarts, unintroduced names, repeated openings) | At most 1 |
  | Content kept | Coverage of the draft's claims | At least 0.85 |
  | Deterministic gates | Form, placeholder and code checks | Zero findings |
  | Henry's preference | 10 section pairs, rewrite against draft, blind | Not vetoed (at most 2 of 10 rewrite wins vetoes) |

- **Choosing the winner:** the candidate with the fewest invented items per post, ties broken by garbled sentences.
  It must beat the A1 rewriter on invented items: a paired sign test over 12 posts, plus the reader's count.
- **Then Pangram, once:** the winner on A1's 30 test-A posts, against A1's C100 scan (canaries must be identical),
  paired. It keeps A1's result if its Human count is at least 22 of 30 and the mean share is under 0.10. About 450
  credits.

## 6. Pangram's role

- Pangram never chooses a candidate, seed, checkpoint or setting within R2. Every choice above is made by the reader
  and the checks.
- Pangram's one scan in phase 2 measures whether the chosen R2 keeps A1's effect. That is a route decision on
  development data, as Henry's design decision 7 allows.

## 7. Costs and time

| Item | Pangram | Modal | Claude calls | Henry |
|---|---|---|---|---|
| Data pilot (40 posts) and full build (400) | 0 | 0 | About 2,000 | none |
| Bake-off and full training | 0 | $0 on the PC, or about $10 to $20 in December's credit | 0 | none |
| Development generation and reads | 0 | About $1 to $3 | About 300 (checks) | 10 pairs, about 45 minutes |
| R2 on A1's test-A posts | About 450 plus canaries | About $3 | About 400 | none |

The earliest training date is set by the PC coming back online, or by Modal's reset on 2026-12-01.

## 8. Stop rules

- **Data:** if the 40-post pilot deletes more than 40% of target words on average, or alignment fails on more than
  20% of sections, stop and redesign the pairing before the full build.
- **Training:** if no candidate beats the A1 rewriter on invented items, report it and bring Henry the choice between
  R4 (grounding in his primary sources) and stopping.
- **The Pangram check:** if R2 keeps quality but loses the Human rate (under 22 of 30), the trade-off is real at this
  scale, and that is reported with both numbers.

## 9. Validators

Each step gets an outside check before it is reported:
- **The data pilot:** an agent audits 10 pairs (alignment, cleaning, leakage against the reserve).
- **The bake-off:** a reader agent blind to cell, and a statistics recompute.
- **The Pangram check:** a statistics and order audit, and a red team.

## Amendment 2026-11-07 22:59 CST: red team, revised order (`results/research/a2-redteam-phase2.md`)

**What the red team found:**
- The development rule could not pick a winner: a rewriter that truly halves invention passes the gate 2% of the
  time.
- A1's after-generation prune and cleanup deleted 22% of output sentences, which left dangling references, and 12 of
  82 sections were cut off at the token cap.
- Deleting target sentences fixes about a third of the invention types.
- The 50% dose third mostly fails alignment.
- The restarts come from training on essay openings only (all 630 B30 targets start at word 1).
- The Claude-call estimate was about three times too low.

The R2 data pilot was stopped after selection; no pairs exist.

**Revised order:**
1. **P2a, the repair test (now, no GPU; about 150 Claude calls, about 520 credits).**
   - A1's 30 C100 texts are flagged by the claim check, `prose_defects` and a coherence check.
   - Each is then repaired with minimal, capped edits that bring flagged spans back to the draft.
   - A reader re-reads 10, and Pangram scans all 30 once.
   - **Question:** how much Human verdict does a faithful, coherent post cost? If it holds, the B30 rewriter plus a
     repair pass is a product path with no training.
2. **P2b, re-pick from the existing 4 seeds** (no GPU, reader time). How far is the best of 4 from the gate?
3. **When compute exists, a zero-training bake-off:**
   - B30 with forced-prefix continuation, no silent deletion and a higher token cap;
   - Smaug-Humanizer on D100;
   - both evaluated under a powered rule.
4. **R2 training only if 1 to 3 leave a gap.** With all-notes drafts only, source repair (Sonnet rewrites the human
   section into AI style, Smaug's pairs) instead of target deletion, mid-post pairs, and the context ablated.

## Amendment 2026-11-07 23:21 CST: P2a result

- **Pangram holds under repair.** Minimal faithful edits to 3.8% of words keep 26 of 30 Human (mean 0.039, against
  C100's 0.032).
- **Repair improves quality, but not enough.** Invented items halve (52 to 30, lower in 10 of 10 posts), but average 3
  per post against the bar of 1. Dropped content does not move (54 to 53), and publishable posts stay at 2 of 10.
- **The largest remaining defect is dropped content.** It comes from A1's after-generation prune and cleanup (22% of
  sentences deleted) and from generations cut at the token cap (73 of 328). Both need regeneration:
  - no silent deletion;
  - a higher token cap;
  - forced-prefix continuation for later sections;
  - code and headings as fixed blocks.
- **That is step 3 of the revised order (the zero-training bake-off), and it waits for GPU compute:** the PC, or
  Modal's reset on 2026-12-01. November's credit has $3.22 left.
- **The product reading so far:** a base-model rewrite of an all-notes draft, plus a capped repair pass, reads Human at
  full length. Faithfulness, coverage and coherence still fall short of publishable. The repair pass stays in every
  later pipeline.

## Amendment 2026-11-08 12:52 CST: P2c generation failed its first check; cell not scanned

- **What happened.** The PC run finished (30 posts, 132 sections, 2 seeds, 2026-11-08 06:10). 68 of the 132 chosen
  sections degenerate into loops (over 25% of word 4-grams repeated), 70 hit the token cap, and posts average 1.78
  times the draft's length. Only 6 of 30 posts are loop-free. The cell is invalid, so the repair pass, reader and scan
  did not run. No credits were spent.
- **Causes, from the raw file (`results/p2c_bakeoff.json`):**
  - The pick rule had no loop check. A looping text copies almost nothing, so "least copying" preferred it, 27 times
    over a clean stopped candidate. This was a design error: B34 had already recorded that long continuations loop.
  - A looped section poisons the next one through the prefix: 44 of 52 sections after a looped prefix loop, against 16
    of 50 after a clean one.
  - Forced prefix itself raises looping: 48% of candidates at k > 0 against 22% at k = 0, and 15% in A1's raw
    generations.
- **Correction to an earlier reading.** The 22% of sentences A1's cleanup deleted was not only damage. A1's raw
  generations looped 50 of 328 times, all at the token cap, and its pick and cleanup removed them (0 of 32 final texts
  loop). "No silent deletion" needs a loop check in its place.
- **Not tested by this run:** whether forced prefix fixes joins or dropped content. Those questions stay open.

## Amendment 2026-11-08 13:02 CST: P2d, P2c rerun with loop protection (before any P2d text exists)

Henry asked to continue. `experiments/p2d_bakeoff.py` holds the rules and `experiments/gpu/gen_fp2.py` the generator:
early stop at a loop, up to 4 seeds a section, a clean-candidate gate before least copying, a lower token cap, and no
looped text carried forward. Gate before any Claude call or scan: at most 20% of sections without a clean candidate, no
final post looping, mean length at most 1.4 times the draft. A failed gate means returning to independent sections with
the loop gate. Correction to the 11-08 amendment's count: 106 of P2c's 264 candidates loop and 4 are empty.

## Amendment 2026-11-09 01:47 CST: P2d gate failed; P2e (independent sections) next

P2d passed two of its three gate conditions and failed the third: 4 of 30 final posts repeat themselves, because later
sections re-write earlier ones. By its pre-registered rule the cell stopped with no Claude call or scan, and the next
step is independent sections with the loop gate: `experiments/p2e_bakeoff.py`, using A1's own sections, plus a gate
against a section repeating more than 15% of the post's earlier chosen text.
