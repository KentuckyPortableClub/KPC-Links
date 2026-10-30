# Fable book: US-MI (38 rows, 19 parks)
HANDOFF (chat 3, Oct 30): Fable work moves to CHAT 8. Step 0 done (16). MI DNR layers found (LAYER lines below) -> WAITING chat 9 pin-in-polygon test (state forests vs Forest Management Units; harbors vs DNR Managed Sites). Harbor pages 404 (no addresses yet).
LAYER | Michigan DNR Forest Management Units | https://www.arcgis.com/sharing/rest/content/items/448967a78d3a4555beaf01f9758a44d9?f=json | found by chat 3 Oct 29-30 | not yet tested against the pins
LAYER | DNR Managed Sites (harbors?) | https://www.arcgis.com/sharing/rest/content/items/a46f4574972e4e98975ae6980220ad10?f=json | found by chat 3 Oct 29-30 | not yet tested against the pins
LAYER | Michigan DNR Wildlife Management Units | https://www.arcgis.com/sharing/rest/content/items/52d906e14ef24af9ae4e7273cf140478?f=json | found by chat 3 Oct 29-30 | not yet tested against the pins
LAYER | DNRManagementBoundariesOPENDATA | https://www.arcgis.com/sharing/rest/content/items/876d19a2df964cee99b90a762d822061?f=json | found by chat 3 Oct 29-30 | not yet tested against the pins
LAYER | Michigan DNR Project Boundaries | https://www.arcgis.com/sharing/rest/content/items/ca1937dd369049f2b700504dd4cca11e?f=json | found by chat 3 Oct 29-30 | not yet tested against the pins
LAYER | DNRLOTSParcelsOPENDATA (parcels, step 4b) | https://www.arcgis.com/sharing/rest/content/items/01fdcbcb99d74265aa6a9147a5fdc7f9?f=json | found by chat 3 Oct 29-30 | not yet tested against the pins
ONE ROW PER PARK from now on: update the park's row in place (add to its cells), don't add a new row. Read the Agency Atlas first: .claude/build/research/agency-atlas/US-MI.md

| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-12802 | | PAD-US at pin: Ottawa National Forest (NF, owner USFS/FED, manager USFS, 994695 ac, Fee, PAD id 3074) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-12802 | Norwich State Game Land | pin inside Ottawa National Forest; POTA link = USFS Box folder | pin-doubt |
| US-12802 | Norwich State Game Land | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-4774 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-4774 | Au Sable State Forest | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): N/A 2997536 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-4774..4779 | Au Sable, Copper Country, Escanaba River, Lake Superior, Mackinaw, Pere Marquette State Forests | POTA link = MI DNR ArcGIS web viewer; no map in our docs | no-layer (check MI DNR open data) |
| US-4775 | | PAD-US at pin: Crystal Falls State Forest Area (SCA, owner SDNR/STAT, manager SDNR, 300717 ac, Fee, PAD id 71307) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-4775 | Copper Country State Forest | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): Grouse Enhanced Management Site 5305 ac [Wildlife Property Boundary]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-4776 | Escanaba River State Forest | potamap lead (its PAD-US copy holds the pin): 'Escanaba State Forest Area' owner SDNR / manager SDNR | R-G2 / R-G8 | R-G2 name agrees (state forest area): CANDIDATE | 2 | Oct 29 |
| US-4776 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-4776 | Escanaba River State Forest | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-4776 Escanaba River SF | NOT SURE | 'State Forest Area' is a management area |
| US-4777 | | PAD-US at pin: Newberry State Forest Area (SCA, owner SDNR/STAT, manager SDNR, 348461 ac, Fee, PAD id 71314) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-4777 | Lake Superior State Forest | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-4778 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-4778 | Mackinaw State Forest | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-4779 | | PAD-US at pin: Cadillac State Forest Area (SCA, owner SDNR/STAT, manager SDNR, 221994 ac, Fee, PAD id 71306) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-4779 | Pere Marquette State Forest | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-6728 | | PAD-US at pin: Sleeping Bear Dunes National Lakeshore (NLS, owner NPS/FED, manager NPS, 56717 ac, Fee, PAD id 3320) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6728 | Manitou Island Group WMA | DNR reference-map PDF; pin sits inside Sleeping Bear Dunes | picture-map-only / pin-doubt |
| US-6728 | Manitou Island Group Wildlife Management Area | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): N/A 33855630 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-6808 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6808 | Cedar River State Harbor | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): N/A 33855630 ac [FWSApproved]; N/A 2102171 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-6808, 6809, 6813, 6814, 6815, 6817, 6821, 6822 | eight state harbors | DNR harbor guide pages | needs-parcel |
| US-6809 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6809 | Copper Harbor State Harbor | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-6813 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6813 | Hammond Bay State Harbor | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): N/A 33855630 ac [FWSApproved]; N/A 2997536 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-6814 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6814 | Lac LaBelle State Harbor | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-6815 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6815 | Lexington State Harbor | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-6817 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6817 | Little Lake State Harbor | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2: no polygon at the pin (100 m) in 5 layers read (state + BLM rec + FWS + NPS); pin stays | chat 9 | 2026-10-29 |
| US-6821 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6821 | Straits State Harbor | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): N/A 33855630 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-6822 | | PAD-US at pin: nothing (no public-land record holds the pin) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-6822 | Whitefish Point State Harbor | look-up 9-p2-mi (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): N/A 33855630 ac [FWSApproved]. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |


## chat 9 PIN TEST (Oct 30 9:05 AM, HQ 8:20 AM): 16 MI parks vs chat 3's layers. Hit = pin inside a polygon; NAME = a proper word of the POTA name is in the polygon's name; NO NAME MATCH = polygon at a pin is not a name match (lead only, pin never moved)
- MI DNR Forest Management Units (DNRManagementBoundariesOPENDATA/FeatureServer/2): 13 of 16 pins inside a polygon, 1 with a name match
    US-12802 Norwich State Game Land -> Baraga [NO NAME MATCH]
    US-4774 Au Sable State Forest -> Grayling [NO NAME MATCH]
    US-4775 Copper Country State Forest -> Escanaba [NO NAME MATCH]
    US-4776 Escanaba River State Forest -> Escanaba [NAME]
    US-4777 Lake Superior State Forest -> Newberry [NO NAME MATCH]
    US-4778 Mackinaw State Forest -> Gaylord [NO NAME MATCH]
    US-4779 Pere Marquette State Forest -> Cadillac [NO NAME MATCH]
    US-6728 Manitou Island Group Wildlife Manag -> Traverse City [NO NAME MATCH]
    US-6808 Cedar River State Harbor -> Escanaba [NO NAME MATCH]
    US-6809 Copper Harbor State Harbor -> Baraga [NO NAME MATCH]
    US-6814 Lac LaBelle State Harbor -> Baraga [NO NAME MATCH]
    US-6815 Lexington State Harbor -> Southern [NO NAME MATCH]
    US-6817 Little Lake State Harbor -> Newberry [NO NAME MATCH]
LAYER | MI parks | MI DNR Forest Management Units | https://services3.arcgis.com/Jdnp1TjADvSDxMAX/arcgis/rest/services/DNRManagementBoundariesOPENDATA/FeatureServer/2 | name field: see layer | pin test Oct 30 chat 9: 1 of 13 hits name-match
- MI DNR Managed Sites (DNRReferenceAssetsOPENDATA/FeatureServer/10): 0 of 16 pins inside a polygon, 0 with a name match
- MI DNR Wildlife Management Units (DNRManagementBoundariesOPENDATA/FeatureServer/7): 13 of 16 pins inside a polygon, 0 with a name match
    US-12802 Norwich State Game Land -> Northern Michigan Region [NO NAME MATCH]
    US-4774 Au Sable State Forest -> Northern Michigan Region [NO NAME MATCH]
    US-4775 Copper Country State Forest -> Northern Michigan Region [NO NAME MATCH]
    US-4776 Escanaba River State Forest -> Northern Michigan Region [NO NAME MATCH]
    US-4777 Lake Superior State Forest -> Northern Michigan Region [NO NAME MATCH]
    US-4778 Mackinaw State Forest -> Northern Michigan Region [NO NAME MATCH]
    US-4779 Pere Marquette State Forest -> Northern Michigan Region [NO NAME MATCH]
    US-6728 Manitou Island Group Wildlife Manag -> Northern Michigan Region [NO NAME MATCH]
    US-6808 Cedar River State Harbor -> Northern Michigan Region [NO NAME MATCH]
    US-6809 Copper Harbor State Harbor -> Northern Michigan Region [NO NAME MATCH]
    US-6814 Lac LaBelle State Harbor -> Northern Michigan Region [NO NAME MATCH]
    US-6815 Lexington State Harbor -> Southern Michigan Region [NO NAME MATCH]
    US-6817 Little Lake State Harbor -> Northern Michigan Region [NO NAME MATCH]
- MI DNR Project Boundaries (DNRLOTSParcelsOPENDATA/FeatureServer/13): 5 of 16 pins inside a polygon, 1 with a name match
    US-4774 Au Sable State Forest -> Grayling Forest Management Unit [NO NAME MATCH]
    US-4775 Copper Country State Forest -> Crystal Falls Forest Management Unit [NO NAME MATCH]
    US-4776 Escanaba River State Forest -> Escanaba Forest Management Unit [NAME]
    US-4777 Lake Superior State Forest -> Newberry Forest Management Unit [NO NAME MATCH]
    US-4779 Pere Marquette State Forest -> Cadillac Forest Management Unit [NO NAME MATCH]
LAYER | MI parks | MI DNR Project Boundaries | https://services3.arcgis.com/Jdnp1TjADvSDxMAX/arcgis/rest/services/DNRLOTSParcelsOPENDATA/FeatureServer/13 | name field: see layer | pin test Oct 30 chat 9: 1 of 5 hits name-match
NOTE: Forest Management Units and Wildlife Management Units are big district polygons (13 of 16 pins inside, almost no name match): they say WHICH unit a park is in, not the park outline. DNR Managed Sites 0 of 16 pins (point or small layer).

Chat 8 (Oct 30): confirmed **US-4776 Escanaba River State Forest -- the only trace candidate of the 6 named state forests.** Checked Wikipedia's List of Michigan state forests: it does NOT establish a 1:1 mapping of the 6 historic names (Au Sable, Copper Country, Escanaba River, Lake Superior, Mackinaw, Pere Marquette) to today's city-named Forest Management Units, so I will not force a match by geography alone. Escanaba River stands on its own T-1 merit (shares the proper word "Escanaba" directly with both the PAD-US "Escanaba State Forest Area" and the FMU/Project-Boundary "Escanaba Forest Management Unit" -- chat 2's existing CANDIDATE confirmed by two layers now). **The other 5 (Au Sable, Copper Country, Lake Superior, Mackinaw, Pere Marquette) share NO proper word with their FMU (Grayling, Crystal Falls, Newberry, Gaylord, Cadillac) -- per T-1 this is never a question, confirmed name-mismatch, pins stay, no grey area.** **8 state harbors**: found MI DNR's dedicated BAS_Harbors service -- its "Harbors" layer is POINT only (no polygon anywhere in the service), so there is no boundary layer for any MI state harbor, period; all 8 stay pin/needs-parcel (can be used later to check pin position, never to trace). **US-6728 Manitou Island Group WMA**: untried wildlife-specific layer (DNRWILDLandsOPENDATA) handed to chat 9. **US-12802 Norwich State Game Land**: found it's likely a USFS "Norwich Openings Complex" inside Ottawa NF, not a MI DNR property at all (matches the PAD-US owner) -- handed to chat 9 to check for a USFS project-boundary layer. **STATE MI DONE** (16/16 accounted for: 1 trace candidate, 5 confirmed name-mismatch/no-layer, 8 confirmed no-polygon-exists (harbors), 2 layer probes to chat 9). Next: UT 17.
