# Discovery Bot, Ohio test: hand grade (chat 8, Oct 27 ~9:15 PM)
Source: KPC-Data `data/discovery/leads.md` + `leads.json` (run 2026-10-28, OH). Rule sheet: Discovery plan §1 (rules 1-6), D-1..D-4. Research order applied: ODNR's own GIS server first, then the agency pages, then a web search to check what a layer holds. Grade B: I read the service names and the agency's pages, I did not run queries on the layers.

## Result: FAIL (4 of 10 agree; needs 7)
The bot gave all 10 the same band (B, grade 3). Mine:

| # | Layer (ODNR) | Bot | Mine | Why |
|---|---|---|---|---|
| 1 | Watercraft Paddling Draw | B | **B** | paddling launches / water trails; the app already reads Watercraft_Motorized_Query, so mostly overlap; check for water-trail lines |
| 2 | Bluff Classification | B | **C** | Lake Erie bluff geology/hazard. Not parks, access, trails or water. |
| 3 | Lake Erie Historic Shoreline | B | **C** | old shoreline history. |
| 4 | Lake Erie Watershed | B | **C** | watershed map. |
| 5 | Lake Erie Public Access | B | **B** | Coastal Management's public access sites. Official, but many sites are city/county parks (house rule: never): keep state/federal only. |
| 6 | ODNR Lakes | B | **B** | lake polygons for the water-only rule (we use NHD today); worth a look, not urgent. |
| 7 | County_Extended | B | **C** | county borders. |
| 8 | Boater and Stream Access | B | **B** | stream access points; boat ramps overlap what we read from DOW_Facilities, the stream sites are new. |
| 9 | Fish Access Permits | B | **C** | fishing-access permits on private land by agreement: not park land (ruling B-G2). |
| 10 | ODNR Trail Heads View | B | **A** | official trailheads (state parks, forests, preserves) = access pins; we read none for Ohio trails. |
Also outside the top 10: #11 Greene County Public Parks C (agrees), #12 FWS Coastal Barrier Resources "replaces" = **C** (coastal barrier zones, nothing it replaces), the Cuyahoga/Fayette/Summit county rows are C (agree).

## (1) What it should have found for Ohio and did not
Already read, so correctly NOT leads: the ODNR Lands layers (state parks, wildlife areas, forests, preserves), DOW parking, DOW facilities, boat ramps, Watercraft_Motorized_Query.
**Missed (all on gis.ohiodnr.gov, all official, none in our files):**
- `DSP_Services/Parks_DNAP_Trails` (state park + nature preserve trail LINES) = **A**: Ohio has no trail lines at all today.
- `OIT_Services/Trails_WayPoints_POI` and `POI_Verify` (trail waypoints, trailheads, points of interest) = A/B for access.
- `DOW_Services/Wildlife_Trails_Verify` (wildlife area trails) = B/A; `DOW_Services/Roads_ParkingAreas` (roads + parking in wildlife areas) = B; `DWC_Services/Watercraft_Paddling_Query` = B.
- **Map pages:** ODNR's wildlife area maps are PDFs at `dam.assets.ohio.gov/image/upload/ohiodnr.gov/documents/wildlife/wildlife-area-maps/<name>.pdf` (beavercreek, killdeerplains, paintcreek, caesarcreek ...). The Maps-tab step looked at 20 pages and kept **0** map links (sample: Clark Lake WA, Veto Lake FA, Great Council SP show `kept 0, map_like []`). The host is on its allow list, so the step is not seeing the link (button text? script-filled?). Open one page by hand and fix the pattern.
- Ownership: nothing new needed for Ohio (ODNR Lands + the USFS/PAD-US ownership cover it), so no ownership lead is correct.

## (2) What it keeps grabbing that it should not
1. **Themes that only name a place:** Lake Erie bluff/shoreline/watershed and county borders. They got the "roads/water" or "outline" gap because the gap comes from the SEARCH KEYWORD ("shoreline"), not from what the layer holds.
2. **Fish access permits** (private-land easements) and a **FWS coastal barrier** layer marked "replaces".
3. **County and metro-park layers** (Greene, Summit, Fayette, Cuyahoga, Midwest Mega Commerce Center, legislative districts): correctly C, but they take list space; the planning layers (legislative reps, runoff forecast, 2006 ortho) should be dropped at the filter, not graded.
4. **Everything is band B:** with `parks_named = 0` the best possible grade is 3, so every agency layer lands in B and the band cannot tell trailheads from bluffs.

## Top 3 fixes (for tomorrow's Fable session)
1. **Walk the agency's own ArcGIS Server folders, not just the catalog search.** `gis.ohiodnr.gov/arcgis/rest/services?f=json` lists DSP_Services, DOW_Services, OIT_Services; hosts already in state-gis.json should be walked folder by folder (the old parking explorer does this for parking only). That finds Parks_DNAP_Trails and the wildlife trails the keyword search missed.
2. **Grade by what the layer IS, not by the search keyword:** read the layer's name + field names + geometry; a layer whose name matches a theme word list (bluff, watershed, historic, county, district, ortho, runoff, parcel, permit) is "not a lead"; points named trailhead/parking/ramp = access A/B; lines named trail = trail A/B; a polygon with a park-name field = outline. And give the grade a "new vs already read" bonus, so the band is not capped at 3.
3. **Fix the Maps-tab step:** 20 ODNR pages, 0 map links kept, while the wildlife-area PDFs sit on the allowed host. Give it the known pattern (`.../wildlife/wildlife-area-maps/*.pdf`, park pages' "Maps" or "Area map" links) and make "kept 0 on 20 pages" a visible warning, not a quiet result.
Smaller: keywords found nothing for 34 of 40 words (ownership, outline, closures): list which words ran and what they returned; add `trail waypoints`, `trails verify`, `water trail`, `wildlife area map`.

Questions for Brandon: none new (D-1 yes and D-2 hold; county layers stay "second witness" only).
