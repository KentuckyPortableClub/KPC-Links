# Official pins fixture (Nov 12, 2026)

`official-pins-nov12.json` is a byte-for-byte copy of KPC-Data `data/intake/official-pins-nov12.json` (KPC-Data #76, read at KPC-Data
main 12112ef). The key workflows read the live copy from KPC-Data (read only); this copy is only for the offline tests of
`.github/scripts/kpc_pin_fill.py` (tests/test_pin_fills_nov12.py). When a KPC-Data checkout is next to this repo (env KPC_DATA or DATA),
the test checks that this copy still matches it.

The other test data (parks, outlines) is SYNTHETIC: real park refs and names, made-up rectangles near the official pins.
