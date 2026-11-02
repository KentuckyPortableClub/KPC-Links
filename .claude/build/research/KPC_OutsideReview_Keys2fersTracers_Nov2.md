KPC Keys, 2-fers and Tracers: Findings and Fixes (Nov 2, 2026)
A read-only review of the bots that build the answer keys, the 2-fer map and the tracers. What is stuck, why, and what to fix first. All times are Louisville time (EST).
On this page
1. The short version
2. What is stuck right now
3. Key builder problems
4. 2-fer bot problems
5. How to speed things up
6. Picture-map and parcel tracers
7. What to do, in order
8. Patch files (not pushed)
9. What I did not read
10. What was built (v0.5.0)
11. Storage issues and fixes
1. The short version
The biggest single cause
BOT A reads chat 11's YES and NO answers at every US key build, but its save step has never worked. The answers vanish after each run, so pins chat 11 already ruled on keep coming back. The error is hidden by || true.
The US key has not gone live since Oct 30. Each build is blocked by just 1 to 10 parks, because one bad park blocks the whole file.
BOT A's answers file has only ever had one save (Oct 29, 11:15 PM). Every run since has thrown its work away.
Builds read an old copy of the repo. The build step checks out the commit the run started on, so it misses BOT A's own changes from earlier in the same run.
Release is all-or-nothing per folder. There is no way to let 240 good parks go live and hold back 5 bad ones.
Chat 11 has already said YES to the Canada key (Nov 1) and the world key (Nov 1), but both approvals are skipped every run because a field is missing.
The 2-fer ids change on every rebuild, so reviews reset and counts swing. Alaska's held 2-fer file is just under GitHub's 100 MiB limit.
The picture tracer drew only 3 of 172 maps. Most fail a chance test because the matcher is close to guessing.
2. What is stuck right now
Flow board (KPC-Data data/status/flow.md, made Nov 1, 8:02 PM). Three piles are STUCK (no movement for 2+ days). All wait on "chat 2 (fix) + chat 11".

| Pile                                                                                | Count            | State               |
| ----------------------------------------------------------------------------------- | ---------------- | ------------------- |
| Held campinfo files (MA, NC, NY)                                                    | 3                | STUCK since Oct 31  |
| Held docs files                                                                     | 49               | STUCK since Oct 31  |
| Held trails files (index, US-11393, US-11905, US-9905, US-9906, finds-lines-report) | 6                | STUCK since Oct 31  |
| Held fers / truth / world-key / wwff                                                | 23 / 9 / 4 / 8   | Waiting since Nov 1 |
| Chat 11: hardlook questions / layer questions / files for a grader                  | 1,489 / 89 / 323 | Waiting             |
| Chat 9 questions                                                                    | 146              | Waiting             |
| Chat 10: RED bots (2-fer checker, storage keeper, T5 site checker)                  | 3                | Broken              |
| Intake bot: layers not checked                                                      | 300              | Waiting             |

From the first pass this morning (read about 5:25 AM).
Inboxes.

| Inbox                                      | Open                       | Done | Notes                                                                                         |
| ------------------------------------------ | -------------------------- | ---: | --------------------------------------------------------------------------------------------- |
| Chat 2 (KPC-Links .claude/inbox/chat-2.md) | 107, plus 14 notices above |  103 | About 33 open items say done or wired but were never moved. 84 of the 107 are from Oct 29-30. |
| Chat 11 (.claude/inbox/chat-11.md)         | 189 list lines under OPEN  |   41 | Plus 20 lines above OPEN. My count of list lines, not of separate topics.                     |

Held files in KPC-Data data/waiting/in/: 296 files (297 with the .keep placeholder). The waiting room's own morning list later showed 232, after an automatic release of 174 trusted campinfo, trails and truth files.

| Kind          |            Held files |
| ------------- | --------------------: |
| world-key     |                    70 |
| us-key        |                    59 |
| trails        |                    54 |
| docs          |                    49 |
| fers (2-fers) |                    42 |
| truth         |                     9 |
| wwff          |                     8 |
| campinfo      |                     3 |
| ca-key        | 1 (only why-not.json) |
| hours         |                     1 |

Chat 11's US key verdicts (from data/waiting/approved.json). Build times converted from UTC.

| Date   | Build                          | Verdict and score | Parks that blocked it                                                                                                                                                     |
| ------ | ------------------------------ | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Oct 30 | Morning build                  | YES, 30/30        | None (last time the US key went live)                                                                                                                                     |
| Oct 30 | Indiana build                  | NO, 6/6 sample    | 6 Indiana lake SRAs joined to lake records (US-5682, 5684, 5685, 5686, 5688, 7842)                                                                                        |
| Oct 31 | Indiana build, 10:47 PM Oct 30 | YES, 6/6          | None, but voided by the next rebuild                                                                                                                                      |
| Oct 31 | 6:13 AM                        | NO, 29/30         | 1: Milford State Fish Hatchery US-7393                                                                                                                                    |
| Nov 1  | 4:11 AM                        | NO, 29/30         | 1: Milford hatchery again                                                                                                                                                 |
| Nov 1  | 6:14 AM (+218)                 | NO, 20/30 (67%)   | 10 'same name, far from the pin' joins (Walnut Creek, Smith River, Twin Buttes, Clear Creek, Long Lake, Pine Island, Mt. St. Helens, Salt Creek, Fortymile, Julian Price) |
| Nov 1  | 3:28 PM (+244)                 | NO, 25/30 (83%)   | 5: Julian Price, Fortymile, Oxford Slough, Iao Valley, Teanaway                                                                                                           |
| Nov 2  | Logged as 3:16 AM (+244)       | NO, 77%           | 7: Fortymile, Owens Spring/Walker/Adams, Rail Trail, Oxford Slough, Teanaway, Julian Price, Capitol SP                                                                    |

Chat 2 later found the Nov 2 sample was really the old Nov 1, 1:38 PM build, because GitHub skipped the scheduled run. Fortymile, Oxford Slough, Teanaway and Julian Price came back after chat 11 had already ruled them out. That is BOT A's save failing.
2-fer reviewed list
kpc-fers-reviewed.json in KPC-Links is still empty. It has had one commit, Oct 27.
Old overlap file
ky-overlaps.geojson in KPC-Links (320,697 bytes) was last changed Oct 13, 10:16 PM EDT.
3. Key builder problems

| #   | Where                                                                  | What goes wrong                                                                                                                                                                                                                                       | Fix                                                                                                        |
| --- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| A   | kpc-us-key.yml line 50 (BOT A save)                                    | git pull --rebase fails with "You have unstaged changes" and \|\| true hides it. On the Nov 1 nightly run, BOT A applied 46 yes, 89 no and 21 name variants on 103 US parks, plus 163/111 Canada and 1,029/2,152 world answers. None of it was saved. | Commit first, then pull and push in a retry loop. Fail the run loudly if it still can't save. Patch ready. |
| B   | kpc-us-key.yml build checkout (~line 87) and join checkout (~line 120) | actions/checkout with no ref uses the commit the run started on, so it misses BOT A's push from earlier in the run.                                                                                                                                   | Add ref: main. Patch ready.                                                                                |
| C   | kpc_key_answers.py line 129                                            | A YES can't clear a NO when that NO is the only one. The code puts the old list back when the filtered list is empty.                                                                                                                                 | Drop the or v.get('no', []) fallback. Patch ready.                                                         |
| D   | kpc_us_key.py lines 1001-1071                                          | Only the main join (line 980) checks NOs by id and by name. The alias_all, RIDB, alias and NAME_JOIN paths skip NOs or check ids only, so a ruled-out record sneaks back by another door.                                                             | One shared NO check (ids + names) called by every join path.                                               |
| E   | kpc_key_answers.py lines 136-142                                       | NOs are stored by record id only. When an agency re-issues ids, the NO stops matching.                                                                                                                                                                | Also store a fingerprint: [name, acres].                                                                   |
| F   | kpc_us_key.py lines 981-996 (id join)                                  | Joins on id plus distance only, with no name check. The name fallback runs only when the id is missing.                                                                                                                                               | Require a name or size match too.                                                                          |
| G   | kpc_us_key.py lines 1429-1458 (keep-last-good)                         | Compares names raw, and the 'refound' path (1446-1452) has no distance check.                                                                                                                                                                         | Normalize names. Add the same distance check as the main join.                                             |

KPC-Links, US key workflow and builder.
Other known bugs found on the way:
The Nov 1 monthly run (started 6:00 AM) failed its save after 6 tries with rebase conflicts. About 1 hour of runner time was lost across 3 jobs.
There was no Nov 2 scheduled run, and scheduled runs start about 40 minutes late. The Alaska file was last built Nov 1, 1:38 PM, before the Fortymile NO was added at 3:30 PM.
Canada nightly (4:49 AM) only builds when answers-provinces.txt has something in it. That never happens because BOT A never saves. It also runs before the late US job.
The waiting room's key rule ^data/(?:us|ca)-key/[^/]+\.json$ also grabs non-key files (why-not.json, overrides, zips, index). Narrow it to (US|CA)-[A-Z]+\.json.
Canada's Nov 1 KEY YES has no chat2 field. The world key's Nov 1 YES has no path field. Both are skipped silently.
Checker crash: 'list' object has no attribute 'get' held trails/index.json (Oct 31) and 8 wwff files (Nov 1). Status and trails got guards on Nov 2, so these should clear on the next check. Still unguarded: c_key (line 422), c_intake (470), c_fers (481), c_pota (571), closures_filter (592).
4. 2-fer bot problems

| Problem                                     | Cause                                                                                                                                                                                                                                       | Fix                                                                                                                                                                                           |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ids change every rebuild, so reviews reset  | The id is the refs plus kind plus the area's center to 3 decimals (lines 2287, 2856, 3009, 3038). The center comes from a raster whose frame depends on the box and tiles (lines 1418, 1425, 1440), so any outline or grid change moves it. | Carry the old id forward when the same refs and kind overlap or sit within 1 km. New ids use refs + kind + center rounded to 0.01 degree, the same as the waiting room's spot_key (line 544). |
| Every code edit throws away the reuse cache | CODE_HASH (line 1655) is a hash of three whole files. There were 39 commits to kpc_fers.py from Oct 29 to Nov 1.                                                                                                                            | Use a hand-bumped FERS_ALGO version number instead.                                                                                                                                           |
| Counts swing, so files get held             | New rules since the live files were written (Oct 29) add rows: edge neighbours from other states, rows filed under the outlined park's state, 3 m trails, river and water routes. The checker counts rows across all kinds (lines 483-485). | Check per kind, on pairs. Label each new pair: new outline, line park, cross-state neighbour, or unexplained.                                                                                 |
| Alaska file size                            | Held US-AK.json.gz is 103,491,694 bytes. GitHub's limit is 104,857,600.                                                                                                                                                                     | Split Alaska by region, or store geometry separately, before it tips over.                                                                                                                    |

KPC-Links `kpc_fers.py`.
Count swings in held files (old to new candidates):

| State | Old | New |
| ----- | --: | --: |
| WA    |  40 | 190 |
| PA    |  45 | 152 |
| CA    |  66 | 133 |
| NC    |  80 | 126 |
| MI    |  82 | 108 |
| FL    | 145 | 192 |
| AR    |  12 |  70 |
| NE    |  15 |  45 |
| TX    |  12 |  41 |
| MT    |  23 |  41 |
| SC    |  26 |  17 |

Line parks show up again and again in the new pairs (US-4556, US-4239, US-4562/4566/4576, US-8313). The 2-fer line runs take up to 2.5 hours per area, and they measure against the live key, so they run on an unsettled key.
5. How to speed things up

| Rank | Change                                                                        | Expected gain                                                  |
| ---- | ----------------------------------------------------------------------------- | -------------------------------------------------------------- |
| 1    | Fix BOT A's save and add ref: main                                            | Stops ruled pins coming back. Fewer rebuild-and-recheck loops. |
| 2    | FERS_ALGO version instead of CODE_HASH                                        | About 60-80% less time on 2-fer reruns                         |
| 3    | Rebuild only changed states (layer edit date + overrides hash + code version) | Nightly from all states down to about 5-15                     |
| 4    | Overwrite-save for generated files; keep the monthly run off nightly days     | About 1 hour a month, no red runs                              |
| 5    | Start builds from KPC-Data events; run Canada after the US plan job           | Removes the ~40 minute lag and skipped runs                    |
| 6    | 5-6 parallel groups instead of 3                                              | About 40% less wall time                                       |
| 7    | Same output every time (sorted keys, rounded coordinates)                     | Fewer false holds                                              |

Ranked. Estimates are my estimates, not measured.
6. Picture-map and parcel tracers
3
Maps drawn
of 172 tried
122
No fit
109 'not better than chance'
47
No line
no boundary found
Picture tracer (KPC-Data .github/scripts/draft/kpc_trace_picture.py). The 3 drawn: CA-0962, US-5265, US-5566. By country: Canada 1 drawn, 79 no fit, 19 no line; US 2 drawn, 43 no fit, 28 no line. 90 maps passed every other test and failed only the chance test. Real scores were about 0.59 to 1.09 times the decoy scores (middle about 0.9), so the matcher is mostly fitting noise.

| Problem                                                                                                | Fix                                                            |
| ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| kpc_picture_prep.py sends no acres, so the scale guess is wide (0.2-25 m per pixel)                    | Pass acres from data/acres.json. Patch ready.                  |
| Prep writes image, but the tracer reads only map_file (line 1020), so it takes the first file it finds | Write map_file. Patch ready.                                   |
| Saved maps are page 1 at 2000 px, quality ~70. 43 boundaries touch the picture edge.                   | Save the actual map page at 4000 px, quality 85.               |
| Point matching is too weak to beat the decoy test                                                      | Score by edges (chamfer) and use road-junction angle patterns. |
| Some maps are GeoPDFs with built-in coordinates                                                        | Check for /LGIDict or /GPTS and use them directly.             |
| Canada gets roads only; the 300 nearest points bunch up in towns                                       | Add Canadian water and survey grids; spread the points out.    |

Parcel tracer (draft/tools/kpc_parcel_trace/kpc_parcel_trace.py).

| Problem                                                                                                                           | Fix                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Generic owners like 'STATE OF X' or 'natural resources + same state' count as a full match                                        | Allow weak owners only near the pin (about 1.5 x the square root of official acres), or require a division word. |
| It keeps adding neighbours and checks size only at the end (lines 908-926, 958-971). Likely cause of Salato 4x and Hiwassee 9.8x. | Grow best-first and stop at 1.25 x official acres.                                                               |
| Neighbour test is loose                                                                                                           | 30 m adjacency plus a minimum shared edge.                                                                       |
| Overlaps with other parks (line 822 checks only a 50% share)                                                                      | Cut out other parks' outlines; skip parcels holding another park's pin.                                          |
| Canada's DFRP has federal land only, so 5 provincial parks found nothing                                                          | Send only federal agencies to DFRP.                                                                              |

7. What to do, in order

| Action                                                                      | Who                                | Effort         | Impact                           | Patch?         |
| --------------------------------------------------------------------------- | ---------------------------------- | -------------- | -------------------------------- | -------------- |
| Fix BOT A save, ref: main, YES-clears-NO                                    | Chat 10, after a test build        | Small          | Very high                        | Yes            |
| Per-park release for keys (hold the N bad parks as pins, release the rest)  | Brandon OKs, chat 10 builds        | Medium         | Very high                        | No             |
| Add chat2 to Canada YES and path to world YES                               | Chat 2                             | 5 minutes      | High                             | No (data edit) |
| One shared NO check on every join path; NO fingerprints                     | Chat 10                            | Medium         | High                             | No             |
| Stable 2-fer ids; FERS_ALGO; per-kind gate                                  | Chat 10                            | Medium         | High                             | No             |
| Guard remaining checker list crashes; narrow key route                      | Chat 10                            | Small          | Medium                           | Partly         |
| Split Alaska 2-fer file                                                     | Chat 10                            | Small          | Medium (prevents a hard failure) | No             |
| Settle keys before 2-fers (run a state's 2-fers only after its key is live) | Brandon decides; chat 2 and chat 8 | Small          | High                             | No             |
| A second checker chat to share chat 11's load                               | Brandon / HQ                       | Small          | High                             | No             |
| One open-issues list where 'done' means live on the site                    | HQ                                 | Small          | Medium                           | No             |
| Batch rule changes weekly instead of daily                                  | Brandon / HQ                       | Small          | Medium                           | No             |
| Tracer fixes (acres, map file, better pages, scoring)                       | Chat 10                            | Small to large | Medium                           | Partly         |
| Move ~33 finished items in chat 2's inbox to DONE; fix the 3 RED bots       | Chat 2, chat 10                    | Small          | Medium                           | No             |

8. Patch files (not pushed)
Replaced by the v0.5.0 patches
The two first-pass patches below have been folded into the six v0.5.0 patches in section 10. Use those instead.
Not pushed, not run
These files are only on the bot's computer. They passed a dry-run apply and a syntax check. They need a test build before anyone uses them.

| File                                                    | What it changes                                                                                                                                                                                                                         |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| /workspace/kpc_review/KPC-Links-review-2026-11-02.patch | (a) kpc_key_answers.py line 129: a YES now clears a lone NO. (b) kpc-us-key.yml line 50: commit, then pull and push up to 5 tries; fail with a clear error if the save never lands. (c) ref: main on the build and join checkouts.      |
| /workspace/kpc_review/KPC-Data-review-2026-11-02.patch  | (a) kpc_waiting_room.py: a file that should be an object but isn't is marked 'unsure, wrong shape' instead of crashing (wwff, trails, status may be lists). (b) kpc_picture_prep.py: passes acres and the right map file to the tracer. |

9. What I did not read
Nothing was cloned, run or changed. All reading was through GitHub, read-only.
I did not find the script that turns PDF maps into the saved JPEGs.
I did not open every held 2-fer file, only the WA reason and the state counts above.
I did not run the tracers, so tracer fixes are from reading the code and the last report.
World key internals beyond the approval records.
10. What was built (v0.5.0)
Download
/workspace/kpc_engine_v0.5.0.zip (1.70 MB, 131 files). It includes the key doctor, the six bot patches with their original files, the storage plan and the tests. 155 tests pass: the 109 old ones, 13 for the key doctor and 33 for the patches. They also pass when run from a fresh unzip.
The key doctor. Run python3 kpc_engine.py doctor --links L --data D --out OUT. It only reads the two checkouts and writes only to OUT/key-doctor/. It refuses an output folder inside either checkout. It exits 1 when something is red: a missing NO, a NO that came back, or a file over 95 MiB.

| Task      | What it does                                                                                                                                                                      | Switch (default)                                 |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| nos       | Checks that chat 11's NOs landed in overrides.json. A missing one is re-applied to a copy (overrides.fixed.json). Also lists NO'd records that came back in a built key.          | key_doctor.reapply_nos (on, copy only)           |
| release   | For a LIVE-FILTERED key: which parks pass and which are held. Failing parks keep their live version.                                                                              | `key_doctor.per_park_release` (OFF, report only) |
| approvals | Flags YES approvals with missing fields: Canada key with no chat2, world key with no path.                                                                                        | require_chat2 / require_path                     |
| fers-ids  | Stable 2-fer ids (sorted refs + kind + centre to 0.01). Old ids carry forward within 1 km.                                                                                        | fer_carry_km (1.0)                               |
| line      | Each area in club order through build, check, grade, save, release, fers, review. Freezes and stamps the build while it is graded, and flags a change mid-grade. Done means live. | freeze_while_graded (on)                         |
| stuck     | A daily stuck list with owners (stuck-YYYY-MM-DD.md).                                                                                                                             | stuck_days (2)                                   |
| storage   | Size guard: WARN at 80 MiB, RED at 95 MiB. Also lists held copies that live already has.                                                                                          | size_guard (on)                                  |

Built on the bot's computer only. Nothing was pushed, committed, commented or opened in either club repo.
The bot fixes, as six patch files in kpc_engine/patches/ (also in /workspace/kpc_review/patches-v0.5.0/).

| Patch                                | Fixes                                                                                                                                                                                                                                                     |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| KPC-Links-01-save-by-overwrite.patch | BOT A's save. No more hidden \|\| true. It re-runs the writers on the newest main and pushes (save by overwrite), and goes red if it never lands. The Join save uses the same script and never overwrites the hand-edited overrides.json. Adds ref: main. |
| KPC-Links-02-key-answers.patch       | Line 129: a YES clears even a sole NO. A NO is stored with its name and acres. Failures are loud.                                                                                                                                                         |
| KPC-Links-03-key-rules.patch         | NO checks on every join path. NO by saved name, a name check on id joins, pre-handoff self-checks, and confidence sorting with one-line reasons.                                                                                                          |
| KPC-Links-04-fers-algo.patch         | FERS_ALGO as the reuse key option instead of CODE_HASH.                                                                                                                                                                                                   |
| KPC-Data-05-waiting-room.patch       | List guards in c_key, c_fers, c_intake, c_pota and closures_filter: a wrong shape is a plain-words HOLD, never a crash. Adds a key-file name switch and held-copy tidy.                                                                                   |
| KPC-Data-06-tracers.patch            | Tracer limits: acres passed in, the chosen image honoured, a tunable better-than-chance gate, ADJ_M, a 1.25x growth cap and subtracting other parks.                                                                                                      |

Every new rule has its own switch. Bug fixes default on. New behaviour defaults to today's practice. The full switch list is in patches/README.md.
Test on a test build first, never straight on main:
1.
On the bot's computer, run python3 -m pytest -q patches/patch_tests. It applies all six patches to the original files and runs the checks.
2.
In a scratch clone of each repo, run patch -p1 --dry-run for each patch. If a repo changed since Nov 2, fix any failing part by hand.
3.
Put the patched files on a test branch in a fork, or a test branch you create. Run the US key workflow by hand for one small state, and check that the log says saved (overwrite, try 1).
4.
Run the key doctor on that test build. nos.json must show 0 missing and 0 came back.
5.
Turn on one new switch at a time, as a repo variable on the test branch. Compare with the previous build before keeping it.
Needs Brandon's OK
Applying any patch to the club repos. Save by overwrite replacing the rebase save. Each new switch (NO by name, id-join name check, found-again near the pin, self-checks, confidence sort, FERS_ALGO reuse, loud failure exit, waiting-room tidy, key-file names only). The tracer numbers (ADJ_M 200 to 30, the 1.25x cap, subtracting other parks). Per-park release. The storage split (section 11).
Not done: the patches are not applied or pushed, because GitHub stays read-only.
Not done: the full key, 2-fer and tracer scripts were not run end to end. They need network, map libraries and the full club data. The tests cover the changed parts directly.
The parcel tracer's repo path (draft/tools/kpc_parcel_trace/) is assumed. If it is elsewhere, apply that file's part of patch 06 by hand.
11. Storage issues and fixes
Alaska is already over the red line
GitHub refuses any file over 100 MiB. US-AK.json.gz is 103.5 MB, which is about 98.7 MiB, or about 1.3 MB of room. About 1.3% more growth and the key save fails for the whole run.

| Fix                                                                                                                                                                                                                                                                                             | Status                                                                     |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Size guard in the key doctor: WARN at 80 MiB, RED at 95 MiB, for any file in either checkout. US-AK shows RED today.                                                                                                                                                                            | Built, on                                                                  |
| Plan to split big state files by region or 2-fer kind (recommended), or move them to Git LFS or a release asset. LFS files are not served by GitHub Pages, and release downloads usually can't be read by the page directly. Also slim the files first (round coordinates, drop unused fields). | Written, NOT applied: needs Brandon's OK (changes how the site reads them) |
| Automatic cleanup of held waiting-room copies once live has the newer build (WAITING_TIDY=1), plus optional old-generation cleanup (WAITING_KEEP_GENS). The doctor lists what it would remove.                                                                                                  | Built, OFF by default                                                      |
| Generated output only on a tools-out branch, with overwrite commits (no merges). Optional monthly squash of tools-out only, never main.                                                                                                                                                         | Advice, needs Brandon's OK                                                 |
| FERS_ALGO is in (fers-2026-11-02.1). With KPC_FERS_REUSE_KEY=algo, 2-fer results are reused until the algorithm changes, not on every script edit.                                                                                                                                              | Built, option (default stays CODE_HASH)                                    |

The full plan is in kpc_engine/patches/STORAGE_PLAN.md (copy at /workspace/kpc_review/STORAGE_PLAN.md).