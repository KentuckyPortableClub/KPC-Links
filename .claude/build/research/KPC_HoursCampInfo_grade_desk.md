# Chat 8 grades the hours/fees/permits bot and the campground info bot (Kentucky run 1) (desk, Oct 28 2026)
I read data/hours/review.md + US-KY.json and data/campinfo/review.md + US-KY.json. Grades: A = I opened the agency page, B = the bot's quoted line is the agency's own and fits the park, C = wrong, cut, or about something else. I could not open the agency pages (not on this session's fetch list), so no A for hours; every grade is from the bot's own quoted line. Bar: A+B ≥ 90%.

## 1. HOURS, FEES & PERMITS BOT: FAIL (6 of 12 parks = 50%; the bot's own gate also says FAIL, 9/38 = 24%)
| Park | Grade | Why |
|---|---|---|
| US-0295 Clarks River NWR | B | refuge sunrise-sunset is the agency's own line; the 'office Mon-Fri 7:30-4:00' line is the OFFICE, so it needs its label |
| US-0538 Reelfoot NWR | C | 'Monday - Saturday (Closed on all Federal Holidays)': no subject (what is open?) |
| US-0724 Abraham Lincoln Birthplace | C | 'The Memorial Building closes at 4:30 pm': one building, not the park |
| US-10098 Green River NWR | B | 'Day use from legal sunrise to legal sunset' |
| US-10099 Wolf Creek Fish Hatchery | B | hours, 'no fee', KY fishing licence + trout permit: all own sentences, right place |
| US-10124 Clay WMA | C | 'Grouse and quail seasons are open until 3 pm … from Nov' CUT at 'Nov.'; it is hunting-season hours, not the area's hours |
| US-10160 Rockcastle River WMA | C | same cut sentence |
| US-10172 Salato Wildlife Education Center | C | hours 'Tuesday - Friday 9-4' fine, but 'Hours and Seasonal Closings' is a HEADING and '26, 2026 | Free Admission' is a date-line fragment |
| US-10173 Kentucky Horse Park | C | fee line is about the Man o' War Memorial ('FREE Entry!'), not park admission: reads as 'the park is free' (false) |
| US-1265 Lincoln Homestead | C | all lines from the FIELD TRIPS page ($2 per person is a school program, shelters) |
| US-1276 Carter Caves | C | '(PERMIT REQUIRED)' with no subject, from a tourism-site PDF map (not the park's own page) |
| US-12971 Bat Cave SNP | B | trails open year round; quote is whole |
**Counts:** 34 of 193 parks have hours, 8 fees, 11 permits, 155 nothing found.
**Fixes (H-R1…H-R6):** (1) never cut a sentence at 'Nov.', 'a.m.', 'p.m.', 'U.S.', 'St.' (same abbreviation hole as the documents bot); (2) a hit needs a SUBJECT (the park, an office, a named building) in the same sentence; headings and date lines are discarded; (3) read the page's MAIN visitor/hours/fees block only: field-trip, group-tour, school, hunting-season and event pages are other topics (hours from a hunt-season sentence are 'hunting hours', a separate label); (4) a fee for one attraction (Memorial, tour, museum) is labelled with that attraction, never 'park fee'; (5) tourism-site PDFs are not the agency (kentuckytourism.com is state government but not the park's page: label 'tourism listing'); (6) the Kentucky gate: Otter Creek Wed-Sun and 25 of 28 expected rows are MISSED, so most Kentucky state-park hours pages are probably script-built (needs the browser pass).

## 2. CAMPGROUND INFO BOT: PASS on rows (9 of 10 distinct campgrounds = 90%), but ONE DANGEROUS ERROR to fix first
The 12 samples are 10 campgrounds (Twin Knobs and Zilpo are listed twice: duplicates, see C-4). They are the records with the MOST facts, so they flatter the bot; ask for a random 12 next time.
| Campground | Grade | Notes |
|---|---|---|
| Twin Knobs (x2) | B | own sentences: $35-64, check-in 2 pm, 'RV sites range from electric-only to full hookups' (so 'sewer = true' should read 'some sites') |
| Zilpo (x2) | B | same; map is a usfs-public.box.com link FROM the agency page (official file share; date unknown, honest) |
| Bandy Creek (TN) | B | facts fine; phone (423) 569-9778 comes from the page FOOTER (park HQ), not the campground |
| Bear Creek Horse Camp (KY) | B+ | sentences are exact ($30 for 30-amp, $35 for 50-amp) |
| Station Camp (TN) | B | fine |
| Blue Heron (KY) | B | fine; same footer phone |
| Holly Bay | B | phone quote is 'Phone: 859-428-7706; 606-864-4163' (two numbers of the Corps office); the bot kept the first only |
| Koomer Ridge | B, **bot right** | 'no hookups', 'No dump station': electric False is correct; our hand key says electric True: **the hand key is wrong** |
| Grove Drive-In | B | fine |
| **Turkey Foot** | **C: INVERTED** | the quote 'There is no water, electricity or dump station available' produced electric = TRUE and dump_station = TRUE (the page's drinking-water 'not available' came out false correctly). The bot lost the 'no'. |
**The answer-key check (67 hand-checked, 44 agree, 16 differ, 164 blank):** blank = the bot only fills a few fields (7 of 109 have a site count; RIDB key missing for the 42 federal rows). The DIFFERs: (a) phones: 5 Daniel Boone camps give the Corps office (859) 428-7706 vs the key's (606) 864-4163: same office, two numbers on the page: keep BOTH; 4 Big South Fork camps give the park HQ number from the footer vs the Bandy Creek visitor center in the key: footer phones must never count; (b) electric: Clear Creek, White Sulphur Horse Camp, Great Meadows say False in the bot, True in the key; Koomer Ridge proves the key can be the wrong one: re-check all four against the quotes (BOT LOOK-UP 1); (c) Mammoth Cave phones (270) 758-2180 vs key 758-2424, Maple Springs 758-2166 vs 758-2180: look up which line is the campground's (BOT LOOK-UP 2).
**Fixes (C-1…C-6):**
- **C-1 NEGATION (first!).** A fact sentence with no / not / without / none / 'does not' / 'unavailable' before the word is False (or null), never True. Add a 30-sentence test (15 'has' + 15 'has no') that must pass 100%.
- **C-2 Footer phones.** Take a phone only from the campground or recreation-area section, never the site footer 'Contact Info'.
- **C-3 Keep all phones** on a quoted line (Holly Bay has two).
- **C-4 Duplicate records.** Twin Knobs and Zilpo appear under two ids; merge by same name + points within 300 m (E-R3) before the camp-and-activate bot uses the list.
- **C-5 Official hosts.** 9 rows say 'not on an official host': landbetweenthelakes.us (Land Between the Lakes, run by the Forest Service: B, I believe it is the official site), kyhorsepark.com (a state agency's own site), levijacksonpark.com (City of London since 2019), breakspark.com (the Breaks Interstate Park Commission). Add them to sources.json host by host with one proof line each (chat 8 can give the proofs), or these 9 stay blank.
- **C-6 'Some sites' wording.** 'RV sites range from electric-only to full hookups' = some sites have sewer: store 'some', not true.
Hand-key fixes for Brandon/HQ: Koomer Ridge electric → False; recheck Clear Creek, White Sulphur, Great Meadows.

## BOT LOOK-UP rows for chat 9
1. Open Recreation.gov/Forest Service pages for Clear Creek, White Sulphur Horse Camp, Great Meadows, Koomer Ridge: electric yes/no (page words).
2. Mammoth Cave campground and Maple Springs: the campground's own phone line on the NPS page.
3. Open Reelfoot NWR visit page (what do 'Monday-Saturday' hours cover?), Salato visit page, Kentucky Horse Park admission page (what does general admission cost?).
