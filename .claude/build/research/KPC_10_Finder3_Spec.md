# One boundary finder for the whole world: build spec (chat 10, Oct 31 2026)

Brandon, Oct 31 11:41 PM: "the gis hunter and world harvester give me instruction on building one".

Builder: the outside coder. Folder `kpc_finder/`. It follows the KPC install contract (PART A of `KPC_10_Outside_Tools_Specs.md`).

**THE FREEZE.** Our GIS hunter and world finder stay untouched until Fable's Nov 6 review. This tool is built ALONGSIDE them and run side by side on the `tools-out` branch. It replaces them only after Nov 6, and only if it beats them on the same areas (see Acceptance) and Brandon says GO.

## Why a new one

Today we have three bots that each do part of the job:

| bot | where | what it does |
|---|---|---|
| GIS hunter | US + Canada | step A: asks the layers we already know, at the pins. Step B: ONE ArcGIS Online search per park (thin: Fable's audit). |
| World finder | rest of the world | the same step A, plus a ladder of finders (agency servers, ArcGIS orgs, catalogs, local-language search) |
| World harvester | rest of the world | the older country-by-country lead gatherer, still feeding `leads-<CC>.json` |

On top of those, separate tools now do pieces of the job well:
- the portal search (`kpc_gis_finders.py`);
- the INSPIRE reader (`kpc_inspire`);
- the map-page link finder (`kpc_sitemaps` / `kpc_map_links`);
- the map-format converter (`kpc_convert_layers`);
- the county parcels finder + tracer (`kpc_parcels`, `kpc_parcel_trace`);
- the map-match scorer (`kpc_map_match`).

**One finder** that walks every park with no official outline through the SAME ladder everywhere, calls those tools instead of copying them, and works by AGENCY (not park by park) will find more, faster, and leave one clear why-not reason per park.

---

## PART 1. RULE SHEET (the existing Rule G + Fable's habits; nothing new is decided)

**1. What counts as a find.**
- An OFFICIAL layer or file is one whose publisher is the government agency that manages the park (or the national / state mapping agency):
  - the agency's own domain (`.gov`, `.gc.ca`, `gov.xx`, `.gouv.fr`, …);
  - its verified ArcGIS organisation;
  - its official open-data portal;
  - the EU INSPIRE service of the country.
- The polygon (or line, for trails) must hold the POTA pin, or for lines lie within 200 m of it.
- It passes the name tiers T-1..T-6 (the collector's tiers).

**2. What does not count:**
- OpenStreetMap, Google, AllTrails, WDPA / Protected Planet, Wikipedia / Wikidata geometry, club or hobby maps;
- any layer behind a sign-in ("Token Required");
- proclamation / administrative lines for agency-land parks (Rule B1: the park is the land the agency OWNS);
- EU compilation layers (Natura 2000 / CDDA): Approximate at best (W-2), never a full YES from this tool.

**3. Sources, in this order (the LADDER).** Stop for a park at the first step that gives a candidate. Every step is batched by AGENCY: one agency's parks are asked together.
- **L0. Layers we already know.** `data/state-gis.json`, `data/ca-key/layers.json`, the world key's layers, PAD-US, CPCAD, the found-layers file. ONE multipoint query per 120 open pins (today's step A).
- **L1. The agency's own servers.**
  - Read the Agency Atlas for the area first: KPC-Links `.claude/build/research/agency-atlas/<area>.md`. It lists the server roots and folders.
  - Walk the ArcGIS REST folders two deep. Keep only polygon / line layers with a name field.
  - Cache per agency in `agencies.json` (re-read after 30 days).
- **L2. Open-data portals.** Search each portal in the club's portal list (intake `portals-*.json` + `state-gis.json` 'portals' + the atlas) through its own search API (ArcGIS Hub v3, CKAN, Socrata). For the US federal agencies, also catalog.data.gov. For EU / EEA countries, the INSPIRE discovery service: call `kpc_inspire` as a library.
- **L3. ArcGIS Online search, by agency then by park,** in the LOCAL LANGUAGE. The park words come from chat 8's world agency table `world_agencies.json`. Only items owned by an official organisation are kept.
- **L4. The park's official page.** `kpc_sitemaps` / `kpc_map_links` (as libraries) find map links on the agency's park pages. Downloadable files (shapefile, KML, GeoPackage, WFS) go through `kpc_convert_layers` (library) to GeoJSON near the pin. A PDF / image map goes to the picture-map saver list (branch picture-maps: never traced here).
- **L5. County parcels** (US, small parks only, under 2,000 acres): `kpc_parcels` finds the parcel layer, and `kpc_parcel_trace` draws an APPROXIMATE outline. Its grade is always "approximate (agency parcels)".

**4. When unsure.** Below tier T-3, or several candidates that disagree = a question for chat 11 with all of them. Never a guess. Nothing found after L5 = the park's why-not tag, e.g.:
- `no-layer: agency publishes none`
- `token-only`
- `blocked (robots)`
- `picture map only`
- `private land`

**5. What people see.** Nothing directly. Candidates go to chat 11 through the waiting room, in the SAME row shape as `data/waiting/questions/layers.json`: `ref, st, url, name_field, agency, kind, licence, answer, checked_by` + evidence. YES rows reach the keys by BOT W as today.

**6. Hard examples to test with:**
- **US-KY:** Kentucky WMAs whose KDFWR layer name differs from POTA's (name mismatch: tier, not drop).
- **US-TN:** tnstateparks.com blocks bots. L4 must say `blocked (robots)` and move on, never retry around it.
- **US-OR:** Monument BLM RMA. Joined to a 1-acre "Monument GS" by the old key, so it must NOT take a tiny record of another kind (size + kind check).
- **CA-ON:** Ontario Parks layer (L0) vs conservation authorities (L1 server walk).
- **CH, JP:** national layers via L2 / L3 in the local language.
- **FR:** INSPIRE (L2).
- **A US city park with no layer anywhere:** it must end at L5 or with a why-not tag, never with an unofficial source.

---

## PART 2. BUILD SPEC (`kpc_finder/`)

### In
- `--areas US-KY,CA-ON,CH,...`. The default is the club's order (`kpc_order.rank`): US + Canada, then North America, then W1-W10, then the rest.
- `--gap`: the parks with no official outline. Build it from:
  - the keys (`data/us-key`, `data/ca-key`, KPC-Links `data/world-key`): `g != "official"`;
  - the POTA pins (`data/parkinfo`, `data/pota/t` tiles);
  - the Fable book rows (KPC-Links `.claude/build/research/fable/<area>.md`), for the old why-not tags.
- `--atlas`, `--portals`, `--agencies-table`: the files above.
- `--acres data/acres.json` (from `kpc_acres`): the size check in the tiers.
- `--steps L0,L1,L2,L3,L4,L5`: the default is all of them. L5 is on for the US only.

### Steps
1. **Build the gap list.** Group the parks by AGENCY: the manager from the key's record or `parkinfo`'s type; unknown = its own group.
2. **For each agency group, run the ladder.** Each step's new layers are pin-tested at once for ALL that agency's open parks (multipoint, 120 pins a query).
3. **Score every hit.**
   - The tiers T-1..T-6: name, kind, size vs `acres.json`, pin inside.
   - Plus `kpc_map_match`'s band. STRONG / WEAK / CONFLICT goes on the row, so the existing AUTO-T1 rule can bot-YES the STRONG ones with chat 11's 1-in-10 sample.
4. **Write the why-not tag** for every park still open, and update its Fable book row IN PLACE: one row per park, the tag in its cell, the date.

### Out (KPC-Data branch `tools-out`, folder `finder/`, until it replaces the old bots)
- `questions.json` (the `layers.json` row shape + evidence: tier, band, step, agency group, pin distance).
- `found-layers.json` (the collector's shape: `{url: {area, name, from, source, date}}`).
- `whynot.json` → `{ref: {tag, step_reached, date, note}}`.
- `picture-maps.json` (for the saver) and `parcels.json` (L5 results, APPROXIMATE).
- `summary.md`: per area, parks open before → after, finds per step, time per step, hosts used.
- **Geometry is never stored**: only envelopes and rough acres (as today).

### Manners (one shared module: the coder's `_common/polite.py`)
- robots.txt obeyed: a robots.txt that answers 403 = no rules. Only ArcGIS REST + sharing/rest are exempt on arcgis.com.
- 2 s per host. 429 / 5xx = back off 30 / 60 / 120 s. Three strikes = a day's rest for that host.
- An honest User-Agent naming the club site.
- Never more than 2 jobs on one agency host at once (`kpc_shard hosts`).

### Built to be split (`kpc_shard`)
- It reads `AREAS` from the environment.
- It writes only its own areas' files plus `state-<part>.json`.
- It prints the hosts each area uses, for `kpc_shard hosts`.
- The national layers (PAD-US, CPCAD, the EEA server) are read ONCE in a step before the groups (HQ note on kpc_shard).

### Exit codes
- `0` = done.
- `3` = time ran out (`--resume` carries on, area by area).

---

## Acceptance (side by side with today's bots, same areas, same week)
- **Areas:** US-RI, US-IA, US-TN, CA-ON, CH, JP.
- **It sees what we know:** at least 95% of the candidates chat 11 already said YES to from the GIS hunter / world finder on those areas are found again.
- **It finds more:** at least 25% more parks get a candidate (counted in PARKS, not layers), with no candidate from a non-official source (grep the publishers).
- **Every park still open has a why-not tag.**
- **Quality:** in chat 11's sample of 40 new candidates, at least 85% are YES.
- **Time:** a US state in one 50-minute run, from an empty cache.

## How chat 10 wires it (after Nov 6, with Brandon's GO)
1. It runs nightly through `kpc-sharded.yml` (8 groups): US + Canada first, then the world in order.
2. Its questions go to `data/waiting/questions/finder.json`. Chat 11 grades (STRONG = AUTO-T1 with the 1-in-10 sample). YES rows go into the keys by BOT W, as now.
3. The GIS hunter, world finder and harvester are retired. Their leads files stay on `tools-out` for a month, then are deleted.
4. The Fable book rows and the why-not tags update themselves, with no chat pasting work logs.

---

## PART 3. Lessons from the outside research runs (Oct 31; files in `outside-methods/`: read FINDINGS_LOG first)

Build these in. Each one came from a real false "no hit".

1. **Pin on the road / entrance.**
   - Named records whose polygon sits 7-110 m from the POTA pin were missed by the "pin inside" test.
   - Every layer is ALSO searched by name (LIKE, Title Case: CPCAD's `NAME_E LIKE` is case-sensitive and `UPPER()` gives error 400). The distance pin → polygon edge is measured and written on the row.
   - Up to 150 m with a name match = a candidate row "pin just outside (N m)" for chat 11 (grey area G-F1).
2. **The name is in an odd field.** Examples: Yukon campgrounds = `REMARKS`; Kingston = `NOTES_NAME_OF_BLDG`; Parks Canada trails = `SectionEn`.
   - Scan EVERY text field for the park's core words, not only the display field.
3. **Wrong POTA pin** (typos: 62 vs 61; 0,0; copied from a neighbour; geocoded to the town). POTA's API pin = the sheet pin, so POTA cannot catch it.
   - When a record matches by name + kind + size but is far from the pin, check an official point (the agency's own point layer, DFHD address, historicplaces.ca meta tags).
   - Write `PIN OFF: real lat,lon, distance, source`.
   - We never move POTA's pin; the row goes to chat 11 with the evidence (grey area G-F2).
4. **Renamed, merged or delisted.** Try English / French / Indigenous variants. Before "not found", read the agency's park-boundary amendments / regulations pages (AB Jan 2024; SK rec sites repealed 2021; Sylvan Lake PP → town 2018).
   - Delisted = why-not tag `delisted <date> (<source>)`.
5. **Wrong kind of place** (lighthouse, building, ship, dam, biosphere / Ramsar with no land boundary). Use the source that fits the kind:
   - DFRP_PUBLIC (federal property): layer 4 polygons, 3 buildings, 2 points;
   - building footprints;
   - heritage registers.

   Biosphere / IBA / Ramsar = `no land boundary`.
6. **Same name, different place.** Always check the distance AS WELL AS the name (Denys Fort vs Nicholas Denys Site; Longwoods CA vs Battle Hill).
7. **Blocked is not "no hit".** These are logged as BLOCKED with the reason and retried later:
   - TLS failures;
   - Cloudflare challenges;
   - servers that only answer some clients;
   - token-only services.

   NEVER use an access token found inside a public web map's config.
8. **Layer ids get renumbered** (GNWT `Environment_LCC` 1/2 → 193-206). A 404 on a known layer = re-read the service's layer list and match by name before calling it gone.
9. **Parcels / cadastre as a last step.** Kept APPROXIMATE (PARCEL grade). Known open ones:
   - the Québec cadastre + MAMH roll use codes (76xx park, 7191 historic);
   - BC ParcelMap (`PARCEL_CLASS = 'Park'`);
   - ISC SaskGrid;
   - CLSS ParcelService/57 (legal NHS boundaries in the North).
10. **Two passes.** First everything, then a second pass on only the NOT FOUND + weak rows with every trick learned (the outside run solved about half the leftovers that way). A new trick found mid-run is written to the shared findings file at once (our Agency Atlas), so every worker uses it.
11. **8 parallel workers was the sweet spot.** Past that, the same government servers rate-limit. So `kpc_shard` groups = 8.

**Grey areas for Brandon:**
- **G-F1:** a named official record whose edge is within 150 m of the POTA pin (pin on the road / entrance): offer it to chat 11 as a candidate?
- **G-F2:** a record that matches by name + kind + size, with the POTA pin clearly a typo (tens of km off), confirmed by an official point: use the outline (pin left as POTA has it) and send the typo to Brandon / the POTA pin list?
