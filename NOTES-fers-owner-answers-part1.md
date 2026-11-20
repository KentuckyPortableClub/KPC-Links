# 2-fer owner answers, part 1

## What is NOT built

- Part 2 is not built: the math-guard fingerprint, the byte-for-byte test changes, and deleting `data/status/test_fers_final_redact_nov17.json`.
- Part 3 is not built: the bot does not yet write `not-sure-rows-<tag>.json`.
- Part 4 is not built. The review (19 Nov, section 5) says yes to a second look later, on its terms, and no to the numbers in the proposal below. No finer-grid code was written in this round. `merge()` was not changed.
- The Kentucky path was not folded into the national one, and no Kentucky file was changed.
- No real area was run. No key, outline, or KPC-Data file was changed.
- Nothing was pushed to `main`. No workflow was started. No pull request was merged.

## Third round (review of 19 Nov, A and B)

Rebased onto `origin/main` `9ee20aa`. Main's 2-fer hash, from `kpc_preflight.base_hash`, is `0637d083bd98`. This pull request's final hash is `40c9a5c612c6`. One changelog line: `0637d083bd98` -> `40c9a5c612c6`. The round hashes (`a18d26726099`, then `8fb1b48a66a8` before this round's code) stay here, not in the changelog.

A. The outline stamp now records the pass, the detail and the decimal count it was hashed at (`outline_detail`). A later run compares that hash only when it holds the outline at the same pass detail, and the coordinates are not a coarser rounding. Otherwise the row is copied on the key entry only and counted. A pass 3 stamp checked in pass 1 is that case. At the same detail, a changed outline is not copied. A pass-1 hash was not also written onto pass 1 rows: those files are compared byte for byte, and the rows are not decided until pass 3.

B. `written_by_rule` is set only on the dict pass 1 builds. `save_json` is main's one line again. A later pass saves the file it loaded, so the mark stays if pass 1 wrote it and stays off if the file is still the old one.

## Second round (review of 19 Nov, sections 1.1 to 1.7)

The 2-fer rules hash moved `a18d26726099` -> `8fb1b48a66a8`. US, Canada and world did not move (`c64b8ace0411`, `dfef94b3dfd3`, `b1f23bf0deea`). Scope entry `2026-11-19-r2f4-stamp-complete`, scope `none`. No park was remeasured, so there is no park-by-park change list. The 127 summary-map parks are the same list as the first round.

1. Every row pass 3 settles carries `made_on`, whatever its status. That is every normal return of `decide()`, and the two rows pass 3 settles without calling it: "dropped in pass 3" and "the outline could not be read". A known-answer row, a water-only row, a not-sure row and a dropped row all keep the stamp, and a later run that does not read those parks still copies them.
2. The key fingerprint now includes `parts` and `approx`, which the loader already reads. A Kentucky tract keeps its acres and its how, the same four fields as a US joined row. The fifth tract number is a count and is not in the stamp.
3. A run that is not a store run stamps the outline hash `pair_fp` reads for that park: the outline, and the line without the read date. The field `outline_kind` is `outline` or `store`, so the two are never compared with each other. When this run has the park's outline in hand, that hash is checked. When it does not, the check is the key entry only, and the report counts those rows: `rows copied on the key entry only (this run did not read the park)`.
4. An area file this code writes carries `written_by_rule` = `R-2F4`. The "still from before this rule" list reads that mark, and only for areas of this run's region. A file the run just wrote is not on the list.
5. The two older tests that failed on this branch are brought up to date, line by line, below.
6. The separate-piece reason now says "its box meets the box of a listed spot". KA-13 is tested on the real grid, with shapes. 120 m apart is two spots. 44 m apart is one spot, because `merge()` joins pieces within 0.0005 degrees. Olympic National Park and Olympic National Forest are decided like any other pair, the same as Grand Canyon and Kaibab.
7. `kpc_fers.py` uses the one switch reader, so the environment notice is printed whichever path asks. A missing or broken `data/state-gis.json` (or `data/us-key/layers.json`) is printed as an error; R-2F1 is not off in silence. The R-2F7 count line is printed in the run log and kept on the store area row. A person opens `data/fers/store-missing-<tag>.json` and reads `areas` -> that area -> `shelf`.

### Tests brought up to date

- `tests/test_fers_area_boxes_time_nov11.py`. The golden was `6d7c5c5b7e33a0c5`. On this code, numpy 2.5.3 and OpenCV 5.0.0, it is `f757225e9e94173c`. `US-WA.json` carries `written_by_rule` `R-2F4`. The report's pass 1 does not list US-WA as still from before this rule, because the run just wrote that file and the file carries the mark. The file still has its two rows. The review had found that, before this fix, only that report line differed and `US-WA.json` matched main.
- `tests/test_fers_one_program_nov16.py`. The switch file's value for `KPC_FERS_FINE_ONLY` is `count`, so the test no longer expects the count to be off when the environment is quiet. The private-folder file's `mode` is `count`. The made-up spot now has `wide_m` 30 and a box that does not meet the listed row's box, so the size test and the box test can run. Setting the environment to `off` still lists the spot and adds no row.
- `tests/test_fers_store_switch_nov15.py`. The byte compare leaves `written_by_rule` out of the area file before it compares. The spots match. Scope `none`: no pair is re-stamped. The report keys this test already ignores are unchanged.

## Part 4 proposal (no code)

A store run reads the same shapes in every pass. The code already says those shapes are about 2 m (`STORE_PASS2_NOTE` in `kpc_fers.py`). Pass 3's grid is 5 m (`CELL`). R-2F3 marks an area row NOT SURE when its measured width is within that one cell of 22.86 m or 45.72 m. On the saved 472-row file that is 380 rows (226 at 25 yards and 154 at 50 yards), water-only rows left out.

Before the bot gives up on such a spot, it could measure that spot again on a grid whose step is the store's own stated detail (about 2 m), and only that spot. The rest of the pair stays as it was. The error left after that is one cell of the finer grid. That number is the store's stated detail, already written in the code. It is not a new number.

The cost is one extra raster of the two outlines, for the spots already inside the 5 m band, not for every pair. The shapes are already in memory on a store run. I did not time it, and I did not remeasure the 43 widths in `known-answers/grid-readings.csv`. Those 43 by 16 readings stay the record of the 5 m grid. A finer pass would be aimed only at the readings that land inside one 5 m cell of either size line. I do not say how many of the 380 would then be sure.

## Baseline

KPC-Links `main` at the start of this work was `7b36ae5` (the hand-off names `5e84846`; that commit is the parent of a notes commit, and this checkout was shallow). The 2-fer rules hash on that tip was `0637d083bd98`, the hash the hand-off names. The first round moved it to `a18d26726099`. This second round moves it to `8fb1b48a66a8`. US, Canada and world hashes did not move (`c64b8ace0411`, `dfef94b3dfd3`, `b1f23bf0deea`).

The fers rule tests that the rules-check workflow runs were run here and ended ALL PASS, including `tests/test_fers_owner_answers_nov19.py` and `tests/test_fers_handoff9_nov17.py`. The hand-off gate was started on this machine; its last lines are at the bottom if it had finished when the notes were written.

## What is built

One switch file, `.github/fers-switches.json`, read by `kpc_fers_switches.py`. An environment variable of the same name wins, the receipt records the value and `file` or `env`, and the run prints one notice when the environment wins. A missing file, a broken file, or a setting the code asks for that the file does not hold stops the bot with exit 4.

| Setting | In force |
|---|---|
| `KPC_FERS_SUMMARY_APPROX` | on (R-2F1) |
| `KPC_FERS_FED_NEIGHBOUR` | removed, with `fed_neighbours` (R-2F2) |
| `KPC_FERS_NEAR_LINE` | on / off only; the band is `CELL` (R-2F3) |
| `KPC_FERS_CARRY_MADE_ON` | on; the stamp is `made_on` (R-2F4) |
| `KPC_FERS_FINE_ONLY` | `count`; `FINE_100M` and `FINE_GAP_M` removed (R-2F5) |
| `KPC_FERS_STRIP_HELD` | on, with the owner's note (R-2F6) |
| `THIN_SHELF` / `KPC_FERS_SHELF_MIN` | removed (R-2F7) |

The PC runner no longer passes the old settings. The area runner never passed them. Both read the file in the checkout.

The Handoff 9 test kept its other checks. Removed from it, and said here: section 2 (the 8 m band), section 4 (the whole-key age, `KPC_FERS_CARRY_MAX`), the Q2 checks (`fed_neighbours`), and the Q5 100 m checks. The Q1 "setting is off" assertion and the Q6 note text were brought up to date because those rules still exist and the old words do not. The Q6 block sets the copy check off so it still tests the strip.

## Numbers

R-2F1. On main's key files, 127 US parks have every joined record from a summary-map layer. The 17 Nov count of 74 was not reused. Mix: water 66, compilation 32, register 20, Michigan project lines (`mid`) 7, Mississippi general-area (`mszp`) 2. The list is below. A park the key grades `approximate` is already an approximate 2-fer: `decide()` builds `_apx` from `status_for(...) == 'approximate'`.

R-2F3. On `tests/fixtures/fers-wl3-near-line-rows.csv`, water-only rows left out: 226 of 226 at the 25-yard line and 154 of 159 at the 50-yard line are NOT SURE with the 5 m cell (380). With the rule off, 0.

R-2F4. On the made-up fixtures in the new test: a stamped row is copied when the key build id changes and the parks do not; one changed key entry drops that pair and keeps the other; an unstamped row is copied by none of `keep_fresh`, `carry_rows`, `keep_old_rows`, or `carry_held_rows`; a changed store-index `fp` is not copied; a key file that cannot be read, or a park missing from it, is not copied. I did not count rows in the club's real public files. No area was run.

## Kentucky, rule by rule

The Kentucky path (`REGION == 'ky'`) was not changed.

- R-2F1 does not act there. `summary_only` returns false unless the region is `na`.
- R-2F2 is gone everywhere, including Kentucky. It had been off.
- R-2F3 acts on a Kentucky area row that reaches the end of `decide()`. The band is the same `CELL`.
- R-2F4 acts on the copy paths, which Kentucky uses (a small batch, a pair skipped for time). The stamp is written in `decide()`, which Kentucky uses. A Kentucky park's key bits come from `data/ky-answer-key.json` when it is not in a US key file.
- R-2F5 does not act there. Fine-only rows are store runs, and Kentucky never uses the store.
- R-2F6 does not act there. The strip is on a store carry, and Kentucky never uses the store.
- R-2F7 does not act there. The shelf line is a store run.

## Where the outline fingerprint comes from

The store index entry for a park carries `fp` (the same fingerprint `AreaStore.park` recomputes from the record checksums). On a store run, `made_on` stores that and sets `outline_kind` to `store`. The check reads it back from the index. It does not read the outline.

On any other run (Kentucky, the old path, the world), `made_on` stores the outline hash `pair_fp` reads for that park and sets `outline_kind` to `outline`. A store fingerprint and an outline hash are never compared with each other.

A public shelf does not list a park it left off, so that park has no `fp` and the stamp's outline is empty. The check is then the key entry only. That is the empty-outline case. It is not the case of a stamp that already holds an outline fingerprint: if today's index has none, the row is not copied. The reason is "the outline fingerprint changed". The row cannot be proved unchanged. The first-round notes had those two cases as one. They are not.

A private store lists the park, including one that is not publishable, and the `fp` is there.

`made_on` holds, per park, a short hash of the joined rows (`m`: id, name, acres, how), the grade `g`, a `line` field when the key entry has one, `parts` when the entry has them, and `approx` when the entry has it. It does not hold a date, a run id, a count, or the check rows `c`.

## Guesses

1. "Joined" for R-2F5 is tested from the boxes the rows already carry (the `box`, or the box of `shape`). If either box is missing, the new piece is not a row. If the boxes touch, the piece is that spot. A box that touches without the shapes touching is treated as joined. That drops a possible row rather than adding a wrong one.
2. The size test for an area piece is `wide_m` against `SHRINK` (22.86 m, 25 yards), the same test the old fine-only code used. A line piece uses `len_m` against `STRETCH` (25 m), the stretch rule already in the code.
3. Every new scope entry is `none`. Nothing is remeasured. R-2F4 changes which old rows are copied. R-2F5 can add a row on a store run. The notes on those entries say so.
4. The older store tests set `KPC_FERS_CARRY_MADE_ON=0` and, where they need an exact copy, `KPC_FERS_STRIP_HELD=0`, so they still prove never-worse, the same-spot rule, and the leak guard. The shipped file has both on. The new test is the one that proves the on behaviour.
5. The store-off byte comparison's report differs by the new "areas still from before this rule" count. The spot files of the US-RI fixture matched main. The comparison ignores that report key, the same way it already ignores the problem-line note.

## Grey areas

Answered by the review (19 Nov, section 1.8). Left as they are:

1. `decide()` is not called again for a row whose status already starts with candidate, not sure, dropped, very tight, water only, or merged (`todo` in pass 3). A fresh run starts at pass 1, which writes the file anew, so pass 3 decides every row of that new file. Scope `none` stands for R-2F1 and R-2F3.
2. A row stamped on a store run, then copied on a run with no store index, is not copied. That is right. A stamp that holds an outline fingerprint is also not copied when today's index has none.
3. The key carries `line` when a park entry has one. Left as built.

New this round:

4. `merge()` still joins pieces of one pair whose boxes are within 0.0005 degrees. The probe shows one spot at 80 m apart and two at 120 m. That is the measuring math. It was not changed. It is the owner's question G1 in the review. Because of it, two 30 m strips 44 m apart are one spot. KA-13 is: 120 m apart = two spots; 44 m apart = one spot.
5. A small batch still loads every park's saved outline before the box test. A carried row whose park is in that load is checked against the outline hash. The key-only count is the rows whose park is not in the loaded outlines and not in the line table.
6. An area file that cannot be read is not put on the "still from before this rule" list. The rule does not say what to do with a file that will not open.
7. The fifth number on a Kentucky tract is a count. It is not in the stamp.
8. Part 4 is not built in this round. The review's section 5 is the answer, for a later draft.

## What in the hand-off did not match the code

- `main` was `7b36ae5`, not `5e84846`. The 2-fer hash was still `0637d083bd98`.
- Pass 3 does not re-decide an already labelled row (grey area 1).
- The PC runner was passing `KPC_FERS_NEAR_LINE_M=5`, `KPC_FERS_CARRY_MAX=key`, `KPC_FERS_SUMMARY_APPROX=1` and `KPC_FERS_STRIP_HELD=1`. The hand-off said to check that it passes nothing. It does not, now.
- The summary-map recount is 127 parks, not 74. The hand-off said to recount and not to test against 74.
- `partial_only_adds` and `no_denials` did not call the age check. Both now do, so an unstamped row is not put back through them either. `no_denials` only puts a row back when `KPC_FERS_KEEP_DROPPED` is on, which stays off.

## Summary-map parks (R-2F1)

127 parks. Number, name, layer kind.

- US-12679 Fort Egbert BLM Historic Area (register)
- US-10424 Upper White Oak Lake Recreation Area State Fishing Lake (water)
- US-11870 Lake Wilhelmina State Fishing Lake (water)
- US-11873 Iron Fork Reservoir State Fishing Lake (water)
- US-13553 Sugar Loaf Lake State Fishing Lake (water)
- US-13554 Lake Atkins State Fishing Lake (water)
- US-13556 Lake June State Fishing Lake (water)
- US-9167 Lake Hinkle State Recreation Area (water)
- US-1660 Day Pond State Park (compilation)
- US-10921 Hawaii Capital National Historic District (register)
- US-10922 Marconi Wireless Telegraphy Station Kahuku National Historic Site (register)
- US-8283 Glenwood Archaeological State Historic Site (compilation)
- US-11250 Thorn Creek Reservoir BLM Recreation Management Area (water)
- US-11252 GrasmereReservoir State Fishing Lake (water)
- US-11253 Fish Creek Reservoir BLM Recreation Management Area (water)
- US-11257 Crane Creek Reservoir State Fishing Lake (water)
- US-11262 Cedar Creek Reservoir State Fishing Lake (water)
- US-11325 Wilson Lake Reservoir State Fishing Lake (water)
- US-11379 Paddock Valley Reservoir State Fishing Lake (water)
- US-11380 Mann Creek Reservoir State Fishing Lake (water)
- US-11382 Mountain Home Reservoir State Fishing Lake (water)
- US-11383 Little Camas Reservoir State Fishing Lake (water)
- US-11386 Lucky Peak Reservoir State Fishing Lake (water)
- US-11387 Lake Cascade Reservoir Management Area (water)
- US-11389 Long Tom Reservoir State Fishing Lake (water)
- US-11416 Sage Hen Reservoir State Fishing Lake (water)
- US-11418 Brundage Reservoir State Fishing Lake (water)
- US-11419 Lost Valley Reservoir State Fishing Lake (water)
- US-11420 Ben Ross Reservoir State Fishing Lake (water)
- US-11421 Herrick Reservoir State Fishing Lake (water)
- US-11423 Blair Trail Reservoir State Fishing Lake (water)
- US-11424 Bliss Reservoir State Fishing Lake (water)
- US-11425 Stone Reservoir State Fishing Lake (water)
- US-11426 Swan Falls Reservoir State Fishing Lake (water)
- US-11464 Blacks Creek Reservoir State Fishing Lake (water)
- US-11516 Ashton Reservoir State Fishing Lake (water)
- US-11517 American Falls Reservoir State Fishing Lake (water)
- US-11518 Alexander Reservoir State Fishing Lake (water)
- US-11519 Boulder Meadows Reservoir State Fishing Lake (water)
- US-11520 Chesterfield Reservoir State Fishing Lake (water)
- US-11521 Condie Reservoir State Fishing Lake (water)
- US-11522 Crowthers Reservoir State Fishing Lake (water)
- US-11523 Daniels Reservoir State Fishing Lake (water)
- US-11524 Deep Creek Reservoir State Fishing Lake (water)
- US-11525 Devils Creek Reservoir State Fishing Lake (water)
- US-11528 Tripod Reservoir State Fishing Lake (water)
- US-11530 Hells Canyon Reservoir State Fishing Lake (water)
- US-11532 Johnson Reservoir State Fishing Lake (water)
- US-11534 Lamont Reservoir State Fishing Lake (water)
- US-11535 Little Valley Reservoir State Fishing Lake (water)
- US-11536 Lower Goose Creek Reservoir State Fishing Lake (water)
- US-11537 Lower Salmon Falls Reservoir State Fishing Lake (water)
- US-11538 Moose Creek Reservoir State Fishing Lake (water)
- US-11539 Mosquito Flat Reservoir State Fishing Lake (water)
- US-11540 Ririe Reservoir State Fishing Lake (water)
- US-11541 Sheep Creek Reservoir State Fishing Lake (water)
- US-11543 Treasureton Reservoir State Fishing Lake (water)
- US-11544 Twenty Four Mile Reservoir State Fishing Lake (water)
- US-11545 Upper Pleasant View Reservoir State Fishing Lake (water)
- US-11546 Upper Salmon Falls Reservoir State Fishing Lake (water)
- US-11579 Dworshak Reservoir State Fishing Lake (water)
- US-11948 Hornet Reservoir State Fishing Lake (water)
- US-12112 Little Payette Lake State Fishing Lake (water)
- US-12227 Crane Falls Lake State Fishing Lake (water)
- US-12228 Cove Arm Lake State Fishing Lake (water)
- US-12232 Horseshoe Bend Mill Pond State Fishing Lake (water)
- US-12292 Dick Knox Pond State Fishing Lake (water)
- US-7397 Pottawatomie No 2 State Fishing Lake (compilation)
- US-7412 Black Kettle State Fishing Lake (compilation)
- US-9190 Marais des Cygnes Massacre State Historic Site (register)
- US-8424 Quincy Quarries State Reserve (compilation)
- US-7974 Harmony Hall National Heritage Site (register)
- US-8459 Erle R. Kelley (Dresden Bog) Wildlife Management Area (compilation)
- US-9171 St. John Ponds Ecological Reserve (compilation)
- US-11392 Paw Paw State Game Land (mid)
- US-3329 Tippy Dam State Recreation Area (mid)
- US-6816 Lime Island State Harbor (mid)
- US-6823 William G. Milliken State Harbor (mid)
- US-6824 Harrietta State State Fish Hatchery (mid)
- US-6825 Marquette State State Fish Hatchery (mid)
- US-6827 Platte River State Fish Hatchery (mid)
- US-2549 Percy E Quin State Park (mszp)
- US-9847 Clark Creek Natural Area State Park (mszp)
- US-11215 Bear Paw Battlefield National Monument (compilation)
- US-11216 Big Springs Trout State Fish Hatchery (compilation)
- US-11217 Bluewater Springs Trout State Fish Hatchery (compilation)
- US-11218 Fort Peck State Fish Hatchery (compilation)
- US-11219 Jacko River Trout State Fish Hatchery (compilation)
- US-11221 Washoe Park Trout State Fish Hatchery (compilation)
- US-12630 Upper Missouri River BLM Wild and Scenic River (compilation)
- US-8001 Lamesteer National Wildlife Refuge (compilation)
- US-8002 Ninepipe National Wildlife Refuge (compilation)
- US-8003 Pablo National Wildlife Refuge (compilation)
- US-8532 Chateau De Mores State Historic Site (register)
- US-8536 Fort Buford State Historic Site (register)
- US-8544 Huff Indian Village State Historic Site (register)
- US-8555 Oscar-Zero Missile Alert Facility State Historic Site (register)
- US-8559 Welk Homestead State Historic Site (register)
- US-3492 Willa Cather Memorial Prairie State Historic Site (register)
- US-4918 Kearsarge Mountain State Forest (compilation)
- US-13251 Virginia City Historic District (Comstock Lode) National Historic District (register)
- US-0822 Fort Smith National Historic Site (register)
- US-11778 Fort Sill National Historic Site (register)
- US-6335 Cabin Creek Battlefield State Historic Site (register)
- US-6336 Honey Springs Battlefield State Historic Site (register)
- US-3061 Walter Umphrey State Park (compilation)
- US-4423 Spring Creek Forest State Preserve (compilation)
- US-6599 Sabine Pass Battleground State Historic Site (compilation)
- US-6607 Varner-Hogg Plantation State Historic Site (compilation)
- US-13000 Spiral Jetty NPS National Historic Site (register)
- US-5821 Mountain Meadows Massacre National Historic Site (register)
- US-5926 Fort Douglas National Historical Park (register)
- US-5980 Central Utah Relocation Center (Topaz) National Historical Site (register)
- US-10015 Accotink Bay Wildlife Refuge (compilation)
- US-7804 Great Falls Park (compilation)
- US-9899 Fort Hunt National Historical Site (compilation)
- US-9937 Meadowood BLM Special Recreation Management Area (compilation)
- US-12255 Rock Creek BLM Recreation Management Area (compilation)
- US-12271 Telford BLM Recreation Management Area (compilation)
- US-12317 Rocky Lake State Recreation Site (water)
- US-12399 Spokane State Fish Hatchery (compilation)
- US-12745 Wallace River State Fish Hatchery (compilation)
- US-13348 Puyallup State Fish Hatchery (compilation)
- US-13360 Lake Washington State Fishing Lake (water)
- US-13361 Lake Stevens State Fishing Lake (water)
- US-2441 Scooteney Reservoir State Park (water)
- US-3157 Bayview State Park (compilation)
