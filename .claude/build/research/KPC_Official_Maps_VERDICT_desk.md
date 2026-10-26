# VERDICT (Research desk, chat 8, Oct 26 11:20 AM): official park maps, 300 busiest US parks

Files checked: `KPC_Official_Maps_done.xlsx` (A) + `KPC_Round12_park_maps_done.xlsx` (B). Chat 2 had already merged both into `data/parkinfo-web.json` (~11:20 AM); the fixes below are for chat 2 to apply there. The desk edited no data file.

## Bottom line
- **Safe to keep:** the 76 rows where both files give the same link, and rows from clean official domains (nps.gov, fs.usda.gov, fws.gov, state park / DNR / wildlife agencies). every sampled row from those groups that could be opened was real and about the right park.
- **Fix or relabel: 12 rows** (list below). Most are a non-official site or a guessed or old file name.
- **NOT SURE: 9 rows.** The link could not be confirmed from here; chat 2's link-status check should decide.

## How it was checked (and the limit)
- All 600 rows: domain, blanks, hedge words, reused pages, status vs link.
- 30 rows by hand, picked from each group (same link / different links / one file only / odd domains). The session could not open most pages directly (allowlist), so each row was confirmed through search results plus opening the park's own official page or the file itself when it was surfaced. "Opened" below = the desk read the page or PDF; "seen" = the exact URL showed up in search results only.
- So this is a sample (30 of 600), not a full link test. Let chat 2's bot check every URL for a live page (HTTP 200) before the site shows them.

## Recount (a row counts as having a map only if DONE and a real http link)
Both found + same link 76 · both found, different links 132 · only A 59 · only B 15 · neither 18 (HQ's earlier 144 / 67 / 3 / 10 counted NOT FOUND rows that hold a park page; chat 2 already noted this). A has 20 NOT FOUND rows with a park page in the map column: skip them, they are not maps.

## FIX (12)
| Ref | Park | Problem | Better official link |
|---|---|---|---|
| US-8313 | Mountains to Sea State Trail | `mountainstoseatrail.org` looks like the trail's support-group site, not the agency | NC state trails PDF page `https://trails.nc.gov/maps/map-pdfs-mountains-sea-state-trail/open` (seen) |
| US-4423 | Spring Creek Forest Preserve | `springcreekforest.org` is a 501(c)(3) (opened: its own page says so); the city of Garland is listed as the partner | Dallas County open-spaces page `https://www.dallascounty.org/departments/plandev/openspaces/locations/04-spring-creek-forest.php` and trail map `https://www.dallascounty.org/Assets/uploads/docs/plandev/trails/25-SpringCreekGarland.pdf` (seen) |
| US-6281 | Loxahatchee River WSR | `fws.gov/rivers/map` is the national Wild and Scenic map, not this river (B said so itself) | Make it `agency_map`, not `map` |
| US-9681 | Camden Expedition Scenic Highway State Trail | `camdenexpedition.org` is not an agency site (B flagged it; A called it "Official"). Search found no agency source | NOT SURE: label non-official or drop `map` until checked |
| US-6927 | Nantahala State Game Land | `ncpaws.org` could not be tied to NCWRC | NCWRC's own `https://www.ncwildlife.gov/hunting/where-hunt-shoot/game-lands-maps/mountain-game-land-maps` (seen) |
| US-6532 | Erie Canalway NHC | `eriecanalway.org` = the heritage area's managing group (NPS's own page lists it under "Managed by"; opened). Not an agency, and the link is a news and publications page | Label 'managing group's site'; NPS page `https://www.nps.gov/places/erie-canalway-national-heritage-corridor.htm` has no map |
| US-3094 | Utah Lake State Park | `utahlake-digital-brochure-2026.pdf` is NOT on the park's publications page (opened: it lists Overview Map, Area Map, Lakeshore Campground Map); A also said NOT FOUND. Looks guessed | `https://stateparks.utah.gov/parks/utah-lake/publications/` as 'map page' |
| US-0637 | Mills Park Natural Area | link cut short: the page's boundary-map link ends `?sfvrsn=56454d3a_2`, ours ends `56454d3` (opened) | Use the full link from `https://www.arkansasheritage.com/arkansas-natural-heritage/naturalareas/find-a-natural-area/mills-park-natural-area` |
| US-3383 | Bald Mountain SRA | page link carries `?rev=…&hash=…`, ours has none (opened) | Copy the full link from `https://www.michigan.gov/recsearch/parks/BaldMtn` (may still work bare: NOT SURE) |
| US-1942 | Cleveland Lakefront State Park | old-style `/assets/media/…` path; the current file is at `clevelandmetroparks.com/getmedia/3496c101-b5d3-44f1-b19c-7ddff3907e44/Lakefront-Reservation-Map.pdf` (seen) | use that, or the Metroparks lakefront page |
| US-0225 | Rocky Flats NWR | A's path `fws.gov/sites/default/files/documents/Rocky Flats Trail Map.pdf` was not found; the file that opened is under `fws.gov/rivers/sites/default/files/documents/…` (Aug 2018 FWS brochure with trail map). A newer one exists: `https://fws.gov/sites/default/files/documents/2024-06/rocky-flats-nwr-brochure-web.pdf` (seen) | use the 2024 brochure |
| US-1312 | Pocahontas State Park | link is real and official (opened: the park page links it) but it is the CAMPGROUND map ("Map of all campsites") | trail guide `https://www.dcr.virginia.gov/state-parks/document/data/trail-guide-pocahontas.pdf` (listed on the park page); keep the campground map as `map_page` |

Also: **US-1055 Catalina** is a 2024 map; newer ones exist (`…/storage/20260807073250cata_parkmap_2026.pdf`, seen). Prefer the park's map page `azstateparks.com/catalina/explore/maps` (already stored as `map_page`).

## NOT SURE (9), nothing proven wrong
US-4011 Chalco Hills (file name '09-12' suggests an older 2012 map; a 2024 interactive map was announced on papionrd.org) · US-3627 Van Fleet State Trail (the floridadep.gov PDF is not linked from the park page; the page has a 'Download Park Map' link whose address could not be read; B was blocked) · US-9557 Jasper SRA (old index.cfm address) · US-3473 Martial Cottle (csparks.maps.arcgis.com) · US-13184 Iron Belle Trail (experience.arcgis.com; DNR's statewide PDF `https://www2.dnr.state.mi.us/publications/pdfs/ForestsLandWater/Iron_Belle_Trail_Maps/0IronBelleTrailStatewide.pdf` was seen) · US-0189 Don Edwards NWR (`/visit-us` and `/map` pages) · US-6462 Garret Mountain (county PDF; domain is Passaic County's) · US-3873 Colonial Dorchester (widencdn host, SC PRT path) · US-0225's B link `fws.gov/refuge/rocky-flats/map`.

## CONFIRMED
Beech Fork (WV State Parks PDF, opened) · Burr Oak Woods ('Area Map' on MDC's page, opened) · Moraine Hills (IL DNR page links the scene7 image, opened) · Upper Mississippi NWR (`/map` is in the refuge's own menu, opened) · Mills Park page + boundary map (opened) · Wharton Brook official CT DEEP PDF (opened; dated Jan 2011; chat 2 already uses it as `map`) · Fort Snelling, Alum Creek, Castlewood Canyon, Acadia (exact URL seen) · Pocahontas (exists).

## Patterns
- Hedging: only one real case (US-3617 'published approximately 2014', in the date cell). B has none. ('May' hits were the month.)
- Reused general pages (agency level only): A 5 (in.gov/dnr/state-parks/maps ×3, fs.usda.gov/ivm ×4, fs.usda.gov/r03/maps-guides ×3, ncwildlife game-lands-maps ×4, MN sra00304.pdf ×2); B 6. Chat 2 already stores these as `agency_map`; keep it that way. One more: the MN sra00304.pdf is used for two parks, check it is not park-specific.
- Both files followed 'official only' except the 6 domains above. No wrong status values.

## Lead for chat 2 (not tested)
Arkansas natural-area boundaries have an official layer: `gis.arkansas.gov/arcgis/rest/services/FEATURESERVICES/Boundaries/FeatureServer/21` (NHC_NATURAL_AREAS), seen in search while checking Mills Park. Check it against state-gis.json.
