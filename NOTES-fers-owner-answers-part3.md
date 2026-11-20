# 2-fer owner answers, part 3

## What is NOT built

- The bot does not settle a row, does not read the not-sure list back, and does not hold a pair because a park is on it. Whether a park on that list should be NOT SURE for 2-fers is the owner's question, not this hand-off.
- Tripwire parks are not written here. The tripwire bot owns those rows.
- Part 4 is not built. The review (19 Nov, section 5) says yes to a second look later, on its terms. No finer-grid code.
- No real area was run. No key or outline was changed. There is no park-by-park change list.

## Second round (review of 19 Nov, sections 3.1 to 3.3)

Restack base is part 2 at `1cc599edb3dc`. The first-round not-sure file, restacked, was `b9881640b28f` (before the restack the line was `180dcd51a7b0` -> `9cee86692de2`). This round moves the 2-fer rules hash `b9881640b28f` -> `76c2faa3e59f`. US, Canada and world did not move (`c64b8ace0411`, `dfef94b3dfd3`, `b1f23bf0deea`).

Scope entry `2026-11-19-not-sure-rows-own`, scope `none`.

1. The file is written through `save_json`, the same guarded write as every other 2-fer file. It is a document `{"about", "rows"}`, not a bare list, so the write guard sees the rows. A store run with a withheld park was written and then read: that park is not in the file.
2. Both halves use this run's own areas. A neighbour loaded for a border pair is not in the file. A run with no `STATES` uses the region's own area names (US and Canada, not Kentucky, for a North America run).
3. An unreadable tripwire list is counted. The report key is `tripwire list could not be read`. A missing list is the old warning, not this count. `tests/test_fers_area_boxes_time_nov11.py` leaves `not-sure-rows-` out of its golden hash, the same way it leaves `receipt-` out, because that file is not one of main's files. That fixture also links `data/state-gis.json` and `data/us-key/layers.json`, so the loud missing-file error is not raised in a fixture that is not a broken checkout.

The gate on Python 3.12.3 (numpy 2.5.3, OpenCV 5.0.0) finished. Last line:

`TOTAL tests: 301/329 pass; with selftests: 311/339 pass; skipped: 2; NEW failures: 25; stale baseline entries: 0 -> GATE FAIL`

Every 2-fer test in this stack passed, including `test_fers_owner_answers_nov19.py`, `test_fers_math_guard_nov19.py`, `test_fers_not_sure_nov19.py`, `test_fers_area_boxes_time_nov11.py`, `test_fers_one_program_nov16.py`, `test_fers_store_nov13.py` and `test_fers_store_switch_nov15.py`. The 25 new failures compare this branch with `origin/main` (`34f6605`), which is 9 commits ahead of the stack's base `7b36ae5` (the no-building rule and the outline sync). Those commits are not in this stack. Two tests skipped because DATA is not set: `test_map_store_hook_nov15.py`, `test_outlines_match_key_nov13.py`.

The newest fers changelog arrow is `082e787b3f86 -> 76c2faa3e59f`. `082e787b3f86` is what this branch's rule list computes for `origin/main` (the new rule files are not on main, so they count as missing). The stack's own steps are the lines under it. Python 3.13 is recorded below when that run finishes.

## What is built

At the end of a run the bot writes `not-sure-rows-<tag>.json` next to the report, through `save_json`. The rows are the shared list's shape: `ref`, `area`, `name`, `code`, `how_sure`, `shows_now`, `why`, `wants`, `found_by` (`2-fer bot`), `evidence`. They are sorted by park number, then code.

Its own doubts only:

| Code | Plain line | Wants |
|---|---|---|
| `SUMMARY_MAP_ONLY` | Every joined record is a summary map, not the agency's own land. | official layer |
| `NEAR_SIZE_LINE` | An overlap is within one grid cell of a size line, so the grid cannot tell which side it is on. | map, a person |

`how_sure` is `unsure`. The bot does not say a row is wrong.

A withheld park is left out before the write, and the document then goes through the write guard. A tripwire park is left out.

The code names above are a proposal for the list's README. They are not free text.

## Guesses

1. "Park number" is the digits at the end of the ref, so US-2 sorts before US-10.
2. A run with no such doubt still writes the file, with an empty `rows` list, so the name is always there. The store-switch byte compare ignores `not-sure-rows-*`, the same way it ignores the receipt.
3. Evidence is one quote, the status line or the fixed sentence, and `where` is the area file or "the key join". There is no page address in a 2-fer row.

## Grey areas

1. A near-line row's status does not name the other park in the tests that passed. If a status names a withheld park, that row is left out rather than written. The file that was read did not contain the withheld park.
2. `how_sure` is `unsure`. The shared list's word list is not in this repository (`kpc_not_sure.py` was not here to check). The review could not check it either. The word is unchanged.
3. A tripwire list that is missing is not the same as one that will not parse. Only a file that is there and cannot be read is counted.
