# Fable book: US-WA (61 rows, 20 parks)
HANDOFF (chat 3, Oct 30): Fable work moves to CHAT 8. Step 0 done (20; 18 link to WA DNR). DNR forest pages = trail PDFs only (picture); DNR 'Go! Map' (dnr.wa.gov/go) is the lead. Layers below -> WAITING chat 9 pin test.
LAYER | Parks Administrative Boundaries (WA State Parks) | https://www.arcgis.com/sharing/rest/content/items/ca1e60b4384f491383adf6b37b4f1a94?f=json | found by chat 3 Oct 29-30 | not yet tested against the pins
LAYER | Wildlife Areas (WDFW) | https://www.arcgis.com/sharing/rest/content/items/54642c30a0f842f2b8603976b5625678?f=json | found by chat 3 Oct 29-30 | not yet tested against the pins
LAYER | Water Access Sites - Boundaries (WDFW) | https://www.arcgis.com/sharing/rest/content/items/88b13ca5a1e3417fbe528152fc7aff04?f=json | found by chat 3 Oct 29-30 | not yet tested against the pins
LAYER | WA RCO Public Lands Inventory 2019 (all state lands; best lead for DNR sites) | https://www.arcgis.com/sharing/rest/content/items/d296b58b0eae485fba2c55ab90e5908d?f=json | found by chat 3 Oct 29-30 | not yet tested against the pins
ONE ROW PER PARK from now on: update the park's row in place (add to its cells), don't add a new row. Read the Agency Atlas first: .claude/build/research/agency-atlas/US-WA.md

| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-10711 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-10711 | Marckworth State Forest | https://www.dnr.wa.gov/managed-lands/forest-and-trust-lands  |  |  | NOTHING NEAR | name-mismatch/pin-doubt |
| US-10711 | Marckworth State Forest | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels];  ? ac [NHDWaterbody]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-11145 | | PAD-US at pin: Washington State Department of Fish & Wi (SRMA, owner SDNR/STAT, manager SFW, 91115 ac, Fee, PAD id 271376) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-11145 | Naneum Ridge State Forest | https://www.dnr.wa.gov/NaneumRidge |  |  | PIN INSIDE other record | name-mismatch/pin-doubt |
| US-11145 | Naneum Ridge State Forest | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels]; Colockum ? ac [UnitBoundaries]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-12296 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-12296 | Raging River State Forest | https://www.dnr.wa.gov/geo/ragingriver.pdf |  |  | PIN INSIDE other record | name-mismatch/pin-doubt |
| US-12296 | Raging River State Forest | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-12315 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-12315 | Dragoon Creek State Recreation Site | https://wadnr.maps.arcgis.com/apps/Shortlist/index.html?appi |  |  | PIN INSIDE | no-layer |
| US-12315 | Dragoon Creek State Recreation Site | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels];  ? ac [NHDWaterbody]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-12316 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-12316 | Sherry Creek State Recreation Site | https://wadnr.maps.arcgis.com/apps/Shortlist/index.html?appi |  |  | PIN INSIDE other record | name-mismatch/pin-doubt |
| US-12316 | Sherry Creek State Recreation Site | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels]; INLAND NORTHWEST NATIONAL WILDLIFE REFUGE COM 65283 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-12565 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-12565 | Skookum Creek State Recreation Area | https://dnr.wa.gov/forest-and-trust-lands/little-pend-oreill |  |  | PIN INSIDE other record | name-mismatch/pin-doubt |
| US-12565 | Skookum Creek State Recreation Area | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-12566 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-12566 | Sheep Creek State Recreation Area | https://dnr.wa.gov/forest-and-trust-lands/little-pend-oreill |  |  | PIN INSIDE other record | name-mismatch/pin-doubt |
| US-12566 | Sheep Creek State Recreation Area | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-12567 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-12567 | Douglas Falls State Recreation Area | https://dnr.wa.gov/forest-and-trust-lands/little-pend-oreill |  |  | NOTHING NEAR | name-mismatch/pin-doubt |
| US-12567 | Douglas Falls State Recreation Area | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels, grange]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-12569 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-12569 | Beverly Dunes State Recreation Site | https://dnr.wa.gov/forest-and-trust-lands/naneum-ridge-state |  |  | PIN INSIDE | no-layer |
| US-12569 | Beverly Dunes State Recreation Site | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [Non-DNR Major Public Lands, Federal Government];  ? ac [DNR Managed Land Parcels]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-13391 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-13391 | Olequa Crossing State Recreation Site | https://wdfw.wa.gov/places-to-go/water-access-sites/olequa-c |  |  | NOTHING NEAR | no-layer |
| US-13391 | Olequa Crossing State Recreation Site | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [NHDWaterbody]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-13516 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-13516 | Horseshoe -Kitsap- State Fishing Lake | https://wdfw.wa.gov/fishing/locations/lowland-lakes/horsesho |  |  | PIN INSIDE | no-layer |
| US-13516 | Horseshoe -Kitsap- State Fishing Lake | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): Horseshoe Lake ? ac [NHDWaterbody] *name; Horseshoe Lake ? ac [Boundaries] *name; Kitsap County Lakes ? ac [Non-DNR Major Public Lands, State Government] *name. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-5565 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-5565 | Ahtanum State Forest | https://www.dnr.wa.gov/Ahtanum |  |  | PIN INSIDE other record | name-mismatch/pin-doubt |
| US-5565 | Ahtanum State Forest | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-5566 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-5566 | Blanchard State Forest | https://www.dnr.wa.gov/Blanchard |  |  | PIN INSIDE other record | name-mismatch/pin-doubt |
| US-5566 | Blanchard State Forest | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-5567 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-5567 | Capitol State Forest | https://www.dnr.wa.gov/Capitol |  |  | PIN INSIDE other record | name-mismatch/pin-doubt |
| US-5567 | Capitol State Forest | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-5568 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-5568 | Elbe Hills-Tahoma State Forest | https://www.dnr.wa.gov/ElbeHillsTahoma |  |  | PIN INSIDE other record | name-mismatch/pin-doubt |
| US-5568 | Elbe Hills-Tahoma State Forest | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-5569 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-5569 | Green Mountain-Tahuya State Forest | https://www.dnr.wa.gov/GreenMountainTahuya |  |  | PIN INSIDE other record | name-mismatch/pin-doubt |
| US-5569 | Green Mountain-Tahuya State Forest | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels];  ? ac [NHDWaterbody]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-5570 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-5570 | Little Pend Oreille State Forest | https://www.dnr.wa.gov/LittlePendOreille |  |  | NOTHING NEAR | no-layer |
| US-5570 | Little Pend Oreille State Forest | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 9 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-5571 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-5571 | Loomis-Loup Loup State Forest | https://www.dnr.wa.gov/LoomisLoupLoup |  |  | PIN INSIDE other record | name-mismatch/pin-doubt |
| US-5571 | Loomis-Loup Loup State Forest | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-5572 | Olympic Peninsula State Forest | potamap lead (its PAD-US copy holds the pin): 'Olympic National Forest' owner USFS / manager USFS | R-G2 / R-G8 | R-G2: national forest vs state forest: NO | 2 | Oct 29 |
| US-5572 | | PAD-US at pin: Olympic National Forest (NF, owner USFS/FED, manager USFS, 631799 ac, Fee, PAD id 2916) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-5572 | Olympic Peninsula State Forest | https://www.dnr.wa.gov/OlympicPeninsula |  |  | PIN INSIDE | no-layer |
| US-5572 | Olympic Peninsula State Forest | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): Olympic National Forest ? ac [Non-DNR Major Public Lands, Federal Government] *name. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-5576 | | PAD-US at pin: Washington State Department of Natural R (SRMA, owner SDNR/STAT, manager SDNR, 2562869 ac, Fee, PAD id 271374) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-5576 | Yacolt Burn State Forest | https://www.dnr.wa.gov/Yacolt |  |  | PIN INSIDE other record | name-mismatch/pin-doubt |
| US-5576 | Yacolt Burn State Forest | look-up 9-p2-wa (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s):  ? ac [DNR Managed Land Parcels]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |


## chat 9 PIN TEST (Oct 30 9:05 AM, HQ 8:20 AM): 20 WA parks vs chat 3's layers. Hit = pin inside a polygon; NAME = a proper word of the POTA name is in the polygon's name; NO NAME MATCH = polygon at a pin is not a name match (lead only, pin never moved)
- WA State Parks (Parks_Administrative_Boundaries/FeatureServer/0): 0 of 20 pins inside a polygon, 0 with a name match; LAYER ERROR (layer index wrong?): {'code': 400, 'message': '', 'details': ['The requested layer (layerId: 0) was n
- WDFW Wildlife Areas (MapServices/WildlifeAreas/MapServer/0): 0 of 20 pins inside a polygon, 0 with a name match
- WDFW Water Access Sites (WP_RealEstate/WaterAccessSites/MapServer/0): 0 of 20 pins inside a polygon, 0 with a name match
- WA RCO Public Lands Inventory (Public_Lands_Inventory_2/FeatureServer/0): 17 of 20 pins inside a polygon, 1 with a name match
    US-11145 Naneum Ridge State Forest -> Kittitas [NO NAME MATCH]
    US-12296 Raging River State Forest -> King [NO NAME MATCH]
    US-12315 Dragoon Creek State Recreation Site -> Spokane [NO NAME MATCH]
    US-12316 Sherry Creek State Recreation Site -> Washington [NO NAME MATCH]
    US-12565 Skookum Creek State Recreation Area -> Pend Oreille [NO NAME MATCH]
    US-12566 Sheep Creek State Recreation Area -> Stevens [NO NAME MATCH]
    US-12567 Douglas Falls State Recreation Area -> Stevens [NO NAME MATCH]
    US-12569 Beverly Dunes State Recreation Site -> Grant [NO NAME MATCH]
    US-13516 Horseshoe -Kitsap- State Fishing La -> Kitsap [NAME]
    US-5565 Ahtanum State Forest -> Yakima [NO NAME MATCH]
    US-5566 Blanchard State Forest -> Skagit [NO NAME MATCH]
    US-5567 Capitol State Forest -> Thurston [NO NAME MATCH]
    US-5568 Elbe Hills-Tahoma State Forest -> Pierce [NO NAME MATCH]
    US-5569 Green Mountain-Tahuya State Forest -> Mason [NO NAME MATCH]
    US-5571 Loomis-Loup Loup State Forest -> Okanogan [NO NAME MATCH]
    US-5572 Olympic Peninsula State Forest -> Clallam [NO NAME MATCH]
    US-5576 Yacolt Burn State Forest -> Clark [NO NAME MATCH]
LAYER | WA parks | WA RCO Public Lands Inventory | https://services2.arcgis.com/TGEC20q86HQAeMS6/arcgis/rest/services/Public_Lands_Inventory_2/FeatureServer/0 | name field: see layer | pin test Oct 30 chat 9: 1 of 17 hits name-match
NOTE: WA State Parks FeatureServer/0 not found (layer index being checked). WDFW Wildlife Areas / Water Access 0 hits: pins are not inside those polygons.
