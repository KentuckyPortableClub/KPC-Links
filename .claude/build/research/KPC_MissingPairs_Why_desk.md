# Missing 2-fers: what is missing and why (chat 8, Oct 29 2026, ~10:50 AM)
Brandon: "check the passed 2fer reports per park and look for missing stuff, make a report after you look for why it is missing."
Sources (all read, nothing run): chat 2's MISSING CHECK files `KPC-Data data/fers/expected-*.json(.gz)` (24 areas: FOUND / DROPPED / NEVER LOOKED AT, each with a reason), POTA "same session" hints `pota-pairs-US-*.json` (same call, same day, identical QSO counts at both parks; a hint, never proof), `missing-*.json`, `scoreboard-parks.json`. Grades are C (names + counts + my knowledge); no polygon opened.

## 1. The numbers (pairs POTA history says go together)
- FOUND (we list them): 2,049
- DROPPED (the bot looked and said no): 5,907 = 4,471 "no shared ground" + 1,253 "dropped in pass 2/3" + 47 not sure (owner map silent) + a few water/closed/wrong-join
- NEVER LOOKED AT (no test was possible): 68,947 = 28,932 "outline boxes do not touch" + about 36,000 where **a park has no official boundary or only an approximate one** + 6,560 "not in this run" (other state / retired / no pin)
- Of the 10,930 pairs where POTA shows **one session logged both parks 10+ times** and we have no row: 5,627 boxes apart, ~3,000 a park without a boundary, 941 not in the run, 699 no shared ground, 466 dropped in pass.

## 2. WHY it is missing, biggest first
1. **A park has no outline (or a rough one).** 1,455 parks "missing", 1,790 pin-only. They cannot be tested at all, and a few carry huge evidence. Worst blockers by activator sessions: Baltimore-Washington Parkway US-7973 (pin only, 8,600), Erie Canalway US-6532 (pin only, 4,500), National Mall and Memorial Parks US-0655 (pin only, 2,400), Trail of Tears NHT US-3791 and Lewis and Clark NHT US-4572 (missing, 3,700 / 2,200), Columbia River Gorge NF US-0731 (no layer, 2,400), Pinelands Preserve US-6609 (no layer, 2,700), Michigan WMD US-0350.
2. **Long trails and routes.** The biggest evidence of all sits on trail numbers: Captain John Smith Chesapeake NHT (18,800), Virginia Bird and Wildlife Trail (11,300), Star-Spangled Banner NHT (7,300), Oregon NHT, Washington-Rochambeau, Civil War Trail, Ice Age Floods, NJ Coastal Trail, Mountains to Sea, Potomac Heritage, California NHT, Florida Trail. The scoreboard now says these are `line` outlines, but the missing check still gave "no official boundary" as the reason: **either the check ran before the lines were in, or lines are not tested against parks at all.** Ask chat 2 which. If it is the first, a rerun of the check after the line data lands will move thousands of pairs from NEVER LOOKED AT to tested. NPS publishes route lines for every National Historic Trail (National Trails System layer): that is the one source that fixes most of this list.
3. **Boxes do not touch (28,932).** Mostly honest: activators log neighbours and trails in one session ("hint, never proof"). Not a gap. But the top of this list is odd enough to be worth a pin/outline look: Green Swamp Wilderness Park Reserve US-5330 with Van Fleet Trail, Withlacoochee SF and Colt Creek SP (540-760 sessions each), Don Carter SP + Fort Yargo SP (287, 46 km apart), Holland Bottoms SNA + WMA (259, 1 km: this one is a same-land pair that sits on the missing-boundary list, not a gap in the test).
4. **Dropped for no shared ground (4,471).** Mostly right (neighbours). The ones I would re-look because real activators call them 2-fers:
   - Jonathan Dickinson SP + Loxahatchee River NWSR (592 sessions, 4 km): the river runs through the park; looks like a river-line/100 ft rule miss.
   - Merritt Island NWR + Canaveral National Seashore (197): the two share ground.
   - Indiana Dunes NP + Indiana Dunes State Park (371), Golden Gate NRA + Fort Point / Mt Tamalpais SP, Point Reyes + Tomales Bay SP, Santa Monica Mtns NRA + Point Mugu SP, Lower Delaware W&S + Washington Crossing SP: state land inside a federal boundary. This is a **policy question for Brandon**, not a bot bug: rule 14 (ownership) drops them because the state park is not federal land, but POTA activators count them. See section 4.
   - Greenbelt Park + National Capital Parks (1,422; "dropped in pass"), Gettysburg NMP + Eisenhower NHS (213), Channahon SP + I&M Canal State Trail (631), Falls Lake SRA / Butner-Falls + Mountains to Sea Trail (343 / 257): ask chat 2 for the reason text and the overlap size.
5. **Not in this run (6,560).** Pairs where one park sits in a state not yet run, or retired, or no pin. Not missing, not done yet (Pacific, Ontario and the world are still stopped).

## 3. Good news
No FOUND pair I checked is a wrong one beyond those already reported (Truman, Salinas, Horseshoe Canyon). Parks with an outline get a row about 35% of the time everywhere (US official 37%, PAD-US 32%, Canada 34-38%), so no state looks starved. Parks with no outline get a row 1% of the time, which proves the outline is the bottleneck.

## 4. For Brandon (one ruling)
**State park inside a federal unit** (Indiana Dunes SP in the NP, Point Mugu SP in the Santa Monica Mountains NRA, Fort Point in Golden Gate...). Our rule says park = where the designation legally applies, so the state land is not part of the federal unit and we drop it. POTA activators log them as 2-fers anyway (dozens to hundreds of times each). Options: (a) keep dropping, (b) list them in their own "inside the boundary, different owner" group with the notice, never as a normal 2-fer. This is a grey area; I lean (b). Waiting on his word.

## 5. Asks
- Chat 2: (1) was the missing check run before the trail lines? rerun it; (2) the reason text and overlap size for the section 2.4 list; (3) tell me if "boxes do not touch" uses the box of the whole trail (a long trail's box would touch everything; a short one nothing).
- Chat 9 / look-up: NPS National Trails System route lines; boundaries for Baltimore-Washington Parkway, Erie Canalway, National Mall, Trail of Tears, Lewis and Clark NHTs, Pinelands, Columbia River Gorge.
- Chat 8 next: grade the rerun when it lands.

ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go.
