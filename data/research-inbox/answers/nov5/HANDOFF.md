# KPC Mystery Parks — Handoff: methods, tricks, and where things stand
_Written 2026-11-05 ~08:00 CST by an outside agent (Fable), after the 4–5 Nov sessions. Read this first if the project is picked up again._

## 1. The two keeper files (everything is merged into these — nothing lives anywhere else)
| File | What it is | State |
|---|---|---|
| `mystery-parks_answered_v9.xlsx` | THE workbook. Tab `All` is the master; every country/state tab mirrors it (0 mismatches at handoff). Only these columns were ever written: `answer, official_source_url, padus_id, other_official_id, correct_lat, correct_lon, notes, researched_by`. Left-hand columns untouched. | **624 of 832 answered** (436 match · 183 other/NEEDS-PERSON · 5 wrong pin). **208 blank, every one carries a note** saying what was checked and why. By author: Fable 503 · Opus 71 · Sonnet 50. |
| `research-sources-all.csv` | THE GIS source ledger, 12 columns, 151 rows, sorted by country. Licences verbatim or "not stated". Blocked hosts recorded, never bypassed. | US 27 · JP 25 · AU 18 · CA 11 … |
| `MYSTERY_PARKS_PASS9_FABLE.md` | Round-by-round log (rounds 1–21). | reference |
| `JP_A10_crosswalk.csv` | 70 Japanese rows → exact A10_005 漢字 join key. | ready for the box |
| `fill.py` | The writer. `python3 fill.py src.xlsx dst.xlsx payload.json`; payload = `{ref: {col: value}}`; writes to every tab by header name. | reuse it |

`correct_lat/correct_lon` were **never** filled — we never invent points. The box can derive corrected pins from the matched polygons.

## 2. The method that cracked it (in one paragraph)
Stop searching park-by-park. Find the **agency's own queryable GIS service** (ArcGIS REST `/query` or OGC WFS `GetFeature`), ask it by name (`UPPER(NAME) LIKE '%kw%'` / `cql_filter=name ILIKE '%kw%'`), pull the polygon back in EPSG:4326, and run a **client-side point-in-polygon + distance-to-nearest-vertex** on the POTA pin. One service answers 20–300 rows at once. The pin test turns "I think this is the park" into "the pin is 3.2 km outside this exact official boundary." Distance also settles twins (two Lähdenevas 100 km apart; two Puertos de Beceites).

### Why the browser, not the sandbox
The cloud sandbox's web fetch strips query parameters and can only reach search-surfaced URLs, so it can read `?f=pjson` metadata but **cannot run `/query` or WFS GetFeature**. The desktop app's built-in browser pane can: `javascript_tool` + `fetch()` against the same origin. Pattern:
1. `request_access(url, scope="site")` → user approves (one prompt per host).
2. `navigate` / `preview_start` to the service's `?f=pjson` page.
3. Define helpers on `window` (they persist per tab/origin): `hav`, `pipE` (esri rings), `pipG` (GeoJSON), a `*q(kw, lat, lon)` query wrapper.
4. For >15 rows, **fire-and-forget**: `window.runQ(list)` starts an async loop storing into `window.US`, returns immediately; poll `window.Qdone`. A single call >45 s times out.
5. **Two-step query for big layers**: attributes first (`returnGeometry=false`), rank by name-token overlap, then fetch geometry only for the top 4 by `objectIds`, `geometryPrecision=5`.
6. **Hidden pane = ~1 query/4 s; pane in front = much faster.** A second worker tab on the same host, running the list in reverse, halves the time.
7. Dump results as compact JSON (`JSON.stringify`), paste to a file, triage in Python, write with `fill.py`.

### Triage rules used
- Exact unit name (or all POTA significant words present, ≥2 tokens) → **match**; note the pin distance / "PIN IS INSIDE".
- Name-related neighbour only, tract/unit piece, kind differs (urban park inside a natural park, reservoir vs "state fishing lake", pasture vs "recreation site") → **other = NEEDS-PERSON**, with the candidate and its id in the note (rules 5 & 7).
- Exact unique name but pin >25 km → **wrong pin**.
- Nothing within 15 km → **blank + note** naming what was searched.
- "If in doubt, NEEDS-PERSON. Never guess." was applied literally; the 183 "other" rows are the human queue.

## 3. Services proven this project (all in the CSV with fields + quirks). Highlights:
| Scope | Service | Rows cleared | Gotcha |
|---|---|---|---|
| **US** | USGS PAD-US 4.1 *Combined* `edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US_gaz_combined/MapServer/0` | 289 swept | `State_Nm` is the unit's state — pins near state lines need the neighbour state (Klamath, Caribou-Targhee). WSRs/NFs split per agency segment. Trails, historic sites, airstrips, byways, BLM rec sites, NPS affiliated areas are NOT units. |
| US | BLM `gis.blm.gov/.../recreation/BLM_Natl_Recs_poly/0`, `BLM_Natl_Recreation/9` (polys) `/3` (points) | 7 polys, ~30 point-only | No national SRMA/ERMA layer; those are in state RMP services. |
| US | USFS EDW `apps.fs.usda.gov/arcx/rest/services/EDW/*` | NRTs, NRA negatives | `national_trail_designation=2` = NRT. Rec-site points come back without geometry. |
| US | NPS `services1.arcgis.com/fBc8EJBxQRMcHlei/.../NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2` | confirms affiliated areas have no polygon | don't request `GIS_Notes` (query fails). |
| **CA** | ECCC CPCAD `maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer/0` | 49 swept | `LOC` is a numeric code, not a province; filter by distance instead. SK "Recreation Sites" appear only as Provincial Pastures. NHS, ZECs, biosphere reserves absent. |
| **EU** | EEA Natura 2000 `bio.discomap.eea.europa.eu/.../ProtectedSites/Natura2000Sites/MapServer` (layers 0 SCI, 1 SPA, 2 both) | 20 | some SITENAMEs UPPERCASE → use `UPPER()`. Twins exist. |
| EU | EEA CDDA v21 `.../ProtectedSites/CDDAv21_Dyna_WM/MapServer/1` | 27 (FI SE AT ES CH NO PL RO) | Romanian ș stored as `?` and ă stripped → use SQL `_` wildcards. Some `siteArea` values wrong — trust geometry. Same site in two inventories (CH03+CH52). |
| **FR** | IGN Géoplateforme WFS `data.geopf.fr/wfs/ows` — full PatriNat catalogue (`patrinat_znieff1`, `rnr`, `sic`, `zps`…) | 154/163 | Server-side `INTERSECTS` returns empty — do pip client-side. |
| **AU** | VIC DEECA PLM25 WFS `opendata.maps.vic.gov.au/geoserver/wfs` (CC BY 4.0) · QLD `spatial-gis.information.qld.gov.au/.../ParksTerrestrialProtectedAreas/MapServer/10` · NSW `mapprod3.environment.nsw.gov.au/.../EDP/Estate/MapServer/0` · WA SLIP `public-services.slip.wa.gov.au/.../Property_and_Planning/MapServer/15` (map service is *open*; only downloads need login; CC BY-NC) · CAPAD `gis.environment.gov.au/.../ogc_services/CAPAD/MapServer/0` | AU closed | No "state beach" tenure anywhere. NTWA covenants only in CAPAD, by exact number. |
| **NZ** | DOC PCL FeatureServer (CC BY 4.0) · Auckland Council Park_Extents `services1.arcgis.com/n4yPwebTjJCmXB6W/...` | — | ECan publishes no regional-park layer. |
| **ZA** | DFFE screening server `screening.environment.gov.za/.../OC_CV/Gazetted_Boundaries/MapServer/44` (SAPAD Q4 2025) | 4 | `dffeportal.environment.gov.za` has an **expired TLS cert** — not bypassed. |
| **GB** | Natural England AGOL `services.arcgis.com/JJzESW51TqeY9uat` (906 layers) · NatureScot WFS `ogc.nature.scot/geoserver/protectedareas/wfs` (OGL v3) | 3 + negatives | AONB layer has no section polygons (Bodmin Moor = Cornwall). |
| Others | GeoNB Socrata · SK PCAN · ICNF BDG · Azores SRAAC WFS · EELIS WFS · data.gouv.nc (NC) · Tokyo 緑のオープンデータ (CC BY per file, mainland only) | see CSV | |

## 4. Japan — how to finish it on the box
All 70 JP rows were `name_differs`: the box's candidates are its own romaji of A10_005 (中部山岳 → "chuubu sangaku"). `JP_A10_crosswalk.csv` gives the exact 漢字 key per row. Join `A10_005 = key` (and `A10_001` prefecture where two prefectures share a name — 多良岳 in 41 & 42), then pin-test. 23 already written as match, 21 as other (都市公園 / 県民の森 inside natural parks), 26 notes with keys. Tokyo mainland urban parks and 都民の森 are in the Tokyo shapefiles; the island parks (大島/多幸湾/羽伏浦/大神山) are not — ask 東京都建設局. Three names flagged unverified (join will simply miss if wrong).

## 5. Open items for the owner (decisions / emails — recorded in the CSV too)
- Licence decisions: **WA DBCA CC BY-NC 4.0**; **MX CONANP "cite the source"**.
- Email: Agrárminisztérium (HU) for the public WMS + reuse terms. Optional courtesy email to Tokyo 緑地景観課 (park files are CC BY; the PDF asks to be told when quoted).
- The 183 **NEEDS-PERSON** rows — mostly kind/piece differences; each note names the candidate and id.
- Box jobs still queued: JP join; PL GDOŚ WFS (Wełtyń); ES ENP_ES zip (6 regional parks are now answered via CDDA anyway); MX CONANP IDEFOR layer (11 rows); corrected pins from matched polygons.

## 6. Dead ends (don't retry)
Parks Canada NHS layer (none) · MX INAH (per-request) · Hungary vector data (ministry only) · catalogo-irig.madeira.gov.pt and ideserver.sma.gob.cl (won't load) · serverags1.economia.gob.mx (won't load in pane) · Oregon/ECan regional parks (not published) · BZ/DO/KE/PA/PY/LK/GA/GT/LR/SV/UY (no official GIS surfaced in 3 searches each) · GUGiK for Polish PAs (wrong agency; GDOŚ).

## 7. Rules we worked under (keep them)
Official agency data only · OSM/WDPA/Google/Wikipedia/hiking sites are leads, never sources · obey robots/bot-checks/logins (WA downloads, DBCA) · never bypass a cert error · nothing saved to the user's PC without asking · never take the bigger place (rule 5) · kind differences go to a person (rule 7) · if in doubt, NEEDS-PERSON.
