# Kentucky REGRADE 2 + first grades of the intake bot and scoreboard (chat 11, Oct 28 2026, ~8:15 AM)
Run graded: KPC-Data run 40685754820 (workshop rerun: truth v4, hours v3, campground v4) + documents bot v3 (KY, GA...) + intake bot + scoreboard first run. Bots' own gates: truth FAIL, hours FAIL (crash), campground FAIL, intake FAIL.
Bar: A+B >= 90% on a 10-12 sample. Words: A right; B right but thin/soft; C wrong or something a person would act on wrongly.

## SUMMARY
| bot | score now | before | verdict |
|---|---|---|---|
| Truth checker v4 | flagged rows 13/17 = 76%; random 'agree' 8/8 | 15/19 = 79%; 9/12 | FAIL (close; 4 old C's fixed, 4 new C's) |
| Hours v3 | nothing to grade: CRASHED on 191 of 193 parks | 4/12 (v2: 10/12 incl. 'nothing') | FAIL (code bug, not quality) |
| Campground v4 | random 10: 9/10 = 90% | 5/10, then 10/10 thin | BORDERLINE: accuracy good, own gate fails on a key problem + 1 new bug |
| Documents v3 (KY) | finder check 18/25 = 72%; random 12 maps 11/12 = 92%; rules pages: 30 parks wrong | 17/25 = 68%; 10/12 | FAIL (maps much better; rules pages are a new C on 30 parks) |
| Intake bot (first run) | 8/10 = 80% (its own gate FAIL 8/10) | n/a | FAIL (2 verdict problems, 1 overstated claim) |
| Scoreboard (first run) | 22 of 30 columns identical to chat 8's hand counts, the rest within 22 and explained | n/a | PASS on counts |

## 1. TRUTH CHECKER v4 (data/truth/US-KY.json, run 40685754820)
Gate (its own): FAIL, 1 miss of 10: Levi Jackson (OFF 722 vs 896 + hint naming the City of London): verdict now 'unsure', agency size None.
My first-grade C's, one by one:
| first-grade C | now |
|---|---|
| US-10105 Green WSR compared with Mammoth Cave's 52,830 | **FIXED** ('no size on page') |
| US-10104 Red River read "708, 879" = 879 | **FIXED** (now 5,600, unsure) |
| US-4689 Kentucky Ridge 23% off shown 'unsure' | **FIXED** (OFF, cause class) |
| US-3790 Fort Heiman on Fort Donelson's page | **FIXED** ('no size on page') |
| US-13599 Kingfisher "21.2 + 13.8 acres" | **FIXED** (agree, 35 vs 34) |
| US-10098 Green River NWR 77% off, unsure, no cause | **FIXED** (OFF, agency bigger) |
| Handover hints 125 rows (85% noise) | **FIXED**: 11 rows on 7 parks. Real: Levi Jackson (State -> City), Otter Creek (-> Meade County 2026), Blackacre (school system), Fort Donelson/Heiman (2006 county transfer). Still junk: 2 Clarks River rows (a 1700s land grant and a definition of 'refuge'), a Big South Fork 'owned by DOI' row, Green River NWR '10 acres donated 2019'. Lost the real ones I had listed: Clyde Buckley (Bluegrass Greensource), Tom Dorman (ex-Kentucky River Authority), White Hall (county maintains) |
| US-0295 Clarks River official 73,962 (land grant) | **PARTLY**: grant gone, but now reads "6 million acres" (the national refuge system line); verdict unsure, harmless but the number is wrong |
| US-0538 Reelfoot (Hatchie's 11,556) | **PARTLY**: now 1,850 acres from the visit page; unsure + multi-state cause: ok |
| US-1271 Taylorsville Lake (248 = a map label) | **WORSE**: was unsure, now a false OFF (713%) |
New C's (regressions):
- US-1264 Levi Jackson: lost the 896-acre agency number (the page that proved it); 'unsure, no total-looking sentence'. This is exactly what the gate caught. The City-of-London hint is still there.
- US-0019 Cumberland Gap: official "15 acres" from the park map PDF, 161,400% off, printed in the review.
- US-3801 Clifty Wilderness: official 8,270 acre is Cave Run LAKE's size ("This 8,270-acre lake"), unsure 51%.
- US-1271 Taylorsville: see above.
Flagged rows (7 OFF + 10 unsure = 17): A 5 (Mammoth Cave, Cedar Creek, Green River NWR, Kentucky Ridge, Big South Fork container), B 8 (Fort Donelson: 'as of 2010' not marked stale; Green River SNA two-piece record; Clarks; Reelfoot; Red River; LBL; GW&J; Little South Fork), C 4 (Taylorsville, Cumberland Gap, Clifty, Levi Jackson) => 13/17 = 76%.
Random 'agree' (8 of 99, seed 23): all A (Kentucky Ridge WMA, Cane Creek, Ballard, Kleber, Doug Travis, South Shore, Bullock Pen 148.9 vs 138, Daniel Boone NF 708,000). The 4 'agree' rows with no park name: Boltz A, Buckley A (375 acre on the Buckley page), Vernon-Douglas A, Clifty (now unsure, C above).
Still 22 'agree' parks with pin outside (chat 2 measured: entrance pins, no wrong polygon).
URL-with-spaces bot error (US-12083): FIXED (agree).
Fixes for chat 10: (1) Levi Jackson: keep the 896 from levijacksonpark.com (it lost it when the filter was tightened); (2) numbers from a map PDF ("15 acres", legend text) and from sentences about a LAKE ("8,270-acre lake") or a "248" map label must not count: a figure needs 'park/preserve/forest/WMA name' in the same sentence or a Size/Total/Acres row; (3) if the cause is 'no total-looking sentence', show NO number; (4) 'as of 2010' figures: print the year; (5) keep the real handover hints (Buckley, Tom Dorman, White Hall) by allowing 'now managed by <X>' when X is named; drop 'refuge is typically managed by FWS' and land-grant sentences.

## 2. HOURS v3: crashed
Every park but 2 = "bot error: too many values to unpack (expected 2)" (191 errors, 75 pages read, 2 parks with output: Wolf Creek, Breaks Interstate). Its own gate FAILED honestly (0 of 2 opened). Wolf Creek (8-4, no fee, licence + trout permit) and Breaks ("Monday: 9am-8pm", "$3 day-use fee per car") are good, but one Breaks line is a day-by-day fragment. Nothing else to grade. This is a code error in the new filtering: fix, then rerun. Recall target from the last grade still stands (gate 70%), and please bring back the real lines the v2 filter lost (Wolf Creek hours, Salato Tue-Fri 9-4, Horse Park 10-4 Fri-Sun, Clarks River office hours under 'office hours').

## 3. CAMPGROUND INFO v4 (data/campinfo/US-KY.json, 103 camps checked, 6 left, status failed)
Own gate: known answers 15/16 right, hand-key agreement 39/66 = 59% (needs 70%): FAIL. Of the 27 key DIFFER rows, 9 are 'bot some vs key True' (vocabulary: the key says True where only some sites have electric: the bot is right), 6 are the key wrong (Clear Creek, White Sulphur, Great Meadows, Turkey Foot, ... electric False per agency words: the Koomer Ridge pattern), 10 are 'sites' (see new bug), 2 others. Only about 3 are plain bot errors. So 59% mostly says: fix the key and make 'some' count as agreeing.
First-grade defects:
| defect | now |
|---|---|
| rv_max_ft from 'Elevation' on 4 WMAs | **FIXED** (3 left: Barren Fork 35, Great Meadows 35, White Sulphur 50; quotes say trailers up to N ft: right) |
| hunting season as camping season | **FIXED** (only Piney 'March through November', right) |
| 877 reservation line as phone | **FIXED** (0) |
| bare 'recreation.gov' booking url | **FIXED** (0) |
| footer phones | **FIXED** (0; but phones now on only 6 of 103: recall is thin) |
| duplicates 4 pairs | **MOSTLY FIXED** (Zilpo merged with an ids list; Twin Knobs x2 left) |
| LBL host / Bandy Creek sewer / 'some' hookups / Koomer Ridge | FIXED (earlier) |
| Piney sewer True from '44 sites with electric, water, sewer' | still True (should be 'some') |
NEW C's:
- **'13 sites' copied to 9 Forest Service campgrounds** (Bee Rock, Clear Creek, Great Meadows, Grove Drive-In, Holly Bay, S-Tree, Turkey Foot, Zilpo, White Sulphur): primitive 13 / total 13 from one shared page; Great Meadows even shows primitive 18 with total 13. These 9 sites numbers are wrong (they cause the 'sites DIFFER' rows).
- Breaks Interstate Park Campground: booking.url = 'shelter-pricing' (picnic shelter reservations) as the camping booking link.
- Wranglers: phone (502) 564-4696 (a Frankfort state number) vs key (270) 924-2200; its 'campground_page' points at the Energy Lake page.
Random 10 (seed 31, status ok): A 3 (Bandy Creek, Blue Heron, Barren Fork), B 6 (Whittleton, My Old Kentucky Home, Blue Licks: a booking link + lodging link only; Piney sewer; Higginson-Henry thin; Wranglers), C 1 (Breaks booking link) => 9/10 = 90%. Still 5 state-park records with only booking links (sites/hookups not read from parks.ky.gov).
Fixes for chat 10: (1) sites only from the park's OWN sentence ('N campsites'); a number that appears on 3+ campgrounds' records from one page is a page-level number: drop it; total must be >= its parts; (2) booking link must be a campground/camping reservation page, not shelters or lodging; (3) phone only if the line names that campground's office; (4) 'sewer'/'water' 'some' when only a subset has it; (5) gate: count 'some' = True and add the 6 key errors to a 'KEY IS WRONG' list so they stop counting; (6) read parks.ky.gov campground pages for sites/hookups; (7) merge Twin Knobs. For chat 2/9: fix the hand key (electric False per agency words; Brandon's list already in chat 10 NEEDS BRANDON).

## 4. DOCUMENTS bot v3 (data/docs/US-KY.json, ver 3)
Maps: 93 'ok' + 82 'opened, a readable map that does not name the park' (kept honestly, labelled) + 8 robots + 7 'page that does not name' + 1 resting + 1 404. Parks.ky.gov (resting) means state park rules are not read.
Finder check (25): 13 same, 5 other valid official page, 7 none: **18/25 = 72%** (was 17/25). Fixed: Wolf Creek (/map), Red River (USFS maps-guides), Jefferson NF WMA (KDFWR map image), Levi Jackson (levijacksonpark.com maps-policies), handover note: the bad Quiet Trails 1992-donation note is GONE, and Otter Creek now has a real 'operated by Meade County Fiscal Court'. Honest: Green WSR = 404 on the NPS backcountry map PDF.
Random 12 with a map (seed 41): 11 A (8 KY State Park map PDFs naming the park with a date, Sloughs, Jones-Keeney, Mammoth Cave maps page), 1 C (Jesse Stuart SNP: the generic EEC 'Energy/Data-Maps' page) => 11/12 = 92%.
Still wrong:
- **RULES: 30 of 193 parks (all OKNP preserves, state forests, 6 Wild and Scenic Rivers: Cumberland River Wilderness, Green, Rockcastle, Big South Fork, Rock Creek, Bad Branch, Green River SNA, Bat Cave, Kentenia, Kentucky Ridge, Knobs, Tygarts...) get https://www.kentucky.gov/policies/Pages/default.aspx = the state WEBSITE's privacy/terms policy page, marked ok.** 70 parks get the KAR 301 hunting regulation index (fine for WMAs, wrong for a preserve or a state forest).
- MAP: 15 parks (Rock Creek WSR, Cumberland River Wilderness, Jesse Stuart, other OKNP) get https://eec.ky.gov/Energy/Data-Maps/Pages/default.aspx: an energy-data page, not a park map. (Replaced the water-GIS page from the first run, same kind of mistake.)
- Rockcastle WSR map = fs.usda.gov/visit/maps (national generic page); Big South Fork NWSR 'a page that does not name'.
- Pine Mountain State Trail: resting.
Fixes for chat 2: (1) rules page must come from the park's own agency: for OKNP preserves/state forests use the agency's site rules or state 'none'; never kentucky.gov/policies, never an energy/water GIS page; (2) deny-list: kentucky.gov/policies, eec.ky.gov/Energy, eec.ky.gov/Environmental-Protection; (3) when parks.ky.gov rests, say 'rules page not read' instead of falling back; (4) Wild and Scenic Rivers: map from NPS / USFS maps page or 'none'.

## 5. INTAKE BOT (first test run; data/intake/review.md; own gate FAIL 8/10)
READY 3, ASK 1, REJECT 6. Grade of the 10 rows: A 7, B 1, C 2 => 8/10 = 80%.
- A: USACE reservoirs (READY, open terms on the item page, but 'closes 0 of 60' because tested parks are not reservoirs), PEI (ASK, nothing stated), Montana + Nevada (already read), Doorstep Greens, Millennium Greens (official, close none), hobby map (REJECT).
- B: SSSI England READY: 'closes 27' = 13 by name + 14 pin only. Per the house rule only a SURE match (pin inside + name + similar size) closes a park; pin-only rows like 'Marshside RSPB Reserve -> Ribble Estuary', 'Spurn Point NNR -> Humber Estuary', 'Hodbarrow RSPB -> Duddon Estuary' are far larger sites: the headline should say what the sure count is (13 at most, and several of those names differ too).
- C: SCDNR managed lands: 'did not open (error Invalid URL)' then REJECT; a read error must give ASK or RETRY, not REJECT. Czechia natural parks: READY on a copyright line from the SERVICE ('(c) krajske urady ... AOPK CR, 2022') and the test expects LIVE-ONLY: 'credit' terms without a licence on the publisher's item page are not READY (Nevada lesson).
Fixes for chat 10: error -> RETRY/ASK; terms must come from the item page; if only the service copyright is found = LIVE-ONLY or ASK; closes = sure matches only, pin-only listed separately with their size ratio.

## 6. SCOREBOARD (data/review/scoreboard-check.md, first run)
Bot counts vs chat 8's hand counts (UT, ON, ID, MS, OH, TN): 22 of 30 columns identical; differences: ON +22 total/+21 outline, ID +1/+5/-2/-2, TN +2/-2: small, explained (retired parks, keys move nightly, BLM names). **PASS.** North America totals 19,194 parks, 15,586 with an outline, 1,459 missing (HQ baseline 1,484); the 'north_america_pct_complete: 23' needs its definition on the page (81% have an outline; 23% must be a fuller all-columns figure). Not graded yet: per-park file scoreboard-parks.json against a sample, and the non-outline columns (hours, campground, closures, 2-fer checked).
