# P1: notes kit for your next post

P1 tests the product on a real post: which drafting workflow gives you a post that reads as yours, reads human to
readers and Pangram, and costs you the least time (attempt-2 design, section 6.2). It needs one post you are about to
write, and about 30 to 60 minutes of notes from you before Claude drafts anything.

## Before you start

- **Pick the post:** one you would write anyway, 1,500 to 3,000 words. Topic and sources are your call.
- **Screen what goes in.** Your notes and sources go to Claude and to Pangram. Leave out anything about client work
  or anything you would not paste into those tools. For the context-engineering series, the client stays "diabetes
  coaching agent", in the post's own words, and nothing more.
- **Time yourself.** Note when you start and stop each step below. Time is one of P1's measures.

## Step 1: your notes, one block per section (timed)

Write a rough outline of sections first, then for each section answer these in your own words. Fragments are fine.
Do not ask Claude for ideas first: points you pick from a Claude menu likely still count as Claude's choice.

1. **The point.** What should a reader believe after this section that they did not before?
2. **Why you believe it.** What did you see, build, measure or read that convinced you? Name the run, the bug, the
   paper, the number, the moment.
3. **The sub-points.** The two to five steps of the argument, in the order you would say them at a whiteboard. This
   is the part that matters most: models flatten sub-arguments even when given the thesis.
4. **What you would push back on.** Where is the common take wrong, or where are you unsure?
5. **One concrete example** only you would use: from your own code, logs, notebook or a conversation.

**Recall prompts if a section feels thin** (from the cognitive interview and stimulated recall):
- Open the repo, notebook, results file or chat where you did this work. What does it remind you of?
- What surprised you? What did you get wrong first?
- If a colleague asked "so what?", what would you say?
- Walk through the timeline: what happened first, next, and what changed your mind?

**Also mark:** any section you will write yourself in full. Those are kept verbatim in every cell.

## Step 2: hand it over

Save the notes as `~/personal/human/data/p1/notes.md` (local, gitignored) with the sources you used beside it, and
tell the session. From there the session builds every cell without more of your time:

| Cell | What |
|---|---|
| C0 | Claude's draft as you draft today (topic and sources, no notes) |
| CN | Claude's draft from your notes |
| CNR | The rewriter on CN |
| LN | The notes-first local writer, section by section, from your notes |

## Step 3: read, then decide whether to write it yourself

- **Blind read:** you get the cells' sections side by side, sources hidden, and pick which you would rather publish.
  This takes about 30 to 45 minutes.
- **Optional R0:** you then write the post yourself from your notes, with Claude allowed to comment but not to write.
  This is the reference every tool has to beat, and it is the version you would publish if no tool beats it.
- **Scans:** every cell is scanned by section and as a whole post, in one blinded batch. The scan uses the prose-only
  form, and the best cell and C0 are also scanned as the full page with math and code. About 250 to 350 credits.
