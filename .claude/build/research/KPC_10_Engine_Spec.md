# The "do it all" park-info engine: build spec (chat 10, Nov 1 2026)

Brandon, Nov 1 12:06 AM: "would like me to build send me instructions". This follows his outside research method (`outside-methods/`: KPC_method_updated.md, KPC_research_tips_GIS_and_info.md, FINDINGS_LOG_Canada_HardLook.md).

Builder: the outside coder. Folder `kpc_engine/`. It follows the KPC install contract (PART A of `KPC_10_Outside_Tools_Specs.md`). Chat 10 installs and wires it.

**One engine, small plug-ins.** The engine finds out what we are missing, groups the work by agency, reads the sites the same polite way every time, keeps the shared findings log, runs 8 workers, and does a second pass on the leftovers. Each kind of information is a PLUG-IN with its own rules, its own output and its own grader, so one NO or one crash never stops the others.

It **decides nothing for the site.** Every plug-in's results go through the waiting room to chat 11 (kind = the plug-in name), exactly as today's bots do.

---

## PART 1. RULE SHEET (rules already in force; nothing new is decided here)

- **Official sources only:** the managing agency, the government, or the real operator. Never OSM, Google, AllTrails, TripAdvisor, Yelp, blogs, Wikipedia, directories, resellers, WDPA, or search snippets.
- **Every link written must open.** Never guess a URL. The page title must name the park.
- **Text is copied word for word,** in the original language. Never turn prices into a range yourself.
- **Standard wording:** `not stated on the agency page`, `no fee`, `open all year, no hours stated`.
- **Blocked is not "not found".** These are logged as BLOCKED with the reason and retried later:
  - TLS failures;
  - Cloudflare / robot challenges;
  - token-only services;
  - robots.txt refusals.

  We never spoof a User-Agent, never click through certificate warnings, never sign in, never get around a robot check, and never use an access token found inside a public web map.
- **SCOPE (Brandon Oct 29 / Oct 30):**
  - Hours, fees and closures plug-ins run for **KENTUCKY ONLY.** The engine refuses to give them a non-KY row.
  - Outlines, maps / documents, parking, trails and camping run for the US + Canada. Outlines and maps also run for the world, in the club's order.
- **POTA pins never move.** R-G12 (a pin within 150 m of a named official record = a candidate) and R-G13 (a POTA pin typo confirmed by an official point: use the outline and list the typo) apply to the outline plug-in.
- **Order of work:** US + Canada first, then the rest of North America, then world stages W1-W10, then the rest (`kpc_order.rank`).

---

## PART 2. THE MISSING LIST (`kpc_engine gaps`)

Every night, build ONE file: what each park is missing, per kind, from the club's own files.

| kind | missing when | club file (read-only) |
|---|---|---|
| `outline` | the key row's `g` is not `official` | KPC-Data `data/us-key/<area>.json`, `data/ca-key/<area>.json`; KPC-Links `data/world-key/<CC>.json`; Kentucky: KPC-Links `data/ky-answer-key.json` (a park with `tracts` is outlined) |
| `map` | no `map` with `status: ok` | `data/docs/<area>.json` `parks[ref].map` |
| `page` | no official `page` | `data/docs/<area>.json` `parks[ref].page` |
| `parking` | no points | `data/access/<area>.json` `parks[ref]` (rows `[lat, lon, label, how]`); Kentucky: KPC-Links `kpc-ky-data.json` `parks[].ap` |
| `camping` | a park with camping words on its page but no campground row | `data/campsites/<area>.json`, `data/campfed`, `data/campstate`, `data/campstate-manual` |
| `trail` (trail parks only) | no official line | `data/trails/` + the trail-line files |
| `hours`, `fees` (KY only) | empty fields | `data/hours/US-KY.json` `parks[ref]` |
| `closures` (KY only) | no source checked in 7 days | `data/closures/US-KY.json` + `sources.json` |

- **Park list:**
  - the POTA pins: `data/parkinfo/<area>.json` rows `[name, web, type, ..., lat, lon, ...]`; Canada is `data/parkinfo/CA.json` with column 10 = province;
  - Kentucky from `kpc-ky-data.json`;
  - the world from `data/pota/t/*.json` tiles.
- **Shapes:** the shapes above are what chat 10 knows today. Read them through ONE adapter module (`adapters.py`) so chat 10 can fix a field name in one place.
- **Output:** `gaps.json` → `{area: {ref: {kinds: [..], agency, why_not: {kind: tag}}}}`, plus `gaps-summary.md` (per area and kind: parks, missing, solved since last night).
- **Agency of each park:**
  - the key record's manager, else the park's own web domain, else the type word;
  - it is the GROUP every plug-in works by (method §2: "biggest agencies first; one agency-wide page often covers hundreds of parks").

---

## PART 3. THE SHARED ENGINE (`kpc_engine/core/`)

1. **`polite.py`:** reuse the coder's `_common/polite.py`.
   - robots.txt obeyed; a robots.txt that answers 403 = no rules.
   - ArcGIS REST / sharing/rest are exempt on arcgis.com.
   - 2 s per host. 429 / 5xx = 30 / 60 / 120 s. Three strikes = a day's rest.
   - An honest User-Agent naming the club site.
   - A disk cache with read dates.
2. **`read.py`, the escalation ladder** (method §4):
   1. a plain fetch;
   2. a structured data file behind the page, when one is known (e.g. NPS `https://www.nps.gov/<code>/structured_data_<code>.json`);
   3. the headless browser (Playwright, Chromium), for script-filled pages;
   4. still blocked → `blocked.csv` (domain, ref, kind, reason, date) and retried at the end of the run, and on the next nights.
3. **`agencies.py`:**
   - Groups the gap rows by agency, biggest first.
   - Keeps `agencies.json`: per agency the server roots, folders, portal search address, page pattern and "agency-wide page" links, re-read after 30 days.
   - Seeded from the Agency Atlas files (KPC-Links `.claude/build/research/agency-atlas/<area>.md`).
4. **`findings.py`, the shared findings log** (method §10, "pass a good trick sideways"):
   - One append-only `findings.jsonl` that every worker reads at the start and writes to the moment it learns something reusable. Examples:
     - `{agency, kind: "name-field", value: "REMARKS"}`;
     - `{host, kind: "renumbered", old: "/1", new: "/193"}`;
     - `{agency, kind: "agency-wide-page", url}`.
   - Every plug-in looks up its agency's findings before working.
   - Seed it from FINDINGS_LOG_Canada_HardLook.md (by hand, once; chat 10 helps).
5. **`notes.py`, the notes standard** (method §10). Every result row carries:
   - `where_looked`: each source and what it gave (hit / no hit / points only / blocked);
   - `solved`: e.g. `PIN OFF: lat,lon, km, source`, `NAME SOLVED: agency calls it X`, `WRONG KIND: lighthouse`;
   - `why_this_record`: name, distance, size, the confirming page;
   - `confidence`: sure / likely / weak, plus what a checker should double-check.
6. **`passes.py`, two passes** (method §11):
   - PASS 1 on every gap;
   - PASS 2 only on the NOT FOUND + weak rows, with every finding learned in pass 1.
   - It records which pass solved each row.
7. **`workers.py`:** splits the agency groups into 8 parts (the sweet spot: more hits the same government servers). Each part writes its own results and saves every 25-50 rows, so it can resume. Built to run under `kpc_shard` (AREAS from the environment, `parts/<i>/`, a join).
8. **`checks.py`, quality** (method §6):
   - every URL written opens;
   - identity columns are compared with the club's files (0 mismatches);
   - boilerplate and other-site text are caught;
   - 20 random rows go in a `spot-check.md` for chat 11.

---

## PART 4. PLUG-INS (each one small, its own rules, its own output)

A plug-in is a module with:
- `KIND`;
- `wants(gap_row) → bool`, which refuses rows outside its scope;
- `work(agency_group, engine) → results`;
- `write(results, out_dir)`, in the SAME file shape the club's current bot writes, so the waiting room checks it with no change.

| plug-in | job | reuse (call as a library, don't copy) | output shape (club file) |
|---|---|---|---|
| `outline` | the new finder (KPC_10_Finder3_Spec.md, ladder L0-L5) | `kpc_gis_finders`, `kpc_inspire`, `kpc_convert_layers`, `kpc_parcels` / `kpc_parcel_trace`, `kpc_map_match` | questions in `data/waiting/questions/layers.json` row shape |
| `map` + `page` | the official park page + its own map (PDF / image / map page) | `kpc_sitemaps`, `kpc_map_links`; picture maps → the picture-map saver | `docs-found-*.json` shape `{ref: {st, page, map, map_page, kind, date, agency, notes}}` (the documents merge reads it) |
| `parking` | official parking / entrance / trailhead / boat-ramp points | the access bot's layer list (`data/access-layers.json`) | `data/access/<area>.json` rows `[lat, lon, label, how]`, agency in the label's brackets |
| `camping` | official campgrounds per park | `kpc_camp_layers` | its `campgrounds/<area>.json` + `dayuse/<area>.json` |
| `trail` | official trail lines | `kpc_trail_lines` | its output shape |
| `hours` / `fees` (KY ONLY) | word-for-word hours / fees from the agency page | the method's NPS structured-data trick | `data/hours/US-KY.json` shape |
| `closures` (KY ONLY) | official closure notices | today's closures sources (`data/closures/sources.json`) | `data/closures/US-KY.json` shape |

Also:
- **Pin typos found by any plug-in** go to `pin-typos.json` (R-G13), never to a pin change.
- **Bad source links** (the POTA website link dead / moved / mistyped) go to `fixes.csv` ("link wrong/dead; correct official page: <URL>"). The club's data is never edited.

---

## PART 5. OUT, BOARD, WIRING

- **Outputs:** everything on KPC-Data branch `tools-out`, folder `engine/<kind>/` (BRANCH FIRST).
  - Chat 10's wiring copies each plug-in's final file to its usual place and diverts it into the waiting room (kind = plug-in).
  - A plug-in that passes chat 11 three times in a row then releases by itself (the trusted rule), with chat 11's 1-in-10 sample.
- **ONE board file:** `engine/board.md`, per kind and per state:
  - missing yesterday → found today → still missing, with the top why-not tags;
  - blocked hosts;
  - pass 1 vs pass 2 solves.

  Chat 10 posts its one-line summary on the status board.
- **Exit codes:**
  - `0` = done;
  - `3` = time ran out (`--resume`);
  - never fails for one bad site or row.

## Acceptance
- **Areas:** US-KY (every kind), US-TN, US-RI, CA-ON, and for outline + map only, CH.
- **It sees what we have:** 0 gaps reported for things the club files already hold (the gap list is tested against the files).
- **It finds more:**
  - outline: the finder's own bar;
  - map / page: at least 20% of the missing KY + TN parks get an official page or map, every link opens and names the park;
  - parking: new points in at least 10% of the KY + TN parks without any;
  - camping: the camp-layers bar.
- **Scope:** a non-KY row never reaches hours / fees / closures (test with a grep).
- **Manners:**
  - never more than 2 workers on one agency host at once;
  - every blocked host is in `blocked.csv` with a reason;
  - no NOT FOUND for an unread page.
- **Pass 2** solves part of pass 1's NOT FOUND, and the report shows how many.
- **Time:** a US state, all kinds, in one 50-minute run from an empty cache, or it resumes cleanly.

## How chat 10 wires it
1. It runs nightly (kpc-sharded, 8 groups): the gap list first, then the plug-ins.
2. **Switch-over:** each existing bot is switched to its plug-in ONE AT A TIME. A comparison run comes first (same area, old vs new). Then chat 11 grades it. Only after that is the old bot retired.
   - Order: documents → parking → camping → outline (after Nov 6) → KY hours / fees / closures last (they are live and proven today).
3. No chat feeds it by hand. New outside research files on intake-files are read by the plug-in of that kind (the intake reader) and added to the findings / agencies files.
