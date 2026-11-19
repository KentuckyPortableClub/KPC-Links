# 2-fer owner answers, part 2

## What is NOT built

- Part 3 is not built. The bot does not yet write `not-sure-rows-<tag>.json`.
- Part 4 stays a proposal in the part 1 notes. No finer-grid code.
- The full hand-off gate was not finished on this machine. Python is 3.12.3. Python 3.13 is not installed here, so the gate was not run on 3.13.
- No 2-fer test was changed from a byte compare to a parsed-JSON compare. The byte compares I found are ones where the bytes are the point: an unchanged neighbour file, a golden hash of a finished run, hash inputs, and the rules check. `tests/test_fers_area_boxes_time_nov11.py` still compares that golden hash. It was not re-run here.
- The Kentucky path was not folded in. No real area was run.

## Baseline

Part 1 left the 2-fer rules hash at `a18d26726099`. This part moves it to `180dcd51a7b0`.

The fers tests run for this part ended ALL PASS: `tests/test_fers_math_guard_nov19.py`, `tests/test_fers_final_redact_nov17.py`, `tests/test_fers_incremental_nov9eve.py`.

## What is built

The dead lines are gone: `FERS_ALGO`, `REUSE_KEY`, `KPC_FERS_REUSE_KEY`, and `CODE_HASH`, which only existed to feed them. Nothing read them. `pair_fp` is unchanged.

The math guard fingerprints the source of `find_spots`, `area_spots`, `water_route_spots`, `line_spots`, `pmask`, `Frame`, `inter`, `tiles`, `dt`, `bbox_groups` and `bbox_lines`, and the constants `SHRINK`, `SMALL_M`, `TIGHT_M`, `TIGHT_SHRINK`, `STRETCH`, `ZONE`, `STATION_IN`, `ROUTE_KM` and `BANK`. Those constants are not inside `pair_fp` (`CELL`, `DET`, `PREC`, `REGION` and `PASS` are). The fingerprint and the scope id sit in `tests/fixtures/fers-math-guard.json`. A different fingerprint fails. A fixture that names a scope entry of `none` fails. The rules-check workflow runs this test.

The baseline scope entry is `2026-11-19-math-guard-baseline`. Its scope is the park `US-MATH-GUARD`, which is not a park, so no real pair is retested. A later math change updates the fixture and points it at a scope entry that is not `none`.

`data/status/test_fers_final_redact_nov17.json` is deleted. That test now changes to its temp folder before it saves, so `kpc_save` writes `data/status/<test>.json` there and not in the repo. After that test, `git status` does not show the file.

## Guesses

1. The function list is the call path from `find_spots` that places or sizes a spot, plus `Frame` and the distance transform. A helper that only logs is not in the list. The reviewer can check the list against the call path.
2. `US-MATH-GUARD` matches no real park, so `rule_stamp` does not add the baseline id to a real pair.

## Grey areas

1. I could not run the gate on Python 3.13. I did not change a byte compare on a guess that 3.12 and 3.13 would disagree.
