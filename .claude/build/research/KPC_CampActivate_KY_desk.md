# Camp & Activate, KENTUCKY (chat 8 desk run, Oct 28 2026) - KNOWN ANSWERS for the bot
Evidence: A (computed here from the files named below; nothing posted, nothing on the site). Rules: Sheet E + RULINGS CA-1..6 (mapping.md). Script: a short Python point-in-outline pass (15 m edge rule, 100 ft line rule, 5-mile nearby, patches from data/fers main + small tiers only).

Inputs: campground points = KPC-Data data/campinfo/US-KY.json (103 records = 38 federal RIDB + 65 chat 9 hand-list); outlines = data/ky-answer-key.json tracts read from the ky-*.geojson layers (proclamation lines left out: Daniel Boone NF uses its Forest Service owned land); patches = data/fers/US-KY.json status `candidate` (rule 11 merge fixed, run 8:51 AM). 189 of 193 Kentucky parks have an outline; the 4 without are the 3 national / long trails (Trail of Tears, Lewis and Clark, Sheltowee Trace) and Salato Wildlife Refuge.

Counts: 99 campgrounds after merging same-name records within 1 mile (4 pairs merged); 79 placed with a point, 20 have NO point (hand list gave a name only); 50 campgrounds sit inside a POTA park (35 parks); 2 are CAMP HERE, ACTIVATE BOTH; 0 line-park rows; 4 go to CHECK FIRST (plus the 20 with no point).

## 1. Sheet E's examples answered

1. **Zilpo: CHECK FIRST, not a clean 'activate both'.** Two records for one campground: RIDB's point is rounded (38.075, -83.500, only 3 decimals) and lands inside Daniel Boone NF only (1.4 km from the edge, not in the Zilpo WMA patch); the hand-list point (38.07091, -83.48425) is inside Daniel Boone NF AND the Zilpo Campground WMA x Daniel Boone patch (223 ac). The two points are ~1.4 km apart, so the answer flips. Needs one good point (Recreation.gov campground page / agency map). **Twin Knobs: CAMP HERE, ACTIVATE BOTH** (RIDB point inside the Twin Knobs Campground WMA x Daniel Boone patch, 688 ac, and 338 m inside the WMA).
2. **Otter Creek: cannot be answered, no point.** The hand list has the name and park (US-8144) but no coordinates. Whatever the point turns out to be, the rule is already ruled: inside Otter Creek ORA; the Lewis and Clark overlap is on the river bank, so 'activate both' only if the point falls in that patch. -> chat 9: needs a real point.
3. **Houchin Ferry: cannot be answered, no point.** It is the one campground that could be 'inside Mammoth Cave AND inside the Green River corridor patch' (the ruled Mammoth Cave x The Green NWSR patch is 6,456 ac). Mammoth Cave Campground itself is inside Mammoth Cave only (5.8 km from the edge, not in that patch); Maple Springs (RIDB) inside Mammoth Cave only. -> needs Houchin's point (NPS page).
4. **Sheltowee Trace: no row.** Using ky-sheltowee.geojson (Forest Service line), no campground point is within 100 ft (30.5 m). Closest: Holly Bay 85 m, Turkey Foot 88 m, Cave Run Dam Tailwater 316 m. Both are over the line, so neither counts. Note: Sheltowee, Trail of Tears, Lewis and Clark have no outline in the key (line parks); this check used the Forest Service line directly. Grey E1 (polygon vs point) did not come up.
5. **Blue Heron: inside Big South Fork NRRA only** (271 m inside). No 'activate both' (the Big South Fork river pair is dropped).
6. **Cumberland Falls: Ridgeline & Clifty Campgrounds inside Cumberland Falls State Park only** (280 m inside; not in the Daniel Boone owned land, pair dropped).
7. **State park campground near a WMA:** works: e.g. see the NEARBY list below (state park campgrounds listed under the WMAs next door).
8. **Geocoded-address points:** none in Kentucky's data (campstate-manual has no KY file). But the 62 hand-list points have no stated source: chat 9 should say which were placed from an agency map and which from an address. Until then they are used as points.
9. **Land Between the Lakes: no campground can be placed.** LBL has an outline (US-3792, Forest Service land) but all 8 LBL hand-list rows (Hillman Ferry, Energy Lake, Fenton, Piney, Wranglers, 10 lakeside self-service, ...) have no point. Corps campgrounds on Lake Barkley / Kentucky Lake (Cadiz, Canal, Eureka, Hurricane Creek, Kendall, ...) are outside every outline.
10. Canada example: not testable in Kentucky.

## 2. CAMP HERE, ACTIVATE BOTH (we think; short 2-fer notice goes on each)

- **Twin Knobs Campground** (FS): inside the Twin Knobs Campground Wildlife Management Area x Daniel Boone National Forest overlap, patch 688.4 ac. Booking: https://www.recreation.gov/camping/campgrounds/233782. ⚠ Parks' boundaries may overlap here, but we can't confirm it. Check both official boundary maps and make your own call before you count it.
- **Great Meadows Campground** (KY (hand-checked list)): inside the Rock Creek National Wild and Scenic River x Daniel Boone National Forest overlap, patch 2593.5 ac. Booking: https://www.fs.usda.gov/r08/danielboone/recreation/great-meadows-campground. ⚠ Parks' boundaries may overlap here, but we can't confirm it. Check both official boundary maps and make your own call before you count it.
  (Zilpo: CHECK FIRST, see 1. Twin Knobs is on the hunt-area WMA: apply the hunt closure dates (CA-5) before showing.)

## 3. Campgrounds INSIDE each park

- Barren River Lake State Park (US-1273): Barren River Lake State Resort Park Campground (264 m in)
- Big Bone Lick State Historic Site (US-3779): Big Bone Lick Campground (378 m in)
- Big South Fork National Recreation Area (US-0686): Bear Creek Campground - KY (1153 m in), Alum Ford Campground (KY) (815 m in), Blue Heron Campground (KY) (271 m in)
- Blue Licks Battlefield State Park (US-1274): Blue Licks Battlefield Campground (64 m in)
- Carr Creek State Park (US-1251): Carr Creek Campground (106 m in)
- Carter Caves State Park (US-1276): Carter Caves Campground (516 m in)
- Columbus Belmont State Park (US-1252): Columbus-Belmont Campground (23 m in)
- Cumberland Falls State Park (US-1277): Ridgeline & Clifty Campgrounds (280 m in)
- Dale Hollow State Park (US-1278): Dale Hollow Lake Campground (1099 m in)
- Daniel Boone National Forest (US-4484): Claylick Boat-In Campground (971 m in), Craigs Creek Group Area (805 m in), Grove (802 m in), Holly Bay (472 m in), Zilpo - Daniel Boone Nat. For. [CHECK FIRST] (1406 m in), Twin Knobs Campground (1068 m in), Boat Gunnel Group Campground (292 m in), Barren Fork Horse Camp (1083 m in), Bee Rock Campground (259 m in), Clear Creek Campground (1824 m in), Great Meadows Campground (41 m in), Koomer Ridge Campground (241 m in), S-Tree Campground (1124 m in), Turkey Foot Campground (256 m in), White Sulphur Horse Camp (1694 m in)
- Fort Boonesborough State Park (US-1256): Fort Boonesborough Campground (49 m in)
- General Burnside State Park (US-1257): General Burnside Island Campground (136 m in)
- General Butler State Park (US-1279): General Butler Campground (172 m in)
- Grayson Lake State Park (US-1258): Grayson Lake Campground (271 m in)
- Green River Lake State Park (US-1259): Green River Lake Campground (178 m in)
- Greenbo Lake State Park (US-1280): Greenbo Lake Campground (173 m in)
- Jenny Wiley State Park (US-1281): Jenny Wiley Campground (25 m in)
- John James Audubon State Park (US-1260): John James Audubon Campground (68 m in)
- Kenlake State Park (US-1282): Kenlake Campground (223 m in)
- Kentucky Dam Village State Park (US-1283): Kentucky Dam Village Campground (211 m in)
- Kentucky Horse Park (US-10173): Kentucky Horse Park Campground (584 m in)
- Kincaid Lake State Park (US-1261): Kincaid Lake Campground (105 m in)
- Lake Barkley State Park (US-1284): Lake Barkley Campground (78 m in)
- Lake Cumberland State Park (US-1285): Lake Cumberland Campground (514 m in)
- Lake Malone State Park (US-1263): Lake Malone Campground (190 m in)
- Mammoth Cave National Park (US-0050): Maple Springs (5101 m in), Mammoth Cave Campground (5779 m in)
- My Old Kentucky Home State Park (US-1267): My Old Kentucky Home Campground [CHECK FIRST] (1 m in)
- Natural Bridge State Park (US-1286): Whittleton & Middle Fork Campgrounds (143 m in)
- Nolin Lake State Park (US-1268): Nolin Lake Campground (31 m in)
- Paintsville Lake State Park (US-1270): Paintsville Lake Campground (97 m in)
- Pennyrile Forest State Park (US-1287): Pennyrile Forest Campground (97 m in)
- Rock Creek National Wild and Scenic River (US-10111): Great Meadows Campground (441 m in)
- Taylorsville Lake State Park (US-1271): Taylorsville Lake Campground (590 m in)
- Twin Knobs Campground Wildlife Management Area (US-10170): Twin Knobs Campground (338 m in)
- Yatesville Lake State Park (US-1272): Yatesville Lake Campground (44 m in)

Parks with campgrounds inside: 35. Every other park with an outline (154): none known (hand list has no point or none exists).

## 4. CHECK FIRST (members only), with reasons

- My Old Kentucky Home Campground: point 1 m inside the park edge -> 'at the edge: check the official map'.
- Zilpo: two points 1.4 km apart (above).
- NO POINT (20): Bandy Creek Campground (TN) (Big South Fork National Recreation Area); Bear Creek Horse Camp (KY) (Big South Fork National Recreation Area); Breaks Interstate Park Campground (Breaks Interstate State Park); Energy Lake Campground (Land Between the Lakes National Recreation Area); Fenton Self-Service Campground (Land Between the Lakes National Recreation Area); Higginson-Henry WMA designated campsites (Higginson-Henry Wildlife Management Area); Hillman Ferry Campground (Land Between the Lakes National Recreation Area); Houchin Ferry Campground (Mammoth Cave National Park); Kingdom Come primitive campsites (Kingdom Come State Park); Levi Jackson Campground (Levi Jackson Wilderness Road State Park); Maple Springs Group Campground (Mammoth Cave National Park); Otter Creek ORA Campground (Otter Creek State Recreation Area); Piney Campground (TN) (Land Between the Lakes National Recreation Area); Rolling Fork WMA designated camping area (Rolling Fork Wildlife Management Area); Self-service lakeside campgrounds (10) (Land Between the Lakes National Recreation Area); Station Camp Campground (TN) (Big South Fork National Recreation Area); West Kentucky WMA designated camping site (West Kentucky Wildlife Management Area); Wilderness Road Campground (Cumberland Gap National Historical Park); Wranglers Campground (Land Between the Lakes National Recreation Area); Yellowbank WMA primitive campground (Main Area) (Yellowbank Wildlife Management Area).
- Hurricane Creek (RIDB) and Zilpo (RIDB) have rounded points (3 decimals): any near-edge answer on them is unreliable.
- Hunt areas: campgrounds inside WMAs (Twin Knobs) need the hunt dates from Sheet D before any 'activate' row shows (CA-5). Not applied here.
- Hand-list park field vs outline test: 0 disagreements for placed rows.

## 5. NEARBY (outside every outline, within 5 miles of the edge; 8 km; nearest 4 per park)

- Barren River Lake State Park: Baileys Point 1.6 mi; The Narrows 1.8 mi; Tailwater 3.6 mi
- Bat Cave State Nature Preserve: Carter Caves Campground 0.1 mi
- Beaver Creek Wildlife Management Area: Barren Fork Horse Camp 4.0 mi; Ridgeline & Clifty Campgrounds 4.4 mi
- Big South Fork National Recreation Area: Great Meadows Campground 1.0 mi; Barren Fork Horse Camp 2.2 mi
- Big South Fork National Wild and Scenic River: Bear Creek Campground - KY 0.5 mi; Blue Heron Campground (KY) 0.7 mi
- Brigadoon State Nature Preserve: The Narrows 4.0 mi; Barren River Lake State Resort Park Campground 4.6 mi
- Buckhorn Lake State Park: Buckhorn Campground 3.0 mi; Trace Branch Campground 4.8 mi
- Cane Creek Wildlife Management Area: Bee Rock Campground 0.4 mi; Craigs Creek Group Area 1.1 mi; Holly Bay 1.5 mi
- Carr Creek State Park: Littcarr Campground 2.7 mi
- Cascade Caverns State Nature Preserve: Carter Caves Campground 1.5 mi
- Clifty Wilderness Area: Koomer Ridge Campground 1.4 mi; Whittleton & Middle Fork Campgrounds 3.5 mi
- Daniel Boone National Forest: Whittleton & Middle Fork Campgrounds 0.1 mi; Blue Heron Campground (KY) 0.2 mi; Cave Run Dam Tailwater 0.3 mi; Ridgeline & Clifty Campgrounds 0.3 mi
- Dawkins Line Rail Trail State Park: Paintsville Lake Campground 4.7 mi
- Dewey Lake Wildlife Management Area: Jenny Wiley Campground 0.4 mi; German Campground 3.1 mi
- Doug Travis Wildlife Management Area: Columbus-Belmont Campground 1.3 mi
- Dr. Norman And Martha Adair Wildlife Management Area: Big Bone Lick Campground 1.2 mi
- General Burnside State Park: Waitsboro Campground 1.6 mi
- Green River Lake State Park: Pikes Ridge 1.3 mi; Smith Ridge 1.6 mi; Holmes Bend 4.6 mi
- Green River National Wildlife Refuge: John James Audubon Campground 0.3 mi
- Green River State Forest: John James Audubon Campground 2.7 mi
- Jenny Wiley State Park: German Campground 2.5 mi
- Jesse Stuart State Nature Preserve: Greenbo Lake Campground 5.0 mi
- Kentucky Dam Village State Park: Canal 3.8 mi; Eureka 4.7 mi
- Kentucky Lake Wildlife Management Area: Kenlake Campground 3.9 mi
- Lake Barkley State Park: Cadiz 3.3 mi; Hurricane Creek 4.8 mi
- Lake Cumberland State Park: Kendall Campground 2.7 mi
- Land Between the Lakes National Recreation Area: Canal 0.2 mi; Old Kuttawa 0.9 mi; Linton 1.2 mi; Kenlake Campground 1.3 mi
- Little South Fork State Natural Area: Great Meadows Campground 2.4 mi
- Mammoth Cave National Park: Nolin Lake Campground 1.5 mi; Moutardier 2.9 mi; Dog Creek (KY) 3.8 mi
- Mill Creek Wildlife Management Area: S-Tree Campground 0.1 mi; Turkey Foot Campground 4.3 mi
- Mill Springs Battlefield National Monument: Fishing Creek Campground 2.1 mi; Fall Creek Campground 2.8 mi; Cumberland Point Campground 3.0 mi
- Mineral Mounds State Park: Old Kuttawa 0.7 mi
- Natural Bridge State Park: Koomer Ridge Campground 1.5 mi
- Nolin Lake State Park: Moutardier 1.3 mi; Dog Creek (KY) 4.4 mi
- Pennyrile State Forest: Pennyrile Forest Campground 0.1 mi
- Pioneer Weapons Wildlife Management Area: Zilpo - Daniel Boone Nat. For. 0.1 mi; White Sulphur Horse Camp 0.5 mi; Clear Creek Campground 0.5 mi; Twin Knobs Campground 1.0 mi
- Red River National Wild and Scenic River: Koomer Ridge Campground 4.0 mi
- Rock Creek National Wild and Scenic River: Blue Heron Campground (KY) 3.5 mi; Bear Creek Campground - KY 4.2 mi; Alum Ford Campground (KY) 4.9 mi
- Rockcastle River Wildlife Management Area: Bee Rock Campground 3.9 mi
- Rough River Dam State Park: Cave Creek 1.8 mi; Laurel Branch 2.4 mi; Axtel 2.5 mi; North Fork (KY) 3.5 mi
- The Cumberland River Wilderness Area: Ridgeline & Clifty Campgrounds 0.1 mi
- The Green National Wild and Scenic River: Mammoth Cave Campground 0.6 mi; Maple Springs 1.0 mi
- The Rockcastle National Wild and Scenic River: Bee Rock Campground 0.4 mi; Craigs Creek Group Area 3.7 mi; Holly Bay 4.1 mi
- Tradewater Wildlife Management Area: Pennyrile Forest Campground 4.3 mi
- Twin Knobs Campground Wildlife Management Area: Boat Gunnel Group Campground 0.2 mi; Zilpo - Daniel Boone Nat. For. 0.6 mi; Cave Run Dam Tailwater 1.6 mi; Claylick Boat-In Campground 2.5 mi
- Tygarts State Forest: Carter Caves Campground 0.3 mi
- William H. Martin State Natural Area: Bee Rock Campground 0.8 mi; Craigs Creek Group Area 4.6 mi
- Wolf Creek National Fish Hatchery: Kendall Campground 0.0 mi
- Yatesville Lake Wildlife Management Area: Yatesville Lake Campground 1.2 mi
- Zilpo Campground Wildlife Management Area: Zilpo - Daniel Boone Nat. For. 0.1 mi; Claylick Boat-In Campground 0.8 mi; Boat Gunnel Group Campground 1.6 mi; Twin Knobs Campground 1.7 mi

50 parks have at least one campground nearby. 'Nearby' never counts toward an activation. Pin-only parks (Salato) get no 'inside' rows and no distance rows here (no pin file read).

## 6. Grey areas found (for Brandon, short)

- G1 When two records for one campground disagree (RIDB rounded point vs hand point), may the bot show 'activate both'? Lean NO: CHECK FIRST until one agency-map point is confirmed.
- G2 Corps of Engineers campgrounds are mostly outside every POTA park (Lake Barkley, Cumberland, Green River Lake...). They show only as NEARBY. Lean yes.
- G3 Campgrounds with no point (20 of 99, incl. Otter Creek, Houchin Ferry, all of LBL, Levi Jackson, Breaks) cannot be answered. Lean: chat 9 gets the real points from the agency pages first.
- G4 Sheltowee Trace and the long trails have no outline; we used the Forest Service line for Sheltowee only. Lean: fine for Sheltowee; Trail of Tears / Lewis and Clark wait for their lines.
