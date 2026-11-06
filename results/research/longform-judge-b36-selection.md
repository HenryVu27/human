# Outside judge: B36 test-A selection (leakage, page type, dates, selection order)

Saved verbatim from the outside-judge agent's final report, 2026-11-06 about 09:40 CST. It was given the selection
rules and code (`experiments/b36_transfer.py`), the selected and reserve posts (`results/b36_docs.jsonl`), the pilot
corpus, the Haiku labels, the earlier training corpora and five claims; not the head session's reasoning. Its
scripts are in the session scratchpad `work/b36audit/`. Action taken: the three failing posts were excluded and
replaced by audited reserve posts (amendment in the B36 docstring), before any test-A rewrite or scan.

## Report

B36 selection audit. I did not edit any project file.

1. Site and owner separation: REFUTED once.
- All 32 sites are alone in the pilot under two groupings: the code's core_name and my own (a wider platform list
  plus country domain endings).
- No test site name appears in any other pilot URL or in the 2,351 URLs in data/*.jsonl. No near-match names either.
- I searched author and blog names across all pilot texts and data/. The breach: p67cdcd8668 (kristinastanley.com)
  is a guest essay by Cathy Ace. She also writes most of train-split post p63f2c1fcb6 (kateeileenshannon.com,
  bucket 16), an interview from her book tour.
- B30's 13 authors share no site with the 32. "Robert Scoble" appears in one of Spolsky's essays, but only as a
  subject.
- Live web: storyempirecom.wordpress.com now redirects to storyempire.com, which the merge rule would not join.
  "storyempire" appears nowhere else in the pilot or data/, so nothing leaked.
- A web search says the Medium post p25679086d9 is by Gabriele Fazio (TUI MM Engineering). That name appears nowhere
  else.

2. Near-duplicates: VERIFIED. I compared exact word 5-gram sets. The largest share of any test post found in another
pilot post is 0.0041. Against 13,890 training texts in data/ (all subfolders) it is 0.0026.

3. Page type: REFUTED, 3 fail.
- p6d59a3ce68: a Singletrack magazine staff review ("Tested: by David Hayward").
- p899ba31bed: an NJIT student-newspaper review with a byline.
- p67cdcd8668: host intro, guest essay and third-person bio, so not one author.
- Borderline, one author but published by an organization: p3a84b9ccbc (school principals' association blog),
  p25679086d9 (company engineering blog), pd870408b22 (golf-coaching business), pd3f07c3e66 (multi-author gaming
  site).
- pa5fd792f87 ends in a 474-word sidebar tag cloud. The post itself is about 1,498 words, under the 1,500 floor.
- pa2b84bf758 is a /2009/11/21/ day-archive URL; the listing rule misses /YYYY/MM/DD/. The Common Crawl page holds
  one article, so its text is a single post.
- I saw no spam or machine-made text.

4. Dates: VERIFIED.
- FineWeb dates for all 32 run from 2019-08-17 to 2022-08-19. URL, dump, date and text match the pilot exactly.
- Sample: random.Random(20261106).sample(range(32), 10).
- Common Crawl index plus a byte-range fetch of the archived page, 5 of 10: pa2b84bf758, p01004974c5, p3bfd623027,
  p827b1c285d, p8fb3502483. Record ID and WARC-Date equal FineWeb's, and 99.3 to 100% of each post's 5-grams are on
  the page.
- The index returned 504 errors for the other 5 on all three tries. Each has an earlier Wayback capture before the
  cutoff with the text present: pbfd12ded77 2019-07 (99.4%), p6d59a3ce68 2017-10 (97.7%), p2358c4bdee 2019-11 (100%;
  its earliest capture has Common Crawl's timestamp and was skipped), p4ad56d5750 2019-07 (100%), p4c5be6086d 2020-09
  (100%).
- The Medium post went up in March 2022 per web search: before ChatGPT, but during the GPT-3 years.

5. Selection: VERIFIED.
- Recomputed: buckets, merged groups, both versions of the listing rule, and exact Jaccard (no pair at 0.5 or more
  among the 523 candidates). Then the sha256("b36-v1:"+id) order.
- Labels cover all 136 candidates walked, with no gaps.
- The first 32 eligible posts held 4 technical posts. The last 4 personal posts (pc181d8f08b, pce9bcaba2a,
  p35b2004659, p10267ee0c0) were swapped for the next 4 technical ones.
- The result matches the file's 32 posts in order and all 61 reserve posts.
- Minor: core_name gives "global" for biblesociety.global, where the docstring rule would give "biblesociety". That
  post ranks 62nd and does not change the 32.

Not verified:
- Whether the labels are right beyond my own reading.
- Whether OLMo-2's pretraining data (DCLM, built from Common Crawl) contains these posts. "Never saw" here covers only
  the project's own data.
- Owners who blog under unrelated names.

Most important next check: replace p6d59a3ce68, p899ba31bed and p67cdcd8668 from the reserve and decide what to do
with pa5fd792f87. Haiku passed 3 non-blog pages out of 32 (about 9%), so hand-check the first reserve posts before
they move in.

## Follow-up: the reserve posts checked before replacement (same agent, about 09:45 CST)

4 of the 5 reserve posts pass; 1 fails:

- p35b2004659 (alienshore.com): PASS. A personal post on the 2006 Canadian election debate. Its site and names appear
  nowhere else.
- pae98db1f7a (torunningchiro.com): PASS. A runner's own marathon recap; it ends by asking for charity donations. No
  overlap.
- p0970e31d18 (motleyvision.org): FAIL. The same publication's newsletter, buttondown.email/motleyvision (p3936c2b9d7,
  bucket 14, train), is in the pilot. The merge rule misses it because buttondown is not in its platform list. The
  site is also a multi-author group blog, and this post has no byline.
- pe9ea594c27 (sixfootcanasian.com): PASS, borderline. A personal food-blog round-up of Calgary Italian restaurants
  that plugs another site, so it leans promotional. The only other "Canasian" is a common word in an unrelated post.
- pa019a09e0e (bakersacres.blog): PASS. A personal story. Note it names and accuses a private individual.

None of the 5 matches anything in data/ or B30's 13 authors. The near-duplicate check was not run on these 5.

Action: the three excluded posts are replaced by p35b2004659, pae98db1f7a and pe9ea594c27 (the first three that pass,
in reserve order).
