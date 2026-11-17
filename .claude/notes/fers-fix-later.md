# 2-FER FIXES, SHELVED (owner 17 Nov 12:42 PM: "Shelf the reviews and your notes for 2fer to fix later")
Pick up AFTER the key batch + rebuild. Nothing below is built.

Sources: HQ review claude.ai/artifact/BRMjsquh27VnuDSzJEi8KR; Handoff 6 reviewer report (owner's upload
handoff6-2fer-code-review-nov17.docx, 17 Nov); already built today: boundaries only (#264), Q1 private-land note (#260/#261),
never worse only for missing inputs (#260), final redact (#255), rules check workflow (#263).

## Bugs (no ruling needed)
- Quiet failures: US land_check crash -> row becomes a candidate (Canada says not sure); closed-area map no answer = treated as
  nothing closed; a crashed pair just disappears, run stays green; an area may lose up to 20 unreadable parks and still count
  as finished. All must fail loud or say NOT SURE.
- Owner ruling N3 (16 Nov: near a size line = NOT SURE) never built: pass 3 grid is 5 m, so 16-20 m overlaps slip past the
  25-yard (22.9 m) line and 46 m reads 45. 472 old rows sit within ~5 m of a size line.
- D10 silently off on the PC runner (not-sure.json not where the PC run looks).
- Old rows revive with no age or key check: 42 files predate the Oct 29-30 rebuild (1,849 rows); nothing reads OLD-KEY-QUARANTINE.
- Math / rule changes do not force a recheck; 20,749 passing spots discarded (WL7).
- World check order would label UK-style national parks (designation lines) public land: apply the Q1 note there too.
- tests/test_fers_area_boxes_time_nov11.py fails byte-for-byte on Python 3.13.5: rerun on 3.12; golden byte tests break on harmless changes.
- Report 'problems' keeps 40 lines and GitHub 10 notices per step: write the full list to the private folder.
- Hard-coded pairs (KNOWN_LIVE, KY_DROP, SAME_LAND_PAIRS, MAPFIX) -> one data file with date + who ruled.
- Kentucky's separate path: fold into the national one later.

## Questions for the owner (HQ lean in brackets), unanswered
1. Summary-map (compilation) outlines official? [only until the agency's own map is found; approximate meanwhile, like D7]
2. National park / refuge x national forest next door along their shared border (Grand Canyon x Kaibab 281 ac, Olympic x
   Olympic 1,029): NOT SURE by default unless one is a designation laid on the other? [yes]
3. Within ~8 m of a size line = NOT SURE until fine lines decide? [yes, his N3]
4. How old may a carried row get? [never past a key rebuild]
5. Separate patches the fine pass finds as their own rows (KPC_FERS_FINE_ONLY=count + 100 m rule)? [yes]
6. Strip a held park's outline pieces from carried rows, keep 'there may be a 2-fer here'? [yes, privacy]
7. Mark scope entries 2026-11-17-thin-shelf and 2026-11-17-d10-tripwire-not-sure approved (owner approved them)? [yes]
