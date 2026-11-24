# Code map

This file was absent from main at `06ab25a7`; the W8b change starts the map here.

## US place checks (W8b)

- `.github/scripts/kpc_match_checks.py`: `pin_3c` decides whether a name-linked row belongs on the place check list. `same_name_piece` and `two_unit_half` are the new name predicates; owner and shape evidence come from `pass_state`. `rings_near` measures the saved rough shapes. The older `own_piece` helper remains unchanged for W10 saved-answer parcel matching.
- `.github/scripts/kpc_us_key.py`: the builder supplies the near-land callback using its `_g` rings. Do not import this module to inspect it: importing starts the builder.
- `.github/scripts/kpc_match_checks_count.py`: the offline counter supplies the same callback using saved `_r` rings.
- `.github/us-key-rule-scope.json`: approved US rule scope, no build requested.
- `tests/test_safe_own_pieces_nov23.py`: invented-name W8b regression and integration tests. `tests/test_own_pieces_no_acres_nov23.py`: prior W8/W9 coverage, with the tract keep now supplying owner and distance evidence.
- `.claude/notes/mapping.md`: W8b rule sheet. `docs/key-rules-change.txt`: approved old/new rules hashes.

W8b changes no live data, Canada proofs or wetland-district rules. A separate-unit exception requires the complementary name in a pin-holding record; no park ID is hardcoded.

## Solver final-pass, pile report only (24 Nov 2026)

- `.github/scripts/kpc_solver_final_pass.py`: recommendations only. Nothing is written to the key or to `c` rows. Listed in `NOT_RULES`, so the rules hashes do not move. Every distance is to the **held** record on the **saved** outline (`kpc_problem_solver.km`), not a nearby same-name candidate and not the key's `bk` working copy. "Pin at the land" is inside or within 100 m, and the held name must fit, before a KEEP. A record that is another POTA park's land is never recommended. Kind-of-land guard: state park / state forest / WMA, and Wilderness / Wilderness Study Area, do not KEEP a mismatch. A unit, tract, access, or campground must not take the whole park (or the other way around) — that is NEEDS LAYER. Trail parks drop the `trl` copy when the official trail holds the pin. Partial joins are labelled "partial, more pieces needed". Unresolved parks go on an IDs-only page-reader re-read list.
- `tests/test_solver_final_pass_nov24.py`: invented parks only; fails without the KEEP rule, and checks that hashes stay at the current main values.
## Clean-up stage, report-only (D, 24 Nov 2026)

- `.github/scripts/kpc_cleanup_report.py`: after a key join, collapse check rows to one row per park per reason class (numbers and units stripped; a count and the record IDs kept), and pre-sort parks into sure / needs a person / pin wrong / land wrong / needs a layer. Solver verdicts may be attached as a last check. The key's `c` rows are not rewritten. Listed in `NOT_RULES` (no rules hash moves). Command: `python3 .github/scripts/kpc_cleanup_report.py --keys data/us-key --out <report.json>`.
- `tools/pc-keys/kpc_test_keys.py`: REPORT.txt includes the before and after check-row counts from that collapse (for example 16,853 → 2,309 on the 23 Nov 22:15 keys; 491 exact reasons → 70 classes).
- `tests/test_cleanup_report_nov24.py`: invented parks only; fails if copies are not folded, if two size reasons with different numbers stay two rows, if a second state's own piece is dropped, if an unknown bucket is hidden, or if `c` rows are rewritten.
- The matching settled-answers file (one KPC-Data file, IDs first; fingerprint is a stable agency ID, else name + acres within 10% + box to 0.001°; record number is a hint only; S4 lists a missing saved record and does not redo or drop it) lives in KPC-Data (`kpc_settled_answers.py`, `docs/settled-answers.md`, `tests/test_settled_answers_nov24.py`). Auto-apply is not part of this step.
