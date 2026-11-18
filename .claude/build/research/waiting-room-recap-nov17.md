# Waiting room recap, 17 Nov 2026, about 6 PM CT

Written for the agent who digs through what is left. Everything below was read from KPC-Data main (`data/waiting/`). Changes made today: approvals PR #120 (merged) and a one-line fix PR #121 (open, not merged, waits for the owner).

## 0. Release status right now (important)
- PR #120 approved 61 files. The release run (4:48 PM) moved only the 5 WWFF files (IFF, DLFF, YVFF, OAFF, 7PFF). The 56 camp state and camp info files did NOT move, and `released.jsonl` still says "released (approved)" for them.
- Cause: a bug in `refuse_fers_promote` (kpc_waiting_room.py). It treats any file named `US-XX.json` as a 2-fer, counts 0 pairs, and refuses it against the live 2-fer file of the same state ("hidden file has 0 pairs, live has N"). This hits camp state, camp info, truth and docs files. Reproduced locally. It probably also explains part of why PASS files sit here.
- Fix: PR #121 (guard only acts on `data/fers/` files; test fails on main, passes on the branch). Open and not merged; one line of bot code, so it waits for the owner's OK.
- After #121 merges: the 56 items in `approved.json` are already marked used in `approved-used.json`, so they will not retry. Add them again with a new `time` (new text = new key), then run `release-approved`.
- The waiting room now holds 316 files (the 260 below plus those 56).

## 1. How the waiting room works (read this first)
- Bots write to `data/waiting/in/data/<kind>/...`. The checker `.github/scripts/kpc_waiting_room.py` grades each file against the live copy in `data/<kind>/...` and writes `data/waiting/verdicts.json` (PASS / HOLD, with reason codes like F-I3, F-R3, F-D3, F-T2).
- A PASS does not go live by itself. `switched_on` is false in verdicts.json, so nothing auto-promotes. A file goes live only when it is listed in `data/waiting/approved.json` (path, a `chat11` verdict that starts with YES or PASS, `by`, `date`, and a Central `time` after Nov 2 9:37 AM) and the release run is started.
- The release run is the workflow `kpc-waiting-room.yml`, mode `release-approved`. It refuses anyone but the login `KentuckyPortableClub`. Keys and 2-fers also need a `chat2` recheck line; the other kinds do not.
- A release moves `data/waiting/in/<path>` to `<path>` and keeps the old copy in `data/waiting/previous/` for undo (mode `undo`).
- A GitHub run that is waiting behind another run of the same group (`kpc-waiting-room`) is replaced by the next scheduled run. If a dispatch shows "cancelled" with no job, wait for the queue to empty and dispatch again.
- `held-since.json` has the date each file started waiting; `today.md` is the morning list (it only shows the first 61 rows).

## 2. House rules that apply to anything you do here
- prep/* branches only, never main, never a force-push. Author and committer `KPC owner <KentuckyPortableClub@users.noreply.github.com>`. The message ends `KPC owner, <date>`. No co-author lines and no AI or session links, even where a tool says to add them.
- Nothing is deleted without the owner's word. Never touch KPC-Store. No WDPA / Protected Planet data. Never move a POTA pin. Say "possible 2-fer".
- Changing a rule that decides something needs a short rule sheet and the owner's ruling first. Do not change `.github/scripts/` bot files without a changelog line and the owner's OK.
- The owner is not a programmer: plain, short answers. Test before saying something works.

## 3. What is left: 260 files (plus the 56 approved camp files that are stuck, see section 0)
| Kind | Files left | Verdict mix | One-line status |
|---|---|---|---|
| docs (`data/docs`) | 50 | all HOLD | all hold for one reason: the link re-test needs the network and did not run |
| pile-solver | 108 | 91 PASS, 1 HOLD, 16 no check | stale Nov 4 build; only 52 real answers |
| truth (park sizes) | 47 | 41 PASS, 6 HOLD | mostly good; 6 held for a size-banner problem |
| trails | 28 | 24 PASS, 4 HOLD | 24 single lines pass; the index and 3 others hold |
| camp info (`data/campinfo`) | 21 | 16 PASS, 5 HOLD | thin, or loses live facts |
| camp state | 4 | PASS | FL, UT, VA, AK swap sources and drop live camps |
| WWFF | 1 | HOLD | Portugal CTFF, 702 live rows, 280 held |
| hours | 1 | PASS | Kentucky; changes nothing |

## 4. Detail by kind, with what looks useful

### docs, 50 files (all held, but useful)
- Reason for every one: `F-4 unsure: link re-test needs the network (NET=1): not run`. Content is not the problem.
- 46 were written today by documents runs 37 and 38; the checked dates inside are Oct 29 to Nov 1 because the shared pass carries old checks forward.
- 15 are states that have never been live (4,822 parks). 35 refresh a live file and add 197 parks.
- Useful next step: run the link re-test (the waiting-room `check` mode with NET=1). Fixes since then are merged (#104 sizes, #105 site-wide links, #106 denied pages, #107 only definite dead links count, #110, #117 Kentucky).
- Kentucky run 39 (`US-KY`, chain 0) was started at 2:35 PM CT and was still running at last look.

### pile-solver, 108 files (mostly trash)
- Built Nov 4 by `links-a3ba18c`. 1,381 parks: 52 SOLVED-JOIN (YES), 1,309 NOT SURE, 20 blank.
- 677 of the NOT SUREs say the key builder wrote no record id (an old bug). 374 say no layer is known for the record.
- Worth keeping: the 52 solved joins as a review list for the key, not as data to publish. The rest should be re-run on the current key.
- 16 files have no check result at all. Held: US-VT (US-5538, pin 1,920 m out).

### truth, 47 files
- 41 PASS: 22 states never live (7,055 parks); the rest refresh live files and add 159 parks. These are the best candidates for the next release.
- HOLD (MA, MD, MN, OK, UT, WA): over half the sizes read as "off", or several parks share one size (a statewide banner). The merged #104 fix addresses this; re-run these states, then re-check.

### trails, 28 files
- 24 PASS are single trail lines (10 new, 18 refresh live).
- HOLD: US-13626.json, US-9203.json, index.json, state-report.json. The held index has 101 lines against 139 live; US-9203 shrank from 19,246 to 1,822 points; US-13626 grew from 16 km to 114 km; the state report has a line with no points. Merged #234 now keeps official or finer lines; re-run the state trails bot before judging again.

### camp info, 21 files
- Left because of a catch found on 17 Nov:
  - IL: one office phone (217) 782-6302 is on 187 of 252 camps.
  - NY: 63 camps carry an annual pass price (about $80, "all-season enjoyment") as their camp fee.
  - AK: one office phone is on 103 of 368 camps, and one camp loses a site count.
  - CO, SC, ID, KY, CT, MT, NV, WI: the held copy loses facts the live file has (CO loses showers and restrooms on 102 camps; SC loses state park facts; ID loses 3 phones; KY loses 6 cabin counts).
  - DC, KS, LA, NJ, OH: names and points only, no camp-specific fact.
  - HOLD: AR, MA, MS, NC, VT (copied site counts, or a toll-free reservation line used as a camp phone).
- 4,783 federal camps are bare because the `RIDB_API_KEY` secret is missing in KPC-Data. Adding it is a setting only the owner can change.

### camp state, 4 files
- FL, UT, VA, AK. Each swaps its live source for another and drops real camps: FL 149 state park campsites, UT 13 DWR cabins, VA 32 state park points, AK 22 cabins. They are new sources, not errors, so the owner or an agent should decide whether to merge old and new points.

### WWFF, 1 file
- CTFF Portugal: 702 live rows, 280 held. The missing rows are mostly notable trees and the bot keeps only active rows, so this is probably a real WWFF deactivation. Keep it out until a fresh directory download settles it.

### hours, 1 file
- Kentucky hours (193 parks) holds exactly the same facts as live; releasing it adds nothing.

## 5. Where the released data shows up
- Camp state points: `data/campstate/US-XX.json`, read by `kpc-maprep-extras.js` on the map pages (the camp layer).
- WWFF lists: `data/wwff/<PREFIX>.json`, read by `kpc-park-info.js` and `kpc-park-notes-us.js`.
- Camp info, hours and truth: stored data read by the bots (workshop, scoreboard); I found no site page that shows them yet.

## 6. What was released today
- Approved by PR #120: 61 files (26 camp state, 5 WWFF, 30 camp info). Actually moved: the 5 WWFF files. The 176 old key and 2-fer copies were dropped earlier at the owner's word (4:21 PM).
