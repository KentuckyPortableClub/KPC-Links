# BREAKING RULE SHEET C: NAME MATCHING WHEN A LAYER DROPS THE TYPE WORD (desk, Oct 27 2026, 11 PM)
Read only. Grades: A = ran the real code or opened the page, B = search result only, C = inference. I did NOT write to any file in `.github/`. I imported `.github/scripts/kpc_us_key.py` (kinds, same_words, name_ok, exact_name, _fill) and ran it on the 13,074 US park names in `data/us-key/US-XX.json`, and read the 131 declared layers in `data/state-gis.json`. A layer's records were not queried (no network here), so what a layer holds is graded C unless the layer name/agency string says it.
**Verdict: the idea (supply the layer's kind) is sound for single-kind layers, but the sheet as drafted breaks on five things. Fix them in the sheet before chat 2 builds.**

## 1. What I found, in order of danger
1. **(e) the open one: yes, many hand-picked layers MIX kinds**, so one declared kind would be wrong for part of the layer (list in section 5). Worst: the FWS refuge layer declared 'wild' (so refuges would get kind wma), NPS units declared 'park' (kind sp), NC Natural Heritage 'Managed_Areas' declared 'preserve' (it holds every managed area), VA 'Local_Parks_2023' declared 'park' (county/city parks, which the house rule says are never a source), and the park-system layers that hold parks + historic sites + recreation areas + forests (MO, WI, MN, UT, WY, WA, GA, SC, MI).
2. **8.8 % of our US parks (1,152 of 13,074) have NO kind at all**, so `same_kind()` lets them match anything. Biggest: State Fishing Lake 298, State Trail 148, State Historical Monument 69, State Reserve 43, State Public Fishing Lake 16, State Harbor 16, Ecological Reserve 15, Forest Reserve 14, Unique Area 25, Multiple Use Area 24 (A: ran `kinds()`). A bare record with a declared kind joins a kindless park whenever the words fit. Real cases (all measured): KS 'Scott State Fishing Lake' joins Historic Lake Scott State Park; KS Crawford, Meade, Wilson (State Park AND State Wildlife Area), Woodson, Mined Land; GA Silver Lake, Ocmulgee, Big Lazer Creek (fishing lake joins its WMA); DE Trap Pond (fishing lake joins the state park); ID Dworshak, Lucky Peak, CJ Strike, Hells Canyon, Blackfoot Reservoir; WA Potholes, Loomis Lake, Fishtrap. This is the largest source of wrong joins and the sheet does not mention it.
3. **Chat 2's claim "today's matcher already refuses the 14 same-kind clashes" is wrong for 4 of them** (A, run on the real functions, full official names, no declared kind): section 2.
4. **The kind taxonomy itself counts a National Historical Park as a state park** (`sp` regex contains `historic(al)? park`): 'Natchez National Historical Park' = {hist, sp}, so Lewis and Clark NHP (OR/WA), LBJ NHP vs LBJ State Park (TX), Natchez, Saratoga, Thomas Edison, Blackstone River, First State, Harriet Tubman (MD) all share `sp` with a state park of the same words. Protected today only by the single-word `ka == kb` test; two-word names ('Lewis and Clark') slip by the 'and' word counting as a big word (len>2).
5. **The drop-both rule (4) does not cover the real failure: the SIBLING IS MISSING from the layer.** If the layer lists 'Sacramento' and not 'Sacramento River', then the park 'Sacramento River NWR' joins the 'Sacramento' record by words, and nothing sees a competitor. Rule 4 only works when both records are present.

## 2. (a) The 14 same-kind clashes, one by one (real functions, full names; "today" = no declared kind)
| State | Pair | Today | With bare record + declared kind | Verdict |
|---|---|---|---|---|
| CA | Sacramento NWR x Sacramento River NWR | **JOINS** (name_ok True, same_name True) | joins | **real hole**, two different refuges |
| CO | Gunnison SWA x Gunnison River SWA | **JOINS** by same_words | joins | **real hole**, 'river' is a different place's word |
| TN | Cheatham WMA x Cheatham Lake WMA | **JOINS** | joins | hole; may be one place (Corps lake part), NOT SURE |
| AR | Muddy Creek WMA x Muddy Creek WMA (US-11394 / US-7307) | joins | joins | probably the SAME place listed twice by POTA (duplicate number); report to HQ, not a matching bug |
| NE | North Platte NWR x North Platte NWR (US-0445 / US-13433) | joins | joins | identical names, two POTA numbers (one is likely a unit/district); 'same land, two numbers' |
| LA | Boeuf WMA x Lake Boeuf WMA | refuses | refuses | **saved only because 'boeuf' has 5 letters** (same_words needs 6+); 'Bayou Cocodrie' vs 'Lake Cocodrie' (7) would behave differently, but that pair also refuses (different second word). Rely on length = luck |
| NV | Walker Lake SRA x Walker River SRA | refuses | refuses | OK (two-word sets differ) |
| NY | Trout Lake SF x Trout River SF | refuses | refuses | OK |
| MI | Van Buren SP x Van Buren Trail SP | refuses | refuses | OK, by the trail test only (`same_name` itself says True) |
| WI | White River State Fish & Wildlife Area x White River State Wildlife Area | joins | joins | probably the SAME place under two POTA names |
| WA | West Foster Creek Wildlife Area x ... State Fish and Wildlife Area | joins | joins | same place twice |
| UT | Welcome Spring BLM SRMA x BLM RMA | joins | joins | same place twice |
| WI | Willow Creek F&W Area x Willow Creek F&W Area; Mud Lake SWA x Mud Lake SWA; WY Boulder Lake RMA x Boulder Lake RMA; WY Lone Tree Trail RMA x RMA | joins | joins | identical names, two numbers: duplicates or units |
So: **3 true cross-joins (Sacramento, Gunnison, Cheatham), 4 refused (2 by luck/trail test), the rest are one place with two POTA numbers.** The 'Lake X' / 'River X' / 'Creek' words must be a "feature word" test like the existing side-word test (`_side`): if one name carries lake/river/creek/bayou/trail/bay/island/mountain/ridge/spring and the other does not, refuse.

## 3. (b) 'Lake X' vs 'X Lake'
`wset` is a SET, so **'Lake Boeuf WMA' and 'Boeuf Lake WMA' are identical to same_words (True, A) but not to name_ok/same_name (False)**. Where the layer writes 'Lake Boeuf' and POTA 'Boeuf Lake' that is the same lake, correct. Where two different places share the words in other order (Walker Lake / Lake Walker): none found in our data (A: no pair with equal word sets and different strings exists in the 13,074 names). Lean: allow the swap for lakes only when the pin is inside or within 0.01 degrees; otherwise 'check by hand'. Louisiana's real pair (Boeuf vs Lake Boeuf) is NOT a swap, it is an added word, and is safe only by the 6-letter rule: add the feature-word test so it is safe by design.

## 4. (c) A park and its own recreation area; (d) county/city parks
- **(c) Indiana:** our list has **38 'State Recreation Area' numbers**, mostly "Unit on Lake" (Mounds on Brookville Lake, Quakertown on Brookville Lake, Paynetown / Hardin Ridge on Monroe Lake, Jackson / Lick Fork / Newton-Stewart / Tillery Hill on Patoka Lake, Dora-New Holland / Lost Bridge / Mt Etna / Mt Hope on Salamonie Lake...) (A). The IN layer is `ManagedLands_DNR_Open/FeatureServer/0`, one polygon per unit with a **manager** field (DNR State Parks / Fish and Wildlife / Forestry / Nature Preserves / Outdoor Recreation) (A). Because the key lists it as kind 'land' it declares nothing, so the sheet does not change IN. But if the unit is written as the lake ('Brookville Lake'), all units on that lake (Mounds + Quakertown, 10 miles apart) match one record by words (extra words ≤ 2): one outline for two parks = a false "same land, two numbers". In the matcher, SRA = `sp`, the same kind as State Park, so a park and its own SRA ('Pokagon State Park' x 'Trine at Pokagon SRA') cannot be told apart by kind (A: the test shows Pokagon joins Trine at Pokagon). Same in NE (Fort Kearny SHP x SRA, Rock Creek Station SHP x SRA, Buffalo Bill), HI (Waimea Canyon SP x Waimea SRA, Wailua x Wailoa), AR (Hobbs SP x Hobbs SP WMA). **Fix: give SRAs their own kind ('sra'), joined to 'sp' only when the name has no "on <Lake>" / "Unit" / "Station" extra words, and let a words-only join to ≥2 parks fall to 'check' unless the pin is inside the polygon.**
- **(d) County/city parks:** our US POTA list has none (only 22 'Park'-type numbers, all national or special: Rock Creek Park, Palisades Interstate Park...) (A), so a same-named county park is a LAYER problem, not a POTA-name problem. **`data/state-gis.json` lists VA 'Virginia DCR (local parks 2023)' as kind 'park' (A)**: that layer is county/city parks, which house rule says are never a source; with the declared kind a local 'Pocahontas Park' could join a state park. Remove it or mark it `skip`. Also check TN 'TN_State_and_Federal_Lands', AR 'lakes' (kind land: harmless).

## 5. (e) Layers that MIX kinds (graded C unless noted; agency strings are A)
| Layer (state-gis.json) | Declared | Why it mixes | Real case |
|---|---|---|---|
| NPS legal boundary, listed under AK CO HI MA NE NY OH PA RI SD | park (sp) | A: national units are not state parks; names like 'Delaware Water Gap', 'Boston Harbor Islands' are bare | record gets kind sp; its POTA twin is nps |
| FWS 'FWSApproved_Authoritative' listed under AZ CA FL | wild (wma) | A: it is NWR boundaries, not WMAs | NWR 'Sacramento River' gets kind wma and can join CDFW 'Sacramento River Wildlife Area' |
| NC 'NC_Public/Managed_Areas' | preserve (snp) | the NHP Managed Areas registry holds state parks, game lands, preserves, federal land | NC state parks would get kind snp |
| VA 'Local_Parks_2023' | park | A: county/city parks | house rule: never a source |
| MO 'Missouri_State_Parks_Boundaries/0' | park | the state park system includes State Historic Sites | historic sites get kind sp (they are 'hist': never get boundaries per HQ) |
| WI 'PR_WSPS_Property_Info' | park | parks system: parks, forests, trails, recreation areas | state forests get sp |
| MN 'plan_stateland_dnr/10' ("state land admin: parks…") and 'MN_State_Parks_and_Recreation_Areas' | park | parks + recreation areas + trails + waysides | trails (kindless State Trail 148) join parks |
| UT 'Utah_State_Park_Management_Areas', WY 'SiteBoundaries' (State Parks, Historic Sites & Trails), WA 'ParkBoundaries/2', NV 'VS_Boundary_Map_2' | park | park + historic + recreation areas | historic sites get sp |
| GA 'Georgia_Licenses_by_District/9', 'WRD_WMA_Public/14' | wild | WRD properties: WMAs + Public Fishing Areas + state fishing lakes | fishing lake joins WMA (GA Silver Lake, Ocmulgee, Big Lazer Creek) |
| SC 'SCDNR_Public_Lands_Viewer/4' | wild | WMAs + heritage preserves + public fishing lakes | |
| TN 'Hunting_Allowed', 'State_and_Federal_Lands_WFL1/49' | wild | WMAs + refuges + other hunting land | TN has Chickasaw SP / WMA / NWR |
| KS 'KDWPT_Wildlife_Areas' | wild | wildlife areas + state fishing lakes (Label_Name) | Wilson SWA x Wilson State Fishing Lake |
| WA 'WP_RealEstate/ManagedPlaces/0' | wild | WDFW managed places: wildlife areas + water access areas | |
| MI '…OPENDATA/8' (btaa record says "State Parks and State Recreation Areas, including parcels owned by others") | park | parks + SRAs (+ possibly harbors) | |
| IN 'ManagedLands_DNR_Open/0' | land (OK: declares nothing) | A: manager field has 5 values and owner/access fields | **best layer to use a per-record kind from the `manager` field, not a layer-wide one** |
| HI 'Infrastructure/16', 'Terrestrial/1' | park / wild | forest reserves, NARS, state monuments mixed | |
**Layers that look single-kind (lean: safe for the declared kind):** AL StateParks, AZ State Parks, AR StateParks, CA ParkBoundaries, FL PARKS_BOUNDARIES, MT FWPLND_STATEPARKS / FWPLND_WMA, ND, NM, OR, SD, TX State Parks, TN State Parks/Natural Areas/State Forests, OH ODNR Lands (one layer per division: parks /5, wildlife /7, forestry /6, preserves /8: the best-built set), WV, MN WMA/State forest/SNA, ID, LA, MS (when found).

## 6. (d, again) Declared kind across two states, Canada
- A layer listed under two states (the NPS and FWS layers above, Land Between the Lakes TN/KY): the kind travels with the entry, one per state, so a wrong kind is wrong in each. The sheet should say the declared kind is per ENTRY, never per service.
- Canada: the CA key is a different script (`kpc_ca_key.py`) and the state-gis entries for NB, PE, SK, NU, QC carry 'park' / 'wild'. French kind words (Parc national, Parc provincial, Réserve faunique, Zec, Pourvoirie) need their own list; I did not run the Canada key. Lean: leave Canada OUT of Rule Sheet C until it has its own test.

## 7. GREY AREAS (for Brandon), with my lean
| # | Grey area | Real example | Lean |
|---|---|---|---|
| N-1 | A layer holds several kinds. Which kind does a bare name get? | NC Managed_Areas; MO state parks + historic sites | Declare kind **per layer only for single-kind layers**; mixed layers need a `kind_field` (record's own type column) or stay kind-less; chat 2 marks each entry `pure: true/false` |
| N-2 | Kindless POTA types match anything | KS Scott State Fishing Lake joins Historic Lake Scott State Park | Add kinds for State Fishing Lake / Public Fishing Lake (`fl`), State Trail (`trail`), State Harbor, Unique Area, Multiple Use Area, State Reserve; kindless = **no words-join** |
| N-3 | A national historical park counts as a state park | Natchez, Lewis and Clark, LBJ, First State | `national` before 'historical park' makes it `hist/nps`, not `sp`; keep 'historical park' = sp only for State |
| N-4 | Sibling missing from the layer | Sacramento / Sacramento River | A words-join is refused when another POTA park in the state has the **exact** name of that record, or when the extra word is a feature word (lake, river, creek, bayou, trail, bay...) |
| N-5 | One record, many parks | Brookville Lake -> Mounds + Quakertown SRAs | A words-only join to ≥2 parks goes to check unless the pin is inside the polygon; SRA gets its own kind |
| N-6 | Duplicate POTA numbers for one place | Muddy Creek WMA (AR), White River F&W Area (WI), Welcome Spring (UT), Mud Lake SWA (WI), North Platte NWR (NE) | Not a matching rule: report to HQ as duplicate list; label 'same land, two park numbers' |
| N-7 | A county/city layer is in the table | VA Local_Parks_2023 | Remove it (house rule) |
| N-8 | 5-letter names saved by luck | Boeuf | Replace the length test by the feature-word test |
| N-9 | 'Lake X' = 'X Lake' | Boeuf Lake WMA | Allow when the pin is inside / within 0.01°; else check by hand |
| N-10 | Federal layers declared as state kinds | NPS 'park', FWS 'wild' | Federal entries declare nothing (kind set empty) or their own kinds (nps, nwr) |

## 8. What I would write into the sheet (for chat 2, after Brandon rules)
(1) What counts: a record from a layer marked `pure` whose declared kind matches the family of the POTA type. (2) Does not count: mixed layers, federal layers under state kinds, local-park layers, kindless POTA types (they join by exact name only). (3) Sources: unchanged. (4) Unsure: words-join refused when a feature word differs, when another park holds the exact name, or when two parks share one record without a pin inside. (5) People see: nothing new; join reason 'same name, kind from the layer'. (6) Examples: the table in section 2 and 5. Then rerun on ONE state first (MO or KS: both have the failures above), compare joins before/after, then the rest.
