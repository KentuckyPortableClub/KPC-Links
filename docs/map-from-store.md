# Map outlines from the outline store (prep, 2026-11-13 / 14)

Status: **prep only. Nothing here changes what the public map shows.**
- No page loads the new loader.
- No workflow runs the builder or the publish script.
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
| `tools/kpc_display_licence_classes.json` | Word-for-word copy of the store tool's `licence-classes.json`. |

### The loader (`kpc-outline-display.js`)

- **Off by default.** It is on only with `?outlines=store` (remembered in that browser; `?outlines=old` turns it off), the
  club-room toggle (`localStorage kpcOutlineStore = '1'`), or an area named in its `LIVE_AREAS` list (empty).
- It keeps today's outline for every park the display copy does not hold, and any failure means today's outline.
- **Limits per look:** at most 48 fine pieces and 1 MB, else it stays on the middle level. It keeps the last 60 fine pieces.

## What the builder does

1. **Licence gate (strict).** A public build reads only the store's PER-AREA index (`index-<AREA>.json`; the combined
   `index.json` merges parks that span areas, so it is never read for a public build), which must say
   `store_format_version: kpc-outline-store-index/3` (or later) and list a sha256 for every area file; every listed file is
   checked against it. A record passes only if all of these hold:
   - the index's `record_meta` for the record and the record itself agree on every licence field, and both say
     `publishable` is exactly `true`, with no private reason;
   - the park is publishable as a whole (`park_publishable`);
   - the class is one the store's `licence-classes.json` allows (`can_be_publishable: true`: OPEN, PUBLIC DOMAIN, NO TERMS
     STATED, DISCLAIMER ONLY, NON-COMMERCIAL). SHARE-ALIKE stays off. The list is a word-for-word copy in
     `tools/kpc_display_licence_classes.json`; a class the builder does not know (in a record or in the index's
     `licence_classes`) stops the build;
   - the publish basis is `verified-row` or `owner-confirmed`;
   - the index's layer table agrees (its keys are the store's form, `host/path` with no `https://`; both sides are
     normalised the same way);
   - a plain credit line (`credit_line`) exists (e-mails, web addresses and account notes are removed).

   WDPA: the store's boolean `wdpa_derived` must be `false` in the index and in the record; then the words WDPA / Protected
   Planet / SPREP / UNEP-WCMC are searched in VALUES only (never in field names; PAD-US's `WDPA_Cd` field is skipped). One
   failing record keeps the whole park on today's outline. Nothing is ever decided from licence text.
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
9. **Public files carry no record keys, licence words, reasons or store names.** `fallback` says only "kept today's outline",
   and credits are per park. The reasons go to the private `--report` file, which must be outside the output folder.

## Commands

```
python3 tools/kpc_display_copy.py build --store STORE_DIR --area US-NH [--area US-ME] --out OUT_DIR \
        --doubtful tools/kpc_display_doubtful.csv --key-dir data/us-key --report /private/report.json
python3 tools/kpc_display_copy.py check --out OUT_DIR --area US-NH --public
tools/kpc_display_publish.sh https://github.com/<owner>/<repo>.git OUT_DIR US-NH US-ME
```

`--private-preview` skips the licence gate (and may read an older index) for a person's own look on their PC. Its output is
stamped PRIVATE PREVIEW in every file, which `check --public`, the publish script and the loader all refuse.

**The publish script:**
- tells "branch missing" (first publish) from "cannot read the remote" (stop);
- fetches the published commit and checks it is the one it listed;
- replaces only this run's areas and checks every area of the new tree with `check --public`;
- then makes one atomic push: `map-display` moves only if it still points at the old commit, and `map-display-prev` moves to
  that old commit.

Any problem stops it before the push.

## What is NOT in this change

- **The hook in `kpc-padus-layer.js`** (with `?v=` bumps on 21 pages and the tests that pin them). It comes in a separate pass
  after an independent grade.
- **Workflow changes:** the Pages step, the publish workflow, and `filter: blob:none` on the five `fetch-depth: 0` checkouts.
- **Any real display data.**

Rules hashes: unchanged (no rule file, scope file or key data is touched). Rebuild level 1.

KPC owner, 2026-11-14
