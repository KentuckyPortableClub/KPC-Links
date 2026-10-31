# KPC 2-FER ACCURACY CHECKER: build spec for an outside coding agent (Fable reviews afterwards)

## Why
Every live 2-fer (two POTA parks whose official boundaries overlap on public ground) was found from official layers at one moment. Layers change, and early runs had bugs. This tool re-checks every live 2-fer against the LIVE official layers and flags any that no longer hold, so a person can look before members are misled.

## Input
- The club's 2-fer files (`data/fers/<area>.json`, `spots[]`: `refs`, `kind` area / trail / river / water-only / same land, `center` [lat, lon], `shape` (the overlap polygon), `lines` (trail / river lines used), `acres`, `wide_m`, `status`, `maps`, and per park the source layer + record id where present).
- The boundary keys (`us-key`, `ca-key`, KY key): per park the official layer URL(s) + record ids / names (`m` pieces).

## What it does, per live 2-fer (skip rows whose status starts 'dropped' / 'merged'; batch, resume)
1. For each of the two (or three) parks: re-read the park's official record(s) from the live layer (ArcGIS query by record id, else by name near the pin; `outSR=4326`, `f=geojson`).
2. Recompute the overlap in a metric projection (UTM of the spot): area parks = intersection of the two polygons; trail / river rows = the park polygon ∩ a 100-ft (30.48 m) buffer of the official trail line / of the river the line follows (the club's rule R5 / R6); water-only rows = the overlap that is water.
3. Compare with the stored row: CONFIRMED (overlap still there, size within ±25 %), SHRUNK (> 25 % smaller), MOVED (overlap centre > 200 m away), GONE (no overlap now), SOURCE DOWN (layer did not answer; retry later), RECORD CHANGED (record id missing / renamed).
4. Size rules (the club's R9): flag rows now under 50 yards across ('small overlap'), and water-only rows.
5. Output `fers_check/<area>.json` + `report.csv` (id, refs, kind, stored acres, live acres, distance moved, verdict, why, layer read dates) + a short summary per area. Never edits the 2-fer files: a person and the club's waiting room decide.

## Rules
- Official layers only (the ones the keys name). Never OpenStreetMap / Google.
- Polite: one request at a time per host, User-Agent naming the club, back-off; cache each park's record for the run.
- Headless on GitHub Actions, ≤ 55 min per job, chunk by area + resume.

## Tech
Python 3.11; requests, shapely ≥ 2, pyproj.

## Test
Kentucky first (every live KY row: compare with the club's own Kentucky checks), then one western state with BLM pairs (Utah) and one with trail pairs (Virginia). Report verdict counts.

## Deliver
`kpc_fers_check.py` (`--areas US-KY …`, `--resume`), `requirements.txt`, README, the test report. Not wired: the club's bot chat does that after Fable's review.
