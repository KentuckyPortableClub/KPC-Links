# NAME MISMATCHES DECODED: US NO-OUTLINE PARKS vs THE LAYER NAMES DUMP (Research desk, chat 8, Oct 29 2026 ~12:15 AM)
Method (A, my own files): chat 2's `layer-names/` dump (490,150 records, centroid + acres) vs the 900 US parks with no outline in scoreboard-parks.json, pins from app/packs. Names decoded first (see section 1), then: layer record within 30 km of the POTA pin; 'inside' = pin within 1.25 x the polygon's equivalent radius + 0.4 km (centroid + acres only, NOT the real polygon: a lead, not a proof). The pin-inside test needs the real polygon; chat 2's NO-BOUNDARY HUNT does that part.
Result for 900 parks: SURE 107 (clean 92 + check-first 15), NAME MATCH PIN OUTSIDE 76, LIKELY 11, PIN INSIDE BUT NAME DIFFERENT 64, SAME NAME FAR AWAY 7, NOTHING NEAR 635.

## 1. THE CODE BOOK: HOW THE LAYERS WRITE POTA'S NAMES (decoded)
1. **Type words dropped or swapped.** The layer holds the bare name: 'Three Mile', 'Steel Bridge', 'Hand', 'Deep River' (WA bar sites, layer sgwab, 12 SURE), 'Ninepipe', 'LeBeau', 'Fort Douglas', 'Ellis'. Strip State Park / Recreation Site / WMA / Natural Area / Preserve both sides. Also swapped: POTA 'State Preserve' = layer 'STATE MONUMENT' (Iolani Palace, Iao Valley, Royal Mausoleum, HI); 'Recreation Site' = 'Recreation Area' (Harding Lake AK); 'State Recreation Area' = 'State Natural Area' (Washington County IL, 1 km: same land); 'Wildlife Management Area' = 'Waterfowl Production Area' (Malan MI, Teal Basins IA).
2. **Abbreviations and CamelCase.** Layers: WMA, WPA, NRMA, SP And RA, SB, OHV, 'OFF HWY VEH', 'AWMarionSP', 'BarkcampSP' (OH). Expand: SP state park, SB state beach, SRA, SF, WPA waterfowl production area, NRMA natural resources management area, OHV/OFF HWY VEH off-highway vehicle. Split camelCase and glued digits.
3. **Upper case / punctuation / accents.** 'IOLANI PALACE', 'LASOYA WILDLIFE AREA' (POTA 'La Soya'), 'LeBeau' vs 'Le Beau', 'El Capitán SB' vs 'El Capitan State Beach', 'St John Ponds' vs 'St. John Ponds', 'Bay View' vs 'Bayview', 'Sandbar' vs 'Sand Bar'. Fold case, accents, dots, spaces.
4. **Spelling slips (either side).** Labrynth/Labyrinth Canyon (UT), Farichild/Fairchild (TX), Capitol/Capital Springs (WI), Conners/Connors Marsh (MI), Sassafrass/Sassafras (MD), Isreal/Israel (NH: layer is misspelled), Finnel/Finnell, Charlotte Ann/Anne (TN). Accept ratio >= 0.8 when the pin is inside; list as 'spelling'.
5. **Agency suffix / longer official name.** 'Gene Howe WMA-W.A. (Pat) Murphy' = POTA 'W.A. Pat Murphy Unit WMA' (TX); 'Lake Tahoe-Nevada State Park (Sand Harbor)' = 'Sand Harbor State Park'; 'Capital Springs Centennial SP And RA'; 'Hanford Reach National Monument, McGee Ranch/Riverlands Unit' (a UNIT of the park: use the unit only if POTA's pin is in it). Rule: when the layer name contains the POTA core name as a unit, accept only with pin inside.
6. **POTA's name is the OTHER agency's.** POTA 'Okefenokee State Park' sits next to the NWR; 'Judith Landing (BLM) Recreation Site' vs 'Judith Landing State Park'; 'Turtle Mountain State Forest' vs 'Turtle Mountain Forest' (different from the Recreation Area); 'Santiam State Forest' vs 'Santiam Park' (29 km, 1 acre). Same core name, different agency or place = TRAP. Always test the pin and the size.
7. **BLM recreation areas hide inside big units.** 'Klondike Bluffs', 'Bar M Trail System', 'Sevenmile Rim', 'Jewell Tibbets Arch Trail' all sit inside 'Labyrinth Rims / Gemini Bridges' (354,533 ac) and Wyoming 'Bobcat-Houlihan Trail', 'Cody Canal' inside 'South Fork Shoshone River' units: their own polygon may not exist. Pin-inside the big unit is NOT a match; keep them pin-only unless BLM's RMA layer has them by name.
8. **Names of the water body or parent area.** 'Magic Reservoir Airstrip SRA' vs 'Magic Reservoir', 'Lake June State Fishing Lake' vs 'June Lake - Lafayette', 'Lloyd Vincent State Fishing Lake' vs 'Lake Vincent': word order and 'Lake' position change; reorder tokens before comparing.

## 2. SURE, CLEAN (92): name decoded, pin inside, small state-layer polygon. Action: take the outline, then run the usual size check.
| St | POTA # | POTA name | Layer name | Match | km to centre | Layer ac | Layer |
|---|---|---|---|---|---|---|---|
| AK | US-7234 | Harding Lake State Recreation Site | Harding Lake State Recreation Area | 1.0 | 0.3 | 329.3 | sgaka |
| AL | US-1039 | De Soto State Park | Desoto State Park | 0.92 | 1.1 | 1527.7 | sgala |
| AL | US-11025 | Uchee Creek Conservation Area | Uchee Creek Confluence | 0.9 | 2.8 | 4772.5 | sgalb |
| AL | US-11027 | Big Canoe Creek Nature Reserve | Big Canoe Creek | 1.0 | 0.5 | 375.0 | sgalb |
| AL | US-12740 | Hinds Road Outcrop Forever Wild Tract State Conservation Area | Hinds Road Outcrop | 0.9 | 0.3 | 79.0 | sgalb |
| AL | US-13081 | Fort Toulouse Forever Wild Tract State Wildlife Area | Ft. Toulouse Tract | 0.9 | 0.9 | 249.5 | sgalb |
| AL | US-9880 | Crow Creek Nature Refuge | Crow Creek Refuge | 1.0 | 1.2 | 3403.9 | sgalc |
| AR | US-11870 | Lake Wilhelmina State Fishing Lake | Wilhelmina Lake | 1.0 | 0.5 | 186.0 | sgarc |
| CA | US-3454 | La Purisima Mission State Historical Park | La Purísima Mission SHP | 0.86 | 1.0 | 1904.4 | sgcab |
| CO | US-12189 | Buena Vista State Wildlife Area | Buena Vista SWA (Fishing Easement) | 0.9 | 0.1 | 44.4 | sgcoc |
| CT | US-7547 | Captain George Comer Memorial State Park | Captain Comer Memorial | 0.86 | 0.0 | 1.7 | sgcta |
| DE | US-10681 | Masseys Millpond State Fishing Lake | Massey Mill Pond | 0.94 | 0.3 | 46.1 | sgdea |
| FL | US-7374 | Wysong Park State Conservation Area | Wysong Lock And Dam | 0.9 | 0.0 | 0.0 | sgflf |
| FL | US-8692 | Lamont, Mt. Gilead State Conservation Area | LAMONT | 0.9 | 0.3 | 293.6 | sgfld |
| FL | US-8696 | Purvis Landing, Otter Springs, Shingle Lndg State Conservation Area | OTTER SPRINGS | 0.9 | 0.0 | 0.6 | sgfld |
| FL | US-8701 | Shelly, Duck Pond, Hartsfield State Conservation Area | SHELLY | 0.9 | 0.2 | 37.3 | sgfld |
| FL | US-8705 | Stephen Foster State Conservation Area | STEPHEN FOSTER STATE PARK | 1.0 | 0.7 | 116.0 | sgfld |
| FL | US-8711 | Owens Spring, Walker, Adams State Conservation Area | ADAMS | 0.9 | 0.0 | 0.1 | sgfld |
| FL | US-8712 | White Springs, Little Shoals, Gar Pond State Conservation Area | WHITE SPRINGS | 0.9 | 0.2 | 48.4 | sgfld |
| GA | US-4648 | Bartram Educational State Forest | BARTRAM FOREST WMA | 0.9 | 0.2 | 904.2 | sggac |
| HI | US-6426 | Iolani Palace State Preserve | IOLANI PALACE STATE MONUMENT | 0.9 | 0.1 | 8.5 | sghib |
| HI | US-6431 | Royal Mausoleum State Preserve | ROYAL MAUSOLEUM STATE MONUMENT | 0.9 | 0.0 | 2.3 | sghib |
| HI | US-7693 | Hanauma Bay Nature Reserve | HANAUMA BAY STATE UNDERWATER PARK | 0.9 | 0.5 | 84.4 | sghia |
| IA | US-11877 | La Soya Wildlife Area | LASOYA WILDLIFE AREA | 0.92 | 0.2 | 73.5 | sgiaa |
| ID | US-0280 | Oxford Slough Wetland Management District | Oxford Slough | 0.9 | 0.6 | 2344.2 | sgidb |
| ID | US-7821 | Magic Reservoir Airstrip State Recreation Area | Magic Reservoir | 0.9 | 2.4 | 3588.5 | sgidb |
| IL | US-0980 | Beall Woods State Park | Beall Woods Nature Preserve | 1.0 | 0.5 | 274.7 | sgilb |
| IL | US-10391 | Kishwaukee River State Fish and Wildlife Area | Kishwaukee River State Natural Area | 1.0 | 0.3 | 561.2 | sgila |
| IL | US-4105 | Washington County State Recreation Area | Washington County State Natural Area | 1.0 | 1.0 | 1460.9 | sgila |
| KS | US-7405 | Melvern River State Fishing Lake | Melvern Wildlife Area | 0.9 | 1.7 | 1191.6 | sgksb |
| MD | US-10751 | Idylwild Natural Area | IDYLWILD WMA | 1.0 | 1.5 | 3658.0 | sgmda |
| ME | US-8287 | Capitol State Park | CAPITAL PARK | 0.86 | 0.0 | 19.7 | sgmea |
| ME | US-8459 | Erle R. Kelley (Dresden Bog) Wildlife Management Area | Dresden Bog | 0.9 | 0.4 | 16.1 | sgmea |
| ME | US-9171 | St. John Ponds Ecological Reserve | St John Ponds | 1.0 | 1.7 | 4240.2 | sgmea |
| MI | US-6666 | Edger Waterfowl National Wildlife Management Area | Edger Waterfowl Production Area | 0.9 | 0.3 | 156.1 | sgmib |
| MI | US-6713 | Kinney Waterfowl National Wildlife Management Area | Kinney Waterfowl Production Area | 0.9 | 0.2 | 77.9 | sgmib |
| MI | US-6726 | Malan Waterfowl National Wildlife Management Area | Malan Waterfowl Production Area | 0.9 | 0.4 | 140.6 | sgmib |
| MI | US-6779 | Schlee Waterfowl National Wildlife Management Area | Schlee Waterfowl Production Area | 0.9 | 0.3 | 158.5 | sgmib |
| MI | US-6780 | Schoonover Waterfowl National Wildlife Management Area | Schoonover Waterfowl Production Area | 0.9 | 0.3 | 93.3 | sgmib |
| MI | US-6796 | Tobico Marsh Wildlife Management Area | Tobico Marsh Unit of Bay City State Park | 0.9 | 0.8 | 2108.4 | sgmib |
| MN | US-13545 | Horseshoe Bay Protected Area | Horseshoe Bay WMA | 1.0 | 0.9 | 269.7 | sgmna |
| MO | US-12084 | Weldon Springs National Historical Park | Weldon Spring CA | 0.96 | 3.4 | 8560.1 | sgmoc |
| MO | US-5707 | Lost Valley State Fish and Wildlife Area | Lost Valley Fish Hatchery | 0.9 | 0.3 | 936.3 | sgmoc |
| MT | US-12822 | Big Horn State Fish and Wildlife Area | Bighorn | 0.93 | 0.2 | 72.1 | sgmtc |
| MT | US-12827 | Brownes Lake State Fish and Wildlife Area | Brownes Bridge | 0.9 | 0.0 | 5.4 | sgmtc |
| MT | US-2576 | Grey Cliff Prairie Dog State Park | Greycliff Prairie Dog Town | 0.88 | 0.1 | 95.9 | sgmta |
| MT | US-8002 | Ninepipe National Wildlife Refuge | Ninepipe | 1.0 | 0.3 | 4289.1 | sgmtb |
| MT | US-8003 | Pablo National Wildlife Refuge | Pablo | 1.0 | 0.2 | 193.4 | sgmtb |
| NC | US-3857 | Horton Grove State Nature Preserve | Triangle Land Conservancy - Horton Grove Preserve | 0.9 | 0.5 | 699.9 | sgnca |
| NC | US-3859 | Johnston Mill State Nature Preserve | Triangle Land Conservancy - Johnston Mill Nature Preserve | 0.9 | 0.7 | 300.1 | sgnca |
| NC | US-3861 | Little River Natural State Conservation Area | Durham County - Little River Park | 0.9 | 0.6 | 253.4 | sgnca |
| NC | US-3862 | Nags Head Woods Ecological State Preserve | Nags Head Woods Ecological Preserve | 1.0 | 0.5 | 816.3 | sgnca |
| NH | US-11849 | Wantastiquet Mt Natural Area State Natural Site | Wantastiquet Mountain Natural Area | 0.92 | 0.5 | 368.3 | sgnhc |
| NV | US-12372 | Cave Rock State Park | Lake Tahoe-Nevada State Park (Cave Rock) | 0.9 | 0.1 | 2.4 | sgnve |
| NY | US-12060 | Crystal Lake State Forest | Crystal Lake Wild Forest | 0.9 | 0.7 | 503.9 | sgnya |
| NY | US-5308 | Split Rock State Forest | Split Rock Wild Forest | 0.9 | 1.4 | 3521.2 | sgnya |
| OK | US-11715 | Lower Illinois River Game Preserve | Lower Illinois River Public Fishing and Hunting Area | 1.0 | 0.7 | 322.5 | sgokb |
| OK | US-2805 | Spavinaw State Park | Spavinaw Game Management Area | 1.0 | 5.0 | 11372.9 | sgokb |
| OK | US-8128 | Lloyd Vincent State Fishing Lake | Lake Vincent | 0.9 | 0.5 | 152.9 | sgokc |
| OR | US-9150 | Saddle Mt State Natural Area | Saddle Mountain | 0.9 | 0.9 | 1401.1 | sgord |
| RI | US-10547 | Silver Spring State Recreation Area | Silver Spring Lake Fishing Access | 0.9 | 0.0 | 12.0 | sgria |
| RI | US-7723 | John H. Chaffee Rome Point State Nature Preserve | Rome Point | 0.9 | 0.9 | 247.5 | sgrib |
| SD | US-10363 | DeGray State Recreation Area | DeGrey | 0.86 | 0.2 | 27.7 | sgsda |
| SD | US-10376 | Le Beau State Recreation Area | LeBeau | 1.0 | 0.2 | 32.0 | sgsda |
| SD | US-7844 | Adams Homestead State Nature Preserve | Adams Nature Area | 0.9 | 0.8 | 1461.3 | sgsda |
| TN | US-3950 | Lauderdale Waterfowl Wildlife Management Area | LAKE LAUDERDALE WATERFOWL REFUGE | 1.0 | 0.3 | 645.1 | sgtnc |
| TN | US-7577 | Charlotte Ann Finnel Neal Wildlife Management Area | Charlotte Anne Finnell Neal WMA | 0.96 | 1.0 | 495.3 | sgtne |
| TX | US-6608 | W.A. Pat Murphy Unit Wildlife Management Area | Gene Howe WMA-W.A. (Pat) Murphy | 0.9 | 1.3 | 870.6 | sgtxb |
| UT | US-10061 | Pine Canyon WMA State Conservation Area | Pine Canyon Conservation Easement | 0.9 | 1.8 | 2961.9 | sgutb |
| UT | US-13592 | Locomotive Springs Back Country Airstrip State Recreation Site | Locomotive Springs WMA | 0.9 | 3.0 | 18356.6 | sgutb |
| UT | US-5926 | Fort Douglas National Historical Park | Fort Douglas | 1.0 | 0.1 | 54.5 | sgutc |
| WA | US-0731 | Columbia River Gorge National Forest | Columbia River Gorge National Scenic Area | 0.9 | 0.9 | 208.5 | sgwad |
| WA | US-13383 | Big Eddy Water Access State Recreation Site | Big Eddy | 0.9 | 0.0 | 9.5 | sgwab |
| WA | US-13384 | Jonker Water Access State Recreation Site | Jonker | 0.9 | 0.0 | 0.3 | sgwab |
| WA | US-13392 | Massey Bar State Recreation Site | Massey Bar | 1.0 | 0.2 | 6.8 | sgwab |
| WA | US-13393 | Woodland Bar State Recreation Site | Woodland Bar | 1.0 | 0.1 | 3.7 | sgwab |
| WA | US-13394 | Three Mile State Recreation Site | Three Mile | 1.0 | 0.0 | 1.0 | sgwab |
| WA | US-13395 | County Line State Recreation Site | County Line | 1.0 | 0.0 | 4.5 | sgwab |
| WA | US-13396 | Steel Bridge State Recreation Site | Steel Bridge | 1.0 | 0.0 | 0.7 | sgwab |
| WA | US-13399 | Hand State Recreation Site | Hand | 1.0 | 0.1 | 4.2 | sgwab |
| WA | US-13400 | Puget Island State Recreation Site | Puget Island | 1.0 | 0.0 | 0.4 | sgwab |
| WA | US-13401 | Deep River State Recreation Site | Deep River | 1.0 | 0.0 | 3.0 | sgwab |
| WA | US-13402 | Highway 4 State Recreation Site | Highway 4 | 1.0 | 0.0 | 0.5 | sgwab |
| WA | US-13516 | Horseshoe -Kitsap- State Fishing Lake | Horseshoe Lake | 0.9 | 0.1 | 1.1 | sgwab |
| WA | US-3157 | Bayview State Park | Bay View State Park | 0.93 | 0.1 | 63.5 | sgwad |
| WA | US-4555 | Hanford Reach National Monument | Hanford Reach National Monument, McGee Ranch/Riverlands Unit | 0.9 | 3.3 | 10198.6 | sgwad |
| WA | US-5573 | Teanaway State Forest | Teanaway Com Forest | 0.9 | 0.9 | 606.6 | sgwac |
| WA | US-6473 | Chief Joesph State Wildlife Area | Chief Joseph Wildlife Area | 0.92 | 0.6 | 77.2 | sgwad |
| WI | US-4264 | Quiver Falls Unit of Menominee River State Recreation Area | Menominee River State Recreation Area | 0.9 | 0.4 | 24.8 | sgwid |
| WY | US-10799 | Ellis State Wildlife Habitat Management Area | Ellis | 0.9 | 0.6 | 38.9 | sgwyc |
| WY | US-12719 | Newton Lakes BOR Recreation Site | Newton Lakes | 0.9 | 0.1 | 472.7 | sgwyd |
| WY | US-6212 | Whiskey Basin/ Little Red Creek Wildlife Management Area | Whiskey Basin | 0.9 | 1.5 | 5652.0 | sgwyc |

## 3. SURE BY NAME BUT CHECK FIRST (15): big units, BLM/federal layers, a different agency or a unit of a bigger park.
| St | POTA # | POTA name | Layer name | Match | km | Layer ac | Layer |
|---|---|---|---|---|---|---|---|
| AK | US-11244 | Knik River Public Use Area State Recreation Area | KNIK RIVER | 1.0 | 17.4 | 260142.9 | sgakb |
| AR | US-11155 | White Rock Mountain State Recreation Area | White Rock WMA | 0.9 | 21.4 | 412962.8 | arw |
| CA | US-12115 | Sáttítla Highlands Natural Monument | Sattitla Highlands National Monument | 0.93 | 7.8 | 229501.2 | fsod |
| ID | US-12230 | South Fork Snake River Access State Fish and Wildlife Area | Snake River | 0.9 | 2.8 | 144134.3 | rst |
| MI | US-4776 | Escanaba River State Forest | Escanaba Forest Management Unit | 0.9 | 4.3 | 74347.0 | mid |
| MT | US-10527 | Judith Landing (BLM) Recreation Site | Judith Landing State Park | 0.9 | 0.8 | 93.2 | sgmta |
| OK | US-4424 | Ouachita National Forest | Ouachita National Wildlife Refuge | 1.0 | 13.7 | 144188.9 | fsod |
| OR | US-10476 | Monument BLM Recreation Management Area | Monument Park | 0.9 | 0.0 | 3.7 | sgore |
| OR | US-12881 | Diamond Craters Outstanding BLM Recreation Management Area | Diamond Craters | 0.9 | 3.4 | 51647.5 | hab |
| UT | US-11003 | Glenwood Open OHV Area BLM Recreation Management Area | Glenwood  | 0.9 | 0.8 | 999.8 | rma |
| UT | US-11652 | Burbank Hills One Day Ride BLM Recreation Management Area | Burbank | 0.9 | 10.9 | 65171.5 | hab |
| UT | US-5992 | Big Creek USFS Wild Horse Territory & BLM Herd Management Area | Big Creek | 0.9 | 0.9 | 3412.9 | hab |
| UT | US-6080 | Conger Mountain One Day Ride BLM Recreation Management Area | Conger | 0.9 | 15.8 | 170027.9 | hab |
| VT | US-3140 | Sand Bar State Park | Sandbar State Park | 0.93 | 0.1 | 0 | vta |
| WA | US-12255 | Rock Creek BLM Recreation Management Area | Rock Creek Recreation Area | 0.9 | 2.8 | 16213.1 | sgwad |

## 4. NAME MATCHES BUT THE PIN IS OUTSIDE THE LAYER SHAPE (centroid test): pin may be off, or it is another place
Often the POTA pin sits at the entrance while the layer centre is far; or a different park with the same name.
| St | POTA # | POTA name | Layer name | Match | km | Layer ac | Layer | Same name elsewhere (km, name, layer) |
|---|---|---|---|---|---|---|---|---|
| AK | US-11835 | Little Susitna Public Use Facility State Recreation Site | Little Susitna | 0.9 | 23.6 | 15466.6 | sgakb |  |
| AL | US-12405 | TVA Guntersville Dam 5(1)(g) Reserve | Lake Guntersville State Park | 0.9 | 20.0 | 7223.4 | sgala |  |
| AL | US-9918 | Thigpen Hill Nature Recreation Area | Thigpen Hill Phase I | 0.9 | 7.8 | 2249.9 | sgalb |  |
| AR | US-7443 | DeGray Lower Lake State Recreation Area | DeGray Lake | 0.9 | 14.4 | 12355.0 | sgarc |  |
| CA | US-11584 | Panoche Hills BLM Special Recreation Management Area | Panoche Hills Ecological Reserve | 0.9 | 3.8 | 582.6 | sgcaa |  |
| CA | US-1174 | Montana de Oro State Park | Montaña de Oro SP | 0.93 | 6.1 | 10242.3 | sgcab |  |
| CO | US-9652 | Grenada State Wildlife Area | Granada SWA | 0.86 | 4.9 | 6063.1 | sgcoa |  |
| CT | US-6875 | The Preserve Essex Land Trust State Park Preserve | Essex Park | 0.9 | 5.3 | 1.0 | sgctb |  |
| DE | US-4367 | First State Heritage State Park | Heritage Park | 0.9 | 27.1 | 0.1 | sgdee |  |
| FL | US-12121 | Lower Reedy Creek: Rough Island North and South, and Johnson Island State Conservation Area | Reedy Creek | 0.9 | 11.7 | 476.6 | sgflf |  |
| FL | US-8689 | Little Creek, McAlpin Landing State Conservation Area | LITTLE CREEK | 0.9 | 4.2 | 38.0 | sgfld |  |
| GA | US-2200 | Okefenokee State Park | Okefenokee National Wildlife Refuge | 1.0 | 28.6 | 3392.5 | fnl |  |
| HI | US-10920 | Kawainui Marsh Wildlife Reserve | KAWAINUI MARSH STATE PARK RESERVE | 1.0 | 1.0 | 24.7 | sghia | [1.6, 'KAWAINUI MARSH STATE PARK RESERVE', 'sghia'] |
| HI | US-6410 | Iao Valley State Preserve | IAO VALLEY STATE MONUMENT | 0.9 | 1.0 | 4.0 | sghia |  |
| ID | US-10072 | Big Southern Butte (BLM) Natural Monument | South Lake | 0.9 | 24.3 | 2.0 | sgidb |  |
| ID | US-10427 | Thomas Creek Airstrip State Recreation Area | Lake Creek Lake | 0.9 | 8.3 | 1.3 | sgidb |  |
| ID | US-11256 | Brownlee/Oxbow Reservoir BLM Recreation Management Area | Oxbow Reservoir | 0.9 | 7.9 | 1161.2 | sgidb |  |
| ID | US-2230 | Castle Rocks State Park | Castle Rocks State Park Fishing Pond | 0.9 | 2.6 | 0.7 | sgidb |  |
| ID | US-4666 | Priest Lake State Forest | Priest Lake | 1.0 | 8.4 | 24243.7 | sgidb | [8.4, 'Priest Lake', 'sgidb'] |
| ID | US-7809 | Big Southern Butte Airstrip State Recreation Area | South Lake | 0.9 | 28.1 | 2.0 | sgidb |  |
| ID | US-7832 | Stanley Airstrip State Recreation Area | Stanley Lake | 0.9 | 10.7 | 186.8 | sgidb |  |
| IL | US-0990 | Donnelley/DePue State Park | Lake DePue State Fish and Wildlife Area | 0.9 | 2.6 | 2261.4 | sgila |  |
| IL | US-4153 | Kaskaskia unit of Shelbyville State Fish and Wildlife Area | Shelbyville State Fish and Wildlife Area | 0.9 | 6.3 | 6237.6 | sgila |  |
| IL | US-4154 | West Okaw unit of Shelbyville State Fish and Wildlife Area | Shelbyville State Fish and Wildlife Area | 0.9 | 8.5 | 6237.6 | sgila |  |
| MA | US-8387 | Francis D. Martini Memorial Shell Park and Moynihan State Recreation Area | Memorial Park | 0.9 | 10.0 | 8.9 | sgmaa |  |
| MD | US-11231 | Sideling Hill Creek State Park | SIDELING HILL WMA | 0.9 | 3.1 | 3396.4 | sgmda |  |
| ME | US-9174 | Mahoosuc Ecological Reserve | Mahoosuc Gateway - Success Pond | 0.9 | 9.5 | 9346.2 | nhc |  |
| MI | US-4779 | Pere Marquette State Forest | Pere Marquette, Michigan National Wild and Scenic River | 0.9 | 23.4 | 13075.0 | fwsr | [49.2, 'Pere Marquette State Game Area', 'sgmib'] |
| MI | US-6821 | Straits State Harbor | Straits State Park | 0.9 | 8.3 | 130.4 | mid |  |
| MI | US-7854 | Molasses River Flooding No 2 Wildlife Management Area | Molasses River Flooding No.5 State Wildlife Management Area | 0.96 | 11.3 | 1457.8 | sgmib |  |
| MN | US-0358 | Detroit Lakes Wetland Management District | DETROIT LAKE | 0.9 | 5.1 | 27.6 | sgmne |  |
| MN | US-0362 | Litchfield Wetland Management District | Litchfield WMA | 0.9 | 8.5 | 114.5 | sgmna |  |
| MN | US-0365 | Minnesota Valley Wetland Management District | MINNESOTA LAKE | 0.9 | 2.3 | 34.1 | sgmne |  |
| MN | US-12378 | Whitewater Wildlife Management Area | WHITEWATER | 1.0 | 14.0 | 39.5 | sgmne | [16.6, 'Whitewater', 'sgmnd'] |
| MS | US-0661 | Gulf Islands National Seashore | Gulf Islands National Seashore | 1.0 | 19.7 | 67623.6 | fnl |  |
| NC | US-12371 | Julian Price National Park | Julian Price Park Wetlands Registered Heritage Area | 0.9 | 1.3 | 247.5 | sgnca |  |
| ND | US-0440 | Valley City Wetland Management District | Valley City | 0.9 | 3.5 | 793.8 | sgnda |  |
| ND | US-5741 | Turtle Mountain State Forest | Turtle Mountain Forest | 1.0 | 4.7 | 157.7 | sgnda | [22.9, 'Turtle Mountain', 'sgnda'] |
| NH | US-4931 | Max Israel State Forest | Max Isreal State Forest | 0.9 | 26.4 | 639.9 | sgnha |  |
| NH | US-4936 | Nash Stream Forest State Forest | Nash Stream Forest | 1.0 | 17.7 | 12725.4 | sgnhc | [20.9, 'Nash Stream Forest', 'sgnha'] |
| NJ | US-7507 | Warren Grove State Recreation Area | Warren Grove Bogs Preserve | 0.9 | 3.0 | 281.8 | sgnjb |  |
| NM | US-7543 | Mescalero Sands Recreation Site | Mescalero Sands North Dune OHV Area | 0.9 | 3.0 | 1616.6 | rma |  |
| NV | US-12373 | Sand Harbor State Park | Lake Tahoe-Nevada State Park (Sand Harbor) | 0.9 | 1.1 | 87.5 | sgnve |  |
| NY | US-8070 | Catskill State Park | Catskill Fp Detatched Parcel | 0.9 | 29.6 | 18.6 | sgnya |  |
| NY | US-8103 | Cayuga Lake Wildlife Management Area | Cayuga Lake | 1.0 | 4.5 | 135.3 | sgnyb | [4.5, 'Cayuga Lake', 'sgnyb'] |
| OK | US-0491 | Tishomingo National Wildlife Refuge | Tishomingo | 1.0 | 4.3 | 3425.7 | sgokc | [4.4, 'Tishomingo Wildlife Management Unit', 'sgokb'] |
| OK | US-11671 | Black Kettle Recreation Site | Black Kettle Wildlife Management Area | 1.0 | 9.0 | 29302.3 | sgokb | [9.0, 'Black Kettle Wildlife Management Area', 'sgokb'] |
| OR | US-10008 | Klamath Hills BLM Recreation Management Area | Klamath | 0.9 | 10.0 | 151.8 | sgorc |  |
| OR | US-10752 | Cascadia short bridge day use National Recreation Area | Cascadia | 0.9 | 2.7 | 178.9 | sgord |  |
| OR | US-12475 | Wolf Creek BLM Special Recreation Management Area | Wolf Creek | 0.9 | 1.5 | 8.4 | sgore |  |
| OR | US-13065 | Leslie Gulch BLM Recreation Management Area | Leslie Gulch | 0.9 | 3.7 | 39.5 | sgore |  |
| OR | US-13070 | Owyhee State Airstrip State Recreation Site | Lake Owyhee | 0.9 | 22.8 | 858.8 | sgora |  |
| OR | US-4390 | Newberry Crater Volcanic National Monument | Newberry National Volcanic Monument | 0.88 | 14.8 | 61456.6 | fsod |  |
| OR | US-5456 | Clatsop State Forest | Clatsop Community College - Main Campus | 0.9 | 24.6 | 10.4 | sgore |  |
| OR | US-5459 | Santiam State Forest | Santiam Park | 1.0 | 29.1 | 1.0 | sgore | [29.1, 'Santiam Park', 'sgore'] |
| OR | US-9986 | West Eugene Wetlands BLM Recreation Management Area | Wetland Park | 0.9 | 13.6 | 20.1 | sgore |  |
| UT | US-10997 | North Fork Virgin River Merriam's Turkey Viewing Area BLM Recreation Management Area | North Fork Virgin River | 0.9 | 4.6 | 1076.0 | rst |  |
| UT | US-11002 | Otter Creek Reservoir BLM Special Recreation Management Area | Otter Creek | 0.9 | 18.5 | 79.5 | sguta |  |
| UT | US-11186 | Timber Canyon Wildlife Management Area | Lake Canyon WMA | 0.9 | 16.2 | 7858.5 | utw |  |
| UT | US-11210 | Lower Range Creek BLM Recreation Management Area | Range Creek | 0.9 | 14.3 | 47790.8 | rst |  |
| UT | US-5762 | Westwater Canyon of the Colorado BLM Recreation Management Area | Westwater Canyon | 0.9 | 7.2 | 637.0 | wsa |  |
| UT | US-5876 | Head of Sinbad BLM Recreation Management Area | Sinbad  | 0.9 | 20.5 | 123816.8 | hab |  |
| UT | US-5885 | Little Wild Horse Canyon TH BLM Recreation Management Area | Little Wild Horse Canyon | 0.9 | 6.8 | 6198.2 | wbl |  |
| UT | US-5987 | Pahvant Valley Heritage Trail BLM Recreation Management Area | Pahvant WMA | 0.9 | 16.2 | 981.2 | utw |  |
| VT | US-3144 | Smugglers' Notch State Park | Smugglers' Notch | 1.0 | 6.7 | 87.0 | sgvta | [6.7, "Smugglers' Notch", 'sgvta'] |
| WA | US-12271 | Telford BLM Recreation Management Area | Telford Recreation Area | 0.9 | 4.8 | 516.9 | sgwad |  |
| WA | US-12278 | Boundary Reservoir BLM Recreation Management Area | Boundary Lake | 0.9 | 5.6 | 2.9 | sgwae |  |
| WA | US-12296 | Raging River State Forest | Raging River Natural Area | 1.0 | 6.3 | 46.6 | sgwad | [8.5, 'Raging River', 'sgwab'] |
| WA | US-12315 | Dragoon Creek State Recreation Site | Dragoon Lake | 0.9 | 9.3 | 10.3 | sgwae |  |
| WA | US-12316 | Sherry Creek State Recreation Site | Sherry Lake | 0.9 | 1.1 | 18.2 | sgwae |  |
| WA | US-3385 | Mt. St. Helens National Monument | Saint Helens Lake | 0.9 | 4.1 | 66.1 | sgwae |  |
| WA | US-5567 | Capitol State Forest | Capitol Lake | 1.0 | 17.6 | 254.0 | sgwae | [17.6, 'Capitol Lake', 'sgwae'] |
| WA | US-5569 | Green Mountain-Tahuya State Forest | Tahuya | 0.9 | 5.9 | 319.2 | sgwac |  |
| WA | US-5570 | Little Pend Oreille State Forest | Little Pend Oreille | 1.0 | 17.1 | 16.2 | sgwac | [18.4, 'Little Pend Oreille', 'sgwac'] |
| WA | US-5572 | Olympic Peninsula State Forest | Olympic National Forest | 0.9 | 2.5 | 21.5 | sgwad |  |
| WI | US-4263 | Piers Gorge Unit of Menominee River State Recreation Area | Menominee River State Recreation Area | 0.9 | 1.1 | 168.0 | mid |  |

## 5. LIKELY (spelling, abbreviation, word order)

| St | POTA # | POTA name | Layer name | Match | km | Layer ac | Layer | Same name elsewhere (km, name, layer) |
|---|---|---|---|---|---|---|---|---|
| CA | US-6454 | El Capitan State Beach | El Capitán SB | 0.76 | 2.5 | 2588.3 | sgcab |  |
| FL | US-8329 | Choctawhatchee & Holmes Creek State Conservation Area | Choctawhatchee River Wildlife Management Area | 0.72 | 4.8 | 45694.6 | sgflg |  |
| IA | US-9334 | Teal Basins State Waterfowl Management Area | TEAL BASINS WPA | 0.78 | 0.4 | 150.2 | sgiaa |  |
| MA | US-13236 | Rockdale Heights Wildlife Management Area | Rockdale Highlands WMA | 0.82 | 0.2 | 46.2 | sgmaa | [213.5, 'Rockdale Heights', 'sgmaa'] |
| MN | US-6468 | Iron Range OHV State Recreation Area | IRON RANGE OFF HWY VEH | 0.78 | 0.0 | 42.8 | sgmne |  |
| TN | US-13364 | Cherokee Trail of Tears State Park | Cherokee Memorial State Park | 0.71 | 0.2 | 3.7 | tnd |  |
| TX | US-4419 | I.D. Farichild State Forest | I.D. FairChild - Main | 0.75 | 0.4 | 1720.6 | sgtxd |  |
| UT | US-12150 | Dry Fork Camping Area BLM Recreation Management Area | Dry Fork Campsite 5 | 0.77 | 0.1 | 0.2 | rma |  |
| UT | US-5837 | Labrynth Canyon BLM Wilderness Area | Labyrinth Canyon | 0.8 | 9.3 | 59735.7 | wbl |  |
| VT | US-5564 | Essex Nursery State Forest | State Tree Nursery | 0.8 | 0.0 | 0 | vta |  |
| WI | US-1458 | Kohler-Andrae State Park | Kohler Park Dunes | 0.72 | 0.2 | 151.9 | sgwic |  |

## 6. PIN INSIDE A LAYER SHAPE BUT THE NAMES DIFFER (the puzzles)
Read the Name column; many are POTA names for trail systems inside a bigger unit (BLM). Real renames: Devil's Playground/Redwash = Red Wash (AKA Devils Playground); Quebec 01 Missile Alert Facility = Quebec 01 MAF; Iron Fork Reservoir = Iron Forks Lake; Bryan Woods = Bryan (Eunice Hamilton) Nature Preserve; Sassafras NRMA; Connors/Conners Marsh; Capitol/Capital Springs; Sunstone Collection = Sunstone Dayuse Area; Barcelona Neck = Linda A. Gronlund Memorial Nature SF at Barcelona Neck.
| St | POTA # | POTA name | Layer name | Match | km | Layer ac | Layer | Same name elsewhere (km, name, layer) |
|---|---|---|---|---|---|---|---|---|
| AK | US-10464 | Chena Wayside State Recreation Site | Chena River State Recreation Site | 0.67 | 0.2 | 22.9 | sgaka |  |
| AK | US-11801 | Clearwater Creek Wayside Recreation Site | Denali Highway SRMA | 0.28 | 8.9 | 551618.0 | rst |  |
| AK | US-11836 | Fred Blixt Cabin BLM Recreation Management Area | White Mountains SRMA | 0.4 | 0.1 | 2.9 | rst |  |
| AK | US-7208 | Big Lake North State Recreation Site | Big Lake State Recreation Site | 0.5 | 0.1 | 188.7 | sgaka |  |
| AR | US-11873 | Iron Fork Reservoir State Fishing Lake | Iron Forks Lake | 0.69 | 0.3 | 313.1 | sgarc |  |
| AR | US-12078 | Peppers Pond State Recreation Site | Camp Robinson WMA | 0.4 | 2.4 | 9313.9 | arw |  |
| AR | US-13556 | Lake June State Fishing Lake | June Lake - Lafayette | 0.44 | 0.5 | 47.4 | sgarc |  |
| AR | US-7525 | Mike Huckabee Delta Rivers Nature Park | Delta Rivers Nature Center Pond | 0.48 | 0.2 | 0.1 | sgarc |  |
| CA | US-6448 | William Randolph Hearst Memorial State Beach | Hearst San Simeon SP | 0.36 | 1.1 | 1766.3 | sgcab |  |
| CO | US-9598 | Hardscrabble-East Eagle BLM National Recreation Area | Hardscrabble Zone 2 Motorized SRMA | 0.54 | 1.5 | 11311.3 | rst |  |
| ID | US-11331 | Mica Bay Boater Park BLM Recreation Management Area | Coeur d'Alene Lake | 0.38 | 5.7 | 64086.9 | rst |  |
| ID | US-12300 | Cougar Bay Preserve BLM Recreation Management Area | Coeur d'Alene Lake | 0.52 | 10.9 | 64086.9 | rst |  |
| IN | US-13101 | Westercamp Wildlife Management Area | Westerkamp Wildlife Managment Area | 0.6 | 0.3 | 101.0 | sgina |  |
| IN | US-4188 | Bryan Woods State Nature Preserve | Bryan (Eunice Hamilton) Nature Preserve | 0.44 | 0.1 | 30.7 | sgina |  |
| IN | US-5689 | Pine Grove State Recreation Area | Monroe Lake | 0.5 | 5.6 | 18683.3 | sgina |  |
| MD | US-13564 | Savage Highlands State Park | SAVAGE RIVER SF	 | 0.57 | 0.1 | 42.6 | sgmda |  |
| MD | US-6392 | Monocacy River Natural Resources Management Area State Natural Area | MONOCACY NRMA | 0.54 | 1.4 | 2046.8 | sgmda |  |
| MD | US-6395 | Sassafras Natural Resources Management Area State Natural Area | SASSAFRASS NRMA | 0.65 | 0.4 | 1187.6 | sgmda |  |
| MI | US-6647 | Connors Marsh Wildlife Management Area | Conners Marsh Flooding State Wildlife Management Area | 0.69 | 0.9 | 1046.0 | sgmib |  |
| MI | US-6817 | Little Lake State Harbor | Newberry Forest Management Unit | 0.29 | 22.0 | 473249.0 | mid |  |
| MI | US-6822 | Whitefish Point State Harbor | Newberry Forest Management Unit | 0.27 | 0.9 | 565.3 | mid |  |
| NC | US-3851 | Brumley Forest State Nature Preserve | Duke Forest | 0.36 | 1.5 | 7012.6 | sgnca |  |
| NC | US-8005 | Fontana TVA Dam National Recreation Area | Nantahala | 0.42 | 29.7 | 553570.1 | sgncb |  |
| NM | US-13186 | Lincoln Tract BLM Recreation Management Area | Rio Bonito Acquired Lands Tract 3 | 0.26 | 0.6 | 196.8 | rst |  |
| NV | US-13062 | Dixie Valley Recreation Site | Clan Alpine | 0.35 | 21.8 | 300663.2 | hma |  |
| NV | US-13196 | Stampede-Nevada BLM Recreation Management Area | Silver King | 0.27 | 15.6 | 582252.3 | hma |  |
| NY | US-8064 | Barcelona Neck Cooperative State Forest | Linda A. Gronlund Memorial Nature State Forest At Barcelona Neck | 0.41 | 0.7 | 276.6 | sgnya |  |
| OR | US-10025 | Lost Forest/Dunes/Fossil BLM Special Recreation Management Area | Sand Dunes WSA | 0.47 | 1.3 | 15420.9 | wsa |  |
| OR | US-10477 | Virtue Flat Off-Highway Vehicle BLM Recreation Management Area | Virtue Flat OHV Area | 0.6 | 3.0 | 5133.8 | rma |  |
| OR | US-10488 | Sunstone Collection BLM Recreation Management Area | Sunstone Dayuse Area  | 0.53 | 0.0 | 1.7 | rma |  |
| TX | US-4514 | Cibola National Forest | Sandia Mountain Wilderness | 0.29 | 2.9 | 37460.1 | wld |  |
| UT | US-10964 | Cathedral Valley Scenic Backway BLM Special Recreation Management Area | Caineville Cove Inn  | 0.35 | 0.9 | 129.0 | rma |  |
| UT | US-10969 | Aurora Open OHV Area BLM Recreation Management Area | Auroura  | 0.46 | 0.7 | 307.1 | rma |  |
| UT | US-10979 | Portal Trail BLM Recreation Management Area | South Moab | 0.4 | 11.6 | 68890.4 | rst |  |
| UT | US-11099 | Klondike Bluffs BLM Recreation Management Area | Labyrinth Rims / Gemini Bridges | 0.29 | 20.1 | 354533.5 | rst |  |
| UT | US-11113 | Baptist Draw BLM Special Recreation Management Area | San Rafael Swell | 0.45 | 21.8 | 1216755.9 | rst |  |
| UT | US-11117 | Trin-Alcove/Three Canyon BLM Wilderness Area | Labyrinth Canyon | 0.55 | 4.1 | 39635.3 | rst |  |
| UT | US-11121 | Government Trail BLM Recreation Management Area | Grand Gulch | 0.4 | 6.0 | 108277.4 | wsa |  |
| UT | US-11176 | Rojo Mountain Bike Trail BLM Recreation Management Area | Red Mountain / Dry Fork | 0.56 | 3.7 | 24748.7 | rst |  |
| UT | US-11207 | Elliott Mesa Wildlife Management Area | Desolation Canyon | 0.41 | 6.8 | 159422.2 | wbl |  |
| UT | US-11658 | Sevenmile Rim BLM Recreation Management Area | Labyrinth Rims / Gemini Bridges | 0.3 | 17.5 | 354533.5 | rst |  |
| UT | US-11661 | Bar M Trail System BLM Recreation Management Area | Labyrinth Rims / Gemini Bridges | 0.4 | 21.7 | 354533.5 | rst |  |
| UT | US-11743 | Upper Valley Granary Wayside BLM Recreation Management Area | Escalante | 0.29 | 5.7 | 23931.1 | rst |  |
| UT | US-11766 | Mansard Trail BLM Recreation Management Area | Kanab Community | 0.38 | 6.9 | 35362.5 | rst |  |
| UT | US-12143 | Devil's Playground / Redwash BLM Recreation Management Area | Red Wash (AKA Devils Playground) | 0.57 | 0.7 | 1884.2 | rma |  |
| UT | US-5823 | Jewell Tibbets Arch Trail BLM Recreation Management Area | Labyrinth Rims / Gemini Bridges | 0.27 | 9.0 | 354533.5 | rst |  |
| UT | US-5834 | Nefertiti BLM Recreation Management Area | Desolation Canyon | 0.27 | 9.6 | 95528.5 | wsa |  |
| UT | US-5932 | Jordan River Off-Highway Vehicle State Park | Jordan River OHV | 0.67 | 0.2 | 158.0 | sguta |  |
| UT | US-6004 | Hanging Rock BLM Recreation Management Area | Rocky Ford | 0.38 | 0.5 | 200.5 | utw |  |
| UT | US-6019 | Onaqui BLM Herd Management Area | Onagui | 0.48 | 28.5 | 504216.2 | hab |  |
| UT | US-6042 | Knolls Off-Highway Vehicle BLM Special Recreation Management Area | Knolls ORV | 0.38 | 3.1 | 40090.0 | rma |  |
| UT | US-6053 | Ibex Crags BLM Recreation Management Area | Kingtop | 0.19 | 15.0 | 170415.9 | hab |  |
| UT | US-6054 | Red Reef East Trail BLM Recreation Management Area | Red Cliffs Recreation Area | 0.44 | 1.0 | 856.2 | rma |  |
| WI | US-10644 | Love and Strutt Creeks State Fish and Wildlife Area | Rem-Love Creek | 0.62 | 0.2 | 8.5 | sgwid |  |
| WI | US-4250 | Capitol Springs State Recreation Area | Capital Springs Centennial SP And RA | 0.64 | 0.2 | 37.2 | sgwid |  |
| WY | US-10828 | Quebec 01 Missile Alert Facility State Park | Quebec 01 MAF | 0.58 | 0.0 | 4.5 | sgwyb |  |
| WY | US-10842 | Boar's Tusk BLM Recreation Management Area | Killpecker Sand Dunes SRMA | 0.39 | 6.6 | 41546.3 | rst |  |
| WY | US-10845 | Bobcat-Houlihan Trail BLM Recreation Management Area | South Fork Shoshone River-Houlihan/Bobcat | 0.43 | 0.3 | 53.3 | sgwyd |  |
| WY | US-10853 | Cody Canal BLM Recreation Management Area | South Fork Shoshone River-Cody Canal | 0.4 | 0.3 | 71.1 | sgwyd |  |
| WY | US-10876 | Lone Tree Trail BLM Recreation Management Area | West Slope SRMA | 0.43 | 3.3 | 218104.5 | rst |  |
| WY | US-10886 | Salt Lick Trail BLM Recreation Management Area | Canyon Creek SRMA | 0.4 | 3.1 | 3647.4 | rst |  |
| WY | US-10893 | Three Patches BLM Recreation Management Area | Rock Springs | 0.28 | 22.4 | 1906130.4 | hab |  |
| WY | US-6203 | Pilot Butte Wild Horse Scenic Tour BLM Recreation Management Area | Rock Springs Field Office ERMA | 0.38 | 24.1 | 3537840.2 | rst |  |
| WY | US-6215 | Simpsons Hollow BLM Recreation Management Area | Little Colorado | 0.29 | 22.5 | 628704.6 | hma |  |

## 7. SAME NAME EXISTS FAR FROM THE PIN (maybe the pin is wrong)

| St | POTA # | POTA name | Layer name | Match | km | Layer ac | Layer | Same name elsewhere (km, name, layer) |
|---|---|---|---|---|---|---|---|---|
| CT | US-6860 | Ferry Landing State Park | Eagle Landing State Park | 0.69 | 18.3 | 9.8 | sgcta | [72.4, 'Ferry Landing', 'sgctb'] |
| IN | US-5688 | Salt Creek State Recreation Area | Indian Creek Wildlife Management Area | 0.64 | 19.3 | 137.6 | sgina | [282.1, 'Salt Creek Public Fishing Area', 'sgina'] |
| KS | US-5718 | Flint Hills Trail State Park | Hillsdale State Park | 0.5 | 18.0 | 514.0 | sgksa | [81.7, 'Flint Hills National Wildlife Refuge', 'sgksc'] |
| NH | US-4980 | White Farm State Forest | Swift Farm | 0.8 | 14.7 | 20.1 | sgnha | [80.9, 'White Farm', 'sgnha'] |
| SC | US-13016 | Pine Island State Park | Dreher Island State Park | 0.67 | 13.9 | 326.3 | sgscb | [193.3, 'Pine Island ', 'sgsca'] |
| WA | US-4477 | Idaho Panhandle National Forest | PEND OREILLE WMA | 0.37 | 7.6 | 7124.9 | idw | [36.3, 'Idaho Panhandle National Forest', 'sgwad'] |
| WA | US-4385 | Umatilla National Forest | Ukiah-Dale Forest | 0.33 | 28.4 | 3100.9 | osp | [109.0, 'Umatilla National Wildlife Refuge', 'sgwad'] |

## 8. NOTHING NEAR (635): no record within 30 km with a similar name. These need a NEW layer, not a name rule (BLM RMAs in UT/WY/ID, MS fishing lakes and WMAs, FL conservation areas).
UT 154, MS 62, ID 51, WA 25, WY 24, MI 21, AR 18, AL 15, CA 15, OR 14, AK 13, IN 13, OK 13, VT 13, WI 12, NE 11, TN 11, NV 10, MN 10, NY 10, NC 9, ND 9, AZ 7, FL 7, GA 6

## 9. GRADE OF 30 RANDOM ROWS FROM THE CLEAN SET (section 2; by eye: name + size + owner)
22 of 30 good (73%): bare names (Hand, County Line, Three Mile, Massey Bar), accents and case (La Soya, Le Beau, La Purisima), spelling (Joesph/Joseph, Massey/Masseys, Finnel/Finnell, De Soto/Desoto), type swaps (Iolani Palace, Schlee WPA), word order (Wilhelmina, Lloyd Vincent).
8 doubtful: Columbia River Gorge NATIONAL FOREST vs National Scenic Area (208 ac: not the same thing); Wysong Park vs Wysong Lock And Dam (0 ac, a point); Split Rock State Forest vs Split Rock WILD Forest (check); Locomotive Springs airstrip site inside an 18,357 ac WMA; Oxford Slough Wetland Mgmt DISTRICT vs a Waterfowl area; Johnston Mill (layer is a LAND CONSERVANCY's, private owner: not a state outline); Lower Illinois River Game Preserve vs Public Fishing and Hunting Area (probably same, size check); White Springs/Little Shoals/Gar Pond (3 sites, one layer record).
So the clean set is NOT yet 90%: do not save any of it without (a) the real polygon holding the pin, (b) the size check, and (c) the layer's owner field. Rule that would have caught most: reject when the layer name has a different DESIGNATION word on a federal type (National Forest vs Scenic Area, WMD vs WPA, Wild Forest vs State Forest) or the owner is not the park's agency.

## 10. HAND-OFFS
- chat 2: add the 8 decode rules to the matcher (fold case/accents, expand SP SB SRA WMA WPA NRMA OHV, camelCase, strip type words, token reorder, spelling >= 0.8 with pin inside); take section 2 as alias hits; section 3/4/6 need the polygon pin-inside test; section 7 may be wrong pins - hand to chat 9 to look.
- chat 9: BOT LOOK-UP: for sections 4 and 7 print the real polygon bounds and whether the POTA pin lies inside.