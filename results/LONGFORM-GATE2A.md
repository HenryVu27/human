# Long-form gate 2a: did any cheap lever work, and is gate 2b worth paying for?

For Henry, 2026-11-06, about 12:35. Full write-up: `results/REPORT-2026-11-04-lora.md` section 38.

## The answers

**1. On the development measure, nothing moved.**

| Lever | Development rate (open detector MELD) | Cost to the post | Pangram test on fresh posts? |
|---|---|---|---|
| None (B36's pick) | 0.067 | none | n/a |
| Pick the rewrite that copies Sonnet's post least, from 4 tries | 0.066, no change | none: same length, claims 95% | no, did not qualify |
| Write from your notes instead (the notes-first writer) | 0.25, more human | only 28% of the post's length, claims 89% | no, did not qualify |

**2. The development measure cannot see what matters.** On rewrites, MELD agrees with Pangram little better than a coin
(AUROC 0.55). So "no change" mostly means "can't tell". The B33 calibration had looked fine because it mixed all kinds
of text.

**3. How Pangram adds up a long post (new, measured).** We inserted a Sonnet paragraph block into real human posts:
- When the block was 7% or 9.5% of the words, the posts still read Human.
- When it was 17%, they read Mixed.
- The AI share always equalled the block's share of words, wherever it sat.

So a whole post reads Human when under 10% of its words are flagged. Every section does not need to pass. B36's
rewrites had 38% flagged.

**4. Your posts, scanned the same day, with the math stripped from both versions.**

| | Original | Rewrite |
|---|---|---|
| Bandits post | Mixed, 24% flagged | **Human, 8% flagged** |
| Context-engineering post | Mixed, 53% | Mixed, 24% |
| Sections | 1 of 12 Human | 6 of 12 Human (8 better, 1 worse) |

- The bandits result is close to the line. Yesterday's version of the same rewrite read Mixed at 13%.
- On the context-engineering post, the new pick improved every section it changed. The 4 tries per section differ a lot,
  so choosing well clearly helps, but nothing we have locally can tell which try is best.

## Is gate 2b worth your money? Not yet.

Gate 2b trains a long-context rewriter at scale, for about $40 to $55. Two problems:
- **It would be built blind.** There is no local judge that tracks Pangram on rewrites.
- **It addresses only part of the gap.** By the red team's estimate, long context would remove about 0.09 of the 0.28
  between the rewrites and the line. The rest is how human each part reads for new writers, and nothing yet says
  training at scale fixes that.

Two cheaper steps first:
1. **Free.** Test every open detector and simple text feature against the roughly 150 rewrites Pangram has already
   scored. Keep anything that ranks them well (AUROC 0.7 or more).
2. **About 400 credits and $1 of Modal.** Scan all 4 tries of each section for 4 fresh posts. This measures how close
   picking the best try can get whole posts to 10%.

If (1) finds a judge and (2) shows real headroom, a pick-and-repair loop may beat training. If neither does, gate 2b is
the next bet, with a judge in hand.

## Also built

Form checks now gate every output: wrong language, invented code, "part two of my series" openings and invented
headings. They caught the bad texts the old claim check missed.

## Spend

- **Pangram:** 555 credits this gate; the dashboard is at 9,079.
- **Modal:** about $6 this gate. The month has used $19.6 to $20.2 of the $30 free credit, and $0.00 has been billed.
