# KPC PICTURE-MAP TRACER: build spec for an outside coding agent (draft; Fable reviews + fixes Thursday)

## What it does
Turns an agency's official PICTURE map of a park (PDF / brochure / JPG, no coordinates) into an **approximate** outline (or a trail route line) on the real map, for parks that have NO official GIS boundary. Many parks at a time (batch).

## Hard rules (from the club's Rule G R-G9; do not change)
1. Only the managing agency's OWN official map of THAT park.
2. The picture must be lined up ("georeferenced") to **at least 3 fixed points** that also exist on an official basemap: road junctions, shoreline bends, section / township corners, river confluences.
3. Compute the **fit error** (RMS, metres) of those control points. **Only draw if the error is under 50 m.** Otherwise: no outline, write why.
4. Output is ALWAYS labelled `grade: "approximate (picture map)"`, `fit_m: <error>`, the source map URL + page. NEVER "official". Never used for 2-fers.
5. If an official GIS outline for the park appears later, the traced one is deleted (handled elsewhere; just keep the park number as the key).
6. Basemap for control points: **public government sources only** (US: Census TIGER roads / PLSS section lines from BLM CadNSDI / USGS hydrography NHD; Canada: NRCan National Road Network / CanVec; elsewhere: the national mapping agency). **Do NOT use OpenStreetMap or Google** (club rule).

## Inputs
- A folder `maps/` of JPEGs named `<park number>_<short-name>.jpg` (max 2000 px, the page that shows the boundary) + `index.json` rows: `{ref, name, agency, source_url, page}`.
- For each park: its POTA pin (lat, lon) from a JSON file `pins.json` `{ref: [lat, lon]}` (gives the area to search for control points).

## Steps per map (batch: loop over all maps; one failure never stops the batch)
1. **Find the boundary on the picture:** the park boundary is usually a distinct colour / dashed line. Detect it by colour clustering (k-means in Lab colour space) + the longest closed contour (OpenCV `findContours`), or for trails the longest open line of the route colour. Save a debug PNG with the detected line drawn on top.
2. **Find control points:** detect road junctions / shoreline corners on the picture (line-segment detection, e.g. OpenCV LSD + intersections); fetch the same kind of features from the government basemap in a box around the pin (e.g. 10 km); match them by geometry (RANSAC on candidate triples, similarity or affine transform). Accept only if ≥ 3 inliers.
3. **Fit:** affine (or 2nd-order polynomial if ≥ 6 points), compute the RMS error in metres; reject if ≥ 50 m or fewer than 3 points.
4. **Transform** the boundary pixels to lon/lat, simplify to 3 m (Douglas-Peucker in a metric projection), make a valid polygon (or a line for trails).
5. **Sanity checks:** the POTA pin should be inside or within 1 km (else flag, never move the pin); area within 0.2×-5× of any known acreage; no self-intersections.
6. **Output** one GeoJSON per area `traced/<area>.json` (FeatureCollection; properties: ref, name, grade, fit_m, n_points, method, source_url, page, date) + `traced/report.csv` (ref, status DRAWN / NO FIT / NO LINE / ERROR, fit_m, n_points, why) + the debug PNGs.

## Tech
Python 3.11; opencv-python-headless, numpy, shapely ≥ 2, pyproj, requests, scikit-learn (k-means). Runs headless on GitHub Actions (ubuntu-latest), max ~55 min per run, so process in chunks and save after each map. Polite web requests (one at a time, a User-Agent naming the club, retries with back-off).

## Test set
Start with 3 maps: US-2685 Winslow State Park, US-7769 Heaters Island WMA, US-8103 Cayuga Lake WMA (Brandon can send the JPEGs), then Kentucky's US-10172 Salato Wildlife Refuge (KDFWR trail map PDF, page 1, shows the KDFWR boundary). Report the fit error for each.

## Deliver
`kpc_trace_picture.py` (single file, a `--refs` option and a `--all` option), a `requirements.txt`, a short README with how to run it, and the test results. Don't wire it into any workflow; the club's own bot chat does that after Fable's review.
