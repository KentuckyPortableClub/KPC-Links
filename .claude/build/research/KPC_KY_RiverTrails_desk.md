# Kentucky river-trail check: Lewis and Clark + Trail of Tears (chat 8, Oct 27 ~3:45 PM)
Brandon: "Lewis and Clark and Trail of Tears missed all the 2-fers on the river, e.g. Ballard WMA." **He is right.** Grade B (data + code read; I cannot see the maps).

**What the data shows**
- Our hand file `ky-trail-parks.json` lists 27 river pairs (Ballard, Big Rivers, West Kentucky, Boatwright, Sloughs, Yellowbank, Otter Creek, Six Mile Island, Green River SF, Audubon, LBL, Kenlake, Kentucky Dam Village, Doug Travis, Fort Donelson/Heiman ...), each "Ohio River bank, within 100 ft of the water".
- The bot's final KY file (`KPC-Data/data/fers/US-KY.json`) has **no row at all for Ballard WMA (US-3793)** and keeps only 4 trail/river pairs (Ohio River Islands, Livingston Co., Columbus-Belmont, Trail of Tears x L&C). About 22 river-bank pairs are missing.

**Why (kpc_fers.py, lines ~268 and ~1160)**
1. A line park is treated as a RIVER (measured from the water's edge, NHD) only if its type text contains "river". "National Historic Trail" does not, so L&C and ToT are measured as plain TRAILS: 100 ft from the NPS centre line.
2. That NPS line is the 1:100,000 "approximate" route (my own note, TrailLines desk #3), 0.2-3 km from the real river. A 100-ft zone around it hits nothing, so every bank pair is dropped.

**Rule (no new decision, this is rule 5 / the 100-ft rule applied right)**
- Water-route national trails (Lewis and Clark, Trail of Tears on the rivers; Fort Donelson/Heiman, LBL, Kenlake on the Tennessee shore) = **river kind**: the NPS line only says WHICH river; the zone is 100 ft from the river's BANK (NHD StreamRiver/water area within ~3 km of the line), on public land of the other park.
- Land-route stretches (Trail of Tears overland, auto-tour routes: Wickliffe Mounds, Big Bone Lick, LBL visitor centre) stay line parks but only on an official line we hold; the NPS "lists this site" entries are sites, not stretches = not a 2-fer unless the park is on the line.
- Keep "approximate line" wording; show "both trail lines are approximate" (ruled).
- Ballard-type WMAs still carry their own closures (quota hunts: closed to non-hunters on those dates) and the ownership test (KDFWR-owned = fine).

**Ask for chat 2 (one bot run, batched, Kentucky only, then I re-check)**
1. Mark NHTs whose route is a water route as kind 'river' (list: Lewis and Clark all KY, Trail of Tears Ohio/Mississippi/Cumberland/Tennessee legs), measure from the NHD bank.
2. Check the 27 pairs in `ky-trail-parks.json` come out (Ballard 7.74 mi, Sloughs 10.76, Otter Creek 11.08 are the big ones); any pair that does not = show the reason in the file.
3. Same fix for the US + Canada run (Missouri/Ohio/Mississippi, Oregon and Mormon trail rivers, Canadian heritage rivers) BEFORE it starts.
