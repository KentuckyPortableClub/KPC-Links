# KY + OH 2-fer line: final check (chat 8, Oct 28)
Evidence grade A (opened the bot files: data/fers/US-KY.json, US-OH.json, known-answers.json). Verdict: **KENTUCKY NOT READY, one bug to fix (about an hour). OHIO READY once the same fix is in.**

## Kentucky (69 live, 19 not sure, known answers 18/18)
1. Rulings show right: same land = 2-fer with its label; Fort Heiman own tract; Big South Fork / Cumberland Falls drops; Mammoth Cave owned land; LBL Forest Service land; Boatwright via KDFWR; river 3-fers (Ballard, Boatwright, West KY); Big Rivers = Lewis and Clark 2-fer only.
2. **BUG (blocks READY): the merge swallows big 2-fers into small 3-fer patches.** Pioneer Weapons x Daniel Boone (7,707 ac) and Zilpo WMA x Daniel Boone (223 ac) sit inside one 1.2-ac "very tight" row; Cane Creek x DBNF (6,649 ac) and Rockcastle NWSR x DBNF (2,718 ac) inside a 99-ac row; Clifty x DBNF (12,364 ac) inside a 592-ac row. Hunters would see a 1-ac patch instead of thousands of acres. Fix: keep each pair's own patch as its own live 2-fer row; the 3-fer row is added on top (rule 11), never replaces.
3. 8 duplicate live river rows (same pair listed twice). Fix: de-dupe by sorted refs + kind.
4. Trail of Tears x Lewis and Clark should be WATER ONLY (rule 9), not a live land row.
5. Kentenia slivers and the Bad Branch / Rockcastle NOT SURE rows disagree with the same pairs elsewhere (one side live, one not sure). Same rule must give the same answer.
6. The 19 NOT SURE: reasons right (owner unknown or mixed owners), apart from item 5.
7. Dropped lists: nothing real found thrown out except what the merge hides (item 2).
8. Park lines sit on the patches (spot-checked 12).

## Ohio (304 spots: 27 live, 14 not sure, 2 water only, known answers 18/18)
- No merge-swallow found. Live: 19 "same land" pairs (state park + same-named forest or wildlife area; right label), plus 8 areas (Mosquito Lake 8,817 ac, John Bryan x Clifton Gorge 239 ac, Hocking 30 and 38 ac, Headlands 20 ac, Broken ARO x Flint Run 15 ac; Grand Lake St Marys x Mercer 7 ac and Wayne x Dean 3 ac are "very tight").
- Water only: Independence Dam x North Turkeyfoot, Blackhand Gorge x Dillon WA. Right.
- NOT SURE 14: Cedar Point NWR x Mallard Club and Ottawa NWR x Magee/Metzger Marsh (mixed owners; right: federal and state land mix there), Lawrence Woods x Andreoff (no public owner shown), Dillon x Blackhand Gorge, Burr Oak SP x Wayne NF (5 rows of the same pair: "owner not known"). Reasons fine; Burr Oak repeats 5 times and Ottawa 4: show once.
