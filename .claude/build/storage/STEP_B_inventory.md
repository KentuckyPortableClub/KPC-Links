# STORAGE PLAN STAGE 2 STEP B, B1 INVENTORY (chat 2, Oct 27 2:20 PM)

Bot-REWRITTEN data that pages FETCH, to move to KentuckyPortableClub/KPC-Data (served at /KPC-Data/, same origin). Sizes from today's copy.
Pages = files that fetch the folder (grep). Bots = workflows that rewrite it (they move to KPC-Data in B5).

## MOVE (folders)
| Folder | Size | Pages that fetch it | Bots (workflows) |
|---|---|---|---|
| data/wwff/ | 32 MB | kpc-park-info.js, kpc-bounds.js, kpc-park-notes-us.js, kpc-lounge.js | kpc-wwff-dir.yml |
| data/world-bounds/ | 26 MB | kpc-bounds.js | kpc-world-key.yml |
| data/pota/ | 24 MB | kpc-tracker.js, kpc-lounge.js, kpc-us-planner.js | kpc-world-pota.yml |
| data/names/ | 21 MB | kpc-lounge.js | kpc-wwff-dir.yml |
| data/sota/ | 20 MB | kpc-bounds.js, kpc-lounge.js, kpc-us-planner.js | kpc-sota-land.yml, kpc-wwff-dir.yml |
| data/canada-bounds/ | 16 MB | kpc-bounds.js, kpc-us-planner.js | kpc-ca-key.yml, kpc-canada-bounds.yml |
| data/parkinfo/ | 15 MB | kpc-tracker.js, kpc-search.js, kpc-hunt.js, kpc-access.js (+ more) | kpc-state-links.yml, kpc-official-links.yml |
| data/world-key/ | 13 MB | kpc-bounds.js | kpc-world-key.yml, kpc-key-measure.yml |
| data/us-key/ | 9.2 MB | kpc-bounds.js, kpc-us-planner.js | kpc-us-key.yml, kpc-boundary-check.yml, kpc-key-measure.yml |
| data/trails/ | 6.6 MB | kpc-trails-layer.js, kpc-us-planner.js, kpc-park-control.js | kpc-state-trails.yml, kpc-us-trails.yml |
| data/access/ | 3.5 MB | kpc-access.js, kpc-lounge.js, kpc-us-planner.js, kpc-park-sheet.html, kpc-kit.js | kpc-us-access.yml |
| data/ca-key/ | 1.7 MB | kpc-bounds.js | kpc-ca-key.yml, kpc-key-measure.yml |
| data/sota-land/ | 1.7 MB | kpc-lounge.js, kpc-sota.html | kpc-sota-land.yml |
| data/leaders/ | 1.2 MB | kpc-top50.js, kpc-hunt.js | kpc-state-leaders.yml (chat 5) |
| data/campfed/ | 0.8 MB | kpc-us-planner.js, kpc-park-sheet.html, kpc-kit.js, kpc-campgrounds-us.js | kpc-fed-camps.yml |
| data/campstate-manual/ | 0.9 MB | kpc-campgrounds-us.js | none (hand rows by chat 2) |
| data/campstate/ | 0.5 MB | kpc-campgrounds-us.js | kpc-state-camps.yml, kpc-state-camps-probe.yml |
| data/nwr/ | 0.4 MB | kpc-weather.js, kpc-park-sheet.html | kpc-nwr.yml |
| data/alerts/ | 0.2 MB | kpc-closures.js, kpc-weather.js, kpc-campgrounds-us.js | kpc-us-closures.yml, kpc-eu-alerts.yml |

## MOVE (single files)
locations.json (5.4 MB, POTA/SOTA/WWFF list; many pages) + locations-ky.json (0.4 MB) · data/northam.json (2.7 MB) · data/canada.json (2.5 MB) · data/parkinfo-web.json (0.5 MB) · data/boundary-score.json (0.9 MB) · data/boundary-report.json · data/state-gis-found.json (2.0 MB; kpc-maprep.js) · data/access-layers.json · data/state-gis.json (read by bots + Map Rep). Check each one's fetchers with the helper switch (B4).

## BOT-ONLY (no page fetches; can go to KPC-Data with their bot in B5, no helper needed)
data/new-refs/ (0.6 MB, kpc-new-refs.yml) · data/hunters/ (kpc-hunters.yml: writes kpc-hunters.json + app/hunters.json which STAY) · data/map-leads.json (map finder) · data/status/ (each bot's own status file goes with its bot).

## STAYS in KPC-Links
Hand-edited Kentucky files (kpc-ky-data.json, ky-*.geojson incl. ky-dbnf-owned.geojson (bot, but Kentucky's map layer: keep with the ky files), kpc-ky-counties*, data/ky-*.json, data/boundary-checked.json; data/us-key/overrides.json is hand-edited but travels WITH data/us-key), app/ (never), page scripts, img, kpc-conditions.json + the small posting-bot JSONs pages need instantly (chat 5 decides), the Kentucky map tools' files.

Total to move ≈ 220 MB of the working tree (and all future rewrites of it).
