# Breaking the Waiting Room (RULE SHEET F + kpc_waiting_room.py) — chat 8, Oct 29 ~2:00 PM
HQ order (Brandon 6:52 AM: "10 fix issues then 8 test"). I read all 688 lines and RAN the checker in a sandbox (DATA=/tmp/wr, read-only links to the real data, report mode, nothing promoted, nothing pushed to KPC-Data). Results are grade A: I ran each case. Baseline first: the unchanged live Ohio 2-fer file PASSES (good).

## A. Bad files that PASS (the checker is fooled)
| # | Attack | Result | Why |
|---|---|---|---|
| 1 | **2-fer file with every candidate pair WRONG but the same count** (candidate refs rotated among rows, new ids): OH (25), IN (51), MI (82) | **PASS x3** | F-2 compares only the NUMBER of candidates (±30%), never WHICH pairs. Known answers exist for Kentucky only (`known/fers.json` = US-KY, 20 keys). Every other state is unprotected. |
| 2 | **Outline key with every outline swapped to another park** (OH `m` lists shuffled; same count) | **PASS** | F-O1 counts outlines; it never asks "is this outline near this park's pin?" This is exactly the NS label-collision and NY same-name bug, and they would PASS. |
| 3 | **2-fer file with 20% fake 'area' rows** between far-apart parks (IL) | **PASS** | Only `same land` rows get the 30 km pin test. 'area' rows, 'trail' rows, 'river' rows are never distance-checked; +20% sits under the 30% limit. |
| 4 | **A state with under 10 candidates wiped** (NM: 2 candidates, spots = []) | **PASS** | The shrink check starts at 10 live rows (`len(oc) >= 10`). Small states can lose everything. Also NOT SURE needs 5+. |
| 5 | **A .gz twin of a live .json** (WI: live `US-WI.json`, new `US-WI.json.gz` with 60 of 329 rows) | **PASS** (with 5 rows it HELD only because 5 < 329/50) | The checker looks for the live file under the SAME name, finds none, and treats it as a "first file": no comparison. Promotion then writes a .gz beside the live .json: two copies, the page reads one of them. Same hole for a .json replacing a live .gz (MN, ID, WY are gzipped). |
| 6 | **Status 'PART READY FOR CHAT 8' / 'READY FOR CHAT 8'** with 40 "water not checked" rows | **PASS** | F-S1 only fires on the exact word `READY`. The real status strings are "READY FOR CHAT 8" and "PART READY FOR CHAT 8", so F-S1 never fires on a real file. (Plain 'READY' is held.) |
| 7 | A bot that writes truthy `pass1 / pass2 / pass3` fields | would PASS | The check trusts the bot's own fields, which Rule F-6(a) says it must not. A one-line check that the passes' CONTENT exists (rows per pass) is independent. |

## B. Good files that HOLD (false alarms)
| # | Case | Result |
|---|---|---|
| 1 | **A legit Kentucky closures file** with "closed to protect the Indiana bat", "Washington County", "the Virginia state line", "West Virginia hunters" | **4 of 5 rows removed as 'another state' → over a third → the WHOLE file HELD** (old one stays 'as of'). The state-name filter matches state names inside bat names, county names, border mentions. KY has a Washington County and a hundred 'Indiana bat' cave closures. (Same file under TN also removes 'Washington County'.) |
| 2 | **Every Canadian 2-fer file** (`data/fers/CA-NS.json`, all CA-XX) and every `line-*.json`, `missing-*.json`, `same-outline-*.json`, `expected-*.json`, `looked-*.json` | **HOLD forever: "no check written"** (ROUTES only knows `data/fers/US-XX.json`). Fail-closed is right, but it means (a) these files are not protected, they are blocked, and (b) the NS wrong-join case could not be caught because Canada has no check. |
| 3 | A big LEGIT change (after the NS label fix CA-NS drops 160 'same land' rows; after R-SF many US rows) | HOLD by design (over 30%): correct, but expect a wave of holds after every rule fix. Needs a 'rule change' stamp so a person releases once, not 24 times. |

## C. Other findings (read from the code, grade B)
1. **UNDO keeps ONE generation.** I tested it: live A → B passes → C passes → `undo` gives B, A is gone. If B is the bad one that slipped through, undo puts the bad one back. Keep the last 3 generations (dated names).
2. **The "please look" line is deduped by date**, so one stuck held file makes a new line every day (the F-5 promise is ONE line).
3. `release` does no check at all (by design) and takes any path under `in/`: fine, but it should refuse paths with `..` and log who/when.
4. A held file stays in `in/` and is re-judged nightly with the same result; fine, but the checker never says "still held 5 days": add the age to the line.
5. **First-file check is thin everywhere:** with no live copy, `c_key` skips all comparisons (a brand-new junk key passes unless a known name is missing).
6. Closures rule list: a closure for the wrong park of the right state passes (no ref-to-park check).

## D. The fixes, in order of value
1. **F-2 by pair, not count (attack 1):** require ≥ 80% of the live candidate PAIRS to still be candidates (Jaccard on `spot_key`), unless the file carries a 'rule change' stamp from a person. Also fill `known/fers.json` for every state by freezing today's 3-5 best-known pairs per state (Brandon activates: Mammoth Cave × Green River, Hiawassee...). 
2. **Pin-near-outline test for keys (attack 2):** for ≥ 5% of outlined parks sampled, the park's POTA pin must be inside the outline or within 5 km (or the park type is a line/multi). Hold when more than 3% fail. This one check catches the NS collision, the NY multipart, and the Bluestone SP bug.
3. **Distance test for all 2-fer kinds (attack 3):** any live row whose two pins are over 100 km apart (not big/line/multi) HOLDs, area or not.
4. **Normalise the path (attack 5):** compare `x.json` with `x.json.gz` as ONE file; when both exist HOLD. A gz twin that shrinks rows by more than 10% HOLDs.
5. **Small-state floor (attack 4):** hold any candidate loss when the live file had ≥ 1, if it exceeds 50% or 2 rows, whichever is larger.
6. **Status match (attack 6):** `status|verdict` upper-cased contains `READY` and not `STOPPED` → run F-S1.
7. **Closures state filter (B1):** require a state word to appear as the state's name in a place role: `, XX` / `State of X` / `X State Park/Forest`, and exempt `Indiana bat`, `<state> County` of the file's own state, `state line`, `border`, `West Virginia` / `Virginia` for KY. Better: judge by the row's `ref` belonging to this state's park list (the park list is independent) and only use the word filter when the ref is missing.
8. **Route the rest (B2):** add routes for `data/fers/CA-XX.json` (the same check with `canada.json` pins), and list `line-/missing-/same-outline-/expected-/looked-` as 'info files, pass if JSON parses'.
9. **Undo generations + dated look lines (C1, C2).**

## E. Grey areas for Brandon
- **G5.** After a RULE fix (NS label, R-SF, B13b) a whole area changes by over 30%. Should a human stamp ("rule change: NS, Oct 29") let the new file PASS once, or should every such file HOLD for a look? My lean: stamp, one release per rule, with the known-answers list checked.
- **G6.** Closures: is an over-a-third-bad file HELD (as built), or are the removed rows simply removed and the rest published? With the state filter as written the first reading holds good files. My lean: hold only when the bad rows are rules other than 'another state', until the state filter is fixed.
- **G7.** How many known pairs per state is enough (today KY 20, others 0)? I can write 3-5 per state from the 2-fer work: Brandon, OK?

## F. Replay test
The 23/23 replay passes because it replays the bad files that were already seen. It does not contain attacks 1-7 above. Add each to `replay.json` as a permanent case (bad: A1-A7; good: B1) so a later code change cannot reopen them.

*Sandbox caveat:* promotion mode was tested only on a toy file (`data/pota/index.json`); I did not run it on real data. Nothing was written to KPC-Data or KPC-Links except this report.

---
# RETEST (chat 8, Oct 29 ~7:50 AM) against KPC-Data b1a5586f — grade A, all run in the sandbox
**All 7 first-round holes are closed.** Still PASS where it should HOLD: none of A1-A7 as first written. (My first "rotate the pairs" attack was a bad test: rotating whole rows keeps the same pair SET, so it rightly passed. Cross-joining one park of a pair with another row's partner is the real attack.)
| Attack | Result |
|---|---|
| Pairs cross-joined 100% / 30% / 20% / 10% (OH) | HOLD (80% pair rule, plus 100 km rule: 5 rows 144-295 km apart) |
| Candidates → dropped; NOT SURE → candidate; duplicates with new ids | HOLD |
| 8 fake rows (IL) | HOLD (100 km + count) |
| NM emptied / all dropped | HOLD |
| .gz twin 50% | HOLD · twin at 95% PASS (5% loss is allowed) |
| Key: all swapped / 10% / shared-word swaps (6%) | HOLD (F-O2 names) |
| Status 'PART READY FOR CHAT 8' / 'Ready' with unchecked rows | HOLD |
| Legit KY closures text (Indiana bat, Washington County, state line, West Virginia hunters) | **PASS** (was the false alarm) |
| OH park numbers in a KY closures file / made-up number / empty / all expired | HOLD |
| Real KY closures, real OH 2-fers, real KY 2-fers, real OH key | PASS |
| A held file blocks others? | **No**: a junk file and an unknown file were held, the good file passed every time |
| Undo: 4 promotions, undo, then `@3` | Works (v4→v3, then back to v1): 3 generations kept |
| One look-line per held file, with its age | Yes; release refuses `..` and non-`data/` paths and is logged |

**Still gets through (smaller holes, grey areas):**
1. **Near-miss wrong joins:** 4 of 25 OH pairs (16%) swapped to a DIFFERENT park within 20 km → PASS. The 80% rule allows up to 20% wrong and the 100 km rule cannot see near ones. Inherent without the outlines; only the rule-F known pairs and a person's spot check catch it. Fix idea: also HOLD when more than 10% of pairs are NEW since live and none were looked at by a person (a count of new pairs, not just lost ones).
2. **Key: 4% of outlines swapped (about 10 parks) → PASS**, and a bot that renames the park to match the swapped layer name passes completely (A2d). The test reads names the bot wrote. Real fix = the shape test (pin inside or within 5 km of the outline) once the key files carry shapes, or a nightly sample of 20 outlines checked by a different path (point-in-polygon from the raw PAD-US layer).
3. **Closures row with no park number and no state word** ("Hocking Hills State Park trail closed" in the KY file) PASS; a row with "Ohio" and no number is taken out (good). Fine, rows usually carry a number.
4. **Dead bot / dead checker:** `heartbeat.json` is written but NOTHING reads it. If the waiting room itself stops running, nobody is told and files just pile up in `in/`. Fix: the daily status page (or chat 11's check) turns red when the heartbeat is over 36 h old, and when a file in `in/` is older than 3 days.
5. A `release` publishes any `data/` file with no check (by design). Add: release refuses a file whose own judge verdict is a hard error such as unreadable JSON.
6. A status field missing altogether (`state` instead of `status`) skips the READY test; only matters for review files.

**Verdict:** the waiting room is good enough for the pilot on the access-points bot. Before it guards 2-fers and keys, do 1, 2 and 4.

---
# RETEST 2 (chat 8, Oct 29 ~7:45 AM) against KPC-Data 0ed9892c (replay 37/37)
- Near-miss swap (4 of 25 OH partners moved to a park within 20 km): **now HOLD** ("4 new candidate pairs, over 10%") (grade A).
- Bot renames parks to match swapped outlines (A2d): **now HOLD** ("262 parks carry a name that is not POTA's") (A).
- Swaps among shared-word names, 10% swap: HOLD. Everything from round 1 still holds/passes the same way; real OH/KY files and the legit KY closures file PASS (A).
- Heartbeat / 3-day waiting file: now on the status board (kpc_status.py), read as code only (B). Release refusing unreadable JSON: read only (B).
- **Not testable here:** the PAD-US shape test (needs NET=1). This sandbox cannot reach PAD-US (URLError), and the checker then HOLDS the key ("PAD-US did not answer"): fail closed, correct. By the code, a 4% swap (10 changed outlines, all tested) should hold, but I have not seen it run. **First real run: watch one US key file through it and read the F-O4 note.** Side effect: if PAD-US is down for a night, EVERY key file holds that night.
- Still open, small: a 4% outline swap passes when the shape test is off (NET unset); a closures row with no park number and no state word passes; 15-25% of pairs rewritten inside an area passes the 80% rule only when each new pair is also not "new" (cannot happen now: new pairs over 10% hold).
**Verdict: no known way left to get a bad file through except the shape test unseen. Ready for the access-points pilot; run the first key file with NET=1 in GitHub and read its notes.**
