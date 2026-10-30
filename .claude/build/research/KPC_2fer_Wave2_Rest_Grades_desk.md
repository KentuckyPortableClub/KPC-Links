# 2-fer grading: rest of Wave 2 (chat 8, Oct 30 2026)
MN, IA, VA, AZ, OH, NM, CO, RI -- Maine + Hawaii already graded (PASS) in a separate writeup. All 8 verdicts say READY FOR CHAT 8, known_answers 19/19. All 8 are in the waiting room, not yet live.

## Candidate counts vs Brandon's Oct 30 status table
| State | Brandon's count | Live candidates now | expected-*.json FOUND | Note |
|---|---|---|---|---|
| MN | 116 | 103 | 126 | gap, see below |
| VA | 48 | 47 | 50 | small, accounted for |
| AZ | 35 | 35 | 36 | exact match |
| OH | 27 | 27 | 34 | exact match live; FOUND gap explained by the duplicate bug |
| NM | 23 | 9 | 24 | **real gap, see below** |
| CO | 17 | 17 | 18 | exact match |
| RI | 3 | 4 | 3 | fine (one new find) |
| IA | 1 | 3 | 2 | fine (new finds) |

## Already-known issue, re-confirmed present (not newly caused by chat 8): same-land duplicate merge bug
All 8 states still carry the self-referential merge-stub duplicates reported while grading ME/HI: MN 370 stub rows (1 self-ref), VA 59 (2), AZ 213 (0 self-ref but still padded), OH **142 stub rows, 120 of them self-referential** -- the worst of this batch, CO 115 (1), NM 17 (0), RI 2 (0), IA 0. Nothing new to add here beyond what's already flagged to chat 2 as release-blocking.

## NEW FINDING: real missing answers, not just duplicate padding (NM serious, MN moderate)
Checked whether every `expected-*.json` FOUND pair actually shows up *somewhere* in the state's spots array (as a candidate, a dropped row, or a merge stub -- anywhere at all). For AZ, OH, VA, CO: every FOUND ref pair shows up somewhere (their candidate-count gaps are fully explained by the duplicate-merge bug swallowing rows, not missing data). But **NM and MN have ref pairs that are not in the spots array at all** -- no candidate, no dropped row, no merge stub, nothing:
- **NM: 19 of 24 expected FOUND pairs (79%) are completely absent from US-NM.json.** Checked that this isn't a dropped/retired park: US-4517 (the park that shows up in the most missing pairs) is confirmed live with a real boundary in `data/us-key/US-NM.json` (1,575,725 ac) and is not in `missing-nm.json`'s no-boundary list either. So the pipeline simply never generated a row for most of these pairs this run -- a real pass1/2/3 gap, not a drop/merge/no-boundary case. This is why NM shows only 9 live candidates against Brandon's reported 23 -- most of the missing 14 are these ghost pairs, not new drops.
- **MN: 13 of 126 expected FOUND pairs are completely absent** the same way. Smaller share (10%) but same pattern.
- OH, VA, AZ, CO: zero ghost pairs -- clean on this specific check.

**This is a different bug from the duplicate-merge one** (that one makes real rows appear 2-113x; this one makes some expected rows not appear at all) and it's worth chat 2/chat 9 knowing before NM and MN release, since right now their waiting-room pages would under-report real 2-fers. Recommend: rerun pass1-3 for NM specifically (worst-affected) and spot-check whether a wider rerun needed for MN, once the duplicate-merge fix goes in -- both issues likely want fixing in the same rebuild pass rather than two separate ones.

## Missing-check reasons (DROPPED / NEVER LOOKED AT)
Checked every reason field across all 8 states' expected-*.json files -- zero blank reasons (MN 203+2338, VA 92+1101, AZ 172+351, OH 106+490, NM 73+450, CO 109+1676, RI 15+290, IA 5+679). All sound, same pattern as Wave 1 and ME/HI.

## Bottom line for chat 2 / chat 9
- **AZ, CO: PASS, no new issues.**
- **VA, OH, RI, IA: PASS** -- their count gaps vs Brandon's table are fully explained by the already-known duplicate-merge bug (chat 2 already has this).
- **MN: HOLD (minor)** -- 13 ghost pairs on top of the duplicate bug; same rebuild that fixes the merge bug should be checked for these too.
- **NM: HOLD (real)** -- 19 of 24 expected answers (79%) are missing outright, not just duplicated or dropped-with-reason. Worth a dedicated rerun of NM's pass1-3 rather than assuming the general merge-bug fix will catch it, since the gap looks like a different failure mode (rows never generated, not rows mis-merged).
