# Name-match fix: offline test (chat 2, Oct 28 2026)
Test: kpc_us_key.py on branch `namematch-test` vs the current key, both run OFFLINE on the same saved PAD-US copies (50 states), so only the matcher differs. NOT live.

**Result: 9 parks newly join, 20 lose their join, 110 keep a join but with different records.** (Round 1 lost 110, round 2 lost 47; fixed in between.)
The 3 live wrong joins are FIXED: Sacramento NWR / Sacramento River NWR, Gunnison SWA / Gunnison River SWA, Cheatham WMA / Cheatham Lake WMA each keep only their own records.

What changed in the matcher: accents folded (N-6); BLM 'RMA/SRMA' suffix stripped (N-3); 'National Historical Park' is a national (nps) kind, never a state park (N-7); two kindless names join only on the exact name (Q5); Virginia Local_Parks_2023 and any local-park layer left out of the state-GIS table (N-7); a record whose name (and kind) is EXACTLY another POTA park's in the same state goes to that park only (N-4 'sibling rule'); a layer can give each record its own kind (`kind_field`, N-1: no layer uses it yet); a park filed under several states that joined in another state is no longer 'nothing found' (`joined_in`).
Not built (yet): N-9 Lake X / X Lake beyond the sibling rule; the PIN + NAME WORDS rule (needs chat 8's sample first).

## Sample of 30 for chat 8 (all 9 new, 10 of the 20 lost, 11 changed at random)
| # | | Park | Before | After | Chat 8 |
|---|---|---|---|---|---|
| 1 | NEW | US-11870 Lake Wilhelmina State Fishing Lake (AR) | — | Wilhelmina Lake | |
| 2 | NEW | US-11873 Iron Fork Reservoir State Fishing Lake (AR) | — | Iron Forks Lake | |
| 3 | NEW | US-0915 Cesar E. Chavez National Monument (CA) | — | César E. Chávez National Monument | |
| 4 | NEW | US-1174 Montana de Oro State Park (CA) | — | Montaña de Oro SP, Montaña de Oro State Park | |
| 5 | NEW | US-3454 La Purisima Mission State Historical Park (CA) | — | La Purísima Mission State Historic Park, La Purísima Mission SHP | |
| 6 | NEW | US-6454 El Capitan State Beach (CA) | — | El Capitán SB, El Capitán State Beach | |
| 7 | NEW | US-6424 Pāʻulaʻula State Historic Site (HI) | — | PAULAULA STATE HISTORIC SITE | |
| 8 | NEW | US-3348 Felix Vallé House State Historic Site (MO) | — | Felix Valle State Historic Site | |
| 9 | NEW | US-11807 Simon Canyon ACEC BLM Special Recreation Management Area (NM) | — | Simón Canyon (Recreation Area) | |
| 10 | LOST | US-6744 Terra Ceia Preserve Frog Creek State Conservation Area (FL) | Terra Ceia Preserve State Park | — | |
| 11 | LOST | US-7461 Ocmulgee State Fishing Lake (GA) | OCMULGEE WMA, Ocmulgee Wildlife Management Area & Public Fishing Area | — | |
| 12 | LOST | US-7462 Big Lazer Creek State Fishing Lake (GA) | BIG LAZER CREEK WMA, Big Lazer Creek Wildlife Management Area & Public Fishing Area | — | |
| 13 | LOST | US-7470 Silver Lake State Fishing Lake (GA) | SILVER LAKE WMA, Silver Lake Wildlife Management Area | — | |
| 14 | LOST | US-7816 Henrys Lake Airstrip State Recreation Area (ID) | Henrys Lake State Park | — | |
| 15 | LOST | US-10786 Siloam Springs Buckhorn Unit State Park (IL) | Siloam Springs State Park | — | |
| 16 | LOST | US-4092 Salem Unit of Apple River Canyon State Park (IL) | Apple River Canyon State Park | — | |
| 17 | LOST | US-4182 Trine at Pokagon State Recreation Area (IN) | Pokagon State Park | — | |
| 18 | LOST | US-8394 Ashuwillticook Rail Trail State Trail (MA) | Ashuwillticook Rail Trail | — | |
| 19 | LOST | US-8398 Southern New England Trunkline Trail State Trail (MA) | Southern New England Trunkline Trail | — | |
| 20 | CHANGED | US-4480 Salmon-Challis National Forest (ID) | Challis National Forest, Salmon National Forest, Boise National Forest, Payette National Forest | Challis National Forest, Salmon National Forest | |
| 21 | CHANGED | US-4466 Sierra National Forest (CA) | Sierra National Forest, Sequoia National Forest, San Joaquin Experimental Area, Stanislaus National Forest | Sierra National Forest, San Joaquin Experimental Area | |
| 22 | CHANGED | US-11472 Montague Plains Wildlife Management Area (MA) | Montague Plains Wildlife Management Area, Montague Wildlife Management Area | Montague Plains Wildlife Management Area | |
| 23 | CHANGED | US-4953 Russell-Abbott State Forest (NH) | Russell-Abbott State Forest, Russell State Forest | Russell-Abbott State Forest | |
| 24 | CHANGED | US-0208 San Diego National Wildlife Refuge (CA) | San Diego National Wildlife Refuge, San Diego Bay National Wildlife Refuge | San Diego National Wildlife Refuge | |
| 25 | CHANGED | US-1125 Año Nuevo State Park (CA) | Año Nuevo SP, Año Nuevo State Park, Año Nuevo State Reserve | Año Nuevo SP, Año Nuevo State Park, Año Nuevo Coast NP, Año Nuevo State Reserve | |
| 26 | CHANGED | US-11936 White River State Fish and Wildlife Area (WI) | White River Marsh Wildlife Area, White River Fishery Area-Waushara | White River Fishery Area-Waushara | |
| 27 | CHANGED | US-13570 Gladwin Field Trial Wildlife Management Area (MI) | Gladwin Game Unit and Field Trial Area of State Forest, Gladwin State Game Area | Gladwin Game Unit and Field Trial Area of State Forest | |
| 28 | CHANGED | US-3548 Rio de Los Angeles State Park (CA) | Rio de Los Angeles State Park SRA, Rio de Los Angeles State Park State Recreation Area, Los Angeles State Historic Park | Rio de Los Angeles State Park SRA, Rio de Los Angeles State Park State Recreation Area | |
| 29 | CHANGED | US-7406 Mined Land State Fishing Lake (KS) | Mined Land Wildlife Area | Mined Land Wildlife Area | |
| 30 | CHANGED | US-6882 Bladen Lakes State Game Land (NC) | Bladen Lakes State Forest | Bladen Lakes State Forest | |

## The other 10 lost (most are the sibling rule: the record is another POTA park's own outline)
- US-13253 Sappington African American Cemetery State Historic Site (MO): was Sappington Cemetery State Historic Site; now nothing (near: Sappington Cemetery State Historic Site)
- US-1795 Watkins Mill State Park (MO): was Watkins Woolen Mill State Park And Historic Site; now nothing (near: Watkins Woolen Mill State Park And Historic Site)
- US-8396 Nashua River Rail Trail State Trail (NH): was Nashua River Rail Trail; now nothing (near: —)
- US-10045 Jay Heritage Center (Jay Estate) State Historic Site (NY): was John Jay Homestead State Historic Site; now nothing (near: —)
- US-12027 Altus-Lugert State Fishing Lake (OK): was Altus Lugert Wildlife Management Area; now nothing (near: —)
- US-2803 Sequoyah State Park (OK): was Sequoyah Bay State Park; now nothing (near: Sequoyah Bay State Park, Western Hills Guest Ranch/sequoya Sp State Resort)
- US-8149 Oak Lea Wildlife Management Area (SC): was Manchester State Forest; now nothing (near: —)
- US-11000 Desert Experimental Range Biosphere Reserve (UT): was Desert Experimental Range; now nothing (near: Desert Range Exp. Station Experimental Area, Desert Experimental Range, Fillmore Field Office)
- US-0061 San Juan Island American Camp National Historical Park (WA): was San Juan Island National Historical Park; now nothing (near: San Juan Island National Historical Park, San Juan Islands National Wildlife Refuge)
- US-11903 San Juan Island English Camp National Historical Park (WA): was San Juan Island National Historical Park; now nothing (near: San Juan Island National Historical Park, San Juan Islands National Wildlife Refuge)

Pattern in the lost: 'X Unit of Y State Park' / 'Y Fishing Lake' lose Y's own outline because POTA also lists Y (sibling rule: correct by N-4, but chat 8 please confirm); three rail trails (MA, NH) lose their join to Q5 (POTA's 'X Rail Trail State Trail' vs the layer's 'X Rail Trail'): a Q5 exception for '... State Trail' = '...' may be wanted.
