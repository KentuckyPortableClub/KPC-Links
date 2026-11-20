# 2-fer owner answers, part 2

## What is NOT built

- Part 3 is not in this pull request. The bot does not yet write `not-sure-rows-<tag>.json` on this branch.
- Part 4 is not built. No finer-grid code.
- No real area was run. No park was remeasured. There is no park-by-park change list. `US-MATH-GUARD` is not a park.
- The measuring step `merge()` was not changed. Its 0.0005 degree join is the owner's question G1, recorded on part 1.

## Second round (review of 19 Nov, sections 2.1 to 2.3)

Restack base is part 1 at `8fb1b48a66a8`. The first-round guard, restacked, was `b158bbb4bd3d` (before the restack the line was `a18d26726099` -> `180dcd51a7b0`). This round moves the 2-fer rules hash `b158bbb4bd3d` -> `1cc599edb3dc`. US, Canada and world did not move (`c64b8ace0411`, `dfef94b3dfd3`, `b1f23bf0deea`).

The guard now fingerprints ten more functions. The scope entry the fixture names carries the same fingerprint. Refreshing the fixture alone does not pass. A fingerprint other than the first-round one has to name a different scope entry.

Scope entry `2026-11-19-math-guard-calls`, scope `{"parks": ["US-MATH-GUARD"]}`, fingerprint `5ebe37a361c8f10835ad5e12e6cb4373a570cb309a0b6adcc6a770e1a8d50f4a`. The baseline entry `2026-11-19-math-guard-baseline` keeps the first-round fingerprint `0162b452da97751fcfad7650ae9c4dcf3ea1f30f7676cfc50ba458ff41f738a1`.

The gate on Python 3.12 and 3.13, and the byte-test look, are run on the top of the stack (part 3) and the result is in that pull request's notes. This branch was not gated on its own.

## What is built

The dead lines are gone: `FERS_ALGO`, `REUSE_KEY`, `KPC_FERS_REUSE_KEY`, and `CODE_HASH`, which only existed to feed them. Nothing read them.

The math guard fingerprints 21 functions, listed in the fixture, and the constants `SHRINK`, `SMALL_M`, `TIGHT_M`, `TIGHT_SHRINK`, `STRETCH`, `ZONE`, `STATION_IN`, `ROUTE_KM` and `BANK`. Those constants are not inside `pair_fp` (`CELL`, `DET`, `PREC`, `REGION` and `PASS` are).

`data/status/test_fers_final_redact_nov17.json` is deleted. That test now changes to its temp folder before it saves, so `kpc_save` writes `data/status/<test>.json` there and not in the repo.

## The 52 functions reachable from find_spots

Reached by name from `find_spots`, then from each of those, in `kpc_fers.py`. 21 are in the guard. The other 31 are left out. One word on each.

In the guard, because they move or size a spot: `find_spots`, `area_spots`, `water_route_spots`, `line_spots`, `pmask`, `Frame`, `inter`, `tiles`, `dt`, `bbox_groups`, `bbox_lines`, `merge`, `Win`, `sample`, `line_m`, `close_m`, `water_route`, `nhd_water`.

In the guard, because they can keep yesterday's spots: `pair_fp`, `rule_stamp`, `answers_unchanged`.

Left out:

1. `Progress` prints the progress line.
2. `HardStop` is the pass's hard end. It stops the run.
3. `ParkTimeout` is one pair running out of its own time.
4. `_ring` is the alarm that raises those two.
5. `_arm` sets that alarm.
6. `_beat` prints a heartbeat so a long stage is not silent.
7. `budget_end` is the moment the pass is out of time.
8. `late` asks whether that moment has passed.
9. `park_clock` is the per-pair limit. A pair it cuts is skipped, not resized.
10. `stage_start` marks the start of a stage in the log.
11. `peak_mb` reads the process's peak memory.
12. `rss_mb` reads the process's memory now.
13. `_say` prints one log line.
14. `_h` is the hasher `pair_fp` calls. A change here changes every fingerprint, so pairs are measured again. `pair_fp` itself is in the guard.
15. `reuse_load` reads the saved pair answers.
16. `reuse_save` writes them. Whether a saved answer is kept is `pair_fp` and `answers_unchanged`.
17. `get` fetches a map, with retries.
18. `_get` fetches one map reply.
19. `evict` drops cached tiles outside the current box.
20. `esri_rings` turns an outline into rings.
21. `_wpath` is the path of one water tile.
22. `_wload` reads a saved water tile.
23. `_wsave` writes one.
24. `_wlive` reads a water tile from the live map when the saved copy is not there.
25. `sbox` reads the box already on a spot, or the box of its shape through `bbox_lines`.
26. `key_of` is the pair's id string.
27. `_shown` asks whether a row is one we show.
28. `denial` asks whether a status is a denial row.
29. `this_runs_verdict` asks whether the row is this run's own verdict.
30. `no_denials` takes denial rows out before a file is written.
31. `save_json` writes a 2-fer file.

## Guesses

1. "Reachable" is a name used from `find_spots`, then from each function reached that way. A function only mentioned inside a nested `def` that is not itself a module function is not in the 52. `box_of` and `cell_of` are nested inside `find_spots`, so their source is inside `find_spots`, which is in the guard.
2. `US-MATH-GUARD` matches no real park, so `rule_stamp` does not add either guard id to a real pair.

## Grey areas

1. `esri_rings`, `get`, `_get`, and the water-tile helpers `_wpath`, `_wload`, `_wsave` and `_wlive` can change the outline or the water a spot is measured from. The review named ten functions to add. These seven are not those ten, so they are not in the guard. A change to one of them does not move the fingerprint.
2. `no_denials` can take a row out of the file after it is measured. It does not move or size the spot. It is not in the guard.
3. The test freezes the baseline entry's fingerprint. It does not freeze the calls entry's fingerprint. A later math change that only edits that entry's fingerprint, and the fixture, passes. That edit is in the scope file, which is the review's copy of the change. A further new entry is the cleaner record. I did not add a rule that forbids editing the calls entry.
