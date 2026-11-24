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

## County safety belt (E, 24 Nov 2026)

- `.github/scripts/kpc_match_checks.py`: in `pass_state`, the county check (`outside_counties`) no longer sends a name-joined record to the check list when `holds_fn` says POTA's pin is inside that land. `COUNTY_FAR_KM` (25) and `COUNTY_FAR_X` (2) are unchanged.
- `tests/test_county_safety_belt_nov24.py`: invented parks only; fails if the belt is skipped or the distance test is loosened. `tests/test_county_check_nov23.py` still covers the original county cases.
- `.github/us-key-rule-scope.json`, `.github/ca-key-rule-scope.json`, `docs/key-rules-change.txt`: approved old/new rules hashes (US `3aabd63147fd` -> `d525bb370fec`, CA `3a1d4bf2e112` -> `5826be395087`; world does not move). The Canada hash moves only because the shared helper is a Canada rule file.
- The matching page-reader fix (a search or list URL is not a park's own page; no county tag unless the page names the park) lives in KPC-Data (`kpc_park_pages.py`, `kpc_park_pages_rules.py`, `tests/test_search_list_not_own_page_nov24.py`).
## Solver final-pass, pile report only (24 Nov 2026)

- `.github/scripts/kpc_solver_final_pass.py`: recommendations only. Nothing is written to the key or to `c` rows. Listed in `NOT_RULES`, so the rules hashes do not move. Every distance is to the **held** record on the **saved** outline (`kpc_problem_solver.km`), not a nearby same-name candidate and not the key's `bk` working copy. "Pin at the land" is inside or within 100 m, and the held name must fit, before a KEEP. A record that is another POTA park's land is never recommended. Kind-of-land guard: state park / state forest / WMA, and Wilderness / Wilderness Study Area, do not KEEP a mismatch. A unit, tract, access, or campground must not take the whole park (or the other way around) — that is NEEDS LAYER. Trail parks drop the `trl` copy when the official trail holds the pin. Partial joins are labelled "partial, more pieces needed". Unresolved parks go on an IDs-only page-reader re-read list.
- `tests/test_solver_final_pass_nov24.py`: invented parks only; fails without the KEEP rule, and checks that hashes stay at the current main values.
## Clean-up stage, report-only (D, 24 Nov 2026)

- `.github/scripts/kpc_cleanup_report.py`: after a key join, collapse check rows to one row per park per reason class (numbers and units stripped; a count and the record IDs kept), and pre-sort parks into sure / needs a person / pin wrong / land wrong / needs a layer. Solver verdicts may be attached as a last check. The key's `c` rows are not rewritten. Listed in `NOT_RULES` (no rules hash moves). Command: `python3 .github/scripts/kpc_cleanup_report.py --keys data/us-key --out <report.json>`.
- `tools/pc-keys/kpc_test_keys.py`: REPORT.txt includes the before and after check-row counts from that collapse (for example 16,853 → 2,309 on the 23 Nov 22:15 keys; 491 exact reasons → 70 classes).
- `tests/test_cleanup_report_nov24.py`: invented parks only; fails if copies are not folded, if two size reasons with different numbers stay two rows, if a second state's own piece is dropped, if an unknown bucket is hidden, or if `c` rows are rewritten.
- The matching settled-answers file (one KPC-Data file, IDs first; fingerprint is a stable agency ID, else name + acres within 10% + box to 0.001°; record number is a hint only; S4 lists a missing saved record and does not redo or drop it) lives in KPC-Data (`kpc_settled_answers.py`, `docs/settled-answers.md`, `tests/test_settled_answers_nov24.py`). Auto-apply is not part of this step.
## Auto-confirm, held name and pin (24 Nov 2026, 7:06 AM CT)

- `.github/scripts/kpc_match_checks.py`: in `pass_state`, a joined park that would stay `outlined` is status-confirmed (`by: held name and pin`) when the held record's own name matches the park and the pin sits inside that record or within 100 m, measured on the saved outline (`km_to_record`), not the key's `bk` working copy. Land (`m`) is never changed. Stops: person-NO, a blocked id, and an IDs-only stop list (calls, land-wrong, pin-wrong). The spelling table is read from `data/names/spelling-table.json` (KPC-Data, agreed with the page-names work) or `.github/name-spelling-table.json`; if neither file is there yet, the shared letters-and-digits name key is used alone.
- `tests/test_auto_confirm_nov24.py`: invented parks only; fails if the key's `bk` distance is used, if land is changed, or if a stop is skipped.
- Hashes (measured, then declared): US `3aabd63147fd` -> `02f61d4a9470`; CA `3a1d4bf2e112` -> `c0436e6a9ab2` (shared helper only). World and 2-fers do not move. Scope none.
