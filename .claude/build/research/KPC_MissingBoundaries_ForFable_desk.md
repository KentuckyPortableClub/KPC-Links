# Missing boundaries + name mismatches: the one-page index for Fable (chat 8, Oct 29 ~8:55 AM)
Everything here is already written in detail by me and chat 2; this page is the map. Counts are from the key files in KPC-Data today (grade A).
**Where the keys stand:** US 13,083 parks: 11,257 outlined, 122 to check, 849 sites on bigger land, 856 nothing found (pin outside its outline: 3,716, well outside 157). Canada 5,918 parks: 4,180 outlined, 62 to check, 372 sites on bigger land, 1,304 nothing found.
**Why a park has no outline (8 reasons, with counts and examples): `KPC_WhyNotMatched_desk.md`.** Fix table in it, biggest first.
**Name near-misses (accent, spelling, 'State Park' vs 'SRA'), graded A/B/NO: `KPC_NameMismatch_USCA_desk.md` (112 near-misses, 66 sister-name pairs) and `KPC_NameMismatch_Decoded_desk.md` (900 US parks decoded from the names dump: 107 SURE, 76 name-match with pin outside, 64 pin inside with a different name, 635 nothing near; 8 decode rules; clean-set grade 73%, so a polygon + size + owner check is still required).**
**Whole-state name hits and far pins: `KPC_ClueSearch_desk.md` (136 of 610: 18 within 3 km = alias candidates, 118 farther).** **Name hunt for 792 state parks: `KPC_NoBoundaryHunt_desk.md` + my review `KPC_NoBoundaryHunt_Review_desk.md`** (aliases 36 keep / 4 check / 3 taken back; Canada 15 yes / 7 check / 7 no); chat 2 added the agreed ones.
**For Fable to look at (what is still open):**
1. The 'nothing near' states: NV 41, MS 39, ND 39 (and others): they need NEW sources, not better matching (Source Book 2 per state).
2. 1,304 Canada parks with no outline: mostly small municipal / conservation sites and the New Brunswick layer (fixed by reading zones by number, chat 2); regrade after the rerun.
3. The 118 far-pin parks: either the POTA pin is wrong (tell POTA) or the name is generic; I marked each in the ClueSearch grades.
4. 'Pin inside another area, name different' (313 US state parks): the park is probably a unit inside a bigger record; needs the part-level clip (chat 2's NY rule) before any alias.
5. Rule in force (Brandon Oct 28): an outline goes on only with a SURE official match (pin inside + name + similar size); everything else stays pin-only.
Nothing here asks Brandon for a ruling.

## RERUN on the new key (chat 8, Oct 29 ~2:05 PM, grade A; asked by HQ for R-G7 step 8)
Key counts today are IDENTICAL to this morning (US 13,083 parks / 11,257 outlined / 122 check / 849 site / 856 none; changed-parks.json is empty), so the key itself placed nothing new. Against my 610-park clue-search list:
- **313 "pin inside a bigger area, name different": 4 now outlined, 309 still open.** Biggest states: ID 27, NV 25, OK 23, WA 17, IN 15, MS 15, VT 13, WI 13, UT 12, NC 11, OR 10, AK 9. List: /tmp copy `rg7_left.json` (refs below in the repo file `missing-after-key.json`).
- R-G7 steps 2-5 (agency's own record, official park map, boundary then ownership, cut) have NOT been run on these yet, so none can go to Fable yet. Only what step 2-5 cannot place goes to Fable.
- The 15 still-open key questions (chat 11) and 26 YES answers are not applied to the key until the waiting room promotes them.
- **"Nothing near": 273, 3 now outlined, 270 open. "Likely": 24, 7 now outlined, 17 open.** Other no-outline parks outside that list: 1,076 (mostly BLM recreation areas 387+35, state trails 73, historic sites 34+33, wild and scenic rivers 32, national recreation trails 30): those are for the Source Book / own-land work, not R-G7.
