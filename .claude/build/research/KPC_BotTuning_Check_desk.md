# Bot tuning check (chat 11, Oct 28; updated 12:40 PM CDT) — what has landed is checked; the rest is marked WAITING

Why partial: chat 10's table is in its REPORT (11:30 note), but at 15:43 UTC only 4 proving runs had written data: fed camps (KY), US access (MN), state camps (TN), Canada bounds/ca-key. I cannot read the Actions notices for KPC-Data (no API access here), so "gate PASS" below is the gate result stored in the data files, not the log. The other bots wait; say 'Inbox' after their commits land and I finish the table. KPC-Data here is a shallow clone: no "before" copies, so before/after counts are only where KPC-Links history has the old file.

## Per bot
| bot | landed? | gate (from the file) | before -> after | spot-checks |
|---|---|---|---|---|
| fed camps (states=KY) | YES 15:42 | PASS, 5 of 5 known KY camps, none missing | 60 -> 60, 0 records changed | Alum Ford 36.765,-84.547 (NPS) in KY; Bear Creek (KY) + Blue Heron in KY; Bandy Creek + Station Camp stay TN (pins 36.49 / 36.55) = right |
| state camps (states=TN) | YES | no gate text in index.json (stored only in the log) | TN 267 camps, 20 states in index, nothing shrunk to 0 | TN source list shows 6 layers (TDEC campground points + cabins): plausible; Actions notice not read |
| US access (states=MN) | YES | none stored in file | MN 201 parks read, points present | see far-off check below |
| Canada bounds / ca-key | YES (15:38/15:39) | not stored | Banff, Jasper, Bruce Pen., Gros Morne, Algonquin all still have outlines in canada-bounds/index.json | CA-2156 (retired) is still listed in KPC-Data's canada-bounds index and file, but KPC-Links' 15:39 commit deleted the file: mirror lag or an index not rewritten — chat 10 check |
| parking explorer, US trails, state trails, new-refs, ref-check, new-lands, state-gis, bot-queue | NOT YET | - | - | trails: only US-4238, US-4556 + index/state-report changed at 10:42, no gate lines seen |

## UPDATE 12:40 PM CDT (what changed since the 10:50 note)
- **Canada: FIXED.** CA-2156 is gone from KPC-Data's canada-bounds index and file; Banff, Jasper, Algonquin, Gros Morne, Bruce Peninsula still have outlines.
- **US trails: kept.** Appalachian Trail (US-4556) and the state trail Sheltowee (US-11181) are still in the data, nothing vanished.
- **Access reruns (13 states) and fed-camp reruns (TN VA WV OH IN IL): NOT LANDED.** Last access commit is 15:57 UTC (before the 100 km name gate was written) and the fed-camp files still show 132 doubled ids (GA/SC, GA/FL ...). Measured today: **178 points are 100+ km from their park**; of these Katy Trail (32 of them) is a 240-mile line park and fine. Still wrong: Robert Moses x2 (27 points at 502 km), Copan WMA (15 at 321 km), Tillamook (12), Lake Sakakawea (13, 116-187 km: may be a long lake park, check), Sherman Creek (11), Dorer (5), Genesee Greenway/Erie Canal (10, line parks). The new gate in kpc_us_access.py (line 357-360) is the right test; this check of the output must wait for the rerun.
- Waiting, no output seen: parking explorer, state trails (only the old 10:42 report), new-refs, ref-check, new-lands, state-gis, bot-queue. State camps TN landed earlier (267 camps).
- I cannot read the Actions logs for KPC-Data from here, so gate results are only those stored in files.

## FOR FABLE TONIGHT (ranked)
1. **Access points tied to the wrong park by name** (Robert Moses x2: 27 points 502 km; Copan WMA 15 at 321 km; Tillamook 12; Sherman Creek 11). File data/access/US-NY.json, US-OK.json, US-OR.json, US-WA.json. How I know: distance from the parkinfo pin to each point. After the 13-state rerun lands, count again; if any remain, the gate misses 'name'-tied rows with a wrong park number.
2. **Federal camps: finish the refile and prove it** (132 ids still in two states; Bear Creek (KY) + Blue Heron in TN and KY). File data/campfed/US-*.json. After the TN/VA/WV/OH/IN/IL rerun: count doubled ids (goal 0) and check Lillydale + Willow Grove (TN, 2-3 km from the KY line). No camp moves into Kentucky from the old files, so chat 8's KY answer key stands.
3. **LBL campgrounds are in no camp file** (Piney, Energy Lake, Wranglers, Hillman Ferry...): chat 9 owns the source; it is also why Camp & Activate has 20 'no point' camps.
4. **Documents bot rules pages** (chat 2): 83 WV parks share a whitewater rules page, 130 GA parks one publuu booklet, 53 FL a shooting-range page, 26 VA maps = inciweb. File data/docs/US-WV|GA|FL|VA.json. See KPC_Docs_chunks1-3_grade_desk.md.
5. **Closures round 4**: grade when its 'grade me' line lands (round 3 = 77%; standing rules, a Virginia notice under KY, expired items).
6. **Remaining tuned bots have shown nothing**: parking explorer, state trails, new-refs, ref-check, new-lands, state-gis, bot-queue. Ask for one 'Inbox' after tonight's runs; I will do the gate-by-gate table then.
