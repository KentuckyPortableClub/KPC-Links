# Outline master records

**What this is.** One small, checked outline for each POTA park, kept in this folder, so a key build can read it instead of downloading a whole agency layer again. A master record says where an outline came from, how many records that layer had when we read it, and when. If anything is short or unsure, the tool stops instead of guessing.

## What is here

| File | What it holds |
|---|---|
| `<area>.geojson.gz` | The park outlines for one area (for example `US-KY`). One entry per park: `ref`, `name`, `geometry`, `g`, source agency, layer URL, source record ids, source feature count, date read, licence, content hash. |
| `layers.json` | One entry per agency layer, with the total the layer itself reported at the last complete read (the *expected count*). Also the expected counts for the saved state copies. |
| `raw-manifest.json` | A list of the big raw layer downloads (name, size, sha256, source, date). The files are **not** in git. |
| `solver-queue/<layer>.csv` | Parks the tool could not match, or matched two ways. A person decides these. |
| `solver-queue/US-XX.nomatch.csv` | Nov 11: parks the live key (`data/us-key/US-XX.json`) knows that have no outline in the master records and are in no layer's queue file: `no layer joined this park in the key`, or `joined in the key, but no outline for it is in the master records`. Written by `collect --us-key`; when every park has an outline it is emptied to its header line (not deleted: the save carries no deletions). Pins are not in the key, so lat / lon are blank. |

`g` says how good the outline is: `official` (an agency's own boundary), `approximate` (a trace), `point-circle` (a circle around the pin), `pin` (a point). A better one is never replaced by a worse one, so an official outline stays official.

## The tool

`python3 .github/scripts/kpc_master_cli.py <command>`

- **trim** reads a layer (GeoJSON, Esri JSON, Shapefile or GDB file, or a live layer URL), matches POTA parks by the layer's own id fields first, then by name with the pin inside the outline, keeps **only** those parks' outlines, and sends the rest to the solver queue. Pins are read, never moved. A queue row has one reason: a pin inside an outline but no name agrees; ambiguous names; a same-name outline nearby but the pin is outside; matched an outline record that has no usable outline; the layer record names a POTA ref the park list does not hold (same country only). Rows are deduped per (park, reason), and a queue file is written only when its bytes change, so a repeat run makes no commit.
  A file needs `--expected N` (the layer's own total) or a stored one. A read that cannot be checked is refused.
- **check** confirms every master file is whole, every hash matches, nothing from Protected Planet is in it, and no raw layer file is tracked by git.
  It also warns about each **suspect baseline**: a layer whose `expected_count` is lower than the records its file held (`source_count`), for example a count capped at 200 before the plain count query. The master step re-records the baseline on that layer's next verified full read (`trim` stores the layer's own total).
- **plan** says which layers (not whole states) need a live read: older than 30 days (`KPC_MASTER_MAX_DAYS`), changed since last read (`lastEditDate`), or a count that no longer matches.
- **gate** runs before a key build reads its saved copies. It compares the actual saved record count (`len(recs)`) to the baseline, not the cache `seen` field. A saved copy with fewer records than the baseline is set aside, its area is not built that run, and the job turns red. A saved copy with no baseline is held and not used, unless the workflow passes `--first-ok` (Canada only, because `CA-ALL` has no baseline yet): then it is used with a notice, and a SHORT copy is still held.
- **baseline** records a saved copy's first baseline after a good full build, only when it has none. It is the copy's record count, or the release copy's count when that is smaller. It never lowers or replaces an existing baseline.
- **`kpc_outlines_from_key.py`** (Nov 11, run on the box, offline) adds an outline for each park the published US key joins
  (`data/us-key/US-XX.json`, `m`) that has none in `US-XX.geojson.gz` yet, from the saved copy `US-XX.json.gz` (boundary-cache).
  It unions the joined records, trims them with the same trim, and writes a master record with `via: key` and
  `layer_url: file:US-XX.json.gz`. It never replaces an outline already in the file, skips trail lines (the trails layer draws
  those) and skips a park whose joined records are not all in the saved copy. No map server is contacted.
- **raw-add** records a downloaded raw file in `raw-manifest.json`.
- **wdpa-lookup** finds a park's managing agency from a Protected Planet file. Output is agency fields only, written outside the repo.

## The rules it keeps

1. **Short reads fail closed.** Fewer records than the layer reports means nothing is saved and the stored expected count does not change. A layer that suddenly reports under 90% of its old count is held for a person. A saved copy is measured by `len(recs)`, not `seen`. A saved copy with no baseline is held, unless the workflow passes `--first-ok` (then the first good full read records it).
2. **Paging honours the layer's own limit.** The page size is never bigger than the layer's `maxRecordCount`, and a small first page is not taken for the last one.
3. **Official wins.** An approximate trace, a circle or a pin never overwrites an official outline. Two officials from different layers: the saved one stays and the conflict is reported.
4. **Read master first.** Re-read one layer only when `plan` says so.
5. **Hosts.** robots.txt is respected (a 403 means no), hub portals wait 60 s between requests, other hosts 2 s. Grant County NM's ArcGIS organisation and `ncnhde.natureserve.org` are never contacted, not even for robots.txt. No count or live read contacts any `services*.arcgis.com` host at all (`services`, `services1` to `services9` and up, and the regional ones like `services-eu1`), robots.txt included. `apps.fs.usda.gov` uses saved copies only. Redirects get the same checks: every hop is checked (host rules, then that host's robots.txt, then pacing) before it is followed, and a hop onto a forbidden host stops the request.
6. **Protected Planet / WDPA** geometry never goes into this repo, the public pages, or the 2-fers (licence). It is only a private lookup for the managing agency.
   **`redistribute: "no"`** (optional) on a layer in `layers.json` or a source in `download-sources.json` means its data may not be shared further. The PC helper, `import-existing` and `fill` then refuse to pack, upload or merge it (`fill` exits 4, so the job goes red). No field means no known restriction. Set it only from the source's own terms, never by guess.
7. **Raw files stay out of git.** Keep them on the club Google Drive folder (backup) and on the bot's computer (working copy), and list them in `raw-manifest.json`.

## Where it plugs in

`kpc-us-key.yml`, `kpc-ca-key.yml` and `kpc-world-key.yml` each run `check` and `plan` first (read master first), then `gate` on the saved copies before the build.

## The master step (Nov 10): one owner of the saved copies

In `kpc-us-key.yml` one step, **THE MASTER STEP** (`kpc_master_cli.py fill`), runs between the plan and the gate. It is the only writer
of the saved copies (`US-XX.json.gz` on the boundary-cache release); the build after it only reads them (`KPC_MASTER_OWNS=1`).

1. **The work list.** The open rows of the needs-download list for the job's states, the copies that are short against their gate
   baseline, the state-GIS layers a copy has no records from (new layers), and the checked downloads a person sent
   (`hand-US-XX.<layer>.geojson.gz` on the release, from the PC helper). With `refresh=all` (the fresh start) the list is every layer of every state.
2. **Read where allowed.** The host rules come first (never-contact hosts, every `services*.arcgis.com` host, the saved-copy-only list).
   Then robots.txt, where a 403 counts as no. The key reads each layer into one layer file (`kpc_us_key.py` with `KPC_REFILL_ONLY=1
   KPC_LAYER_OUT`). A person's download is read the same way (`KPC_LAYER_IN`), so it gets the same shaping.
3. **Per layer file:** the count must reach the layer's own total (fail closed) → `trim` → `raw-add` → the keep-bigger merge into the saved
   copy (a smaller read never replaces a saved layer). The existing save step uploads what changed. The gate and its baselines are unchanged.
4. **The ONE needs-download list** (KPC-Data `data/needs-download.json`, one schema: id, area, layer, url, page, host, who, why, expected,
   have, source, added, status, note). who=`bot` means a bot downloads it, `person` means a person does it with the PC helper, and `never` means nobody contacts that server.
   The KPC-Data bots (hunters, finders, collector, engine) only add rows to it and never save layers. The US key's rows go up as the
   release asset `needs-download.json`, and KPC-Data's hourly copy job merges them in.

### Canada and world (owner rule, 2026-11-10)

`fill` takes area ids, not only states: `US-XX`, `CA-XX` / `CA-ALL`, `W-XX` (`--states` for the US job, `--areas` for the others).
A hand file's area and layer come only from its name, `hand-(US-XX|CA-XX|CA-ALL|W-XX).<layer>.geojson.gz`. Any other name is refused.
The file must also say the same area and layer (`kpc.area`, `kpc.layer`) and hold at least its own count. A file is never applied
to an area other than the one in its name. One national file (FWS, NPS) is packed once **per area**, and each area gets its own
checked file with its own count.

The US saved copy takes a hand file because the US key itself turns it into saved-copy records (`KPC_LAYER_IN`), so it gets the
same shaping and names as a live read. The Canada and world saved copies cannot take one the same way without changing their builders:

- **Canada** (`CA-ALL.json.gz`): each record carries `_k`, the kinds from `kpc_ca_key.kinds()`, a rule function. The Canada key
  already merges its own checked hand files (`hand-CA.<name>.geojson.gz`, `_ca` records, `KPC_CA_HAND`, keep-bigger, fail closed), so
  `fill` keeps no second path. A `hand-CA-XX.<layer>` file is checked (name, area, count, licence, trim to Canada's POTA parks) into the
  per-area checked store (`fill --checked`), and its row is held for a person.
- **World** (`W-XX.json.gz`): each record's name `n` and type `ty` come from the world key's own field rules (`pick_name`, `TYPEF`, the
  sheet's name field), and its `sid` decides the fallback. The world key reads a saved copy only for a source that fails (every
  `services*.arcgis.com` layer). It reads no hand files. So `fill` checks a `hand-W-XX.<layer>` file into the checked store (trimmed
  to that country's POTA parks) and its row is held: who=person, "checked file saved; the world builder does not read hand files yet".
- The builder change still needed (a rules-hash move): in `kpc_world_key.py`, in the per-source loop (`for s in SRC.get(cc, [])`,
  where a failed or saved-only source takes its saved records), read `hand-W-<CC>.*.geojson.gz` from a `KPC_WORLD_HAND` folder whose
  `kpc.url` is that source's address. Build each record with the key's own `arcgis_rec(label, url, oid field, feature)`, check the count
  (fail closed), and keep the bigger set. In `kpc_ca_key.py`, at the `KPC_CA_HAND` reader, also read `hand-CA-*.<layer>` names.

**Baselines.** Every `W-XX` copy the world key builds has a baseline (`caches`). `CA-ALL` has none, because no file offline records
its total. The Canada build runs `gate --first-ok`, and after a good full build `baseline` records the first one in `layers.json`
(saved with the Canada key). After that, Canada's gate and `save-check` work like the others.

The PC helper for the who=`person` rows is `tools/kpc_pc_helper.py`, with plain steps in `tools/README-pc-helper.md`.

## download-sources.json (Nov 10): the official download sources and the change check

One entry per official download source from the hand-filled layer list: `areas`, `layer`, `page`, `file` (a direct file when
there is one), `format`, `stated_count`, `version` (as the page states it), `kind` (`first-party`, `fallback` = only PAD-US or
CPCAD, which the keys read already, `none` = none found yet), `check` (`bot` = a bot may check it for a change; `person`),
`terms` (always "see the source page": the terms are on each page, not copied here), and `fp`, the last-seen fingerprint
(size, Last-Modified, ETag, stated version, record count) with `fp_seen` and `changed`.

`kpc_master_cli.py watch` runs in the US key join step (no own schedule). Allowed requests only: `kpc_master.live_ok`, then
robots.txt (a 403 = no), the per-host pacer (60 s on hub portals); never a services*.arcgis.com host or a never-contact host.
A HEAD of the direct file, or the ScienceBase item JSON. The first check only sets the baseline. A later difference in a field
both checks read reopens that source's rows in the needs-download list (source `change check`), and only then a person is asked.
A held row (fallback only / none found) stays held unless its source changes.

## Asking only for what is actually missing (Nov 10)

- **The master step** lists a layer only when the live key (`data/us-key/US-XX.json`) joins a park to a record of it that the
  saved copy does not hold, or when a layer of the state's own has no records in the copy at all (a new layer). A copy that is
  short of its baseline is not, by itself, a reason to ask anyone.
- **The seed** checks every saved copy before it opens a row: `US-XX` by the layer id (OBJECTID prefix; the US key's own prefix
  for a row with no id), `CA-ALL` by the Canada layer id (the first 12 letters of the label) or the source label, `W-XX` by the
  source label (or its equivalent in a box-side map when the label differs). A layer the copy holds is a done row.
- **An official direct file** a bot may fetch (by the same host rules) makes the row a bot's. The fresh-start run
  (`refresh=all`) downloads it with `fill --official-files`: the pre-request host check, then robots.txt (a 403 = no), then the
  per-host pacing (60 s on hub portals). Nothing is downloaded on any other run.
- **`kpc_master_cli.py import-existing`** (run on the box) takes in the downloads already made: the hand map, the downloads
  table, the Drive index and the research inbox. It writes raw facts only (name, size, sha256, date, source, record count) to
  `raw-manifest.json`, marks the rows those files cover as done (source `existing download`), and builds checked hand files
  for rows whose records are only in a box file (`hand-US-XX.<layer>`, `hand-CA.<name>`, `hand-W-XX.<layer>`). `--upload`
  puts them on the boundary-cache release. A US hand file is merged by the master step; a Canada one by the Canada key
  (`KPC_CA_HAND`); the world key does not read hand files yet. A checked file is noted only on rows of the area in its name.
- Point layers (hatcheries, river access points) have a table entry in `data/state-gis.json` without `nm`: the outline key
  skips them (a point is not an outline); their checked hand files are kept for the point tier.
