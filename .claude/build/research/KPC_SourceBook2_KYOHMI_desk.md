# SOURCE BOOK 2, batch 1: KENTUCKY, OHIO, MICHIGAN (chat 8 desk, Oct 28 2026)
Grades: A = I opened it or it is in our own files; B = found in a search result (title/URL only, not opened); "none found" = searched, nothing. Order used: state open-data portal, then the agency site, then web search. This session cannot open most agency sites (allowlist), so B rows need a GitHub-bot open before anyone builds on them. Already answered in our files: parking/ramps (data/access-layers.json: OH 4 rows, MI 5 rows, KY 0 rows, KY uses ky-access-extra.json + kpc-ky-data.json), MI closures page (data/closure-pages.json), KY hunting seasons (data/ky-hunting.json), the park outlines (data/state-gis.json).

## KENTUCKY
1. **Hunt closures / quota-draw dates:** KDFWR (fw.ky.gov) per-area pages + quota hunt table (script-built page, read with a headless browser by closures round 4); our data/ky-hunting.json already holds seasons + WMA-specific closures (A). Format: per-area web page + statewide table. No official open file found.
2. **Park closures / alerts:** parks.ky.gov/park-closures (B), plus /severe-weather, /flood-impacts, /improvements (B): state parks. Federal in KY: NPS pages per park (e.g. nps.gov/cuga/planyourvisit/closures.htm, B); DBNF/LBL via the Forest Service alerts pages (not read this pass). Format: web pages; no feed seen.
3. **Own-land layers:** state parks = ky-state-parks.geojson, WMAs = ky-hunting-areas.geojson (A, ours); KDFWR WMA owners = data/ky-wma-owners(-hand).json (A). Open-data portal (opengisdata.ky.gov) search surfaced no state park / WMA parcel layer (none found). Private inholdings: not shown in our WMA layer; owners file is the cross-check.
4. **Hydrography with both banks:** no statewide Kentucky water-area layer found on the portal. Leads: Kentucky Geological Survey hydrography page (uky.edu/KGS/gis/hydro.htm, B); Census TIGER area hydrography per county (catalog.data.gov, B: water polygons with both banks, coarse); county layers (Jefferson Co water bodies, Boone/NKY WaterbodyPoly, B). Fallback = USGS NHD (already used).
5. **Campground points:** hand list kpc-campgrounds.json (65, club) + RIDB (38) in data/campinfo (A). State-park campgrounds: no open point layer found; parks.ky.gov pages (B).
6. **Access / parking / ramps:** ky-access-extra.json + ky-wma-parking.json (A); no state layer found.
7. **Trails:** ky-sheltowee.geojson, ky-trail-parks.json (A, ours). No state open file found.
8. **Hours + fees pattern:** parks.ky.gov park pages (B); data/hours already built by the hours bot (A).

## OHIO
1. **Hunt closures / dates:** ODNR Wildlife per-area hunting map PDFs on dam.assets.ohio.gov (e.g. lakealmahuntingmap.pdf, jesseowenshuntingmap.pdf, Hueston Woods map, B) + the statewide "Ohio Hunting and Trapping Regulations" PDF (B). Closures usually announced by news release (Magee Marsh road closure, WTOL/outdoorhub, B). No per-area closure table found. Format: PDF + news.
2. **Park closures / alerts:** ODNR news releases (seasonal closure of horseback/APV trails in state forests, B); state park alert page not surfaced (none found in this pass): leave to the closures bot.
3. **Own-land layers:** `ODNR_ODNR_Lands_Public_nolakes` FeatureServer 5 parks / 6 forests / 7 wildlife (A, ours, LAKES CUT OUT); other ODNR services to try for lakes: ODNR_ODNR_Lands_External3, ODNR_Lands_Dissolved, Ohio_Conservation_Lands (B; chat 9's test found External and Dissolved also miss Mosquito Lake: so lakes must come from the park's own lake layer or the USGS water map). Private inholdings: layer is ODNR-owned parcels only (C).
4. **Hydrography:** none found statewide with water areas from the state (OGRIP search returned only county layers and an FEMA SOP); ODNR "Ohio_Dams" (B); Census TIGER county area hydrography (B). Fallback USGS NHD.
5. **Campground points:** ODNR_POI MapServer and POI_Verify (POI_Forestry), Ohio_POI (B): point-of-interest layers that include campgrounds; need a bot open + test.
6. **Access / parking / ramps:** data/access-layers.json OH rows 34, 35, 36, 110 (A).
7. **Trails:** ODNR trails layers (Esri Ohio trails write-up, B); not in trails-layers.json: add via the trails bot.
8. **Hours + fees:** ohiodnr.gov park pages (B); hours bot.

## MICHIGAN
1. **Hunt closures / dates:** MI DNR newsroom closures page (A: data/closure-pages.json) + SGA special-regulations PDF (michigan.gov/documents/dnr/sga_special_regulations_..., B) + per-area SGA map PDFs (dnr.state.mi.us/PUBLICATIONS/PDFS/HuntingWildlifeHabitat/SGA/*.pdf, B) + press releases for controlled hunts that close parks (Hoffmaster SP closes Nov 20-23 for the deer hunt, GovDelivery bulletin, B). Format: web + PDFs + bulletins. Pointe Mouillee/Shiawassee also post FWS "Upcoming Closures" (fws.gov/carp/refuge/shiawassee, B).
2. **Park closures / alerts:** michigan.gov/dnr/about/newsroom/closures (A).
3. **Own-land layers:** DNRManagementBoundariesOPENDATA FeatureServer 8 (parks), DNRWILDLandsOPENDATA FeatureServer 2 (wildlife) (A, ours; chat 9's test: the parks layer KEEPS Lake Michigan water). Private inholdings: DNR-managed units only; ownership vs "managed" can differ (C).
4. **Hydrography:** Michigan Geographic Framework (gisagocss.state.mi.us ... michigan_geographic_framework MapServer, B), "River Polygons MGF" metadata (mcgi.state.mi.us, B), Hydrography_Polygons v17a (MTU portal, B), "Lake Polygons [Michigan]" (BTAA catalog, B), EGLE "Great Lakes Shorelines 2024" (gisagoegle.state.mi.us AUID2024OpenData MapServer/1, B). MI is the one state with state water-AREA polygons incl. rivers: best candidate for a "both banks" backup.
5. **Campground points:** dnrParksAndRecreation FeatureServer (layers incl. boating access, A in access-layers); DNRReferenceAssetsOPENDATA/6 (parking, trail access) (A). A campground-specific layer: not found (campgrounds are in "Recreation Base Features" DNRRecreationBaseFeatures_ReadOnly, A in access-layers: type detail needs a check).
6. **Access / parking / ramps:** access-layers.json MI rows 15, 16, 105, 106, 161 (A).
7. **Trails:** DNR "state trails" open data (not read this pass); trails bot owns it.
8. **Hours + fees:** michigan.gov/dnr park pages (B).

## HAND-OFF LINES
- chat 10 (closures, campgrounds, hours, access, trails): KY closures = parks.ky.gov/park-closures + NPS per-park closure pages; OH = ODNR news + per-area hunting map PDFs; MI = DNR newsroom closures + SGA special regulations PDF + GovDelivery bulletins; OH campgrounds = ODNR_POI layers; MI campgrounds = DNRRecreationBaseFeatures TypeDetail.
- chat 2 (own-land, hydrography): OH lake parks need a lake source (all three ODNR land layers miss Mosquito Lake): use the USGS water area or the MI-style approach; MI has real water-area polygons (MGF / Hydrography_Polygons v17a / EGLE shorelines): test them as the "both banks" backup; KY: no state water-area layer found, KGS page + TIGER county area hydrography are the leads.
