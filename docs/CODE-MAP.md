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

## Clean-up stage, report-only (D, 24 Nov 2026)

- `.github/scripts/kpc_cleanup_report.py`: after a key join, collapse check rows to one row per park per reason (with a count and the record IDs), and pre-sort parks into sure / needs a person / pin wrong / land wrong / needs a layer. Solver verdicts may be attached as a last check. The key's `c` rows are not rewritten. Listed in `NOT_RULES` (no rules hash moves).
- `tests/test_cleanup_report_nov24.py`: invented parks only; fails if copies are not folded, if a second state's own piece is dropped, if an unknown bucket is hidden, or if `c` rows are rewritten.
- The matching settled-answers file (one KPC-Data file, IDs first; fingerprint is a stable agency ID, else name + acres within 10% + box to 0.001°; record number is a hint only; S4 lists a missing saved record and does not redo or drop it) lives in KPC-Data (`kpc_settled_answers.py`, `docs/settled-answers.md`, `tests/test_settled_answers_nov24.py`). Auto-apply is not part of this step.
