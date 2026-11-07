# A2 reader check of A1 outputs (C100 and C50)

Date: 2026-11-06. Reader: Claude (Opus 5.5), read by hand against the input draft and the human original.

Goal behind the check: a rewrite counts only if it reads human, is better writing than its draft, and adds nothing.
Pangram verdicts and the automatic checks (claim support, copying, form) cannot see most of what is below.

## Sample and method

- C100: the first 10 C100 texts by doc id among those Pangram labelled Human (28 of 32 C100 texts are Human).
  Docs p01004974c5, p0f92b38ac3, p10267ee0c0, p25d4111207, p2a4982704f, p35b2004659, p3a84b9ccbc, p3bfd623027,
  p40c33738de, p4b8e886641. p35b2004659 is flagged excluded in a1_texts (copied_from_human 0.17).
- C50: the first 5 C50 texts by doc id: p01004974c5, p0f92b38ac3, p10267ee0c0, p1c9cb11d31, p25d4111207. All 5 are
  Pangram Mixed (ai_share 0.13 to 0.66).
- Each text read in full next to its full input draft (D100 for C100, b36_inputs D for C50). Human originals were
  skimmed, and searched wherever a rewrite had something its draft lacked.
- Mechanical aid (scratch script, not in the repo): 6-gram runs found in the rewrite and the human post but not in the
  draft; numbers and capitalised words missing from the draft; non-ASCII characters; repeated 8-grams; final 120
  characters. Every candidate it raised was then checked by reading.
- Not done: no Modal, no Pangram, no repo edits, no .env reads. Faithfulness was judged against the draft only. I did
  not check whether the drafts are faithful to the notes, and I did not fact-check the drafts against the world.

## Per-text findings

Quotes are single sentences from the texts.

### C100

**p01004974c5 (Social Business to Open Business; Human 0.07)**
1. Faithfulness: one small invented framing ("now that Social Business has become mainstream"). One logic flip: the
   draft's point that social tools have proven their value becomes "One is that social technologies have proven their
   value over and over again" as a reason why companies stall. It drops the series framing, Cushman's two titles and the
   closing invitation. Memorization: wording only ("rather successful in communications" matches the human post; the
   draft says "done fairly well").
2. Defects: the text cuts off mid-token, ending "a better category than HR 2." "Instead, I will use the terms Open
   Business" has no antecedent because the drop-the-labels sentence is gone. Also "Enterprise 2.o", "a Open Business
   Council", agreement slips, and spaces before punctuation ("CMSWire : Social").
3. Editor would publish the draft: it is complete and in order.
4. Reads human (a rambling enterprise blogger), but the text is unfinished.

**p0f92b38ac3 (Alaska trip; Human 0.00; 1 fallback section)**
1. Faithfulness: the first half is close to the draft. Echoes the human post's wording in places ("a research project
   on language"). Section 2 holds none of the draft's second half: Idle No More, the ANHC, the social stakes, the French
   loanwords, the Iditarod, Buser and the finale are all missing.
2. Defects: section 2 is a single mixed French/English sentence that opens "A l'Inside le Native Resource Center
   d'Anchorage". It is 0.49 of the draft's length. Also the non-word "accompanyists".
3. Editor: draft, easily.
4. Section 1 reads human. The ending is not English.

**p10267ee0c0 (Case for Obama 2012; Human 0.07)**
1. Invented or distorted: "promised him something like $2012" (the draft and the human post both say about two
   thousand dollars). "Jackson was a genocidal maniac" and "Jefferson had children that he sold as slaves" escalate the
   draft's claims. "Yes, I know, it's a policy reason" contradicts the draft, which frames temperament as a non-policy
   reason. The quit-smoking request becomes a voting reason. "President Obama has had a busy year" against the draft's
   three-plus years. Memorization: wording only, but heavy (bumper stickers, the "O" t-shirt sentence, "the Republican
   opposition was willing to", "appointed twice as many women to the").
2. Defects: at the section 1/2 join, "Let's look at some of them." is followed straight away by "Now, let's look at these arguments."
   "Here are some of the things I think the President has done well this year:" is followed by no list.
   "That hurts his base" points at nothing, because the deportation setup is paragraphs away. "He hasn't been in office
   for three years. He's been in office for just over three years." "If that's surprising to you, then the surprise is
   yours, not his" follows an Oprah sentence. The tax cuts are covered twice, and the dash style changes between
   sections. Drops Emo Progs, Larry Summers, Herman Cain, Libya and the closing callback.
3. Editor: draft.
4. Voice is convincingly human and the structure is broken.

**p25d4111207 (God's pressure pot; Human 0.00)**
1. Faithfulness: mostly faithful. "My mom and dad lived by their own rules" changes the draft's "lived by their own
   words" (they practised what they preached). "Our parents were a team" is a small addition. Drops the vine-pruning,
   iron-sharpens-iron and 1 Corinthians passages and the blog boilerplate (that last drop is good).
2. Defects: "The parents are the blunt iron that does not sharpen anyone" is left dangling, because the iron image it
   calls back was dropped. "They don't like themselves because of their inner integrity" (inherited from the draft).
   "My parents were raised with strict rules set by their parents, and they were raised the same way."
3. Editor: toss-up, leaning to the draft for completeness. The rewrite's folksy register is closer to the author's.
4. Reads human.

**p2a4982704f (Trophy hunting and Cecil; Human 0.00)**
1. Faithfulness: faithful in what it keeps. It drops fair chase, the pride and infanticide mechanism, the 30,000-lion
   and 15% figures, and the closing. As a result, "The reason for this is that repeatedly killing the cubs of a dominant
   male makes breeding difficult" now explains a 50% population rise, which makes no sense.
2. Defects: "I knew more about lions at age  than I knew about most things" (the number is missing).
   "No one is eating a family because they killed a lion". "Cecil the Lions". Section 2 restarts with "In the midst of
   some intense, emotional feelings, I've written about what I think of trophy hunting".
3. Editor: draft.
4. Reads strongly human. The errors look like a hasty blogger's.

**p35b2004659 (Canadian leaders' debate; Human 0.00; excluded for copying 0.17)**
1. Faithfulness: the rewrite reverses the author's preference. The draft prefers the first debate's audience questions,
   but the rewrite calls this debate "a welcome change from the first debate". Harper is never named ("His suit was
   perfect." starts his paragraph). Martin's handgun quote becomes the narrator's own words ("I'm saying that we have
   to ban hand guns."), with a stray closing quote mark. The human post carries the same unattributed quote, so this is
   memorized formatting, the copying that the 0.15 rule caught.
2. Defects: "Martin is a great leader, but is he a great leader?" (at the section join). "There are 500, ooo hand
   guns". "Martin, that your party has been one of the biggest recruiting agents for the Bloc" (a fragment that has lost
   its speaker). "Harper's GST cut" appears without the GST quote. The voting-dilemma conclusion that the first
   paragraph promises is gone.
3. Editor: draft.
4. Sentences read human. The piece does not hold together.

**p3a84b9ccbc (Black administrator in majority-white schools; Human 0.00)**
1. Faithfulness: close. Small changes: the Zoom call becomes a colleague who "looked at me". The draft's self-critical
   "harsh tone" becomes "I was tense". "I am tired." and "it was okay to be vulnerable" are added. Memorization: the
   rewrite recovers several of the human's idioms ("courageous conversations about race, equity, and inclusion", "pulled
   up a chair") where the draft had thesaurus swaps ("brave talks"). copied_from_human is 0.11.
2. Defects: minor. "And it's not just a leadership role." is a vague filler sentence. The opening is a little
   redundant.
3. Editor: the rewrite, narrowly. It uses the real idioms and reads less like a paraphrase, though some of that edge
   comes from the human's own wording.
4. Reads human.

**p3bfd623027 (Mapping North Korean sites; Human 0.00)**
1. Faithfulness: Curtis Melvin goes unnamed, then appears as "My colleague Melvin", an invented relationship. The rewrite
   overclaims ("My goal has been to map all of the archaeological sites in North Korea, and I have been able to do
   this"; the draft says he viewed every square mile). "about 300" temples left where the draft has "under 300". It
   drops "Why this history matters" and the 1,009-year unity figure.
2. Defects: "The first is a list of 113 sites ... The other is from the work of Sarah Parcak" (no lists were
   introduced). "I have marked all 98 sites in North Pyongan Province (the most of any province) and 71 of them."
   Scrape-style spacing ("11 th century", "download it directly here .").
3. Editor: draft.
4. Reads human (a hobbyist researcher).

**p40c33738de (DIY breath acetone detector; Human 0.00)**
1. Invented: the rewrite says the author compared Ketosense "to values measured by a device that measures the amount of
   acetone in my breath (which I'm calling a reference device)". The draft and the human post use urine strips
   (Keto-Diastix), and the draft says plainly that no better reference was available. The urine strips then appear
   unexplained near the end. It swaps two values: "I used the values 60 and 28 for temperature and humidity" (60 is
   humidity, 28 is temperature). The molar mass of 58.08 becomes 58.0. The draft's caveat ("I won't say the instrument
   is functional") is gone.
2. Defects: every formula lead-in is left hanging. "Here's the one I used:", "I used the following scaling function:"
   and "Here's the new scaling function:" are each followed by nothing, because all six code blocks were dropped. A
   "Results" heading sits over hardware notes. Section 2 is one paragraph of about 600 words. Section 3 restarts the
   post ("So I decided to make a ketone breath tester out of an Arduino."). No code was invented.
3. Editor: draft, clearly.
4. The sentences read human. As a build log it is unusable and in one place false.

**p4b8e886641 (Foreshadowing in fiction; Human 0.00)**
1. Invented: the author's rough-draft excerpts are recast as quoted fiction with new dialogue ("The sun is shifting,"
   she said.), and Knight's interior thought becomes a spoken question. The draft paraphrases these excerpts and the
   human post's wording differs, so the rewrite has made up text from the author's own manuscript. "and then beats him
   up" for Eowyn killing the Witch-king.
2. Defects: section 2 opens "We see the father's anxiety and unease about the circus". Bradbury, Something Wicked This
   Way Comes, Will and the lightning-rod setup were all dropped, so the reader cannot know which book is meant.
3. Editor: draft (the reference is missing and the excerpts are invented). Sentence for sentence, the rewrite's prose
   is pleasant.
4. Reads human.

### C50

**p01004974c5 (Mixed 0.41)**
1. Faithful. One wrong value: "HR 2013" for the draft's "HR 2.0". No memorization (one 6-gram).
2. Defects: few. Spacing artifacts ("( The first two were", "21 st century").
3. Editor: toss-up. It is tighter than the draft and keeps the draft's aphoristic beats ("Resources are things you
   manage and consume.").
4. Mostly human. Those beats are the draft's cadence, which fits the Mixed score.

**p0f92b38ac3 (Mixed 0.66; 1 fallback section)**
1. Invented: "I came from Geneva, where it was 36 degrees Celsius". The draft has Geneva only a degree or two warmer
   than Anchorage, and 36 belongs to the Asia leg. "I went to Alaska in the winter, and the temperature was very cold"
   contradicts the draft. A fabricated quote: "Rochelle's words have been in my mind ever since: 'If a language can wake
   up, then perhaps a community can too.'" (the draft gives this line as the narrator's reflection). Buser is credited
   with a claim that the draft makes as the narrator's inference ("He said that the Swiss precision helped him to
   succeed"). Rochelle is never introduced before "I learned from Rochelle".
2. Defects: "It's a modern city, but it's not like other cities in the world." follows "It's like a city anywhere else
   in the world." "Alaska is a beautiful place." is filler. Section 1 is thin.
3. Editor: draft.
4. Reads like a weak student essay, not like this author.

**p10267ee0c0 (Mixed 0.30)**
1. Invented framing: "In today's column , I argue". "I voted for Obama four years ago" is added.
2. Defects: section 1 is scrambled. "So they're not happy with Obama." comes before any "they". "What have they got
   against Obama? That one is easier to understand. I'm a registered Democrat." does not follow. "Who should we replace
   him with? That's the key question." comes right before a promise not to compare him with opponents. "I'll give you
   another one here." refers to nothing. "Because if you do the latter, you're just blowing smoke." has no "latter".
   "then you need to explain how President Reagan was" inverts the logic. The final third is near-verbatim draft.
3. Editor: draft.
4. Mixed: the sections that read human are the broken ones.

**p1c9cb11d31 (book review; Mixed 0.34)**
1. Faithful. Nothing invented. No memorization.
2. Defects: three wall-of-text paragraphs. At the dropped "Jacob" heading, "He is one of my favorite characters." follows
   sentences about the President, so it reads as the President. Section 2 opens "She starts to explore her jewelled
   princess side" with no name. "I really hope you read this series, especially if you've read books one through six."
3. Editor: draft (structure and referents).
4. Reads like a gushing fan reviewer, which fits the genre.

**p25d4111207 (pressure pot; Mixed 0.13)**
1. Distortion: "I believe that my husband and I were like this, too." follows the blunt-iron parents, so it says the
   opposite of the draft (they parented the firm way). The Proverbs citation is dropped and the verse is left as two
   unattributed fragments. The "whoopin'" release passage, central to the metaphor, is dropped.
2. Defects: the last section is one paragraph with 21 "I believe" (the draft has 4), a loop. "I believe that God is
   not pleased" and "God is unhappy with the way that we parent today" repeat each other. Section 2 is short declaratives
   on a loop ("They told us to do things. They did them. They told us things were wrong. They did not do them."). The
   ending is abrupt.
3. Editor: draft.
4. Section 1 reads human. Section 3 reads like a chant.

## Rates

| Problem | C100 (n=10) | C50 (n=5) |
|---|---|---|
| Substantive invented fact, quote, number or framing | 5 (p10267, p35b, p3bfd, p40c, p4b8) | 2 (p0f92, p10267) |
| Meaning inverted or distorted | 4 (p0101, p35b, p40c swap, p2a49 mechanism) | 2 (p25d, p0f92) |
| Any of the two rows above | 7 | 3 |
| Memorized human content (facts) | 0 | 0 |
| Memorized human wording or format (noticeable) | 3 (p35b, p3a84, p10267) | 0 |
| Broken or garbled sentences | 8 | 4 |
| Truncated or unfinished, or content left dangling ("Here's the function:" with nothing) | 6 (p0101, p0f92, p10267, p25d, p35b, p40c) | 2 (p25d, p10267) |
| Abrupt section join (lost referent, restart, duplicate transition) | 6 (p0f92, p10267, p2a49, p35b, p40c, p4b8) | 4 (p0f92, p10267, p1c9, p25d) |
| Loop or restart | 2 (p40c restart, p10267 repeated material) | 1 (p25d, 21 "I believe") |
| Non-English run | 1 (p0f92) | 0 |
| Editor prefers the rewrite | 1 (p3a84), 1 toss-up (p25d) | 0, 1 toss-up (p0101) |
| Reads like a person at sentence level | 9 | 3 |
| Publishable as is | 0 | 0 |
| Publishable after a light copyedit | 2 (p3a84, p25d) | 1 (p0101) |
| Needs moderate edits but no restructuring | 2 (p2a49, p3bfd) | 1 (p1c9) |
| Unpublishable without going back to the draft | 6 (p0101, p0f92, p10267, p35b, p40c, p4b8) | 3 (p0f92, p10267, p25d) |

Small samples: these are counts, not estimates. The C100 sample is the Human-labelled subset, which is 28 of 32.

## Answers

Are any Human-labelled C100 texts unpublishable? Yes, 6 of 10 as written, and none are publishable without edits. The
worst cases all scored Pangram Human with ai_share 0.00. p40c33738de invents its reference instrument and drops every
formula. p0f92b38ac3 ends in garbled French at half length. p35b2004659 reverses the author's opinion and turns a
quoted politician into the narrator. p4b8e886641 invents dialogue from the author's own novel.

Is C100 better writing than D100? In 1 of 10 cases (p3a84b9ccbc), helped by recovering the human's own idioms.
Elsewhere the rewrite's single advantage is register: it sounds like a person. It pays for that with lost structure,
lost content and new errors.

## Patterns

1. Section joins are the main failure point. Each section is rewritten without the previous one, so section 2 or 3
   opens on a pronoun or a callback whose referent was in the dropped heading or the prior section's lost lines. This
   happens with Harper, Bradbury, Jacob, Rochelle and the "blunt iron" image. Other joins restart the post (p40c, p2a49)
   or duplicate a transition (p10267). An outcome-level fix: give the rewriter the previous section's last paragraph
   and a list of introduced entities, and add a check that every proper noun or pronoun in a section's first two
   sentences has an antecedent.
2. Dropping content creates dangling text. The claim check scores the rewrite's claims against its section, which
   measures precision. Omissions go unpenalized above the half-length floor. Median length ratio is 0.83 (C100) and 0.81
   (C50), with a minimum of 0.49. The dropped material leaves behind lead-ins with nothing after them ("Here's the new
   scaling function:"), explanations of facts that are gone (the cubs mechanism) and promises never kept (the debate
   post's "why I still don't know who to vote for").
3. The fabrications are specific and plausible: a reference device, quoted dialogue, a colleague, a dollar figure, a
   Geneva temperature, a quote moved into another person's mouth. Every one sits in a text with claim support of 0.93
   or more (p40c: 101/108, p0f92 C50: 35/45 with a fallback). One unsupported sentence in a section barely moves a
   ratio.
4. The errors look human, and that may be part of why texts score Human. Missing words, run-ons, stray quote marks,
   spaces before punctuation ("CMSWire :", "11 th", "here ."), "2.o", "500, ooo". These look like web-scrape artifacts
   from the base model's training data, not AI polish. Whether sloppiness drives the Human verdicts is untested (see
   the open question below).
5. Memorization shows up as wording and format, not facts. I found no fact taken from the human post that was missing
   from the draft. The rewriter does pull the human's phrasing back (p3a84, p10267), and in p35b it reproduced the
   human's unattributed quote, the case the 0.15 rule excluded. C50 shows almost none, as expected with half the notes.
6. C50 rewrites copy more of the draft's cadence: near-verbatim closing sections in p10267 and p0101, and the draft's
   aphorisms. That fits their Mixed labels. Where C50 departs from the draft it breaks (p0f92, p25d), as C100 does.

## Findings beyond the brief (with evidence)

- **B36 selection assumption is violated.** The a1_content.py docstring says these posts "carry no code or math by
  B36's selection". p40c33738de's D100 has 6 fenced code blocks, its D50 has code, and the human post has code. The
  scoring-form check passed because the rewrite dropped the code, so the check could not see it.
- **The automatic checks miss every severe problem above.** Claim support, form checks and copied_from_input passed
  p40c (invented reference device, no formulas), C100 p0f92 (French sentence, half the length) and C50 p0f92
  (fabricated quote). Only the copying rule caught p35b, and it caught it for copying, not for the inverted opinion or
  the misattributed quote.
- **Possible selection pressure, a hypothesis:** C1's pick prefers the least-copying candidate that passes. If the
  candidates that diverge most from the draft are also the most garbled, or the ones that echo the human, the pick
  favors them. This could be tested by reading all 4 seeds for a few sections.

## What I could not verify

- Whether the Human verdicts come from the defects (sloppiness reading as human) or from register. That needs Pangram
  on copyedited versions of the same texts, which I did not run.
- Whether the drafts themselves add material beyond the notes (C50 draft p0f92 has invented color such as "zipped up
  my coat"). I judged rewrites against drafts only.
- The 18 remaining Human-labelled C100 texts and 27 C50 texts are unread. The rates above are from 15 texts.
- Historical facts in the posts (Korean dates, Obama record) were not checked against outside sources. Only
  draft-to-rewrite changes were checked.
