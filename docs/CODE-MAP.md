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

## Auto-confirm, held name and pin (24 Nov 2026, 7:06 AM CT)

- `.github/scripts/kpc_match_checks.py`: in `pass_state`, a joined park that would stay `outlined` is status-confirmed (`by: held name and pin`) when the held record's own name matches the park and the pin sits inside that record or within 100 m, measured on the saved outline (`km_to_record`), not the key's `bk` working copy. Land (`m`) is never changed. Stops: person-NO, a blocked id, and an IDs-only stop list (calls, land-wrong, pin-wrong). The spelling table is read from `data/names/spelling-table.json` (KPC-Data, agreed with the page-names work) or `.github/name-spelling-table.json`; if neither file is there yet, the shared letters-and-digits name key is used alone.
- `tests/test_auto_confirm_nov24.py`: invented parks only; fails if the key's `bk` distance is used, if land is changed, or if a stop is skipped.
- Hashes (measured, then declared): US `3aabd63147fd` -> `02f61d4a9470`; CA `3a1d4bf2e112` -> `c0436e6a9ab2` (shared helper only). World and 2-fers do not move. Scope none.
