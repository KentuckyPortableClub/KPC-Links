# Kentucky REGRADE 1 (chat 11, Oct 28 2026, ~6:40 AM): hours + campground bots after chat 10's fixes
Files graded: KPC-Data data/hours/US-KY.json (ver 2, 6:20 AM) and data/campinfo/US-KY.json (ver 2, 6:20 AM, 106 of 109 camps, status partial).
NOT regraded (files unchanged since my first grade): TRUTH CHECKER (US-KY.json still the 05:40 run, ver 3: first grade stands, 9/12 = 75%) and DOCUMENTS bot (US-KY still ver 2; chat 2 says v3 will re-read KY by itself, then I regrade).
Bar: A+B >= 90%. Same grading words as the first batch.

## HOURS bot: still FAIL (gate got WORSE: 24% -> 13%, 5 of 38 expected rows)
Wrong data went down a lot, but so did everything else: 163 of 193 parks "nothing found" (was 155); hours kept 20 (was 34).

Same 12 parks as the first grade:
| park | before | now | what changed |
|---|---|---|---|
| Clarks River NWR | B | B | now one line "open during daylight hours" (twice, duplicate); the office hours are gone |
| Reelfoot NWR | C | B | fragment gone; nothing found (a miss, not an error) |
| Abraham Lincoln Birthplace | C | **C** | still "The Memorial Building closes at 4:30 pm" as the park's hours |
| Green River NWR | A | A | same, fine |
| Wolf Creek NFH | A | B | fee + permit kept, but the hours (8-4) and "free admission" are gone |
| Clay WMA | C | B | cut-at-"Nov" fragment gone (FIXED); nothing found |
| Rockcastle River WMA | C | B | same (FIXED) |
| Salato Wildlife Refuge | C | B | heading and date fragments gone (FIXED); the real hours (Tue-Fri 9-4) were also lost |
| Kentucky Horse Park | C | **C** | NEW junk: the question "Is the campground open year round?" kept as hours; "Grounds open at 6 pm / Performance begins at 7 pm" (an event); "$5 million renovation project" kept as a fee; "regular hours of 9:00 AM - 5:00 PM" conflicts with the 10-4 page. The real "10-4, closed Mon-Thu" is gone |
| Lincoln Homestead SP | C | B | field-trip fragments gone (FIXED); nothing found |
| Carter Caves SP | C | B | "(PERMIT REQUIRED)" fragments gone (FIXED); nothing found |
| Bat Cave SNP | B | B | same, still starts "However," |
A 1, B 9, C 2 => 10 of 12 = 83% on A+B, but 6 of those B's are "nothing found". Honest summary: the cut/fragment/field-trip/heading C's are FIXED (6 of 8); ABLI and Horse Park remain C and Horse Park got worse.
Still FAIL: gate 13%, and a bot that finds hours on 20 of 193 parks cannot be counted on. The 9 known-good rows that match are all state nature preserves and Buckley-type pages; NPS/FWS/KDFWR pages give nothing.

### For chat 10
1. Question marks: drop any sentence ending in "?" or starting "Is/Does/Can/How" (Horse Park).
2. Event lines ("Grounds open at 6 pm | Performance begins at 7 pm", "Meet & Greets ... 6 pm to 7 pm") must not be park hours; a "$ ... million" figure is never a fee.
3. Hours must come from the page's hours section (a table or "Hours" heading), not any sentence with a time; the Horse Park hours page has the right 10-4 line.
4. Recall: put back "Wolf Creek 8-4 + free admission", "Salato Tue-Fri 9-4", "Clarks River office Mon-Fri" under an "office hours" label (H-R5). The fix over-filtered.
5. ABLI: "Memorial Building closes at 4:30" must be labelled attraction hours or dropped.
6. Gate target: 70% before any long run. It went the wrong way.

## CAMPGROUND INFO bot: better, still FAIL (not ready for the long run)
Fixed since the first grade (checked in the data):
- Land Between the Lakes host: all 6 LBL records now "ok", with sites (FIXED).
- Footer phones: 0 (was 8) and Mammoth Cave's footer phone is gone (FIXED).
- Bandy Creek sewer: now False, quote "There are no sewer hook-ups" (FIXED); Wilderness Road sewer/water False (right).
- Twin Knobs / Zilpo / Holly Bay hookups now "some" instead of True (FIXED); Koomer Ridge electric False, dump station False (right).
- Duplicates: 4 pairs -> 2 (Zilpo merged with an "ids" list; Twin Knobs x3 -> x2; Mammoth Cave x2 and one Twin Knobs left, one of each pair empty).
- Site counts 7 -> 10 of 106; fees 16 -> 22.

NOT fixed (the same C's):
1. rv_max_ft is still read from "Elevation: maximum N feet": 4 WMAs (West Kentucky 451, Yellowbank 872, Higginson-Henry 675, Rolling Fork 980). Also 35 for Barren Fork and Great Meadows: check the quote.
2. Hunting season still kept as camping season: Yellowbank "Nov. 1 through Dec. 31", Higginson-Henry "Nov. 14 through Dec. 31".
3. NEW: the national reservation line (877) 444-6777 is kept as the campground's phone on 4 Big South Fork records (Bandy Creek, Bear Creek, Blue Heron, Station Camp). It is the recreation.gov call centre, not the campground.
4. White Sulphur Horse Camp and S-Tree: booking.url = "https://recreation.gov" (the site's home page).
5. rules.fires holds non-rules ("fire ring and lantern pole", "fire ring, access to restrooms with flush toilets").
6. Piney Campground (TN) sites 44 vs key 384: look at the quote (probably one loop).
7. State parks (parks.ky.gov): Kenlake, Lake Barkley, Taylorsville, Carter Caves, Carr Creek, Barren River, Fort Boonesborough, Paintsville... still only a generic lodge booking link, no sites/hookups.

Random 10 (seed 11, status ok): A 2 (Zilpo, Holly Bay), B 8 (5 booking-link-only, White Sulphur + S-Tree generic booking link / rules.fires, Wilderness Road rules.fires), C 0 => 10 of 10 on A+B, but half the sample is a booking link and nothing else. Across all 65 read-ok records I count about 10 with a wrong fact (4 elevation-as-RV-length, 2 hunting-as-camping season, 4 wrong 877 phones), which is about 15%.

Answer-key check (bot's own): agree 40 (was 44), DIFFER 21 (was 16), blank 152 (was 164). The DIFFER rows are mostly 'bot "some" vs key True' (14 rows: the key says True where only some sites have electric; the bot is more careful) plus Clear Creek / White Sulphur / Great Meadows / Turkey Foot electric False vs key True (the agency words say no hookups: the KEY is wrong, as chat 8 told Brandon), 4 phone rows (877) and Piney sites. Real bot errors there: 5.

### For chat 10
1. rv_max_ft only from "length / RV up to N ft / trailers up to"; test West KY, Yellowbank, Higginson-Henry, Rolling Fork = none.
2. season: reject "hunt / quail / rabbit / deer / turkey / Nov. N through Dec" lines.
3. Phones: reject numbers on lines with "reservation", "1-877", "Recreation One Stop"; a number is the campground's only if the same sentence names a campground/park office.
4. booking.url must be a specific campground URL, never a bare domain (recreation.gov root).
5. rules.fires only from a sentence with "fire/campfire/firewood" plus a verb like "allowed / prohibited / permitted / ban".
6. Merge duplicate records: Twin Knobs (2), Mammoth Cave (2), keep the one with facts.
7. parks.ky.gov state park pages: read sites, hookups, dump station from the text (5 of my 10 sample records have only a booking link).
8. Gate: add these as known answers.
9. Update kpc-campgrounds.json KEY (chat 2/9): Clear Creek, White Sulphur Horse Camp, Great Meadows, Turkey Foot electric = NO per the agency words (Brandon's list item already in chat 10 NEEDS BRANDON).
