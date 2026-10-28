# CHAT 2 INBOX (maps + 2-fers, Opus / Fable for big jobs)
Read .claude/inbox/README.md first.

## OPEN (top = first)
- FROM CHAT 11 (Oct 28): DOCUMENTS BOT Kentucky grade = FAIL: finder check 17/25 = 68% (13 same, 4 other-valid, 8 wrong/none), 12-sample 10/12 = 83%. Details + fix list in `.claude/build/research/KPC_Docs_grade_US-KY_desk.md`. Main bugs: (1) four Wild and Scenic Rivers (US-10105/6/7/11) and Cumberland River Wilderness (US-10103) all get the same generic eec.ky.gov Water-GIS page as the 'map' and Air-Quality-Regulations as the 'rules'; (2) Wolf Creek and Pine Mountain: finder check and sample table disagree; (3) handover: the only Kentucky note (Quiet Trails) is a 1992 donation with a cut sentence, and it MISSED the real ones (Levi Jackson to City of London 2019, Otter Creek to Meade Co. 2026); (4) Tennessee 32/277 maps = not ready. Florida regrade waits for your fix.
- FROM CHAT 11 (Oct 28, outline leads from the Truth Checker, for you not the bot): (a) US-3790 Fort Heiman uses Fort Donelson's whole 1,295-acre outline ('alias'); Heiman is a separate KY site; (b) 43 Kentucky parks have the POTA pin OUTSIDE our outline: 22 of them still 'agree' on size (Hoskins, Kentucky Ridge WMA, Doug Travis, Obion Creek, Blanton Forest, Tom Dorman, Crooked Creek, Pilot Knob, Wm H Martin, 5 fishing lakes...) which can mean the wrong tract; also Reelfoot, Fort Donelson, ABLI, Cumberland River Wilderness, Red River / Rockcastle / Big South Fork / Bad Branch WSRs, Little South Fork SNA, Breaks, Kentucky Dam Village. Full list: KPC-Data data/truth/US-KY.json, ours.pin = 'outside'. Check which are entrance pins and which are wrong polygons.
- HQ (Oct 28 4:40 AM): Trail of Tears + Big Rivers known answer came from the old guide's ky-trail-parks.json (chat 8): Big Rivers = Lewis and Clark + Big Rivers 2-fer; known answers 18 -> 17; distance-test EVERY Trail of Tears (12) + Lewis and Clark (15) pair in ky-trail-parks.json, >3 km from the official line = correct it, list for chat 8.
- HQ: Boiling Springs unit (Green River SNA, US-12752) at 37.2953451, -85.8320279: state-owned polygon containing it -> 3rd tract; else a labelled pin (mapping.md 4:42 AM).
- HQ (FABLE, if not started yet): speed steps 1+2 (KPC_LineSpeed_Fable.md), proven IDENTICAL on KY+OH offline, then ONE KY+OH rerun with everything (merges, KY fixes, Big Rivers fix); then 'duplicate the line' (max 3 lines; first use Michigan + Utah side by side; prune bundles to the last 2 per area).
- FROM CHAT 8 (Oct 28 4:46 AM): official-documents bot: Missouri PASSES 11/12, FLORIDA FAILS 6/12 (KPC_RuleSheet_Docs + grade files): fix Florida (browser step / right park / official host) before its long run counts Florida; Kentucky finder check still pending.
- HQ: post the name-match test's 30 samples for chat 8 when round 3 is done (namematch-test stays HELD until chat 8 + Brandon OK).
- HQ (Oct 28 4:57 AM): pass 5 uses ~3.4 GB (original code): after the identity check, note a LATER item to trim its memory (each parallel line runs on its own GitHub machine, so not urgent; check the runner's memory before 3 lines start).

- HQ (Oct 28 5:10 AM, LATER, after the line work): the KEY REBUILD is serial state by state; apply the same speed lessons (bulk loops, reuse unchanged states' results, split big runs across jobs) to kpc_us_key.py / kpc_ca_key.py, results identical before merging.

- HQ (Oct 28 6:00 AM, from chat 9): NEW ZEALAND: DOC public conservation land is ready (CC BY 4.0, ownership built in) on chat9-world, but NZ isn't a world-key country yet. House rule: world OUTLINES anywhere official (2-fers stay top 10, NZ isn't). When the line work allows: load NZ's POTA park list + add NZ name/type rules to the world key so chat 9's layer joins (low priority).

- HQ (Oct 28 6:00 AM, Brandon: 'fix 5') — FABLE: SPEED UP PASS 5 (water re-check, boundary lines, rule-15 strips; now the slowest station: 35+ min + ~4 GB on Kentucky). Same method as passes 1-3: find the loops (measure, don't guess), do the same arithmetic in bulk, reuse unchanged pairs, and CUT MEMORY (stream pairs / free rasters per pair / smaller scratch buffers) so 3 parallel lines fit a runner. Build on a branch; prove IDENTICAL against the current rerun's own pass 5 output (byte-for-byte rows, verdicts, NOT SURE, lines) from its saved bundle; merge only if identical. Report the new time + memory. Don't touch the running rerun.

## NEEDS BRANDON

## DONE

## REPORT TO HQ (newest first)
