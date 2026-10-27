# KENTUCKY 2-FER RE-CHECK after chat 2's rerun (Research desk, chat 8, Tue Oct 27 ~8:30 AM)

Checked: `data/fers/US-KY.json` as of commit c2470595 (165 spots: 48 pair groups kept as candidate / very tight / not sure). By the final rules 1-14 and the HQ rulings. **What I could and could not do:** I read the data and the official pages (KDFWR, Forest Service, Kentucky Nature Preserves), but I cannot see polygons and could not query the map layers, so the geometry (is the patch really 50+ yards, is the pin really inside) stays with chat 2's bot. My verdicts are about WHETHER the pair is allowed (owner, public access, rule fit), not about the shape.

## 0. Headline
1. **Only 6 of the kept rows are "fresh"** (the Trail of Tears x Lewis and Clark rows). Every other kept row says "saved outline only". Under the Finder sheet (rule 1) those stay HIDDEN until a fresh pass, so the public Kentucky list would have 6 rows, not 104. Chat 2 should say whether the next run refreshes the outlines.
2. **Sheltowee Trace x Daniel Boone = 50 rows.** The trail lies wholly inside the forest, so every stretch on Forest Service land is a "2-fer" by definition. Show it as ONE row for the pair (the Finder rule: up to 3 pins, nearest a road first), not 50.
3. **Three official-link problems** in the `maps` fields: Fort Donelson's map button is a POTA page (https://next.pota.app/park/US-0703), not an agency map. Fix to the NPS map (https://www.nps.gov/fodo/planyourvisit/maps.htm is already used for Fort Heiman and covers both).

## 1. KEEP (official source supports it)
| Pair | Why | Source (grade) |
|---|---|---|
| Redbird, Beaver Creek, Cane Creek, Mill Creek, Pioneer Weapons, Twin Knobs, Zilpo WMAs x Daniel Boone NF | KDFWR's own pages say each is owned by the U.S. Forest Service: real layering (Forest Service land managed by KDFWR) | `data/ky-wma-owners.json` (KDFWR Public Lands Search), https://fs.usda.gov/r08/danielboone/recreation/cane-creek-wildlife-management-area (A) |
| Clifty Wilderness x Daniel Boone NF (12,359 ac) | a wilderness inside the forest on Forest Service land | Forest Service (A earlier) |
| Wild river corridors x Daniel Boone NF (Cumberland River, Red River, Rock Creek, Rockcastle) and the 3-fer Red River + Clifty + Daniel Boone | area parks (Brandon's ruling); the ownership test says "layered on usfs land" | `ky-wild-rivers.geojson` + chat 2's ownership step (B for the test) |
| Rockcastle WSR x Cane Creek WMA (+ Daniel Boone 3-fer) | Cane Creek is Forest Service-owned | KDFWR (A) |
| Mammoth Cave NP x Green River (6,855 ac) | one owner (NPS), corridor on park land | the bot (B) |
| Bad Branch WSR x Bad Branch State Nature Preserve (1,206 ac) | one owner, state | the bot (B) |
| Sheltowee Trace x Big South Fork NRA, x Big South Fork WSR, x Cane Creek WMA, x Mill Creek WMA, x Clifty | line park (100 ft from the trail) over public land; only valid if the trail line used is the Forest Service's own line | see line note below |
| Sheltowee Trace x Daniel Boone NF | same; show as ONE row | -- |
| Carter Caves SP x Bat Cave (134 ac) and x Cascade Caverns (20 ac) preserves | one owner (state), layered. **Seasonal note required (rule 10): "the caves are closed to public visitation from October to May. The hiking trails on the portion of the preserve which is above ground are open year round."** Today (Oct 27) the caves are closed, so the spot must be above ground. Cascade Caverns: steep banks above Tygarts Creek listed as a hazard | https://eec.ky.gov/Nature-Preserves/Locations/Pages/Carter-Caves.aspx (A) |
| Trail of Tears x Lewis and Clark (6 fresh rows) | both water routes; spots on public land within 100 ft of the river edge, tested against the NHD shoreline | grey case 6 (trail x trail) is still OPEN; fine to list as "possible" once Brandon rules |

**Line note:** the Sheltowee Trace and the two national trails are line parks. The 100-ft test is only as good as the line. The Forest Service's own Sheltowee Trace line is the right one; chat 2 should write in the data which line was used (and its date). NPS trails are labelled approximate.

## 2. VERY TIGHT (members' list only), unchanged
Pioneer Weapons x Zilpo (1.1 ac, +3-fer with the forest) and Ross Creek x Daniel Boone (3.3 ac). **Ross Creek:** KDFWR's news page says the WMA "expands to almost 1,300 acres" (about April 2026; https://fw.ky.gov/News/Pages/Ross-Creek-WMA-expands-to-almost-1,300-acres.aspx, A) and the page does not name the owner. The saved outline may pre-date that expansion: refresh before any result.

## 3. NOT SURE (kept out of the guide)
| Pair | Why |
|---|---|
| Hoskins WMA x Daniel Boone NF (6 patches, 1.9 to 43 ac) | KDFWR's page names no owner and I found no official page that does. By HQ's ruling chat 2's Basic Ownership test decides ("layered on usfs land"), so it can stay in the kept set, but the owner is **not independently confirmed** (grade C). Most patches are small acreage: confirm each is 50+ yards. |
| Sunny Brook WMA x Daniel Boone NF (9 ac, "borderline 50 m") | KDFWR's map PDF labels the forest around it but states no owner, acreage or county (A for the map, no owner source). At 50 m it sits on the line between "small" and "very tight": 50 m is about 55 yards, so it passes the 50-yard line only by 5 yards. Rule: small tier at best; I would hold it out until a fresh outline. |
| Rockcastle River WMA x Daniel Boone NF (2 patches, 16 ac and 5 ac) and x Rockcastle WSR (28 ac) | KDFWR's PDF says only "Pulaski County; 2,924 acres", no owner; its news page says "owned or co-owned by Kentucky Fish and Wildlife" (https://fw.ky.gov:443/News/Pages/Public-access-on-Rockcastle-River-WMA-expands-by-513-acres.aspx). If KDFWR owns it, it is side by side with the forest (DROP like Burchell-Beech). The ownership map says the patch is on Forest Service land, which fits only if a Forest Service tract is inside the WMA. Chat 2: show the owners of the tracts INSIDE this WMA. |
| Livingston County WMA x Trail of Tears | KDFWR page has no owner line. A water-route trail pair: needs the shoreline test and the owner. |
| Columbus-Belmont SP x Trail of Tears | The park is on a bluff: public park land must be within 100 ft of the river's edge. Chat 2 should give the measured distance from the NHD shoreline. |
| Cumberland Gap NHP x Shillalah Creek WMA (2 patches, 26 and 72 ac; FED:NPS vs STATE) | Shillalah Creek is KDFWR-owned (KDFWR page); the park is NPS: different owners side by side. **Recommend DROP** (rule 3). |
| US-0703 x US-10140, US-10140 x US-3790 (Fort Donelson / Fort Heiman area, FED:TVA vs UNK, 80 ac) | I cannot name US-10140 from the data; owner unknown. Stay NOT SURE. |
| US-1281 x US-4687 (FED:USACE vs STATE, 2.6 ac) | different owners; probably touching. Stay NOT SURE; 2.6 acres is also likely below the size floor. |
| US-10139 x US-7966, US-4526 x US-7966 (FED:USFS vs PRIVATE, 0.8 ac) | private land is not park land (B-G2); 0.8 ac. **Recommend DROP.** |
| Ohio River Islands NWR x Lewis and Clark | the pin is a road on the Ohio side (E Front St); the "spot" is on islands: **water-only (boat) list**, and some refuge islands have their own rules (check). |

## 4. SAME LAND, TWO NUMBERS (grey area 4, still open)
Fort Donelson x Fort Heiman and Jefferson NF WMA x George Washington and Jefferson NF share one outline. Note: the Jefferson row is at 37.09, -82.73 (the Virginia/Kentucky line by Pine Mountain) and carries a KDFWR link for the WMA and a Forest Service link; fine, but it needs Brandon's ruling.

## 5. Corrections to the file or the bot
1. Fix the Fort Donelson map link (POTA page, not official).
2. One Sheltowee row, not 50 (above).
3. Write the trail-line source and date into each line-park row.
4. Show only the owner of land INSIDE a WMA, not the surrounding owner, when the WMA is not Forest Service-owned.
5. The 98 "saved outline only" rows need a fresh pass before a person can see them.

## 6. NEW GREY AREAS (for Brandon)
- **KR-1.** Is a trail that runs wholly inside a forest a 2-fer along its whole length? Rec: yes for land the Forest Service owns within 100 ft, shown as one row with up to 3 pins.
- **KR-2.** Cave preserves closed seasonally (Carter Caves): list with the season note, spot above ground only. Rec: yes.
- **KR-3.** A WMA owned by KDFWR that lies inside the forest outline (Rockcastle River?): side by side like Burchell-Beech. Rec: DROP unless a tract inside is Forest Service-owned.
- **KR-4.** Pair needs the owner and KDFWR does not publish one (Hoskins, Sunny Brook, Ross Creek, Livingston County): use the ownership test only, or wait for an official owner? Rec: ownership test counts, but mark "owner not published" in the members' "how we checked" line.

Sources: https://eec.ky.gov/Nature-Preserves/Locations/Pages/Carter-Caves.aspx; https://fw.ky.gov/More/Documents/RockcastleRiverWMA_ALL.pdf; https://fw.ky.gov:443/News/Pages/Public-access-on-Rockcastle-River-WMA-expands-by-513-acres.aspx; https://fw.ky.gov/More/Documents/SunnybrookWMAall.pdf; https://fw.ky.gov/News/Pages/Ross-Creek-WMA-expands-to-almost-1,300-acres.aspx; https://fw.ky.gov/More/Documents/BooneForestlandsWMA_ALL.pdf; `data/ky-wma-owners.json`; `data/fers/US-KY.json`.

## RULED (Brandon via HQ, Oct 27 8:10 AM, see mapping.md / website.md 'FINAL (HQ Oct 27 8:10 AM)')
KR-1 yes (one row, up to 3 pins). KR-2 Carter Caves: listed with NO special 2-fer note; the PARK CARD carries 'Caves closed to visitors October to May; trails above ground open all year' (this replaces my rule-10 season note in section 1). KR-3 drop. KR-4 ownership test counts; 'owner not published' in the members' how-we-checked line. Grey 4 (same land, two park numbers) is shown openly, labelled 'Same land, two park numbers', with the short notice (Fort Donelson/Heiman, Jefferson NF WMA/GW&J NF no longer hidden). Grey 6 (Trail of Tears + Lewis & Clark) listed as possible, 'both trail lines are approximate'. Chat 2 fixes: fresh pass, Sheltowee one row, Fort Donelson link to NPS, trail-line source and date, owner inside the WMA only. NEXT: re-check after chat 2's fresh pass.

## FINAL LOOK (chat 8, Oct 27 ~2 PM, after chat 2's green run 40525983791) — data/fers/US-KY.json
Checked from the file only (I cannot see the maps). Result: **OK to stop the Kentucky rounds**, with 5 small notes for chat 2.
- Counts match chat 2's note: 31 candidate, 20 "saved outline only", 4 very tight, 6 not sure ("two owners"). All 51 candidate/saved rows passed all 3 passes. Every ruling drop is applied (Big South Fork, Cumberland Falls, W.H. Martin, Burchell-Beech, Cumberlands WMA, side-by-side).
- Wild rivers (park 10138 x Daniel Boone) and the two name fixes: now rows in the list, read live 2026-10-27. Sheltowee and Pine Mountain merged: one row per pair.
- Notes for chat 2 (none block anything):
  1. **Wild river 10138 x Daniel Boone has 6 separate rows** (1.9 to 43 acres). Same pair, same river: show as ONE row with up to 3 pins (like KR-1), or Brandon will see six cards for one thing.
  2. **Two "same land, two park numbers" rows** (US-0703+US-3790, US-10139+US-4526) have no ownership line, no map date, no access pin. Fine for the label, but add "checked" date + both map links so the card matches the rest.
  3. **Water check timed out 4 times**: any candidate near a river (the trail rows, 10102/10112) is not decided on water-only. Rerun just those four before the list is shown.
  4. **20 rows still "saved outline only"** (Pine Mountain 10102/10112, Red River Gorge area 10104/10106, 10111, 10103, 10107, 1276, 0050, 1252). Allowed (Kentucky file copy), but members' line must say "saved outline, not read live today".
  5. **Triple + its pairs** (10104+3801+4484 and its two pair rows, same for 10106+10121+4484): fine under rule 11 only if the card shows them as ONE patch; otherwise 3 cards for one spot.
- Tight rows look right: "very tight" = 40–42 m wide (under 50 yd), "small overlap" tier = 54–80 m. 10158+10171 (1.2 acres, 40 m) correctly sits in very tight.
- Not checked: the ownership of the 6 "not sure" rows (kept out, as ruled) and any polygon on the ground.
