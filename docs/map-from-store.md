# Map outlines from the outline store (prep, 2026-11-13 / 14)

Status: **prep only. Nothing here changes what the public map shows** (Nov 15: the map hook is in, still OFF for everyone).
- No page includes the new loader: `kpc-padus-layer.js` fetches it only for a visitor who asks (`?outlines=store`).
- No workflow runs the builder or the publish script. The Pages deploy copies the `map-display` branch in when it exists.
- The go-live list is empty.

## What it is

The public map (the finder and the US trip planner) draws official outlines from `data/released/outlines/US-XX.geojson.gz`.
Those are copies of the key's saved state copies, which the map server simplified to about 110 m, and they often hold only the
tract at the pin. The outline store keeps every tract of every park at about 2 m. This change adds:

| File | What |
|---|---|
| `tools/kpc_display_copy.py` | Builds the **display copy** of one or more store areas, for drawing only (details below). Standard library only, no network. The store is only read. |
| `tools/kpc_display_precedence.json` | The small editable table of which layer wins per area when a park's layers disagree. The state or agency layer comes before PAD-US. |
| `tools/kpc_display_doubtful.csv` | The matcher's list of doubtful joins (KEEP-FLAGGED, 589 rows): these parks keep today's outline. |
| `tools/kpc_display_publish.sh` | Publishes built areas to the `map-display` branch safely (see below). |
| `kpc-outline-display.js` | The browser loader (details below). **No page includes it yet.** |
| `tests/test_display_copy_nov13.py` | 77 checks on synthetic stores, including the grade's cases (no real outlines, no network). |
| `tests/test_display_copy_huge_nov14.py` | 13 checks: a 503,789-point synthetic park across two states. |
| `tests/test_display_publish_nov14.py` | 11 checks: the publish script against a local bare repository. |
| `tests/display_copy_fixture.py` | The synthetic store writer the tests use (store index format 3 shape). |
| `tests/test_display_copy_v3store_nov14.py` | Opt-in (set `KPC_STORE_TOOL_DIR` to the unzipped store tool): 16 checks on stores the real store tool builds offline from its own test answers in a temporary folder; otherwise it says SKIP. |
| `tests/test_display_no_worse_nov15.py` | Nov 15: the "no worse than released" check on a made-up store and released folder. |
| `tests/test_pages_display_step_nov15.py` | Nov 15: the Pages step's own script against a local bare repository (no branch, unreadable, good + bad area). |
| `tests/test_map_store_hook_nov15.py` + `tests/map_store_hook_nov15_browser.py` | Nov 15: the hook's wiring, and headless Chromium on made-up display data (off by default, `?outlines=store`, fallbacks, the line-park click target, levels). |
| `tools/kpc_display_licence_classes.json` | Word-for-word copy of the store tool's `licence-classes.json`. |

### The loader (`kpc-outline-display.js`)

- **Off by default.** It is on only with `?outlines=store` (remembered in that browser; `?outlines=old` turns it off), the
  club-room toggle (`localStorage kpcOutlineStore = '1'`), or an area named in its `LIVE_AREAS` list (empty).
- It keeps today's outline for every park the display copy does not hold, and any failure means today's outline.
- **Limits per look:** at most 48 fine pieces and 1 MB, else it stays on the middle level. It keeps the last 60 fine pieces.

### The map hook (`kpc-padus-layer.js`, Nov 15)

- **Where.** The US official-outline drawing (`attachUsOfficial`): each state on screen asks `storeOr('US-XX', today's pack)`.
  `kpcKeyOutlines` itself is NOT changed: kpc-bounds.js shares it for "am I in the park", and the display copy is for drawing only.
- **Off by default.** The loader (`kpc-outline-display.js?v=20261115ms`) is fetched only when the page already has it, or the
  address says `?outlines=store` / `?outlines=old`, or this browser has `localStorage kpcOutlineStore = '1'`. Everybody else makes
  no new request. The loader's own `wanted()` then decides (its `LIVE_AREAS` is still `[]`). Going live for everybody later means
  adding the area to `LIVE_AREAS` AND including the loader on the pages (one `<script>` tag before `kpc-padus-layer.js`).
- **Fallback.** The loader not loading (10 s at most), no index, a part missing or of another build, a bad file, an empty pack:
  today's pack, drawn exactly as before. A park the display copy does not hold is drawn from today's file (`merge()`).
- **Drawing.** `role: line` = the drawn line (no fill); `role: hit` = the park's drawn tracts, clicks only (no stroke); a plain
  park feature as today. The popup adds the park's credit line (`creditLine()`).
- **Click target.** A park with a `role: line` feature and no `role: hit` feature gets a second Leaflet polyline over the same
  line: weight 12, opacity 0, no fill, interactive, carrying the popup. No band is drawn.
- **Levels.** After each look, a store park in view whose `level()` says `mid` or `fine` has that level's lines drawn (at most
  12 parks per look) and its overview line hidden (its popup and click target stay). A fine look that is too big uses the middle
  level; any failure keeps the overview.

### The Pages step (`pages-deploy.yml`, Nov 15)

After the Jekyll build: if branch `map-display` exists, it is fetched (depth 1), every area folder is checked again with
`check --public`, and the areas that pass are copied to `_site/data/display/`. No branch, a branch that cannot be read, or an area
that fails = nothing added for it; the step is `continue-on-error` and never fails the deploy. A change on `map-display` alone does
not start a deploy: it goes live with the next deploy (a push to main or the 2-hour timer when the site changed).

### No worse than released (`kpc_display_copy.py`, Nov 15)

A park drawn from the store must not lose land against today's released outline (`--released`, default this repository's
`data/released`; its `outlines/<AREA>.geojson.gz` and parts are what the map draws now). Today's polygons are rastered (about
40,000 cells per polygon, cells of 2 m or more); a cell is lost when it is outside every store tract the park draws and more than
30 m (or 1.5 x the released `detail`) from the store's boundary. More than 4 lost cells: the park keeps today's outline, its
reason goes to the private report and it is listed under `no_worse_kept_today` (the command line prints the refs). Only official
released outlines are compared (not `approximate`, not pins); a line-only store park against a released area keeps today's
outline. A released folder that is not there, or a released file that is broken or missing a part, stops the build.

## What the builder does

1. **Licence gate (strict).** A public build reads only the store's PER-AREA index (`index-<AREA>.json`; the combined
   `index.json` merges parks that span areas, so it is never read for a public build), which must say
   `store_format_version: kpc-outline-store-index/3` or `/4` (ONLY these two: a newer format, `/5` or anything else,
   stops the build until this reader is updated) and list a sha256 for every area file; every listed file is
   checked against it. A record passes only if all of these hold:
   - the index's `record_meta` for the record and the record itself agree on every licence field, and both say
     `publishable` is exactly `true`, with no private reason;
   - the class is one the store's `licence-classes.json` allows (`can_be_publishable: true`: OPEN, PUBLIC DOMAIN, NO TERMS
     STATED, DISCLAIMER ONLY, NON-COMMERCIAL). SHARE-ALIKE stays off. The list is a word-for-word copy in
     `tools/kpc_display_licence_classes.json`. A class the builder does not know in the index's `licence_classes` list
     stops the build; on one record it drops that record only (the private report says why);
   - the publish basis is `verified-row` or `owner-confirmed`;
   - the index's layer table agrees (its keys are the store's form, `host/path` with no `https://`; both sides are
     normalised the same way);
   - a plain credit line (`credit_line`) exists (e-mails, web addresses and account notes are removed).

   WDPA: the store's boolean `wdpa_derived` must be `false` in the index and in the record; then the words WDPA / Protected
   Planet / SPREP / UNEP-WCMC are searched in VALUES only (never in field names; PAD-US's `WDPA_Cd` field is skipped).
   Nothing is ever decided from licence text.

   **Each record is judged on its own** (the park-level `park_publishable` flag is not read). The records that pass are
   drawn, with their own credit lines; a record that fails (not publishable, WDPA-derived, a class that may not be drawn ...)
   is never drawn, never measured against and never named in a public file, and its reason goes to the private report. A
   park with no record that passes draws nothing from the store: it keeps today's outline, and its POTA pin is never moved.

   Also left out, one record at a time (never the whole area): a record whose geometry does not match its own checksum or
   point count (publishable or not), and a record the store marks `use` anything but `true` (the store tool sets
   `use: false` with a `use_why` for PAD-US proclamation lines, easements, closed and military land: not the park's land;
   FORMAT-4.md gives the field no other meaning). A record with no `use` field is judged by the gate alone.

   **Geometry kinds (store index format 4, store tool full 3.5).** A record's `geometry_kind` is `area`, `line` or `pin`
   (absent = `area`). The licence gate above is the same for every kind, so a line or pin that is not publishable, or is
   WDPA-derived, is never drawn. Then:
   - `area`: drawn as an area, as before. (River banks live in the store's water section, `store/water/...`, which the
     display copy does not read.)
   - `line` (official trail or river): drawn **as the store gives it**, an open line with every point, only rounded to 5
     decimals, in every level (overview, middle, fine). It is never simplified, buffered, joined or made into a polygon, and
     no zone band is drawn. The map today draws a trail park as its official line and applies POTA's 100 ft each side only in
     its own "am I in the park" test (`kpc-bounds.js`, 0.03048 km); this change keeps that and draws no band. The feature
     says `line: true`, and `INDEX.json` names the rule in `line_rule`. A park whose lines hold more than 30,000 points keeps
     today's outline (no line levels yet).
   - The line's zone note goes to the public feature as `zone: [{rule, ft, from, bank}]` from an **allow-list only**:
     `boundary_rule` trail_100ft | river_100ft_from_bank; `corridor_from` centreline | waters_edge; `bank_status` covered |
     bank_missing | bank_not_needed | line_missing | "route line too coarse for a bank test"; `corridor_ft` a number from 1
     to 1000. Any other value is dropped and counted (`zone_values_dropped`, private). Nothing else of the record (no
     `river_class`, `corridor_rule`, `bank_source` or other store text) is written. `check --public` refuses a feature
     property that is not on its public list and a zone value that is not on the allow-list.
   - **Click target for a line-only park.** Such a park has one `role: line` feature and no `role: hit` polygon (a polygon
     would be an invented band). `kpc-outline-display.js` needs no change (its `pack()` keeps the line feature as the park's
     feature); the map hook that draws the pack (kpc-padus-layer.js, Nov 15) makes that line itself clickable: when a park has no
     `hit` feature, bind the popup to its `line` feature, drawn with a wider invisible stroke (for example a second Leaflet
     polyline, weight 12, opacity 0, interactive).
   - `pin` (an official agency point) and stand-in circles in any form (`ring_is_stand_in_circle` or a record-level
     `circle` set to anything but false, or the record's `grade: point-circle`): the display copy has no place for an
     official point, so they are not drawn (counted in the private report). A pin is never an outline and never moves or
     replaces the POTA pin. A park with only pins keeps today's outline.
   - Any other kind is left out (counted).
2. **Doubtful joins** (`--doubtful`, a list that must exist), the store's check-join flag, or tracts 10 km apart: today's outline.
3. **The same geometry is drawn once**, using the copy from the highest-ranked layer.
4. **One layer per park.**
   - The winning layer is drawn in full.
   - A lower layer is judged per segment, by points every 5 m. A segment whose points all lie inside land a higher layer draws,
     or within 30 m of its line, is not drawn. Holes are not land.
   - Every uncovered stretch is drawn.
   - A ring covered all round is still drawn whole if hiding it would lose any land.
   - The 30 m strip is the "layers disagree" allowance: a lower-layer copy offset by less than 30 m adds a strip that is not
     drawn. Its area is reported privately.
5. **Draw once:** a segment within 3 m of a segment **already drawn** is not drawn again.
6. **Parks across states** are built with all their states (`--key-dir` makes a park with a missing state keep today's
   outline). Where the park's own tracts meet at the state line, on opposite sides, no line is drawn.
7. **Levels:**

| Level | File | Size | When the map uses it |
|---|---|---|---|
| Overview | `<AREA>.geojson.gz` (+ `.pN`) | at most 3,000 points per park | zoomed out |
| Middle | `mid/<REF>.geojson.gz` | at most 30,000 points | to zoom 13 |
| Fine | `fine/<REF>/<ix>_<iy>.geojson.gz` | lines at 1 m in pieces under 128 KB each | from zoom 14 |

   A level drops rings smaller than its tolerance only when that tolerance is over 5 m.
8. **Invariants, for every park, on its finest level.** A park that fails keeps today's outline:
   - **I1:** every metre of boundary that must be drawn lies within 5 m of a drawn line;
   - **I2:** no store land is lost (each covered tract is checked on its own grid of cells of 50 m or less).
9. **Public files carry no record keys, licence words, reasons, layer names or store names.** `fallback` says only "kept
   today's outline", and credits are per park. The only store text in a public file is the park's `name` and the credit
   lines, both scrubbed the same way (e-mails, web addresses and owner notes removed; anything with `<`, `>`, password,
   token, secret, `key=` or a private word is refused: a credit line then does not pass, a name becomes the park's ref). The
   layer names (`layers`, `won`) are in the private report only (the loader never read them). A park whose ref is not a POTA
   reference (`[A-Z0-9]{1,4}-[0-9]{4,5}`) is left out of every public file, even the fallback list. A record that is not an
   object, has no plain text key or shares its key with another is left out and counted. `check --public` refuses any of
   these, any feature property or INDEX key not on its fixed list, and an INDEX `about` / `line_rule` that is not the fixed
   text. The reasons go to the private `--report` file, which must be outside the output folder AND outside every git work
   tree. The index format must be written exactly `kpc-outline-store-index/3` or `/4` (no padding, spaces or other digits).
   A record with no `use` field is drawn when it passes the gate (the field is optional in older stores).

## Commands

```
python3 tools/kpc_display_copy.py build --store STORE_DIR --area US-NH [--area US-ME] --out OUT_DIR \
        --doubtful tools/kpc_display_doubtful.csv --key-dir data/us-key --report /private/report.json
python3 tools/kpc_display_copy.py check --out OUT_DIR --area US-NH --public
tools/kpc_display_publish.sh https://github.com/<owner>/<repo>.git OUT_DIR US-NH US-ME
```

`--private-preview` skips the licence gate (and may read an older index with no format, never a newer one) for a person's
own look on their PC. Its files carry private credit lines and layer names, so its `--out` must be OUTSIDE every git work
tree (any folder with a `.git` above it is refused). Its output is stamped PRIVATE PREVIEW in every file, which
`check --public`, the publish script and the loader all refuse.

**The publish script:**
- tells "branch missing" (first publish) from "cannot read the remote" (stop);
- fetches the published commit and checks it is the one it listed;
- replaces only this run's areas and checks every area of the new tree with `check --public`;
- then makes one atomic push: `map-display` moves only if it still points at the old commit, and `map-display-prev` moves to
  that old commit.

Any problem stops it before the push.

## Follow-ups (open, not in this change)

- A ringed record that has only a `pin_point` (no `geometry_kind`, no circle flag), or a `circle` / `grade` flag only inside
  `attrs`, is not recognised as a stand-in circle (neither form is in FORMAT-4.md).
- `use` absent is drawn; once every store writes `use` on every record, require `use` to be exactly `true`.
- Two records with one key are both left out (safe); the store tool should never write that.

## What is NOT in this change

- **Workflow changes** other than the Pages step: the publish workflow, and `filter: blob:none` on the five `fetch-depth: 0` checkouts.
- **Any real display data.**

Rules hashes: unchanged (no rule file, scope file or key data is touched). Rebuild level 1.

KPC owner, 2026-11-14; map hook, Pages step and no-worse check 2026-11-15
