# Long-form B38: can a local judge stand in for Pangram when picking rewrites?

For Henry, 2026-11-06, about 14:05. Full write-up: `results/REPORT-2026-11-04-lora.md` section 39.

## The answers

**1. A judge cleared the bar you approved, but it is not useful yet.** We trained two judges on the 1,534 texts Pangram
has already scored:
- J1: a simple model on top of five free detectors.
- J2: a fine-tuned small language model.

J1 cleared the pre-set bar. On rewrites it separates Pangram's Human from not-Human at AUROC (area under the receiver operating characteristic curve)
0.735, against a bar of 0.70. On rewriters it was not trained on, it drops to 0.62.

**2. On 4 fresh posts, picking with J1 looked good at first.**

| Pick 1 of 4 tries per section (14 sections) | Average share Pangram flags as AI |
|---|---|
| Random try | 34% |
| J1's pick | 22% |
| Best possible pick | 16% |

**3. Then the checks took most of that away.**
- **J1 picks texts that lose content.** Its picks keep 60% of the words. 8 of its 14 picks break the content rules: claims
  not supported, or under half the words. Pangram rewards that too, since cutting text removes flagged words.
- **With the content rules kept, J1 is no better than what we had.**

  | Pick 1 of 4 tries, content rules kept | Average share flagged |
  |---|---|
  | Random try | 34% |
  | J1 (trained) | 29% |
  | Copies least from the AI draft (free, from gate 2a) | 29% |
  | One free detector (MELD), no training | 26% |
  | Best possible pick | 21% |

- **The bar measured the wrong thing.** The 0.735 mostly tells experiments apart. A score that only knows which
  experiment a text came from does better (0.78). Picking needs a judge that ranks the tries of one section, and none of
  our labelled data had that.

**4. Picking alone cannot reach Human on these posts.** A whole post reads Human under 10% flagged. With J1's picks, 1 of
4 posts reads Human. A random pick gets that same post to Human 7 times in 8. Even the best possible pick leaves the
other 3 posts at 16%, 20% and 25%. Whole-post figures are added up from the section scans, not scanned whole.

**5. The clearest signal is copying.** The more of a try's words come straight from Sonnet's draft, the more Pangram
flags it. It is the best single predictor we have (correlation 0.70), and it costs nothing.

**6. Your bandits post: the math was the difference.** Scanned in the same batch:
- with the math kept, it is Mixed at 41%;
- with the math stripped, it is Mixed at 24%, the same as the earlier scan.

So the earlier 41% against 24% was the math, not scan noise.

## What this means for the program

- The judge is not ready to replace Pangram for development, and best-of-4 is not the lever. The rewriter itself has to
  write sections that read more human; copying less from the AI draft is the clearest direction.
- The final test set (798 posts, locked by hash) is untouched. Nothing was trained, picked or scored on it.

## If you want the judge pursued

The cheapest test of whether any judge beats the free rule:
- 4 tries for sections of about 16 more posts, about $1 to $2 of Modal (inside the free credit);
- Pangram scans only where the judges disagree, about 350 to 500 credits.

Without that test, judge work should stop here.

## Checks and spend

- **Checks:** three independent checks.
  - Every number was recomputed from the raw files.
  - The order of steps was confirmed from git and Modal's server times.
  - No leak from the final test set or the test posts. One small cross-fold overlap moves the result by 0.002 at most.
  - A red team found the content-loss and no-better-than-free problems above.
- **Spend:**
  - Pangram 362 credits (9,079 to 8,717 left).
  - Modal about $1.60, with $20.99 of the $30 monthly free credit used and $0.00 billed.

## Also noted

The form checks should also catch leftover placeholder math such as "$Rewrite{n}$". The bandits rewrite that read Human
at 8% had broken sentences and a garbled proof, so it is not publishable as is.
