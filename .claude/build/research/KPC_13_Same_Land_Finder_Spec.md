# KPC 13: "SAME LAND, TWO PARK NUMBERS" FINDER. A build spec for an outside coder.
Read KPC_HOW_WE_WORK.md first.

## Why
Sometimes POTA gives two numbers to what is really the same land, for example:
- a state park and a state nature preserve on one record;
- a national historic site that IS one unit of a national park;
- a park listed once under its old name and once under its new one.

The club's rule: such pairs are SHOWN with the label **"same land, two park numbers"**, never as an ordinary 2-fer
(and the club never questions whether a POTA park should exist). This tool finds the candidates so a person can label them.

## Tests for each pair of parks whose outlines overlap
(US and Canada from the keys, world from `world-bounds`; only pairs that both have a POTA number)

| test | what it means |
|---|---|
| S1 same record | Both parks point to the same record id(s) on the same layer = SAME RECORD (strong) |
| S2 nearly the same shape | Overlap ÷ smaller area ≥ 0.95 AND overlap ÷ larger area ≥ 0.80 = SAME SHAPE (strong); 0.95 / 0.5-0.8 = ONE INSIDE THE OTHER (normal layering: NOT same land, list it apart) |
| S3 same name family | Names normalised (initials, accents, type words dropped), token-set ratio ≥ 0.85, or one name contains the other = NAME FAMILY |
| S4 pins | Both POTA pins within 200 m = SAME SPOT |
| S5 the agency | Same managing agency (the record's agency / owner field) or different. Different agencies on the same land = layering, i.e. a normal 2-fer (Brandon's Carter Caves ruling: a Tourism cabinet park and an Energy cabinet preserve are different land managers, so the normal overlap test applies, not same land) |

**Verdict:**
- **SAME LAND: likely** = S1, or S2-strong with S3 or S4, and the same agency.
- **CHECK** = S2-strong with a different agency, or S3 + S4 without S2.
- **NOT SAME** = all else.

## Inputs
The keys + bounds + `fers/` (to note when a pair already has a 2-fer row, and which kind); `--areas`, `--resume`, `--max-minutes 50`.

## Outputs
- `sameland/<area>.json`: pairs with the test results, verdict, why (one plain sentence), any existing 2-fer row ids.
- `sameland/questions.json`: SAME LAND likely + CHECK rows as questions for the checker (answer null).
- `sameland/summary.md`.
- **Never** relabels a 2-fer itself.

## Tech
Python 3.11+, shapely ≥ 2 (STRtree for pair finding), pyproj, rapidfuzz, requests (only to read records the keys name).

## Test (TEST_REPORT.md)
1. Kentucky: compare with the club's own Kentucky 2-fer file (`fers/US-KY.json`). Rows of kind "same land" must come out SAME LAND or CHECK.
   Carter Caves State Resort Park vs the preserves inside it must NOT come out same land (different cabinets).
2. Tennessee and Ontario: list the top 10 candidates.
3. Unit tests with made-up shapes for S1-S5.
