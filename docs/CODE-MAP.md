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
