# KPC 10: WHOLE-MAP ACCURACY AUDIT. A build spec for an outside coder.
Read KPC_HOW_WE_WORK.md first.

## Why
The club wants a full accuracy check once the US and Canada outlines are complete. This tool grades EVERY saved park outline with simple
tests, so the worst ones go to a person first. **It decides nothing:** it ranks.

## Tests per park outline
(US: the key's records read live; Canada: `canada-bounds` + the key; world: `world-bounds`)

| # | test | flag |
|---|---|---|
| T1 | pin: POTA's pin inside the outline? | Else the distance. 0 = PASS, ≤ 500 m = NEAR, > 500 m = OUTSIDE, > 10 km = FAR |
| T2 | size: outline acres (equal-area projection) vs the official acres | Official acres = the record's own acres field, PAD-US GIS_Acres, or the club's acreage list (`acres-list.json` when given). Within ×1.5 = PASS, ×1.5-5 = OFF, > ×5 = WAY OFF |
| T3 | name: the record's name vs POTA's current name (normalised: case, accents, punctuation, initials joined, type words dropped; token-set ratio gated by the park's own words) | ≥ 0.9 PASS, 0.75-0.9 WEAK, < 0.75 MISMATCH |
| T4 | kind: the record's type field vs the park type | Conflict (WMA vs State Park, a whole lake vs a recreation area on it, a whole canal vs one section, a national forest's proclamation line vs its owned land) = CONFLICT |
| T5 | shape health | Invalid geometry, self-intersection, slivers under 10 m wide, holes smaller than 100 m², more than 50 separate pieces spread over more than 50 km, an empty geometry |
| T6 | spill | The outline covers more than 30% of ANOTHER POTA park's pin area with a different name and no 2-fer row = SPILL (possibly the wrong record) |
| T7 | detail | The saved outline's vertex spacing vs the 3 m rule (US / Canada); over 5 m = TOO COARSE (world: report only) |
| T8 | duplicate | Two parks with the same record id(s): list them for the "same land, two park numbers" finder (KPC 13) |
| T9 | age | The source's last-edit date (layer metadata) older than the club's read date + 1 year = STALE CHECK |

**Score:** 0 = all PASS. Add 3 for OUTSIDE / WAY OFF / MISMATCH / CONFLICT / SPILL, 5 for FAR, and 1 for each softer flag.

## Inputs
`--areas US-KY US-TN … CA-ON … CH …`, the keys + bounds folders, `--acres acres-list.json` (optional), `--resume`, `--max-minutes 50`.

## Outputs
- `audit/<area>.json`: one record per park, with the test results + `score` + `why` (one plain sentence naming the worst flag).
- `audit/worst.csv`: all areas, sorted by score, top first. This is the checker's work list.
- `audit/summary.md`: per area, how many parks pass / have flags, and the 10 worst.
- `audit/questions.json`: the top 50 per area as questions for the checker (answer null, same shape as the club's question files), with the record link and the POTA link.
  Leave a `picture` field empty for KPC 9 to fill.

## Must not
- Never change a key or an outline.
- Never use OSM / Google / WDPA.
- POTA pins are never moved.

## Tech
Python 3.11+, requests, shapely ≥ 2, pyproj, rapidfuzz.

## Test (TEST_REPORT.md)
1. Kentucky (all parks in `ky-answer-key.json`).
2. Tennessee (`us-key/US-TN.json`): show the 10 worst with their `why`.
3. Ontario (`ca-key/CA-ON.json`).
4. Switzerland (`world-bounds/CH`).

Unit tests with made-up shapes for T1-T8.
