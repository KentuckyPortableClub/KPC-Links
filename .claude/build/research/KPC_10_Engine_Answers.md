# Answers for the outside coder (engine + finder), chat 10, Nov 1 2026

## 1. File shapes (real rows, Nov 1)

**`data/us-key/<area>.json`** (KPC-Data; Canada `data/ca-key/<area>.json` is the same shape, with `prov`)
```json
{"st": "TN", "note": "...", "counts": {...}, "nonum": [[objectid, name, designation, manager, acres], ...],
 "parks": {"US-0019": {"n": "Cumberland Gap National Historical Park", "t": "National Historical Park",
   "g": "official", "m": [[3197, "Cumberland Gap National Historical Park", 5365, "name"]],
   "c": [], "src": ["PAD-US"], "read": "2026-10-30", "pin_in_state": "VA"}}}
```
- `m` = joined records `[record id, record name, acres, how]`.
- `c` = records to check by hand (NOT joined).
- `g`:
  - `official` = has an official outline;
  - `approx`;
  - missing = pin only.
- The record id is the layer's OBJECTID. PAD-US for the US; CPCAD / the province layer for Canada (`data/ca-key/layers.json` lists the layers).

**`data/world-key/<CC>.json`** (KPC-Links)
```json
{"cc": "CH", "sources": [...12 layers...], "counts": {"parks": 319, "matched": 261, "check": ..., "pin_outside": ..., "saved_outlines": ...},
 "parks": {"CH-0001": {"n": "Schweizerischer National Park", "t": "National Park", "g": "approx",
   "gsrc": "EU compilation of national data", "m": [[114465, "Schweizerischer Nationalpark", "EEA nationally designated areas", "name"]], "c": []}}}
```
- NOTE: here `m[2]` is the SOURCE name, not acres.
- `g` is only written for approximate rows. A row with `m` and no `g` = matched to an official national layer.

**`data/docs/<area>.json`** (KPC-Data)
```json
{"area": "US-TN", "read": "...", "counts": {...},
 "parks": {"US-0019": {"n": "...", "t": "...", "page": "https://www.nps.gov/cuga/index.htm", "checked": "2026-10-29", "agency": "National Park Service",
   "map": {"url": ".../CUGAmap1-3.pdf", "status": "ok", "kind": "pdf", "names_park": true, "page": ".../maps.htm", "date": null, "date_label": "date unknown", "posted": "Dec 07, 2022", "via": "the agency site"},
   "rules": {"url": ".../lawsandpolicies.htm", "status": "ok"}, "runs": [], "handover": [], "notes": [], "ver": 7}}}
```
- "Has a map" = `map.status == "ok"`.

**`data/access/<area>.json`** (KPC-Data)
```json
{"st": "TN", "src": "...", "credits": [...], "read": {"US-11241": "2026-10-31"},
 "parks": {"US-11241": [[35.968087, -84.299134, "Parking (Tennessee Wildlife Resources Agency)", "name"],
                        [35.907255, -84.394567, "Boat ramp / launch: Gallaher (TWRA; all managers)", "place"]]}}
```
- Rows are `[lat, lon, label, how]`. `how` = `name` (tied by the layer's area name) or `place` (sits on the park's land).
- The agency = the label's last brackets, text before `;`. These are not agencies: `work in progress`, `n/a`, `KPC ...`, `just outside the line ...`.
- **Kentucky is different:** KPC-Links `kpc-ky-data.json` → `parks: [{c: ref, n, la, lo, ap: [[lat, lon, "KDFWR gate"], ...]}]`.
  - The agency is the first word: KDFWR = Kentucky Fish & Wildlife, NPS, Forest Service.
  - Labels starting `KPC` are club-made: not official.

**`data/campsites/<area>.json`** (KPC-Data)
```json
{"area": "US-TN", "inside": {"US-0019": [{"id": "TN-8b551e00f9", "name": "Baptist Gap Campsite", "kind": "campground", "lat": 36.56627, "lon": -83.72507,
     "agency": "state", "booking": "", "m_inside": 42, "outline": "name", "tier": "inside|at the edge", "sites": null, "notes": []}]},
 "nearby": {"US-0019": [{"id": "...", "name": "...", "kind": "campground", "miles": 2.3}]},
 "dayuse": [{"id": "232556", "name": "Cook Day Use Area", "kind": "day-use shelter / picnic area", "agency": "USACE", "booking": "https://www.recreation.gov/...", "park": null}],
 "both": [{"name": "...", "parks": ["US-12361", "US-2945"], "patch_id": "...", "patch_acres": 1137.5, "notice": "⚠️ Parks' boundaries may overlap here ..."}],
 "dispersed": {}, "check_first": [...], "disagree": [...], "merged": [...], "counts": {...}}
```
- The facts for each campground (season, fees, hookups, rules ...) are in `data/campinfo/<area>.json` → `camps: [ {name, lat, lon, kind, season, sites, fees, reservable, booking:{url}, phone, hookups:{...}, rules:{fires, generators, pets, quiet_hours, stay_limit}, ...} ]`.

**`data/parkinfo/CA.json`** (KPC-Data; the US files are `data/parkinfo/US-XX.json`, same row shape, without column 10)
```json
{"program": "CA", "sites": {...},
 "parks": {"CA-0001": ["Alaksen National Wildlife Area", "https://www.canada.ca/...alaksen.html", "National Wildlife Area",
                       "Automobile,Pedestrian", "Automobile,Foot", 49.1013, -123.173, 10, 12, 354, "BC"]}}
```
- Columns:
  - 0 name, 1 website, 2 type;
  - 3-4 access modes;
  - 5 lat, 6 lon;
  - 7-9 activation numbers;
  - 10 province (Canada only).
- There is NO `US-KY` file (see Kentucky above). World pins: `data/pota/t/<lat>_<lon>.json` → `[[ref, name, lat, lon], ...]`.

## 2. World coverage (world key, matched / POTA parks, Nov 1)
- **Keyed, 28 countries:**

  | country | matched / parks |
  |---|---|
  | FR | 13102/14367 |
  | AU | 7245/10272 |
  | GB | 3288/7074 |
  | NO | 3044/3337 |
  | PL | 2691/2982 |
  | SE | 2016/2224 |
  | IT | 1919/2167 |
  | ES | 1789/2497 |
  | FI | 1592/1838 |
  | DE | 683/1265 |
  | HR | 366/381 |
  | RO | 305/1334 |
  | AT | 273/420 |
  | CH | 261/319 |
  | PT | 223/410 |
  | CZ | 193/232 |
  | JP | 185/1217 |
  | BE | 164/593 |
  | SI | 137/1181 |
  | DK | 106/291 |
  | IE | 96/307 |
  | SK | 83/352 |
  | NL | 81/312 |
  | EE | 72/155 |
  | LU | 45/53 |
  | LT | 28/38 |
  | HU | 23/244 |
  | LV | 7/14 |

  In EU / EEA countries, many matches are the EU compilation (`g: approx`, "EU compilation of national data"), NOT the national agency's layer: replace them when a national layer is found.
- **Approved world layers waiting to draw** (in `data/world-key/extra-layers.json`): AU, AT, GB, IT, ZA, CO, CL and others. CO / ZA / CL are not built into the key yet.
- **No official layer found yet** (world finder stage 1, most open parks first): RU 7933, CN 1845, KR 1287, JP 1032 more, NZ 907, TH 858, BR 813, MX 534, TR 467, AR 390, GR 293, CU 283, PH 264, RS 243, MD 232, BG 212, DO 200, IN 195, BA 192, CY 151, TT 147, BY 141, MY 122, MK 116, IS 116. In all, 202 countries have no layer and no candidate.
- **Blocked / not usable:**
  - Spain's INSPIRE service answered 403 to your box. Try from GitHub.
  - tnstateparks.com and tn.gov refuse an honest bot name: they go to browser or hand work.
  - Sign-in ("Token Required") layers are never used.
  - **NEVER:** WDPA / Protected Planet, OpenStreetMap, Google, AllTrails, Wikidata geometry.

## 3. World stages
The same as `kpc_order.py`. W1-W10 = **GB, AU, JP, DE, PL, FR, ES, IT, NO, NL**. Before them come US + Canada, then North America (the `NA` set: MX, Central America, the Caribbean, GL, PM, BM ...). After them comes the rest by activity.

## 4. Output
**Not** KPC-Links and **not** a pull request.
- Write everything inside `--out`, in the SAME file shapes as above (and the question-row shape below).
- Chat 10 runs it on GitHub with `--out` on the KPC-Data side branch `tools-out` (`engine/<kind>/`). Chat 10's workflow then copies each kind's final file into KPC-Data main and puts it in the waiting room, where chat 11 grades it.
- **Question rows** (for outlines / layers, the shape of `data/waiting/questions/layers.json`): `{ref, st, url, name_field, agency, kind, licence, answer: "", checked_by: ""}`, plus your evidence fields (record where clause, `pin_m`, acres, names, tier / band, rule R-G12 / R-G13, notes standard fields).
- **Files:** JSON, UTF-8, no geometry stored except small envelopes, or the simplified 3 m outline only where the spec says so.

## 5. Where it runs
- **Platform:** GitHub Actions in the KPC-Data repo (public, so minutes are free), `ubuntu-latest`, **Python 3.12**.
- **Runs:** scheduled nightly by chat 10's workflow; each job runs up to 50-55 min, exits 3, and the next job resumes (`--resume`).
- **Parallel:** split with `kpc_shard` into up to 8 jobs.
- **Libraries:** pip packages are fine (shapely, pyproj, openpyxl, pypdf, rapidfuzz ...); keep `requirements.txt` short.
- **Browser:** Playwright Chromium is installed by the workflow when the plug-in needs it (`python -m playwright install --with-deps chromium`).
- **Network:** open internet from GitHub. The club's chat sessions are blocked from many sites, so all reading happens on GitHub.
- **Cache:** kept between runs with the Actions cache.
- **Contact for the User-Agent:** env `KPC_CONTACT`.
