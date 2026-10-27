# Ohio 2-fer spot-check (chat 8, Oct 27 ~3 PM)
Source: KPC-Data `data/fers/US-OH.json` (the 2-fer data now lives in the KPC-Data repo). File only; I cannot see the maps. Grade B.

**Verdict: mostly good, 3 fixes before Michigan.**

Counts (222 rows): 27 candidate (17 of them "same land, two park numbers", 10 real overlaps), 4 very tight, 14 not sure, 1 water only, 53 merged, 110 dropped, all passes 1/1/1.

What looks right
- Wayne NF x Wallace H. O'Dowd and Symmes Township wildlife areas: 13 rows dropped "side by side" (state land beside Forest Service land). Correct under the ownership rule; the 2015 ownership-map caveat is why none are shown.
- 14 NOT SURE kept out: 5 "owner not known for Burr Oak State Park" (no public owner = not sure, as ruled), 7 FWS/state mixed owners, 1 mixed state/unknown, 1 low-confidence Headlands Dunes outline.
- Same-land rows merged into one row per pair (up to 7 rows folded into one).

Fix before the next region
1. **One row per area pair is not applied in Ohio.** US-1964 x US-7848 has 4 rows (two identical 12.5 acre patches, 5.9, 239), US-4521 x US-5438 has 2 identical 3.3 acre "very tight" rows 400 m apart, US-1958 x US-5442 has one candidate and one very tight. Same fix as Kentucky (one row, up to 3 pins). Please rerun Ohio after that.
2. **Typo in the drop reason:** "is stat land" (should be "state land"). Members would see it.
3. **"Same land" rows (17) carry no checked date, owner line or access pin** (same note as Kentucky). Add "checked" + both map links.

Questions for Brandon: none new.
Next: Michigan spot-check when chat 2's run is green.
