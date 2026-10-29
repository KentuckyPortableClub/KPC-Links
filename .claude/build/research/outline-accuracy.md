# Stored outlines vs a fresh full-detail read (chat 2 probe, 2026-10-29)

Metres, each park's 95% value, then median / 95% / worst over the sample. OFF = stored corners from the live edge; CUT = live corners from the stored edge (thinning cuts them).

| Set | parks | OFF median | OFF 95% | OFF worst | CUT median | CUT 95% | CUT worst | kind | within 5 m (95%) |
|---|---|---|---|---|---|---|---|---|---|
| Kentucky files (ky-*.geojson) | 16 | 0.5 | 0.6 | 0.7 | 2.7 | 8.4 | 216.7 | edge-keeping (corners on the real edge) | NO |
| Kentucky app pack (3 m) | 12 | 0.5 | 2218.8 | 2334.0 | 7.7 | 921.3 | 1037.9 | edge-keeping (corners on the real edge) | NO |
| US key saved copy (PAD-US, cache/us) | 20 | 0.5 | 0.6 | 0.7 | 36.6 | 78.2 | 107.1 | edge-keeping (corners on the real edge) | NO |
| Canada key saved copy (CPCAD, CA-ALL) | 20 | 46.2 | 61.0 | 61.0 | 347.6 | 1643.3 | 2156.3 | drifted (stored corners off the real edge) | NO |
| Canada outlines the site draws (data/canada-bounds) | 12 | 47.2 | 2230.2 | 2230.2 | 251.7 | 5042.3 | 7103.8 | drifted (stored corners off the real edge) | NO |

## Parks

### Kentucky files (ky-*.geojson)

- Burchell-Beech Creek WMA: off 0.3/0.5/0.7 m, cut 1.4/7.8/10.0 m, points 87 vs 253, acres 1235 vs 1235
- Cumberland Forest WMA: off 0.2/0.5/0.7 m, cut 0.4/7.4/11.0 m, points 2597 vs 5250, acres 55355 vs 55362
- Jenny Wiley State Resort Park: off 0.2/0.5/0.7 m, cut 1.1/8.2/10.7 m, points 264 vs 630, acres 1406 vs 1408
- Zilpo Campground: off 0.2/0.6/0.6 m, cut 0.3/8.4/11.1 m, points 59 vs 92, acres 219 vs 220
- Tygarts State Forest: off 0.2/0.5/0.6 m, cut 0.4/7.8/216.7 m, points 121 vs 233, acres 1169 vs 1170
- Pine Mountain State Scenic Trail: off 0.3/0.6/0.7 m, cut 0.4/3.0/4.7 m, points 2139 vs 9930, acres 197 vs 197
- John James Audubon State Park State Nature Preserve: off 0.3/0.6/0.6 m, cut 0.8/2.1/2.6 m, points 37 vs 466, acres 337 vs 337
- Dinsmore Woods State Nature Preserve: off 0.2/0.4/0.6 m, cut 0.4/1.7/2.3 m, points 26 vs 42, acres 104 vs 104
- Floracliff Nature Sanctuary: off 0.2/0.5/0.7 m, cut 1.2/2.6/48.0 m, points 46 vs 247, acres 347 vs 347
- Natural Bridge State Park State Nature Preserve: off 0.2/0.6/0.7 m, cut 0.3/3.2/4.6 m, points 171 vs 265, acres 1232 vs 1232
- Livingston County Wildlife Management Area and State Nature Preserve (Newman's Bluff SNP): off 0.2/0.5/0.5 m, cut 0.2/1.2/1.8 m, points 47 vs 191, acres 989 vs 989
- Green River State Natural Area (Rush Island Bottoms): off 0.2/0.5/0.6 m, cut 0.3/2.1/4.0 m, points 29 vs 32, acres 139 vs 139
- Dr. William H. Martin State Natural Area: off 0.2/0.5/0.6 m, cut 0.2/2.2/3.4 m, points 105 vs 137, acres 457 vs 457
- Martin's Fork State Natural Area: off 0.3/0.6/0.6 m, cut 0.5/2.7/4.0 m, points 175 vs 578, acres 1593 vs 1594
- Sinking Creek State Natural Area: off 0.3/0.5/0.6 m, cut 0.3/2.7/3.7 m, points 82 vs 94, acres 300 vs 300
- Green River State Natural Area (Davis Bend): off 0.2/0.6/0.6 m, cut 0.3/2.7/3.9 m, points 54 vs 79, acres 165 vs 165

### Kentucky app pack (3 m)

- US-10139 Jefferson National Forest: off 0.2/0.6/0.7 m, cut 1.4/7.3/10.3 m, points 82 vs 351, acres 856 vs 853
- US-10171 Zilpo Campground: off 0.2/0.6/0.6 m, cut 0.3/8.4/11.1 m, points 59 vs 92, acres 219 vs 220
- US-10170 Twin Knobs Campground: off 0.2/0.5/0.6 m, cut 0.3/8.2/9.6 m, points 99 vs 133, acres 683 vs 682
- US-4690 Knobs State Forest: off 1699.9/2218.8/2334.0 m, cut 7.5/921.3/1037.9 m, points 130 vs 129, acres 1597 vs 500
- US-4526 Jefferson National Forest: off 0.2/0.6/0.7 m, cut 1.4/7.3/10.3 m, points 82 vs 351, acres 856 vs 853
- US-7951 Green River State Forest: off 0.2/0.6/0.6 m, cut 0.4/8.2/9.9 m, points 36 vs 50, acres 1086 vs 1087
- US-4692 Pennyrile State Forest: off 0.2/0.5/0.7 m, cut 1.2/7.1/11.1 m, points 553 vs 2106, acres 16148 vs 16149
- US-4689 Kentucky Ridge State Forest: off 0.2/0.5/0.7 m, cut 0.9/7.6/10.9 m, points 655 vs 1864, acres 12603 vs 12605
- US-4688 Kentenia State Forest: off 0.2/0.5/0.6 m, cut 0.4/7.7/10.7 m, points 179 vs 296, acres 4061 vs 4061
- US-3792 Land Between The Lakes National Recreation Area: off 0.2/0.5/0.7 m, cut 2.1/7.6/11.2 m, points 4295 vs 19685, acres 107439 vs 107509
- US-0608 Ohio River Islands National Wildlife Refuge: off 0.2/0.5/0.6 m, cut 0.3/6.0/11.0 m, points 29 vs 77, acres 377 vs 379
- US-4693 Tygarts State Forest: off 0.2/0.5/0.6 m, cut 0.4/7.8/216.7 m, points 121 vs 233, acres 1169 vs 1170

### US key saved copy (PAD-US, cache/us)

- US-ME Dorothea Dix Park: off 0.4/0.5/0.5 m, cut 3.5/78.2/78.2 m, points 4 vs 18, acres 15 vs 24
- US-ME T03 R09 NWP Plt: off 0.3/0.5/0.5 m, cut 12.1/67.5/81.0 m, points 9 vs 63, acres 958 vs 959
- US-DC No name: off 0.3/0.6/0.6 m, cut 3.5/16.5/21.2 m, points 12 vs 34, acres 1 vs 2
- US-DC National Capital Parks: off 0.2/0.5/0.7 m, cut 1.5/36.6/95.4 m, points 4501 vs 49896, acres 3541 vs 4004
- US-NM Broad Canyon - Fee Property: off 0.2/0.6/0.6 m, cut 8.5/46.2/55.3 m, points 18 vs 108, acres 786 vs 787
- US-NM Coronado National Forest: off 0.3/0.5/0.6 m, cut 1.0/40.7/100.0 m, points 121 vs 580, acres 70003 vs 70103
- US-CT Unknown: off 0.3/0.3/0.3 m, cut 2.7/21.0/21.0 m, points 4 vs 8, acres 0 vs 0
- US-CT Unknown: off 0.1/0.3/0.3 m, cut 1.4/5.6/5.6 m, points 4 vs 10, acres 0 vs 0
- US-NJ Tichenor Park: off 0.6/0.6/0.6 m, cut 1.3/2.2/2.2 m, points 4 vs 11, acres 1 vs 0
- US-NJ Great Egg Harbor River Wildlife Management Area: off 0.3/0.6/0.6 m, cut 0.1/69.2/88.8 m, points 22 vs 28, acres 66 vs 73
- US-IA Four Mile Lake: off 0.2/0.4/0.4 m, cut 15.8/57.7/88.5 m, points 15 vs 571, acres 85 vs 92
- US-IA Wolf Hollow Wildlife Management Area: off 0.5/0.5/0.5 m, cut 0.3/0.5/0.5 m, points 5 vs 5, acres 40 vs 40
- US-SD Nine Mile Creek: off 0.2/0.4/0.4 m, cut 14.0/58.1/61.2 m, points 8 vs 100, acres 217 vs 213
- US-SD Mccook County Waterfowl Production Area: off 0.2/0.5/0.6 m, cut 0.3/53.0/107.1 m, points 187 vs 466, acres 3463 vs 3467
- US-ND Viola Eid Park: off 0.2/0.2/0.2 m, cut 3.6/12.0/57.7 m, points 4 vs 619, acres 2 vs 3
- US-ND Woodbury Park: off 0.3/0.6/0.6 m, cut 22.4/50.4/53.2 m, points 4 vs 64, acres 8 vs 11
- US-WY State Lands 1111121734: off 0.3/0.4/0.4 m, cut 0.2/0.4/0.4 m, points 6 vs 9, acres 79 vs 79
- US-WY State Lands 1111116333: off 0.1/0.2/0.2 m, cut 0.1/0.3/0.3 m, points 5 vs 9, acres 40 vs 40
- US-AZ San Rafael Ranch Natural Area: off 0.3/0.5/0.5 m, cut 0.4/10.6/11.2 m, points 14 vs 55, acres 3554 vs 3550
- US-AZ Jefferson Park Elementary School: off 0.2/0.3/0.3 m, cut 8.6/32.7/38.3 m, points 4 vs 21, acres 1 vs 1

### Canada key saved copy (CPCAD, CA-ALL)

- Main River Special Management Area: off 19.8/30.6/30.6 m, cut 19.3/1089.6/1089.6 m, points 4 vs 9, acres 553 vs 781
- Old Growth Forest Lands: off 26.9/30.7/30.7 m, cut 64.0/113.8/316.7 m, points 4 vs 73, acres 81 vs 159
- UNION PASSAGE MARINE PARK: off 46.8/61.0/61.0 m, cut 264.4/1360.1/1496.1 m, points 20 vs 1187, acres 1404 vs 2492
- 04352R517 Biological Refuge: off 17.0/33.9/33.9 m, cut 178.8/374.8/563.5 m, points 4 vs 65, acres 164 vs 285
- Privately Protected Area (NCC 141770): off 10.4/39.2/39.2 m, cut 22.1/58.5/62.7 m, points 4 vs 97, acres 2 vs 4
- David Dunlap Observatory Park: off 17.8/48.7/48.7 m, cut 61.8/273.6/381.4 m, points 8 vs 264, acres 76 vs 112
- KITSUMKALUM LAKE NORTH PROTECTED AREA: off 30.6/54.9/54.9 m, cut 251.6/725.1/864.6 m, points 8 vs 466, acres 514 vs 971
- Elbow-Sheep Wildland Provincial Park: off 22.5/44.8/50.0 m, cut 307.3/1360.2/1467.8 m, points 29 vs 6779, acres 199474 vs 200978
- N 1/2 NE-17-003-06 E: off 46.8/46.8/46.8 m, cut 49.7/399.5/399.5 m, points 4 vs 5, acres 44 vs 79
- Privately Protected Area (NCC 1000705): off 30.3/30.3/30.3 m, cut 50.5/144.6/144.6 m, points 4 vs 5, acres 2 vs 10
- DUC Fee Simple Lands: off 35.4/53.8/53.8 m, cut 21.5/512.7/512.7 m, points 4 vs 7, acres 86 vs 159
- DUC Fee Simple Lands: off 42.8/42.8/42.8 m, cut 42.9/100.0/100.0 m, points 4 vs 6, acres 0 vs 28
- REDFERN-KEILY PARK: off 11.4/52.8/52.8 m, cut 530.0/1643.3/2156.3 m, points 17 vs 16466, acres 196042 vs 197694
- Privately Protected Area (NCC 1000037): off 6.6/6.6/6.6 m, cut 23.5/25.4/25.4 m, points 4 vs 5, acres 0 vs 0
- Old Growth Forest Lands: off 46.2/46.2/46.2 m, cut 48.5/164.3/183.1 m, points 4 vs 611, acres 35 vs 31
- Medway Lakes Wilderness Area: off 15.8/47.9/47.9 m, cut 102.3/347.6/750.3 m, points 16 vs 980, acres 686 vs 1056
- DUC Fee Simple Lands: off 11.0/23.2/23.2 m, cut 17.5/17.8/17.8 m, points 4 vs 5, acres 1 vs 1
- Babine Forested North: off 34.2/44.8/44.8 m, cut 52.9/588.9/588.9 m, points 4 vs 5, acres 80 vs 157
- Privately Protected Area (NCC 140218): off 56.5/56.5/56.5 m, cut 27.7/67.3/134.4 m, points 4 vs 124, acres 23 vs 17
- DUC Fee Simple Lands: off 40.6/48.9/48.9 m, cut 26.1/199.7/199.7 m, points 4 vs 5, acres 11 vs 20

### Canada outlines the site draws (data/canada-bounds)

- CA-5581 Ruigrok Tract: off 29.0/38.4/38.4 m, cut 37.9/251.7/272.0 m, points 16 vs 47, acres 474 vs 228
- CA-1629 Smith Lake Conservation Reserve: off 24.4/44.5/44.5 m, cut 312.6/673.8/721.6 m, points 8 vs 320, acres 6692 vs 4049
- CA-0424 Wakami Lake Provincial Park (Recreational Class): off 14.5/53.9/56.2 m, cut 1.2/22.3/40.5 m, points 28 vs 63, acres 43321 vs 21732
- CA-2070 J.-Clovis-Laflamme Ecological Reserve: off 9.3/42.3/60.3 m, cut 26.9/102.4/136.4 m, points 51 vs 472, acres 7382 vs 2474
- CA-0395 Sleeping Giant Provincial Park (Natural Environment Class): off 0.6/47.2/278.3 m, cut 20.6/100.1/182.1 m, points 221 vs 5051, acres 119143 vs 59844
- CA-2038 Île à la Brume Bird Sanctuary: off 0.2/0.5/0.6 m, cut 96.3/450.2/702.9 m, points 336 vs 4983, acres 9214 vs 10769
- CA-3823 MORDEN COLLIERY HISTORIC PARK: off 19.3/33.1/33.1 m, cut 10.1/33.4/33.4 m, points 20 vs 33, acres 16 vs 10
- CA-2494 Proulx Lake Wildlife Management Area: off 1.5/56.1/59.0 m, cut 19.9/85.2/122.0 m, points 40 vs 212, acres 15319 vs 7663
- CA-1501 Manitou Conservation Reserve: off 23.3/49.2/57.5 m, cut 780.2/5042.3/7103.8 m, points 320 vs 21492, acres 4 vs 17651
- CA-1543 Night Hawk Lake Shoreline Bluffs Conservation Reserve: off 11.2/2230.2/2230.2 m, cut 169.8/715.5/1070.5 m, points 8 vs 309, acres 5044 vs 2191
- CA-1714 Willow Lake Conservation Reserve: off 20.2/20.5/20.5 m, cut 150.0/353.2/361.6 m, points 8 vs 137, acres 122 vs 138
- CA-1834 Roseway River Wilderness Area: off 17.9/59.3/1751.6 m, cut 7.8/33.1/69.4 m, points 657 vs 2523, acres 12405 vs 4152

