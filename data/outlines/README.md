# Outline master records

**What this is.** One small, checked outline for each POTA park, kept in this folder, so a key build can read it instead of downloading a whole agency layer again. A master record says where an outline came from, how many records that layer had when we read it, and when. If anything is short or unsure, the tool stops instead of guessing.

## What is here

| File | What it holds |
|---|---|
| `<area>.geojson.gz` | The park outlines for one area (for example `US-KY`). One entry per park: `ref`, `name`, `geometry`, `g`, source agency, layer URL, source record ids, source feature count, date read, licence, content hash. |
| `layers.json` | One entry per agency layer, with the total the layer itself reported at the last complete read (the *expected count*). Also the expected counts for the saved state copies. |
| `raw-manifest.json` | A list of the big raw layer downloads (name, size, sha256, source, date). The files are **not** in git. |
| `solver-queue/<layer>.csv` | Parks the tool could not match, or matched two ways. A person decides these. |

`g` says how good the outline is: `official` (an agency's own boundary), `approximate` (a trace), `point-circle` (a circle around the pin), `pin` (a point). A better one is never replaced by a worse one, so an official outline stays official.

## The tool

`python3 .github/scripts/kpc_master_cli.py <command>`

- **trim** reads a layer (GeoJSON, Esri JSON, Shapefile or GDB file, or a live layer URL), matches POTA parks by the layer's own id fields first, then by name with the pin inside the outline, keeps **only** those parks' outlines, and sends the rest to the solver queue. Pins are read, never moved.
  A file needs `--expected N` (the layer's own total) or a stored one. A read that cannot be checked is refused.
- **check** confirms every master file is whole, every hash matches, nothing from Protected Planet is in it, and no raw layer file is tracked by git.
- **plan** says which layers (not whole states) need a live read: older than 30 days (`KPC_MASTER_MAX_DAYS`), changed since last read (`lastEditDate`), or a count that no longer matches.
- **gate** runs before a key build reads its saved copies. It compares the actual saved record count (`len(recs)`) to the baseline, not the cache `seen` field. A saved copy with fewer records than the baseline is set aside, its area is not built that run, and the job turns red. A saved copy with no baseline is held and not used (never used with only a notice).
- **raw-add** records a downloaded raw file in `raw-manifest.json`.
- **wdpa-lookup** finds a park's managing agency from a Protected Planet file. Output is agency fields only, written outside the repo.

## The rules it keeps

1. **Short reads fail closed.** Fewer records than the layer reports means nothing is saved and the stored expected count does not change. A layer that suddenly reports under 90% of its old count is held for a person. A saved copy is measured by `len(recs)`, not `seen`. A saved copy with no baseline is held, never used with only a notice.
2. **Paging honours the layer's own limit.** The page size is never bigger than the layer's `maxRecordCount`, and a small first page is not taken for the last one.
3. **Official wins.** An approximate trace, a circle or a pin never overwrites an official outline. Two officials from different layers: the saved one stays and the conflict is reported.
4. **Read master first.** Re-read one layer only when `plan` says so.
5. **Hosts.** robots.txt is respected (a 403 means no), hub portals wait 60 s between requests, other hosts 2 s. Grant County NM's ArcGIS organisation and `ncnhde.natureserve.org` are never contacted, not even for robots.txt. No count or live read contacts any `services*.arcgis.com` host at all, robots.txt included. `apps.fs.usda.gov` uses saved copies only.
6. **Protected Planet / WDPA** geometry never goes into this repo, the public pages, or the 2-fers (licence). It is only a private lookup for the managing agency.
7. **Raw files stay out of git.** Keep them on the club Google Drive folder (backup) and on the bot's computer (working copy), and list them in `raw-manifest.json`.

## Where it plugs in

`kpc-us-key.yml`, `kpc-ca-key.yml` and `kpc-world-key.yml` each run `check` and `plan` first (read master first), then `gate` on the saved copies before the build. The key scripts themselves are unchanged, so the rules hashes are unchanged.
