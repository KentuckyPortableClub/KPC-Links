# Why so many park boundaries are missing (Nov 11, 2026)

Checked on `main` at cb20065 (after #124, #125 and #126). Everything here is read offline from files in the repo: `data/us-key/US-XX.json`, `data/outlines/US-XX.geojson.gz`, `data/outlines/solver-queue/`, and git history since Oct 30 (a shallow history; no map server, no release download). The CSV `docs/boundary-gap-nov11.csv` lists every missing park with its cause, and `tools/kpc_boundary_gap.py` rebuilds both the CSV and these counts (`--history` adds the "dropped in run" column).

## The short answer

The key lists 13,107 parks. 6,678 have an outline in their own state's file and **6,429 do not**. Three causes explain 91% of them:

| # | Cause | Parks | Share |
|---|---|--:|--:|
| 1 | **Joined in the key, but no outline was ever built.** The key already says which agency records make up the park. The step that turns those joins into an outline file (`kpc_outlines_from_key.py`) has been run by hand once, for 11 states (#125). No workflow runs it. | **4,689** | 73% |
| 2 | **No join: a record exists but the rules did not accept it.** 677 have the pin inside a record whose name does not agree (265 of them BLM Recreation Management Areas, 55 State Recreation Areas), 57 have a similar name that the rule rejected, 11 have a same-name record far from the pin. | **745** | 12% |
| 3 | **No saved layer record near the pin.** Nothing in any saved layer is close. Mostly State Historic Sites (83), Historical Monuments (37), BLM RMAs (35), State Recreation Areas (30), Fish Hatcheries (30). Worst states: NV 60, OK 36, MS 35, UT 35, ND 34. | **470** | 7% |

The rest: 300 parks joined only to a trail line (drawn by the trails layer, no outline by design), 176 held on purpose (125 "a person said NO", 24 old-id holds in NV, the rest rule holds), 30 whose outline sits only in a neighbour state's file, 19 joined to a record that has no shape.

## What the brief assumed, and what the files show

- **"About 1,413 parks with no layer at all."** The key has 1,434 bare pins, but only **470** have no layer record near the pin. 745 have a candidate that failed a join rule, and 176 are held. So the true "no layer" number is about a third of that figure.
- **"Lost between runs."** No outline was dropped from `data/outlines` (the files first appear Nov 10 and every commit since only adds). The key did lose joins, and 208 of the missing parks were once joined official and are not now (table below). Most of that is by design or already fixed, but two are worth a look.
- **"Failed joins sent to the solver queue."** The queue is both noisy and incomplete. It holds 4,225 parks in 9,466 rows, and **3,519 of those parks are already official in the key** (the layer trim did not match them in that layer, another layer did). Meanwhile **787 of the 1,215 parks in causes 2 and 3 are not in the queue at all**. The key's own candidates (`c` and `a` lists) never reach it.
- **Cross-group overwrite and the FL Keys read** (#126). Both are fixed on main. The history shows no loss that I can pin on an overwrite. FL has 164 joined-but-not-built parks like every other state, so the Keys read is not a visible cause now.

## Cause 1 in detail: nothing builds outlines from the key

`kpc_outlines_from_key.py` reads each state's saved copy (`US-XX.json.gz` on the boundary-cache release) and builds an outline for every joined park that has none. In the 11 states where it ran (CT DC GA LA ME MI MS NC NJ NY SC) it left **zero** joinable parks behind: the 210 parks still missing there are 173 bare pins, 36 trail-only and 1 other. So it works, and it is the whole gap for the other 39 states. The name-and-pin outlines (3,860) that exist elsewhere came from the master step trimming individual agency layers, which only covers the layers that were downloaded.

Examples: AR has 306 key parks and 123 outlines. Of the 183 missing, 129 are joined-not-built, 21 no layer record, 18 trail-only, 9 name failures, 5 held. OH: 276 key parks, 136 outlines, 137 joined-not-built, 1 no layer record, 2 trail-only. The key says 274 of OH's 276 parks are official, so almost all of its gap is cause 1.

**Fix (needs the saved copies, so it runs on the box, not here):**
`python3 .github/scripts/kpc_outlines_from_key.py --cache <boundary-cache dir> --states "<the 39 states>"`, commit the `US-XX.geojson.gz` files, same as #125. Expected: about 4,400 new official or approximate outlines. #125's 2,429 outlines added about 2.3 MB, so expect roughly 5 to 10 MB more in `data/outlines` (now 7.5 MB); western states have bigger shapes. The tool skips a park when any joined record is not in the saved copy and prints it, so run it once with `--dry-run` and read the skip list first. I could not do this here: GitHub is not linked for this session (no release download) and `shapely` is not installed. Longer term, one small step in the US key workflow's finish (read the saved copy, run this tool, commit) would keep it from falling behind again. That touches the workflow and the master step, which is #126's area, so I left it.

## Cause 2 and 3: the joins that need a person or a rule

- 677 of the 745 are "pin is inside a record, no name agrees". Typical: a BLM recreation site whose POTA name is the campground, inside the field office's RMA record. These need a name-alias rule or a person's yes; they are not data gaps.
- 470 "no layer record" are 427 not in the queue, so nobody is looking at them. A small queue file per state from the key's own failures would fix that (see the proposal below).
- 24 NV Herd Management Areas are held on purpose: a person said NO to the land under its old id (for example `sgnvi432 = hma28`), and the key carries that NO forward. A test pins this on purpose (`test_us_key_holds_nov8.py`), so it is not a bug. The only question for the owner is whether that NO still stands, because the pins sit 0.6 to 10.8 km from the record (10 of the 22 with a distance are 4 km or more, which is probably why they were refused). If it does not, these are 24 official outlines waiting.

## Lost between runs

Parks that were official-and-joined in an earlier key run and are not now: **208** of the missing ones. By run:

| Run (date, commit) | Parks | What the files show |
|---|--:|---|
| 11-01 `47057815` | 54 | ID. 53 of them are now approximate, so most likely the Nov 1 approximate tier moving them, not a loss. |
| 11-03 `8471cf67` | 35 | Spread over 21 states, mostly now bare pins. |
| 11-08 `29838a53` | 25 | NV. 24 are the held Herd Management Areas above (a deliberate hold, so not a bug). |
| 11-02 `e343acc1` | 23 | Spread over 13 states. |
| 11-10 `2e1a0d6e` | 22 | MN 7, ND 5, SD 3 and 4 other states. The PAD-US record count in the key for ND dropped from 2,168 to 1,484 in the same run, SD from 1,797 to 1,299. |
| 11-01 `b9b7d495`, `2d7956fb` | 31 | 15 in AR (`2d7956fb`); 16 in 11 states, OR 4 most (`b9b7d495`). |

The shrinking counts are the signal. Runs where a state's PAD-US record count in the key fell more than 10%: WI 80,934 to 1,585 (Nov 6), ND 2,168 to 1,484, SD 1,797 to 1,299, IN 1,985 to 1,528 and MO 5,990 to 5,006 (all Nov 10), DE several times, VT 2,001 to 1,492 (Nov 4). A short read can quietly cost a few joins. The whole-layer reader and the save-check gate from the review fixes (#120, #121) are meant to stop that, but the first full US run after #126 is the test. The cheapest guard: compare the new key's official count with the last commit's and fail the postcheck when a state drops more than 3%. (The postcheck already warns at 5% for the whole key.)

## Smaller things found

- 30 parks have their outline only in a neighbour's file (CA file holds NV parks, TX holds NM, and so on). The map draws a file when that state is in view, so it shows for a viewer on the border but not otherwise; the park's own state never sees it. 152 more are in both files, which is fine. Fix: copy them into the home state's file in the next build.
- 3 MS outlines name `file:_tmp-ms-proj.geojson.gz` as their source, a temporary file name that should not be in the record.
- 19 parks joined to an agency record that has no shape (MN, ND and MI Wetland Management Districts). They stay bare pins.

## Per state

| State | Key parks | Have outline | Missing | Joined, no outline built | Name join failed | No layer record | Trail only | Held | Other |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| AK | 179 | 72 | 107 | 62 | 20 | 9 | 3 | 13 | 0 |
| AL | 155 | 52 | 103 | 79 | 4 | 13 | 1 | 4 | 2 |
| AR | 306 | 123 | 183 | 129 | 9 | 21 | 18 | 5 | 1 |
| AZ | 119 | 13 | 106 | 87 | 8 | 3 | 7 | 1 | 0 |
| CA | 411 | 16 | 395 | 366 | 10 | 5 | 6 | 8 | 0 |
| CO | 276 | 90 | 186 | 167 | 4 | 3 | 7 | 4 | 1 |
| CT | 157 | 147 | 10 | 0 | 5 | 2 | 3 | 0 | 0 |
| DC | 35 | 24 | 11 | 0 | 3 | 0 | 6 | 1 | 1 |
| DE | 89 | 56 | 33 | 23 | 2 | 1 | 6 | 1 | 0 |
| FL | 460 | 271 | 189 | 164 | 14 | 4 | 1 | 6 | 0 |
| GA | 238 | 225 | 13 | 0 | 3 | 6 | 2 | 2 | 0 |
| HI | 103 | 43 | 60 | 46 | 8 | 1 | 1 | 3 | 1 |
| IA | 181 | 128 | 53 | 48 | 1 | 0 | 3 | 0 | 1 |
| ID | 362 | 29 | 333 | 194 | 101 | 18 | 12 | 7 | 1 |
| IL | 219 | 135 | 84 | 76 | 1 | 0 | 3 | 3 | 1 |
| IN | 229 | 119 | 110 | 96 | 6 | 5 | 1 | 2 | 0 |
| KS | 145 | 118 | 27 | 0 | 4 | 16 | 7 | 0 | 0 |
| LA | 123 | 115 | 8 | 0 | 1 | 5 | 0 | 2 | 0 |
| MA | 421 | 238 | 183 | 169 | 6 | 4 | 3 | 0 | 1 |
| MD | 186 | 104 | 82 | 63 | 3 | 2 | 7 | 4 | 3 |
| ME | 148 | 140 | 8 | 0 | 3 | 3 | 1 | 1 | 0 |
| MI | 388 | 352 | 36 | 0 | 8 | 18 | 8 | 1 | 1 |
| MN | 319 | 218 | 101 | 73 | 2 | 4 | 15 | 1 | 6 |
| MO | 561 | 150 | 411 | 394 | 0 | 5 | 8 | 4 | 0 |
| MS | 155 | 102 | 53 | 0 | 16 | 35 | 0 | 1 | 1 |
| MT | 254 | 172 | 82 | 70 | 5 | 1 | 5 | 1 | 0 |
| NC | 253 | 221 | 32 | 0 | 6 | 10 | 6 | 10 | 0 |
| ND | 155 | 109 | 46 | 0 | 5 | 34 | 2 | 0 | 5 |
| NE | 201 | 182 | 19 | 0 | 3 | 8 | 5 | 3 | 0 |
| NH | 206 | 106 | 100 | 84 | 4 | 6 | 3 | 1 | 2 |
| NJ | 134 | 128 | 6 | 0 | 2 | 2 | 2 | 0 | 0 |
| NM | 124 | 14 | 110 | 85 | 10 | 8 | 7 | 0 | 0 |
| NV | 367 | 109 | 258 | 85 | 77 | 60 | 5 | 31 | 0 |
| NY | 851 | 825 | 26 | 0 | 14 | 4 | 5 | 3 | 0 |
| OH | 276 | 136 | 140 | 137 | 0 | 1 | 2 | 0 | 0 |
| OK | 205 | 154 | 51 | 0 | 10 | 36 | 5 | 0 | 0 |
| OR | 440 | 184 | 256 | 195 | 26 | 16 | 10 | 7 | 2 |
| PA | 494 | 134 | 360 | 346 | 1 | 3 | 6 | 0 | 4 |
| RI | 61 | 19 | 42 | 38 | 1 | 1 | 1 | 1 | 0 |
| SC | 167 | 160 | 7 | 0 | 3 | 1 | 2 | 0 | 1 |
| SD | 120 | 79 | 41 | 33 | 1 | 1 | 3 | 0 | 3 |
| TN | 277 | 63 | 214 | 190 | 5 | 8 | 5 | 1 | 5 |
| TX | 222 | 31 | 191 | 170 | 6 | 9 | 3 | 1 | 2 |
| UT | 692 | 107 | 585 | 265 | 217 | 35 | 48 | 17 | 3 |
| VA | 184 | 20 | 164 | 134 | 3 | 1 | 21 | 3 | 2 |
| VT | 109 | 57 | 52 | 34 | 3 | 1 | 2 | 11 | 1 |
| WA | 536 | 289 | 247 | 201 | 27 | 12 | 5 | 2 | 0 |
| WI | 348 | 217 | 131 | 109 | 9 | 2 | 3 | 3 | 5 |
| WV | 172 | 36 | 136 | 123 | 1 | 6 | 5 | 0 | 1 |
| WY | 294 | 46 | 248 | 154 | 53 | 21 | 10 | 7 | 3 |

"Joined, no outline built" is cause 1. "Other" is no-shape, other-state-file and far-pin parks.

## Tests

`kpc_preflight.py` on a clean tree: no hash moved, no workflow touched, no file over 1 MB (the CSV is 0.95 MB; gzipped it would be 0.1 MB), no forbidden host or name. Suite 169/171; the two failures are `test_maprep_state_search_fast_nov8` and `test_tracts_nov7`, both known to fail on main. actionlint is not installed here.

Note on the counts: 17 parks are counted as "held" although the key still joins them as official (a hold on one extra candidate, or a record shared with another park). The outline builder would build most of them, so cause 1 is really about 4,700. That does not change the order of the causes.

## What I did not do

Run the builder (no saved copies, no `shapely`), verify that each joined park's records are in its saved copy (the skip list will say), or touch the key join, `kpc_master_cli` or FL (#126's areas). Only this report, the CSV and the offline script are in the PR. No rules hash changed.

KPC owner, 2026-11-11
