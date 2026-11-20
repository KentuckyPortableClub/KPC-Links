# KPC repairs checklist

Made by the club's reviewer (Fable), 19 Nov 2026, 7:50 PM CST, from everything agreed today. Updated 9:05 PM from main `4537910` and key-quality items 44 to 47.
Save it in KPC-Links at `.claude/inbox/REPAIRS.md`. This is the ONE list. Every map chat reads it first.

## How it is kept

- A line is ticked only with proof beside it: a link, a run number, or a number that changed. "Built", "pushed" or "started" is not done.
- A chat changes only its own lines.
- The list is closed. A new problem goes under "Found later" at the bottom. It does not become a new job.
- If a list or a count already exists, read it. Do not rebuild it.

## The owner's stop (19 Nov, 5:53 PM), his words

> "No building maps till all the oatches are done...we writing patch after patch and we still have a mess fix the problems get the info we need and then try one last time before I give up"

No key rebuild, no outline rebuild, no Release, no 2-fer run. A small offline test build that only makes a "who changes" list is allowed.

---

## Opus

- [x] **O1. Both daily key starts off.** Done when: the key workflow has no schedule and no key run starts by itself. **DONE: KPC-Links ad948efa, 6:06 PM. The nightly boundary rebuild is off with them.**
- [x] **O2. Notes saved:** items 44 and 45 in `key-quality.md`, and this file in the repo. Done when: the commit link is here. **DONE: items 44 and 45 saved (5099f686); item 47 saved (eee4465). This file saved as `.claude/inbox/REPAIRS.md` (KPC-Links 9b26bf28, 19 Nov 9:10 PM).**
- [ ] **O3. Information bot.** Read gate run 44631073762. Merge the hand-off 05 stack if it passed on both Pythons. Fix the three reading faults (A, B, C of item 43). ONE run by hand, Kentucky only. Then a blind check of what it read. Done when: the Kentucky facts file and its blind score are linked here. **PART: the 05 stack is in and the reading faults are fixed (KPC-Data 2ea99d0); two more crashes fixed + a per-park guard (4816f03f). Kentucky run 44656781088 READ: asked 193, read 193, 0 skipped, 139 requests; pages html 116, pdf 18, resting 53 (read again next run), dead 1, none 4, script-built 1; facts on KPC-Data tools-out `park-pages/facts/US-KY.json`. LEFT: the blind check of those facts.**
- [x] **O4. Gold and kit answers off the public branch** (S1). Old sealed parks become tune parks; a new sealed set is made privately. Done when: nothing named gold or kit-keys is on `tools-out`. **DONE: KPC-Store 9e29899 (item 46). Squashing tools-out is still to do.**
- [x] **O5. The sample kit, from today's saved key.** At least 299 random outlined parks, plus the 25 busiest per state. Two zips to Brandon. After O4. **DONE: two zips given to Brandon (item 46): 300 random + 8 planted, and 1,193 busiest.**
- [x] **O6. Kit C second-pass packet** (agency size tables). To Brandon for a fresh agent. **DONE: `KPC-kitC-pass2.zip` given to Brandon (item 46).**
- [ ] **O7. Quiet the run** (S2, workflow parts): a held state is a warning; a rule edit with no scope entry is refused; each build records its mode, limits and switches. **DRAFT PR, waits for review: KPC-Links #294 (prep/keys-s2-workflow). Not done until merged. One question for the reviewer in the PR: the build job's own red 'Master gate verdict' step.**
- [ ] **O8. Layers** (S3): the three stale baselines corrected, no re-read; the gate refuses a wrong baseline and a missing copy; the ready check as a report. **Its report is the first column of the per-state board:** one file, kept by the bot. **DRAFT PR, waits for review: KPC-Links #300 (prep/keys-s3-baselines-ready); first report on KPC-Data tools-out fbeca817. Both blocking parts are switches, OFF: on today's copies they would hold 24 states (state baselines) and 48 of 50 (ready check), so which count a baseline must match is the reviewer's rule (in the PR).**
- [ ] **O9. The wider drop list, report only** (S5). After K4 below. **Uses what exists, no new tool:** sizes from the outline = the packet bot's `acres_of` (KPC-Data `kpc_key_review_packet.py:884`); official sizes = the acreage bot's `acres.json` (tools-out `acres/`).
- [ ] **O10. The test gate on Python 3.12 and 3.13** for each outside-agent stack when it comes back. Done when: the two verdict lines are here.

## Outside agent, job A: the 2-fer pull requests

Works from `REVIEW-hand-off-06-PRs-289-290-292.md`.

- [ ] **A1. #289 second round** (review section 1). **ROUND 2 READ: not yet. Round 3 from `REVIEW-hand-off-06-ROUND-2.md` (A, B, C, D, E).**
- [ ] **A2. #290 second round** (review section 2). **ROUND 2 READ: passes as written. Moves with the stack.**
- [ ] **A3. #292 second round** (review section 3). **ROUND 2 READ: passes as written. C and D only.**

## Outside agent, job B: five key drafts

Works from `KPC-hand-off-keys-first-for-Opus.md`, revision 3.1. The first three are stacked in this order.

- [ ] **K1. Hold a state on an error** (part of S2). Its "who changes" list must be empty.
- [ ] **K2. The holder table** (S6a). Switched off. List by park number.
- [ ] **K3. Saved answers say what happened** (S6b). Switched off.
- [ ] **K4. One routine that measures acres from the outline** (S4).
- [ ] **K5. "Verified" needs an outside witness** (S6c). List of parks whose class changes.

## Graders and fresh agent sessions

- [ ] **G1. The sample, two blind passes** (after O5). Done when: the error rate with its range is here.
- [ ] **G2. Kit C second pass** (after O6).
- [ ] **G3. NV US-2635 fixed with a saved "no" and its evidence,** two passes. Nevada does not go public before this.

## Fable (the reviewer)

- [ ] **F1. Read job A's second round.** **DONE for round 2. Round 3 to read.**
- [ ] **F2. Read job B's five drafts and every "who changes" list, in one sitting.**
- [ ] **F3. The public-against-working table** (item 43 step e).
- [ ] **F4. After the sample:** rule sheets for names that collide, the size test, and switching the piece rule and D5 on.

## Nobody has these yet

- [ ] **N1. The Release guard's blind spots, with three test cases** (Grok F1).
- [ ] **N2. The daily "public map is this far behind the key" line** (Grok F3).
- [ ] **N3. Three release checks:** an outline sits only in the file of a state whose key lists the park; none is `via: name+pin` unless named; US-2635 held or fixed.
- [ ] **N4. Push check:** `installed` not true means "no list"; two more tests (store repo).
- [ ] **N5. Two shown 2-fer rows that involve a held park:** check against the private list. Never named in a public file.
- [ ] **N6. KPC-Data housekeeping:** save `layers.json.gz` and the scoreboard only on change; the cleanup, keeping `tools-out`, `intake-files`, `lookup`, `picture-maps` and every branch with an open pull request.

N1 to N3 must be done before any Release.

## Brandon

- [ ] **B1. Hand each agent chat its files** and say job A or job B. Job A now gets `REVIEW-hand-off-06-ROUND-2.md`.
- [ ] **B4. Give the two sample zips to two fresh agent sessions,** and the Kit C zip to a third.
- [x] **B5. Attach `KPC-hand-off-keys-first-for-Opus.md` (revision 3.1) in the Opus chat.** **DONE 8:27 PM; saved in KPC-Store `key-quality/2026-11-19/keys-first/` (34834e6).**
- [ ] **B2. Name who takes N1 to N6.**
- [ ] **B3. One question when ready:** the measuring step still joins pieces of one pair within about 100 m into one spot. Leave it, or fix it before the first fresh 2-fer run?

## Held on purpose. Not dropped.

- New matching rules (names, size test, switches on): after the sample.
- 2-fers batch 2, and the finer second look (part 4): after job A passes.
- KPC-Data history restart: after this list is closed, before the one build.
- The rest of the per-state board, the split of the 2-fer bot, the licence question, the 30-minute bots.
- Hand downloads: after O8 names what is missing.
- **Next week (owner, 19 Nov 8:23 PM):** hide every country but the US and Canada on the map tools. Keep all the other countries' data.
- **After the Kentucky run is read (owner's idea, 19 Nov 8:21 PM):** parks whose POTA link is only an agency front page, and parks with directions but no map point, go as rows to the searching bot, which looks for the park's own page and feeds it back to the reader. First count how many parks that is.

## The finish

- [ ] **Z1. One build.** Every switch Fable passes goes on together. The parks changed must be exactly the lists.
- [ ] **Z2. Fact check and a second sample** on that key.
- [ ] **Z3. Release by numbers,** state by state. Brandon presses the button.

## Found later

- Main's own test gate is red: 18 tests fail on main `4537910` on Python 3.13, and `tests/known-fail-main.txt` is from 7 Nov. One of main's tests rewrites `data/status/kpc_key_drop_guard.json`. (Fable, 19 Nov 9 PM, both gate runs.)
- The ready check (O8) counts 73 Kentucky parks whose POTA link is only an agency front page (AGENCY_HOME_ONLY in run 44656781088): the count the owner's 8:21 PM idea asks for first. (Opus, 19 Nov 9:10 PM.)
- **The acreage bot already exists and is not used** (owner, 19 Nov 9:16 PM). KPC-Data `draft/tools/kpc_acres` (run through `kpc-tool-trial.yml`, tools=acres), last run 15 Nov: 1,668 parks with an official size on tools-out `acres/acres.json`. 52 agency lists were skipped only because `pypdf` is commented out in its requirements.txt (30 FWS, 13 BLM, 9 others) and 28 were blocked by robots.txt. Measuring acres from an outline also exists already (packet bot `acres_of`, truth bot `poly_acres`). K4 (S4) and O9 (S5) use these; nothing new is written. (Opus, 19 Nov 9:20 PM.) **FIXED + RUNNING (owner 9:19 PM: "Fix it and use the bots"):** pypdf on and the 52 PDF-skipped lists read again on resume (KPC-Data 9db5ae17); acreage run 44667049409 started 9:25 PM, results on tools-out `acres/`. **Kit C (G2, agency size tables) overlaps this bot:** read the run before a fresh agent does Kit C by hand.
