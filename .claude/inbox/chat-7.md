# CHAT 7 INBOX (HQ)
Read .claude/inbox/README.md first. Other chats leave HQ notes here (newest first).

- FROM CHAT 10 (Oct 28 9:50 PM, Brandon asked): BOT-BY-BOT ISSUES, LAST 48 HOURS: `.claude/build/research/KPC_IssuesForFable_Oct29.md` (also the 1:20 AM Fable pass's starting list; the Waiting Room note is section 0). Short: FIXED + counted tonight = access far points 178 -> 0 (52 on line parks) and fed-camp doubled ids 132 -> 0 (both had silently NOT been fixed at 11:45 AM: the rerun never started + the rule spared every far point); closures hunt 0 -> real dates but gate 46% (quota dates for 6 WMAs live on a page we have not found); truth v12 KY+VA+IL test running; hours PASS 88%; campground waits on chat 11's v8 grade; Waiting Room built, replay 20/20, NOT switched on.
- **FROM CHAT 2 (Oct 29 7:05 AM): STORED OUTLINES CHECKED (your border-thinning ask), sample vs a fresh full-detail read:**

| Stored set (who reads it) | parks | corners OFF the real edge (95%) | real corners CUT (median / 95%) | verdict |
|---|---|---|---|---|
| Kentucky files ky-*.geojson (site + KY 2-fers + app pack) | 16 | 0.6 m (on the edge) | 2.7 / 8.4 m (one 217 m: Tygarts) | edge-keeping, but cuts corners ~8-10 m: over 5 m |
| Kentucky app pack (3 m Douglas-Peucker of the KY files) | 12 | 0.6 m | 7.7 m (Knobs SF row = a test mismatch) | same as the KY files (+≤3 m) |
| US key saved copy cache/us (2-fer pass 1 coarse look only) | 20 | 0.6 m | 36.6 / 78 m | coarse BY DESIGN; passes 2-3 re-read finer; not drawn by the site |
| Canada key saved copy CA-ALL (2-fer pass 1 + saved builds) | 20 | 46-61 m (drifted) | 348 / 1,643 m | coordinates rounded to 3 decimals (~100 m) + 0.02 deg thinning |
| Canada outlines the SITE draws data/canada-bounds | 12 | 47 m median (drifted) | 252 / 5,042 m | thinned 0.0004 deg (~44 m), big parks 0.002-0.006 deg (200-650 m): WORST set |

  Also: the site draws US + Canada key outlines LIVE with maxAllowableOffset 0.0001-0.0002 deg (kpc-bounds.js) = server thinning up to ~11-22 m, which alone explains chat 3's 8-20 m. Suggest 0.00003 (~3 m) near 2-fer spots (chat 3's page). Proposed (chat 2, needs HQ's OK for storage): re-read data/canada-bounds at 0.00003 deg with geometryPrecision 6 (edge-keeping Douglas-Peucker at 3 m on our side for big parks), re-thin the KY files the same way from a full read, keep the coarse key copies coarse (pass 1 only). Full table: .claude/build/research/outline-accuracy.md.
