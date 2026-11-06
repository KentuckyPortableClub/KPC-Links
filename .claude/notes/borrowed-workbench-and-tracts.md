# Borrowed from the KY GIS Workbench + the tract / 2-fer patch (Nov 6, 2026)

Brandon [pt437u], Nov 6: "for the key/2fer go ahead and borrow all that ... the guest tools and mapping rep stuff we want to use
add that to the notes for them". This note is for the chats and bots that pick these up later. Nothing here is live on the site.

## Already ported (in the key / 2-fer code)
- `kpc_pin_edge.py` = the Workbench's `edgeInfo` / `checkPin` (inside, distance to the nearest edge in m, the edge point) and
  `turf.area` acres (`acres_rings`, holes even-odd). Self-test: a 1 km square = 248.7 ac; a pin 100 m outside reads 100.1 m.
- Measured acres: every tract record carries `ac_measured` (from the outline the key keeps; coarse at 0.01 deg, so compare loosely).
- The field catalog idea (`ky-gis-layers.json`: `KDFWR_ID`, `ACRES_CAL`, owner fields) became ONE worldwide table,
  `kpc_source_fields.py`: source -> id field, acres field (+unit), owner field, parent field, access, basis. KY is just rows in it.
- The banned Grant County NM server (`services.arcgis.com/33TOOklri9xpic7U`) was NOT ported, and the coverage probe skips it.

## Guest tools / Mapping Rep Tool Box: worth using later (NOT built in this patch; UI is out of scope)
- Pin check card: inside / outside + feet to the nearest edge + the nearest polygon's name (now `kpc_pin_edge.pin_check` gives the
  same answer server-side; a Tool Box card could read `data/*/tracts/*.json` + the bounds files).
- Identify with measured acres next to the layer's own acres (e.g. Blackford Oaks WMA 564.83 measured vs KDFWR ACRES_CAL 565.09).
- UPDATES check: `returnCountOnly` per catalog layer + `editingInfo` + a diff of the KY server's service list against the catalog;
  a session-only "add to map" and "copy catalog entry". Good model for a guest "is this layer new or changed?" panel.
- Sketch / measure with GeoJSON + KML export, and "edit as sketch" from an official polygon (largest part, no holes, <= 400 points).
- Privacy rules to keep in any guest tool: parcel / PVA layers never show owner name, mailing address, city, zip, account or deed
  (`isParcel` = catalog group OR /pva|parcel/ in the URL or title); OSM is basemap only; KPC-drawn shapes are dashed "not evidence".
- Short refs pad to 4 digits (`19` -> `US-0019`), like the club's other tools.

## The new data (for pages and bots that want it)
- Tract side files (same key files untouched): `data/us-key/tracts/US-XX.json`, `data/ca-key/tracts/CA-XX.json`,
  `data/world-key/tracts/CC.json`, `data/tracts/US-KY.json`. Per park: the joined records as tracts (source, stable id, official
  acres, measured acres, owner, parent, access, pieces, box), plus `nested` (park inside park, from shapes) and `same_area` (source
  parent links such as CPCAD PARENT_ID: separate zones of ONE official area, not nesting).
- 2-fer count switch: `KPC_FERS_COUNT_MODE` = whole_park (default, today) | tracts | nested (labels only; see kpc_fers_count.py).
- Switches (all defaults = today's keys): `KPC_US_PUBACCESS=report` (default; REPORT ONLY: flags parks with closed PAD pieces, never drops a join or a park), `KPC_US_FS_OWNED=1` (note
  FS-owned-only on National Forest parks), `KPC_WORLD_ACRES=1` (world key gets official acres), `KPC_TRACT_STORE=0` (no side files).

## World key continent split (design only; not built)
The world key is already one file per country (92 files, 18 MB); the weight is in the build (one matrix job group per country list)
and in `index.json`. A lean split = an extra `continent` field per country in `index.json` + `index-<continent>.json` written next to it
by the join step, so a page can load one continent's list. That changes what the pages read, so it waits for Brandon; follow-up:
"world key: index per continent (join step only, flag KPC_WORLD_CONTINENT_INDEX)".

## Workbench v2 "FIND NEW" (BDW-Coils PR #2, merged Nov 6) — what we borrowed and what waits
Built (report only, this follow-up PR): `kpc_pin_cover.py` (0.25 mi pin coverage, the workbench's CAND_NEAR_MI rule, on the keys'
`bk` distance), `kpc_name_match.py` (the workbench's NAME_STOP / normName / nameMatch, accents folded for worldwide names) used by
`kpc_two_name_check.py`, `kpc_also_in.py` (which official layers a park's joined land comes from), and a test that the recorded-acres
field per source matches the workbench's candInfo() order (GIS_Acres -> ACRES_CAL -> ACRES -> ABSOLUTE_ACREAGE).
For later (not keys):
- Mapping Rep Tool Box: the whole FIND NEW flow (public land in view with no POTA pin inside or within 0.25 mi, 9 sources, filters for
  closed / private / small / local, "named like an existing park" flag, lead export), the owner privacy scrub (scrubOwner), and
  "pin vs this". Still no drawing tools for reps.
- Guest tools (Trip Planner / Park Commander cards): OPEN / RESTRICTED / CLOSED access badges from Pub_Access / PUB_ACCESS / AreaOpen
  (candAccess), and "also in" layer credits on a park card.
- Keys, possible next step (needs Brandon): feed `pin-cover-*.json` `unjoined_near` (unjoined parks with an official record under
  0.25 mi) into the hand-check queue; today it is a list only.
