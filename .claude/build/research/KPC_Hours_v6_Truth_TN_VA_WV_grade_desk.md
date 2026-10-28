# Hours (Kentucky, latest) + truth checker TN/VA/WV — chat 11, Oct 28 ~5:10 PM CDT
## HOURS / FEES / PERMITS (KY): quality PASS on what it finds, recall + own gate still FAIL
- Own gate: 10/27 known hours rows = 37% (was 24%); marked FAILED.
- Parks with any hour/fee/permit: 48 of 193 (25%; was 20 of 193).
- Random 12 (seed 5): **A 8, B 3, C 1 = 92%.** A: Pilot Knob, Blackacre (weekday 3 pm-dusk, weekend dawn-dusk), Big Bone Lick trail, Wolf Creek hatchery (8-4, no fee), Audubon, Blue Licks, Tom Sawyer (10 pm close), Reelfoot. B: Isaac Shelby (state tourism PDF, labelled), Carter Caves (dawn-dusk + $5 adults), Peabody (right $15.86 permit but also the statewide $5.29 shooting-range price). **C: Griffith Woods WMA = "In some areas, a user permit is required" (statewide hunting page, not this area), repeated 3x.**
- Fixed since Regrade 3: headings, duplicates, statewide licence prices mostly gone; 'agency-wide rule rows' are now left out of the gate (10 rows).
- Left to fix: (1) statewide hunting-page permit sentences still land on single WMAs (Griffith Woods, Peabody's $5.29); (2) 145 parks have nothing (recall; mostly WMAs and nature preserves with no hours on a page); (3) hours on the gate: Otter Creek, US-3781, US-7966, US-7956 still missed.

## TRUTH CHECKER TN / VA / WV (bot says gate PASS for TN)
Counts: TN 1 agree / 8 off / 4 unsure / 237 no size on page / 23 no outline; VA 6 / 73 / 42 / 35 / 28; WV 1 / 96 / 26 / 37 / 12.
- **TN flagged 8: 5-6 right.** Right: Cross Creeks 13,158 vs 8,862; Tennessee NWR 21,684 vs 51,000; Bays Mountain 12,192 vs 3,788 (our figure wrong); Beaman Park; Fort Donelson (844 vs 1007, correctly marked 'as of 2010'). **Wrong kind: Great Smokies, Big South Fork, Chickamauga** are flagged against the WHOLE park total (522,427 / 125,000 / 9,000) while ours is the Tennessee part: needs 'crosses a state line' (the page says 'KY,TN' / 'NC and TN'), not 'off'. 237 of 277 parks have no size on a page = most state natural areas/WMAs have no acreage line (recall gap, honest).
- **WV flagged 96: 76 are ONE number.** Every WMA gets "1.4 million acres" from the wvdnr WMA index page (the statewide total) as its official size. Random 7 WV 'off': 1 right (Watoga 20,419 vs 10,100 = two units merged), 6 junk = 14%.
- **VA flagged 73: random 7 = 3 right (Conway-Robinson 1,779 vs 440, Harrison Lake 1,129 vs 444, Wilderness Road 1,570 vs 327) and 4 junk = 43%.** Junk: 13 natural areas get "66,000 acres" (all Virginia natural area preserves); Hungry Mother = the 108-acre LAKE; Booker T. Washington = a 207-acre FARM in the history text.
Verdict: FAIL for WV and VA (bar 90%; the junk is systematic), TN flags usable once cross-state parks are handled.
## Fixes (chat 10)
1. A figure on a page that 3+ parks share (same URL + same number) is never a park's size: drop it (kills WV 76 and VA 13).
2. Skip "acre" sentences that name a lake/pond/farm/preserve system ('108-acre Hungry Mother Lake', '207-acre farm', 'sixty-nine preserves encompassing').
3. Park on a state line ('KY,TN', 'NC and TN', GA+TN): compare to the whole-park total only with the other state's pieces added, else label 'crosses states', never 'off'.
4. Hours: drop hunting-page permit sentences that do not name the area; keep the gate rows list.
