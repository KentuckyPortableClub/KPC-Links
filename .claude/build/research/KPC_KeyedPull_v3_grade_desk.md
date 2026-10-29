# Keyed parking pull HOLD v3: accuracy check (chat 11, Oct 29 ~12:15 PM)
File: KPC-Data data/access-leads/keyed-pull-hold.json (version 3): 1,925 points, 481 parks (A 25, C 347, B 1,553). inside 1,432 / edge 69 / outside 166 / no outline 258. Nothing is live.
Sample: 30 points, 15 states, seed 1129: 4 A, 7 C, 9 B inside, 6 outside, 4 no outline. Judged by name, kind of thing, 'where', distance (agency maps do not open from my side).

## VERDICT: 26 of 30 right = 87%, NO wrong-park point. Just under the 28/30 bar because of ONE class of fault, which is easy to filter.
Right (26): 4/4 NPS lots (San Antonio Missions, Cuyahoga x2, Arches Wolfe Ranch); trailheads, takeouts and rec sites (Hunter Canyon, Cisco Takeout, Conger Mountain, Crabtree, Williams Creek, Patton, Chikamin, Wheats Meadow, Sunlight Creek picnic, Slate Creek, Beauty Bay, Sand Island group sites, Klondike Bluffs TH, Tom Merrill rec area, Cove's Nest marina); the 'outside, nearby' ones that serve their forest (Filter Plant river access, Silver Creek group camp, Big Rock day use, Green Valley Lake, E Royce / Spruce Hill TH); General Crook road interpretive site; Wolf Creek SP (its own entrance).
Wrong, same class (4): **an AREA is listed as an access point**: 'Oregon Buttes WSA' (12.7 km from the pin), 'Vasquez Peak Wilderness', 'Chassahowitzka Wilderness' (outside), and 'Bull River Guard Station' (outside, 10 km).

## Whole file
- **129 labels are designated Wilderness / WSA areas** (e.g. 'Havasu Wilderness', 'Izembek Wilderness', 'Great Swamp NWR Wilderness' on the refuges; 'Jennie Lakes Wilderness' outside Sequoia): an area, not a place to park. Drop labels that end in Wilderness / WSA / Study Area unless they also say Trailhead / Campground / Parking / Boat / Day Use / Overlook. This alone lifts my sample to 29/30 (guard station stays borderline).
- 14 'resort / ski' labels (Jekyll Island Club Resort, Brian Head, Keystone, Bald Mountain, Wildcat, Rocky Point, Easley Hot Springs): lodges are ruled IN (Brandon 11:24 AM), but a SKI AREA 'nearby, outside the park line' is a business: HQ call, I lean to keep only those inside the park.
- Fixed since v2: 0 points with longitude > 0 (Acadia OK); 0 sources on more than one park (was 208); DC went from dozens of hotels / museums to 3 points; no more office / museum rows.
- Outside points: 166, all within 11.8 km of the pin; labelled 'nearby, outside the park line'. 127 are B, 38 C, 1 A.
- Kentucky camps: still ONE (Houchin Ferry Campground, NPS API 37.20169, -86.23772: correct, Green River at Mammoth Cave). HQ expected 4: 3 missing, chat 9 please say why (not found in the API, or dropped).
- Credit line 'Recreation.gov / National Park Service data' is in the file.

## Recommendation
After the Wilderness / WSA filter (and a keep-or-drop call on outside ski areas): PASS to go to the waiting room. Then Brandon's GO.
