# Eight tools for the outside coder (chat 10, Oct 31 2026)

Brandon, Oct 31 5:57 PM: "all of them ... give great instructions to make it easy for you to install".
Who reads this: the outside coder who builds the tools. Chat 10 wires them. Fable reviews them.
Build order (best payoff first): **T1, T2, T5**, then T3, T4, T6, T7, T8.

---

## PART A. The install contract (the same for all eight tools; please follow it exactly)

If a tool follows this part, chat 10 can install it in about 15 minutes with no changes to your code.

1. **One folder per tool**, named as in its section: `kpc_<name>/` holding
   - `kpc_<name>.py` (one file is best),
   - `requirements.txt` with pinned versions (Python 3.12; no apt packages; Playwright allowed),
   - `README.md` (half a page: what it does, how to run it, one example),
   - `tests/` (a tiny sample input plus the expected output; `python kpc_<name>.py --selftest` runs it with no network and prints PASS or FAIL).
2. **Command line, the same everywhere**:
   - `--in <file>` (or the named inputs in the tool's section)
   - `--out <dir>`
   - `--max-minutes 50`: it stops starting new work after this, because GitHub jobs are 55 minutes.
   - `--resume`: skip what `<out>/state.json` says is done.
   - `--limit N`: only the first N items, for tests.
   - `--areas US-KY,US-TN`: where it makes sense.
3. **Exit codes**:
   - `0` = all done
   - `3` = time ran out and work is left (chat 10's workflow starts the next run)
   - anything else = a real crash.

   Never exit non-zero for a single bad item: write it to the report with a reason and go on.
4. **Writes only inside `--out`.** It must never edit the club's data files: it writes NEW files and the club's own scripts merge them.
5. **Manners on the open web**:
   - **Robots:** obey robots.txt.
   - **Speed:** at most 1 request every 2 seconds per host.
   - **Who we are:** send the User-Agent `KPC park tools (<KPC_CONTACT>)`, where `KPC_CONTACT` is an environment variable.
   - **Back off:** on 429 / 503, wait and retry 3 times, then mark the host "resting" for the run.
   - **Caching:** a download cache folder (`--cache`) may be kept between runs.
6. **Sources never used, as code, in every tool**:
   - OpenStreetMap / Overpass / Geofabrik
   - Google Maps / My Maps / Google tiles
   - AllTrails, Gaia, Strava, TripAdvisor, Yelp, Wikipedia
   - Protected Planet / WDPA / UNEP-WCMC

   A government's own file on cloud storage (storage.googleapis.com, S3, Azure blob) IS allowed when the government's own page links to it.
7. **No keys or passwords.** Use only open public endpoints. If a source needs a sign-in or a token, write "needs sign-in" and skip it.
8. **Every output row says where it came from and when**: `source_url`, `read_date` (YYYY-MM-DD), and a short `why` in plain English.
9. **It decides nothing for people.** Tools write candidates and scores. The club's rules decide; a person grades. Never write YES / NO into a club file.
10. **Small outputs.** Pictures are JPEG, longest side ≤ 1600 px, quality ≤ 70. No file over 20 MB. Big working files go in `--out/work/` (chat 10 keeps that on a side branch).

### Club file shapes the tools read

- **Park pins.** `data/parkinfo/US-XX.json` → `{"parks": {"US-1234": [name, website, type, access, access2, lat, lon, ...]}}`. Canada is `data/parkinfo/CA.json` (column 10 = province). The world is `data/pota/t/*.json` (rows `[ref, name, lat, lon]`).
- **Questions for chat 11.** `data/waiting/questions/layers.json` → `{"questions": [{ref, park, tier, record, record_name, layer, record_link, acres_approx, answer, ...}]}`. Other question files in the same folder have the same row shape.
- **Picture maps.** Branch `picture-maps`: `maps/<ref>_<short-name>.jpg` + `index.json` → `{"maps": [{ref, name, agency, source_url, page, files, date}]}`.
- **Official documents.** `data/docs/US-XX.json` → `{"parks": {ref: {"n", "page", "map": {url, status, kind, names_park, date, ...}}}}`.
- **2-fer rows.** `data/fers/US-XX.json` (see `.github/scripts/tools/kpc_fers_check/README.md`).
- **Keys.** `data/us-key/US-XX.json` → `{"parks": {ref: {"g": "official" | "approximate" | "pin", "m": [[record id, name, acres, how], ...], "src": [...]}}}`.

---

## T1. Map-match second opinion (`kpc_map_match/`): takes the most load off chat 11

**Job.** For every open question ("is this official record that park?"), score how well the candidate outline matches the park, so the plain cases can be answered by the club's rules and only the unclear ones reach a person.

**In.**
- `--questions data/waiting/questions/*.json` (open rows only)
- the park pins
- the picture-maps index (when a park has a saved agency map)
- `--docs data/docs/*.json` (the agency map link)

**What it measures for each row.**
1. Fetch the candidate record's polygon from `layer` + `record`, using the ArcGIS `query?objectIds=` with `returnGeometry=true` and `outSR=4326`, simplified to 3 m.
2. **Pin.** Is the POTA pin inside it? If not, how far away is it, in metres?
3. **Size.** The record's acres compared with any acres the park's own page or POTA states (read them from the agency page text when they are there).
4. **Name.** A name-similarity score (0-1) between the park name and the record name and the record's other text fields (unit name, alias, designation).
5. **Agency map.** If a picture map or agency PDF map exists:
   - draw the outline on the satellite tile around the pin;
   - put the agency map page next to it;
   - write one side-by-side JPEG.
6. **Fit.** If the agency map is georeferenced (GeoPDF, or has a world file), compute the polygon overlap (intersection over union).
7. **Neighbours.** Find records of the same layer within 2 km whose name matches the park better, and flag them as "better record nearby".

**Out.** `<out>/map_match.json` → `{ref|record: {pin_inside, pin_dist_m, acres_record, acres_park, acres_ratio, name_score, iou, better_nearby: [...], picture: "<file>.jpg", band: "STRONG" | "WEAK" | "CONFLICT", why}}` + the JPEGs.

**Bands.**
- STRONG = pin inside, name_score ≥ 0.85, acres within ×2 (or no acres to compare), no better record nearby.
- CONFLICT = the pin is outside, or the acres are off by ×10, or a better record is nearby.
- WEAK = everything else.

**Test.** 20 rows chat 11 already answered (10 YES, 10 NO from `layers.json`): STRONG must contain no NO, and CONFLICT must contain no YES.

**Acceptance.** On 200 answered rows, STRONG agrees with chat 11's YES ≥ 97%, and CONFLICT agrees with NO ≥ 95%.

---

## T2. Dead-link fixer (`kpc_link_fix/`)

**Job.** When an official map or page link answers 404 / 410 / a "page not found" page, find the same document on the same agency's site at its new address.

**In.** `--links <file>`, a list of `{ref, url, kind: "map"|"page", agency_host?}`. Chat 10 builds it from:
- docs rows whose map status is `HTTP 404` / `HTTP 410`;
- failed save-map requests;
- chat 8's dead lists.

**How.**
1. Same file name: search the agency host's sitemap.xml (T3) for the same file name, or the same name without dates and version numbers.
2. The site's own search page, if it has one (most state sites: `/search?q=`).
3. The Wayback Machine (web.archive.org): **only to read the OLD page's title and words** so they can be searched for on the live site. Never return an archive.org link as the answer.
4. The parent folder or page (`.../maps/` from `.../maps/x.pdf`), read for a link with the same title words.

**Out.** `<out>/link_fix.json` → `{old_url: {new_url | null, how: "sitemap same name" | "site search" | "parent page" | ..., confidence: 0-1, checked: date, opens: true, names_park: true|false}}`.

The new link must open (HTTP 200) and the PDF's first page or the page text must name the park. Otherwise `new_url` = null with the reason.

**Test.** The three dead trail maps chat 8 found on Oct 31:
- US-2350 Prairie Spirit (ksoutdoors.com)
- US-7836 Ozark Trail (mostateparks.com)
- US-9753 Rock Island Corridor (mostateparks.com)

**Acceptance.** It fixes ≥ 1 of the 3, and it never returns a link that does not name the park.

---

## T3. Agency sitemap reader (`kpc_sitemaps/`)

**Job.** Read each agency's own sitemap(s) and list every map PDF / map image / park page on the site, much faster than crawling.

**In.** `--agencies data/intake/us-agency-maps-index.csv` (166 rows: agency, state, url) plus the hosts in `data/docs/*.json` map links. Canada and the world come later with the same shape.

**How.**
1. `robots.txt` → its `Sitemap:` lines, else `/sitemap.xml`, `/sitemap_index.xml`, `/wp-sitemap.xml`. Follow sitemap indexes. Gzip allowed.
2. Keep the URLs whose path or file name says map / brochure / guide / trail / boundary / atlas / .pdf / .jpg / .png, plus the "park page" URLs (the paths the agency uses for parks, learned from the docs links on that host).
3. Match each URL to POTA parks by name words in the path / file name, against the park list of that state. Keep **all** candidates; do not pick one.

**Out.** `<out>/sitemaps/<host>.json` → `{host, read_date, n_urls, maps: [{url, lastmod, refs: [{ref, score}], words}], pages: [...]}`.

**Test.** Tennessee: tnstateparks.com + tn.gov/twra.

**Acceptance.** It lists ≥ 50 Tennessee park map files, and ≥ 80% of the Tennessee map links already in `data/docs/US-TN.json` appear in its list.

---

## T4. County land-owner finder (`kpc_parcels/`)

**Job.** For parks with no official park layer (city, county, small state sites), find the county's land-ownership (parcel) map and say who owns the land under the POTA pin, so the club's ownership rule (R-G7) can work.

**In.**
- `--parks <file>` = `[{ref, name, lat, lon, county_fips?}]` (chat 10 builds it: parks with `g: pin` in the keys, US first).
- `--known data/intake/parcel-layers.json` (may be empty): `{county_fips: layer_url}`.

**How.**
1. **County from the pin:** the Census TIGERweb county layer (a point query).
2. **Find that county's parcel layer:** the state's open-data portal search, the state's parcel service (many states have one statewide, e.g. TX StratMap, NC, FL, WI, MN, OH), the county's own ArcGIS server root, then ArcGIS Hub search with the county name + "parcels". **Only government hosts.**
3. **Owner under the pin:** a point query (send the JSON point form AND `where=1=1` if the plain form fails; Texas needs this). Return the owner name, parcel id and acres, plus the parcels that share the same owner name within 1 km. Those are the park's other pieces.
4. **Owner type:** classify the owner as `government (city / county / state / federal / school / utility)`, `private` or `unknown`, by keywords ("CITY OF", "COUNTY", "STATE OF", "COMMONWEALTH", "UNITED STATES", "PARKS", "DNR", ...).

**Out.**
- `<out>/parcels.json` → `{ref: {county, layer_url, owner, owner_type, parcel_id, acres, same_owner_parcels: [{parcel_id, acres, dist_m}], why}}`
- `<out>/parcel-layers.json` = the layers it found, which chat 10 keeps for next time.

**Test.** 10 Kentucky city parks + 10 Texas Historical Commission sites.

**Acceptance.** It finds a parcel layer for ≥ 70% of the counties and has no private owner on a known government park.

---

## T5. Site checker robot (`kpc_site_check/`): replaces chat 11's hand card checks

**Job.** Every week, open the club's map tools like a person on a phone, for a sample of parks, and report what a visitor sees.

**In.**
- `--site https://kentuckyportableclub.github.io/KPC-Links/`
- `--sample <file>` = `[{ref, expect: "official" | "approximate" | "pin", fers: [ref,...]}]` (chat 10 builds it from the keys: 10 official, 10 approximate, 10 pin, 10 with 2-fers; Kentucky + 3 other states + 2 Canada + 2 world).

**How.** Playwright, at a phone screen size (390×844) and a desktop size (1280×900). Before the pages load, set `navigator.webdriver = false`, so it sees the guest view the public sees.
- **US Trip Planner** (`kpc-planner-us.html`):
  1. type the ref in `#usq`;
  2. click the first suggestion (`.kps-box button[data-i="0"]`);
  3. click the park's row (`a.ref` with the ref text);
  4. click the button INSIDE the open card (`.leaflet-popup-content [data-a="bound"]`);
  5. wait up to 15 s;
  6. read the card text and `#us-status`;
  7. take a screenshot.
- **Overlap Finder, Kit, Park Info, Am I in the Park:** a similar recipe for each. Chat 10 will add the selectors to `tests/recipes.json`; please make the recipes data, not code.
- **Checks:**
  - an outline is drawn (the leaflet SVG path count goes up);
  - the label matches `expect` (Official / Approximate / Pin only);
  - for 2-fer parks, the short 2-fer line is present word for word: "⚠️ Parks' boundaries may overlap here, but we can't confirm it. Check both official boundary maps and make your own call before you count it.";
  - the information notice is present on the page;
  - the card fits the phone screen (it is not cut off, and there is no sideways scroll);
  - the browser console shows no errors.

**Out.** `<out>/site_check.json` → `{ref: {tool, device, outline_drawn, label, label_ok, fers_line_ok, notice_ok, fits_phone, console_errors: [...], screenshot}}`, plus a one-page `summary.md` with the failures first.

**Acceptance.** It runs against the live site in under 30 minutes for 40 parks × 2 devices. On a test where a label is wrong on purpose (a local copy with one edited key), it flags it.

---

## T6. Europe map-catalogue finder, INSPIRE CSW (`kpc_inspire/`)

**Job.** Every EU / EEA country publishes its official map layers in an INSPIRE catalogue (CSW). Search them for "protected sites" layers (INSPIRE theme PS) and return the country agencies' own WFS / ArcGIS / download links. One tool covers about 30 countries.

**In.** `--countries AT,BE,...` (default: the EU 27 + NO, IS, LI, CH, GB).

**How.**
1. The EU INSPIRE Geoportal CSW, plus each country's own national CSW (the list is in the Geoportal).
2. `GetRecords` filtered on the Protected Sites theme / keywords (protected sites, Schutzgebiete, aires protégées, espacios protegidos, aree protette, rezerwat, natura, national park, nature reserve, in the country's language).
3. From each record: the service links (WFS GetCapabilities, OGC API, ArcGIS REST, download), the publisher, the licence, and the date.
4. Open each link once: does it answer, and which layers / feature types does it list?

**Out.** `<out>/inspire.json` → `{cc: [{title, publisher, licence, date, links: [{url, kind: "wfs"|"ogcapi"|"arcgis"|"download", opens, layers: [...]}]}]}`.

**Rules.**
- The EEA's own EU-wide compilation (Natura 2000 / CDDA) is NOT a country source. List it apart as `eu_compilation: true`.
- Never Protected Planet.

**Test.** Austria, Germany, Spain.

**Acceptance.** It finds each one's national or state protected-area WFS.

---

## T7. Sharp trail lines (`kpc_trail_lines/`)

**Job.** The 31 national scenic / historic trails are saved about 80 m off. The club's 100-foot trail rule needs lines within 3 m (R-G6).

**In.**
- `--trails <file>` = `[{ref, name, source_url}]` (chat 10 builds it from `kpc_us_trails.py`'s list: the NPS / USFS / BLM national trail layers).
- the state trail layers in `data/state-gis.json`.

**How.**
1. Read each trail's official line at full detail: ArcGIS query `maxAllowableOffset` ≤ 0.00003, `geometryPrecision` 6, with paging.
2. Keep the route attributes: land route / water route, segment status (certified, high-potential, auto tour).
3. Simplify to 3 m in a local metric projection.
4. Save one file per trail per state.

**Out.** `<out>/trails/<ref>/<ST>.geojson` (properties: name, route_type, segment, source_url, read_date) + `<out>/trails/index.json`.

**Acceptance.**
- The Appalachian Trail across Virginia matches the official line within 3 m at 20 random points.
- The water-route segments of Lewis and Clark and Trail of Tears are labelled `route_type: water`.

---

## T8. Canada outline sharpener (`kpc_ca_sharpen/`)

**Job.** 273 Canadian park outlines are saved at coarse detail (hundreds of metres; Fable review #10). Re-read each one from its official source at ≤ 3 m, or say why it can't be done.

**In.** `--parks <file>` = `[{ref, layer_url, record_id, current_detail_m}]` (chat 10 builds it from `data/canada-bounds` files with no `detail_m` or `detail_m > 5`).

**How.**
1. **Re-read the record:** ArcGIS `objectIds` query with `maxAllowableOffset` 0.00003; if the server refuses, step to 0.00005 and stop there (never coarser than 5 m).
2. **Too big:** for a very big park, use the same cap rule as the world bot (Brandon Oct 31): every piece at 3 m if it fits 1,500 points, else coarser steps, with the detail written on it.
3. **Download-only:** for BC local / regional parks and Québec ZEC, which come from downloads, read the province's open-data download (BC Data Catalogue WFS, Données Québec) instead.

**Out.** `<out>/canada/<ref>.json` → `{ref, rings, detail_m, source_url, read_date, why}`.

**Acceptance.** ≥ 200 of the 273 come back at ≤ 5 m, and CA-2242 (12 points today) comes back with its real shape.

---

## PART B. How chat 10 installs each tool (for the coder's information)

Same steps every time:
1. Copy the folder into KPC-Data `.github/scripts/tools/`.
2. Run its `--selftest`.
3. Run a 10-item test.
4. Add one never-red workflow. It follows the house patterns:
   - `--max-minutes 50` with chaining on exit 3;
   - outputs on the side branch `tools-out` when they are big;
   - club files are changed only through the waiting room;
   - questions go to chat 11;
   - one status-board line per run.
5. Fable reviews.

Delivery: put each finished folder in KPC-Data `.github/scripts/draft/tools/<folder>/` (as before), with its `TEST_REPORT.md` showing the acceptance numbers.
