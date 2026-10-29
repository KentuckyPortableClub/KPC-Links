# Missing boundaries: the list for Fable (NEWEST ONLY; Brandon Oct 29 1:54 PM: 'get rid of old one')
The 8:55 AM index was removed. Its detail files are still in .claude/build/research/ if anyone needs them.

## RERUN on the NEW Rule G key (chat 8, Oct 29 ~2:30 PM, grade A; replaces my 2:05 PM section, which read the stale KPC-Data copy)
Read from KPC-Links data/us-key (13,083 parks, 11,312 outlined, 120 check, 808 sites on bigger land, 858 nothing found, pin outside 4,210).
- **The 313 "pin inside a bigger area": 24 now outlined, 289 left.** Needs R-G7 step 2 (a state layer already names something): 63. Step 3 (the official park map hunt; the POTA page link is given): 224. Step 3 with no page at all: 2. Step 4 (ownership) comes only after step 3 finds no boundary line.
- **"Nothing near" 273: 7 now outlined, 266 left. "Likely" 24: 13 now outlined, 11 left.**
- **Fable list so far: nothing.** It is only what steps 2-5 cannot place, so it stays empty until chat 2 / the look-up bot run them. Pool of refs: `missing-after-key.json` (keys PIN INSIDE / NOTHING NEAR / LIKELY).
- Other no-outline parks outside these lists (about 1,000): BLM recreation areas, state trails, historic sites, wild and scenic rivers, national recreation trails. Those are Source Book / own-land work, not R-G7.
- Open key questions: chat 11 answered 26 YES / 1 NO; the rest wait.

- **PICTURE MAPS FOR FABLE (Brandon 3:58 PM: 'fable might figure out something from it'):** rows marked 'picture map only (G-ID3)' keep the map link on purpose: Fable may find a way to use them (e.g. matching the picture to parcels or roads) without drawing a rough line. Search this file for G-ID3.

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
| US-9652 | Grenada SWA | our parkinfo: POTA link = cpw.state.co.us GranadaDeadmanSWA_geo.pdf (opened 200); map-check filed | 3 (map found) | TRACE: map read: Granada AND Deadman SWAs (Prowers Co., CPW 3/5/2018), legend shows "SWA Boundary"; disclaimer: mapped lines may not match legal holdings (note: one map, two SWAs, trace only Granada) | 8 | Oct 29 |
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
| US-9229 | Wild Turkey WMA | SCDNR WMA map PDF wmamap5 (opened 200; WMA unconfirmed); SCDNR ManagedLand/116 page; map-check filed | 3 | CORRECTION: wmamap5 is NOT Wild Turkey (it shows Draper/McConnells/Ross/Kirsh, Rock Hill Blackjacks, Worth Mountain, Delta); need the other map number for Wild Turkey (SCDNR ManagedLand/116 page) | 8 | Oct 29 |
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

### NY
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-2081 | Iona Island WMA | NY DEC layers: gisservices.dec.ny.gov dil_land_activities MapServer/2 "Wildlife Management Areas" and reference MapServer/2 "DEC Lands"; our doc: map page does not name park | 2 (agency layer) | to check layer | 8 | Oct 29 |
| US-8103 | Cayuga Lake WMA | our parkinfo: POTA link = dec.ny.gov cayugamap.pdf (own map); DEC WMA layer | 3 (map found) / 2 | to trace | 8 | Oct 29 |
| US-2151 | Thompsons Lake SP | our doc: no map; OPRHP park (parks.ny.gov); state park boundary layer not yet found (only OPRHP regions) | 2 | pin (no source yet) | 8 | Oct 29 |
| US-8082 | Jamaica Bay "State" Wildlife Area | our doc: nps.gov/gate maps page (Gateway NRA is NPS land, not state); NPS boundary | 3 -> 4b | NPS land: use NPS Gateway boundary | 8 | Oct 29 |
| US-8084 | Breezy Point Tip "State" Rec Area | our doc: same NPS Gateway maps page | 3 -> 4b | NPS land | 8 | Oct 29 |
| US-8088 | Miller Field "State" Rec Area | our doc: same NPS Gateway maps page | 3 -> 4b | NPS land | 8 | Oct 29 |
| US-2001 | Adirondack Park | our doc: dec.ny.gov adkmaponly.pdf (the Blue Line map); DEC lands layers DECLANDS_ADK | 3 / GREY G-NY1 | see grey area | 8 | Oct 29 |
| US-8070 | Catskill Park | our doc: no working map; DEC Lands layer | 3 / GREY G-NY1 | see grey area | 8 | Oct 29 |

### AK
| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-10464 | Chena Wayside SRS | AK DNR Open Data: arcgis.dnr.alaska.gov OpenData/Recreational_ParkBoundary MapServer layer 2 "ASP Park Boundary" (also DPOR/Park_Boundary_Facility); no doc entry for AK | 2 (agency layer) | to check layer | 8 | Oct 29 |
| US-11846 | Bing's Landing SRS | AK DNR Open Data: arcgis.dnr.alaska.gov OpenData/Recreational_ParkBoundary MapServer layer 2 "ASP Park Boundary" (also DPOR/Park_Boundary_Facility); no doc entry for AK | 2 (agency layer) | to check layer | 8 | Oct 29 |
| US-12709 | Funny River Campground SRS | AK DNR Open Data: arcgis.dnr.alaska.gov OpenData/Recreational_ParkBoundary MapServer layer 2 "ASP Park Boundary" (also DPOR/Park_Boundary_Facility); no doc entry for AK | 2 (agency layer) | to check layer | 8 | Oct 29 |
| US-12710 | Izaak Walton Campground SRS | AK DNR Open Data: arcgis.dnr.alaska.gov OpenData/Recreational_ParkBoundary MapServer layer 2 "ASP Park Boundary" (also DPOR/Park_Boundary_Facility); no doc entry for AK | 2 (agency layer) | to check layer | 8 | Oct 29 |
| US-12711 | Morgan's Landing SRS | AK DNR Open Data: arcgis.dnr.alaska.gov OpenData/Recreational_ParkBoundary MapServer layer 2 "ASP Park Boundary" (also DPOR/Park_Boundary_Facility); no doc entry for AK | 2 (agency layer) | to check layer | 8 | Oct 29 |
| US-11834 | Susitna Landing SRS | ADF&G access site (Alaska Dept of Fish and Game, not DNR parks); ASP layer may not hold it | 2/3 | to check layer; else pin | 8 | Oct 29 |
| US-11835 | Little Susitna Public Use Facility SRS | ADF&G facility (same as above) | 2/3 | to check layer; else pin | 8 | Oct 29 |
| US-13462 | Sportsman's Angler Access SRS | ADF&G fishing access (same) | 2/3 | to check layer; else pin | 8 | Oct 29 |
| US-11798 | Tangle Lakes Archeological Reserve | BLM page (cultural heritage); BLM land | 3 -> 4b | BLM land: BLM layer | 8 | Oct 29 |

### Adirondack Park + Catskill Park (US-2001, US-8070): Rule G answers it (Brandon Oct 29 3:34 PM "G rules are the rules"; my G-NY1 withdrawn)
R-G7 step 4(a): the park has its own official boundary line (the Blue Line; our doc has DEC's adkmaponly.pdf, and DEC publishes park-boundary layers) = that line is the outline. Private land inside is handled the way POTA's plain answer 5 says (private inholdings are not activatable; the 2-fer rules cut them out), not by shrinking the outline. Source: NY DEC park boundary layers / Blue Line map. Trace (chat 2).

### UPDATES to the work log, Oct 29 ~4:50 PM (chat 8; rows above stay, these add sources)
| st | park(s) | new source | Rule G step | result |
|---|---|---|---|---|
| ME | US-8287 Capitol State Park | NRHP nomination 89000252 (opened): Capitol Park, Augusta, 1827 landscape, about 20 ac; verbal boundary "City of Augusta tax map 32, lot 24" | 4a (a written boundary + parcel) | TRACE from the City of Augusta parcel, tax map 32 lot 24 |
| ME | US-9174 Mahoosuc Ecological Reserve | Maine BPL GIS/Mapping page (maine.gov/DACF/parks/about/gis_mapping.shtml) for BPL lands; Maine "Conservation Lands" layer (gis.maine.gov MapServer/5) | 2 | to check layer for the Mahoosuc Public Reserved Land unit |
| CT | US-6860 Ferry Landing, US-7529 Beckley, US-7542 Satan's Kingdom, US-6875 The Preserve | CT "DEEP Property" dataset (CT DEEP's own owned-land polygons; catalog.data.gov/dataset/deep-property) and "Protected Open Space" (owner field) | 2 (agency's own record) | to check dataset; The Preserve: open-space owner tells state vs land trust |
| MN | US-13547 Two Harbors, US-13546 Twin Points, US-13548 Knife River, US-13549 McQuade | MN DNR pages (dnr.state.mn.us/water_access/harbors/...): they are DNR "small craft harbors / protected access" sites (McQuade Small Craft Harbor, Knife River Marina and Access); DNR small craft harbor page | 3 -> 4b | the DNR-owned harbor parcels (Lake/St. Louis County parcels); no boundary map on the pages |
| SC | US-9229 Wild Turkey WMA | SCDNR WMA maps are numbered wmamapN.pdf (5 = Draper/McConnells/Ross..., NOT Wild Turkey); SCDNR ManagedLand/116 page | 3 | find the right map number via the page |
| NH, MD, NY, AK | see rows above | MD iMAP server was down (503), NH reservation page blocks the bot (403) | 2 | retry later |
### Oct 29 3:55 PM chat 3 update (look-up F read: CA WV TN)
- CA US-3578 Tijuana Estuary: CA State Parks map viewer https://csparks.maps.arcgis.com/apps/instant/basic/index.html?appid=065b067caa204e8da48d4b53c9483ab0&UNITNBR=9997 (official, a unit boundary viewer; step 3 found) + brochure PDF https://www.parks.ca.gov/pages/669/files/SanDiegoCoastWebLayout041509.pdf. Line not seen yet; R-G8: the reserve sits inside Tijuana Slough NWR (different agency).
- CA US-7375 Cowell Ranch: Coastside State Parks interactive map https://www.coastsidestateparks.org/map/ (a partner map, not the agency's).
- CA US-6448 Hearst Memorial Beach: parks.ca.gov page 589 has no map link. US-11336 Rainbow Basin: BLM page links only the BLM maps hub (https://www.blm.gov/maps), no park map. US-12616 Black Butte Lake: USACE page 403 (blocked to the bot). US-2638 Van Sickle: NV State Parks page opened, no map link.
- WV: state portals found (RESEARCH ORDER step 1): WV GIS & Mapping https://wvdnr.gov/gis-mapping/ , Hunt/Fish map https://www.mapwv.gov/huntfish/ , WMA map & list https://wvdnr.gov/lands-waters/wildlife-management-areas/ , stream access points. None names the hatcheries or Forks of the Coal yet. Cedar Lakes maps page has only picture links (no boundary seen).
- TN: ALL 7 tn.gov / tnstateparks pages return 403 to the bot (blocked). Needs a different route (TN open data portal, or Brandon opening one).


### Layer facts read Oct 29 ~5:15 PM (chat 8, grade A: layer metadata opened)
| st | layer | what it is |
|---|---|---|
| AK | arcgis.dnr.alaska.gov OpenData/Recreational_ParkBoundary MapServer/2 "ASP Park Boundary" | Alaska DNR Parks' own polygons (NAME, PARKNAME, ACREAGE, PRKTYPABRV); "land available for public recreation", compiled from statutes + state land ownership; may differ from the outer statutory boundary (that is the R-G6 official-map-detail case). Max 1000 records. |
| NY | gisservices.dec.ny.gov reference/MapServer/2 "DEC Lands" | lands in DEC's care: WMAs, Unique Areas, State Forests, Forest Preserve (UNIT, FACILITY, CATEGORY, CLASS, ACRES, MANAGE_BY). |
| CT | Connecticut_DEEP_Property FeatureServer/0 (services1.arcgis.com/FjPcSmEFuDYlIdKC) | land DEEP owns in fee (parks, forests, wildlife areas, water access sites); excludes easements; CC0; updated Aug 19 2026; GeoJSON/shapefile downloads at geodata.ct.gov. |
| ME | gis.maine.gov dep ... MapServer/5 "Maine Conservation Lands" | parcels with PARCEL_NAME, DESIGNATION (State Park, State WMA, ...), ECO_RESERVE flag, HOLD1_NAME (holder), RPT_AC. |
Point-in-polygon look-ups filed at the park pins: 8-rg7-pk-ak (8 parks), -ny (3), -ct (4), -me (2).
| US-11944 | Dankworth Pond SP | AZ State Parks park map PDF (DAPO_Park Map_8-2023) | G-ID3 (Brandon 3:57 PM) | picture map only: link kept, PIN (no line traced from a picture); a GIS / parcel layer would allow a line | 2 | Oct 29 |
| US-3390 | River Island SP | AZ State Parks park map PDF (Park Map-RIIS) | G-ID3 (Brandon 3:57 PM) | picture map only: link kept, PIN (no line traced from a picture); a GIS / parcel layer would allow a line | 2 | Oct 29 |
| US-9652 | Grenada SWA | CPW GranadaDeadmanSWA_geo.pdf | G-ID3 (Brandon 3:57 PM) | picture map only: link kept, PIN (no line traced from a picture); a GIS / parcel layer would allow a line | 2 | Oct 29 |
| US-7769 | Heaters Island WMA | the map found in the row above | G-ID3 (Brandon 3:57 PM) | picture map only: link kept, PIN (no line traced from a picture); a GIS / parcel layer would allow a line | 2 | Oct 29 |
| US-2685 | Winslow SP | the map found in the row above | G-ID3 (Brandon 3:57 PM) | picture map only: link kept, PIN (no line traced from a picture); a GIS / parcel layer would allow a line | 2 | Oct 29 |
| US-8103 | Cayuga Lake WMA | the map found in the row above | G-ID3 (Brandon 3:57 PM) | picture map only: link kept, PIN (no line traced from a picture); a GIS / parcel layer would allow a line | 2 | Oct 29 |
### Oct 29 4:05 PM chat 3 update (look-up G: Tennessee open data)
- TN state GIS servers (tdeconline.tn.gov, tnmap.tn.gov) are closed to the bot (403 / services directory off). The ArcGIS Online search worked.
- Official TDEC items found (owner TDEC Bureau of Conservation): 'Tennessee State Park Boundaries (Public View)' (polygons: US-13364 Cherokee Trail of Tears SP may be named in it, step 2) and 'TN State Natural Area Points' (POINTS only, no polygons: Grundy Forest, Harry Lee Carter, Hawkins Cove, Vine Cedar Glade stay pins unless a polygon layer turns up). Others: 'TN State Parks Boundaries' / 'TDEC - State Park Boundaries (mobile/web)' (author a TDEC staffer's account), 'Tennessee State and Federal Lands_WFL1' (a third-party layer, not official).
- No hit for the two TWRA state fishing lakes (US-12775, US-13514): no boundary layer found; stay pins (step 4b parcel later).
- NEXT (chat 2 / the key bot): read 'Tennessee State Park Boundaries (Public View)' for names matching the 8 TN parks (step 2). I could not open the layer's URL from here.


### Point-in-polygon ANSWERS at the park pins, Oct 29 ~5:30 PM (chat 8, grade A: bot answers 8-rg7-pk-ak/ct/ny/me)
| st | park | official polygon at the pin | Rule G step | result |
|---|---|---|---|---|
| AK | US-10464 Chena Wayside SRS | "Chena River State Recreation Site" 27.4 ac, ASP Park Boundary layer (POTA's own link is the Chena River SRS page "chenariversrs.htm") | 2 (agency's own record, same site) | MATCH: trace this polygon (chat 11 yes/no) |
| AK | US-11846 Bing's Landing, US-12709 Funny River, US-12710 Izaak Walton, US-12711 Morgan's Landing campgrounds | only "Kenai River Special Management Area" 50,234 ac (a bigger area, different name) | R-G7 case: step 2 no named piece -> step 3 DPOR campground/site maps (Alaska State Parks Kenai unit pages) -> 4b | NOT the SMA outline; bot/map hunt for each campground map |
| AK | US-11834 Susitna Landing, US-11835 Little Susitna, US-13462 Sportsman's Angler Access | no DPOR polygon (these are Alaska Dept of Fish and Game sites) | 2 none | step 3 ADF&G access site pages; else pin |
| CT | US-7529 Beckley Iron Furnace SP | "Industrial Monument Historic Preserve" 2.86 ac (DEEP Property; POTA's page is "Beckley Furnace Industrial Monument") | 2 | MATCH by identity: trace (chat 11 yes/no) |
| CT | US-6875 The Preserve | "Preserve State Forest" 888.8 ac, DEEP-owned (State Forest) | 2 | STRONG CANDIDATE: name "Preserve" + POTA's page is a DEEP page; so it is DEEP land, my earlier 'land trust, take-back' note is wrong. chat 11 checks size/name |
| CT | US-7542 Satan's Kingdom SRA | "Farmington River Water Access (New Hartford)" 12.3 ac, DEEP-owned | 2 | CANDIDATE: Satan's Kingdom is the New Hartford Farmington River access; chat 11 checks (name differs) |
| CT | US-6860 Ferry Landing SP | "Marine District Headquarters" 16.2 ac (DEEP) | 2 | NOT a match by name; Ferry Landing SP sits beside the DEEP marine HQ at Old Lyme: needs a second look (name search in DEEP Property: bot) |
| NY | US-2081 Iona Island, US-8103 Cayuga Lake, US-2151 Thompsons Lake | DEC Lands layer 2: nothing at the pins | 2 | retry on the WMA layer (8-rg7-pk-ny2); Thompsons Lake is OPRHP (parks), not DEC |
| ME | US-9174 Mahoosuc, US-8287 Capitol | layer URL answered 404 "service not found" | 2 | retry on the other Maine host (8-rg7-pk-me2); Capitol Park parcel (Augusta tax map 32 lot 24) stands |
### Oct 29 4:20 PM chat 3: LOOK-UP E SEEN (the PDF pictures; I looked at each one)
| park | what the picture shows | Rule G result |
|---|---|---|
| MT US-11216 Big Springs Trout Hatchery | MT FWP map 'Big Springs Trout Hatchery' draws a red hatched 'Site Boundary' (6 small pieces along the creek) | R-G7 step 4a, official line, from https://fwp.mt.gov/binaries/content/assets/fwp/gisresources/visitmaps/htc/39753636.pdf: TO TRACE (chat 2); chat 11 yes/no |
| MT US-11219 Jocko River Trout Hatchery | FWP map 'Jocko River Trout Hatchery' (spelled Jocko) draws a 'Site Boundary' (one polygon, Flathead Reservation) | step 4a, official line, .../htc/39753949.pdf: TO TRACE; chat 11 yes/no (name spelling Jacko vs Jocko = same place) |
| MT US-12827 Brownes Lake SFWA | the FWP map is 'Browns Bridge Fishing Access Site' with a boundary: a DIFFERENT NAME than POTA's 'Brownes Lake' | NOT used. Grey area for Brandon (G-MT1): is Brownes Lake SFWA the same land as Brownes Bridge FAS? Pin until ruled |
| MT US-12925 Thoreau State Beach | the FWP page id we had (39753904) is 'Thibodeau' FAS, not Thoreau: wrong site | NOT used. Needs the FWP page for Thoreau (not found); pin |
| IL US-13298 North Point Marina SRA | a marina drawing (no boundary line, no scale) | NOT a boundary map; pin. Step 4b (IDNR-owned land inside Illinois Beach SP) |
| IL US-12640 Rauchfuss Hill SRA | IDNR 'Rauchfuss Hill - Dixson Springs State Recreation Area' hunter map: blue 'IDNR Property' line drawn (2 blocks + a strip by Marina Dr) | step 4a, official line, from our docs: TO TRACE (chat 2); chat 11 checks the strip by Marina Dr (Golconda Marina belongs to a different park) |
| IL US-4118 Copperhead Hollow SFWA | IDNR hunter map with a clear blue 'IDNR Boundary' line (one shape, ~0.45 mi scale) | step 4a, official line, from our docs: TO TRACE |
| MA US-8422 Pope John Paul II Park | DCR Neponset River Greenway map: the park drawn as a green 'DCR owned or managed' shape (legend says 'not authoritative') | step 4b: ownership shape, grade APPROXIMATE; chat 2 to cut it; chat 11 yes/no |
| IL US-10788 Ray Norbut | web app opens on a satellite picture with no outline | still no boundary; pin |
NEW RULING NEEDED (G-MT1): see the line above (Brownes Lake vs Brownes Bridge). Also a naming note: POTA 'Jacko' vs FWP 'Jocko' is one place (spelling).
### Oct 29 4:35 PM chat 3: GREY AREAS G-MT1 + G-MT2 RESEARCHED (Montana names that differ)
EVIDENCE for US-12827 'Brownes Lake SFWA': (1) POTA's own official link for the park (our parkinfo) is the FWP page https://myfwp.mt.gov/fishMT/fas/39753504 = 'Brownes Bridge Fishing Access Site'. (2) POTA's pin 45.5467, -112.692 equals that page's own map point (45.54671, -112.6923) to 4 decimals. (3) The key finds the pin INSIDE the 10-acre Brownes Bridge record. (4) A separate real 'Brown's Lake FAS' exists (FWP id 39754193, a different place near Ovando); so 'Brownes Lake' in POTA's name is POTA's own mix-up/old name, not a second park. (5) FWP's map PDF draws the site boundary (seen).
EVIDENCE for US-12925 'Thoreau State Beach': POTA's link is FWP page .../fas/39753904 = 'Thibodeau Fishing Access Site'; POTA pin 46.9525, -113.612 equals the page's own point (46.95252, -113.61191) to 4 decimals; FWP's map draws the Thibodeau boundary (seen).
LEAN (R0 'match POTA', R-G7 step 2 'ID or named by the agency record'): YES for both, POTA points to that exact agency page and place. Outline = the agency's boundary, grade Official, label with the agency's name ('FWP: Brownes Bridge FAS' / 'FWP: Thibodeau FAS'), park keeps POTA's name. Ask: Brandon rules (or HQ under R-G7 step 9).
| US-11835 | Little Susitna Public Use Facility State | potamap lead (its PAD-US copy holds the pin): 'Susitna Flats State Game Refuge' owner SDNR / manager SDNR | R-G2 / R-G8 | R-G2/R-G8: a different place with a shared word: NO | 2 | Oct 29 |
| US-11155 | White Rock Mountain State Recreation Are | potamap lead (its PAD-US copy holds the pin): 'Black Mountain National Game Refuge' owner DESG / manager USFS | R-G2 / R-G8 | R-G2/R-G8: a different place with a shared word: NO | 2 | Oct 29 |
| US-3578 | Tijuana Estuary Reserve State Conservati | potamap lead (its PAD-US copy holds the pin): 'Tijuana Slough National Wildlife Refuge' owner FWS / manager FWS | R-G2 / R-G8 | R-G2: national refuge vs state reserve: NO | 2 | Oct 29 |
| US-6448 | William Randolph Hearst Memorial State B | potamap lead (its PAD-US copy holds the pin): 'Hearst San Simeon State Park' owner SPR / manager SPR | R-G2 / R-G8 | R-G8: a bigger, different park (Hearst San Simeon SP): NO | 2 | Oct 29 |
| US-10540 | Bellevue-Watson State Fish Hatchery | potamap lead (its PAD-US copy holds the pin): 'Watson Lake SFU' owner SFW / manager SFW | R-G2 / R-G8 | R-G2/R-G8: a different place with a shared word: NO | 2 | Oct 29 |
| US-10687 | Trussum Pond State Fishing Lake | potamap lead (its PAD-US copy holds the pin): 'Trap Pond State Park' owner SPR / manager UNK | R-G2 / R-G8 | R-G2/R-G8: a different place with a shared word: NO | 2 | Oct 29 |
| US-8329 | Choctawhatchee & Holmes Creek State Cons | potamap lead (its PAD-US copy holds the pin): 'Choctawhatchee River Water Management Area' owner RWD / manager RWD | R-G2 / R-G8 | R-G2/R-G8: a different place with a shared word: NO | 2 | Oct 29 |
| US-7812 | Copper Basin Airstrip State Recreation A | potamap lead (its PAD-US copy holds the pin): 'Copper Basin Patrol Cabin' owner USFS / manager SFW | R-G2 / R-G8 | R-G2/R-G8: a different place with a shared word: NO | 2 | Oct 29 |
| US-12827 | Brownes Lake State Fish and Wildlife Are | potamap lead (its PAD-US copy holds the pin): 'Brownes Bridge Fishing Access Site' owner UNK / manager SFW | R-G2 / R-G8 | R-G2/R-G8: a different place with a shared word: NO | 2 | Oct 29 |
| US-6848 | President James K. Polk State Historic S | potamap lead (its PAD-US copy holds the pin): 'Polk Memorial State Historic Site' owner OTHS / manager OTHS | R-G2 / R-G8 | R-G2 name + kind agree (state historic site): CANDIDATE | 2 | Oct 29 |
| US-13409 | Belmont Nevada State Historical Monument | potamap lead (its PAD-US copy holds the pin): 'Belmont Courthouse State Historical Site' owner SPR / manager SPR | R-G2 / R-G8 | R-G2 name agrees, same kind (state historic site/monument): CANDIDATE | 2 | Oct 29 |
| US-2081 | Iona Island Wildlife Management Area | potamap lead (its PAD-US copy holds the pin): 'Iona Island State Park' owner SPR / manager SPR | R-G2 / R-G8 | R-G8: another kind of place (state PARK vs WMA): CHECK | 2 | Oct 29 |
| US-8103 | Cayuga Lake Wildlife Management Area | potamap lead (its PAD-US copy holds the pin): 'Cayuga-Seneca Canal' owner OTHS / manager OTHS | R-G2 / R-G8 | R-G2/R-G8: a different place with a shared word: NO | 2 | Oct 29 |
| US-5572 | Olympic Peninsula State Forest | potamap lead (its PAD-US copy holds the pin): 'Olympic National Forest' owner USFS / manager USFS | R-G2 / R-G8 | R-G2: national forest vs state forest: NO | 2 | Oct 29 |
| US-1458 | Kohler-Andrae State Park | potamap lead (its PAD-US copy holds the pin): 'John Michael Kohler State Park' owner SDNR / manager SDNR | R-G2 / R-G8 | a PIECE of Kohler-Andrae (Kohler + Terry Andrae parks): CANDIDATE | 2 | Oct 29 |
| US-4776 | Escanaba River State Forest | potamap lead (its PAD-US copy holds the pin): 'Escanaba State Forest Area' owner SDNR / manager SDNR | R-G2 / R-G8 | R-G2 name agrees (state forest area): CANDIDATE | 2 | Oct 29 |
| US-10575 | Walnut Woods State Conservation Area | potamap lead (its PAD-US copy holds the pin): 'Walnut Woods Conservation Area' owner OTHS / manager OTHS | R-G2 / R-G8 | R-G2 name agrees; owner City of Liberty (R-G7 4b ties): CANDIDATE | 2 | Oct 29 |
| US-10511 | Jessups Mill Pond State Game Land | potamap lead (its PAD-US copy holds the pin): 'Suggs Mill Pond Game Land' owner SFW / manager SFW | R-G2 / R-G8 | R-G2/R-G8: a different place with a shared word: NO | 2 | Oct 29 |

### UPDATES from chat 11 (Oct 29 ~5:30 PM) — yes/no on the rows that name me; name + owner + size reasoning, I did not open the agency maps
| ref | answer | why |
|---|---|---|
| AK US-10464 Chena Wayside SRS | YES | POTA's own link is the Chena River SRS page; the layer record is that park (27 ac) |
| CT US-7529 Beckley Iron Furnace | YES | same site (Beckley Furnace Industrial Monument), DEEP owned |
| CT US-6875 The Preserve | NOT SURE | name 'Preserve' alone; a DEEP page is not proof it is this park's land |
| CT US-7542 Satan's Kingdom SRA | YES | the New Hartford Farmington River access is the recreation area |
| MT US-11216 Big Springs, US-11219 Jocko River hatcheries | YES | FWP's own site-boundary line, exact names |
| IL US-12640 Rauchfuss Hill SRA | YES | IDNR's own property line, exact name |
| MA US-8422 Pope John Paul II Park | YES, Approximate | DCR shape says 'not authoritative' (R-G7 step 7 grade) |
| potamap leads: US-6848 Polk, US-13409 Belmont, US-10575 Walnut Woods | YES | name variants of the same state site |
| US-1458 Kohler-Andrae | YES as a piece | the Kohler half only |
| US-4776 Escanaba River SF | NOT SURE | 'State Forest Area' is a management area |
| US-2081 Iona Island | NO | WMA vs state park are different designations |
Key-pieces file (KPC-Data data/waiting/questions/key-pieces.json): of 307 questions 204 YES, 27 NO, 76 NOT SURE (list in chat 2's inbox); the NOT SURE ones are Fable-bound only if no agency layer or map answers them.
