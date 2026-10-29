# Missing boundaries: the list for Fable (NEWEST ONLY; Brandon Oct 29 1:54 PM: 'get rid of old one')
The 8:55 AM index was removed. Its detail files are still in .claude/build/research/ if anyone needs them.

## RERUN on the NEW Rule G key (chat 8, Oct 29 ~2:30 PM, grade A; replaces my 2:05 PM section, which read the stale KPC-Data copy)
Read from KPC-Links data/us-key (13,083 parks, 11,312 outlined, 120 check, 808 sites on bigger land, 858 nothing found, pin outside 4,210).
- **The 313 "pin inside a bigger area": 24 now outlined, 289 left.** Needs R-G7 step 2 (a state layer already names something): 63. Step 3 (the official park map hunt; the POTA page link is given): 224. Step 3 with no page at all: 2. Step 4 (ownership) comes only after step 3 finds no boundary line.
- **"Nothing near" 273: 7 now outlined, 266 left. "Likely" 24: 13 now outlined, 11 left.**
- **Fable list so far: nothing.** It is only what steps 2-5 cannot place, so it stays empty until chat 2 / the look-up bot run them. Pool of refs: `missing-after-key.json` (keys PIN INSIDE / NOTHING NEAR / LIKELY).
- Other no-outline parks outside these lists (about 1,000): BLM recreation areas, state trails, historic sites, wild and scenic rivers, national recreation trails. Those are Source Book / own-land work, not R-G7.
- Open key questions: chat 11 answered 26 YES / 1 NO; the rest wait.

## WORK LOG BY STATE (Brandon Oct 29 3:21 PM: everything found goes in THIS file)
One section per state, low to high (IA, MN, RI, CO, HI, ME, VA, AZ, NM, …, NV). Each chat that works a park adds ONE row under its state, never deletes others' rows:
`| park | name | source found (link / layer / our doc) | Rule G step | result: traced / owned land / pin | by chat | date |`
When every park in a state has a row, add 'STATE XX DONE' under it. What is left with 'pin' and no source = the real Fable list.

### MN
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-13547 | Two Harbors Protected Area | our doc: DNR harbor page, no map; look-up blocked (403) | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13546 | Twin Points Protected Area | our doc: DNR harbor page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13548 | Knife River Marine Protected Area | our doc: DNR harbor page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13549 | McQuade Marine Protected Area | our doc: DNR harbor page, no map | 3 | pin (no source yet) | 8 | Oct 29 |

### CO
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-9652 | Grenada SWA | our parkinfo: POTA link = cpw.state.co.us GranadaDeadmanSWA_geo.pdf (opened 200); map-check filed | 3 (map found) | to trace | 8 | Oct 29 |
| US-10540 | Bellevue-Watson Fish Hatchery | cpw.state.co.us/hatchery/bellvue-watson (opened; page, no map); Watson Lake SWA geo PDF likely | 3 | pin until map seen | 8 | Oct 29 |

### ME
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-9174 | Mahoosuc Ecological Reserve | our doc: maine.gov/dacf/mnap page, no map; BPL site 403 to bot | 3 | pin (no source yet) | 8 | Oct 29 |
| US-8287 | Capitol State Park | NRHP 89000252 nomination PDF opened (200), written boundary; POTA link is AllTrails | 3 -> 4a | to read + trace | 8 | Oct 29 |

### AZ
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-11944 | Dankworth Pond SP | AZ State Parks park map PDF (usedirect DAPO_Park Map_8-2023); map-check filed | 3 (map found) | to trace | 8 | Oct 29 |
| US-3390 | River Island SP | AZ State Parks park map PDF Park Map-RIIS (opened 200); map-check filed | 3 (map found) | to trace | 8 | Oct 29 |
| US-6071 | Little Black Mountain Petroglyph Site | BLM page (opened 200): BLM Arizona Strip site, not state land; BLM surface layer | 3 -> 4b | BLM land: trace from BLM layer | 8 | Oct 29 |

### CT
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-6860 | Ferry Landing SP | our doc: depdata.ct.gov parks map (statewide, does not name park) | 3 | pin until DEEP park map seen | 8 | Oct 29 |
| US-6875 | The Preserve (Essex Land Trust) | our doc: DEEP page, no map; land trust owns | 3 -> 4b | land-trust parcel; take-back candidate | 8 | Oct 29 |
| US-7529 | Beckley Iron Furnace SP | our doc: DEEP page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-7542 | Satan's Kingdom SRA | our doc: no map on DEEP page | 3 | pin (no source yet) | 8 | Oct 29 |

### MO
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-5715 | Roger Pryor Pioneer Backcountry SP | our doc: park page, no working map; mostateparks trail map PDFs | 3 | pin until map seen | 8 | Oct 29 |
| US-5716 | Bruce R. Watkins Cultural Heritage Center SP | our doc: no map | 3 -> 4b | Jackson County parcel | 8 | Oct 29 |
| US-10575 | Walnut Woods CA | MDC news (opened): donated to City of Liberty Parks & Rec; our doc: no map | 4b | owner = City of Liberty: Clay County parcel | 8 | Oct 29 |
| US-10576 | Rush Creek CA | MDC news (opened): donated to City of Liberty Parks & Rec | 4b | owner = City of Liberty: Clay County parcel | 8 | Oct 29 |

### SC
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-9229 | Wild Turkey WMA | SCDNR WMA map PDF wmamap5 (opened 200; WMA unconfirmed); SCDNR ManagedLand/116 page; map-check filed | 3 | to confirm which WMA the PDF is | 8 | Oct 29 |
| US-9759 | May Forest SP | our doc: park page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13016 | Pine Island SP | our doc: park page, no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-13198 | Black River SP | our doc: park page, no map | 3 | pin (no source yet) | 8 | Oct 29 |

### LA
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-2365 | Jimmie Davis SP | our doc: no map on file; web search: no Louisiana state-parks open-data layer found (LDOTD layers only) | 3 | pin (no source yet) | 8 | Oct 29 |
| US-2373 | Poverty Point Reservoir SP | our doc: no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-10354 | Forts Randolph & Buhlow SHS | our doc: no map | 3 | pin (no source yet) | 8 | Oct 29 |
| US-10447 | Audubon SHS | our doc: only a brochure-request page | 3 | pin (no source yet) | 8 | Oct 29 |
| US-2374 | Saint Bernard SP | our doc: no map | 3 | pin (no source yet) | 8 | Oct 29 |

### MD
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-13564 | Savage Highlands SP | our doc: no map; leads: MD iMAP MD_ProtectedLands (geodata.md.gov) + DNR AIMS layers (dnr.geodata.md.gov); layer-probe 8-rg7-mdnh filed | 2 -> 3 | to check state layer | 8 | Oct 29 |
| US-7768 | Frederick City Watershed WMA | our doc: map page does not name park; lead WMABoundaries FeatureServer + MD_ProtectedLands | 2 | to check state layer | 8 | Oct 29 |
| US-7769 | Heaters Island WMA | our doc: dnr.maryland.gov/wildlife/Documents/heatersislandmap.pdf (own map PDF) + WMABoundaries layer | 3 (map found) | to trace | 8 | Oct 29 |
| US-6388 | Tawes Garden SP | our doc: map page does not name park; MD_ProtectedLands | 2 | to check state layer | 8 | Oct 29 |
| US-6389 | Jefferson Patterson Park & Museum SP | our doc: no map; MD_ProtectedLands | 2 | to check state layer | 8 | Oct 29 |

### NH
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-2642 | Androscoggin Wayside SP | our doc: shared 51-park file dropped; leads: NHDOT_BOUNDARIES_Parks_Forest MapServer, GRANIT consnh conservation lands | 2 | to check state layer | 8 | Oct 29 |
| US-2654 | Gardner Memorial Wayside SP | same | 2 | to check state layer | 8 | Oct 29 |
| US-2685 | Winslow SP | our doc: nhstateparks.org Mt-Kearsarge map PDF (own map) + consnh | 3 (map found) | to trace | 8 | Oct 29 |
| US-8024 | Taylor Saw Mill SHS | our doc: dropped shared file; consnh | 2 | to check state layer | 8 | Oct 29 |
| US-4931 | Max Israel State Forest | NH Div. of Forests and Lands "State Reservation Maps" page (nhdfl.dncr.nh.gov/land-management/state-reservation-maps); consnh | 3 | page to read (bot filed) | 8 | Oct 29 |
| US-4936 | Nash Stream Forest State Forest | same | 3 | page to read (bot filed) | 8 | Oct 29 |
| US-4980 | White Farm State Forest | same | 3 | page to read (bot filed) | 8 | Oct 29 |
### NM (add)
| US-2719 | Angel Fire Vietnam Veterans Memorial | our docs none; POTA link https://www.vietnamveteransmemorial.org/ | R-G7 step 3 -> 4b | pending (3-fable-low-c) | chat 3 | Oct 29 |
### DE
| US-10687 | Trussum Pond State Fishing Lake | POTA link = DNREC pond maps web app (experience.arcgis.com ...Pond-Maps); our docs: no map | R-G7 step 3 (a pond map, check it shows land) | to check, then 4b | chat 3 | Oct 29 |
| US-4367 | First State Heritage Park | https://destateparks.com/History/FirstStateHeritage ; docs: none; nothing near | R-G7 step 3 -> 4b (Dover, state-owned parcels) | pending (3-fable-low-c) | chat 3 | Oct 29 |
| US-9885 | Indian River Life-Saving Station SHS | https://destateparks.com/Centers/IRLifesavingStation ; pin inside Delaware Seashore SP | R-G7 step 3 -> 4b | pending (3-fable-low-c) | chat 3 | Oct 29 |
| US-9886 | Dupont Nature Center State Conservation Area | DNREC page; pin inside Milford Neck Wildlife Area | R-G7 step 3 -> 4b | pending (3-fable-low-c) | chat 3 | Oct 29 |
### MT
| US-11216, 11219 | Big Springs / Jacko River Trout State Fish Hatcheries | MT FWP lands pages (lmsId 39753636, 39753949) | R-G7 step 3 -> 4b (FWP-owned parcel) | pending (3-fable-low-c) | chat 3 | Oct 29 |
| US-12827 | Brownes Lake SFWA | FWP FAS page 39753504 (pin inside Brownes Bridge FAS: different name) | R-G7 step 2/3 | pending (3-fable-low-c) | chat 3 | Oct 29 |
| US-12925 | Thoreau State Beach | FWP FAS page 39753904 (key 'likely' = Missoula Field Office: wrong, R-G8) | R-G7 step 3 | pending (3-fable-low-c) | chat 3 | Oct 29 |
### IL
| US-10661 | Oakwood Bottoms USFS Rec Area | OUR DOCS ok: https://www.fs.usda.gov/r09/shawnee/maps-guides (Shawnee NF maps page, may not name the area) | R-G7 step 3; USFS rec sites usually have no boundary: 4b NF-owned parcel inside Shawnee | pending (3-fable-low-c) | chat 3 | Oct 29 |
| US-10788 | Ray Norbut East Hannibal Unit SFWA | docs: no readable map; https://huntillinois.org/sites/ray-norbut-sfwa/ | R-G7 step 3 | pending (3-fable-low-c) | chat 3 | Oct 29 |
| US-12640 | Rauchfuss Hill SRA | OUR DOCS ok: hunter map PDF .../RauchfussHillHunterMap.pdf (a hunter map: check for the property line) | R-G7 step 4a from our docs if a line shows | pending (3-fable-low-c) | chat 3 | Oct 29 |
| US-4118 | Copperhead Hollow SWA | OUR DOCS ok: hunter map PDF .../CopperheadHollowHunterMap.pdf | R-G7 step 4a from our docs if a line shows | pending (3-fable-low-c) | chat 3 | Oct 29 |
| US-13298 | North Point Marina SRA | https://dnr.illinois.gov/parks/park.northpointmarina.html ; docs none; pin inside Illinois Beach SP | R-G7 step 3 -> 4b | pending (3-fable-low-c) | chat 3 | Oct 29 |
### MA
| US-2436 | Greycourt State Park | docs none; mass.gov Lawrence Heritage page is a different park's page: check | R-G7 step 3 | pending (3-fable-low-c) | chat 3 | Oct 29 |
| US-8385 | Farnham-Connolly State Park | mass.gov page; docs none | R-G7 step 3 | pending (3-fable-low-c) | chat 3 | Oct 29 |
| US-8387 | Martini Shell Park / Moynihan SRA | mass.gov page; pin inside Neponset River Reservation | R-G7 step 3 | pending (3-fable-low-c) | chat 3 | Oct 29 |
| US-8388 | Great Falls Discovery Center SRA | mass.gov page; nothing near | R-G7 step 3 -> 4b | pending (3-fable-low-c) | chat 3 | Oct 29 |
| US-8422 | Pope John Paul II Park State Reserve | OUR DOCS ok: https://www.mass.gov/doc/neponset-river-greenway-map-tnf | R-G7 step 4a from our docs if the map shows the line | pending (3-fable-low-c) | chat 3 | Oct 29 |
### Oct 29 3:55 PM chat 3 update (look-up B read)
- RI US-10545: layer 21 name query returned 'Failed to execute query' (400); retried with UPPER(NAME) LIKE in 3-fable-low-d.
- IA US-9334: FWS Iowa WMD map page opened (75 WPAs, 18 counties); whether Teal Basins is drawn needs a screenshot (low-d).
- VA US-9931, HI US-10923, VA US-9961: the bot read the PDFs as raw bytes (no text); screenshots asked in low-d.
- NM US-11797 Los Luceros: nmhistoricsites page opened, no map link. HI US-10925: dlnr forestry reserves page is 404 (both Hawaii DLNR URLs dead); needs a search for the working page.

**ACTIVE SET (Brandon 3:29 PM: 24 states at a time, fewest parks first):** IA 1, MN 1, RI 1, CO 2, HI 2, ME 2, VA 2, AZ 3, NM 3, CT 4, DE 4, MO 4, MT 4, SC 4, IL 5, LA 5, MA 5, MD 5, CA 6, NH 7, WV 7, NY 8, TN 8, AK 9 (102 parks). Next in line: GA 9, NE 9, FL 10, AL 11, TX 11, WY 11, WI 12, VT 14, MI 16, IN 17, UT 17, KS 18, OR 18, NC 19, WA 20, AR 22, OK 31, ID 38, ND 42, MS 51, NV 68.
### Oct 29 3:40 PM chat 3 update (look-up C + D read)
- IA US-9334: FWS Iowa WMD map page has a 'Boundaries' layer ('boundary map layer compiled by USFWS', 75 WPAs). Teal Basins WPA is a FWS WPA, so the outline source = FWS WPA boundaries (key already holds 'Teal Basins WPA' 151 ac: R-G8 type/agency check, then it is chat 2's join). Result: map found (agency boundary layer).
- RI US-10545: RIDEM layer 21 has NO record named Hillsdale (query returned none). Pin sits in 'Beaver River - deCoppett' (1,825 ac). R-G7 step 3 not met -> step 4b (RIDEM-owned parcel, Richmond; the 45-acre parcel from the DEM press release). Still pin.
- MT per-site official FWP maps (to confirm lines): US-11216 .../visitmaps/htc/39753636.pdf ; US-11219 .../htc/39753949.pdf ; US-12827 .../visitmaps/fas/39753504.pdf ; US-12925 .../fas/39753904.pdf. Screenshots asked (low-e).
- IL US-13298 North Point: site map PDF https://dnr.illinois.gov/content/dam/soi/en/web/dnr/parks/documents/northpointmarinasitemap.pdf ; US-10788 Ray Norbut: IDNR web app find=Ray Norbut (webmap aca55c3d...) + page #site-maps; US-12640/4118 hunter map PDFs (our docs) and US-10661 Shawnee 'maps-guides' + GIS page https://www.fs.usda.gov/r09/shawnee/data-tools/gis (step 2: USFS layers may name Oakwood Bottoms). Screenshots asked (low-e).
- MA US-2436 / 8385 / 8387 / 8388: mass.gov pages carry NO map link; step 2 = MassGIS Protected and Recreational OpenSpace layer (state open-data portal, first in RESEARCH ORDER) -> next request. US-8422: Neponset Greenway map doc https://www.mass.gov/doc/neponset-river-greenway-map-tnf/download (screenshot asked).
- DE: destateparks.com pages return 403 to the bot (US-4367, US-9885); DNREC Dupont Nature Center page opened, no map. Next: Delaware open data portal (FirstMap) layers. VA / HI / NM: see 3:55 update; PDFs still need a text/picture reading (low-d gave 2 screenshots only).
- NM US-2719 Angel Fire: site has only a contact page; no map. Pin until parcel step.

