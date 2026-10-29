# State parks inside or touching federal land: do both claim the ground? (chat 8, Oct 29 ~1:10 PM)
Brandon: "we need a plan to look at overlays: do both claim both lands, is there an overlap or hard boundaries?"
Grades: counts = A (hidden files read). Pair classifications = C (my knowledge of who owns what; no PAD-US owner/manager field was opened from here, the first test of the plan is to read it). 

## 1. The pairs we already hold (state x federal)
Pulled from every `fers/US-*.json(.gz)` row where one park is a state designation and the other federal (by the park type). 6,314 rows (rows, not unique pairs; a pair can appear in several passes).
| Federal side | live | not sure | dropped (side by side / sliver) | other (merged, tight, waiting, water) |
|---|---|---|---|---|
| Forest Service (NF, grassland) | 193 | 26 | 1,949 | 1,052 |
| NPS (parks, monuments, historic, trails, rivers) | 395 | 73 | 545 | 789 |
| Fish and Wildlife (refuges, WMD, WPA) | 71 | 22 | 746 | 261 |
| BLM | 2 | 15 | 50 | 33 |
| Corps / TVA / BOR | not countable: these lands are not POTA parks, so they never appear as a "federal side". They matter only as the OWNER of a state park's ground. |
Live by state: FL 71, MA 59, DE 55, KY 34, MN 33, NC 28, OR 26, CA 25 (NV 23, GA 21 close behind). Hard to say how many are right: that is what the plan tests.
The rows where a live pair is really a **trail** (NHT, Lewis and Clark, Trail of Tears x state parks and WMAs: all 34 of Kentucky's trail rows) are a different question (trail rule 100 ft), not this one.

## 2. The two cases (the whole question in one table)
| | LAYERED (both claim the same ground) | HARD BOUNDARY (side by side) |
|---|---|---|
| Ground | one owner, two names | two owners, two parcels |
| Example | Redbird / Mill Creek / Beaver Creek / Pioneer Weapons WMA on Daniel Boone NF: the land is Forest Service, Kentucky Fish and Wildlife manages hunting under an agreement. Bluestone State Park on Bluestone Lake: Corps land leased to West Virginia. | Cumberland Falls SRP and Natural Bridge SRP inside the Daniel Boone proclamation line: the state OWNS its park, the forest boundary just goes around it. Indiana Dunes State Park inside the National Park. |
| PAD-US | `Own_Name` = federal, `Mang_Name` = state (or a lease / cooperative agreement) | `Own_Name` = state on the park's parcels, federal on the rest; one holds a hole where the other sits |
| 2-fer? | **Yes**, a real 2-fer: the same ground is in both parks, public, open | **No**: the park is not part of the forest / national park; the proclamation line is not federal land (rule 2 of our list). Not "both claim" |
| Notice | normal 2-fer notice | none; it can sit in a "next to each other" list if Brandon wants it |

## 3. How to tell, best source first (per pair, per overlap patch)
1. **PAD-US Fee polygons, fields `Own_Name`, `Own_Type`, `Mang_Name`, `Mang_Type`, `Des_Tp`** at several points inside the overlap (not one point). Federal owner + state manager = LAYERED. State owner on the patch = HARD.
2. The federal agency's own land record: USFS **Basic Ownership** (it said "not Forest Service" for 14 rows already: those are HARD boundaries, the layer is right), NPS **Land Resources Division tract** layer (fee vs easement), Corps real-estate / Lake boundary, TVA land, FWS Approved Acquisition Boundary vs **fee-owned** land.
3. The state side: the state park page ("leased from the U.S. Army Corps of Engineers"), the state parcel layer, the lease or memorandum of agreement if posted.
4. POTA's own park page note if it says so (Brandon: POTA is the tiebreaker).
Special cases to separate:
- **Easement, not fee** (Natchez Trace, Blue Ridge Parkway, scenic rivers): the agency owns a strip or only a right; a state park beside it is HARD unless it sits on the easement strip.
- **Authorised / acquisition boundary** (NPS, FWS): a line drawn around the area the agency MAY buy. State parks inside are HARD until bought.
- **Wild and Scenic River corridor** (NPS): the corridor is drawn around the river; state land inside stays state. HARD, unless NPS owns the strip.

## 4. Twenty pairs (C: from what I know; each says what to read)
| # | Pair | My call | Evidence to read |
|---|---|---|---|
| 1 | Redbird WMA x Daniel Boone NF (KY, 23,900 ac) | **LAYERED** | NF land, KDFWR cooperative WMA; PAD-US Own = USFS, Mang = KDFWR |
| 2 | Mill Creek WMA x Daniel Boone NF (12,865 ac) | LAYERED | same |
| 3 | Beaver Creek WMA x Daniel Boone NF (17,534 ac) | LAYERED | same |
| 4 | Pioneer Weapons WMA x Daniel Boone NF (7,708 ac) | LAYERED | same |
| 5 | Cane Creek WMA x Daniel Boone NF (6,649 ac) | LAYERED | same |
| 6 | Zilpo and Twin Knobs Campground "WMA" rows x Daniel Boone NF | LAYERED | USFS campground names POTA uses |
| 7 | Cumberland Falls SRP x Daniel Boone NF (KY) | **HARD** | state-owned park (given 1930s), hole in the NF map |
| 8 | Natural Bridge SRP x Daniel Boone NF (KY) | HARD | state-owned; the Red River Gorge units sit around it |
| 9 | Little Sextons Creek WMA x Daniel Boone NF (611 ac, NOT SURE) | UNCLEAR | probably a state WMA bought parcel by parcel inside the forest: needs PAD-US |
| 10 | Kentenia State Forest x Daniel Boone NF (3.9 ac, NOT SURE) | HARD (a sliver) | state-owned forest beside |
| 11 | Kenlake / Kentucky Dam Village SRP, Lake Barkley SRP, Lake Cumberland SRP | LAYERED to their lake, but the lake owner (TVA / Corps) is not a POTA park so no pair | the pair exists only if POTA numbers the TVA / Corps tract |
| 12 | Kentucky Lake WMA x Fort Heiman / Fort Donelson (79 ac) | UNCLEAR | Fort Heiman is a county park; Donelson NPS; check owner |
| 13 | Indiana Dunes SP x Indiana Dunes NP (IN, 371 sessions) | **HARD** | state-owned park inside the NP authorised boundary |
| 14 | Point Mugu SP x Santa Monica Mountains NRA (CA) | HARD | state-owned parcels inside an NRA of mixed ownership |
| 15 | Mason Neck SP x Mason Neck NWR (VA, 5 ac) | HARD (adjoining, a sliver where the two maps differ) | FWS fee vs state fee |
| 16 | Lower Hatchie NWR x Fort Pillow SP (TN, 0.9 ac) | HARD (sliver) | same |
| 17 | Bluestone SP x Bluestone Lake WMA (WV, 13,036 ac) | **LAYERED** | Corps land, WV DNR manages both; but see section 6: the SP outline looks too big |
| 18 | Lake Hartwell SP x Brasstown Creek WMA (SC), Dillon SP x Blackhand Gorge (OH) | UNCLEAR | Corps lakes: a state park on leased Corps land next to a state preserve |
| 19 | Mission Tejas SP x Davy Crockett NF (TX, NOT SURE) | HARD | state-owned park, NF around it |
| 20 | Current River SP / Rocky Creek CA / Sunklands CA x Ozark NSR (MO, 12 rows low-confidence) | HARD (most) | NPS owns the riverbank strips; state parks are state parcels; the NPS boundary map is the question |
Also noted: Washington Crossing SP x Lower Delaware W&S (NJ, 269 sessions) = HARD (corridor drawn around state land); Missouri Mark Twain NF x state conservation areas = checkerboard, each parcel HARD or LAYERED by parcel; Merritt Island NWR x Canaveral NS = federal x federal on NASA-owned ground (LAYERED, both agencies manage NASA land by agreement: it is a different question, not state).

## 5. The plan: rule sheet R-SF ("state park and federal land")
1. **What counts as a 2-fer:** the overlap patch (at least 50 yd across) lies on ground where the federal agency is the OWNER and the state is the MANAGER, lessee or co-manager under an agreement (LAYERED), the ground is public and open, and both designations legally apply there.
2. **What does not count:** a patch where the state or a local government is the OWNER and the federal map is only a boundary or proclamation line around it (HARD); a federal easement strip beside a state park; an acquisition-boundary overlap with private land; slivers where two maps disagree over one border.
3. **Sources, best first:** PAD-US `Own_*` / `Mang_*` at 5-20 sample points inside the patch; the federal agency's tract layer; the state's park page or lease; the state parcel layer; POTA's park page.
4. **When unsure:** NOT SURE. A patch with mixed owners (some federal, some state) is judged by the part that is at least 50 yd wide; if only a sliver is mixed, HARD.
5. **What people see:** LAYERED pairs use the normal 2-fer wording and notice. HARD pairs are not shown as 2-fers. (If Brandon wants a separate "inside the boundary, different owner" group, it gets its own label and the notice, never "2-fer".)
6. **Examples:** rows 1-20 above. Hard ones: 9, 12, 18, 20.

### How the line tests it automatically
Per overlap patch: sample points on a grid (5-20 points, each at least 25 yd inside the patch); for each point read PAD-US Own / Mang / Des_Tp (ask for points, never the whole polygon, which times out in the West); then
- all points federal-owned + state-managed -> LAYERED -> live
- all points state-owned -> HARD -> dropped, reason "state owns this ground; the federal line goes around it"
- mixed (each side at least 50 yd) -> split: count only the layered part
- no answer / unknown owner -> NOT SURE (and log which source failed)
Write the owner/manager of the middle point in the row (`owner_here` is already a field), so the row explains itself.

## 6. Grey areas for Brandon
1. **Simple test vs owner test.** His Oct 28 test (8:17 PM) says two official boundaries that overlap even a few feet on public ground = 2-fer. A state park inside a national forest's proclamation boundary passes that test but fails rule 2 (a proclamation line is not federal land). Which wins for state-owned parks inside a federal boundary? My lean: owner test (HARD = no 2-fer), with a visible "next to it" mention. Indiana Dunes SP + NP (371 activator sessions) and Cumberland Falls + Daniel Boone are the test cases.
2. **Mixed patches** (FWS + state in one overlap, 22 NOT SURE rows): Brandon's simple test says live; the owner test says sliver = HARD unless the layered part is 50 yd across. I withdraw my earlier "should be live" for slivers under 5 acres (Lower Hatchie 0.9, Brasstown 0.5).
3. **Corps / TVA lakes** have state parks on leased land but no POTA park for the federal side: nothing to pair. Say so on the page, don't invent a pair.
4. **Easement strips** (Natchez Trace, Parkway): HARD, but the trail-line rule (100 ft) may still apply to the trail itself.

## 7. Chat 2's questions
- **Channahon SP (US-0987) x I&M Canal State Trail (US-10660):** the only row is **0.3 ac, dropped in pass 3**, and it was tested as an AREA. The I&M Canal State Trail has an official outline (`off`) and runs through the Channahon parkway along the canal (631 sessions). It should be tested as a TRAIL with the 100 ft rule, not the 50-yard patch rule. I&M x Des Plaines FWA is the same: 0.4 ac x 3, dropped. Recommend: re-test any pair where either park's type is Trail / State Trail as kind "trail".
- **Bluestone (WV):** Bluestone NWSR x Bluestone SP is live at **2,989 ac**, and Bluestone SP x Bluestone Lake WMA at **13,036 ac**. Bluestone State Park is about 2,155 acres, so overlaps larger than the park prove the SP's outline was joined to the wide Corps / WMA record. **Fix the US-1804 join** (it should be the park's own record near Hinton). The NWSR x SP overlap needs a redo with the right outline.
- **Pine Creek Gorge (PA):** the Pine Creek Gorge parks are Colton Point SP (US-1344, PAD-US outline) and Leonard Harrison SP (US-1374, official outline) inside Tioga State Forest (US-5478). **Neither park has any row with Tioga SF in the files (not even a dropped one)**, while Tioga SF is paired with 9 other parks. Cause is probably that the Tioga SF outline has a hole where the two state parks sit (same owner, DCNR, different maps): then they are side by side and the correct answer is to tell activators it is not a 2-fer. If the forest outline has no hole the pair row should exist: chat 2 to check the outline.

ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go.

## CORRECTION (chat 8, Oct 29 2:00 PM): read with Brandon's Oct 28 rulings
Brandon 8:31 PM: a patch owned by more than one PUBLIC body inside two overlapping official boundaries IS a 2-fer (only private pieces are cut out). 8:34 PM: ownership questions belong in STEP 1 (getting the right boundary for each park, e.g. a national forest = agency-owned land with private and state inholdings cut out); the 2-fer line does not re-argue a patch that sits inside two official boundaries. So R-SF is a rule for step 1: a state park inside a national forest is a HARD boundary because the forest's own outline already has a hole there. Where the two official outlines DO overlap, even by a sliver, on public ground, the answer is LIVE; I withdraw my section 6 grey area 2 ("slivers = HARD") and the "leave slivers out" lean. Grey area 1 still stands only for forests whose outline is a proclamation line, not agency-owned land.
