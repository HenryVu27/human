# A2 blind reader: p2a read pack (20 items, 10 docs)

Reader: one blind model reader (Claude Opus 5.5), 2026-11-07. Inputs read: results/p2a_read_pack.jsonl (20 items) and the D100 field of results/a1_d100.jsonl (the draft for each doc). No other repo file was opened. Each item was read whole against its draft. Pair membership was not used to judge which item is which; within each pair a sentence diff was run only to make sure every differing sentence got scored.

## Rubric (applied the same way to every item)

- invented: each distinct claim, number, name, value, stance, preference, quote or attribution the draft does not give, or gives differently. Counted once per distinct item. Included: changed values (58.0 for 58.08), changed causes or causal links, new reasons or lessons, new relationships ("my colleague"), pronouns the draft never gives, value words the draft does not use ("barbaric"), and hedges dropped from harsh generalisations about people. Not counted: close paraphrase, small intensity shifts, or extra filler with no new content.
- garbled: each sentence that is ungrammatical beyond style, cut off, looping, word salad, or in the wrong language. Typos and run-ons are not counted.
- joins: each place the text restarts as a new post, points at something never introduced (including "Here's the one I used:" followed by nothing, "pictured above", "here" links that do not exist), promises something it never delivers, or jumps with no connection.
- dropped: each paragraph-level draft point, code block or list missing entirely. Partial paraphrase counts as kept. Adjacent paragraphs on the same point count as one.
- publish: would a careful editor publish this item rather than the draft as written.

## Table

| item | doc | words | invented | garbled | joins | dropped | publish |
|---|---|---|---|---|---|---|---|
| 0 | p1c9cb11d31 | 917 | 6 | 0 | 2 | 7 | no |
| 1 | p40c33738de | 1699 | 6 | 1 | 10 | 10 | no |
| 2 | p01004974c5 | 1150 | 3 | 1 | 3 | 6 | no |
| 3 | p0f92b38ac3 | 594 | 4 | 1 | 3 | 10 | no |
| 4 | p3a84b9ccbc | 1411 | 2 | 1 | 0 | 2 | yes |
| 5 | p2a4982704f | 1004 | 3 | 2 | 2 | 5 | no |
| 6 | p25d4111207 | 1325 | 1 | 2 | 3 | 6 | yes |
| 7 | p4ad56d5750 | 1552 | 4 | 0 | 3 | 1 | no |
| 8 | p3bfd623027 | 1337 | 4 | 1 | 3 | 2 | no |
| 9 | p3bfd623027 | 1371 | 8 | 1 | 4 | 2 | no |
| 10 | p3a84b9ccbc | 1450 | 3 | 1 | 0 | 2 | yes |
| 11 | p25d4111207 | 1354 | 4 | 2 | 2 | 6 | yes |
| 12 | p0f92b38ac3 | 588 | 3 | 1 | 3 | 10 | no |
| 13 | p10267ee0c0 | 1815 | 10 | 2 | 3 | 5 | no |
| 14 | p4ad56d5750 | 1515 | 1 | 0 | 1 | 1 | no |
| 15 | p10267ee0c0 | 1802 | 8 | 1 | 1 | 5 | no |
| 16 | p2a4982704f | 972 | 1 | 0 | 1 | 5 | no |
| 17 | p1c9cb11d31 | 891 | 3 | 0 | 0 | 6 | no |
| 18 | p01004974c5 | 1161 | 4 | 1 | 3 | 6 | no |
| 19 | p40c33738de | 1572 | 4 | 0 | 8 | 10 | no |
| total | | 25,280 | 82 | 18 | 55 | 107 | 4 yes |

Word counts are whitespace tokens. Drafts run 1,203 to 2,315 words, so every item is shorter than its draft, some by half (items 3 and 12 are under half of a 1,203-word draft).

## Findings

1. Dropped content is the biggest defect, and it is shared within each pair. Dropped counts match across the two items of a doc in 9 of 10 docs (p1c9cb11d31 is 7 vs 6). Whatever separates the two items of a pair, it is not recovering lost draft content. If the repair step works sentence by sentence, it cannot fix this; the cut happens upstream.
2. The two items of a pair share most of their text. The sentence diff found 1 to 12 differing sentences per pair. Invented, garbled and join counts differ mostly at those spots, so the pair contrast comes from a handful of local edits.
3. Items 7 and 14 copy about 40% of their words from the draft in runs of 8 or more words (the second half is close to the draft verbatim). Every other item is 6% to 24%. Worth knowing if the judge scores those items as human.
4. Technical posts break the hardest. In p40c33738de both items lose all five code blocks but keep the lead-in sentences ("Here's the one I used:"), which accounts for most of their 10 and 8 joins.
5. A mechanical check (every number and capitalised name in each item compared against its draft) found no new numbers or names beyond the ones logged by hand (58.0; the "$2012" in item 13 slips past it because 2012 appears in the draft as a year). Invented content here is mostly changed claims and attributions, not new entities.

## Per-item notes

Quotes are kept short. "Draft:" gives what the draft says.

### p1c9cb11d31 (book review, draft 1,458 words)

- Item 0. Invented 6: the opener speaks to the Ramblers as if they were the author ("fan of your writing"); "do something different" contradicts the draft ("this one is no different"); "a new dragon in the mix" (draft: a fresh dragon within Jacob); "not the kind of book that can stand on its own"; Jaymin called "she" (the draft never gives a gender); the closing "exactly what I needed / I hope you enjoyed it too" on a pre-order review. Joins 2: "I'm not going to say more than that... that sentence" points at the flying-zombies line, which was cut; the PS mentions "your survival kit", which was never introduced. Dropped 7: the setup (Louis, timeline, President wants to "learn"); the home visit where trouble starts; Justice hiding her feelings; the dread line; flying zombies; what goes in the survival kit; the invitation to new readers to subscribe. Publish no: wrong opening address, missing setup, dangling references.
- Item 17. Invented 3: the stand-alone claim; Jaymin as "she"; the post-release closing. Dropped 6: the "jumbled reviews" intro, the setup, the home visit, the hidden feelings, the dread line, the subscribe invitation. Publish no (borderline): it reads naturally but loses the plot setup and adds the pronoun guess.

### p40c33738de (Arduino breath ketone meter, draft 1,962 words)

- Item 1. Invented 6: the reference was "a device that measures the amount of acetone in my breath" (draft: urine strips); a new backstory ("measuring them from breath is a pretty good way to go"); acetone molar mass 58.0 (draft 58.08); "60 and 28 for temperature and humidity" (draft: humidity 60, temperature 28); "After that, the max value is no longer updated"; the "now" value "only valid if it's decreasing" (draft: the true max is reached once now falls below max). Garbled 1: the heading "How to convert the resistance to PPM." fused into a 600-word paragraph. Joins 10: the promised ketosis background never comes; a second opening ("I've been looking into how to measure ketones"); "pictured above"; "the voltage" never introduced; five dangling lead-ins ("Here's the one I used:", "the following scaling function:", "the above conversion", "Here are my readings:", "Here's the new scaling function:"); urine strips appear with no introduction. Dropped 10: what ketosis is (blood vs urine tests); the parts list; the voltage-divider section; five code blocks (regression, R0, scaling factor, mmol, new calibration); the two-week Keto-Diastix test and its scale; "is it working" with the blood-meter follow-up. Publish no.
- Item 19. Invented 4: 58.0; the temperature/humidity swap; the max-update claim; the now-valid rule. Joins 8: the promised background; "the voltage"; the five dangling lead-ins; unintroduced urine strips. Dropped 10, same as item 1. Publish no.

### p01004974c5 (Social Business to Open Business, draft 1,393 words)

- Item 2. Invented 3: "There are many reasons why this happens", with proven value and the integration question recast as causes of the stall (the draft gives no causes); HR given a quoted answer ("most will probably answer with..."); "In my blog I have talked about this many times". Garbled 1: ends mid-word, "better category than HR 2." Joins 3: "Instead, I will use the terms Open Business" with no sentence saying the old labels are dropped; "I have not been the one who has created this" without saying who did; "category" refers to blog categories never introduced. Dropped 6: the trio framing; the move away from gadgets, vendor jargon and sales/marketing; the decision to drop the labels; Cushman's two writings; the new blog categories section; the "Join me" close. Publish no.
- Item 18. Invented 4: the same three plus "now that Social Business has become mainstream". Garbled 1, joins 3, dropped 6, all as item 2. Publish no.

### p0f92b38ac3 (Alaska trip, draft 1,203 words)

- Item 3. Invented 4: "I told her about Academie Sans Frontières" and the Facebook group (draft: the author founded both and does not say she told Rochelle); "I told her about my interest in" who speaks what; "Her parents were a lost generation" (draft: the gap between them); the French tail adds that you can take language courses there. Garbled 1: the last line switches to French and starts "A l'Inside le Native Resource Center". Joins 3: "And I was returning from a three-month trip" is left hanging; Rochelle appears with no "I met"; the French paragraph restarts in another language. Dropped 10: Idle No More; the Language Center (survey, partners, three groups); the social-harm stakes; the program staff; the French loanwords and the gigue; the Iditarod and licence plates; Buser and Seavey; the other mushers; the private train and thanks; the closing. Publish no: it stops less than halfway through.
- Item 12. Invented 3: "told her about my interest"; "lost generation"; the language-course claim. Garbled 1, joins 3, dropped 10, same as item 3. Publish no.

### p3a84b9ccbc (Black administrator, draft 1,365 words)

- Item 4. Invented 2: the entry-point point is tied to the outburst ("a mistake of this nature could shut doors"), where the draft makes it a general point; "I'm also a representative because of the people I attract into my life. My closest friends tend to be people like me" reverses the draft's logic (other people's friends look like them, so some had no Black person to turn to but him). Garbled 1: "And it's not just a leadership role." Dropped 2: the Zoom-call setting with the "Black administrators can feel alone... free to speak up" paragraph; the author bio. Publish yes (borderline): faithful and natural, but the friends line needs fixing.
- Item 10. Invented 3: the same two plus "In that moment, I realized that it was okay to be vulnerable." Garbled 1, dropped 2, as item 4. Publish yes (borderline), with the same fix.

### p2a4982704f (trophy hunting, draft 1,450 words)

- Item 5. Invented 3: "this barbaric practice" (a value word the draft does not use); tigers listed as available on hunting sites (the draft names tigers and wolves separately, as stately animals); the hedged "From what I have seen... make up the bulk" and "a harsh thing to say" become the flat "The people who do this are wealthy Americans who are new to money". Garbled 2: "at age  than" (the number is missing); "No one is eating a family". Joins 2: a meta restart ("In the midst of some intense, emotional feelings, I've written about..."); "killing the cubs of a dominant male" when the pride and cub-killing mechanism was never introduced. Dropped 5: fair chase; why lions are different (pride takeover, cub killing); the argument that age can only be confirmed after death; the 15% decline and 30,000 lions; the closing ask with "Cecil deserved better". Publish no.
- Item 16. Invented 1: the dropped hedge on "new money". Joins 1: the cub-killing mechanism is never introduced. Dropped 5, same as item 5. Publish no: coherent, but it loses the lion-biology argument and the closing ask.

### p25d4111207 (discipline and the pressure pot, draft 1,712 words)

- Item 6. Invented 1: "My mom and dad lived by their own rules" (draft: by their own words). Garbled 2: "what the proper pounds of pressure for whatever food you are cooking" (verb missing); the fragment "One thing I call 'like-ism'." Joins 3: "They raised beans..." with no antecedent after the chores paragraph; the jump from the farm to "I am not here to criticize parents" with the critique of modern culture never set up; "blunt iron that hones nobody" when "iron sharpens iron" was never introduced. Dropped 6: vine pruning ("pressure that makes us strong"); iron sharpens iron; the "feelings nor the rod" paragraph; "world turned upside down" with 1 Corinthians 14:33; the subscribe block; the books. Publish yes (borderline): faithful, ending intact, three small fixes.
- Item 11. Invented 4: "own rules"; "Our parents were a team."; "Parents are not to blame for the pressure pot entirely."; the hedge dropped in "The parents are the blunt iron" (draft: today's parents too often are). Garbled 2, as item 6. Joins 2: the modern-culture jump and the blunt iron ("Our parents were a team" supplies the antecedent for "They raised beans"). Dropped 6. Publish yes (borderline).

### p4ad56d5750 (clothes shopping after surgery, draft 1,787 words)

- Item 7. Invented 4: "the whole season is getting shorter" (draft: arriving quicker); "My girlfriend, and male friends" (draft: friends of both sexes); "I never had the money to try stuff on" (draft: he never had wealth, and he skipped trying things on because it was miserable); "I'm a big guy, and that's the kind of store I usually go to" said about Old Navy, which contradicts the post. Joins 3: "but first a bit of business" with no business after it; the jump from family to clothes with the Mystery Train bridge gone; a second opening ("I went on a shopping spree for clothes at Old Navy and Kohl's today") after Old Navy has already been described. Dropped 1: the Mystery Train "clothes make the man" frame, closing line included. Publish no.
- Item 14. Invented 1: the money-to-trying-on causal claim. Joins 1: the family-to-clothes jump. Dropped 1. Publish no (borderline): faithful, but it is two walls of about 700 words each, it has lost the title frame, and about 41% of its words are draft text verbatim.

### p3bfd623027 (mapping North Korea, draft 1,382 words)

- Item 8. Invented 4: a new backstory ("I realized there were a lot of them when I saw that Melvin's project had only mapped 113"); "My goal has been to map all of the archaeological sites in North Korea, and I have been able to do this" (draft: he has viewed every square mile and wants experts to fill in details); "often vassals" (draft: sometimes); "The locations are taken from the official register" (draft: he cites its treasure numbers). Garbled 1: "I have marked all 98 sites in North Pyongan Province ... and 71 of them". Joins 3: "Melvin's project" before Melvin is introduced; "The first is a list" (first of what); "download the file here or ... directly here" with no links. Dropped 2: why this history matters (the war, Japanese rule, the West losing the north's history); two thirds of the sites known only by location. Publish no.
- Item 9. Invented 8: the realization backstory; "These belong to the larger burial mounds section" (turns the 213 sites into tombs); "The other is from the work of Sarah Parcak" (makes Parcak a second site list); "I hope to contribute to the field"; the claim to have mapped everything; "often vassals"; locations taken from the register; "My colleague Melvin". Garbled 1, as item 8. Joins 4: "when I looked at this site" with no site named; "The first is a list"; a restart ("This is a list of some of North Korea's ancient historical sites"); the dangling "here" links. Dropped 2. Publish no.

### p10267ee0c0 (case for Obama 2012, draft 2,315 words)

- Item 13. Invented 10: the essay writer was promised "something like $2012" (draft: just over two thousand dollars); "Jackson was a genocidal maniac" (draft: massacred American Indians); "Jefferson had children that he sold as slaves" (draft: kids who were traded as property); the Trump/Oprah myth called "a bipartisan creation", with the author's retraction about Oprah lost; "He also started the Cash for clunkers program"; "President Obama has had a busy year" (draft: just over three years); Obama "promised to enforce the immigration statutes when he was admitted to the bar" (draft: the author took the bar oath, Obama swore his as president); quitting smoking turned into a reason to vote for him; temperament called "a policy reason" (draft: explicitly not policy); the Bachmann/Palin dare turned into a reason to vote for him. Garbled 2: "He hasn't been in office for three years. He's been in office for just over three years."; the loop "Let's look at some of them." then "Now, let's look at these arguments." Joins 3: "the surprise is yours, not his" right after the Oprah line; the dangling "Here are some of the things I think the President has done well this year:"; "That hurts his base" when the deportation record was never set up. Dropped 5: the Liberal Festivus opener; Elon James White's "Emo Progs"; the defense of Libya against the Congress objection; the Larry Summers objection; the close (Howe/MacLaine callback, five more years, t-shirt). Publish no.
- Item 15. Invented 8: the same, minus "$2012" and "genocidal maniac". Garbled 1: the three-years pair. Joins 1: "That hurts his base". Dropped 5. Publish no.

## What this reading could not verify

- Single reader, single pass. No second rater, so there is no inter-rater agreement figure. The invented and dropped counts depend on the granularity rules above; a different reader may split or merge items differently. The within-pair contrasts should hold up better than the absolute levels, because both items of a pair were scored side by side with the same rules.
- The drafts were taken as ground truth. Where a draft is itself odd (for example the 1995 Dockers sentence, or "dislike themselves because of inner integrity"), the item was not charged for repeating it.
- Publish calls are one editor's judgment, not checked against a panel or a human editor.
- The read key was not opened, so these counts have not been matched to conditions.
