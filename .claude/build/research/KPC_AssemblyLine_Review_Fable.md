# 2-FER ASSEMBLY LINE: REVIEW (Fable, chat 2, Tue Oct 27 ~7:30 PM CDT; read only, nothing changed)

What was reviewed (as on main at 00:20 UTC Oct 28): KPC-Data `.github/workflows/kpc-fers-line.yml` (fetcher → worker → checker),
`kpc-fers-regions.yml` (3 regions side by side), `kpc-fers.yml` (single state), and in KPC-Links `.github/scripts/kpc_http_cache.py`
(the bundle), `kpc_push_data.sh` (the safe save), `kpc_fers_line_check.py` (the verdict), `kpc_fers_expected.py`, `kpc_fers_known.py`,
`kpc_pota_pairs.py`, `kpc_overlay.sh` + `.github/kpc-moved.txt` (reading KPC-Data's copies), and the parts of `kpc_fers.py` the line
drives (passes 1-3 + 5, `late()`, the NHD back-off, `slim()` / `sharp_shape()`, rule 15). Checked against the 15 rules in
notes/mapping.md and my two earlier reviews (`KPC_2fer_DesignReview_Fable.md`, `KPC_Boundary_DesignReview_Fable.md`).
I also read the FIRST REAL RUN (Kentucky, run 40604891648, 23:50-00:12 UTC) after it finished; it was not touched.

## 0. The one-paragraph verdict
The design is right (three stages, one bundle, one save, a written verdict) and the engine under it is the same one that passed
Kentucky with chat 8. But the line as built LOST ITS FIRST RUN SILENTLY AND WENT GREEN: the fetcher did all 555 Kentucky pairs in
20 minutes (the NHD back-off works), then its bundle upload failed, the worker ran passes 3 + 5 on an empty folder in 48 seconds,
the checker wrote `STOPPED` and the run finished green. Nothing emailed, nothing in git except the verdict file, the fetcher's work
is gone (it was never uploaded) and KPC-Data has NO release at all. Four small fixes (A1-A4 below) make the line trustworthy;
they are all one-line or a few lines. **Kentucky has to be run again from `stage=all` after A1-A4.** Ohio must not go through the
line before A1-A6.

## 1. What the first run showed (facts from the run's own notes)
| Stage | What happened | Why |
|---|---|---|
| Fetcher | POTA history 193/193 parks (4 min). Pass 1: 555 of 555 pairs tested, no 'stopped for time' (20 min). Pass 2: 118 pairs, 350 spots, 324 agree. Printed "fetcher bundle 9.1M". | Good: with `NHD_DOWN` the water map's 502/504s no longer eat the pass. |
| Fetcher → release | `gh release view/create/upload fers-bundles` ran with NO `-R`, from the KPC-LINKS checkout. gh infers the repo from the working folder's git remote, so it tried KPC-LINKS with KPC-Data's token: create = no permission, upload = no release. Both ends `\|\| true`. | The bundle was never uploaded anywhere. KPC-Links has only `site-pdfs` + `boundary-cache`; KPC-Data has no releases. |
| Worker | "no bundle yet: run stage all". Ran pass 3 + 5 on an empty `data/fers` (0 spots, 48 s), then "worker bundle 160K" (upload also failed: no release). | A missing bundle is a notice, not a stop. |
| Checker | `STOPPED: no test file; no missing-check file; US-KY: no 2-fer file`. Saved `line-ky.json` (the safe save worked). Also: "stopped: [Errno 2] expected-ky.json" (the checker never made `data/fers`) and "stopped: 'PosixPath' object has no attribute 'startswith'" from the observations log (A4). | The verdict is honest, the run colour is not. |

## 2. FIX BEFORE OHIO (A1-A4 also before Kentucky is run again)
**A1. The bundle goes to the wrong repo (the cause of the lost run).** `kpc-fers-line.yml` fetcher "Bundle up" and "Tools + saved outlines":
every `gh release …` call there has no `-R`; the working folder is the KPC-Links checkout, so gh targets KPC-Links. The worker's
calls carry `-R ${{ github.repository }}` and are right. Fix: `-R ${{ github.repository }}` on all four fetcher calls (view, create,
download, upload). Effort: 4 edits.

**A2. A failed bundle upload / download must stop the line, not print a size.** Today `gh release upload … \|\| true` then `du -h`
prints a size whether or not it went up; the worker's "no bundle yet" is an echo and the passes run anyway on nothing; the checker
then grades an empty folder. Fix: (a) fetcher + worker: `gh release upload … \|\| { echo "::error::bundle upload failed"; exit 1; }`
(the step is `continue-on-error: true`, so make the step's outcome visible: drop `continue-on-error` on "Bundle up" so the job goes
red = Brandon's email, which HQ asked for on a lost save; the same rule applies to a lost bundle); (b) worker: if the download or
`tar xzf` fails, `exit 1` before the passes; (c) after `tar xzf` check the expected files exist (`data/fers/<state>.json` for each
state in `STATES`, or for tag ky `US-KY.json`). Also write a tiny `bundle/stamp.json` {stage, tag, states, date, run id} at each
"Bundle up" so the next stage can refuse a bundle from the wrong tag or an older run. Effort: ~15 lines.

**A3. The verdict must check the passes really ran, not only 'waiting' rows.** `kpc_fers_line_check.py` says READY whenever
known-answers passes, the missing check has a reason for every pair and no row says 'waiting'. Three silent paths give READY on bad
data: (1) pass 1 'stopped for time' (untested pairs are simply absent: no rows, no 'waiting'; the earlier Kentucky run tested 28 of
555 this way and nothing but a counts line said so); (2) pass 2 or 3 killed by the step timeout before its save (rows keep status
'pass 1' / 'pass 2'; the missing check calls those DROPPED with a non-empty reason, so `pass` stays true); (3) a stale bundle (the
worker's upload failed, the checker read the fetcher's pass-2 bundle). Fix in `kpc_fers_line_check.py`: for each state file require
`pass1`, `pass2`, `pass3`, `pass5` all == today (or ≥ the run's start date), read `report-<tag>.json` and STOP on
`pass1.stopped for time` / `pass2.stopped for time`, STOP if `looked-<tag>.json` 'tested' < 'pairs whose boxes touch', and count
rows whose status is still 'pass N' as 'not finished'. Also report (not fail) the NOT SURE counts: 'water not checked', 'ownership
map did not answer', 'two owners', so chat 8 sees how much is parked. And `mkdir -p data/fers` in the checker before the scripts
(the expected builder crashed on a missing folder). Effort: ~25 lines.

**A4. The observations log has crashed on every run since ~6:15 PM (chat 2's own B6 edit).** `kpc_map_observations.py`
`now(path)` now does `path.startswith(MOVED)`; line 177 calls `now(OUT)` with a `pathlib.Path` → AttributeError → the script's
top-level `except` prints "stopped: 'PosixPath' …" and writes NOTHING. That hits the line's checker, `kpc-fers.yml`, the regions
workflow and tomorrow's daily `kpc-watch.yml` (11:53 UTC). Fix: `path = str(path)` at the top of `now()` and `head()`. Effort: 2 lines.

**A5. The worker reads KPC-Data's moved data through a sparse clone that can fall back silently.** The worker job has no
`kpcdata` checkout; `kpc_overlay.sh` (no argument) does a `git clone --filter=blob:none` + sparse checkout of KPC-Data, and on any
failure prints "using this repo's copies" and exits 0. Those copies (`data/trails`, `data/parkinfo`, `data/access`) are the ones
B6 part 2 will delete from KPC-Links: after that, a failed clone means pass 3 runs with NO trail lines → every trail pair's row
becomes 'dropped in pass 3', a wrong answer with no notice (`trail_lines()` is try/except; 'with official lines: 0' is only a counts
number). Fix: give the worker the same `actions/checkout` of KPC-Data (`path: kpcdata`) + `kpc_overlay.sh kpcdata` as the other two
jobs (1-2 min, no network luck involved), and make `kpc_fers.py` STOP a pass when `with official lines` is 0 for a US state run or
`data/parkinfo` is missing (the line's known-answers would also catch Kentucky, but not Ohio). Effort: 6 lines + one guard.

**A6. The checker can write back other states' files from its snapshot.** The bundle carries ALL of `data/fers` (every state, the
world files) from the fetcher's checkout; the checker copies every file that differs from main at checker time. Today this is safe
only because every writer of `data/fers` shares the concurrency group `kpc-fers`; the day any job outside the group writes there
(a watch, a hand fix, the Kentucky lines step that was deleted, a second regions workflow), the line reverts it. Fix: in the
checker copy back only `<state>.json` for the run's states + the tag's own files (`report-/looked-/expected-/missing-/same-outline-/
line-<tag>.json`, `pota-pairs-<state>.json`, `known-answers.json` for ky), and only include `data/fers/<states>` + tag files in the
bundle (also makes the bundle 10x smaller and keeps the 94 MB `W-FR.json` out of every tar). Effort: 10 lines.

## 3. FIX LATER (before the regions run side by side, or in the first monthly cycle)
**B1. Bundle growth and old answers.** `kpc_http_cache.py` never deletes: an answer older than `HTTP_CACHE_DAYS` (21) is ignored
but stays in the bundle and is re-uploaded for ever; a big western state at pass-3 detail (BLM surface management tiles, NHD water at
2e-5°) could reach hundreds of MB per bundle (one asset per tag, 50 tags). Fix: before `tar czf`, delete cache files older than
21 days and cap the folder (drop oldest beyond ~300 MB); skip `W-*.json` (A6). Release assets do not count toward the 1 GB repo
limit, but the 2 GB per-asset limit and upload time do.

**B2. Rule 13 wording vs the bundle.** `MAPDATE[r] = 'read live from the agency ' + today` is written even when the answer came
from the bundle (up to 21 days old on a rerun). The spot then shows a map date newer than the data. Fix: `kpc_http_cache.cached()`
returns the file's date with a hit (or sets a module-level 'oldest hit'), and `MAPDATE` says 'read from the agency on <that date>'.

**B3. Pass-2 bundle answers are not reused by pass 3 (expectation, not a bug).** The cache key includes `maxAllowableOffset` and
`geometryPrecision`, which differ per pass (pass 2 = 2e-4/5, pass 3 = 2e-5/6), so the worker re-asks every outline, ownership tile
and water tile at its own detail. The bundle saves a RERUN of the same stage (the stated purpose), not the stage after. Say so in the
workflow comment, or let pass 2 already ask at pass-3 detail for the pairs it keeps (more bytes in pass 2, nothing in pass 3).

**B4. Job timeouts are tight: a slow tar/upload turns a good run red.** Fetcher: 65 + 270 min of steps + setup + bundle inside a
345-min job; worker: 320 + setup + a possibly large tar inside 345. With B1 (small bundles) this is fine; without it a 1 GB bundle's
tar + upload can push the worker past 345 → job timeout → red run → email, for a run whose data was good. Fix: cap `minutes` at 280
or raise the job timeout to 355 (GitHub max 360).

**B5. `sharp_shape()` closes trail stretches.** `slim()` now runs `cv2.approxPolyDP(..., closed=True)` on every `shape` over 80
points, including trail / river stretches (polylines). Closing joins the two ends, so the simplification can drop a true end point
and draw the last few metres of a stretch wrong. Fix: `closed = (kind == 'area')`. Tiny visual issue; chat 3 draws `zone` now anyway.

**B6. Known-answers freshness in the verdict.** `kpc_fers_line_check.py` accepts `known-answers.json` of any age (the engine guard
`known_ok()` in `kpc_fers.py` wants ≤ 7 days, but it only runs for all-US pass 1, which the line never does). A Kentucky pass from
weeks ago would let Ohio through after an engine change. Fix: require ≤ 30 days, and print its date in the verdict (already there as
found/required, add date).

**B7. `kpc_push_data.sh` and paths with spaces / many files.** `for f in $CH` splits on whitespace; fine for `data/fers/*.json`,
wrong the day a path has a space. Use `git diff --cached -z` + `while read -d ''`. Also the script's `git add -A $CH` after the
reset: a file DELETED on main meanwhile is re-added from the snapshot (correct for this job's files, by design).

**B8. The POTA history step on a big state.** `kpc_pota_pairs.py` = 1 request/s, 60-min cap: Texas (~900 parks) or California fit;
a region job (southeast ≈ 1,800 parks) will stop at ~3,500 parks → `complete: false` → re-read next run. Fine, but the regions
workflow gives it 60 min per JOB: nine states × 1 s each ≈ 30 min, OK. Just note `complete:false` in the verdict.

**B9. Concurrency groups.** `kpc-fers`, `kpc-fers-regions` and `kpc-fers-line` share group `kpc-fers` (good: no two writers of
`data/fers` at once), so the line and the regions cannot overlap at all; a queued run is cancelled by a newer queued run (GitHub keeps
one pending per group). That is the intended "one at a time"; say it in the workflow comments so nobody dispatches Ohio's line while
the regions run and wonders where it went.

**B10. `HTTP_OFFLINE=1` in the checker is harmless but misleading.** None of the checker's scripts call `get()`; the flag suggests
the checker re-runs engine code offline. Either drop it or (better, later) have the checker re-run `kpc_fers_known.py`-style spot
checks through the bundle so a reviewer can replay a spot without the network.

## 4. FINE (checked, no change)
- The three-stage split, time split (pass 1 ≤ M/3, pass 2 ≤ 2M/3; pass 3 4/5, pass 5 1/5) and `late(screen=True)` at 70% of pass 3
  follow my 2-fer review #1; pass 1 did all of Kentucky in 20 min once the NHD back-off was in.
- `NHD_DOWN`: two failures → 'not checked' for 10 min; a 'not checked' answer is never written to the bundle (errors are not cached),
  and rows stay NOT SURE (rule 7), never 'no water' (chat 8's KY note 3). Correct.
- `kpc_push_data.sh`: only this job's changed files, fresh `main`, no rebase, six tries, STRICT → red. The checker used it and pushed.
  `--diff-filter=D` deletes are replayed. Safe against chat 5's bots pushing in between (the thing that lost the earlier KY run).
- Bundle mtimes survive `tar` (GNU tar restores them), so the 21-day age works across stages. Cache keys include the full query
  (`where`, offsets, SR), so partial pages and tiles never collide.
- Files over 20 MB are gzipped before the save (limits plan L-b); `gzip -9n` is deterministic, so an unchanged `W-FR.json` round-trips
  to identical bytes and is not re-committed (lucky but true; A6 makes it moot).
- Regions side by side: each job has its own `RUN_TAG` files, state files are per state, the observations log is written ONCE by a
  job after the matrix, each job's `cmp` loop compares against its own checkout so it never copies another job's states, and
  `max-parallel: 3` keeps PAD-US / NHD / agency load at 3. Safe as designed; A6's whitelist makes it safer still.
- Email noise: fetcher and worker never fail by design; the checker fails only on a lost save (HQ's wish). After A2 a lost BUNDLE
  also fails (one more honest email, never a repeating one).
- Memory: 600-tile caches + per-tile rasters; a 16 GB runner is fine for a state or a region.
- The overlay in the fetcher and checker uses the real `kpcdata` checkout (good); `.github/kpc-moved.txt` lists exactly the moved
  paths; `skip-worktree` keeps the staying KPC-Links bots from saving overlaid files back.

## 5. The 15 rules, as the line applies them
| Rule | Where in the line | Verdict |
|---|---|---|
| 1 park = designation; 1b agency land only | `OWNED` + `pmask()` through `kpc_owned.py`, same in every stage | FINE |
| 2 public + open | `pad_use()` / closed areas, `decide()` | FINE |
| 3 / 14 layered vs side by side, NOT SURE when the map cannot tell | `ownership_step()` in pass 3 (worker); 'ownership map did not answer' → NOT SURE | FINE; A3 adds the counts to the verdict |
| 4 size tiers (100 / 50-100 / 25-50 / under 25) | pass 3 core `TIGHT_SHRINK`, `slim()` tiers | FINE |
| 5 rivers/trails: corridor = area; line-only = 100 ft from the bank / line | `water_route_spots()` (bank = NHD), `line_spots()` | FINE |
| 6 sources best first | saved key → fresh agency download / Kentucky live layers | FINE; B2 for the date wording |
| 7 NOT SURE kept out, never a 'no' | statuses `not sure: …`, the Finder hides them | FINE |
| 8 POTA only, 'we think', notices | wording in `ABOUT` on every file | FINE |
| 9 water only separate | pass 5 `land_check()` → '🚤 Water only' | FINE |
| 10 closed / restricted | `pad_closed()`, `ACC` notes | FINE |
| 11 n-fers share one patch | `tidy_rows()` folds pairs into the n-fer | FINE |
| 12 missing boundary list | `missing-<tag>.json` from pass 1 | FINE |
| 13 last checked + map dates; retired out | `checked`, `map_dates`, `RET` | B2 (bundle date) |
| 15 trail strip ≥ 10 yd somewhere | `add_zones()` → `rule15()` in pass 5 (worker) | FINE; B5 cosmetic |
| Missing check + known answers | checker | A3 (must also check the passes finished) |

## 6. What to run, in order
1. A1-A4 (≈ 45 lines in all), one push each repo. 2. Kentucky through the line again, `stage=all`, tag `ky`: expect the fetcher's
20-30 min, a worker of 1-2 h, a verdict with known 18/18 and the missing check. 3. Chat 8's Kentucky look. 4. A5 + A6 before Ohio.
5. B1-B4 before the first regions run; B5-B10 in the monthly cycle.

Sources: the files named above at KPC-Links `main` 39681be8…/KPC-Data `main` 54186ccc; run 40604891648's job steps + annotations
(read through the REST check-runs route); notes/mapping.md rules 1-15; `KPC_2fer_DesignReview_Fable.md` §3 + #1/#8;
`KPC_Boundary_DesignReview_Fable.md` §3 (drift / dates).
