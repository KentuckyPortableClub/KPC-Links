# Park truth checker, Kentucky: GRADE (chat 11, Oct 28 2026)
Run graded: KPC-Data run 40669098603, data/truth/US-KY.json + review.md, ver 3 (after chat 10's T1..T6 fixes). 193 parks: 98 agree, 5 OFF, 14 unsure, 72 no size, 125 handover-hint rows on 49 parks.
Bar: A+B >= 90% on 10-12 items. A = right park, right number, right verdict. B = right verdict but a wrong or weak reason/number. C = wrong page or wrong number that a person would act on, or a verdict that should be different.

## RESULT: FAIL (9 of 12 = 75%). Flagged items only (all 5 OFF + 14 unsure): 15 of 19 = 79%. "agree" rows look good.

| # | ref | park | bot says | grade | why |
|---|---|---|---|---|---|
| 1 | US-3800 | Cedar Creek Lake WMA | OFF: ours 2,390 vs KDFWR 796 | A | KDFWR's own page for this WMA ("Size: 796 acres, Lincoln"). Real find; our outline probably holds water or a neighbour. |
| 2 | US-0050 | Mammoth Cave NP | OFF: 71,228 vs 52,831 | A | NPS statistics page for the park; cause class (boundary vs owned) is a sensible label. |
| 3 | US-10105 | The Green National Wild and Scenic River | OFF: 6,984 vs 52,830 | **C** | WRONG PAGE: 52,830 is Mammoth Cave NP's total area (maca/statistics.htm), not the river. A false OFF. (Also bears on chat 8's question to Brandon about which "Green River" this is.) |
| 4 | US-1264 | Levi Jackson Wilderness Road SP | OFF: 722 vs 896 + handover | A | levijacksonpark.com history page; ALSO caught the real 2019 state-to-City-of-London transfer. Best find in the batch. |
| 5 | US-12752 | Green River State Natural Area | OFF: 304 vs 440 | B | Real mismatch likely, but the page is the Rush Island Bottoms preserve page and our record is two pieces (Davis Bend 165 + Rush Island 139); the cause text ("may miss a tract") is a guess. |
| 6 | US-0295 | Clarks River NWR | unsure; official "73,962 acres" | B | Number is the 1700s land grant to George Rogers Clark ("Two grants totaling 73,962 acres were conveyed"): the history filter (T2) missed this wording. Verdict "unsure" is only right by luck. |
| 7 | US-10104 | Red River NWSR | unsure; official "879 acres" | **C** | PARSE BUG: the sentence says "708, 879 acres of national forest" (Daniel Boone NF); the bot read 879. Also first number on the page is an 8,270-acre lake. Garbage number printed in the review. |
| 8 | US-4689 | Kentucky Ridge State Forest | unsure (23% off) | **C** | Clean official sentence "consists of 15,251 acres", ours 11,736 = 23% off, over the 15% rule: should be OFF. Shown as unsure with NO cause. |
| 9 | US-3792 | Land Between the Lakes NRA | unsure (170,000 vs 106,948) | A | 170,000 is the whole TN+KY area; ours is the KY side. Unsure is the right call. |
| 10 | US-3820 | Kentucky River WMA | agree (3,623 vs 3,643) | A | KDFWR page, name matches, 1% off. |
| 11 | US-4688 | Kentenia State Forest | agree (4,060 vs 4,081) | A | eec.ky.gov Kentenia page, "seven scattered tracts totaling 4,081 acres". |
| 12 | US-3825 | Miller Welch WMA | agree (1,836 vs 1,847) | A | KDFWR page. |

Extra rows I also graded from the data (not in the 12): B: US-0019 Cumberland Gap (the "14,000 acres" is "14,000 acres of wilderness" marketing; NPS unit is about 24,000, stayed unsure), US-0538 Reelfoot (11,556 is HATCHIE NWR's size, wrong refuge), US-0703 Fort Donelson (29% off but unsure; 1,007 acres is "as of 2010"), US-10098 Green River NWR (9,500 beside "10 acres donated"; 77% off but unsure, no cause), US-1271 Taylorsville Lake SP (248 = a map label), US-13599 Kingfisher Lakes ("21.2 and 13.8 acre lakes" = 35.0 vs ours 34: should AGREE, the bot took only 13.8), US-7962 Little South Fork (page is the Burnett WWCA preserve, different name). C: US-3790 Fort Heiman (compared with Fort Donelson's page and outline). A: US-10107 Big South Fork NWSR and US-4526 GW&J NF (container figures correctly left unsure).

## Handover / closure hints: FAIL (about 85% noise)
- 125 rows on 49 parks. 82 rows come from 3 generic pages: eec.ky.gov/About (64 rows: a staff biography, "transferred to the Division of Waste Management"), nps.gov/aboutus/accessibility (9: Access Pass text), nps lawsandpolicies (9). 18 more are just "Owned by U.S. Forest Service / KDFWR" lines on KDFWR pages (ownership, not a handover). Old gifts and donations (Kentenia 1919, Quiet Trails 1992, Lee K. Nelson, Clark land grant) are history, not a change.
- Real signals, only about 7 of 49 parks: Levi Jackson (to City of London 2019), Otter Creek SRA (to Meade County Fiscal Court 2026), Clyde Buckley Sanctuary (Bluegrass Greensource), Blackacre (JCPS + conservancy), Tom Dorman (ex-Kentucky River Authority), White Hall (county maintains playground/pond/trail), Fort Heiman (2006 county transfer).
- Why it happens: while looking up Green WSR etc. the bot also reads unrelated eec.ky.gov pages (/About, Air Quality Regulations, Archived Regulation History): the agency's parent site is being crawled.

## "agree" class (98): good, with two cautions
- 11 checked (8 random + the 3 above): all A, name on the page matches.
- 67 of the 98 are KDFWR outline vs KDFWR page (same agency): that proves our copy matches KDFWR, not that KDFWR is right. Say so on the card/review ("same agency").
- 4 agree rows have no park-name match in the page line/URL: US-13607 Boltz Fishing Lake (fisheries wid=50), US-3801 Clifty Wilderness (a general Daniel Boone "about-area" page), US-3802 Clyde Buckley (bggreensource.org), US-7957 Hall-Hill/Vernon-Douglas. Not graded yet: please check.
- 22 "agree" parks have the POTA pin OUTSIDE our outline (Hoskins, Kentucky Ridge WMA, Doug Travis, Obion Creek, Blanton Forest, Tom Dorman, Crooked Creek, Pilot Knob, Wm H Martin, 5 fishing lakes...). Size agreeing while the pin sits outside can mean the wrong tract or just an entrance pin: for chat 2 (43 pin-outside parks in all, list in chat 2's inbox).

## Other
- 1 bot error: US-12083 University of the Cumberlands WMA: "URL can't contain control characters" (spaces in the PDF path; quote the path).
- Gate (state.json): PASS on 2 known answers only (Levi Jackson, Otter Creek). Too thin: it passed while 4 of 19 flagged rows were wrong.
- Cause class is None on all 14 unsure rows: a reviewer cannot tell why.
- fw.ky.gov strike/403 handling worked (1 strike, no failures).

## Fixes for chat 10 (sent to its inbox)
1. Number parse: "708, 879" must not become 879 (read comma-space as one number); skip numbers in sentences that name a lake, a forest, a county or "container" words unless the park's name is in the same sentence.
2. Other-unit pages: if the page or statistics URL belongs to a different unit (maca for Green WSR, fodo for Fort Heiman, Hatchie for Reelfoot), drop the number. Require the park's name core (6 letters) in the sentence or in a labelled "Size/Total Area/Park Size" row for THAT park.
3. History words: add "grants", "conveyed", "deeded", "patent", "totaling", "of wilderness" (marketing), "as of 20xx" older than 3 years = stale, show the year.
4. Unsure must carry a cause, and a clean official number more than 15% off is OFF: Kentucky Ridge SF (23%), Green River NWR (77%, say the page also lists 10 acres), Fort Donelson (29%, stale 2010 figure, say so).
5. "A and B acre lakes": sum the pieces before comparing (Kingfisher).
6. Handover hints: read only the park's OWN page; never /About, /accessibility, /lawsandpolicies, news; park name must be in the sentence; drop "Owned by"; keep a hint only if it has a year of 2000 or later or the words "now", "currently", "transferred to", "managed by" next to a different owner than the one in our land record. Output the owner change as "old owner -> new owner, year".
7. URL with spaces: quote it.
8. Gate: add 8 known answers from this grade (US-10105 must NOT compare to Mammoth Cave; US-10104 must not read 879; US-0295 must not use 73,962; US-1264 OFF + handover; US-0703/US-3790 not both the same page; US-10098 and US-4689 must be OFF).
