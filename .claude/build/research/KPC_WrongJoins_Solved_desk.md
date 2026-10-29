# WRONG JOINS: TWO PARK NUMBERS ON ONE OUTLINE, SOLVED (Research desk, chat 8, Oct 29 2026 ~12:25 AM)
Puzzle: why does the NY line put Robert Moses (Thousand Islands) on Long Island, and why are 20+ pairs 'same land' that are 100-500 km apart? Method (A): all 4,105 'same outline' pairs in data/fers/same-outline-*.json (chat 2) vs the POTA pins in app/packs; flag pairs whose pins are > 8 km apart (189 found).

## THE ANSWER: the key joins by NAME alone, with no distance test
US-4374 'Robert Moses (Thousand Islands) State Park' (44.99,-74.86) and US-2128 'Robert Moses (Long Island) State Park' (40.62,-73.26) both got PAD-US record 237576 'Robert Moses State Park' (and sgnyb178-180 'Robert Moses', Long Island). The key even marked US-4374 `far: edge`, but nothing enforces that flag. US-2028 Captree and US-2061 Gilgo (both Long Island, correct) got joined to the same Robert Moses record because the layer name is 'Captree/Robert Moses State Park' (match type 'words').
Same cause for NY's county-qualified state forests: the layer holds 'South Hill State Forest' with NO county; POTA names 'South Hill (Chenango County)', '(Oneida County)', '(Delaware and Otsego County)'. The matcher drops the bracket, finds one record, and joins every county's forest to it.

## FIVE CAUSES, WITH EXAMPLES
1. **County in brackets (NY, 16 pairs, 52-377 km apart):** Lost Nation St. Lawrence vs Allegany (377 km), Pine Hill Cattaraugus vs Delaware (299), Black Creek Ulster vs Herkimer (180), Beaver Creek St Lawrence vs Madison (176), Bear Swamp Otsego vs Cayuga (134), South Hill Chenango/Oneida/Delaware+Otsego (104, 52), Tracy Creek Steuben vs Broome (103), Hogsback Lewis vs Oneida (68). FIX: when the POTA name has '(X County)', pick the record whose centre is nearest the pin; if no record is within 15 km, NO JOIN.
2. **Same place name, different place (the Robert Moses case).** FIX: a name match needs the pin inside the polygon or within 2 km of its edge (or inside the buffered bbox). `far: edge` must mean 'no join'.
3. **Parent and part joined (the child takes the parent's whole outline):** Cordell Hull Birthplace SP (63 km) + Cordell Hull WMA; Las Palomas Anacua Unit + Lower Rio Grande Valley Units (18.5 km, 7 records); Rich Mountain Cartecay Tract + Rich Mountain WMA (19 km); LaSage Unit + Wolf River SWA; Horseshoe Canyon North + South; Pottawatomie No 1 + No 2 (28 km). A unit may only get its own record (name has the unit word) or stay PIN-only; never the parent.
4. **Different designations with a shared word:** Grand Canyon NP vs Grand Canyon-Parashant NM (151 km), Coronado National Memorial vs Coronado National Forest (65 km), Boise NF vs Salmon-Challis NF (168 km) vs Sawtooth NF, Clearwater NF vs Nez Perce NF (109 km), Arapaho NF vs White River NF, Nebraska NF vs Oglala NG, Buffalo National River vs Buffalo River WMA, Apalachicola River Wildlife Area vs State Conservation Area, Platte River State Park vs Platte River Landing, Glacial Lakes State Park vs State Trail (55 km), Loess Hills Wildlife Area vs State Forest, Gold Butte HMA vs Gold Butte National Monument. FIX: the designation words (National Forest / National Monument / Memorial / Wildlife Area / State Trail) must agree, or be on the same agency's layer; otherwise no join.
5. **Pins that are genuinely far because the area is huge** (national forest centre vs its edge): not a bug when the pin lies INSIDE the shared polygon. Test with the polygon, not the centroid.

## COUNTS (pins > 8 km apart on one outline): 189 pairs. Worst 60 below.

| km | POTA # | name | POTA # | name | record | file |
|---|---|---|---|---|---|---|
| 502.7 | US-2128 | Robert Moses (Long Island) State Park | US-4374 | Robert Moses (Thousand Islands) State Park | 237576 | neb |
| 377.1 | US-10284 | Lost Nation (St. Lawrence County) State Forest | US-5398 | Lost Nation (Allegany County) State Forest | 236621 | neb |
| 299.1 | US-12030 | Pine Hill (Cattaraugus County) State Forest | US-5249 | Pine Hill (Delaware County) State Forest | 236695 | neb |
| 180.1 | US-5123 | Black Creek(Ulster County) State Forest | US-5124 | Black Creek(Herkimer County) State Forest | 236435 | neb |
| 176.3 | US-5110 | Beaver Creek(St Lawrence County) State Forest | US-5111 | Beaver Creek (Madison County) State Forest | 236424 | neb |
| 168.1 | US-4474 | Boise National Forest | US-4480 | Salmon-Challis National Forest | 2770 | mountain |
| 151.1 | US-0030 | Grand Canyon National Park | US-7887 | Grand Canyon-Parashant National Monument | 3443 | mountain |
| 134.4 | US-5106 | Bear Swamp(Otsego County) State Forest | US-5107 | Bear Swamp(Cayuga County) State Forest | 236421 | neb |
| 108.7 | US-4476 | Clearwater National Forest | US-4478 | Nez Perce National Forest | 2675 | mountain |
| 103.6 | US-5304 | South Hill (Chenango County) State Forest | US-8096 | South Hill (Oneida County) State Forest | 236746 | neb |
| 103.3 | US-12778 | Tracy Creek (Steuben County) State Forest | US-5342 | Tracy Creek (Broome County) State Forest | 236785 | neb |
| 93.1 | US-4474 | Boise National Forest | US-4481 | Sawtooth National Forest | 2801 | mountain |
| 93.1 | US-4474 | Boise National Forest | US-4481 | Sawtooth National Forest | 2771 | mountain |
| 87.4 | US-4400 | Arapaho National Forest | US-4410 | White River National Forest | 2693 | mountain |
| 81.4 | US-6936 | Pisgah State Game Land | US-6937 | Pisgah WRC State Game Land | sgncb62 | southeast |
| 68.2 | US-5060 | Hogsback (Lewis County) State Forest | US-9141 | Hogsback (Oneida County) State Forest | sgnya63762 | neb |
| 68.2 | US-5060 | Hogsback (Lewis County) State Forest | US-9141 | Hogsback (Oneida County) State Forest | sgnya63090 | neb |
| 68.2 | US-5060 | Hogsback (Lewis County) State Forest | US-9141 | Hogsback (Oneida County) State Forest | 236582 | neb |
| 64.8 | US-0771 | Coronado National Memorial | US-4429 | Coronado National Forest | 2743 | mountain |
| 63.1 | US-2937 | Cordell Hull Birthplace State Park | US-7581 | Cordell Hull Waterfowl Refuge Wildlife Management Area | 255598 | southeast |
| 55.1 | US-2486 | Glacial Lakes State Park | US-9388 | Glacial Lakes State Trail | sgmne7550 | midwest |
| 55.1 | US-2486 | Glacial Lakes State Park | US-9388 | Glacial Lakes State Trail | sgmne7549 | midwest |
| 55.0 | US-10339 | Owyhee River Wilderness Area (BLM) Wilderness Area | US-13039 | Owyhee River Wilderness Area | wbl171 | mountain |
| 52.4 | US-5304 | South Hill (Chenango County) State Forest | US-8097 | South Hill (Delaware and Otsego County) State Forest | sgnya61827 | neb |
| 52.4 | US-5304 | South Hill (Chenango County) State Forest | US-8097 | South Hill (Delaware and Otsego County) State Forest | 236746 | neb |
| 50.6 | US-2937 | Cordell Hull Birthplace State Park | US-7580 | Cordell Hull Wildlife Management Area | 255598 | southeast |
| 49.9 | US-3371 | Nebraska National Forest | US-7478 | Oglala National Grassland | 2725 | southcentral |
| 46.5 | US-10844 | Diamond BLM Herd Management Area | US-13126 | Diamond Complex BLM Herd Management Area | hma28 | mountain |
| 40.2 | US-2621 | Platte River State Park | US-4015 | Platte River Landing State Park | sgnec44 | southcentral |
| 34.6 | US-6288 | Apalachicola River Wildlife Area | US-8326 | Apalachicola River State Conservation Area | 190217 | southeast |
| 34.3 | US-6893 | Chowan State Game Land | US-6894 | Chowan Swamp State Game Land | sgncb17 | southeast |
| 34.3 | US-0646 | Buffalo National Wild and Scenic River | US-7270 | Buffalo National River Wildlife Management Area | 3488 | southcentral |
| 32.6 | US-12192 | Loess Hills Wildlife Area | US-4659 | Loess Hills State Forest | sgiaa58128 | ia |
| 32.6 | US-12192 | Loess Hills Wildlife Area | US-4659 | Loess Hills State Forest | sgiaa34306 | ia |
| 32.6 | US-12192 | Loess Hills Wildlife Area | US-4659 | Loess Hills State Forest | sgiaa34304 | ia |
| 32.6 | US-12192 | Loess Hills Wildlife Area | US-4659 | Loess Hills State Forest | sgiaa34303 | ia |
| 32.4 | US-10045 | Jay Heritage Center (Jay Estate) State Historic Site | US-10046 | John Jay Homestead State Historic Site | 237393 | neb |
| 31.7 | US-5833 | Horseshoe Canyon (North) BLM Wilderness Area | US-5846 | Horseshoe Canyon (South) BLM Wilderness Area | wsa994 | ut |
| 31.7 | US-5833 | Horseshoe Canyon (North) BLM Wilderness Area | US-5846 | Horseshoe Canyon (South) BLM Wilderness Area | wsa978 | ut |
| 28.4 | US-7396 | Pottawatomie No 1 State Fishing Lake | US-7397 | Pottawatomie No 2 State Fishing Lake | sgksc969 | southcentral |
| 28.4 | US-7396 | Pottawatomie No 1 State Fishing Lake | US-7397 | Pottawatomie No 2 State Fishing Lake | sgksc968 | southcentral |
| 25.4 | US-11936 | White River State Fish and Wildlife Area | US-4341 | White River Marsh State Wildlife Area | 272998 | midwest |
| 23.4 | US-4343 | LaSage Unit of Wolf River Bottoms State Wildlife Area | US-4344 | Wolf River State Wildlife Area | 273010 | midwest |
| 23.3 | US-0831 | Harry S. Truman Family Farm National Historic Site | US-11015 | Harry S Truman Home National Historical Site | 3141 | midwest |
| 21.9 | US-13115 | Gold Butte BLM Herd Management Area | US-4393 | Gold Butte National Monument | nca21295 | mountain |
| 21.9 | US-10186 | Kinnickinnic River State Fish and Wildlife Area | US-1457 | Kinnickinnic State Park | 272601 | midwest |
| 21.2 | US-9254 | High Rock Canyon BLM Special Recreation Management Area | US-9263 | Little High Rock Canyon Wilderness Area | wbl198 | mountain |
| 20.3 | US-13570 | Gladwin Field Trial Wildlife Management Area | US-6683 | Gladwin State Game Land | sgmib88 | mi |
| 18.9 | US-12417 | Rich Mountain Cartecay Tract Wildlife Management Area | US-7452 | Rich Mountain Wildlife Management Area | sggac745 | southeast |
| 18.9 | US-12417 | Rich Mountain Cartecay Tract Wildlife Management Area | US-7452 | Rich Mountain Wildlife Management Area | sggac744 | southeast |
| 18.9 | US-12417 | Rich Mountain Cartecay Tract Wildlife Management Area | US-7452 | Rich Mountain Wildlife Management Area | sggaa9 | southeast |
| 18.9 | US-12417 | Rich Mountain Cartecay Tract Wildlife Management Area | US-7452 | Rich Mountain Wildlife Management Area | 195073 | southeast |
| 18.9 | US-12417 | Rich Mountain Cartecay Tract Wildlife Management Area | US-7452 | Rich Mountain Wildlife Management Area | 194396 | southeast |
| 18.5 | US-6571 | Las Palomas , Anacua Unit Wildlife Management Area | US-6572 | Las Palomas , Lower Rio Grande Valley Units Wildlife Management Area | 263479 | southcentral |
| 18.5 | US-6571 | Las Palomas , Anacua Unit Wildlife Management Area | US-6572 | Las Palomas , Lower Rio Grande Valley Units Wildlife Management Area | 263448 | southcentral |
| 18.5 | US-6571 | Las Palomas , Anacua Unit Wildlife Management Area | US-6572 | Las Palomas , Lower Rio Grande Valley Units Wildlife Management Area | 263447 | southcentral |
| 18.5 | US-6571 | Las Palomas , Anacua Unit Wildlife Management Area | US-6572 | Las Palomas , Lower Rio Grande Valley Units Wildlife Management Area | 263446 | southcentral |
| 18.5 | US-6571 | Las Palomas , Anacua Unit Wildlife Management Area | US-6572 | Las Palomas , Lower Rio Grande Valley Units Wildlife Management Area | 263443 | southcentral |
| 18.5 | US-6571 | Las Palomas , Anacua Unit Wildlife Management Area | US-6572 | Las Palomas , Lower Rio Grande Valley Units Wildlife Management Area | 263442 | southcentral |
| 18.5 | US-6571 | Las Palomas , Anacua Unit Wildlife Management Area | US-6572 | Las Palomas , Lower Rio Grande Valley Units Wildlife Management Area | 263440 | southcentral |

## WHAT SHOULD HAPPEN TO THE ROWS
- The 'same land, two park numbers' rows built on these joins are WRONG and must be dropped, not shown (e.g. US-2128+US-4374, 931 acres, live on Long Island). Re-run neb after the distance gate.
- Add to the known answers: Robert Moses (Long Island) must NOT pair with Robert Moses (Thousand Islands); each South Hill forest keeps its own record.
- The same distance gate belongs in the US key matcher (kpc_us_key) and the 2-fer 'same outline' reader. The matcher already stores `far`; use it.

## HAND-OFF
- chat 2: distance gate + county rule + parent/child rule; rerun neb; drop the 189 pairs (or only those that fail the polygon test). Fable (Issues file, section 13): this is the cause behind my NY NOT READY.