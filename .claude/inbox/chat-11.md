# CHAT 11 INBOX (bot-output checker, Sonnet)
Read .claude/inbox/README.md first. ROLE: grade what the BOTS produce (official documents, hours/fees/permits, campground info, Truth Checker, World Harvester, Gap Filler, scoreboard, layer intake). Chat 8 keeps 2-fers, boundaries and rule sheets. Read only; never edit bot data or scripts; the owning chat fixes. Each bot now has a self-grading gate (chat 10): you see its FAILURES + a small sample, not everything. Your bar: A+B >= 90% on a 10-12 item sample, with a written 'why' per C.

## OPEN (top = first)
- Every session: read KPC-Data data/status/inbox-chat-8.md (bots' 'grade me' lines; until chat 10 renames it) and grade each batch: file `.claude/build/research/<BOT>_grade_<area>_desk.md`, then add the fixes as an item in the owning chat's inbox (chat 10 for its bots, chat 2 for the documents bot + harvester).
- Florida documents regrade: waits for chat 2's Florida fix (in chat 2's inbox); then grade a fresh 12.
- After chat 10's batched Kentucky rerun (hours, campground, truth checker): regrade a fresh 12 of each.
- The 4 'agree' rows with no park name on the page (US-13607, US-3801, US-3802, US-7957) and the 3 Fort Donelson / Fort Heiman style wrong-unit cases: verify when the rerun lands.

## NEEDS BRANDON
- Nothing new from me. Already waiting on him (chat 10's list): `RIDB_API_KEY` in KPC-Data (42 federal campground records stay empty) and the FCC token.

## DONE
- Oct 28: first batch graded, all from Kentucky, all FAIL the 90% bar: TRUTH CHECKER 9/12 = 75% (flagged rows 15/19), HOURS 4/12 = 33% (its own gate 24%), CAMPGROUND INFO random 10 = 50%, DOCUMENTS bot finder check 17/25 = 68% (12-sample 10/12). Files: `.claude/build/research/KPC_TruthChecker_grade_US-KY_desk.md`, `KPC_Hours_grade_US-KY_desk.md`, `KPC_CampInfo_grade_US-KY_desk.md`, `KPC_Docs_grade_US-KY_desk.md`. Fixes sent to chat 10 (3 bots), chat 2 (documents bot + outline leads), chat 8 (US-10105 flag, finder check done). The truth checker's 'grade me' line (run 40669098603) is graded; I cannot edit KPC-Data from here, so chat 8 strikes it.

## REPORT TO HQ (newest first)
- Oct 28 ~6 AM: first inbox session. Graded the four Kentucky batches (files above): none reaches A+B 90%. Best finds the bots made: Levi Jackson (city handover + 896 acres) and Otter Creek (2026 county transfer). Worst: HOURS bot (24% on its own gate; do not start its long run), campground bot (elevation stored as RV length on 4 WMAs, 'no sewer hook-ups' stored as sewer = true, duplicates, footer phones), and handover hints (about 85% noise from 3 generic pages). Documents bot: Wild and Scenic Rivers get a state water-GIS page as their map; Tennessee 12% maps = not ready. Truth checker 'agree' rows are solid (11 of 11 checked). Suggested order for chat 10: one batched Kentucky rerun of all three bots, then I regrade. Not graded yet: Florida (waits on chat 2), harvester, gap filler, scoreboard (no 'grade me' lines yet). Observation for HQ: the bots' own gates are too thin (truth checker passed on 2 known answers while 4 of 19 flagged rows were wrong) and the 12-samples the bots print are 'first 12' / 'most facts', not random: I sampled my own from the JSON.
