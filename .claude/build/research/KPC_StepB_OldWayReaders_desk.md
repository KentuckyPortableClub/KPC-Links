# Step B hunt: who still reads moved data the OLD way (chat 8, Oct 27 ~7 PM; read only, nothing changed)
Method: grep of every .html/.js in KPC-Links, every script + workflow in KPC-Links and KPC-Data, KPC-App, PDFs. Grade A for "this line reads it"; I did not run the pages.
`KPC.dataUrl` does NOT patch fetch, so only code that calls it (or a wrapper that does) is safe.

## 1. PAGES that fetch a moved file directly (break the day it is deleted; the site copy is the only one they try)
| File | Lines | Reads |
|---|---|---|
| kpc-bounds.js | 152, 169, 210, 289, 290, 292, 311, 320, 323, 333, 370, 371, 384 | data/us-key/, ca-key/, canada-bounds/, world-key/, world-bounds/, wwff/, sota/t/ — **biggest one: every outline, Am I in the Park, Kit, planner** |
| kpc-us-planner.js | 30 (locations, northam, canada), 45-46 (pota/wwff/sota tiles), 148, 190, 201, 207, 213, 219, 234, 502 | us-key, wwff, parkinfo, access, campfed, trails/index (502 = offline pack list) |
| finder.js | 28, 178, 179 | locations.json, locations-ky.json (Activation Finder; note KPC.dataUrl is not used here although the offline file mentions it) |
| kpc-tracker.js | 87, 89, 90, 165 | parkinfo/index, CA, <PFX>, pota/index |
| kpc-rare.js | 28, 29, 43 | parkinfo/index, CA, <place> |
| kpc-lookup.html | 110, 111 (jget raw fetch, line 109) | parkinfo/index, parkinfo/<cc> |
| kpc-park-sheet.html | 189, 194 (jget raw, via once()) | data/nwr, parkinfo, campfed, access |
| kpc-sota.html | 165, 184 | sota-land/<area>, locations.json |
| kpc-checker.html | 184 | locations.json |
| kpc-sota-az.js | 30 | locations.json |
| kpc-trails-layer.js | 31, 36 | trails/index, index-state, trails/<ref> |
| kpc-park-control.js | 20, 21 | trails/US-3791, US-4572 (the Trail of Tears + Lewis and Clark lines) |
| kpc-park-info.js | 209 | wwff/<prefix> |
| kpc-park-notes-us.js | 30 | wwff/<prefix> |
| kpc-map-tools.js | 40 | wwff/<prefix> |
| kpc-guide-top25.js | 81 | parkinfo/<state> |
| kpc-radar-plus.js | 19 | locations-ky.json |
| kpc-maprep.js | 262 (via B.jget, which is raw in kpc-bounds.js) | data/state-gis.json |
| kpc-weather.js | 273 (jget only wraps data/alerts) | **data/nwr/<ST>.json**; locations.json (64) and parkinfo/CA (64) also raw |
| kpc-closures.js | fine (only data/alerts) | ok |

Soft failures (offline "save" lists; a 404 only shows fewer files saved): kpc-logger.js 997 (parkinfo/index), kpc-kit.js 322 (wwff), kpc-us-planner.js 502, kpc-offline.js (locations are handled with DATA_MOVED, good).

Already safe (wrap everything through KPC.dataUrl): kpc-access, kpc-campgrounds-us, kpc-hunt, kpc-kit, kpc-logger, kpc-lounge, kpc-top50, kpc-search, and (alerts only) kpc-closures + kpc-weather. Caution: their MOVED regex has no `data/leaders` typo, fine; kpc-weather/closures only cover alerts, so nwr/locations there are NOT covered (above).

## 2. BOTS
**KPC-Data workflows (check out KPC-Links and read its data; only data/fers is laid over it):**
- kpc-fers.yml, kpc-fers-regions.yml, kpc-fers-line.yml, kpc-fers-ky-lines.yml run kpc_fers.py, which reads data/trails (257-267), data/us-key/layers.json (150, 359), data/ca-key + world-key layers (360, 363), data/canada-bounds (481), data/parkinfo (128, 248), data/state-gis.json (149), data/boundary-score.json (658), data/access/<st>.json (1442) and locations.json. **After the delete the 2-fer bot loses its trail lines, layer lists and access pins (most reads are try/except, so it would run and give wrong answers silently).** Needs `rsync -a kpcdata/data/ data/` + locations copy like the alerts/leaders workflows already do.
- kpc-parking-explorer.yml (kpc_parking_explorer.py: state-gis.json 106-111, us-key/layers 112, ca-key/layers 95, access-layers.json 114), kpc-watch.yml (kpc_near_miss.py: parkinfo 75, 106; kpc_map_observations.py: us-key, ca-key, world-key 57, access 131, campstate 142, parkinfo-web 151), kpc-discovery.yml (kpc_discovery.py: 51-62, 187-188), and kpc_outline_lead_test.py (parkinfo/CA 36): same missing overlay.
- Already fine: kpc-eu-alerts, kpc-state-leaders, kpc-us-closures (they rsync kpcdata/data over the checkout), and kpc_map_observations MOVED = alerts, leaders only.
**KPC-Links workflows that stay or have not moved yet** (all still IN LINKS today): kpc-us-key, kpc-ca-key, kpc-world-key, kpc-key-measure, kpc-boundary-check, kpc-canada-bounds, kpc-canada, kpc-wwff-dir, kpc-world-pota, kpc-sota-land, kpc-state-links, kpc-official-links, kpc-state-trails, kpc-us-trails, kpc-us-access, kpc-fed-camps, kpc-state-camps (+probe), kpc-nwr, kpc-state-gis, kpc-new-refs, kpc-ref-check, kpc-us-closures (a second copy also exists in KPC-Data). If any run after the delete they re-create partial folders in Links and read nothing old.
**Bots that STAY in Links but read moved files:** kpc_formtools.py 118 (data/wwff — the form approvals bot), kpc_park_notes.py 58, 62 (parkinfo/index, wwff/KFF; writes kpc-park-notes), kpc-campground-notes (kpc_campground_notes.py 72: parkinfo), kpc_retired_sweep.py 128, 141, 195, 212 (edits locations.json / locations-ky.json IN PLACE: after the delete it edits a stale or missing copy), kpc_search_lists.py 18 (rewrites locations.json), kpc_map_linkcheck.py 13 + kpc_map_finder.py 47-50 (parkinfo-web, parkinfo), kpc_name_index.py (wwff, sota/t), kpc_outline_score.py + kpc_boundary_report.py (us-key, boundary-score).

## 3. LINKS in guides / PDFs / posts
- Nothing in the 13 PDFs, the guides or the Discord/Facebook post scripts links straight to a moved file.
- Two bot scripts build GitHub links to moved review files: kpc_us_key_issue.py line 10 (data/us-key/review/US-%s.md) and kpc_ca_key_issue.py line 10 (data/ca-key/review/CA-%s.md): the issue links 404 after the delete; point them at KPC-Data.

## 4. KPC-App (read)
- www/kpc-parks.js 11 reads site `app/packs/` (stays). www/kpc-alerts.js and kpc-app.js read kpc-conditions.json / app/version.json / hunters.json / kpc-special-events.json (all STAY). Nothing in the app fetches a moved folder.
- But the pack builder in KPC-Links, `.github/scripts/build_app_pack.js`, reads data/parkinfo (readdirSync, line 57: **throws if the folder is gone**), data/access/US-XX.json (63), data/status/kpc_state_links.json (56). Not in a workflow; whoever runs it by hand must have KPC-Data data/ laid in first.

## Suggested order for chat 2 / chat 1
1. Pages first: kpc-bounds.js, kpc-us-planner.js, finder.js, kpc-weather.js (nwr, locations), kpc-lookup/park-sheet/sota/tracker/rare/trails-layer/park-control (use the same dfetch wrapper as kpc-access.js).
2. Then add the overlay step to the KPC-Data fers / watch / explorer / discovery workflows.
3. Then the staying Links bots (formtools, park_notes, retired_sweep, search_lists).
4. Delete only after a page test at 390 px with the Links copy blocked (I can do that test on request).

## BLOCKED-COPY TEST RESULT (chat 8, Oct 27 ~8 PM, after chat 1 + chat 2 fixes)
Method: Playwright 390 px, local server; every path in `.github/kpc-moved.txt` (alerts, leaders, parkinfo, wwff, sota, names, sota-land, trails, access, status/kpc_state_links.json) answered 404 from the Links copy; KPC-Data's files served from a clone for the KPC-Data address; locations.json NOT blocked. All 119 pages x member + guest (webdriver off), then targeted checks on Am I in the Park (KPCB: us key, outline, WWFF and SOTA near), Kit (OH, KY, WWFF), park sheet, lookup, trip planner (search), Campgrounds (TN, OH), Access finder, Weather, Hunters + Activators Lounges, Tracker, Rare, SOTA pages, Park Control, Finder.
- **Pages: PASS.** 0 requests to a blocked Links path anywhere; 0 sideways scroll (all 390); no page errors; data shows (KPCB wwffNear 8, sotaNear 122, us key + outline found, Campgrounds OH/TN lists, Access finder, Kit KY + WWFF, Hunters spots list). Fallbacks seen and fine: locations.json / locations-ky.json answer 404 from KPC-Data (removed on purpose) and fall back to Links.
- Test-only noise ignored: unpkg/leaflet, tiles, weather and pota.app calls (blocked in this sandbox: Kit for an OH park and a SOTA summit shows empty here with AND without the block), `/KPC-Links/` absolute paths on 404.html, `/logger-beta/capacitor.js`, and the Overlap Finder asking localhost for `/KPC-Data/data/fers/...` (works on the real site, same origin).
- Static grep: no fetch/src/href to a moved folder left outside KPC.dataUrl or a dfetch/dget/jget wrapper; no `'data/'+x` built paths.
- **Bots: 1 left.** `kpc-world-key.yml` (kpc_world_key.py line 710 reads data/parkinfo/<CC>.json) has no kpc_overlay step: after the delete it silently skips the park-name matching (try/except), so the world key gets weaker. Add the overlay step. (kpc-discord-relay reads KPC-Data first, kpc-us-closures downloads from KPC-Data: both fine; every KPC-Data workflow has its overlay.)
**VERDICT: PASS for the pages. B6 part 2 can go once kpc-world-key.yml gets its overlay line.**

## RE-CHECK AFTER THE REAL DELETE (chat 8, Oct 27 ~8:50 PM; fresh clones of KPC-Links + KPC-Data, nothing blocked by hand)
- Delete commit 80d6ed04 (10,093 files): every deleted path is on `.github/kpc-moved.txt`; nothing else deleted (checked up to HEAD 396741e8). Every listed folder is gone. locations.json, locations-ky.json, kpc-conditions.json, app/, kpc-ky-data.json, ky-dbnf-owned.geojson, data/us-key (+ overrides.json), ca-key, canada-bounds, world-key, pota, northam/state-gis, hunters, ky-*.json, holidays all still there.
- Every deleted file exists in KPC-Data **except** `data/status/kpc_state_links.json` (KPC-Data/data/status only holds kpc_us_closures.json). Only build_app_pack.js reads it (in a try/catch, dates only): run the state-links bot in KPC-Data once so it is written there.
- Pages: 119 x member + 119 x guest at 390 px + the same 20 spot checks: same result as the blocked test. 0 reads of a deleted path, 0 sideways scroll, 0 page errors, data shows. Same known test-only noise.
**PASS** (one small note: kpc_state_links.json).
