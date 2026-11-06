# Outside judge: B32 pilot corpus (site split, earlier-corpus leakage, dates, genre tags)

Saved verbatim from the outside-judge agent's final report, 2026-11-06 about 03:10 CST. It was given the corpus
script and rules (`experiments/modal/lf_corpus.py`), the pilot metadata and sample (`results/b32_pilot_meta.jsonl`,
`results/b32_pilot_corpus.jsonl`, `results/b32_pilot_summary.json`), the earlier corpora (`data/*.jsonl`) and six
claims; not the head session's reasoning. Its scripts and downloads are in the session scratchpad `work/`. Its
fixes are adopted in the design doc (section 5.1 and the amendments) for the full build.

## Report

B32 pilot corpus audit. I read no text from earlier runs and wrote nothing into the project.

1. Splits: VERIFIED. I recomputed site_key for all 15,132 URLs with tldextract 5.3.0 and got 0 mismatches. I
   recomputed the split with my own sha256 code, and with shasum on a few sites: 0 mismatches. No site is in more
   than one split (train 12,135, dev 1,492, test 1,505).

2. Earlier-corpus sites forced to train: VERIFIED as coded, but the intent is REFUTED once. The data/*.jsonl files
   give 2,303 URLs on 1,498 sites. 46 pilot documents sit on those sites and all 46 are in train; 7 of them would
   otherwise have hashed to dev or test. The breach: p5236cb6dfb (test, broeder10.blog) is the same blog as
   broeder10.wordpress.com from data/human.jsonl. A Wayback capture from 2022-01-26 shows a 301 redirect from one to
   the other.

3. Site key: PARTLY REFUTED. www vs non-www, http vs https and blogspot country domains all collapse correctly; I
   tested them directly, and all 757 blogspot URLs are .com anyway. Under-grouping does happen. I grouped keys by
   their core name and found 32 groups with more than one key; I judge about 27 to be the same owner. 11 groups span
   splits, and 10 of those look like the same site:
   - wordpress.com vs own domain: ovunquesiamoweb, gabriellechana, hiddenharmonyworld
   - substack vs own domain: billytownsend, andrewsullivan
   - different country endings for one site: theregister, heyrick, commongunsense, mollyfield, stankovuniversallaw

   I confirmed 6 with outside evidence: three live 301 redirects and three sites that link to each other. So at
   least 10 of the 2,997 dev and test documents have a same-owner document in another split. That is a lower bound,
   because name matching cannot catch renamed blogs. With more shards and more than one document per site, the full
   build will have more.

   Medium: 34 keys, no name collisions. Whether the same author writes under both a publication and an @user page is
   UNVERIFIED (it needs bylines).

   Other site_key findings:
   - Platform names are matched as substrings, which produces wrong keys. p0dfec67d35 gets
     "drsharifahblogspot.wordpress.com.blogspot" and pb0bf9bfb90 gets "mamilblogspot.com.blogspot".
   - Blogs at user.medium.com, home.blog and netlify.app are lumped into one key per platform. This loses data rather
     than leaking it.
   - Scraped copies mean the site is not the author. p7cb0742b99 on pavvydesigns.com is Florens Verschelde's
     fvsch.com article (confirmed by web search).

4. Near-duplicates in the 400 sample: VERIFIED. I compared all 79,800 pairs. The highest word 5-gram Jaccard is
   0.0015 and none reach 0.5. This test is weak: only 67 of the 400 are dev or test.

5. Dates: VERIFIED. All 15,132 capture dates are before 2022-11-30 (latest 2022-08-20) and fall inside each dump's
   crawl window. I drew 10 documents with random.Random(20261106).
   - Common Crawl: all 10 records are in the index; the WARC-Record-ID matches FineWeb's id and the WARC-Date matches
     its date; 96.7 to 100% of the 5-grams appear in the WARC HTML.
   - Wayback: 8 of 10 have a separate capture before the cutoff with 96.7 to 100% overlap (earliest 2011 to 2021).
   - p7cb0742b99 and p426f666ca3 only have a Wayback capture with exactly the Common Crawl timestamp. The Wayback
     Machine took those copies from Common Crawl, so they are not a second source.
   - Blind spot: a pre-ChatGPT date does not mean human-written. pbb8bbfeedc is spun spam captured in 2022, and
     p3af89280af is an auto-generated video-transcript page.

6. Genre tags (seed 6062026).
   - tech: 12 of 20 are real technical posts, 60% (95% interval roughly 39 to 78%). 4 of the 12 are company blogs and
     2 lean on affiliate links. 3 are real blog posts on other subjects (pba08bffe98 physiotherapy, p7479fb737a
     philosophy, pc3aca5c1e9 a firearm review). 5 are not blog posts: a news-style article (p2f3d40e2ae), spun spam, a
     video-transcript page, and two question-and-answer or interview transcripts (pef0c38ed0b, p1692b8176a).
   - personal: 13 of 20 are real personal posts, 65% (roughly 43 to 82%). The misses are a site's list of post
     teasers (pea5b30e658), two magazine pieces (p958ffd2d2f, p9ec47645cd), three company marketing posts
     (p8b4b83b13d, p7c5bde24cf, p7db5ddf264), and one post that is mostly quoted committee minutes (pacbb4e23ed). 4 of
     the 13 hits are archive or tag pages that join several posts together.

   Across all 15,132 URLs, 18.5% look like listing pages: date archives 1,249, tag, category or author pages 1,169,
   home pages 302.

Changes before the full build:
- Merge site keys before splitting: same name across .com and other endings, wordpress.com or substack versus the
  blog's own domain, redirects found in the crawl data, and @user versus user.medium.com. Run the earlier-corpus
  check on the merged groups too.
- Match platforms by domain ending rather than substring.
- Drop listing pages.
- Deduplicate texts across splits over the whole corpus at a looser threshold, and check for scraped copies.
- Filter out company, magazine and transcript pages, then measure tag precision on a labelled held-out set.
- Guard against machine-made text in 2021 and 2022 captures.

Not verified: author overlap that cannot be seen from URLs (Medium, people blogging under different names),
near-duplicates outside the 400 sample, the original source of p2f3d40e2ae, and whether the PSL used on Modal matches
mine.

Most important next check: run the merged-key split over the full corpus and count how many dev and test sites
change, including any that match earlier-corpus sites.
