# FABLE QUICK REVIEW: mapping + 2-fer code (Brandon Oct 31 10:36 AM)

You are Fable, opened in a FRESH chat for a quick, READ-ONLY code review. Goal: find bugs in the mapping and 2-fer code NOW, so the full review after US + Canada are complete is easier. You did not write this code; read it with fresh eyes.

## Rules for this review
- READ ONLY: change no code, start no workflow, post nothing. Write findings only (file below). Chat 2 fixes them.
- House rules: `.claude/CLAUDE.md`. Rules in force: `.claude/RULES-NOW.md` (R0-R10 2-fer rules, POTA plain answers, Rule G, R5 trails = within 100 ft of the trail LINE, R6 wild rivers, R7 water only, R9 sizes).
- The GIS hunter + world finder are frozen until Nov 6: note problems there, don't propose rewrites.
- Clone both repos: KentuckyPortableClub/KPC-Links (website) and KentuckyPortableClub/KPC-Data (bots). Read with grep / small scripts; don't load giant data files whole.

## Where the code is
- KPC-Links `.github/scripts/`: `kpc_fers.py` (the 2-fer line) + `kpc_fers_layered.py`, `kpc_fers_line_check.py`, `kpc_fers_far_check.py`, `kpc_fers_far_hold.py`, `kpc_fers_known.py`, `kpc_fers_proof.py`, `kpc_fers_expected.py`, `kpc_fers_review.py`; `kpc_us_key.py`, `kpc_ca_key.py`, `kpc_world_key.py`, `kpc_key_layers.py`, `kpc_key_check.py`, `kpc_ky_key.js`; `kpc_us_trails.py`, `kpc_state_trails.py`.
- KPC-Data `.github/scripts/`: `kpc_layer_collector.py`, `kpc_tiers.py`, `kpc_key_questions.py`, `kpc_key_summary.py`, the waiting room (`kpc_waiting_room.py`, `kpc_release_approved.py`).
- Pages that draw them: `finder.js` / `kpc-overlap-finder.html`, `kpc-bounds.js`, `kpc-trails-layer.js`.

## Known bugs (real cases). #1, #2 (Kentucky), #3, #4, #5 and the release check are ALREADY FIXED by chat 2 / 3 / 10: don't re-report them. CHECK THE FIX IS RIGHT and look for the SAME KIND of bug elsewhere (other states, other rivers / trails, other joins).
Fixes Oct 31 morning: the 2-fer line now takes a water route's water as the river it follows (not lakes / sloughs inside the park); the access pin's road / lot must be on the parks' own land (no road across a river or state line); the Finder draws the line each river / trail row used (dotted, 'approximate line' note); Kentucky's key carries the three trails' official lines (Am I in the Park counts 100 ft from the line).
1. **KY river trails:** the card says 'POSSIBLE RIVER OVERLAP: WITHIN 100 FT OF THE RIVER BANK, US-3791 Trail of Tears NHT + US-3793 Ballard WMA + US-4572 Lewis and Clark NHT, 3 stretches, ~25.6 mi'. The card map does NOT draw the trail lines, and the shaded zone near Metropolis, IL is MORE than 100 ft from the river. Is the 100 ft measured from the trail LINE (R5) or the BANK (label)? Why no line drawn? Are the miles right?
2. **Trails show 'pin' in the key** while the trail file has their lines (Option A, chat 2, Sunday: the key will point trail parks at their official line). Check nothing else assumes trails are polygons.
3. **AT x Virginia trails filed under Maine**, and **the AT's Georgia pin stretched Maine's area box** (chat 2 fixed both Oct 30): look for the same class of bug elsewhere (multi-state parks, area boxes, cross-state lines).
4. **Iowa DNR re-numbered records** were lost until a name-near-pin fallback was added: check other joins that rely on record IDs.
5. The release step only took 'YES' at the start of chat 11's text (fixed Oct 30): look for other brittle text checks.

## Then look for, in order
- Distance math: degrees vs metres, buffers in the wrong projection, 100 ft / 50 yd / 100 yd thresholds applied right (R5, R9).
- Line vs polygon handling (trails, rivers, byways): buffering, clipping to park outlines, 'water only' (R7).
- Multi-state and cross-border parks; parks split into pieces; pins outside outlines (pins never move).
- Simplification over 3-5 m (R-G6), shapes saved at the wrong detail.
- Label text that promises more than the rule (e.g. 'within 100 ft of the bank').
- Anything that silently drops a park or a pair, or fails without a reason.

## Output
Write `.claude/build/research/KPC_Fable_QuickReview_Oct31.md`: for each finding, the file + line, what is wrong, a real example, how sure (sure / likely / check), and the smallest safe fix. Rank by how many parks / pairs it affects. Then add ONE line under `## OPEN` in `.claude/inbox/chat-2.md`: '- **FROM FABLE QUICK REVIEW (Oct 31): N findings in .claude/build/research/KPC_Fable_QuickReview_Oct31.md, the top 3: …**' and one line in `.claude/inbox/chat-7.md` for HQ. Commit once ('Fable quick review: mapping + 2-fer code') with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`, `git pull --rebase`, `git push origin HEAD:main`. End with 3 plain lines for Brandon.
