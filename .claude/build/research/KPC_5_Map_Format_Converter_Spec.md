# KPC MAP-FORMAT CONVERTER: build spec for an outside coding agent (Fable reviews afterwards)

## Why
The club's layer collector only reads ArcGIS REST layers (…/MapServer/n, …/FeatureServer/n). Research has found ~2,250 OFFICIAL map sources in other formats (WFS / OGC API Features services, shapefile / GeoPackage / GeoJSON / KML / KMZ / GML downloads, CKAN / Socrata / ArcGIS Hub dataset pages). This tool turns each into the SAME thing the collector already tests, so all of them can be used.

## Input
`leads.json`: `[{ref, area, url, agency, status, note}]` (from the club's file `data/intake/leads-oct31.json`, key `other_layer`), plus optional `name_field`.

## What it does, per URL (batch; one failure never stops the run)
1. **Detect the kind**: WFS (GetCapabilities), OGC API Features (`/collections`), ArcGIS Hub / Socrata / CKAN dataset page (find the download or API link on it), direct file (zip of shapefile, .gpkg, .geojson, .kml/.kmz, .gml).
2. **Fetch only what is needed**: for services, query a bounding box around the park pin (e.g. 5 km; grow to 25 km if empty) instead of downloading the whole country; for files, download once per URL (cache by URL + ETag / Last-Modified; skip files over 500 MB and report them).
3. **Read** with GDAL / Fiona / pyogrio (any OGR format), reproject to EPSG:4326, keep polygons (and lines for trails).
4. **Name field**: pick the field that holds the site name (common names: NAME, NAAM, NOM, NOMBRE, SITE_NAME, SITENAME, Name_E, NAME_EN, BEZEICHNUNG, DENOMINAZIONE…) or the one given; list all text fields in the report.
5. **Output**, for each (ref, url): the records within 2 km of the pin as a small GeoJSON (`converted/<area>/<ref>__<hash>.geojson`, properties: name, record id, source url, licence text if found, read date), simplified to 3 m in a metric projection; plus `converted/report.csv` (ref, url, kind, n_records_near, name_field, licence, status OK / EMPTY / TOO BIG / ERROR, why).
6. **Licence**: copy the licence / terms text from the service metadata or dataset page; flag 'no licence found'.

## Rules
- Official sources only: the URL list comes from the club; don't follow links off the official host except to the same agency's download host.
- Never OpenStreetMap, Google, or Protected Planet / WDPA downloads (refuse these hosts).
- Polite: one request at a time per host, a User-Agent naming the club, back-off, respect robots.txt.
- Runs headless on GitHub Actions (ubuntu-latest), ≤ 55 min per job: chunk + save after each URL, resume from the report.
- Decides NOTHING about matching: the club's collector + a person decide.

## Tech
Python 3.11; requests, pyogrio (or fiona) + GDAL, shapely ≥ 2, pyproj, OWSLib (WFS), beautifulsoup4 (dataset pages).

## Test
10 leads: 3 WFS (e.g. European national protected-site services), 3 shapefile / GeoPackage downloads, 2 KML/KMZ, 2 Hub / CKAN dataset pages. Report each.

## Deliver
`kpc_convert_layers.py` (`--leads leads.json`, `--refs`, `--resume`), `requirements.txt`, README, the test report. Not wired into any workflow: the club's bot chat does that after Fable's review.
