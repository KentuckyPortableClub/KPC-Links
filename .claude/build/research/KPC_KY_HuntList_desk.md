# Kentucky hunt list 2026-27 (chat 8, Oct 29 ~9:00 AM) — for Brandon to check
List: `data/closures/hunt-lists/US-KY-2026-27.json` content is below (KPC-Data is closed to this chat: chat 10 copies it in from `.claude/build/research/US-KY-2026-27.json`; `checked_by` stays EMPTY until you say it is right).
**Source:** the KDFWR hunting guide quota table, https://www.fw.ky.gov/Hunt/Documents/HuntingGuideQuotaHunts.pdf. I could not download it (this chat's network is blocked); I read the table twice through the page reader. Both reads agree on every area and date (38 rows). Grade B (the reader paraphrases the notes, so quote the dates, not the wording).
**What the list says (36 area rows + 4 not-numbered WMAs):**
- **CLOSED to everyone except drawn hunters (4 areas):** Big Rivers WMA US-3796, Cane Creek WMA US-10121, Higginson-Henry WMA US-3815: **Nov 6-8** (the area page says: closed during AND the day before the two-day hunt that starts the first Saturday in November; the guide dates are Nov 7-8). Curtis Gates Lloyd WMA US-3805: **Nov 14-21**.
- **Hunt NOTE only (the area page does not say the area closes):** Ballard, Beaver Creek, Clay, Dewey Lake, Fishtrap Lake, Dennis-Gray, Kentucky River, Kleber, Rich, Pennyrile SF, Tradewater, Veterans Memorial, West Kentucky (Tract 1 closed), Zilpo (Dec 12) and the 6 state-park hunts (Dale Hollow Nov 20-22 + youth Dec 4-6, Greenbo Dec 17-20, Green River Lake SP Dec 10-13 and 17-20, Kenlake Nov 19-22 and Dec 3-6, Kincaid Dec 3-6 and 11-14, Lake Barkley Nov 2-6 and Jan 5-6).
- **No POTA number:** Green River Lake WMA, Paintsville Lake WMA, Taylorsville Lake WMA (the POTA parks of those lakes are state parks, a different place) — listed, not used.
**Needs you (3):**
1. **State park hunts (Dale Hollow, Greenbo, Green River Lake, Kenlake, Kincaid, Lake Barkley):** the guide says only that drawn hunters hunt there. Does the park close to visitors on those days? I could not read the park pages; the list makes them notes. Your call, or a member who knows.
2. **A stray sentence:** the bot filed "closed for four consecutive days starting the third Friday in November" (Nov 20-23) under Green River Lake State Park US-1259. By the guide that is Dale Hollow (Nov 20-22). I believe it is Dale Hollow's; tell chat 10 to re-file it (or drop it).
3. **Deer only.** The guide's table is the DEER quota hunts. Pheasant (Clay WMA Dec 4-7), waterfowl, elk and fox-trial closures already come from the area pages; nothing else is added here.
**Dates sanity:** first Saturday of November 2026 = Nov 7 (so Nov 6 = the day before). Third Friday in Nov 2026 = Nov 20. Zilpo's hunt is in even years = Dec 12, 2026.
**For chat 10:** copy the JSON to KPC-Data `data/closures/hunt-lists/US-KY-2026-27.json`; the bot reads only a list with `checked_by` set, so nothing goes live until Brandon says OK. Rule for other states (8.11): same format, one row per park number and date range.

## UPDATE Oct 29 ~8:40 AM (Brandon 8:23 AM answers)
- **State park hunts = NOTE only** (the park stays open; at most parts close). The 10 rows (Dale Hollow x2, Greenbo, Green River Lake SP x2, Kenlake x2, Kincaid x2, Lake Barkley x2) carry the wording "Parts of the park may be closed during the quota hunt <dates>." and `inside_park: NOT VERIFIED`: **held back until the hunt ground is checked against the park's POTA boundary.** I could not do that from here: the guide and the State Parks hunt info sheet (kyparks, 2022-23) only say "contact the park"; the maps are not on a page this chat can open. **Hand-off:** chat 10 / a GitHub bot reads each park's quota-hunt map (the park's page under parks.ky.gov, or a request to the park) and tests the hunt area against our park outline (data/ky-*.geojson). Inside = the wording goes live; next to it = the note moves to the neighbour (a WMA with a number) or nowhere. Lake Barkley is NOT in the State Parks' own hunt sheet at all (only the guide lists it): check that one first.
- **Misfiled sentence deleted from the list:** the 'third Friday in November' line was never in my list (I only flagged it); chat 10 must remove it from US-KY.json (US-1259, Nov 20-23).
- The list is otherwise unchanged: 4 closed areas, wildlife area notes.

## STATEWIDE SEASONS 2026-27 (chat 8, Oct 29 ~9:50 AM) — into `US-KY-2026-27.json` as `seasons`
Source: KDFWR hunting guide, https://fw.ky.gov/Hunt/Documents/huntingguideentire.pdf (deer p.10, fall turkey p.22), read twice through a page reader; two gaps filled from the KDFWR seasons planner page. Grade B.
| Season | Dates as printed |
|---|---|
| Deer archery | Sept 5, 2026 - Jan 18, 2027 (guide p.10 shows 'Sept. 5, 2026 -'; the end is from the seasons planner) |
| Youth/senior crossbow | Sept 5, 2026 - Jan 18, 2027 (planner; guide shows '...Jan. 18, 2027 *'; for residents 65+ and youth under 16) |
| Crossbow | Sept 19, 2026 - Jan 18, 2027 |
| CWD antlerless (Zone 1-3 counties in the CWD zone) | Sept 25-28, 2026 |
| Youth-only modern firearms | Oct 10-18, 2026 |
| Early muzzleloader | Oct 17-18, 2026 |
| Modern firearms | Nov 14-29, 2026 |
| Late muzzleloader | Dec 12-20, 2026 |
| Free Youth Weekend (the 'holiday youth' season) | Dec 26-27, 2026 |
| Fall turkey: shotgun | Oct 24-30 and Dec 5-11, 2026 |
| Fall turkey: archery | Sept 5, 2026 - Jan 18, 2027 |
| Fall turkey: crossbow | Oct 1-18 and Nov 14 - Dec 31, 2026 |
**Brandon's turkey read CONFIRMED** (all three match). Notes: (1) the guide's p.11 box says proposed rules may add antlerless seasons and open some WMAs; they are pending, so check fw.ky.gov in the fall. (2) WMA-specific season exceptions: none found in what I can read; the Public Lands page still shows 2025-26 (not used). The guide's Public Lands section was cut off in the reader: a bot should read pages with per-WMA season text. (3) Only the QUOTA hunts close an area (see the list above); a statewide season never closes a WMA to the public.
