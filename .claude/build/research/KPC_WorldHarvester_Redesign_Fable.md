# WORLD HARVESTER → WORLD LAYER FINDER: redesign note for Opus
**Fable, Oct 29 2026 9:50 PM CDT. Brandon 9:40 PM: "make same notes for Opus to improve it too, get layers for other places than US and Canada … seed material: 8, or program it in: your call." My call: PROGRAM the finding in; chat 8 seeds only what the program still leaves empty. Scope rule: rest of world = accurate boundaries + official documents/maps only (no 2-fers). Rule G applies (official sources only, Rule G research order, nothing decided by a bot).**

## 0. What is wrong with it today (why 21 of 42 countries have 0 leads)
- It is **catalog-driven**: it types a few park words into a national catalog and hopes. Catalogs are the worst-indexed place for GIS; half answer 400 or hold only downloads. It knows nothing about the PARKS it is working for.
- It measures **leads**, not **parks covered**. A country can be "done" with 0 usable layers.
- Seeds are hand-written per country (chat 8's desk file). That does not scale to 150 countries.
- Nothing stops it from re-walking a country that is already 90% covered (FR 13,102 of 14,367 matched) while RU (7,933 POTA parks, no world key at all), CN, KR, NZ, TH, BR, CO, MX, TR, CL, AR, ZA have never been read.

## 1. Rename and re-aim: kpc_world_finder.py, driven by POTA's own parks
- **Input = the gap per country**, not a country list: `data/pota/index.json` (parks per country) minus `KPC-Links data/world-key/<CC>.json` matched. Order = biggest gap first: RU, GB (3,800 open), AU (3,300), CN, KR, NZ, TH, JP (1,000), SI (1,000), BR, ES (700), RO (1,000), DE (600), CO, MX, BE, TR … FR last (97% done).
- **Pins + names per country** from the POTA tiles `data/pota/t/` (the same pins the world key uses). Group parks by the **agency words in their names** (P-4: "Parc national", "Réserve naturelle", "Nationalpark", "Naturschutzgebiet", "National Park", "Conservation Park", "Site of Special Scientific Interest"…): each group = one agency to find, not one park.
- Keep every manners rule (robots.txt; the ArcGIS REST exemption; 2 s per host; a day's rest after 3 strikes) and the no-geometry storage rule.

## 2. Step A = polygons we already have, pins first (same as the GIS hunter)
For a country with any layer in `data/world-gis-sources.json` / `data/harvest/leads-<CC>.json` (band A/B, probed OK): one multipoint query per layer per 120 open pins → hits judged exactly as the GIS hunter does (name match / name mismatch / inside-other), written to `data/waiting/questions/gis-hunter.json` (same file, `area: CC`) for chat 11. Only parks with NO hit go on to the finding steps. (Share the code: import `step_a`, `inside`, `acres`, `words` from kpc_gis_hunter.py; add the country's language stop-words to STOP.)

## 3. Step B = PROGRAMMED finders, in Rule G order, per agency group (this is the "seed material" built in)
Stop at the first finder that yields a layer whose polygons sit under ≥ 3 of the group's pins (or ≥ 1 for a group of 1-2).
1. **INSPIRE discovery (every EU/EEA country + UK, ~32 countries, one pattern):** each has a national CSW catalogue; query `GetRecords` for theme **Protected Sites (PS)** + the agency words; take records with a WFS / WMS / OGC API endpoint. Catalogue addresses: the INSPIRE geoportal's list of national discovery services (one fetch, cached in `data/harvest/inspire-csw.json`). Also the **EEA CDDA** per-country lead (already in) and **Natura 2000** (EEA service) as the fallback national-level layers.
2. **National geoportal conventions** (programmed as a table, not per-country prose): ArcGIS Hub `/api/v3/datasets?q=` on `hub.arcgis.com` filtered to the country's government domains (`.gov.xx`, `.gouv.fr`, `.gob.xx`, `.go.jp`, `.go.kr`, `.govt.nz`, `.gov.au` + state domains, `.gc.ca`); CKAN `package_search` (plain `q`, %20 spaces: the NL lesson) on the known national CKANs (data.gov.au, data.gov.uk, dados.gov.br, datos.gob.es/mx/cl/ar/co, data.go.kr, data.go.jp, data.govt.nz, data.gov.ru), keeping only rows whose resources are WFS / ArcGIS / OGC API / GeoJSON.
3. **ArcGIS Online org search by agency name in the local language** (`sharing/rest/search?q=<agency words> type:"Feature Service"`), publisher must read as government (the existing `official()` test + govwords); then `walk_service` as today.
4. **OGC API / WFS capabilities** on any endpoint found (today's `ogc_collections` / `wfs_capabilities`), picking collections whose title carries a park word; probe once (`probe_layer`).
5. **The agency's own page** that POTA links for a park of the group (parkinfo-web for the world is thin: read the POTA page's "official link" field): headless browser, collect embedded map-service URLs (the look-up bot's `page` kind). A page is a lead, never a boundary.
6. **Nothing** → the group is tagged `no-layer: <finders tried>` and goes on chat 8's short seed list (section 5).
Every layer found → probe → `data/intake/queue.json` (`from: 'world-finder'`, `closes: [refs in the group]`) → the intake's READY rules → chat 9 approval → `world-gis-sources.json` by chat 2/9 → the world key. The finder itself never writes a source file or a key.

## 4. Output and the measure that matters
- `data/harvest/leads-<CC>.json` keeps its shape (the intake reads it) but gains `parks_open`, `parks_hit_known_layers`, `groups: [{words, refs, finder_hit, layer}]`.
- COUNT line per country: `open N / hit on known layers H / groups G: found F (layers L queued), no-layer Z` + `'grade me'` for chat 11. The weekly `last_run.json` row shows parks covered before → after, so "done" means parks, not leads.
- WORK LOG rows (same table as the US/Canada Fable files) into `data/gis-hunter/worklog-<CC>.md` for the Canada-style Fable list HQ will want for the world later.

## 5. Chat 8's part (small, after the first programmed pass)
Only the groups the finders tag `no-layer` reach chat 8, as ONE list per country ("RU: federal zapovedniks + national parks: no catalogue answered; ZA: SANParks + provincial reserves"), with the finders tried. Chat 8 looks for the agency's own map server (Rule G research order) and writes the address into `KPC_HarvesterSeeds_desk.md` as today; the finder reads the seed book first on its next pass (known-good bypass stays). Until Opus's first run, chat 8 keeps only the 8 never-seeded countries from my 8:20 PM list; the 13 "0 leads" countries wait for the programmed finders.

## 6. Order of work for Opus
1. Build Step A + the gap-ordered queue (one day): run GB, AU, DE, RO, JP, SI first: known layers exist, so chat 11 gets candidates immediately. 2. INSPIRE CSW + Hub/CKAN conventions (finder 1-2). 3. AGOL + OGC/WFS (3-4, mostly today's code). 4. Page reader (5) last. Test one EU country with a known CSW (AT or DK) and one non-EU (NZ: data.govt.nz + LINZ) before chaining. Chat 11 grades like the GIS hunter (random 10 candidates 9+ right on the agency's own map; no 'no-layer' with empty `tried`).

## 7. Grey areas for Brandon (numbered; not guessed)
- **W-1** May the finder READ the UNEP-WCMC / Protected Planet (WDPA) record of a park to learn the MANAGING AGENCY's name, then search that agency's own servers? (WDPA is not official and its shapes are never used; only the agency name would be read.) Default until ruled: NO (official sources only).
- **W-2** Natura 2000 / CDDA (EEA, EU-level official compilations of national data): acceptable as a park's outline when the national agency publishes no layer of its own? Default until ruled: candidate for chat 11 with the label "EU compilation of national data", never Official grade.

## 8. Today's harvester
No run is in progress (the 24-country refill finished). Do not start another; the redesign replaces it. Its code (`get`, `official`, `probe_layer`, `walk_service`, `wfs_capabilities`, `ogc_collections`, `agol_search`, `catalog`, the seed-book reader) is reused inside the finder, so nothing is thrown away.
