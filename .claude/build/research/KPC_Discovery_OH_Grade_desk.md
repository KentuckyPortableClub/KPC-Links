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

---

# REGRADE after the tune (chat 2, Opus, Oct 27 ~9:30 PM CDT)
Run: KPC-Data `kpc-discovery.yml` 40616431293 (OH, steps A-D, 37 min), leads.json/leads.md of 2026-10-28.
**I am grading my own chat's bot, so this is a self-check, not chat 8's verdict: chat 8 should confirm it in the morning.**
Graded the same way as above: the list's own top 10 rows, by what each layer holds.

## Result: FAIL again, 0 of 10 agree (needs 7) — but for the opposite reason
The tune fixed what it was asked to fix; the GRADE is now the broken part. Everything the server walk classified lands at
grade 5 = band A (124 A's of 154 leads), so the band again tells nothing apart, and the top of the list is filled by the
server walk's first alphabetical hits instead of the best finds.

| # | Row (as the bot ranks it) | Bot | Mine | Why |
|---|---|---|---|---|
| 1 | Earthquakes_EB — "Closed seismic stations" | A 5 | **C** | seismic network. 'Closed' in a layer name is not a park closure. |
| 2-3 | Commercial_Fishing_Closed_Zones_June15_Sept15 (listed TWICE) | A 5 | **C** | Lake Erie commercial netting zones. Not park access, and one service shown twice (MapServer + FeatureServer). |
| 4-5 | Commercial_Fishing_Closed_Zones_May15_Oct15 (twice) | A 5 | **C** | same. |
| 6-7 | Commercial_Fishing_Permanently_Closed_Zone (twice) | A 5 | **C** | same. |
| 8 | DOW_LakeHPRestrictions | A 5 | **C** | horsepower limits per lake: boating rules, not water bodies or access. |
| 9 | DOW_Lakes_Bathymetry | A 5 | **C** | lake depth. We use NHD for water. |
| 10 | DOW_Services/Parking_Areas_view (FeatureServer) | A 5 | **not a lead** | we ALREADY read it: `access-layers.json` holds `…/DOW_Services/Parking_Areas_view/MapServer/29`. The already-read test compares the exact service URL, so the FeatureServer form of the same service reads as new. |

## What the tune DID fix (the reason the run is still worth keeping)
- **The server walk works.** 18 folders, 164 services on gis.ohiodnr.gov read layer by layer, 66 leads; the image server (74 services) correctly gave none.
- **Parks_DNAP_Trails: FOUND by itself** (both MapServer and FeatureServer), graded A, gap 'trail line' — chat 8's #1 miss is now the bot's own find.
- **Trailheads: half.** Of chat 8's 7 hand finds the walk found 4 by itself (Parks_DNAP_Trails, Wildlife_Trails_Verify, Roads_ParkingAreas, POI_Verify). Missed 3, each for a readable reason:
  - `Watercraft_Paddling_Query`: skipped as 'no layer a gap needs'. Its only layer is named **"Stream Access (All Fields)"**; the access word list wants 'access site/point/area', and the SERVICE name (Paddling) is never read. Fix: test the service name too, and let bare 'access' in a layer name count for a point layer.
  - `Trails_WayPoints_POI` and `ODNR_Trail_Heads_View`: the walk never saw them on that server (they are not among the 164 service names it listed; the AGOL copies of both were found earlier by the catalog search). Fix: walk at depth 2 (sub-folders) and keep the AGOL copy when the agency server has none.
- **Theme layers are gone from the top:** no bluff, shoreline, watershed or county rows anywhere in the A band (they are the 16 C's).
- **The PDF host step works:** 102 wildlife areas tried by URL pattern, **77 maps found** (e.g. `…/wildlife-area-maps/mageemarsh.pdf`). I could not open one from this session (the proxy answers 403 for that host), so chat 8 should spot-check three before we trust the 77.
- **The warning fired:** "20 agency pages opened, 0 map links kept" — the browser step still sees nothing on ODNR's park pages, now loudly. The PDF pattern is doing that job instead.
- **'What ran' table** is in leads.md (per keyword and per server walk: hits, new, already read, not agency, not this state, theme).

## The three fixes this regrade asks for (grade only; nothing about what counts)
1. **Stop the band inflation.** The 'new to us, holds records' bonus fires for every walked layer, so grade 5 is the floor. Make it worth +1 only when the gap is one we are actually short of in that state (no trail lines, no access points, no closures feed), and cap the walk's own grade at 4 unless a layer names parks we lack. A band should mean something again.
2. **One row per service.** Key leads by service path without the MapServer/FeatureServer ending (the dedupe already in the known-good matcher), and compare already-read the same way — that removes the six duplicate rows AND the Parking_Areas false 'new'.
3. **Tighten 'closures'.** Require a park/recreation word in the service or layer name (park, trail, area, campground, refuge, forest, preserve, access) before a 'closed/closure/status' layer counts; otherwise it is a theme layer.

With those three, the list's top would be the trail lines, trailheads, waypoints and the 77 map PDFs rather than fishing zones.
I have NOT made these changes: they are grade rules, and after two self-graded reruns tonight the next change should be reviewed
before it runs again (RULES FIRST). Suggest: HQ reads this, chat 8 confirms the 0-of-10 and spot-checks three PDFs, then one more
Ohio run tomorrow.

