# World harvester: leads graded (chat 8 desk, Oct 28 2026)
Read: KPC-Data data/harvest/leads-AU/GB/DE/PL/JP.json, leads.md, state.json (logs), countries.json (seeds) and the script .github/scripts/kpc_world_harvest.py. My grade: **A** = official park / protected-area boundaries, usable as an outline source; **B** = official and related, but a designation, a line, points, water-only or one layer buried in a big service; **C** = not park data, or not official. Bot bands in brackets.

## Totals
| Country | Leads | Bot A/B/C | Mine (graded) | Verdict |
|---|---|---|---|---|
| AU | 47 (run paused after step 1 of 6) | 38 / 9 / 0 | 10 graded: A 3, B 1, C 6 | bot over-grades about 8 of 10 |
| GB | 6 | 3 / 3 / 0 | 6 graded: A 0, B 2, C 4 | 2 of 6 worth a look |
| DE | 2 | 2 / 0 / 0 | 2 graded: A 0, B 2 | right data, wrong publisher |
| PL | 13 | 0 / 0 / 13 | 10 graded: C 10 | bot is right, but all noise |
| JP | 0 | none | | nothing found; causes below |

## AU (10 of 47)
| Lead | Bot | Mine | Why |
|---|---|---|---|
| SLIP_Public_Services/Environment (WA) | A | **A** | Layers include Forest Blocks (DBCA-025), conservation reserves; the DBCA parks layers sit in this service (only 4 layers shown in leads: list all) |
| Public/PWSPublic (Tasmania Parks & Wildlife) | A | **A** | 'Management Plan - Kent Group National Park', 'Maria Island National Park'...: park-by-park polygons from the park agency |
| Public/OpenDataWFS (Tasmania LIST) | A | **A** | Contains 'LIST Local Government Reserves'; our known-good layer 26 lives here |
| Public/CadastreAndAdministrativeV2 (Tasmania) | A | B | Informal Reserve, Non Production Forest, Forest Management Units: forestry land, not parks |
| Public/Indexes | A | C | 'Towns Atlas Page Index', 'National Park Map Index' = map sheet grids |
| Public/ABS_2016 | A | C | Census statistical areas |
| AerialPhotoViewer/Orthophoto_Coverage_Area | A | C | Aerial photo footprints |
| Landgate_Public_Maps/Map_of_Bush_Fire_Prone_Areas_3 | A | C | Fire-prone land, property boundaries, LGAs |
| SLIP_Public_Services/People_and_Society | A | C | Aboriginal communities, heritage areas, town reserves |
| SLIP_Public_Services/Plants_and_Animals | A | C | WWF conservation targets, roadside conservation capture status |
Also seen: DPIRD Fisheries Guide 'Closed Waters / Marine Reserves' = B (water-only list). Whole AU list: my read is about 4 or 5 real park services of 47 (about 10%), not 38.
**Known-good missed (3): all time, not bugs.** The AU run stopped after step 1 of 6 ('orgs'); the QLD server gisext.qfes.qld.gov.au (Protected_areas), the Victorian WFS opendata.maps.vic.gov.au and the services-ap1 'Protected_areas' layer are in steps 2 and 3, which never ran. (WA layer 15 and Tasmania layer 26 were found.)

## GB (all 6)
| Lead | Bot | Mine | Why |
|---|---|---|---|
| SSSI_UK_Merged | A | B | Official, Open Government Licence, 2023: a good polygon source but SSSI is a designation, not a park (grey area for Brandon) |
| National_Trails_England | B | B | Official, OGL, 2026-10-13: lines (trails), a known-good |
| CRoW_Act_2000_Access_Layer | B | C | Open-access (right-to-roam) land: not public land (W-3) |
| CRoW Section 4 Registered Common Land | A | C | Common land, same rule |
| PM10_daily_mean_Local_Authority_2020 | A | C | Air-quality data |
| Nitrogen_Dioxide_annual_mean | B | C | Air-quality points |
**Known-good missed:** GoBe Consultants' Core_Data_Non_WMS **layer 50**. Two causes: the harvester reads only the first 40 layers of a service (MAX_LAYERS = 40, so layer 50 is never opened), and the org is a consultancy, not a government (`official()` drops it). Also lost: three AGOL searches and one org read died with 'Unterminated string' (truncated JSON, not retried), and data.gov.uk's catalogue returned HTTP 400 four times.

## DE (both)
FFH and Vogelschutzgebiete (bot A, A) = Natura 2000 habitat and bird areas, published by WWF Germany, not the state; licence text garbled. Mine: **B** each (right content, wrong publisher; take BfN's own service instead). **Known-good missed:** geodienste.bfn.de/ogc/wfs/ returned HTTP 404 (the base address; the WFS lives under /ogc/wfs/<service>, my fetch of a guessed sub-address was blocked, so BOT LOOK-UP). govdata.de's catalogue was refused by robots.txt four times. WWF got through `official()` although it is not a government (check that rule).

## PL (10 of 13)
All 10 graded **C**, same as the bot: the dane.gov.pl catalogue returned statistics and funding datasets (religion decisions, census tables, PKOB building classification, 'Narodowa' = national minorities, Park centralny forms, DGA protected-data lists for three parks, a priority programme for biodiversity). Not GIS. **Known-good missed (3):** (1) powietrze.gios.gov.pl root returned 404 (the service FormyOchronyPrzyrody exists: I opened it, so a direct visit works; the root path is wrong); (2) wfs.bdl.lasy.gov.pl and (3) ogcapi.bdl.lasy.gov.pl both gave '0 feature types': the capabilities regex wants `<FeatureType>` with no attributes and cannot read an OGC API at all. Also the BDL data is ownership / forest, not protected areas. The right Polish layer is the GIOS 'Formy ochrony przyrody' MapServer.

## JP (empty)
Not a block. The seed had no official orgs, no servers, no WFS (all empty), only the e-gov catalogue, which answered HTTP 400 to all four Japanese keywords (query format; the same 400 hit data.gov.uk). ArcGIS Online search found 9 to 29 hits per keyword but read 0, because none of the hosts pass the official test (.go.jp, or a government word in the publisher). Japan's real sources (MLIT national land numerical information A10, Ministry of the Environment) are file downloads, not map services, so a service crawler cannot see them. My OFFICIAL_MAPS/WORLD/JP_desk.md has the MLIT A10 page as a BOT LOOK-UP.

## TOP 3 FIXES FOR THE HARVESTER
1. **Test the seeded known-goods first, directly.** Walk every `known_good` URL (service URL → walk_service; WFS → capabilities; a root that 404s → try the service itself) before any crawl. Lift MAX_LAYERS for services named Environment / Protected / Boundaries / Reserve, or list layer names first and probe only park-named layers. This one change would have found GB layer 50, PL gios, AU services, DE BfN.
2. **Fix the grading.** A 'named area polygons' layer must not earn the outline point and band A (it gave A to census areas, aerial photo footprints, fire-prone land, air-quality polygons). Require a park word (park, reserve, protected, national, nature, conservation, NNR...) in the layer or service name for band A; generic area/boundary layers cap at C. Non-government publishers (WWF, consultancies) must stay at B/C with a note, not A, and not be dropped when the content is official (GoBe).
3. **Fix the readers.** WFS: parse `<FeatureType ...>` with attributes (and send version=2.0.0), and read OGC API `/collections`. Catalogues: find why data.gov.uk and e-gov.go.jp return HTTP 400 (path or parameters), keep only datasets whose resources are shp / gml / WFS / ArcGIS / GeoJSON (that removes all 13 Polish noise rows), swap govdata.de (robots refusal) for the GDI-DE geodata catalogue gdk.gdi-de.org, and retry a truncated JSON response once.
Also: AU paused at step 1: give each country enough time per run (or run steps in the order servers, wfs, orgs) so the known-goods are read first. For JP, add a 'download' lead type fed by hand from the survey (MLIT A10, Environment Ministry).
