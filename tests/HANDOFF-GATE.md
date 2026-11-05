# Handoff gate (Nov 6 2026)

Before any bundle is handed to Quality, run the full suite on the final stack **and** on main:

    LINKS=<KPC-Links checkout> DATA=<KPC-Data checkout> python3 .github/scripts/kpc_full_suite.py --report tests.txt

It runs every `tests/test_*.py` one by one, plus every `.github/scripts/*.py --selftest`. It then compares the results with `tests/known-fail-main.txt`.
- **GATE PASS** (exit 0) means every failure is already a failure of main.
- **GATE FAIL** (exit 1) means there's a new failure, or a test or selftest that changed the repo's files.

pytest isn't the suite: these files are scripts, and pytest can't collect them. The gate starts nothing, pushes nothing and doesn't use the network.
