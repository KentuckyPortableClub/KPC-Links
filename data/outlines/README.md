# Outline master records

**What this is.** One small, checked outline for each POTA park, kept in this folder, so a key build can read it instead of downloading a whole agency layer again. A master record says where an outline came from, how many records that layer had when we read it, and when. If anything is short or unsure, the tool stops instead of guessing.

## What is here

| File | What it holds |
|---|---|
| `<area>.geojson.gz` | The park outlines for one area (for example `US-KY`). One entry per park: `ref`, `name`, `geometry`, `g`, source agency, layer URL, source record ids, source feature count, date read, licence, content hash. |
| `<area>.p2.geojson.gz` ... | Nov 11: the next parts of an area whose outlines do not fit one file under 1 MB (see *Parts* below). |
| `layers.json` | One entry per agency layer, with the total the layer itself reported at the last complete read (the *expected count*). Also the expected counts for the saved state copies. |
| `raw-manifest.json` | A list of the big raw layer downloads (name, size, sha256, source, date). The files are **not** in git. |
| `solver-queue/<layer>.csv` | Parks the tool could not match, or matched two ways. A person decides these. |
| `solver-queue/US-XX.nomatch.csv` | Nov 11: parks the live key (`data/us-key/US-XX.json`) knows that have no outline in the master records and are in no layer's queue file: `no layer joined this park in the key`, or `joined in the key, but no outline for it is in the master records`. Written by `collect --us-key`; when every park has an outline it is emptied to its header line (not deleted: the save carries no deletions). Pins are not in the key, so lat / lon are blank. |

`g` says how good the outline is: `official` (an agency's own boundary), `approximate` (a trace), `point-circle` (a circle around the pin), `pin` (a point). A better one is never replaced by a worse one, so an official outline stays official.

## Parts: an area over 1 MB (Nov 11)

An area file that would pass 1 MB (gzip bytes) is saved in parts by `kpc_master.save_area`, with the same part scheme the release
uses (`kpc_release.split` / `join`; the pages' `KPCREL` block reads it):

- `US-AK.geojson.gz` is part 1 and keeps the area's own name; parts 2..N are `US-AK.p2.geojson.gz` ... `US-AK.pN.geojson.gz`.
- Every part is a whole FeatureCollection with the same `kpc` header plus `kpc_part: [i, N, tag]`; `tag` is the first 12 hex of the
  sha256 of the whole area, so parts of two different saves are never put together (the reader refuses: never half an area).
- Parks go into the parts in ref order. One park that alone does not fit is cut by its polygons into pieces: Features with the same
  properties plus `kpc_piece: [k, M]`. Reading puts the polygons back in order, so the record (and its content hash) is the same.
- Part 1 decides how many parts there are. The copy-mode save carries no deletions, so an old `.p3` left behind after the area
  shrinks is harmless: nobody reads it. An area that fits stays one file with no part fields, exactly as before.
- Every tool reads every part: `load_area` (and so trim, `check`, `collect`, `part`, `kpc_outlines_from_key`, `kpc_outlines_keep_main`,
  `kpc_key_drop_guard`, `tools/kpc_boundary_gap.py`), the release (a working area in parts is released part by part, byte for
  byte), and the pages (`KPCREL.get` reads part 1, then parts 2..N, on the working-copy path too).
- Each part is a tracked file under 1 MB, so the preflight size check covers them as it covers any file.

## Pin-graded parks have no outline (Nov 11)

`kpc_master.save_area` leaves out a park the US key grades `pin` (`kpc_master.pin_drops`), so every writer and every map tool agrees
without reading the key. The rule looks at every US key that lists the park, whichever state's file holds the record (a record
in a neighbour's file counts the same): the park is dropped when every one of those keys grades it pin. A park no US key lists is
left alone. A park that is pin in one state and official in another (US-4514: pin in TX and OK, official in NM; US-0015: pin in DC,
official in MD and WV) keeps its outline: the planner's lookup takes the best grade over the states it reads, so it draws that outline. `kpc_outlines_keep_main` does not bring such an outline back from main's copy, and the
drop guard does not count it as a lost outline. `kpc_master_cli.py resave [--dry-run]` puts every area file through the save once.

The same place keeps the grade honest: a record whose `g` is higher than the key allows (say `official` while
`data/us-key/US-XX.json` grades the park `approximate`) is saved as `approximate` (`kpc_master.grade_lowers`; only `g` and the content
hash change), whichever state's file holds it, only when approximate is the best grade any US key that lists the park gives it:
a park official in any state's key is not touched, and a grade is never raised this way. A later trim or main's old official copy
cannot flip it back, because every save applies the rule again (`kpc_master.key_fix`, also in `kpc_outlines_keep_main`).

**Same content, other bytes = no change.** Another zlib build packs the same content into other bytes (the deflate stream differs;
the header is fixed: mtime 0, the file name, XFL 2, OS 255). So every writer compares the unpacked content, not the bytes, and leaves
a file that already holds the same content untouched (`kpc_master.write_if_changed`: save_area and its parts, `resave`, `collect`,
`part`, `kpc_outlines_from_key`; the release keeps a released file and its version). `kpc_outlines_keep_main`, which runs as the
save's redo step just before `git add`, puts main's own bytes back for any area file whose content equals main's, so git sees no change.

## Building the outlines a key joins (Alaska, Nov 11)

On a computer with shapely and the saved copy (`US-AK.json.gz` from the boundary-cache release) in a folder, from the repo root:

    python3 .github/scripts/kpc_outlines_from_key.py --cache <folder with US-AK.json.gz> --states AK --dry-run   # what would be written, the part files and sizes
    python3 .github/scripts/kpc_outlines_from_key.py --cache <folder with US-AK.json.gz> --states AK             # write it (parts when over 1 MB)
    python3 .github/scripts/kpc_outlines_from_key.py --verify --states AK                                        # old outlines unchanged, every file under 1 MB, counts
    python3 .github/scripts/kpc_master_cli.py check --repo .

Full default precision (5 decimals, the 0.0001 degree trim the master always keeps); nothing else is simplified.

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
5. **Hosts.** robots.txt is respected (a 403 means no), hub portals wait 60 s between requests, other hosts 2 s. Grant County NM's ArcGIS organisation and `ncnhde.natureserve.org` are never contacted, not even for robots.txt. No count or live read contacts any `services*.arcgis.com` host at all (`services`, `services1` to `services9` and up, and the regional ones like `services-eu1`), robots.txt included. `apps.fs.usda.gov` is no longer saved-copy only (2026-11-13); it is a slow host: at least 10 s between requests, one at a time, Retry-After honoured, stopped after a run of 403 / 429 answers (its robots.txt answers 403, which the robots check here still counts as no). Redirects get the same checks: every hop is checked (host rules, then that host's robots.txt, then pacing) before it is followed, and a hop onto a forbidden host stops the request.
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
  sheet's name field), and its `sid` decides the fallback. The world key itself still does not read hand files (that change would
  move the world rules hash). Since 2026-11-12 `fill` keep-bigger merges a `hand-W-XX.<layer>` file into the saved copy (`kpc_world_hand.py`,
  not a rule file) by source id, then still checks the file into the per-area store (trimmed to that country's POTA parks). A
  smaller re-read never replaces a saved layer. The next saved-shapes run (`kpc-world-cache.yml`) applies repo (and release)
  `hand-W-<CC>.*.geojson.gz` files after T0, so a blocked live refresh that does not rewrite the copy still leaves a fuller file
  for save-check / upload. Owner hand files live in `data/outlines/hand/`.
- The builder change still possible later (a rules-hash move): in `kpc_world_key.py`, in the per-source loop (`for s in SRC.get(cc, [])`,
  where a failed or saved-only source takes its saved records), also read `hand-W-<CC>.*.geojson.gz` from a `KPC_WORLD_HAND` folder whose
  `kpc.url` is that source's address. In `kpc_ca_key.py`, at the `KPC_CA_HAND` reader, also read `hand-CA-*.<layer>` names. A file is merged only after `check_other` passes, and only when its meta records a licence or terms and is not share_block / WDPA flagged. A record with no `_bb` / `_r` (or zero-area geometry) is not merged or counted. `hand-W-XX.<layer>.chunkN.geojson.gz` groups are concatenated before the merge. World-cache fill writes an empty parks list so this job can merge a licensed file offline; pin / 5 km checks then run at key build. Release hand files are staged and never `--clobber` a repo copy of the same name, or a file whose country is not the job's `W-$CC`.

**Baselines.** Every `W-XX` copy the world key builds has a baseline (`caches`). `CA-ALL` has none, because no file offline records
its total. The Canada build runs `gate --first-ok`, and after a good full build `baseline` records the first one in `layers.json`
(saved with the Canada key). After that, Canada's gate and `save-check` work like the others.

The PC helper for the who=`person` rows is `tools/kpc_pc_helper.py`, with plain steps in `tools/README-pc-helper.md`.

### Trimmed copies and owner-approved baselines (Nov 11)

A saved copy trimmed on purpose (a hand bundle that keeps only the features near POTA parks) is never compared with the full-layer
baseline in `layers.json` (`caches`). Whoever makes such a bundle runs, on the final file, right before the upload:

    python3 .github/scripts/kpc_master_cli.py bundle-manifest W-XX.json.gz --by "KPC owner" [--source-full "LABEL=N" ...]

It writes the copy's own manifest INTO the copy: trimmed to parks, the record count per layer and in total, who made it and when, the
records' sha256, and (optional) each source layer's full count for the record. `--show` prints a copy's per-layer counts and file
sha256; `--check` checks a copy against its manifest. The world key's gate (`gate --allow-trimmed`) checks a trimmed copy against its
own manifest, exactly (fewer records, in total or for one layer = SHORT, moved aside), and refuses one whose manifest is incomplete or
does not match the records. A full copy keeps its full baseline. The gate writes no baseline; `baseline` refuses a trimmed copy and
`save-check` never lets a bot upload one.

Copies made before manifests existed, and baselines recorded wrong, go through the owner: `world-baselines.proposed.json` lists the
proposed counts with a reason each; the gate never reads it. The gate reads only `world-baselines.approved.json`, and only when
`approved_by` / `approved_date` is a real sign-off, and each entry only for the one copy whose sha256 it names (`copy_sha256`).

## The layer intake bot (Nov 11): one raw layer in, two outputs out

`python3 .github/scripts/kpc_layer_intake.py --source ... --sidecar ... --parks locations-pota.json --out DIR [--write]`

A person or a finder bot drops a saved copy on the KPC-Archive release `layer-intake` (the file plus `<file>.intake.json`: area,
layer, source_url, license, expected = the layer's own full count, the match fields). The bot never reads a layer live: the input is
that release asset, a `boundary-cache` asset, or a direct official file that `live_ok` and robots.txt allow. WDPA / Protected Planet
and `redistribute: "no"` layers are refused before anything is fetched or stored (exit 4). The file must hold exactly the sidecar's
count: fewer is a short read (exit 2), more means the count is not this file's (exit 3), so a wrong count never becomes a baseline.

1. **The original**, byte for byte, goes to the KPC-Archive release `layer-originals` (parts under 2 GB when bigger) with a sidecar
   (sha256, size, record count, source, licence, date). It is never in git and never on a Pages site. Its facts (no licence text) go
   to `raw-manifest.json`; a US original is recorded by the master step instead, when it merges a US hand file (as `import-existing`).
2. **The trimmed copy**, in the formats the tools already read: the master records, the layer's `layers.json` entry and its
   solver-queue CSV from `trim` on the **full** read (so the layer's baseline is its full count); a checked hand file
   `hand-<AREA>.<layer>.geojson.gz` holding only the park-relevant records (matched, or holding a POTA pin or a same-name outline
   near one, so a later trim of it cannot settle an ambiguity by leaving a rival out: checked on every run); for a `W-XX` area a
   bundle `W-XX.json.gz` made with the world key's own record builder and source id (read from `kpc_world_key.py`, which is not
   changed) at the detail `kpc-world-cache.yml` saves, stamped by `bundle-manifest`, and a row in `world-baselines.proposed.json`
   (never the approved file); research-inbox rows for the leftovers.
   A country the world key reads several sources for: the bundle is the `boundary-cache` copy with only this layer's records replaced
   (never by a smaller set), so the other sources' saved records stay; with no copy there yet it is a first copy of this layer alone
   and the report says so; if the asset list cannot be read there is no bundle. Records without a unique id: no bundle.

The default is a dry run: everything is built in `--out` and nothing goes to a release or to the repo. A write run tries the trim
as a dry run first, so a refusal (a shrink held) stops before the original is stored. A US hand file is never
uploaded by the bot (the master step would hold a trimmed one as a shrink, or record its count as the layer's baseline). A `W-XX`
bundle is uploaded only as a first copy, with the owner's OK; an existing `W-XX.json.gz` is never replaced by a bot.

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
