# KPC 11: BOUNDARY CHANGE WATCHER. A build spec for an outside coder.
Read KPC_HOW_WE_WORK.md first.

## Why
Agencies redraw parks: land is bought or sold, records are merged, or a layer is moved to a new address. The club's saved outlines and
2-fers then go stale. This tool runs once a week, compares every park's saved outline with the agency's live layer, and flags the ones that changed.
(The club's 2-fer checker already does this for 2-fer patches; this tool covers every park.)

## What it does, per park (batch by area, resume)
1. **The layer:**
   - Read the layer's metadata (`?f=json`): `editingInfo.lastEditDate`, `serviceItemId`, the record count.
   - If the layer did not change since the last run (same last-edit date + count), mark the whole layer UNCHANGED and skip its parks (cheap).
2. **Otherwise the record(s)** (`objectIds` query, `outSR=4326`, simplified on the server with `maxAllowableOffset` ≈ 3 m in degrees):
   - its fingerprint = rounded area (acres, to 0.1%) + bounding box (to 10 m) + vertex count;
   - compare with the last run's fingerprint and the saved outline.
3. **The verdict:**
   - SAME;
   - GREW / SHRANK (area changed more than 2% or more than 5 acres);
   - MOVED (bounding box shifted more than 50 m with a similar area);
   - RECORD GONE (the id is missing);
   - RENAMED (the name field changed);
   - LAYER MOVED (HTTP 404 / "service not found" at the URL: search the same server's folder for a service with the same name / field and report it as a lead);
   - SOURCE DOWN (retry next run).
4. **For a changed park, also say:**
   - which 2-fer rows use it (from `fers/<area>.json`: the `refs` contain it);
   - how much of the old outline is still inside the new one (10 m tolerance).

## Inputs
The keys (`us-key`, `ky-answer-key.json`, `ca-key`) + `layers.json` + `fers/` + the bounds folders; `--areas`, `--resume`, `--max-minutes 50`, `--state watch/state.json`.

## Outputs
- `watch/state.json`: fingerprints per layer and record. Keep it small: numbers, not geometry.
- `watch/changes-<date>.json`: only the changed parks, with verdict, why, 2-fer rows affected, and the old-vs-new acres.
- `watch/summary.md`: counts per area plus the changed parks list.
- **The first run only builds fingerprints.** "Changed" starts on the second run.

## Rules
- Official layers only, as the keys name them.
- Never edit a key, an outline or a 2-fer.
- Weekly schedule friendly: stay under 50 minutes per job, chunk by area.

## Tech
Python 3.11+, requests, shapely ≥ 2, pyproj.

## Test (TEST_REPORT.md)
1. Build fingerprints for Kentucky + Tennessee + Ontario.
2. Run again at once: everything must be SAME, which proves no false alarms.
3. Unit tests: fake a grown / shrunk / moved / gone / renamed record and a moved layer. Each must give the right verdict.
