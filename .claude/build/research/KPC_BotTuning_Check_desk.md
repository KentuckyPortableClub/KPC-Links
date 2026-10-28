# Bot tuning check (chat 11, Oct 28 ~10:50 AM CDT) — PARTIAL: most proving runs have not landed yet

Why partial: chat 10's table is in its REPORT (11:30 note), but at 15:43 UTC only 4 proving runs had written data: fed camps (KY), US access (MN), state camps (TN), Canada bounds/ca-key. I cannot read the Actions notices for KPC-Data (no API access here), so "gate PASS" below is the gate result stored in the data files, not the log. The other bots wait; say 'Inbox' after their commits land and I finish the table. KPC-Data here is a shallow clone: no "before" copies, so before/after counts are only where KPC-Links history has the old file.

## Per bot
| bot | landed? | gate (from the file) | before -> after | spot-checks |
|---|---|---|---|---|
| fed camps (states=KY) | YES 15:42 | PASS, 5 of 5 known KY camps, none missing | 60 -> 60, 0 records changed | Alum Ford 36.765,-84.547 (NPS) in KY; Bear Creek (KY) + Blue Heron in KY; Bandy Creek + Station Camp stay TN (pins 36.49 / 36.55) = right |
| state camps (states=TN) | YES | no gate text in index.json (stored only in the log) | TN 267 camps, 20 states in index, nothing shrunk to 0 | TN source list shows 6 layers (TDEC campground points + cabins): plausible; Actions notice not read |
| US access (states=MN) | YES | none stored in file | MN 201 parks read, points present | see far-off check below |
| Canada bounds / ca-key | YES (15:38/15:39) | not stored | Banff, Jasper, Bruce Pen., Gros Morne, Algonquin all still have outlines in canada-bounds/index.json | CA-2156 (retired) is still listed in KPC-Data's canada-bounds index and file, but KPC-Links' 15:39 commit deleted the file: mirror lag or an index not rewritten — chat 10 check |
| parking explorer, US trails, state trails, new-refs, ref-check, new-lands, state-gis, bot-queue | NOT YET | - | - | trails: only US-4238, US-4556 + index/state-report changed at 10:42, no gate lines seen |

## The 230 far-off access points
Measured today over all access files (park pin from parkinfo, 270 km or more): 47,377 points, **54 still far**. Only MN has been rerun with the new code, so the drop from 230 is not proof of the fix; the other states are old files. What the 54 are:
- Robert Moses (Long Island) US-2128 and Robert Moses (Thousand Islands) US-4374: 27 points, 502 km away — two parks of the same name sharing one layer = a NAME MIX-UP, not a timeout. Wrong on the map.
- Copan WMA US-6347 (OK) 15 points at 321-327 km; Lost Nation US-10284 (NY) 3 at 376 km; Pine Hill US-5249 (NY) 1; Tillamook US-5461 (OR) 1; PA 086 Game Land 1; **Beaver Creek WMA US-12811 (MN) 2 at 273 km — still there after the MN proving run** (the new check did not catch it).
- Katy Trail US-1766 (MO) 4 at 275-286 km = a 240-mile line park, legitimate.
So 50 of 54 look wrong.

## Federal campgrounds that move INTO Kentucky
None found. Checked every other state's campfed file for pins in Kentucky: Illinois/Indiana/Ohio/West Virginia hits are across the river, and TN/VA rows sit on the right side (Bandy Creek, Station Camp, Dale Hollow, Wilderness Road, Cranesnest, Flannagan, High Knob). Border cases to recheck after the TN/VA reruns: Lillydale (TN file, 36.604,-85.3025) and Willow Grove (36.587,-85.342), both within ~2-3 km of the line. Doubles still in the old files: Bear Creek (KY) and Blue Heron are in BOTH TN and KY (the other states have not been refiled yet; only KY ran). LBL (Piney, Energy Lake, Wranglers, Hillman Ferry, etc.) is in NO federal file at all: that is the "20 campgrounds with no point" gap, not a refile issue. So chat 8's Camp & Activate KY key does not need new rows from this refile.

## FOR FABLE TONIGHT
1. Access points wrong by NAME match: Robert Moses (two parks, 27 points 502 km away), Copan WMA (15 at 321 km), Lost Nation, Beaver Creek WMA. File: data/access/US-NY.json, US-OK.json, US-MN.json; how I know: haversine from the parkinfo pin to each point. The new "40% drop" gate does not catch wrong ties; add a "point more than 100 km from its park, except line parks" drop.
2. LBL campgrounds absent from every federal/state camp file (Piney, Energy Lake, Wranglers, Hillman Ferry, Fenton, Gatlin Point, etc.): grep over data/campfed. Needs a source (USFS LBL page or ArcGIS).
3. Rerun fed camps for TN, VA, WV, OH, IN, IL (states=KY only fixed KY): Bear Creek and Blue Heron still doubled in TN; the 196 wrong-state/132 doubles claim is untested outside KY.
4. Canada: CA-2156 still in KPC-Data canada-bounds index/file; confirm the delete reached KPC-Data.
5. Remaining bots (parking explorer, trails, new-refs, ref-check, new-lands, state-gis, bot-queue): no output yet; grade when they land (say 'Inbox').
