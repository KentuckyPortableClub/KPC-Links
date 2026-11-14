# Round-3 rows left out

Verified 2026-11-06. Only confirmed URL rows and sourced abbreviation or example rows were stored.
Rows marked blocked, broken, unverified, or from_memory were not added. No email was sent.

## Agencies

A whole agency row is left out when its row status is not confirmed. Confirmed slots on those rows were not written, so a blocked row cannot fill one URL while another slot failed.

- blocked | AZ | Arizona Game & Fish Department | home blocked (HTTP 403) https://www.azgfd.com/; finder blocked (HTTP 403) https://www.azgfd.com/location-type/where-to-watch-wildlife/; gis empty
- blocked | CO | Colorado State Land Board | home confirmed (already in PR48 (same URL); not re-fetched) https://slb.colorado.gov/; finder blocked (HTTP 403) https://slb.colorado.gov/maps; gis blocked (HTTP 403) https://slb.colorado.gov/maps/arcgis
- blocked | FL | Florida State Parks | home confirmed (already in PR48 (same URL); not re-fetched) https://floridastateparks.org/; finder blocked (HTTP 403) https://www.floridastateparks.org/statewide-map; gis confirmed (HTTP 200) https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/PARKS_BOUNDARIES/MapServer
- unverified | ID | Idaho Fish & Game | home confirmed (already in PR48 (same URL); not re-fetched) https://idfg.idaho.gov/; finder unverified (HTTP 503) https://idfg.idaho.gov/wma; gis unverified (HTTP 503) https://idfg.idaho.gov/data/gis
- unverified | IN | Indiana DNR (state parks, fish & wildlife areas) | home confirmed (already in PR48 (same URL); not re-fetched) https://in.gov/; finder confirmed (HTTP 200) https://in.gov/dnr/fish-and-wildlife/properties; gis unverified (HTTP 500) https://www.in.gov/gis/geoinsights/indianamap
- blocked | LA | Louisiana State Parks | home confirmed (already in PR48 (same URL); not re-fetched) https://lastateparks.com/; finder blocked (HTTP 403) https://www.lastateparks.com/find-a-state-park-or-preserve; gis empty
- blocked | LA | Louisiana Department of Wildlife & Fisheries | home confirmed (already in PR48 (same URL); not re-fetched) https://wlf.louisiana.gov/; finder blocked (HTTP 403) https://www.wlf.louisiana.gov/page/wmas-refuges-and-conservation-areas; gis confirmed (already in PR48 (same URL); not re-fetched) https://www.wlf.louisiana.gov/page/wma-gis-data-download
- blocked | ME | Maine Bureau of Parks & Lands | home blocked (HTTP 403) https://www.maine.gov/dacf/parks/; finder blocked (HTTP 403) https://www.maine.gov/DACF/parks/about/state_parks.shtml; gis confirmed (already in PR48 (same URL); not re-fetched) https://www.maine.gov/geolib/
- blocked | ME | Maine Inland Fisheries & Wildlife | home blocked (HTTP 403) https://www.maine.gov/ifw/; finder blocked (HTTP 403) https://www.maine.gov/ifw/fish-wildlife/wildlife/lands/wildlife-management-areas/; gis confirmed (already in PR48 (same URL); not re-fetched) https://maine.hub.arcgis.com/datasets/1adcd31a16134741b014f39a9d04d8f6_0/about
- blocked | MA | Massachusetts DCR (state parks, forests) | home confirmed (already in PR48 (same URL); not re-fetched) https://mass.gov/; finder blocked (HTTP 403) https://www.mass.gov/get-involved-with-dcr/locations?page=5; gis confirmed (already in PR48 (same URL); not re-fetched) https://www.mass.gov/info-details/massgis-frequently-asked-questions
- blocked | MA | MassWildlife | home confirmed (already in PR48 (same URL); not re-fetched) https://mass.gov/; finder blocked (HTTP 403) https://www.mass.gov/info-details/welcome-to-masswildlife-lands; gis confirmed (already in PR48 (same URL); not re-fetched) https://www.mass.gov/orgs/massgis-bureau-of-geographic-information
- blocked | MI | Michigan DNR (state parks, game areas, forests) | home blocked (HTTP 403) https://www.michigan.gov/dnr; finder blocked (HTTP 403) https://www.michigan.gov/dnr/places-to-go/state-forests; gis confirmed (already in PR48 (same URL); not re-fetched) https://gis-midnr.opendata.arcgis.com
- blocked | NE | Nebraska Game & Parks Commission | home confirmed (already in PR48 (same URL); not re-fetched) https://outdoornebraska.gov/; finder blocked (HTTP 403) https://outdoornebraska.gov/conservation/land-management/wildlife-management-areas; gis confirmed (already in PR48 (same URL); not re-fetched) https://data-outdoornebraska.opendata.arcgis.com/
- blocked | NH | New Hampshire Fish & Game | home confirmed (already in PR48 (same URL); not re-fetched) https://wildlife.nh.gov/; finder blocked (HTTP 403) https://wildlife.nh.gov/wildlife-and-habitat/wildlife-management-areas; gis empty
- broken | NJ | New Jersey State Park Service (DEP) | home confirmed (already in PR48 (same URL); not re-fetched) https://nj.gov/; finder broken (HTTP 404) https://www.nj.gov/dep/parksandforests/parks/maps; gis broken (HTTP 404) https://nj.gov/dep/gis/hottopics.html
- broken | NJ | New Jersey Fish & Wildlife (DEP) | home confirmed (already in PR48 (same URL); not re-fetched) https://dep.nj.gov/; finder confirmed (HTTP 200) https://www.nj.gov/dep/fgw/news/2022/wmas.htm; gis broken (HTTP 404) https://nj.gov/dep/gis/hottopics.html
- blocked | NY | New York State DEC (WMAs, state forests) | home confirmed (already in PR48 (same URL); not re-fetched) https://dec.ny.gov/; finder blocked (robots_disallow) https://dec.ny.gov/places-to-go/wildlife-management-areas; gis confirmed (HTTP 200) https://gis.ny.gov/
- blocked | TN | Tennessee Wildlife Resources Agency | home confirmed (already in PR48 (same URL); not re-fetched) https://tn.gov/; finder blocked (HTTP 403) https://www.tn.gov/twra/wildlife-management-areas; gis blocked (HTTP 403) https://www.tn.gov/twra/gis-maps/
- blocked | TN | Tennessee Division of Forestry / Natural Areas | home confirmed (already in PR48 (same URL); not re-fetched) https://tn.gov/; finder blocked (HTTP 403) https://www.tn.gov/content/tn/environment/program-areas/na-natural-areas/list-of-natural-areas.html; gis empty
- blocked | UT | Utah Trust Lands Administration | home confirmed (already in PR48 (same URL); not re-fetched) https://trustlands.utah.gov/; finder blocked (HTTP 403) https://trustlands.utah.gov/tools/maps/maps-gallery/; gis confirmed (HTTP 200) https://at.trustlands.utah.gov/tools/maps
- blocked | WI | Wisconsin DNR (state parks, wildlife areas, forests) | home confirmed (already in PR48 (same URL); not re-fetched) https://dnr.wisconsin.gov/; finder blocked (HTTP 403) https://dnr.wisconsin.gov/topic/parks/findapark_classic; gis confirmed (HTTP 200) https://dnr.wisconsin.gov/maps/GetGISData
- unverified | AB | Alberta Environment and Protected Areas | home confirmed (already in PR48 (same URL); not re-fetched) https://alberta.ca/; finder unverified (HTTP 200 but robots_unknown) https://alberta.ca/wildlife-management-units; gis confirmed (already in PR48 (same URL); not re-fetched) https://geospatial.alberta.ca/
- blocked | NU | Government of Nunavut Environment | home blocked (HTTP 403) https://www.gov.nu.ca/en/department-environment; finder empty; gis blocked (HTTP 403) https://www.gov.nu.ca/en/department-environment/geospatial-information-and-land-tenure
- unverified | QC | Sépaq (parcs nationaux du Québec) | home confirmed (already in PR48 (same URL); not re-fetched) https://sepaq.com/; finder confirmed (already in PR48 (same URL); not re-fetched) https://www.sepaq.com/pq/; gis unverified (HTTP 200 but robots_unknown) https://www.donneesquebec.ca/recherche/dataset/aires-protegees-au-quebec
- unverified | QC | Québec Environnement (réserves fauniques, aires protégées) | home confirmed (already in PR48 (same URL); not re-fetched) https://quebec.ca/; finder confirmed (HTTP 200) https://www.environnement.gouv.qc.ca/BIODIVERSITE/aires_protegees/index.htm; gis unverified (HTTP 200 but robots_unknown) https://www.donneesquebec.ca/recherche/dataset/aires-protegees-au-quebec
- blocked | YT | Yukon Parks | home confirmed (already in PR48 (same URL); not re-fetched) https://yukon.ca/; finder blocked (HTTP 403) https://yukon.ca/en/outdoor-recreation-and-wildlife/parks-and-protected-areas/yukon-territorial-parks-and-other; gis confirmed (HTTP 200) https://open.yukon.ca/data/park-and-protected-areas-1m
- blocked | YT | Yukon Environment (habitat protection areas) | home confirmed (already in PR48 (same URL); not re-fetched) https://yukon.ca/; finder blocked (HTTP 403) https://yukon.ca/en/outdoor-recreation-and-wildlife/parks-and-protected-areas/yukon-territorial-parks-and-other; gis confirmed (HTTP 200) https://open.yukon.ca/data/park-and-protected-areas-1m

27 agency rows left out. 70 confirmed URLs were filled on rows that stayed confirmed. Existing agency rows were kept.

## Official park pages

- broken | US-0990 | Donnelley/DePue State Park | HTTP 404 | https://dnr.illinois.gov/parks/park.donnelleydepue.html
- blocked | US-8393 | Stodder's Neck & Abigail Adams State Park | HTTP 403 | https://www.mass.gov/locations/stodders-neck-abigail-adams-park
- blocked | US-7656 | Ralph and Martha Perry Memorial State Wildlife Area | robots_disallow | https://mdc.mo.gov/discover-nature/places/ralph-martha-perry-memorial-conservation-area
- broken | US-9457 | Della Gates & Edward Charles Bott State Wildlife Area | HTTP 404 | https://ohiodnr.gov/go-and-do/plan-a-visit/find-a-property/della-gates-edward-charles-bott-wildlife-area

## Abbreviations

Sourced rows were added. from_memory rows and the sourced row whose spot check was blocked were not.

- from_memory | US-KY | SNP | not network-checked
- from_memory | US-KY | SNA | not network-checked
- from_memory | US-KY | NAP | not network-checked
- from_memory | US-KY | SRP | not network-checked
- from_memory | US-KY | SP | not network-checked
- from_memory | US-KY | SHS | not network-checked
- from_memory | US-KY | SF | not network-checked
- from_memory | US-KY | NHP | not network-checked
- from_memory | US-KY | NRRA | not network-checked
- from_memory | US-KY | NRA | not network-checked
- from_memory | US-KY | Ft. | not network-checked
- from_memory | US-DC | NPS reservation | not network-checked
- from_memory | US-DC | C&O Canal NHP | not network-checked
- from_memory | US-DC | Mt. | not network-checked
- from_memory | US-DC | Ft. | not network-checked
- from_memory | US-DC | St. | not network-checked
- from_memory | US-DC | Nat'l / Natl | not network-checked
- from_memory | US-DC | NCP-East | not network-checked
- from_memory | US-CT | SP | not network-checked
- from_memory | US-CT | SF | not network-checked
- from_memory | US-CT | WMA | not network-checked
- from_memory | US-CT | NAP | not network-checked
- from_memory | US-CT | Devil's / Devils | not network-checked
- from_memory | US-CT | People's / Peoples | not network-checked
- from_memory | US-CT | Mt. / Mount | not network-checked
- from_memory | US-CT | Fort | not network-checked
- from_memory | US-NE | SRA | not network-checked
- from_memory | US-NE | SHP | not network-checked
- from_memory | US-NE | SP | not network-checked
- from_memory | US-NE | WMA | not network-checked
- from_memory | US-NE | NRD | not network-checked
- from_memory | US-NE | Ft. | not network-checked
- from_memory | US-NE | Lewis & Clark | not network-checked
- blocked | US-LA | SP | HTTP 403
- from_memory | US-LA | State Commemorative Area | not network-checked
- from_memory | US-LA | WMA | not network-checked
- from_memory | US-LA | Jean Lafitte NHP&P | not network-checked
- from_memory | US-GA | PFA | not network-checked
- from_memory | US-GA | WMA | not network-checked
- from_memory | US-GA | SP | not network-checked
- from_memory | US-GA | SHS | not network-checked
- from_memory | US-GA | F.D. | not network-checked
- from_memory | US-GA | Stephen C. Foster | not network-checked
- from_memory | US-GA | HP | not network-checked
- from_memory | US-NC | SNA | not network-checked
- from_memory | US-NC | SRA | not network-checked
- from_memory | US-NC | SP | not network-checked
- from_memory | US-NC | GL / Game Land | not network-checked
- from_memory | US-NC | Mt. / Mount | not network-checked
- from_memory | US-NC | Weymouth Woods-Sandhills Nature Preserve | not network-checked
- from_memory | US-NC | NHP | not network-checked
- from_memory | US-SC | WMA | not network-checked
- from_memory | US-SC | SP | not network-checked
- from_memory | US-SC | Ft. / Fort | not network-checked
- from_memory | US-SC | St. | not network-checked
- from_memory | CA-BC | Mt. | not network-checked
- from_memory | CA-BC | Nlaka'pamux / Nlakapamux | not network-checked
- from_memory | CA-BC | Ts'yl-os | not network-checked
- from_memory | CA-BC | Say Nuth Khaw Yum | not network-checked
- from_memory | CA-NL | Provincial Park | not network-checked
- from_memory | CA-NL | Ecological Reserve | not network-checked
- from_memory | CA-NL | Cape St. Mary's / St. Mary's | not network-checked
- from_memory | CA-NL | Akami-Uapishku-KakKasuak-Mealy Mountains | not network-checked
- from_memory | CA-NL | Frenchman's Cove | not network-checked
- from_memory | CA-PE | Wildlife Management Area | not network-checked
- from_memory | CA-PE | Parc national de l'Île-du-Prince-Édouard | not network-checked
- from_memory | CA-PE | Skmaqn-Port-la-Joye-Fort Amherst | not network-checked
- from_memory | CA-SK | Provincial Park | not network-checked
- from_memory | CA-SK | Recreation Site | not network-checked
- from_memory | CA-SK | Interprovincial Park | not network-checked
- from_memory | CA-SK | Saint Victor | not network-checked
- from_memory | CA-SK | Fort Qu'Appelle / Qu'Appelle | not network-checked
- from_memory | CA-SK | Fort Carlton | not network-checked

## Joint ownership examples

Tests use sourced rows whose spot check was confirmed. These were not turned into fixtures.

- from_memory | US-KY | Cane Creek Wildlife Management Area (Daniel Boone National Forest) | search/memory only per return notes
- from_memory | CA-ON | Rouge National Urban Park | search/memory only per return notes
- services*.arcgis.com disallow | US-CA | Santa Monica Mountains National Recreation Area (tract layer) | not spot-checked this pass

## Nested tract examples

The Daniel Boone row was kept for Mill Creek only. Cane Creek and Redbird were named on that row from search results and were not used as confirmed children.

- services*.arcgis.com disallow | US-CA | Santa Monica Mountains National Recreation Area | TRACT (alias 'Tract No.'), TRACTS_ID, Park_Label, Specific_Label, Manager | services*.arcgis.com project disallow — not fetched
- unverified | US-NPS | NPS unit boundary (any unit) in the Land Resources Division 'nps_tracts' dataset | tract-level polygons (parcels; fee or other interest e.g. easement) | not spot-checked this pass
- from_memory | US-KY | West Kentucky Wildlife Management Area | 'A Tracts' (lettered tract groups) | search/memory only

## Sources not ingested

NY OPRHP on gisportaldev.dot.ny.gov stays on do_not_ingest. NCNHP and AU-WA stay matching-only and are not displayed. The Grant County NM parcel server was not used.

- US-OK | Protected Areas of Oklahoma (PAD-OK) AGOL FeatureServer | robots_disallow
- US-OK/KS/SC/NY | PAD-US 4.1 State Downloads (ScienceBase) | ScienceBase PAD-US;robots_disallow;notes_say_human
- US-FED | FWS National Realty Approved Acquisition Boundaries | robots_disallow
- US-FED | FWS National Realty Boundaries (NWRS) | robots_disallow
- US-NC | Game Lands 2003 (obsolete) | no URL to resolve; keep unknown
- IE | National Parks of Ireland (Generalised 50 m) | robots_disallow
- GB-NIR | ASSI (Irish Grid) | NI/DAERA zip disallow;robots_disallow;notes_say_human
- GB-NIR | National Nature Reserves (Irish Grid) | NI/DAERA zip disallow;robots_disallow;notes_say_human
- AU-WA | DBCA-011 Legislated Lands and Waters | SLIP login wall on shapefile (HTTP 403); matching-only per wa_dbca_licence.md
- NZ | Protected Areas (layer 53564) | LINZ export;robots_disallow;notes_say_human
- GB-WLS | National Parks (inspire-nrw:NRW_NATIONAL_PARK) | robots_disallow;notes_say_human

## Human-download list

A person downloads these. Bots do not. No user-agent trick is used. A robots 403 on services*.arcgis.com is a disallow.

Note, 2026-11-13 (KPC owner): for `apps.fs.usda.gov` and `gis.blm.gov` the robots reasoning above was wrong. A robots.txt that answers 403 or 404 serves no rules file, so it is not a Disallow (RFC 9309, section 2.3.1.3: a 4xx answer means no rule is stated). On 2026-11-13 `apps.fs.usda.gov/robots.txt` answered 403 ("You don't have permission") and `gis.blm.gov/robots.txt` answered 404. Neither host is on this list. Bots may read `gis.blm.gov`. Bots may read `apps.fs.usda.gov` slowly: at least 10 seconds between requests, one at a time, the club's User-Agent, Retry-After honoured, stop after a run of 403 / 429 answers. (The robots check in the code still counts any robots.txt 401 / 403 as a no, for every host; that was left as it is, so the master step still will not read `apps.fs.usda.gov` until the owner decides on that rule.) The one BLM Nevada service that needs a sign-in (`gis.blm.gov/nvarcgis/rest/services/BLM_Nevada_SNPLMA_Disposal_Boundary`) stays blocked as sign-in only. This note changes nothing for `services*.arcgis.com`, `ncnhde.natureserve.org` (its robots.txt disallows AI crawlers) or the Grant County NM server.

1. ScienceBase PAD-US 4.1 state downloads (US-OK, KS, SC, NY fallback). robots disallow.
2. LINZ Protected Areas export (NZ layer 53564). robots disallow /e/ and /*/download/.
3. NI / DAERA ASSI and National Nature Reserves zips. robots disallow *.zip, and NIEA asks for written permission before display.
4. FWS National Realty approved acquisition boundaries and NWRS boundaries (iris.fws.gov). robots disallow.
5. PAD-OK live AGOL FeatureServer. services*.arcgis.com disallow. Use the PAD-US human download instead.
6. Ireland NPWS "National Parks generalised 50 m". robots disallow. Per-park national-park zips are the preferred robots-ok copy.
7. Wales National Parks. /geoserver/ disallow. Use datamap.gov.wales/download/<id> by hand.
8. AU-WA DBCA-011 shapefile. SLIP login wall. Matching only (CC BY-NC). Do not display the polygons.
9. PEI provincial parks and natural areas. The GeoLinc WMA REST layer is separate and was added. Parks and natural areas still need a person or the unsent draft.
10. Kansas, South Carolina, and Oklahoma parks shapefiles. No open download was found.

Licence drafts for SC, KS, LA, NCNHP, GA, WA, IE, MB, NIEA, and PEI were not stored and were not sent.
