# Map outlines from the outline store (prep, 2026-11-13 / 14)

Status: **prep only. Nothing here changes what the public map shows.** No page loads the new loader, no workflow runs the
builder, and the go-live list is empty.

## What it is

The public map (the finder and the US trip planner) draws official outlines from `data/released/outlines/US-XX.geojson.gz`.
Those are copies of the key's saved state copies, which the map server simplified to about 110 m, and they often hold only the
tract at the pin. The outline store keeps every tract of every park at about 2 m. This change adds:

| File | What |
|---|---|
| `tools/kpc_display_copy.py` | Builds the **display copy** of one or more store areas, for drawing only (details below). Standard library only, no network. The store is only read. |
| `tools/kpc_display_precedence.json` | The small editable table of which layer wins per area when a park's layers disagree. The state / agency's own layer comes before PAD-US. |
| `kpc-outline-display.js` | The browser loader. **Off by default:** it is on only with `?outlines=store` (remembered in that browser; `?outlines=old` turns it off), the club-room toggle (`localStorage kpcOutlineStore = '1'`), or an area named in its `LIVE_AREAS` list (empty). It keeps today's outline for every park the display copy does not hold; any failure means today's outline. **No page includes it yet.** |
| `tests/test_display_copy_nov13.py` | 64 checks on synthetic stores (no real outlines, no network). |
| `tests/test_display_copy_huge_nov14.py` | 12 checks: a 503,789-point synthetic park across two states (memory, sizes, levels, state-line seam, what one screen loads). |
| `tests/display_copy_fixture.py` | The synthetic store writer both tests use. |

## What the builder does

- **Licence gate.**
  - Store tool full 2 indexes: only records marked `publishable`, with their own licence class and credit line.
  - Older indexes: the licence text `CLASS; credit: X` if present, else not publishable.
  - WDPA never goes in.
  - One record that does not pass keeps the whole park on today's outline (`fallback` in the index, with the reason).
- **Doubtful joins** (a CSV list, the store's check-join flag, or tracts 10 km apart): today's outline.
- **One layer per park.**
  - A lower layer's tract that lies 90% or more inside the land a higher layer draws (or within 30 m of its line) is not drawn.
  - Any other lower-layer tract draws only the stretches of its line outside that land.
  - The same land is never drawn from two layers. The winner per park is written into the index (`won`).
- **Draw once:** a tract whose whole line is within 3 m of a drawn line is not drawn again; it stays listed.
- **Parks across states** are built in one run with all their states:
  - a tract held in two states' stores is drawn once;
  - the line where the park's own tracts meet at the state line is not drawn (only where the two tracts lie on opposite sides);
  - such a park carries `areas` and the run's `gen`, and the map draws it new only when all its states are on and from the same run;
  - with `--key-dir data/us-key`, a park whose other state is not in the run keeps today's outline.
- **Three levels:**

| Level | File | Size | When the map uses it |
|---|---|---|---|
| Overview | `<AREA>.geojson.gz` (+ `.pN`) | at most 3,000 points per park | zoomed out |
| Middle | `mid/<REF>.geojson.gz` | at most 30,000 points; only when the overview is more than 25 m off | to zoom 13 |
| Fine | `fine/<REF>/<ix>_<iy>.geojson.gz` | lines at 1 m in square pieces, each under 128 KB; only when the coarser levels are more than 5 m off | from zoom 14, only the pieces on screen |

  A level drops rings smaller than its own tolerance (under a pixel where it is used). The fine level drops nothing. Whatever is
  on screen at street level is within 5 m of the store.
- **Files.** Every file is gzip with mtime 0 (byte-identical rebuilds), and overview parts and middle files stay under 1 MB.
  - A park with hidden stretches has a `line` feature (drawn) and a `hit` feature (its tracts, for clicks only, never drawn).

## Commands

```
python3 tools/kpc_display_copy.py build --store STORE_DIR --area US-NH [--area US-ME] --out OUT_DIR \
        [--doubtful doubtful-joins.csv] [--key-dir data/us-key] [--precedence table.json]
python3 tools/kpc_display_copy.py check --out OUT_DIR --area US-NH --public
```

`--private-preview` skips the licence gate for a person's own look on their PC. Its output is stamped PRIVATE PREVIEW in every
file, which `check --public` and the browser loader both refuse, and the tool will not write it into a folder named
`data/display`.

## What is NOT in this change

- **The hook in `kpc-padus-layer.js`** that asks the loader first and switches levels. It needs `?v=` bumps on 21 pages and in
  the tests that pin them, and it comes in a separate pass after an independent grade.
- **The Pages step** that copies the display copy into the site from its own branch.
- **Any real display data.** Store licences are not recorded yet.

Rules hashes: unchanged (no rule file, scope file or key data is touched). Rebuild level 1.

KPC owner, 2026-11-14
