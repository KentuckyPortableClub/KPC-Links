# KPC repairs checklist

Kept by the club's reviewer (Fable). Version of 19 Nov 2026, 9:55 PM CST.
Sources: everything agreed today, main `4537910`, key-quality items 44 to 47, the outside review's update of 9:25 PM, and hand-off revision 3.2.
Save it in KPC-Links at `.claude/inbox/REPAIRS.md`. This is the ONE list. Every map chat reads it first.

## How it is kept

- A line is ticked only with proof beside it: a link, a run number, or a number that changed. "Built", "pushed" or "started" is not done.
- A chat changes only its own lines.
- The list is closed. A new problem goes under "Found later" at the bottom. It does not become a new job.
- If a list, a count or a test report already exists, read it. Do not make it again.
- One round per document: the reviewer gathers every note on a draft and sends one list.

## The owner's stop (19 Nov, 5:53 PM), his words

> "No building maps till all the oatches are done...we writing patch after patch and we still have a mess fix the problems get the info we need and then try one last time before I give up"

No key rebuild, no outline rebuild, no Release, no 2-fer run. Until he lifts it, a "who changes" list is predicted from the saved files and says so.

## The owner on usage (19 Nov, 9:01 PM)

Usage has to last the week. No second agent pass on a file another agent already did. No test run twice.

---

## Opus

- [x] **O1. Both daily key starts off.** **DONE: KPC-Links ad948efa, 6:06 PM. The nightly boundary rebuild is off with them.**
- [x] **O2. Notes saved.** **DONE: items 44 and 45 (5099f686); this file is `.claude/inbox/REPAIRS.md` (first saved 9b26bf28; this 9:55 PM version saved with key-quality items 49 to 51, 19 Nov ~10:30 PM).**
- [ ] **O3. Information bot.** **The 05 stack is in and the reading faults are fixed (KPC-Data 4816f03f).**
  - Kentucky run 44656781088: confirm it finished. Nothing more is spent on Kentucky. **CONFIRMED: finished green, asked 193, read 193, 0 skipped.**
  - The real test: **Montana**, one run, scored against the parks already settled by hand. **Nevada** next if Montana reads well. (Owner, 8:58 PM: "real world test a state we are horrible at".)
  - Done when: Montana's score is here. **STARTED, NOT READ: Montana run KPC-Data 44667523484 (19 Nov 9:36 PM).**
- [x] **O4. Gold and kit answers off the public branch** (S1). **DONE: KPC-Store 9e29899 (item 46). Squashing `tools-out` is still to do.**
- [x] **O5. The sample kit, from today's saved key.** **DONE: zips given to Brandon (item 46): 300 random + 8 planted, and the 1,193 busiest.**
- [x] **O6. Kit C packet.** **DONE: given to Brandon (item 46). See G2: it may not be used.**
- [x] **O7. Quiet the run** (S2, workflow parts). **Draft #294 read by Fable: not yet, two small changes (`REVIEW-294-and-300.md`, 1 and 2). ROUND 2 PUSHED (3ac74511): 1, 2 and 3 done. DONE: Fable passed it 9:48 PM; MERGED to main 61541c95 (no hash moves, builds nothing).**
- [x] **O8. Layers** (S3). **Draft #300 read by Fable: not yet, one fix (4), then the report run again. The three baselines are accepted. ROUND 2 PUSHED (d4f4a39c): 4, the rulings of 5 and 6 done; report again on tools-out 42c8b4dc. DONE: Fable passed it 9:48 PM; with the hand / hand-held mark (432515eb) MERGED to main 956d3ee5. Report round 3 on tools-out 32ed1893: of 167 hand-download layers, 140 are already in the saved copy (rows never closed) and 27 are real = 2 downloads (`real-hand-downloads.csv`).** Its report is the first column of the per-state board: one file, kept by the bot.
- [ ] **O9. The wider drop list, report only** (S5). Needs #298. The outside agent's list `S4-acres-released-vs-working.csv` already has the numbers: start from it.
- [ ] **O10. The test gate on Python 3.12 and 3.13,** where the packages are installed, for job A's third round and for #295 to #299. The agent's own reports are in its zip (`test-gate-reports/`): read them first. Done when: the verdict lines are here.

## Outside agent, job A: the 2-fer pull requests

- [ ] **A1. #289.** **Round 2 read: not yet. Round 3 from `REVIEW-hand-off-06-ROUND-2.md` (A to E).**
- [ ] **A2. #290.** **Round 2 read: passes as written. Moves with the stack.**
- [ ] **A3. #292.** **Round 2 read: passes as written. C and D only.**

## Outside agent, job B: five key drafts

All five are open as drafts, switched off, with green automatic checks. None is read by the reviewer yet. Lists: `KPC-draft-lists-19-Nov.zip`.

- [ ] **K1. #295, hold a state on an error.** US rules `c64b8ace0411 -> a34f224459cc`. One of the four places is changed; the pull request says why the other three are not.
- [ ] **K2. #296, the holder table.** `-> ac55685ff9c0`. **As agreed it moves no row:** the winner test needs full names and the records use short ones ("Cheatham WMA"). Waits for F5.
- [ ] **K3. #297, saved answers say what happened.** `-> 530776fd7b7e`. Uses a build notice and counts, not check rows.
- [ ] **K4. #298, acres measured from the outline.** No rule file.
- [ ] **K5. #299, a stricter "verified".** Sits on #298. Predicted: 8,125 verified parks become 428 until a size table exists.

## Graders and fresh agent sessions

- [ ] **G1. The sample: ONE blind pass** (owner, 9:01 PM). **PASS 1 BACK AND SCORED (KPC-Store 0fbe709): plants 6 of 8; 15 of 300 = 5.0% (3.1 to 8.1%) hold a named record that is not the park. LEFT: the second look at the rows this pass calls wrong.** The eight planted parks show how good the grader was. A second look only at the parks that pass calls wrong. Report the rate for each fact-check class too. Done when: the error rate with its range is here.
- [ ] **G2. Kit C: no second pass** (owner, 9:01 PM). A second look only where a size and the outline disagree.
- [ ] **G3. Plain cases fixed with a saved "no" and its evidence:** NV US-2635 against `fsod68`, and the 8 rows named in #296. The 12 disagreements in #296 go the same way. Nevada does not go public before US-2635 is done.

## Fable (the reviewer)

- [ ] **F1. Read job A's third round.** **Round 2 done.**
- [ ] **F2. Read the five key drafts, in this order:** #295 and #298, then #299, #297, #296. One sitting, with the lists.
- [ ] **F3. The public-against-working table** (item 43 step e). Start from `S4-acres-released-vs-working.csv`: 219 parks fall to 0.8 or less, 749 rise to 1.5 times or more, none judged. The 25 busiest of each state first.
- [ ] **F4. After the sample:** rule sheets for names that collide, the size test, and switching the piece rule and D5 on.
- [ ] **F5. After the sample: may the winner test in #296 read short forms** (WMA, SP, SF, NWR, SFL)? Without it #296 does nothing.

## N1 to N6: owners named (Fable, 19 Nov 10:20 PM; hand-offs given to Brandon)

- **N1, N2, N3 = job C:** the outside agent that wrote #295 to #299. Draft pull requests in KPC-Links, refuse only, no rebuild, no rules hash moved.
- **N4, N5:** Opus (they need the private store). N5 first.
- **N6:** the chat that did the two-day size check on KPC-Data. Steps 1 and 2 now; the history restart stays held.
- **Rule for every draft from now on (Fable, after the owner found the unused size check):** the pull request says which code-map tools it looked at and why they were not enough.

- [ ] **N1. The Release guard's blind spots, with three test cases** (Grok F1).
- [ ] **N2. The daily "public map is this far behind the key" line** (Grok F3).
- [ ] **N3. Three release checks:** an outline sits only in the file of a state whose key lists the park; none is `via: name+pin` unless named; US-2635 held or fixed.
- [x] **N4. Push check:** `installed` not true means "no list"; two more tests (store repo). **DONE as a draft (Opus, 19 Nov ~10:55 PM): KPC-Store #25. Both holes shown by tests first (5 failed before), fixed: 54/54 + 166/166. Also closed: a neighbour's held park outside a pair row now fails. Waits for Fable's read (diff + test output handed back).** **READ BY FABLE 19 Nov 10:40 PM (the diff and Opus's test output; nothing rerun): PASSES, with ONE change before the merge, no second read needed: the new border scan must fail closed. Today, if the file does not read as a dict, or the scan raises ValueError, the new scan is skipped without a word (`doc = None`, `lk = {}`); both must add a refusal instead, with one test.** **CHANGE MADE AND MERGED (Opus, 19 Nov ~11:05 PM): the border check now REFUSES a spot file it cannot read as a JSON object or cannot scan (two new tests, 56/56; 166/166); KPC-Store #25 merged to main ba250648. Fable's three notes stand for later (a third park inside a pair row; an old public row may be refused on the first real push; lists written before `installed` existed are refused).**
- [x] **N5. Two shown 2-fer rows that involve a held park:** check against the private list. Never named in a public file. **CHECKED, 0 SHOWN, NO EDIT (Opus, 19 Nov ~10:45 PM): both held parks are PIN in the released and working key, so the site already hides both rows; neither is withheld for privacy, and no private withheld list exists in KPC-Store (the store 2-fer job never ran).**
- [x] **N6. KPC-Data housekeeping:** save `layers.json.gz` and the scoreboard only on change; the cleanup, keeping `tools-out`, `intake-files`, `lookup`, `picture-maps` and every branch with an open pull request. **DONE 19 Nov 10:40 PM.** Step 1: KPC-Data pull request #132 (a .gz file and the scoreboard are saved only when the inside changed; `layers.json.gz` not re-saved in the 23 bot saves after it; the scoreboard half has not had its nightly run yet). Step 2: 33 merged branches deleted in KPC-Data (26 + 7) and 55 in KPC-Links, by the one-time clean-up bot (#133, #134; Links #293); keep-list untouched. Left for the history restart, on Brandon's word: 7 unmerged branches (`probe-relay` 763 MB, `prep/nov13-unblock-blm-fs`, `prep/nov8-trail-distance`, `tracer-draft`, `trace-test`, `trial-outside-ky`, `replay-files`), `data/waiting/previous` (kept: undo copies), and the `tools-out` squash (S1). Size: 1.43 GB on 17 Nov, 1.51 GB now; it does not drop until the restart.

N1 to N3 must be done before any Release.

## Brandon

- [ ] **B1. Job A agent:** send `REVIEW-hand-off-06-ROUND-2.md` and `review-06-round2-probe.zip`.
- [x] **B2. Name who takes N1 to N6.** **DONE by Fable, 19 Nov 10:20 PM (owners above). Brandon: send each hand-off to its one owner.**
- [ ] **B3. One question when ready:** the measuring step still joins pieces of one pair within about 100 m into one spot. Leave it, or fix it before the first fresh 2-fer run?
- [ ] **B4. The sample:** give the pass 1 zip to ONE fresh agent session. The pass 2 zip and the Kit C zip stay unused unless you say otherwise.
- [x] **B5. Opus has the hand-off file.** **DONE: #294 and #300 are built from it.**
- [x] **B7. Opus:** send `REVIEW-294-and-300.md`. **DONE: received 9:20 PM and in `TO-OPUS-round6.zip`.**
- [ ] **B6. Your call: let chats install packages** (a network setting). Tonight no chat could run the full gate on Python 3.12 or build from saved shapes, so lists were predicted and tests were run more than once. The outside review calls it the cheapest saving it can point to.

## Held on purpose. Not dropped.

- New matching rules (names, size test, switches on): after the sample.
- 2-fers batch 2, and the finer second look (part 4): after job A passes.
- KPC-Data history restart: after this list is closed, before the one build.
- The rest of the per-state board, the split of the 2-fer bot, the licence question, the 30-minute bots.
- Hand downloads: after O8 names what is missing. **NAMED (19 Nov 10:05 PM): 2 downloads, given to Brandon: the Army Corps recreation areas layer (22 states) and the NPS tract layer (5 states).**
- Pulling the passes out of the key builder's one long function, and a "draft mode" for the test gate.
- **Next week (owner, 8:23 PM):** hide every country but the US and Canada on the map tools. Keep all the other countries' data.
- **After Montana is read (owner's idea, 8:21 PM):** parks whose POTA link is only an agency front page, and parks with directions but no map point, go as rows to the searching bot, which looks for the park's own page and feeds it back to the reader. First count how many parks that is.

## The finish

- [ ] **Z1. One build.** Every switch Fable passes goes on together. The parks changed must be exactly the lists.
- [ ] **Z2. Fact check and a sample** on that key.
- [ ] **Z3. Release by numbers,** state by state. Brandon presses the button.

## Found later

From Fable's gate runs (9 PM):
- Main's own test gate is red: 18 tests fail on main `4537910` on Python 3.13, and `tests/known-fail-main.txt` is from 7 Nov. One of main's tests rewrites `data/status/kpc_key_drop_guard.json`.

From the outside review's update (9:25 PM), all predicted from saved files:
- A saved "no" does not follow a record whose id was renumbered. After a layer refresh the record can join again. Case: AR US-1080.
- 15 parks hold one record under both join and no (list: `S6b-297-join-and-no.csv`).
- 472 bare-name saved joins; 32 match no joined row today.
- A check row can take joined land off a park on the next build (`kpc_join_check.py:232`). The drafts use notices for that reason.
- 70 records are held by a person's answer in one park and by name in another with no winner; 12 disagree with the saved answer.
- The 2-fer list is public: every row is in the public KPC-Data repo.
- `tests/test_us_key_reads_nov10r.py` fails on main (seen by the outside agent and in Fable's gate run).

From Opus (19 Nov, 9:20-10:30 PM):
- The ready check (O8) counts 73 Kentucky parks whose POTA link is only an agency front page (AGENCY_HOME_ONLY in run 44656781088): the count the owner's 8:21 PM idea asks for first. (Opus, 19 Nov 9:10 PM.)
- **The acreage bot already exists and is not used** (owner, 19 Nov 9:16 PM). KPC-Data `draft/tools/kpc_acres` (run through `kpc-tool-trial.yml`, tools=acres), last run 15 Nov: 1,668 parks with an official size on tools-out `acres/acres.json`. 52 agency lists were skipped only because `pypdf` is commented out in its requirements.txt (30 FWS, 13 BLM, 9 others) and 28 were blocked by robots.txt. Measuring acres from an outline also exists already (packet bot `acres_of`, truth bot `poly_acres`). K4 (S4) and O9 (S5) use these; nothing new is written. (Opus, 19 Nov 9:20 PM.) **FIXED + RUNNING (owner 9:19 PM: "Fix it and use the bots"):** pypdf on and the 52 PDF-skipped lists read again on resume (KPC-Data 9db5ae17); acreage run 44667049409 started 9:25 PM, results on tools-out `acres/`. **Kit C (G2, agency size tables) overlaps this bot:** read the run before a fresh agent does Kit C by hand.
- **Acreage bot, second fix:** run 44667049409 gave 1,675 parks with an official size (1,668 on 15 Nov); 42 PDF lists (30 FWS, 12 BLM) were refused on a column name: fixed (KPC-Data 5aba489d), run 44668442339 reads them again. Lines with several numbers stay skipped until a list says which column.
- **Sample:** one clean planted gold row was called BIGGER for a second forest's record: the gold row may be wrong (private file, KPC-Store).
- **For later (Fable, 9:48 PM):** with the baselines now equal to the saved copies, the first re-read of a layer that comes back even one record smaller holds its state until somebody approves the new count. That is the gate working; expect it when layer refreshes start again.
- **Why the bots did not fetch the 2 "hand downloads" (owner 9:57 PM: "Why didnt keeper or our bots download it?"):** services*.arcgis.com's own robots.txt says no to every robot, so the key's bots may not ask. BUT the keeper (KPC-Store) has both layers on its allow list (`engine/verified-layers.csv`, fetch yes) and its store already mentions the Corps layer in 13 state files and the NPS tract layer in 12. **The key builder never reads the keeper's store:** it reads only boundary-cache copies plus hand files. Two systems keep the same layers apart; that is why rows sit open and people are asked for files the club already has. For Fable: one fix (the key's master step takes a layer the keeper already holds), not a new tool. The owner's Corps download (19 Nov 9:59 PM) held 22 areas of 2 Kentucky lakes only (the download took what was on screen), so it is not the whole layer; his NPS tract file (108 MB) came whole. (Opus, 19 Nov 10:05 PM.)
- **ArcGIS robots.txt, read live (owner 10:05 PM: "Check arcgis robot.txt?"; Opus, built-in browser, 19 Nov ~10:10 PM CST):** `https://services1.arcgis.com/robots.txt` and `https://services7.arcgis.com/robots.txt` both answer **HTTP 403 "Invalid URL": there is no robots.txt, and no "Disallow"**. By the standard (RFC 9309) and the keeper's own reading (owner decision 8), a 4xx means "no rules": allowed. The earlier note that ArcGIS says "User-agent: * / Disallow: /" to every agent (outside agent, 19 Nov) does not hold today. So the key bots' ban on services*.arcgis.com is **our own rule** (`kpc_net_guard.py` SERVICES_RE, `kpc_master.py` live_ok), not ArcGIS's. Rule sheet R-NET1 (key-quality item 19: drop the hard-coded bans, robots.txt the only test) waits for Fable; by its own text it merges only after the release sign-off. Owner's call whether that order still stands.
- **CORRECTION (Opus, 19 Nov 10:20 PM, from the owner's code map v5, KPC-Store `docs/code-map/`):** the ArcGIS question is not open. **The owner ruled on 15 Nov:** arcgis.com and Forest Service sites are allowed (slow, one at a time), robots.txt always obeyed; the map then said the guard files were "not yet brought in line (on the owner's list)". They never were, which is why the key bots still refuse ArcGIS and asked for two hand downloads tonight. Also from the map: "Keeper refreshes the public saved copies" is **Planned**, never built (the keys read only boundary-cache). Both are unfinished owner decisions of 15 Nov, not new questions. CLAUDE.md now points every chat to the code map and states the 15 Nov host ruling.
- **Size checks already in the repo and not used (owner, 10:01 PM: "pretty sure we had one them all ready probably never got used"; Fable read the code and the 15 Nov code map):** `KPC_SELF_CHECKS` (2 Nov, joined acres against official acres, 0.2x to 5x) is OFF for every state in `.github/key-switches.json`; `kpc_join_check.py` (6 Nov, acreage + distance) runs after each key build and a failure is only a warning; `kpc_pin_edge.py` measures acres from an outline; `kpc_source_fields.py` holds the official-acres field per source; `kpc_key_trend.py` counts acres that disagree, report only. F2 reads #298 and #299 against these first.
- **ROOT CAUSE of the ArcGIS mess (owner 10:21 PM: "one central bot rules for polite"; counted by Opus 19 Nov 10:25 PM):** there is no one rule book. Host and politeness rules live in at least 6 places: KPC-Links `kpc_net_guard.py` + `kpc_master.py`; KPC-Data `kpc_host_rules.py` + `kpc_manners.py`; KPC-Store `engine/kpc_outline_store.py` + `engine/packs-fixed/_shared/host-policy.json`; and 91 bot files read robots.txt themselves. The 15 Nov ruling reached the keeper only. **The fix, once:** ONE rules file (start from KPC-Store's `host-policy.json`, the most complete) that every bot in all three repos reads, and a test in each repo that fails when a bot carries its own host list. Not a new bot; it replaces copies.
- **FINISH, DON'T REBUILD: the saved-copy refresh (owner 10:23 PM: "this over and over and over"; CHECKED LIVE by Opus 10:32 PM, the first version of this line was wrong).** Built 17 Nov. **The keeper's half is ON and working** (KPC-Store `keeper/layer_requests.py`, job `layer-requests` in `kpc-store-keeper.yml`; the notes calling it "not applied" were stale): `layer-requests.json` on KPC-Links' boundary-cache release, written 19 Nov 11:35 AM CST, holds **144 requests in 43 areas (140 US, 4 Canada), all asked 18 Nov because the layer's count changed**. **Nobody has run the cache side** (KPC-Links #247: `kpc-geo-cache.yml` / `kpc-world-cache.yml`, by-hand button, `from_requests` box). What stops it: (1) the run re-reads saved copies, so it waits for the owner's word inside his stop; (2) the cache bot still obeys the leftover ArcGIS ban (the host-rules line above), so ArcGIS layers in those 144 would be skipped; (3) Fable's note: baselines now equal the copies, so a re-read that comes back smaller holds its state until approved. Order: the one rules file, then the owner's GO, then ONE `from_requests` run.
- **NEXT OPUS CHAT, FIRST JOB (owner 10:24 PM: "Finish it"): bring the key bots in line with the 15 Nov host ruling. Everything is found; just do it.** Ruling (code map v5): arcgis.com and apps.fs.usda.gov ALLOWED, slow, one at a time, no bulk paging; robots.txt always wins; Grant County NM rule deleted. Code: KPC-Links `.github/scripts/kpc_net_guard.py` (`SERVICES_RE` and `apps.fs.usda.gov` in `NEVER`, `host_rule()` ~line 92), `.github/scripts/kpc_master.py` (`is_arcgis_services_host` in `live_ok()` ~line 71, `NEVER_CONTACT`, `SAVED_ONLY_HOSTS`); KPC-Data `.github/scripts/kpc_host_rules.py` + `kpc_needs_download.py`. Keep ncnhde.natureserve.org as it is (not in the 15 Nov ruling). Pace: KPC-Store `engine/packs-fixed/_shared/host-policy.json` already says how (10 s on these hosts; a robots 401/403/404 = no rule stated, owner decision 8): copy its reading, do not invent a new one. Tests that assert the old ban (KPC-Links, 26 files): test_net_guard_nov10r, test_hostguard_pkg_a_nov11, test_master_step_nov10, test_master_needs_actually_missing_nov10, test_us_key_redirect_hops_nov10, test_map_data_rule_nov11, test_master_outlines_nov10, test_us_key_pace_checked_nov10, test_us_short_copy_refill_nov10, test_world_layer_fall_back_nov11 and 16 more (grep 'arcgis' in tests/). Flip each to the ruling; add one test that fails if a hard-coded host ban comes back without a dated robots reading. One draft PR per repo, Fable reads, merged OFF-effect (it only matters at the next read). Then the owner's GO for ONE `from_requests` cache run (144 requests waiting).
- **From Fable's read of KPC-Store #25 (19 Nov 10:40 PM), not blockers:** (1) a pair row is cleared whole, so a third park named in a note or a names field INSIDE a pair row is not checked against the neighbours' lists; tighter = clear only the refs listed in that row. (2) The new border scan does not use the carried-row rule (2b), so the first real 2-fer push may be refused for an old, already-public one-park row; that is the guard being strict, decide then. (3) A list written before the `installed` field existed now counts as no list (refused): right, but expect it on lists older than the field.
