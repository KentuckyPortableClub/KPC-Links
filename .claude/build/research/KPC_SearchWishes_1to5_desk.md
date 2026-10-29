# What I would search for, and what I found (chat 8 desk, Oct 28 10:50 PM CDT; for future reference, Brandon thinking on it)
Grades: B = a search result (title/URL only, not opened); C = my knowledge, not checked. Nothing here is built or run.

## 1. Open the agency pages I cannot (fws.gov, nps.gov, state sites)
- **NPS has a free DATA API** (developer key): nps.gov/subjects/developer/get-started.htm and nps.gov/subjects/developer/guides.htm (B). It serves parks, alerts (closures), campgrounds, visitor centers and "things to do" as JSON, so a bot with a free key reads NPS facts without scraping pages. Best single fix for NPS rows. Needs a key stored as a GitHub secret (Brandon does it, never in chat).
- **FWS boundaries:** "FWS National Realty Approved Acquisition Boundaries" (catalog.data.gov, B) and the service services.arcgis.com/QVENGdaPbd4LUkLV/ArcGIS/rest/services/FWSApproved_Authoritative/FeatureServer (B): the refuge's approved outline, to be read beside the Real Estate Interest layer (the fee tracts).
- **Everything else:** a generic "open this URL, write back OK / dead / blocked + the page title and date" bot (chat 9's probe is the closest; it needs a list input and a result file). I would batch all my B-grade source rows into one run.

## 2. Satellite picture of an overlap (the drawing check)
- ArcGIS REST servers answer an `export` call that returns a PNG for any bounding box (the standard "Export Map" operation; many servers listed it in the search, B). Esri's World Imagery service uses the same call (C: the exact service path must be tested; imagery is credited to Esri on the picture). A bot can take one overlap's box, fetch the imagery, draw the park outlines + the gold overlap line on it (Pillow/matplotlib), and save a small PNG per overlap into the repo. Then I (or anyone) open the PNG and answer HQ's two questions (official map placed right? gold on both borders?). Cost: one run, ~2 images per area, free.

## 3. Each state's own water-AREA layer (both banks of a river)
- **Indiana:** gisdata.in.gov NHD_Local_Resolution FeatureServer/1, NHD_Local_Resolution_RO FeatureServer/1, Legacy NHD Lakes and Rivers 2008 (B); IN "Waterbodies GIS Layer" on hub.mph.in.gov (B).
- **Tennessee:** tnmap.tn.gov/ArcGIS/rest/services/ENVIRONMENTAL/HYDRO_FEATURES/MapServer/1 "WATERBODIES" (B).
- **West Virginia:** gis.transportation.wv.gov/arcgis/rest/services/Hydrology/FeatureServer/3 (B).
- **Illinois:** only a Department of Energy "Water_Bodies_IL" layer surfaced (arcgis.netl.doe.gov, B): not the state; look again at the Illinois state GIS clearinghouse.
- **Virginia:** only county layers (Prince William, Leesburg, B); no statewide water-area layer found.
- **Michigan:** already found (Michigan Geographic Framework, Hydrography_Polygons v17a, EGLE shorelines): KPC_SourceBook2_KYOHMI_desk.md.
- Pattern: these are mostly state copies of the national NHD. Test each for ONE thing: does it have a polygon layer for river areas (NHDArea) as well as lakes? That decides whether it fixes the water-edge gap.

## 4. All tracts of a nature preserve / natural area (the Green River Natural Area problem)
- The state's preserve pages follow one pattern: `eec.ky.gov/Nature-Preserves/Locations/Pages/<Name>.aspx` (Rush Island Bottoms, Glenview came up, B). The Green River Natural Area page itself did not surface in my search.
- **Kentucky Office of Nature Preserves Biennial Report** (apps.legislature.ky.gov committee document, Nov 5 2026, B) and its newsletters (eec.ky.gov Natky29.pdf, B) usually list tracts and acres per preserve; the Western Kentucky University Green River project summary (wku.edu/greenriver ... wkugrp_summary_jan2014.pdf, B) may name the tracts. Open these first for the Boiling Springs / Timberlake question.
- Rule I would add for the detective: when a preserve has several tracts, list every tract row with acres and say which one the pin is in.

## 5. Where POTA says a park is (its own park pages / API)
- Found only community use of `api.pota.app` (Ian Renton's POTA scripts, HAMRS forum threads on wrong grid squares, a POTA MCP tool "pota_nearby_parks", B). Nothing official that documents boundary notes: POTA's park record carries entity, grid, lat/lon, website. So this is LOW value for 2-fer boundaries; it is useful for pin checks (HAMRS threads show wrong grid squares are a known issue).

## Order I would do them in (best value first)
1. The satellite picture bot (item 2): it unlocks the drawing and river-corridor checks HQ asked for.
2. The NPS Data API key (item 1): one free key fixes most NPS rows.
3. The link-opener list (item 1): all my B rows in one run.
4. The state water-area test (item 3): ONE run that asks each layer "is there a river-area polygon?".
5. The nature-preserve tracts (item 4): three document opens.
6. POTA pages (item 5): last.
