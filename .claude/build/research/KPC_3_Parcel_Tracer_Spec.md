# KPC PARCEL TRACER: build spec for an outside coding agent (Fable reviews afterwards)

## What it does
For a park with NO official GIS boundary, build an **Approximate** outline from the county (US) or municipal / provincial (Canada) PARCEL map: every parcel **owned by the park's managing agency** around the POTA pin, joined into one shape. Batch: many parks per run.

## Hard rules (club Rule G, G-2 + R-G7 step 4b; do not change)
1. Only parcels whose OWNER is the park's managing agency (state parks, wildlife agency, city, county, conservation authority, province, federal agency). Match the owner name as written by the parcel source; keep the exact owner string.
2. Output grade is ALWAYS `"approximate (agency parcels)"`, never official, never used as Official by the 2-fer line. Source = the parcel layer URL + owner name + parcel IDs + read date.
3. Only parcels that touch, or are within 200 m of, the growing shape starting from the parcel under (or nearest within 500 m of) the POTA pin: stop when no more same-owner parcels connect. Never sweep the whole county.
4. POTA pins never move. Pin outside the result by > 1 km → don't output; report it.
5. Official government parcel sources only (county / state / province GIS, statewide parcel layers, Ontario Parcel, BC ParcelMap, GeoNB, NS property, Quebec cadastre where open). NEVER OpenStreetMap, Google, Regrid / real-estate sites.
6. If the agency's own boundary layer for the park appears later, ours is deleted (handled elsewhere: just key the output by park number).

## Inputs
- `parks.json`: `[{ref, name, state_or_prov, lat, lon, agency_owner_names: ["STATE OF X DEPT OF NATURAL RESOURCES", "…"], parcel_layer_url}]` (the parcel layer URL comes from the club's research workbooks, round 14 'Parcel / layer URL' + 'Owner on the parcel').
- `owner_aliases.json` (optional): agency → list of owner spellings used on parcels.

## Steps per park (one failure never stops the batch)
1. Query the parcel layer (ArcGIS REST `query`, `outSR=4326`, `f=geojson`) with a point at the pin, then an envelope around it (start 1 km, grow to max 10 km), paging with `resultOffset` / `resultRecordCount`.
2. Owner match: normalise (upper case, strip punctuation, expand DEPT / DNR / ST / STATE OF…), compare against `agency_owner_names` + aliases; fuzzy ratio ≥ 0.9 only, else report 'owner unclear'.
3. Grow the connected set (shapely `unary_union`, 200 m adjacency) from the seed parcel.
4. Dissolve, fix validity (`make_valid`), remove slivers < 0.1 ac, simplify to 3 m in a metric projection (pyproj UTM of the area).
5. Sanity: area vs any known acreage (0.2×–5×), pin inside or ≤ 1 km.
6. Output `parcels/<area>.json` (FeatureCollection; properties: ref, name, grade, owner, parcel_ids, n_parcels, acres, source_url, read_date) + `parcels/report.csv` (ref, status DRAWN / OWNER UNCLEAR / NO PARCEL / PIN FAR / ERROR, why).

## Tech
Python 3.11; requests, shapely ≥ 2, pyproj, rapidfuzz. Headless on GitHub Actions, ≤ 55 min per run: chunk + save after each park. Polite: one request at a time per host, a User-Agent naming the club, back-off on errors, respect `maxRecordCount`.

## Test set
Kentucky first: US-10172 Salato Wildlife Refuge (Franklin County KY; owner = Kentucky Department of Fish & Wildlife Resources). Then 5 US rows marked PARCEL in round 14 and 5 of the Canadian PARCEL rows from round 13. Report each result.

## Deliver
`kpc_parcel_trace.py` (`--refs` and `--all`), `requirements.txt`, a short README, the test report. Don't wire it into a workflow: the club's bot chat does that after Fable's review.
