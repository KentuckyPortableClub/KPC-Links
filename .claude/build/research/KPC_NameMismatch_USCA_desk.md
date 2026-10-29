# NAME MISMATCHES: US + CANADA MISSING OUTLINES (Research desk, chat 8, Oct 29 2026)
Source (A): data/review/scoreboard-parks.json (1,441 US+CA parks with no outline: 1,324 'no layer', 112 'likely name mismatch', 5 'missing'). I could NOT see the layers' own name lists (the repo keeps only counts), so these are matches by name on our side; every row is a LEAD, not a proven match. Rule: an outline goes on only with a SURE match (pin inside + name + similar size).

## 1. THE 112 'LIKELY NAME MISMATCH' PARKS, SORTED BY HOW CLOSE (the bot's near-miss name vs POTA's name)
Tier A = core name equal, one contains the other, or ratio >= 0.8 (92). Action: the bot should accept the near-miss name as an alias, then run the sure-match test (pin inside, size). Tier B = weaker (20): check by hand.

### Tier A
| Area | POTA # | POTA name | Layer's name (near-miss) | Match |
|---|---|---|---|---|
| CA-AB | CA-6125 | Porcupine Hills Public Land Use Zone Other Conservation Area | Porcupine Hills | 1.0 |
| CA-BC | CA-3282 | Delta Nature Reserve | Delta Waterworks | 0.48 |
| CA-BC | CA-3679 | Kilby Provincial Park | Kilby General Store Museum | 0.32 |
| CA-BC | CA-5539 | Uplands Park Natural Area | The Uplands Gates | 0.7 |
| CA-NB | CA-6536 | New Brunswick #20 Wilderness Area | New Brunswick #20 Wildlife Management Area | 1.0 |
| CA-NS | CA-6111 | Swiss Air Memorial Peggys Cove Provincial Park | Swiss Air Memorial | 0.75 |
| CA-ON | CA-1299 | Bannockburn Conservation Reserve | Bannockburn CA | 1.0 |
| CA-ON | CA-1519 | Milne Dam Conservation Park | Milne Park | 0.71 |
| CA-ON | CA-5118 | Selwyn Beach Conservation Reserve | Selwyn Conservation Area | 0.67 |
| CA-ON | CA-5631 | Cavan Swamp Wildlife Area | Cavan Swamp Wildlife Area - Preston Block | 0.61 |
| CA-ON | CA-5641 | Sylvan Glen Conservation Area | Sylvan Glen C.A. | 0.85 |
| CA-ON | CA-5645 | Ball's Mill Conservation Area | Ball's Mill C.A. | 0.85 |
| CA-ON | CA-5648 | Garden Hill Conservation Area | Garden Hill C.A. | 0.85 |
| CA-ON | CA-5649 | Richardson's Lookout Conservation Area | Richardson's Lookout C.A. | 0.91 |
| CA-ON | CA-5650 | Thurne Parks Conservation Area | Thurne Parks C.A. | 0.86 |
| CA-ON | CA-5653 | Pottawatomi and Jones Falls Conservation Area | Pottawatomi | 0.65 |
| CA-ON | CA-5659 | Bognor-Marsh Management Area | Bognor Marsh | 1.0 |
| CA-ON | CA-5661 | Feversham Gorge – Madeleine Graydon Memorial Conservation Area | Feversham | 0.35 |
| CA-ON | CA-5663 | Hepworth Management Area | Hepworth | 1.0 |
| CA-ON | CA-5664 | Massie Hills Management Area | Massie Hills | 1.0 |
| CA-ON | CA-5665 | The Glen Management Area | The Glen | 1.0 |
| CA-ON | CA-5666 | Bighead River Management Area | Bighead River | 1.0 |
| CA-ON | CA-6012 | Morrison Dam Conservation Area | Morrison Dam CA | 1.0 |
| CA-ON | CA-6208 | Ausable River Cut Conservation Area | Ausable River Cut CA | 1.0 |
| CA-PE | CA-6596 | Souris Beach Gateway Provincial Recreation Area | SOURIS BEACH | 0.75 |
| CA-QC | CA-0515 | Parc de la Chute-Montmorency Provincial Park | Site patrimonial de la Chute-Montmorency | 0.86 |
| US-AK | US-7208 | Big Lake North State Recreation Site | Big Lake State Recreation Site | 0.5 |
| US-AK | US-7209 | Big Lake South State Recreation Site | Big Lake State Recreation Site | 0.5 |
| US-AK | US-7234 | Harding Lake State Recreation Site | Harding Lake State Recreation Area | 1.0 |
| US-AL | US-11025 | Uchee Creek Conservation Area | Uchee Creek Confluence | 0.67 |
| US-AL | US-11027 | Big Canoe Creek Nature Reserve | Big Canoe Creek | 1.0 |
| US-AL | US-12740 | Hinds Road Outcrop Forever Wild Tract State Conservation Area | Hinds Road Outcrop | 0.65 |
| US-AL | US-9880 | Crow Creek Nature Refuge | Crow Creek Refuge | 1.0 |
| US-AR | US-11870 | Lake Wilhelmina State Fishing Lake | Wilhelmina Lake | 1.0 |
| US-AR | US-13556 | Lake June State Fishing Lake | June Lake - Lafayette | 0.44 |
| US-CT | US-6875 | The Preserve Essex Land Trust State Park Preserve | Preserve State Forest | 0.0 |
| US-CT | US-7547 | Captain George Comer Memorial State Park | Captain Comer Memorial | 0.86 |
| US-FL | US-8689 | Little Creek, McAlpin Landing State Conservation Area | MCALPIN LANDING | 0.7 |
| US-FL | US-8692 | Lamont, Mt. Gilead State Conservation Area | LAMONT | 0.55 |
| US-FL | US-8696 | Purvis Landing, Otter Springs, Shingle Lndg State Conservation Area | OTTER SPRINGS | 0.48 |
| US-FL | US-8701 | Shelly, Duck Pond, Hartsfield State Conservation Area | SHELLY | 0.36 |
| US-FL | US-8711 | Owens Spring, Walker, Adams State Conservation Area | ADAMS | 0.33 |
| US-FL | US-8712 | White Springs, Little Shoals, Gar Pond State Conservation Area | GAR POND | 0.36 |
| US-HI | US-10920 | Kawainui Marsh Wildlife Reserve | KAWAINUI MARSH WILDLIFE SANCTUARY | 0.74 |
| US-HI | US-6410 | Iao Valley State Preserve | IAO VALLEY STATE MONUMENT | 0.69 |
| US-HI | US-6426 | Iolani Palace State Preserve | IOLANI PALACE STATE MONUMENT | 0.74 |
| US-HI | US-6431 | Royal Mausoleum State Preserve | ROYAL MAUSOLEUM STATE MONUMENT | 0.77 |
| US-ID | US-0280 | Oxford Slough Wetland Management District | Oxford Slough | 0.6 |
| US-IL | US-0980 | Beall Woods State Park | Beall Woods Land and Water Reserve | 0.79 |
| US-IL | US-4153 | Kaskaskia unit of Shelbyville State Fish and Wildlife Area | Shelbyville State Fish and Wildlife Area | 0.68 |
| US-IL | US-4154 | West Okaw unit of Shelbyville State Fish and Wildlife Area | Shelbyville State Fish and Wildlife Area | 0.68 |
| US-MI | US-6666 | Edger Waterfowl National Wildlife Management Area | Edger Waterfowl Production Area | 0.73 |
| US-MI | US-6713 | Kinney Waterfowl National Wildlife Management Area | Kinney Waterfowl Production Area | 0.74 |
| US-MI | US-6726 | Malan Waterfowl National Wildlife Management Area | Malan Waterfowl Production Area | 0.73 |
| US-MI | US-6779 | Schlee Waterfowl National Wildlife Management Area | Schlee Waterfowl Production Area | 0.74 |
| US-MI | US-6780 | Schoonover Waterfowl National Wildlife Management Area | Schoonover Waterfowl Production Area | 0.78 |
| US-MI | US-6796 | Tobico Marsh Wildlife Management Area | Tobico Marsh Unit of Bay City State Park | 0.63 |
| US-MN | US-12378 | Whitewater Wildlife Management Area | Whitewater WMA: Main Branch Unit | 0.54 |
| US-MN | US-13545 | Horseshoe Bay Protected Area | Horseshoe Bay WMA | 1.0 |
| US-MT | US-10527 | Judith Landing (BLM) Recreation Site | Judith Landing State Park | 0.88 |
| US-NC | US-12371 | Julian Price National Park | Julian Price Park Wetlands Registered Heritage Area | 0.45 |
| US-NC | US-3857 | Horton Grove State Nature Preserve | Triangle Land Conservancy - Horton Grove Preserve | 0.53 |
| US-NC | US-3859 | Johnston Mill State Nature Preserve | Triangle Land Conservancy - Johnston Mill Nature Preserve | 0.55 |
| US-NC | US-3861 | Little River Natural State Conservation Area | Durham County - Little River Park | 0.63 |
| US-NV | US-12372 | Cave Rock State Park | Cave Rock Lake Tahoe-Nevada State Park | 0.58 |
| US-OK | US-11715 | Lower Illinois River Game Preserve | Lower Illinois | 0.72 |
| US-OR | US-12881 | Diamond Craters Outstanding BLM Recreation Management Area | Diamond Craters | 0.65 |
| US-RI | US-10547 | Silver Spring State Recreation Area | Silver Spring Lake Fishing Access | 0.79 |
| US-RI | US-7723 | John H. Chaffee Rome Point State Nature Preserve | Rome Point | 0.57 |
| US-SD | US-10319 | South Scalp Creek State Recreation Area | S. Scalp Creek Recreation Area | 0.87 |
| US-UT | US-11652 | Burbank Hills One Day Ride BLM Recreation Management Area | Burbank | 0.38 |
| US-UT | US-5913 | Historic Union Pacific Rail Trail State Park | Rail Trail | 0.36 |
| US-UT | US-5926 | Fort Douglas National Historical Park | Fort Douglas | 1.0 |
| US-UT | US-5992 | Big Creek USFS Wild Horse Territory & BLM Herd Management Area | Big Creek | 0.34 |
| US-WA | US-12317 | Rocky Lake State Recreation Site | Rocky Lake | 1.0 |
| US-WA | US-13383 | Big Eddy Water Access State Recreation Site | Big Eddy | 0.55 |
| US-WA | US-13384 | Jonker Water Access State Recreation Site | Jonker | 0.48 |
| US-WA | US-13392 | Massey Bar State Recreation Site | Massey Bar | 1.0 |
| US-WA | US-13393 | Woodland Bar State Recreation Site | Woodland Bar | 1.0 |
| US-WA | US-13394 | Three Mile State Recreation Site | Three Mile | 1.0 |
| US-WA | US-13395 | County Line State Recreation Site | County Line | 1.0 |
| US-WA | US-13396 | Steel Bridge State Recreation Site | Steel Bridge | 1.0 |
| US-WA | US-13399 | Hand State Recreation Site | Hand | 1.0 |
| US-WA | US-13400 | Puget Island State Recreation Site | Puget Island | 1.0 |
| US-WA | US-13401 | Deep River State Recreation Site | Deep River | 1.0 |
| US-WA | US-13402 | Highway 4 State Recreation Site | Highway 4 | 1.0 |
| US-WA | US-5573 | Teanaway State Forest | Teanaway Com Forest | 0.8 |
| US-WI | US-4263 | Piers Gorge Unit of Menominee River State Recreation Area | Menominee River State Recreation Area | 0.64 |
| US-WI | US-4264 | Quiver Falls Unit of Menominee River State Recreation Area | Menominee River State Recreation Area | 0.62 |
| US-WY | US-10799 | Ellis State Wildlife Habitat Management Area | Ellis | 0.56 |
| US-WY | US-12719 | Newton Lakes BOR Recreation Site | Newton Lakes | 0.86 |
| US-WY | US-6212 | Whiskey Basin/ Little Red Creek Wildlife Management Area | Whiskey Basin | 0.6 |

### Tier B (look at each)
| Area | POTA # | POTA name | Near-miss | Match |
|---|---|---|---|---|
| CA-BC | CA-3966 | Pitt Meadows Athletic Park Recreation Site | Pitt Meadows General Store and Post Office | 0.64 |
| CA-NB | CA-6481 | New Brunswick Highlands Ecological Area | New Brunswick #7 Wildlife Management Area | 0.74 |
| CA-QC | CA-0964 | Parc Cartier-Roberval Archeological Reserve | Site archéologique Cartier-Roberval | 0.62 |
| US-AK | US-10464 | Chena Wayside State Recreation Site | Chena River State Recreation Site | 0.67 |
| US-AL | US-13081 | Fort Toulouse Forever Wild Tract State Wildlife Area | Ft. Toulouse Tract | 0.69 |
| US-AR | US-7525 | Mike Huckabee Delta Rivers Nature Park | Delta Rivers Nature Center Pond | 0.48 |
| US-IA | US-9334 | Teal Basins State Waterfowl Management Area | TEAL BASINS WPA | 0.78 |
| US-ID | US-11256 | Brownlee/Oxbow Reservoir BLM Recreation Management Area | Brownlee Reservoir | 0.78 |
| US-MD | US-6392 | Monocacy River Natural Resources Management Area State Natural Area | MONOCACY NRMA | 0.54 |
| US-ME | US-0337 | Carlton Pond Wetland Management District | Carlton Pond Headwaters | 0.62 |
| US-MN | US-10720 | Forest Lake AMA Aquatic Reserve | FOREST LAKE #3 | 0.0 |
| US-MN | US-6468 | Iron Range OHV State Recreation Area | Iron Range Off-Highway Vehicle | 0.64 |
| US-NV | US-2638 | Van Sickle Bi State Park | Van Sickle Unit/AmackerSchultz Lake Tahoe-Nevada State Park | 0.43 |
| US-NY | US-8064 | Barcelona Neck Cooperative State Forest | Linda A. Gronlund Memorial Nature State Forest At Barcelona Neck | 0.41 |
| US-OR | US-10476 | Monument BLM Recreation Management Area | Monument School | 0.74 |
| US-TN | US-13567 | Clinch River Valley State Park | Kyles Ford - Clinch River Access # 2 | 0.59 |
| US-UT | US-5932 | Jordan River Off-Highway Vehicle State Park | Jordan River OHV | 0.67 |
| US-WY | US-10828 | Quebec 01 Missile Alert Facility State Park | Quebec 01 MAF | 0.58 |
| US-WY | US-10845 | Bobcat-Houlihan Trail BLM Recreation Management Area | South Fork Shoshone River-Houlihan/Bobcat | 0.43 |
| US-WY | US-10853 | Cody Canal BLM Recreation Management Area | South Fork Shoshone River-Cody Canal | 0.4 |

## 2. NOTES ON THE TIER A ROWS
- **Ontario conservation areas (CA-5641..6208, 12 rows):** layer writes 'CA' / 'C.A.' for 'Conservation Area'. One rule fixes them all: treat 'C.A.', 'CA', 'Conservation Area' as the same word.
- **Ontario 'Management Area' (CA-5659..5666):** layer drops the words; core name equal.
- **Washington 'State Recreation Site' (10 Columbia/Cowlitz bars, US-13392..13402):** layer holds the bare name ('Massey Bar'). Strip the type words both sides. These are small river-access sites: confirm a polygon exists (may be a point; then pin-only).
- **Type disagreements, same name (check same land?):** US-AK Harding Lake (Site vs Area), CA-NB #20 (Wilderness vs Wildlife Mgmt Area), US-MN Horseshoe Bay (Protected Area vs WMA), US-MI Schoonover (Wildlife Mgmt vs Waterfowl Production Area), US-HI Royal Mausoleum (Preserve vs Monument). Match on location, not type.
- **False friends to avoid:** US-MT Judith Landing (BLM) Recreation Site vs Judith Landing STATE PARK (different land, same river landing: sure match fails on agency); CA-AB Porcupine Hills is a big public land use zone: only accept if the layer feature is that zone.

## 3. SISTER NAMES: same core name, different park type, already has an outline (66 pairs)
These are POTA parks with two numbers whose names share a core. Sometimes the same land (then 'same land, two park numbers' is SHOWN with that label, never hidden), often two different places. DO NOT copy the sister's outline unless the agency map says it is the same ground. Top rows (ratio 1.0 = same core words):

| Area | Missing # | Missing name | Has outline | Its name | Ratio |
|---|---|---|---|---|---|
| CA-AB | CA-1194 | Sylvan Lake Provincial Park | CA-3144 | Sylvan Lake Natural Area | 1.0 |
| CA-BC | CA-3186 | Nisga'a Memorial Lava Bed Provincial Park | CA-3899 | Nisga'a Memorial Lava Bed Protected Area | 1.0 |
| CA-BC | CA-3778 | Maquinna Marine Provincial Park | CA-3779 | Maquinna Protected Area | 1.0 |
| CA-BC | CA-3307 | Cedar Creek Park Conservation Area | CA-0704 | Bear Creek Provincial Park | 0.86 |
| CA-MB | CA-2464 | Narcisse Provincial Park | CA-2465 | Narcisse Wildlife Management Area | 1.0 |
| CA-MB | CA-2529 | Wallace Lake Wildlife Management Area | CA-1082 | Wallace Lake Provincial Park | 1.0 |
| CA-NB | CA-6536 | New Brunswick #20 Wilderness Area | CA-6547 | New Brunswick #2 Wildlife Management Area | 0.97 |
| CA-NB | CA-4444 | McCoy Brook Protected Area | CA-4441 | McCarty Brook Protected Area | 0.83 |
| CA-NS | CA-0485 | Trout Brook Provincial Park | CA-1897 | Trout Brook Wilderness Area | 1.0 |
| CA-NS | CA-1876 | Irish Cove Provincial Park | CA-1775 | Irish Cove Nature Reserve | 1.0 |
| CA-ON | CA-5619 | Springwater Conservation Area | CA-0400 | Springwater Provincial Park | 1.0 |
| CA-ON | CA-5999 | Harmony Conservation Area | CA-1434 | Harmony Forest Conservation Reserve | 1.0 |
| CA-ON | CA-5666 | Bighead River Management Area | CA-0165 | Brightsand River Provincial Park | 0.83 |
| CA-PE | CA-4766 | Victoria Park Natural Area | CA-6593 | Victoria Provincial Nature Reserve | 1.0 |
| CA-QC | CA-2039 | Ile aux Fraises Migratory Bird Sanctuary | CA-2040 | Ile aux Herons Migratory Bird Sanctuary | 0.89 |
| CA-QC | CA-2246 | Senneville Migratory Bird Sanctuary | CA-2169 | Nicolet Migratory Bird Sanctuary | 0.87 |
| CA-QC | CA-2007 | Estuaire de la Riviere Bonaventure Nature Reserve | CA-2347 | ZEC de la Riviere Bonaventure Nature Reserve | 0.86 |
| CA-QC | CA-2042 | Ile Blanche Migratory Bird Sanctuary | CA-2038 | Ile a la Brume Migratory Bird Sanctuary | 0.85 |
| CA-SK | CA-2787 | Overflowing River Recreation Site | CA-2788 | Overflowing River Ecological Reserve | 1.0 |
| CA-SK | CA-6203 | Prairie - Unit Number 13 National Wildlife Area | CA-6174 | Prairie - Unit Number 3 National Wildlife Area | 0.98 |
| CA-SK | CA-6315 | Prairie - Unit Number 27 National Wildlife Area | CA-6173 | Prairie - Unit Number 2 National Wildlife Area | 0.98 |
| CA-SK | CA-2580 | Bitter Lake Recreation Site | CA-2581 | Bittern Lake Recreation Site | 0.92 |
| CA-SK | CA-2603 | Cenotaph Regional Park Recreation Site | CA-1132 | Meota Regional Park | 0.84 |
| CA-YT | CA-4616 | Nisutlin River Recreation Site | CA-0065 | Nisutlin River Delta National Wildlife Area | 0.82 |
| US-AK | US-11244 | Knik River Public Use Area State Recreation Area | US-12708 | Kenai River State Conservation Area | 0.86 |
| US-AK | US-10464 | Chena Wayside State Recreation Site | US-11839 | Chena Pump Wayside State Recreation Site | 0.84 |
| US-AL | US-9880 | Crow Creek Nature Refuge | US-9876 | Crow Creek Management Area | 1.0 |
| US-AR | US-11394 | Muddy Creek WMA Wildlife Management Area | US-7307 | Muddy Creek Wildlife Management Area | 1.0 |
| US-AR | US-7522 | Cherokee State Recreation Area | US-7276 | Cherokee Wildlife Management Area | 1.0 |
| US-GA | US-2200 | Okefenokee State Park | US-0263 | Okefenokee National Wildlife Refuge | 1.0 |
| US-ID | US-4666 | Priest Lake State Forest | US-2246 | Priest Lake State Park | 1.0 |
| US-ID | US-11261 | Big Cottonwood BLM Recreation Management Area | US-5590 | Big Cottonwood Wildlife Management Area | 0.88 |
| US-IL | US-0980 | Beall Woods State Park | US-12387 | Rall Woods State Reserve | 0.86 |
| US-KS | US-5718 | Flint Hills Trail State Park | US-0291 | Flint Hills National Wildlife Refuge | 1.0 |
| US-MD | US-10751 | Idylwild Natural Area | US-7741 | Idylwild Wildlife Management Area | 1.0 |
| US-MI | US-13169 | Lake Ottawa National Recreation Area | US-4489 | Ottawa National Forest | 1.0 |
| US-MI | US-7854 | Molasses River Flooding No 2 Wildlife Management Area | US-6737 | Molasses River Flooding No 1 Wildlife Management Area | 0.96 |
| US-MI | US-4779 | Pere Marquette State Forest | US-6754 | Pere Marquette State Game Land | 0.85 |
| US-MN | US-12378 | Whitewater Wildlife Management Area | US-2528 | Whitewater State Park | 1.0 |
| US-MO | US-12084 | Weldon Springs National Historical Park | US-6492 | Weldon Spring State Conservation Area | 0.96 |
| US-MO | US-10576 | Rush Creek State Conservation Area | US-8278 | Brush Creek State Conservation Area | 0.95 |
| US-MO | US-10575 | Walnut Woods State Conservation Area | US-11058 | Walter Woods State Conservation Area | 0.83 |
| US-MS | US-7114 | Bienville Wildlife Management Area | US-4493 | Bienville National Forest | 1.0 |
| US-MS | US-7119 | Natchez Wildlife Management Area | US-0747 | Natchez National Historical Park | 1.0 |
| US-MS | US-7109 | Old River Wildlife Management Area | US-7123 | Wolf River Wildlife Management Area | 0.84 |
| US-MT | US-12827 | Brownes Lake State Fish and Wildlife Area | US-12826 | Brown's Lake State Fish and Wildlife Area | 0.92 |
| US-MT | US-10527 | Judith Landing (BLM) Recreation Site | US-12941 | Judith Landing State Park | 0.88 |
| US-NC | US-10511 | Jessups Mill Pond State Game Land | US-6954 | Suggs Mill Pond State Game Land | 0.86 |
| US-ND | US-5741 | Turtle Mountain State Forest | US-7510 | Turtle Mountain State Recreation Area | 1.0 |
| US-NY | US-8103 | Cayuga Lake Wildlife Management Area | US-2029 | Cayuga Lake State Park | 1.0 |
| US-NY | US-5308 | Split Rock State Forest | US-5262 | Pulpit Rock State Forest | 0.86 |
| US-OK | US-11671 | Black Kettle Recreation Site | US-6340 | Black Kettle Wildlife Management Area | 1.0 |
| US-OK | US-2805 | Spavinaw State Park | US-6376 | Spavinaw Wildlife Management Area | 1.0 |
| US-OR | US-13065 | Leslie Gulch BLM Recreation Management Area | US-13066 | Upper Leslie Gulch BLM Wilderness Area | 0.84 |
| US-SC | US-13016 | Pine Island State Park | US-0265 | Pinckney Island National Wildlife Refuge | 0.85 |
| US-TN | US-12775 | Davy Crockett State Fishing Lake | US-2941 | David Crockett State Park | 0.89 |
| US-TN | US-6273 | Vine Cedar Glade State Natural Area | US-3925 | Vesta Cedar Glade State Natural Area | 0.85 |
| US-UT | US-5881 | Crack Canyon BLM Wilderness Area | US-5836 | Jack Canyon BLM Wilderness Area | 0.9 |
| US-UT | US-11655 | Eardley Canyon BLM Recreation Management Area | US-5891 | Eagle Canyon BLM Wilderness Area | 0.88 |
| US-UT | US-11752 | Collins Canyon BLM Recreation Management Area | US-5798 | Coal Canyon BLM Wilderness Area | 0.85 |
| US-UT | US-11708 | Hunter Canyon BLM Recreation Management Area | US-5847 | Turtle Canyon BLM Wilderness Area | 0.82 |
| US-UT | US-5895 | Price Canyon BLM Recreation Management Area | US-6032 | Spring Creek Canyon BLM Wilderness Area | 0.82 |
| US-WA | US-4385 | Umatilla National Forest | US-0596 | Umatilla National Wildlife Refuge | 1.0 |
| US-WA | US-5570 | Little Pend Oreille State Forest | US-0584 | Little Pend Oreille National Wildlife Refuge | 1.0 |
| US-WA | US-12317 | Rocky Lake State Recreation Site | US-13375 | Rock Lake State Fishing Lake | 0.89 |
| US-WI | US-4264 | Quiver Falls Unit of Menominee River State Recreation Area | US-4262 | Pemene Falls Unit of Menominee River State Recreation Area | 0.85 |

Most likely SAME LAND (name + type pair that agencies usually draw together): CA-MB Wallace Lake WMA/Provincial Park; CA-NS Trout Brook PP/Wilderness Area; CA-ON Springwater CA/Provincial Park; CA-ID Priest Lake State Forest/State Park; US-ND Turtle Mountain State Forest/Rec Area; US-MI Pere Marquette SF/State Game Land; US-OK Spavinaw State Park/WMA. Different land (do not copy): US-GA Okefenokee State Park vs the NWR; US-KS Flint Hills Trail SP vs Flint Hills NWR; US-MO Weldon Spring NHP vs state conservation area; US-NY Cayuga Lake WMA vs State Park; US-MS Natchez WMA vs Natchez NHP; US-MS Bienville WMA vs National Forest.

## 4. WHAT I CANNOT SEE, AND THE FIX (BOT LOOK-UP)
The 1,324 'no layer' parks might hold more mismatches, but our files keep only each layer's feature COUNT, not its names (outline-leads/*.json holds a 5-name sample, tested.json holds counts). So the matcher cannot be graded from here.
**Ask chat 2 / chat 9 for one thing:** a names dump per read layer (data/names-layer/<area>.json: layer url, name field, every feature's name + centroid + area in acres; no shapes, small). Then one pass can match all 1,324 by name + pin inside + size, and I can grade 30 samples. Without it each guess costs a live query.
Name rules to add to the matcher (all seen above): strip generic type words both sides; 'C.A.' = 'CA' = 'Conservation Area'; 'St'/'Saint', 'Mt'/'Mount'; drop '(BLM)'/'BOR' tags; accept a name inside a longer one only when the pin is inside the polygon.

## 5. HAND-OFFS
- chat 2: Tier A aliases into the outline matcher; Ontario CA rule; Washington bar sites (check polygon vs point).
- chat 9: BOT LOOK-UP: the names-dump job above for the layers in state-gis.json + ca-key/layers.json; then chat 8 grades 30.