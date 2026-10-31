# KPC 9: MAP PICTURE MAKER for the checkers. A build spec for an outside coder.
Read KPC_HOW_WE_WORK.md first.

## Why
The club's checker (chat 11) grades map matches and 2-fers by name, kind of place and acres, because it cannot see a map.
A small picture per item lets it grade by LOOKING: is this outline really the park, does the 2-fer patch really sit where both parks are?
This is the biggest single help to the checks.

## What it makes
One small JPEG per item, about 900 × 700 px and **under 150 KB**, plus a one-line caption JSON. Each picture shows:
- **The base map.** Government basemaps only:
  - US: USGS The National Map (`basemap.nationalmap.gov` USGSTopo / USGSImageryTopo tiles);
  - Canada: Natural Resources Canada CBMT (`maps-cartes.services.geo.ca` / `geoappext.nrcan.gc.ca`);
  - elsewhere: the country's national mapping agency WMTS if open (e.g. swisstopo, IGN France Géoplateforme, basemap.at), else a plain background with coastlines from Natural Earth.
  - **Never OSM or Google tiles.** Put the tile credit in the corner.
- **The outline being graded:** gold, 2 px. Its neighbours on the same layer within the view: thin grey with their names.
- **POTA's pin:** a red dot with the park number.
- **For a 2-fer:**
  - both parks' outlines (gold + blue);
  - the overlap patch filled orange at 40%;
  - for trail / river rows, the 100 ft band (from the trail line, or from the river bank for water trails, R5) as a dashed line;
  - the patch's width in yards in the caption.
- **A scale bar,** a north arrow, and a title line: park number, name, grade, record name, acres (record vs POTA / PAD-US), "pin inside / N m outside".
- **An optional inset** at 4× zoom-out, so the checker sees where it is.

## Inputs
- `--questions <file>`: the club's question files (`data/waiting/questions/*.json`: `ref`, `layer`, `record`, `record_name`, `acres_approx`, `answer`) → one picture per question, reading the record live (`/query?objectIds=…&returnGeometry=true&outSR=4326&f=geojson`) and the neighbours (envelope query).
- `--fers <area file>` (`data/fers/US-XX.json`) → one picture per live 2-fer row, using the stored `shape` + the parks' records from the keys (read live).
- `--refs US-0019,…` with `--key` → one picture per park outline from the key.
- `--limit`, `--resume`, `--out pictures/`, `--max-minutes 50`.

## Outputs
- `pictures/<kind>/<ref or id>.jpg` + `pictures/index.json`: {id, file, caption, read_date, sources [urls], warnings}.
- **Warnings** are written when something looks wrong:
  - the pin is more than 2 km outside;
  - the outline is tiny vs the record acres;
  - the 2-fer patch is under 50 yards across;
  - the record geometry is empty.
- The pictures folder is designed to be pushed to a THROWAWAY branch and deleted after grading. The tool also has `--clean-older-than DAYS`.

## Tech
Python 3.11+, requests, shapely ≥ 2, pyproj, Pillow (draw the tiles + vectors yourself; no browser needed), and mercantile (or your own tile maths).
Tiles are cached on disk for the run.

## Test (TEST_REPORT.md, with 12 example pictures in the zip)
1. 4 Kentucky 2-fer rows from `fers/US-KY.json`: 2 area, 1 trail, 1 river (show the bank band).
2. 4 questions from `waiting/questions/layers.json`: 2 YES, 2 NO.
3. 2 Canadian parks from `ca-key/CA-ON.json`.
4. 2 Swiss parks from `world-bounds/CH`.

Report: time per picture, average size, any tile source that failed.
