# KPC 12: RIVER-BANK LIBRARY for Canada + the world. A build spec for an outside coder.
Read KPC_HOW_WE_WORK.md first.

## Why
The 2-fer rule for WATER TRAILS (R5) counts the strip within 100 ft (30.48 m) of the **water's edge** (the river bank) of the river the water
trail follows, not a centre line.
- In the US the club reads river banks from USGS NHD (NHDArea StreamRiver + NHDWaterbody lakes / reservoirs).
- Canada and the rest of the world have no bank source yet, so water 2-fers there cannot be checked.

This tool builds the bank polygons from official national water data, for the stretches the club needs.

## Official sources (the managing government's own data only)
- **Canada:** National Hydro Network (NHN, Natural Resources Canada) waterbody polygons, through the open-data download / WFS / GeoBase, and the provinces' own hydro layers where finer:
  - BC Freshwater Atlas `WHSE_BASEMAPPING.FWA_RIVERS_POLY` / `FWA_LAKES_POLY` via `openmaps.gov.bc.ca/geo/pub/wfs`;
  - Ontario Hydro Network (OHN, Ontario GeoHub);
  - Québec GRHQ (Données Québec);
  - Alberta / Manitoba hydro layers.
  - Use the finest official one per province; say which.
- **Europe:** EU-Hydro (Copernicus Land Monitoring Service, river polygons + inland water) and, where finer, the national mapping agency's own water layer (e.g. swisstopo swissTLM3D, IGN BD TOPAGE France, Kadaster TOP10NL, Lantmäteriet, Ordnance Survey Open Rivers is lines only, so OS MasterMap water is not open: say so).
- **Others:** the national mapping agency's open hydro polygons when they exist (Australia: Geoscience Australia surface hydrology polygons; New Zealand: LINZ river polygons; Japan: GSI). Otherwise report NO OFFICIAL BANK SOURCE.
- **Never OSM water polygons, never Google, never global datasets made from imagery** (JRC Global Surface Water etc.) unless the club approves later.
- When only a centre line exists (a narrow river with no polygon), report LINE ONLY. The club then uses the line rule and marks it so; it never invents a width.

## What it does
Input `--stretches stretches.json`: [{id, refs [the two parks], river name, center [lat, lon], bbox or the water trail's line}].
For each stretch:
1. Find the official water polygons inside the bbox (+ 1 km).
2. Keep the ones that touch the river the trail follows: match by the polygon's name field where there is one, else by touching the trail line within 200 m.
3. Merge them, repair them (`make_valid`), and simplify to 1 m.
4. Write the bank polygon and the 100 ft band (the bank buffered outward and inward by 30.48 m, i.e. the strip on both sides of the water's edge) in EPSG:4326.
5. Record the source + licence + read date.

## Outputs
- `banks/<id>.geojson`: water polygon + band, properties {source, licence, read_date, method polygon | line-only}.
- `banks/report.csv`: id, refs, source used, status (OK / LINE ONLY / NO OFFICIAL BANK SOURCE / SOURCE DOWN), why.
- `sources.md`: per country / province, which official water source and its licence.

## Tech
Python 3.11+, requests, pyogrio (with GDAL wheels), shapely ≥ 2, pyproj, OWSLib for WFS. Cache downloads; never store a whole national file in the output.

## Test (TEST_REPORT.md)
1. Three Canadian water stretches:
   - one in BC (Cowichan River: CA-6131's pin is 1 m from it on the BC FWA network);
   - one in Ontario;
   - one in Québec.
2. Two European stretches: one Swiss, one French.
3. One stretch with only a centre line, which must give LINE ONLY.

The club will send `stretches.json` for its real Canadian water-trail pairs when wiring.
