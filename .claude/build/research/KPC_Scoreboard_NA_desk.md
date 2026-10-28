# Scoreboard: US + Canada parks, with an outline or without (desk, Oct 27 2026 night)
Read only. Source: our own answer-key files `data/us-key/US-XX.json` and `data/ca-key/CA-XX.json` in this clone (state of Oct 27; KPC-Data may hold newer copies, recount before relying on a single row). Every row is in `KPC_Scoreboard_NA.csv` (region, state/province, park type, total, with outline, without, pin-only, line, likely name mismatch, no layer found). US-DC (34 parks) and the two Canadian island keys (Sable, St Paul, matched) are left out of the region totals.

## How I sorted the 'without outline' parks
- **Pin-only** (not a gap): historic sites and monuments, heritage sites, city/county/regional/recreation parks, scenic byways, hatcheries, airstrips, interpretive sites, memorials, and BLM recreation 'areas' whose name reads like a single site (boat ramp, trailhead, kiosk, spring…).
- **Line types** (not a gap, different rule): trails, rivers, canals, wild & scenic rivers.
- **Likely name mismatch**: the matcher itself holds a 'check by hand' near-miss for the park (a layer we read has a similar name or the pin falls inside a differently-named polygon). This is a LOWER bound: only 117 are flagged; my desk reading says more are mismatches (WA 13 state forests, ON conservation authorities, QC accented names and mojibake like 'AmÃ©ricains', AL De Soto SP).
- **No layer found**: no near-miss at all.

## Totals
**18,935 parks; 15,295 with an outline; 3,640 without.** Of the 3,640: pin-only 1,787, line types 369, likely name mismatch 117, no layer found 1,367. So the real gap to close is about **1,484 parks** (not 3,640).

| Region | Parks | With outline | Without | Pin-only | Line | Name mismatch | No layer |
|---|---|---|---|---|---|---|---|
| SE | 2,060 | 1,820 | 240 | 39 | 48 | 18 | 135 |
| MW | 2,771 | 2,524 | 247 | 45 | 67 | 20 | 115 |
| NE | 2,854 | 2,698 | 156 | 16 | 52 | 7 | 81 |
| SC2 | 1,195 | 1,003 | 192 | 74 | 43 | 4 | 71 |
| MTN | 2,493 | 1,656 | 837 | 412 | 71 | 16 | 338 |
| PAC | 1,667 | 1,426 | 241 | 46 | 56 | 23 | 116 |
| CAE | 3,235 | 2,055 | 1,180 | 830 | 9 | 24 | 317 |
| CAW | 2,660 | 2,113 | 547 | 325 | 23 | 5 | 194 |

## The 20 biggest state/province × type gaps (name mismatch + no layer)
| # | Place | Park type | Total | Without | Gap | Mismatch | No layer | What it is |
|---|---|---|---|---|---|---|---|---|
| 1 | UT (US) | BLM Recreation Management Area | 257 | 216 | 150 | 1 | 149 | BLM sites + areas; polygon layers read, so mostly sites/names (Round 3) |
| 2 | ON (CA) | Conservation Area | 264 | 81 | 81 | 9 | 72 | conservation authority lands: per-authority layers unread |
| 3 | SK (CA) | Recreation Site | 165 | 44 | 44 | 0 | 44 | Saskatchewan rec sites (Crown land): CAW-5 ruling |
| 4 | QC (CA) | Nature Reserve | 291 | 43 | 43 | 0 | 43 | mixed: private réserves naturelles (ruled), urban "reserves", accents |
| 5 | NS (CA) | Provincial Park | 157 | 38 | 38 | 1 | 37 | NS provincial parks polygons not in the PAS file |
| 6 | NT (CA) | Territorial Park | 37 | 37 | 37 | 0 | 37 | FOUND: GNWT Environment_LCC layer 195 (Round 2) |
| 7 | YT (CA) | Recreation Site | 33 | 31 | 31 | 0 | 31 | YT recreation sites: points |
| 8 | ID (US) | State Recreation Area | 32 | 31 | 31 | 0 | 31 | IDPR state parks hub (Round 2) |
| 9 | WY (US) | BLM Recreation Management Area | 56 | 40 | 27 | 2 | 25 |  |
| 10 | MS (US) | State Recreation Area | 24 | 22 | 22 | 0 | 22 | MARIS layers (Round 1) |
| 11 | MS (US) | Wildlife Management Area | 54 | 20 | 20 | 0 | 20 | MARIS WMA layer (Round 1) |
| 12 | FL (US) | State Conservation Area | 157 | 17 | 17 | 6 | 11 |  |
| 13 | WA (US) | State Recreation Site | 19 | 16 | 16 | 12 | 4 | WA DNR rec sites; 12 are near-misses |
| 14 | NB (CA) | Nature Reserve | 67 | 15 | 15 | 0 | 15 |  |
| 15 | ON (CA) | Conservation Reserve | 331 | 15 | 15 | 2 | 13 |  |
| 16 | MS (US) | State Fishing Lake | 16 | 15 | 15 | 0 | 15 | MARIS facilities |
| 17 | PE (CA) | Provincial Park | 24 | 14 | 14 | 0 | 14 | no open layer (Round 2) |
| 18 | ID (US) | BLM Recreation Management Area | 83 | 72 | 14 | 1 | 13 |  |
| 19 | OR (US) | BLM Recreation Management Area | 77 | 15 | 14 | 2 | 12 |  |
| 20 | VT (US) | State Park | 61 | 14 | 14 | 0 | 14 | ANR state parks layer not in key (easy add) |

## The ten places with the most true gaps
UT 194, ON 145, QC 67, ID 65, MS 63, NB 57, WA 56, SK 50, NS 48, NT 43 (then YT 40, WY 38, MI 36, OR 31). Utah is mostly BLM sites; Ontario is conservation authorities; Idaho, Mississippi, Washington, NS, NT, PE are missing layers I have leads for (KPC_BigHoles_desk.md).

## Caveats
The classification is by POTA park type and name, not by looking at each park. The pin-only rule on BLM 'recreation areas' is a name test (rough). Counts of 'with outline' include approximate matches (PAD-US / fuzzy), so 'with' is not the same as 'official line'. Recount once chat 2 refreshes the key.