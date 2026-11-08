# Red team of the phase 2 R2 design

Date: 2026-11-07. Reviewer: reviewer-2 and red-team agent, working from the raw files. I did not run anything on
Modal or Pangram, made no Claude calls, edited no repo file and read no .env file.

Artifact under attack: `docs/specs/2026-11-07-phase2-r2-design.md`, plus its implementation `experiments/r2_data.py`
(written 2026-11-07 22:48 and not yet run).

Goal behind the task: before about 2,000 Claude calls and the December compute go in, find where R2 would fail or
waste them. The outcome behind that: Henry publishes posts that read Human and say only what his notes say.

## Verdict in one paragraph

Three things break the design as written. First, the development rule cannot pick a winner. A rewriter that truly
halves invented content beats the A1 rewriter under the 12-post sign test only about a quarter of the time, and it
passes the gate about 2% of the time. The likely outcome is "no candidate beats A1", whatever the truth, and that
outcome triggers the stop rule. Second, the diagnosis gives the model too much of the blame. About 22% of every raw
output's sentences are deleted after generation (the prune, the repeat drop and the cleanup). I traced two of the
reader's dangling-text defects directly to those deletions. B30 was also trained only on post openings (630 of 630
targets start at the essay's first word), so the restarts are a train/inference mismatch, not a lack of context.
Third, cleaning the targets by deletion repeats the mechanism that made the dangling text. It cannot touch most of the
invention types the reader found, and it leaves the other half of the pairing problem alone: targets that omit draft
content teach the rewriter to drop it. The one-third of posts at the 50% dose makes this much worse. There are
cheaper tests that would answer the decisive question first. Two of them need no GPU and could run now.

## Checks run on raw files

All scripts are in the session scratchpad
(`/private/tmp/claude-501/-Users-henryvu--claude-spares-spare-s6HQlu/cbf959c7-1fb4-4dcb-918e-c248455f5f2d/scratchpad/rt2/`).
That folder is temporary, so each method is described below.

1. **What the post-processing deletes from A1's outputs.**
   - Method: for each of C100's 82 picked sections, I compared the picked seed's raw generation (`a1_gen_c100.jsonl`)
     with the final text (`a1_texts.jsonl`). This works because every step is deletion only, so a sentence either
     survives unchanged or is gone.
   - Result: mean 22.2% of raw sentences deleted, median 18.6%.
   - In 66 places a deleted sentence is followed by a kept sentence that opens with a referring word ("Instead",
     "That", "So", "He").
2. **B30's training targets.** All 630 completions in `data/rewritepool/train.jsonl` begin at the first 60
   characters of their essay. Completions run 400 to 1,300 words, and 33 sit at the 1,300 cap.
3. **Running R2's own pairing code on A1 and B36 drafts.**
   - Method: `r2_data.align` and B36's `sections()` on A1's D100 (all notes) and B36's D (half notes), each against
     the human post (`b36_docs.jsonl`). Then sentence-level TF-IDF (term frequency times inverse document frequency)
     matching shows where each sentence's best counterpart lands.
4. **Target length and token budget per aligned pair**, from the same alignment.
5. **Power of the development rule:** a simulation with overdispersed counts, reader recall and false positives
   (`power.py`).
6. **Claude-call count:** derived from the code paths (`b27_reworded.reword_all`, `b37_gate2a._assess`) and from B36's
   label and notes files.
7. **Leakage paths in `r2_data.select`**, and the bucket composition of the B39 reserve and of B34's posts.

## Findings, ranked by how much compute, calls or credibility they would waste

### 1. The development rule cannot detect a real improvement, and the gate is probably out of reach (highest waste)

- **Sign test.** A paired sign test over 12 posts needs 10 wins out of 12 (no ties) for one-sided p < 0.05.
- **Base rate.** My count of the reader's items in `a2-reader-a1.md` gives these C100 numbers per post: 2, 0, 6, 2, 1,
  2, 4, 3, 3, 3 (mean 2.6, SD 1.65, where SD is standard deviation).
- **Simulation assumptions:**
  - negative binomial counts with shape 3;
  - a shared difficulty per post;
  - reader recall 0.7;
  - 0.3 false-positive items per post.

  These are assumptions, not measurements.
- **Results:**

  | True R2 rate (A1 = 3.7 true, 2.6 seen) | Sign test significant | Gate passed (mean at most 1, max at most 2) | Both |
  |---|---|---|---|
  | Same as A1 | 0.02 | 0.00 | 0.00 |
  | Half of A1 | 0.24 | 0.02 | 0.01 |
  | 1.0 per post | 0.57 | 0.20 | 0.15 |
  | 0.5 per post | 0.79 | 0.58 | 0.49 |

- **Reliability.** Two independent reads of the same 12 texts, at a true rate of 1.0 per post, agree on the gate
  decision 78% of the time. The "at most 2 in any post" clause is a maximum over 12 noisy counts, so it is driven by
  the single worst post and by reader false positives.
- **Reachability is unknown.** No positive control exists. Nobody knows what this rubric ("every claim not in the
  draft, every changed value or stance") counts on a text that is faithful by construction, such as a careful
  Sonnet paraphrase of the draft. Over 1,600 to 3,000 words it may well be 1 or more.
- **Unvalidated instruments:**
  - The "coverage of the draft's claims at least 0.85" gate has no instrument. `claims.claim_check` only scores the
    output against the draft (precision), and A0's planted-error audit never tested omission.
  - `prose_defects` flags 8 of 30 clean Sonnet sections (amendment 19:53), so feeding it into a gate adds false
    positives.
- **Consequence.** The design spends roughly 5,000 Claude calls building data (finding 8), then most likely ends at
  stop rule 2 ("no candidate beats the A1 rewriter") even if R2 is better. Henry would then be offered R4 or
  stopping on a false negative.
- **Fixes:**
  - Count per section (about 40 units, not 12) and use a rate-ratio test with a post random effect, or a Wilcoxon on
    per-post counts.
  - Pre-register the effect: rate ratio at most 0.5 with the interval's upper end below 1.
  - Use 24 development posts. Generation is cheap; reading is the cost.
  - Two independent reader passes, with disagreements adjudicated.
  - A planted-fabrication set of the observed types (value swap, misattribution, stance flip, invented relation,
    invented instrument, quotes recast from paraphrase) to measure the reader's recall.
  - A positive-control cell, so the gate is set from data.
  - Build and validate the coverage instrument before using it as a gate.

### 2. A large share of the reader's coherence defects come from the post-processing, not the rewriter

- **The deletions.** `_assess` (B37) runs B11's prune, B24's repeat drop and B13's cleanup on every candidate. Each
  deletes whole sentences. On C100's picked sections they removed 22% of raw sentences (check 1).
- **Two defects traced to deletions:**
  - **p01004974c5.** The raw output has "Now, after 8 years, it is time to drop these labels, because they mean
    something else." just before "Instead, I will use the terms Open Business". The pipeline deleted the first
    sentence, which left the second without an antecedent. The reader cites exactly this as a defect.
  - **p10267ee0c0, section 2.** The raw output has "The President's justice department has deported more
    undocumented workers than any other administration" just before "That hurts his base". The pipeline deleted the
    first sentence. The reader blamed setup "paragraphs away".
- **Truncation.** 12 of the 82 picked sections hit the token cap (no end of sequence (EOS); `hit_eos` false). That
  explains part of "unfinished" and "cut off mid-token".
- **Consequence:**
  - Some of the "8 of 10 garbled" and "6 of 10 abrupt joins" are pipeline artifacts. They can be fixed with no
    training.
  - The same deletion step is what R2 proposes for its training targets (finding 3).
- **Fixes:**
  - Do not delete flagged sentences silently. Either keep them and let a minimal-edit repair act on the flag, or run
    an antecedent check after deletion that restores the deleted sentence when the next one refers to it.
  - Raise the token cap.

### 3. Cleaning targets by deletion addresses about a third of the invention, and it teaches dangling text

- **The prune's recall on these error types is low.** The prune already ran on every A1 output, against its draft
  section, and the reader's items survived it: the reference device, the swapped 60/28, "$2012", "colleague Melvin",
  the invented dialogue and the reversed preference. Cleaning targets with that same prune will leave the
  equivalent material in the targets.
- **Most invention is not added sentences.** My rough sort of the reader's C100 items:
  - about 7 are added framing or sentences, which deletion can remove;
  - about 7 are value or entity substitutions;
  - about 6 are stance or logic flips or misattributions;
  - 2 are escalations.

  Substitutions are what the reverse-pair task trains. The draft is a reworded, lossy paraphrase (B27 swaps wording
  on purpose), and the loss rewards guessing the original words. Where the model cannot recover them, it guesses.
  Deleting target sentences does not change this.
- **Deletion makes the targets choppy.** Pangram is probably safe: A1c and B11 show that deletion keeps Human
  verdicts. Coherence is not. The deletions in check 1 put a deleted sentence in front of a kept referring sentence
  66 times in 82 sections. A rewriter trained on targets with those holes learns that a referent can vanish.
- **The pairing problem has two directions, and the design treats only one.**
  - `a2_diag_trainpairs.json` measures target claims supported by the draft (0.929). Nobody measured draft content
    missing from the target.
  - In D100, about 25% of draft words are Sonnet's elaboration (a2-redteam-a1, finding 1), and that elaboration is
    absent from the human target.
  - Aligned human targets are a median 1.24 times the words of their draft section (p90 1.58). Human posts are 1.25
    times D100's length.

  So each pair teaches the model both to drop draft content and to expand. A1's outputs show both: a median length
  ratio of 0.83 after pruning, dropped code blocks and dropped referents, together with invention.
- **A better way to make pairs faithful: repair the source, not the target.**
  - Keep the human section untouched. Per aligned pair, Sonnet edits the AI draft section so that it states
    everything the human section states and nothing it does not, in Sonnet's own wording.
  - This costs one call per section, the same as the prune.
  - Both directions become faithful, the target stays fully human and coherent, and the draft is still AI text.
  - This is also Smaug-Humanizer's recipe: the AI side is made from the human original, and pairs are kept only if an
    LLM (large language model) judge finds the facts identical.
  - A cheaper variant: drop unfaithful pairs (filter) instead of editing them.
  - An ablation-only variant: keep unsupported target sentences in place but mask them out of the loss.

### 4. The one-third of posts at the 50% dose trains omission and will hit the alignment stop rule

From check 3, running R2's own `align`:

| | D100 (all notes) | D (half notes) |
|---|---|---|
| Mean section alignment cosine | 0.169 | 0.131 |
| Sections under 0.10 (the design's alignment-failure line) | 3 of 82 (4%) | 16 of 84 (19%) |
| Matched draft sentences whose best human match is in another section's target (threshold 0.18 / 0.12) | 14% / 16% | 23% / 29% |
| Target words / draft words, share over 1.5 | 0.13 | 0.27 |
| Target words / draft words, share under 0.5 | 0.02 | 0.15 |

- **Why the half dose is wrong for training.** Half-dose drafts are about two thirds Sonnet fill (36% note words).
  Their targets cannot contain that fill. The rewriter cannot tell fill from real content, so it learns to drop about
  half of what any draft says. That conflicts directly with the coverage gate of 0.85.
- **The stop rule.** A one-third half-dose mix puts the expected alignment-failure share at about 9%. The pilot's
  sampling noise can then reach the 20% stop.
- **Fix:** drop the half dose from training. If sparse-notes drafts matter for Henry, handle them with the source
  repair in finding 3, which removes the fill from the draft.

### 5. The diagnosis of the joins is wrong in one load-bearing detail, and the design confounds two fixes

- **What the design says and what is true.** Section 2 says "B30 was trained on one section at a time". It was not.
  It was trained on whole essay cuts, all from the essay's first word (check 2), and then run on mid-post sections in
  B36 and A1. Every later section was out of distribution, so the model wrote a post opening. That matches "So I
  decided to make a ketone breath tester..." in section 3 of p40c and B36's 12 of 52 restarts.
- **The confound.** R2's data adds mid-post pairs and the Previous block at once. Mid-post pairs alone may fix the
  restarts. The bake-off holds the context format fixed, so it can never tell which change mattered.
- **A zero-training fix to test first: forced-prefix continuation with the existing B30 adapter.** For section k:
  - the prompt is "Draft:\n{draft sections k-1 and k}\n\nRewrite:\n{output of section k-1}";
  - the model generates the continuation.

  This is B30's own training shape (a whole draft, with the rewrite following from its start), so it stays in
  distribution. With 600-word sections it fits about 3,600 tokens of OLMo-2's 4,096. Smaller sections give more
  room.

### 6. The Previous block, as designed, spreads errors and is undone by the checks

- **The Guard spreads errors.** The Guard's allowed names and numbers come from `allowed_specifics(allowed_text,
  prompt)` (`lf_rewrite_hf.py` line 82). The prompt would contain the previous output, so a name or number invented
  in section k-1 becomes allowed in section k. Build the Guard from the draft only.
- **The checks undo the context.** The prune and the claim check score each section against its own draft section.
  A back-reference that the context makes possible ("as with Harper...") counts as unsupported and is deleted. Prune
  against the previous and current draft sections.
- **Train/test mismatch.** Training uses the cleaned human previous section, with holes. Inference uses the model's
  own output. This is ordinary exposure bias, the same as any whole-post generation, and probably not the main risk,
  because the outputs already read human. Two bigger risks:
  - **The token budget.** Median context plus draft plus target is about 2,350 tokens, p90 about 3,350, and 9% of
    pairs exceed 3,500. That leaves less room for the output at a cap that already truncated 12 of 82 sections.
  - **The context as a second source.** Facts in it can reappear in section k.
- **Fixes:**
  - Use the last paragraph of the previous output plus the previous draft section as context.
  - Or train whole-post pairs on the long-context arm (gemma-4-12B at 8K) and generate by forced-prefix
    continuation. That needs no alignment at all, which removes findings 4 and 9 for that arm.

### 7. The Guard caused at least two of the reader's value errors

- **How it works.** The Guard blocks any digit token mid-sentence unless it begins a number the draft contains
  (`guard.py`).
- **The errors:**
  - p10267's draft gives "about two thousand dollars" in words, and its title holds 2012. The Guard allows "$2" to
    grow only into "2012", which produced "promised him something like $2012".
  - p2a49's "at age  than" is a number the Guard blocked outright.
- **Fixes:**
  - Map number words to digits in the allowed set.
  - Or run Guard-off as the default and check numbers after generation.

  This is already listed as an ablation. It should be a fix, made before the bake-off.

### 8. Claude calls are underestimated about 2.5 to 3 times

| Step | Design | From the code |
|---|---|---|
| Page labels (Haiku) | not counted | about 615 (B36 eligibility 0.65) |
| Notes | 400 | 400 |
| Rewording | 400 | about 1,710 (`reword_all` makes one call per 20 notes; B36 averaged 76 notes, 4.3 calls a post) |
| Draft | 400 | 400 |
| Target prune | about 1,000 | about 1,050 (2.6 sections a post) |
| B30's 630 pairs "cleaned the same way" | not counted | about 630 to 900 |
| Development (3 calls per candidate: prune, cleanup, claim check) | about 300 | about 1,900 (12 posts, about 3.3 sections, 4 seeds, 3 cells, plus the Guard ablation) |
| R2 on test-A | about 400 | about 980 (82 sections, 4 seeds, 3 calls) |
| **Total** | **about 2,700** | **about 7,700 to 8,000** |

- **Wall time.** The design's own rate is 2,000 calls in 8 to 10 hours at 4 workers. At that rate, the total is
  about 30 to 40 hours on Henry's shared account.
- **Compute is not the constraint.** B30 trained in 38 minutes on the PC (158 steps, 14.4 s a step, 11.9 GB peak;
  `results/gpu13b/out_rewritepool/summary.json`). The binding costs are Claude wall time and reading time.

### 9. Code issues in `experiments/r2_data.py` (the implementation, not yet run)

- **The length filter is in words.** The filter is "context + draft + target over 3,500 words". The design says
  tokens. 3,500 words is about 4,700 tokens, past OLMo-2's 4,096, and `train13b.encode` silently truncates the end
  of the completion and its EOS.
- **One post per site breaks when a run resumes.** `seen_sites` starts empty and is not filled from the pilot's
  labels, so the 400-post build can take a second post from a pilot site.
- **The prune runs against the draft section only** (`prune_one(target_raw, draft)`). Target sentences that the
  alignment put next to the wrong section (14 to 29% of matched content, finding 4) are deleted as unsupported, and
  their draft counterparts end up with no target, which teaches omission. Prune against the whole draft, or the
  neighbouring sections too.
- **`align` has no unaligned state.** Every human paragraph is forced into some target, so human material that no
  draft section covers always lands in a target. Targets range from 35 to 1,810 words against draft sections of
  about 600 words.
- **Headings.** The source corpus has almost no short lines: 0.1% of 1,000 sampled posts of 1,000 to 3,000 words have
  a line of 1 or 2 words. D100 drafts carry about 14 short heading-like lines each. Targets therefore teach the
  rewriter to drop the draft's headings, which is the reader's "Jacob" referent loss (a heading dropped, then "He is
  one of my favorite characters"). Strip headings from training drafts, or treat them as fixed blocks.

### 10. Leakage, Pangram's role and confidentiality: mostly sound, three gaps

- **Confirmed sound:**
  - The training pool excludes buckets 75 to 99 and every owner group that touches them.
  - The 28 reserve posts that sit in buckets 0 to 74 through merged groups are excluded by id and by MinHash.
  - The Haiku labelling runs only on candidates that have already passed those filters, so no reserve text reaches
    Claude.
  - Test-A (buckets 90 to 94) cannot enter training.
- **Gap: B34's other posts.** The development set excludes B34's 10 H posts but not B34's 8 B openings. All 18 sit in
  buckets 75 to 79. Exclude all 18 and B38's 4.
- **Gap: Pangram as a selector across tries.** Section 6 allows one scan, and stop rule 3 only reports the outcome.
  Nothing forbids a second R2 variant (the runner-up, Guard off) on the same 30 test-A posts after a failure. That
  would make Pangram a selector across tries on the same posts. Pre-register that test-A gets one R2 scan, and that
  any later variant goes to fresh development posts.
- **Gap: what the test-A scan means.** Test-A is now development data. An R2 number on it is a route decision, not a
  test result, and the B39 reserve stays the only test. The design should say so where it reports the 22-of-30 bar.
- **Confidentiality:** none found. The inputs are public pre-2022 web posts and none of Henry's posts are used. The
  shared account sees only public text.

## Answers to the seven questions

1. **Cleaning targets.**
   - It will cut whole-sentence additions somewhat. That is about a third of the invention types.
   - It will not cut substitutions, flips or misattributions, and the same prune already failed to catch these on
     outputs.
   - Human-ness for Pangram is probably kept, but coherence is not: the deletions teach dangling referents
     (findings 2 and 3).
   - The better route is source repair: edit the AI draft to match the untouched human section, or filter pairs the
     way Smaug does.
2. **Pairing.**
   - For all-notes drafts it is feasible but imprecise: 4% of sections fail, and 14 to 16% of matched content lands
     in the wrong section.
   - For half-dose drafts it is poor: 19% fail, and 23 to 29% is misplaced.
   - Simpler options, in order:
     - drop the half dose;
     - prune against the whole draft;
     - train whole-post pairs on the 8K arm and generate by forced-prefix continuation, which needs no alignment.
3. **Context.**
   - It may help duplicated transitions. The restarts come from B30 never seeing a mid-post target, which mid-post
     pairs fix without context.
   - The real risks are not the mismatch. They are the Guard licensing invented names from the context, the prune
     deleting back-references, and the token budget (finding 6).
   - Test forced-prefix continuation with B30 first.
4. **Development evaluation.** Not reliable enough to pick a winner. The power is about 0.24 for a true halving, and
   the gate is reached about 2% of the time (finding 1). The gate is probably set too strict for 12 posts and has no
   positive control, and the coverage gate has no validated instrument.
5. **Pangram, the reserve and confidentiality.**
   - No Pangram selection within R2 as written. Pre-register the single test-A scan.
   - No path from the reserve or test-A into training.
   - Exclude B34's 8 B posts from the development set.
   - No confidential material.
6. **Compute and calls.**
   - Compute is fine: B30 took 38 minutes on the PC.
   - Claude calls are about 7,700 to 8,000, not about 2,700 (finding 8).
   - The cheapest path is below.
7. **Cheaper fixes first.** Yes. The cheaper fixes are below.

## Cheapest path to the decisive answer

The decisive question is whether a full-length rewrite can be faithful and coherent and still read Human. R2 bets
thousands of calls on "yes" without having tested it.

1. **Now, with no GPU: the repair test on A1's existing outputs** (about 100 to 150 Claude calls, about 450 credits;
   a route decision under decision 7).
   - Take the 30 C100 texts.
   - Restore deleted sentences that a kept sentence refers back to; the raw generations are on disk.
   - Reinsert code blocks.
   - Have Sonnet fix only the reader-flagged spans with minimal edits (for example at most 3 words per fix, plus
     inserting dropped names).
   - The reader re-reads 10 of the texts with the same rubric, and Pangram scans all 30 once.
   - What the result means:
     - If they stay at 22 of 30 or more and read clean, B30 plus a repair pass is a product path with no training.
     - If they fall, a measured amount of faithfulness costs the Human verdict. R2 then needs a generator that is
       faithful by itself, and the budget for its edits is known.
2. **Now, with no GPU: re-pick from the existing 4 seeds** (328 raw samples on disk). The reader rates every seed on
   about 8 posts. This measures how much better the best of 4 is than C1's pick. If the best of 4 is already near
   the gate, the fix is a better selector (adjudicated claims, a number and name diff, an antecedent check), not new
   training.
3. **When the PC or December's Modal credit is available: a zero-training bake-off** on 24 development posts, with
   the powered rule from finding 1 (about $2 to $4 of Modal, about 1,500 to 2,000 calls). Two variants:
   - B30 with forced-prefix continuation, number words in the Guard, no silent deletion, a higher token cap, and code
     and headings as fixed blocks;
   - Smaug-Humanizer on D100 in 500-word chunks. `experiments/modal/a1_smaug.py` already exists and needs only a
     prompts file.
4. **R2 only if all three leave a gap**, and with these changes:
   - all-notes drafts only;
   - source repair instead of target deletion;
   - a prune against the whole draft;
   - the context ablated against mid-post pairs without context;
   - whole-post pairs on the 8K arm;
   - the pilot's audit reads 10 targets for coherence, not only for alignment.

**At the outcome level:** whatever R2 achieves on dense notes from Common Crawl posts, P1 (Henry's real notes,
technical posts) remains the test of the goal. A2-redteam-a1 finding 9 still applies: his drafts may look like the
half-dose drafts, not D100.

## What I could not verify

- **Claude's real prune deletion rate on targets.** I used lexical TF-IDF matching, which undercounts paraphrase,
  so the deletion share and the alignment errors are directional, not calibrated. The 40-post pilot measures them.
  Even there, coherence needs a reader, not only a deletion rate.
- **The power simulation's inputs.** Reader recall (0.7), false positives (0.3 per post) and overdispersion are
  assumptions. The base counts are my tally of the reader's free-text items, not a fixed rubric.
- **The sort of invention by type.** It is mine, from the reader's descriptions.
- **Restarts.** That the restarts come from the opening-only training is inferred from the data shape and B36's
  12 of 52. I did not generate a test.
- **Forced-prefix continuation and Smaug on D100.** Their quality and Pangram behaviour are untested.
- **The Guard's role** in "$2012" and the missing age is inferred from the Guard's rule and the reader's description
  of the drafts. I did not replay decoding.
- **Wall time per Claude call.** It is taken from the design's own estimate, not from cache timestamps.
