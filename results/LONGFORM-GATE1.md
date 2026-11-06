# Long-form gate 1: does B30's rewriter work on whole posts by new writers?

For Henry, 2026-11-06, about 11:10. Full write-up: `results/REPORT-2026-11-04-lora.md` section 37. Design and
amendments: `docs/specs/2026-11-06-longform-program.md`.

## The answer

**Not at full length. It moves every post toward human, but almost none clear Pangram's bar.**

- **The test.** 32 long blog posts (1,500 to 3,000 words) by writers the rewriter never saw. The sites are in no
  training data of the project, and every post predates ChatGPT. Sonnet wrote each post from half the author's notes,
  and B30's rewriter rewrote it section by section. All texts were scanned blind.
- **Sonnet's posts:** 0 Human, 13 Mixed, 19 AI. Mean AI share 0.81.
- **The rewrites, whole:** 1 Human, 31 Mixed, 0 AI. Mean AI share 0.38. The share fell on all 32 posts, but Human
  needs at least 90% of the text labelled human.
- **The same rewrites, first 300 words only:** 11 Human of 32.
- **Real human posts:** Human 10 of 10 at 300 words and at full length. Length does not make human writing look AI.

**Why whole posts fail.** Each 300-word stretch of a rewrite reads Human about a third of the time. A 1,400-word post
needs every stretch to pass, which predicts about 2 of 32. We observed 1. B30's short posts by known essayists passed
at about 0.8 per stretch. At that rate, about 18 of 32 whole posts would read Human. So the gap is the quality of each
stretch, and length multiplies it.

**What drives the leftover AI share:**
- how AI-like Sonnet's input was;
- how much of it the rewriter copied: 32% of its words, against 13% in B30;
- the pick rule, which keeps the seed with the most supported claims and so tends to keep the one that copies more.

## Your two posts

**Neither whole post reads Human yet:**
- context-engineering post: AI share 0.55 before, 0.40 after;
- bandits post: 0.41 before, 0.13 after, just above the 0.10 line.

**By section, 5 of 12 rewritten sections read Human; none of the originals did.** 8 sections improved and none got
worse.

**Cautions:**
- Half of the "before" labels come from B15's scan a day earlier.
- The rewrites are shorter.
- Much of the context-engineering rewrite is your own wording.

**Confidentiality:** nothing medical beyond your original wording and no client detail was introduced (checked by an
independent audit).

## Problems found

The claim check missed two bad texts and some invented framing:
- 40 lines of invented code;
- three paragraphs of garbled French;
- section openings like "This is the second of three articles".

Language, code and format checks have to be added before any further run.

## What this means for gates 2 and 3

The rule fixed in advance says that if the rewriter does not transfer, long-context training is next. The red team
sharpened that: a longer context alone will not fix it. Each stretch has to read Human about 80% of the time. My
recommendation is to split gate 2:

- **Gate 2a, cheap, about $5 of Modal and 0 to 800 credits.**
  1. Re-pick the rewrites already generated, with a penalty for copying and more seeds, judged by the open detector
     (MELD) and the local checks. This is nearly free.
  2. Run the notes-first voice writer (B28's L, Human on 11 to 17 of 19 at about 600 words) on the same 32 posts at
     full length. This shows whether writing from your notes holds up at length.
  3. Scan with Pangram only on fresh test documents, and only if the development measures improve.
- **Gate 2b, the original gate 2, about $40 to $55.** Train a long-context rewriter on thousands of writers, only if
  2a shows the per-stretch rate can move.
- **Gate 3, the final test.** Its size and endpoints get re-fixed from B36's measured spread.

## Spend

| Resource | Gate 1 | Program so far | Cap |
|---|---|---|---|
| Pangram | 1,715 credits (dashboard 11,349 to 9,634) | 1,715 | 2,500 for this gate |
| Modal | about $3.70 | about $4.80 | inside the free credit; no paid money used |

## Not verified

- How Pangram aggregates its windows exactly.
- Whether "unseen writers" or "obscure genre" is the cause: B30's writers were famous essayists.
- How much of the length effect comes from section joins.
- How large the length effect really is: its significance is fragile.
