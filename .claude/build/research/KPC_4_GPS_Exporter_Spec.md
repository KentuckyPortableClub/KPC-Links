# KPC GPS FILE MAKER (US + Canada): build spec for an outside coding agent (Fable reviews afterwards)

## What it makes
One GPS file set per US state and Canadian province, like the club's Kentucky 2-fer file (`KPC_KY_POTA_2fers_3fers.gpx`), for GPS units and phone apps (Gaia, OsmAnd, Garmin, Avenza):
- **GPX** (`<area>.gpx`): waypoints for every POTA park pin, every 2-fer / 3-fer spot, every parking / access point; tracks for trail lines.
- **KML** (`<area>.kml`, optionally KMZ): the same + park OUTLINES as polygons, styled by grade.

## Data inputs (JSON, read from the club's data copy)
- Park pins + names: `data/pota/` (or `parkinfo/<area>.json`: name, type, lat, lon).
- Outlines + grade: the boundary keys (`us-key/US-XX.json`, `ca-key/CA-XX.json`, Kentucky's own key) and the outline files they point to; grade = official / approximate / pin.
- Trail lines: `data/trails/<ref>.json` (+ the key's trail-line pointers).
- 2-fer spots: `data/fers/<area>.json` (only rows the club has released: status live, not 'not sure'; each has the park numbers, the spot's lat/lon, kind area / trail / river / water-only, size, 'checked' date).
- Parking / access points: `data/access/<area>.json` (`parks{ref: [[lat, lon, label, kind], …]}`, with credits).

## Rules (do not change)
1. Names: waypoint name = `US-1234 Park Name` (park), `2-fer US-1234 + US-5678` (spot), `P US-1234 Lot name` (parking). Keep every credit line from the source files in the description.
2. Every 2-fer waypoint's description carries this exact notice: "⚠️ Parks' boundaries may overlap here, but we can't confirm it. Check both official boundary maps and make your own call before you count it."
3. Every file's header / first description carries: "ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go." plus "KPC is an independent ham radio club, not part of Parks on the Air®, SOTA or WWFF."
4. Approximate outlines are labelled in their name / style ("approximate"); pin-only parks get a pin, no outline. Water-only spots say "water only (boat / kayak)".
5. No POTA / SOTA / WWFF logos or icons. No hours, fees or closures outside Kentucky.
6. Outline detail: keep the stored detail (≤ 3-5 m); for KML size, a 'lite' option that simplifies to 10 m is OK only if the file says so.

## Output + size
`gps/<area>/<area>.gpx`, `<area>.kml` (+ `<area>-lite.kml` if > 10 MB), and `gps/index.json` (area, counts, sizes, build date). Validate GPX against the GPX 1.1 schema; open the KML in a parser to check it.

## Tech
Python 3.11; standard library (xml.etree), shapely for simplification. Headless on GitHub Actions, one run builds all areas (or `--areas US-KY CA-ON`).

## Test
Kentucky first (compare with the existing KY 2-fer GPX: same spots, notices present), then one big state (Utah) and one province (Ontario). Report counts per file.

## Deliver
`kpc_gps_export.py`, a short README, the 3 test files. Don't publish anything: the files go public only on Brandon's GO.
