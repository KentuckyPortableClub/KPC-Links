# Map outlines from the outline store (prep, 2026-11-13)

Status: **prep only. Nothing here changes what the public map shows.** No page loads the new loader, no workflow runs the
builder, and the go-live list is empty.

## What it is

The public map (finder, US trip planner) draws official outlines from `data/released/outlines/US-XX.geojson.gz`. Those are
copies of the key's saved state copies, which the map server simplified to about 110 m, and they often hold only the tract at
the pin. The outline store keeps every tract of every park at about 2 m. This change adds:

| File | What |
|---|---|
| `tools/kpc_display_copy.py` | Builds the **display copy** of one store area: one feature per park with all its tracts. It is simplified only past 3,000 points per park, and a park whose cap costs more than 5 m also gets a **fine** copy for when someone zooms in. Only records whose licence class is publishable go in. A park with one unpublishable tract, a doubtful join, or tracts 10 km or more apart keeps today's outline (listed under `fallback`). Standard library only, no network. The store is only read. |
| `kpc-outline-display.js` | Browser loader for the display copy. **Off by default:** on only with `?outlines=store` (remembered in that browser; `?outlines=old` turns it off), the club-room toggle (`localStorage kpcOutlineStore = '1'`), or an area named in its `LIVE_AREAS` list (empty). For every park the display copy does not hold it keeps today's outline. Any failure means today's outline. **No page includes it yet.** |
| `tests/test_display_copy_nov13.py` | 44 checks on a synthetic store made inside the test (no real outlines, no network). |

## Commands

```
python3 tools/kpc_display_copy.py build --store STORE_DIR --area US-NH --out OUT_DIR [--doubtful doubtful-joins.csv]
python3 tools/kpc_display_copy.py check --out OUT_DIR --area US-NH --public
```

`--private-preview` skips the licence gate for a person's own look on their PC. Its output is stamped PRIVATE PREVIEW, which
`check --public` and the browser loader both refuse, and the tool will not write it into a folder named `data/display`.

## Display copy format (`kpc-display-1`)

`OUT/<AREA>/INDEX.json` lists the parts (`[name, sha12, parks, bytes]`), the fine files, the credit line per layer, and the
fallback parks with their reasons. The parts are `<AREA>.geojson.gz` (+ `.p2` ...): whole parks, each under 1 MB, in the same
FeatureCollection shape as today's outline files. Feature properties: `ref name g detail_m points store_points records layers
cr fine drawn_once`. Fine files are `fine/<REF>.geojson.gz`. All files are gzip with mtime 0, so the same store gives
byte-identical files.

## What is NOT in this change (see the design note for the plan)

- The hook in `kpc-padus-layer.js` that asks the loader first. It needs `?v=` bumps on 21 pages and in the tests that pin them.
- The Pages step that copies the display copy into the site from its own branch.
- Any real display data. The store's licences are not recorded yet, so a gated build publishes nothing today.

Rules hashes: unchanged (no rule file, scope file or key data is touched). Rebuild level 1.

KPC owner, 2026-11-13
