# Blind reader sheet: p2e read pack

Single reader. Each of the 20 items was read in full against its own draft (field D100 in results/a1_d100.jsonl). I did not open any key or text file other than the two named in the brief.

## Rubric as applied

- invented: a claim, number, name, value, stance, preference, quote or attribution the draft does not give or gives differently. A changed hedge (probably to certainly), a swapped number or an added feeling each count once. Plain synonyms do not count.
- garbled: a sentence a copy editor must repair: ungrammatical, cut off, looping, word salad, wrong word. Spacing artifacts such as "11 th" are not counted and are listed under other.
- joins: a restart as a new post, a reference to something never introduced or not present (including a "here is the code" with nothing after it), or a jump the reader cannot follow. Ordinary topic changes do not count.
- dropped: a whole draft point, section, list or code block missing. Each code block counts once. A lost single-sentence detail does not count.
- publish: yes only if a careful editor would run this item over the draft with copy-edit-level fixes (typos, paragraph breaks, restoring a byline). Any material false claim or lost section means no.

Words are whitespace-separated tokens. Quoted text is from the item unless marked otherwise.

## Table

| item | doc | words | invented | garbled | joins | dropped | publish |
|---|---|---|---|---|---|---|---|
| 0 | p3bfd623027 | 1240 | 2 | 2 | 2 | 4 | no |
| 1 | p40c33738de | 1572 | 5 | 0 | 9 | 12 | no |
| 2 | p4ad56d5750 | 1515 | 3 | 0 | 3 | 1 | no |
| 3 | p0f92b38ac3 | 588 | 3 | 2 | 4 | 8 | no |
| 4 | p2a4982704f | 972 | 3 | 1 | 2 | 4 | no |
| 5 | p4ad56d5750 | 1539 | 7 | 0 | 5 | 4 | no |
| 6 | p25d4111207 | 1434 | 5 | 2 | 0 | 5 | no |
| 7 | p01004974c5 | 1150 | 4 | 5 | 3 | 3 | no |
| 8 | p01004974c5 | 1287 | 2 | 2 | 2 | 0 | yes |
| 9 | p25d4111207 | 1325 | 2 | 2 | 3 | 3 | no |
| 10 | p40c33738de | 1239 | 10 | 6 | 8 | 14 | no |
| 11 | p10267ee0c0 | 2137 | 15 | 2 | 5 | 4 | no |
| 12 | p0f92b38ac3 | 1207 | 9 | 0 | 4 | 3 | no |
| 13 | p2a4982704f | 1563 | 11 | 7 | 4 | 4 | no |
| 14 | p3bfd623027 | 1337 | 11 | 3 | 4 | 2 | no |
| 15 | p1c9cb11d31 | 1184 | 7 | 2 | 5 | 8 | no |
| 16 | p3a84b9ccbc | 1411 | 4 | 2 | 2 | 2 | no |
| 17 | p1c9cb11d31 | 891 | 3 | 0 | 0 | 4 | no |
| 18 | p3a84b9ccbc | 1323 | 1 | 0 | 2 | 2 | yes |
| 19 | p10267ee0c0 | 1802 | 11 | 1 | 2 | 4 | no |

## Per-item notes

### Item 0
- invented (2): adds stance "It is exciting to see all of these historical sites"; turns the draft's probably into certainty with an added reason "I am sure that they existed"
- garbled (2): fragment "National Treasures of North Korea (there is an official list)"; missing article "with physical site in North Korea"
- joins (2): "National Treasures of North Korea" arrives with no lead-in; jump from Sinuiju to "South Korea recently closed" with no bridge
- dropped (4): Why this history matters paragraph (Korean War framing, the West losing the north's history); honest limits paragraph (academics probably know the sites, baffled without graduate training); heritage paragraph (belongs to all Koreans, deserves protection, reunification hope); Get the file section (KMZ name, URL, hashtag request, byline)
- publish: no. Accurate in what it keeps, but loses four whole points, including the file link the post exists to share.
- other: "In Kyongsong Hyanggyo" treats the school's name as a place. Not counted.

### Item 1
- invented (5): "where you breathe in" (draft has exhaling into the chamber); praise "a great tutorial"; "58.0 g/mol" (draft gives 58.08); rule "only valid if it's decreasing" (draft says the max has been hit at that point); swapped order "the values 60 and 28 for temperature and humidity"
- garbled (0):
- joins (9): promise "a bit of background on ketosis" never kept; "Ketosense's main components" with the name never introduced; heading "Results" over datasheet text with no results; heading "The sensor" restarts the explanation after the long block; "Here's the one I used:" with nothing after; "the following scaling function:" with nothing after; "the above conversion" with no conversion above; "Here are my readings:" with nothing after; "Here's the new scaling function:" with nothing after
- dropped (12): ketosis and measurement background (blood versus urine, costs); parts list; voltage divider section; code block for PPM from 50k to 3600 ohms; code block for PPM below 3600 ohms; code block for temperature and humidity scaling; code block for acetone mmol/l conversion; code block for recalibrated function; R0 derivation from the datasheet; Keto-Diastix level list; Is it actually working section (caveat, blood-meter method); Final thoughts
- publish: no. Every formula the build needs is gone, with dangling pointers to them left behind.
- other: one 500-plus-word paragraph holds the wiring, switches, startup and PPM material.

### Item 2
- invented (3): "I've just added a link" (draft only says a link is there); "I never had the money to try stuff on" (draft keeps wealth and trying-on as separate reasons); "I was afraid of going" (draft says held back)
- garbled (0):
- joins (3): "the season has a different flavor" before any season is mentioned; jump to "I don't remember the last time" with the Mystery Train lead-in gone; "before my surgery" with surgery never introduced
- dropped (1): Mystery Train line and the clothes make the man motif, including the closing line
- publish: no. Faithful, but the title motif is gone, the second half is two unbroken blocks, and the tail is the draft's wording largely unchanged.

### Item 3
- invented (3): comparison "than the usual international convention"; "I told her about my interest" (draft reports no such conversation); "a lost generation" (draft says her parents were the gap)
- garbled (2): non-word "accompanyists"; French-English mix "A l'Inside le Native Resource Center"
- joins (4): "And I was returning from a three-month trip" follows nothing and the invitation is never completed; "Rochelle Adams was a" opens with no meeting; jump to "I started Academie Sans" inside the Rochelle passage; switch into French at "A l'Inside le"
- dropped (8): Idle No More; ANHC Language Center survey, partners and three groups; stakes paragraph (alcohol, drugs, violence, suicide); staff list; French words in Gwich'in; Iditarod section with Buser and mushers; private train finale; closing reflection
- publish: no. Stops about halfway, in French.

### Item 4
- invented (3): "where he could be legally killed" (draft says only no protection applied); stance "is jarring"; hedge removed in "The people who do this are wealthy Americans"
- garbled (1): "Cecil the Lions"
- joins (2): jump to "To see pictures of zebras" after the Nebraska rules; "the would-be hunter" never introduced
- dropped (4): fair chase argument; Why lions are different section (prides, infanticide, male-only defense); species decline passage (15 percent, 30,000 lions, tigers and wolves); closing ask (Don't pay a guide, Cecil deserved better)
- publish: no. Clean sentences, but the core lion argument and the ending are gone.

### Item 5
- invented (7): "it wasn't ideal because my parents"; "I proudly say that I'm a liberal" (draft says lean liberal); "I didn't look like a fat guy"; "if they were having a major sale" (draft says barring a clearance, the reverse); "$40-$87 each" (draft says six or eight bucks); "I'm glad I signed up" for the store card; "I'm happy, and I feel good about this"
- garbled (0):
- joins (5): restart "I would just buy something and try it on at home" repeats an earlier passage; restart "I went clothes shopping at ordinary stores" after the Old Navy trip; "In other news" returns to Old Navy; "encouraged me to try it out" with no referent for it; "before my surgery" with surgery never introduced
- dropped (4): Mystery Train and clothes make the man motif; Big and Tall sizing surprise; not good at everything yet passage (color matching, girlfriend's opinions); holidays and regular guy reflection
- publish: no. Reversed price claim, wrong shirt prices, and shopping passages out of order.

### Item 6
- invented (5): "this is the pressure cooker parents need to use" (draft says parents do something similar); "Spanning is grown-ups leading" gives the draft's definition of discipline to spanking; "a little building" (draft says a single barn); "soft iron" (draft says blunt iron); "because they lack inner integrity" (draft says because of inner integrity)
- garbled (2): wrong word "Spanning was not abusive"; wrong word "Spanning is grown-ups leading"
- joins (0):
- dropped (5): argument that the abuse label accuses ancestors back to Adam and Eve and God; 1 Corinthians verse; like-ism passage; Proverbs rod passage and promise of Part II; Stay in touch section (subscribe, books)
- publish: no. Reads cleanly but loses scripture, like-ism and the ending, and stops abruptly.

### Item 7
- invented (4): "I hear a lot of stories about companies" (draft says he notices); "There are many reasons why this happens" with a reasons framing; quoted answer "most will probably answer with"; "I have talked about this many times"
- garbled (5): typo "Enterprise 2.o"; "Instead, I will use the terms Open Business"; "a Open Business Council"; cut off "better category than HR 2."; agreement "but have not taken part"
- joins (3): "Instead, I will use the terms" with no lead-in; "David Cushman's vision" never introduced; "Employee Engagement seemed to me" with no category introduced
- dropped (3): what he is moving away from (gadgets, vendor jargon, Sales and Marketing focus); What comes next section (two new categories and plans); Join me closing
- publish: no. Ends mid-word in a sentence and loses the closing sections.

### Item 8
- invented (2): "In my post yesterday on CMSWire" (draft gives no day); "As I wrote in my post" (draft gives no such citation)
- garbled (2): "next 10 2 years"; "thinking about where I want to go next for several months now, both in person and online"
- joins (2): "is where this series started" with no series introduced; "As I wrote in my post" with no post introduced
- dropped (0):
- publish: yes. Complete and faithful, needing one number fix and two small attribution trims.
- other: closing line about being part of a series is close to the draft, not counted.

### Item 9
- invented (2): "a bunch of robots" (draft says people with no individuality); "their own evil nature" (draft says bad conduct)
- garbled (2): missing verb "what the proper pounds of pressure"; fragment "One thing I call"
- joins (3): "And that is what I want to talk about today" with that pointing at nothing; jump to "I am not here to criticize parents"; "blunt iron that hones nobody" with the iron metaphor never set up
- dropped (3): Pressure that makes us strong section (pruning, iron sharpens iron, shed of life); world turned upside down passage (right is wrong, 1 Corinthians); Stay in touch section
- publish: no. Close, but two argument sections are gone.

### Item 10
- invented (10): gas list "hydrogen, methane, carbon monoxide"; "It takes about a minute to heat up"; "readings are not very stable"; "It's very easy to use with an Arduino"; "The code for the Arduino is very simple" (draft stresses tinkering); "My assumption is that the levels of acetone"; "hope you can still learn something from my mistakes"; textbook line "A resistor is a component that resists"; claim "inversely proportional"; method "you need a voltmeter and a resistor" (draft uses the Arduino pin)
- garbled (6): "It's resistance decreases"; loop "The sensor has a very slow response time, so readings"; loop "It's also sensitive to a number of other gases"; loop "The sensor is also sensitive to humidity"; "the David A. Mellis, Limor Fried, Tom Igoe library for the LCD crystal library"; fragment "DHT11 is too slow."
- joins (8): "The code is below:" with nothing after; "Here is a picture of the completed device:" with no picture; "Here is a picture of the device in action:" with no picture; "but it works:" with nothing after; "PPM = pow(10, logPPM)" with logPPM undefined; second "PPM = pow(10, logPPM)" likewise; restart "But I hope you can still learn" mid-post; new post at "How to measure breath acetone levels"
- dropped (14): ketosis and measurement background (blood versus urine, costs); parts list; voltage divider section; code block for PPM from 50k to 3600 ohms; code block for PPM below 3600 ohms; code block for temperature and humidity scaling; code block for acetone mmol/l conversion; code block for recalibrated function; Taking a measurement section; enclosure and buttons section; urine strip test results; Is it actually working section; breathalyzer section; Final thoughts
- publish: no. Half the post is gone and it drifts into an invented explainer.

### Item 11
- invented (15): identity list "I'm not a conservative. I'm not a libertarian"; "$2012 in free money" (draft says just over two thousand dollars); "as much as I'd like to call everyone who disagrees with me names"; "far more women" (draft says two times more); "And then we can have a real conversation"; "please ignore this post"; altered quotation "President Obama has been a huge failure"; "I hope I've earned your respect"; "it has worked for me so far"; "the news media is fragmented"; "see the world through other people's eyes"; "We should debate ideas, not people"; "honest about my own biases"; "the power of the individual"; "I couldn't do this without you"
- garbled (2): looping "Angry at him because"; looping list "I'm not a centrist"
- joins (5): opens mid-thought "But now that Obama has announced his candidacy"; "People are talking about the fact" disconnected; "(If you're not interested in my views" disconnected; sign-off "I hope I've earned your respect" mid-post; "This is more important than ever" with no referent
- dropped (4): The man we actually elected section (moderate campaign, Trump and Oprah); cigarettes request; Why I'm still in section (temperament, Cheney, better for Republicans, runner-up); Bachmann and Palin closing with the t-shirt payoff
- publish: no. Good middle, but the end leaves the draft for roughly 350 words of invented generic reflection.

### Item 12
- invented (9): "which means that the people accompanying the attendees can also come to the workshop" (draft opened the pre-meeting tour); "36 month trip" (draft says three months); "I didn't have much time to think about it"; "once-in-a-lifetime"; "I was very happy to see that it is a modern city"; "I was very surprised when she told me"; "I was very happy to be able to talk"; "she was raised in an environment where she didn't speak the language"; "we didn't mind"
- garbled (0):
- joins (4): "central Geneva" never introduced; "the center was preparing" with no center introduced; "a shrinking glacier" with no glacier in the body; "the Wild, Wild West of my daydreams" with no daydream set up
- dropped (3): Wild West daydream opening; Jewish Mother and Anita sendoff; Northern Lights, moose and glaciers passage
- publish: no. Wrong trip length and repeated added feelings.

### Item 13
- invented (11): "I don't think I'm the best person to make this case" (draft says no spotless position); first-person passage "If I were a lion"; overclaim "you're killing a whole generation"; "It's true for zebras"; "We don't have the numbers yet"; "We don't know how many lions are left"; "He was going on a safari"; "I know that a lot of people who saw this post felt this way"; "this is something that happens all the time"; "They're ashamed of it"; "this is bullshit" (draft says uninformed, deceptive and wrong)
- garbled (7): stutter "maybe 30, 30, thousand"; repeat "If they really wanted a trophy, if they really wanted a trophy"; repeat "When the story of Cecil came out, when the story of Cecil came out"; loop "Hunting clubs and hunting programs trap lions"; loop "you're not just killing him, you're killing a whole generation"; loop "So when you kill a dominant male, you're killing a generation"; repeated line "No one's feeding their family with a lion's mane on the wall"
- joins (4): "I don't bring that up" with that dropped from the text; jump to "If I were a lion"; "T he idea" after the lion passage; "these hunting websites" never introduced
- dropped (4): Palmer's prior conviction and harassment charge; FACT on money to locals and tourism; FACT on the 2005 to 2008 ban and lion numbers; FACT that trophy hunting is not hunting
- publish: no. Looping and invented escalation, and no facts section.
- other: heavy "And the thing is" tic, counted as style.

### Item 14
- invented (11): origin story "I realized there were a lot of them"; "My goal has been to map all of the archaeological sites" (draft says viewed every square mile); "often vassals of China" (draft says sometimes); "I'm sure that archaeologists in North and South Korea" (draft says probably); "I hope they will be able to tell me more"; "that must have existed" (draft says probably); "I have marked all 98 sites" (draft gives 71 his, 27 Melvin's); "The locations are taken from the official register"; "only about 3 miles apart" (draft says under 3); "only about 300 left" (draft says under 300); "has much to offer the world"
- garbled (3): "(the most of any province) and 71 of them"; loop "You can download the file here or you can download it directly here"; agreement "because it is an example"
- joins (4): "Melvin's project" before Melvin is introduced; "The first is a list of 113 sites" with no list; jump to "Recently, South Korea shut down"; "The sites listed here" with no list
- dropped (2): Why this history matters paragraph; two-thirds finding (nothing beyond the location)
- publish: no. Invents a completed goal and a false site count.
- other: spacing artifacts "11 th" and "13 th".

### Item 15
- invented (7): "more than you love your own face"; "a scary presence"; "that itchy feeling"; "You can blame Jaymin"; "one thing she is not is boring"; "because he's Jaymin" (draft gives no pronoun); "feel all the feels"
- garbled (2): loop "There's a lot of adventure, but there's a lot of introspection too"; loop "I knew that Jaymin would fix things, and he did"
- joins (5): opens "So here it goes."; "she's having a lot of adventure" with she unnamed; "he goes through a lot of things" with he unnamed; "It's about a family" with no subject; "gather your survival kit" with the kit never introduced
- dropped (8): ending-first framing and opening thanks; ARC disclosure; survival kit list; Setup section (Louis, timeline, President); Justice's distrust and the trip home; Mischa's growth; extra scenes; newcomer subscribe note
- publish: no. Unnamed characters, repeated beats, and the ARC disclosure is gone.

### Item 16
- invented (4): "I didn't realize how important it was"; "It means that I am constantly on display"; "because of the people I attract into my life" (draft is a general remark about close friends); "I was tense when I entered our conversation" (draft says he opened in a harsh tone)
- garbled (2): "With the support of my hard work"; non-sequitur "And it's not just a leadership role"
- joins (2): "One of my colleagues looked at me" with the Zoom call never set up; "It means that I am constantly on display" with no referent
- dropped (2): reason for sharing (Black administrators feeling alone, free to speak up); author bio
- publish: no. Close, but changes what the author did and why.

### Item 17
- invented (3): "It's not the kind of book" that stands alone (draft says only this review leans on the history); "Jacob is an old favorite"; "I know she wouldn't let me down" (draft gives no pronoun)
- garbled (0):
- joins (0):
- dropped (4): ending-first framing; Setup section (Louis, timeline, the President holding them); Justice hiding her emotions passage; newcomer subscribe note
- publish: no. Clean, but the plot setup and the reviewer's framing are gone.

### Item 18
- invented (1): "I am a good listener" (draft says he takes time absorbing information)
- garbled (0):
- joins (2): "We are often the" with we undefined; "Everyone on the call" with no call introduced
- dropped (2): reason for sharing (Black administrators feeling alone, free to speak up); author bio
- publish: yes. Faithful; restore the sentence on why he shares this, the bio and the paragraph breaks.
- other: second half is one unbroken block.

### Item 19
- invented (11): "children that he sold as slaves" (draft says his children were traded as property); "a bipartisan creation"; "President Obama has had a busy year" (draft covers three years); "undocumented workers" (draft says illegal aliens); "I am a fan of a lot of what he has done"; "when he was admitted to the bar" (draft says that of the writer, not Obama); "it hurts me"; "doesn't smoke cigarettes" recast as a reason to vote; "Yes, I know, it's a policy reason" (draft contrasts temperament with policy); "If Obama can lead Dick Cheney"; "He also started the Cash for clunkers program" (draft does not say he started it)
- garbled (1): "He hasn't been in office for three years"
- joins (2): "That hurts his base" with no adjacent deportation point; "a decade-long search ended on his watch" with no bin Laden context nearby
- dropped (4): Liberal Festivus opening; Emo Progs passage; Larry Summers objection; closing with the Howe and MacLaine callback, five more years and t-shirt
- publish: no. Close to the draft in places, but too many changed claims.

## What I could not verify

- One reader. No second reader or adjudication, so the stance and join counts carry judgment. A script listed numbers and capitalized names in each item that are absent from its draft. It surfaced nothing beyond what is logged here, apart from format variants (0.50 for 0.5, 30 years for thirty years). It cannot catch a draft number reused in the wrong place ($40-$87 and $2012 were found by reading), and it does not check stance.
- A second script confirmed that table counts match the per-item lists, word counts match the pack, and every quoted fragment occurs in its item.
- Dropped counts treat a code block as one each and a section as one, so a post with many short sections can count higher than a post with few long ones.
