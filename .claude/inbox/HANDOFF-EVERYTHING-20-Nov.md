# KPC map key: the whole picture (20 Nov 2026, 9:45 AM Central)

Written by Fable (the reviewer) for the owner, Brandon KZ4CP, and for any agent he hands this to.
It covers everything the three reports of 19 Nov found: what is repaired, what is written but not yet checked, what is still broken, what is not wired together, who has each job, and what waits on the owner.

The live list is `.claude/inbox/REPAIRS.md` in KPC-Links. This file is a snapshot of it. If the two disagree, REPAIRS wins.

Each line below is marked:
- **FIXED** = on main, with the commit or pull request that proves it.
- **WRITTEN, NOT CHECKED** = an agent pushed a fix; Fable has not read it yet. Not done.
- **GIVEN OUT** = one named agent has it; nothing back yet.
- **BUILD ONLY** = nothing but the one build can fix it.
- **OWNER** = waits on Brandon's word.
- **NOBODY** = no owner yet.

---

## 1. Where it stands, short

- The three reports found 41 problems (Claude review 24, Grok 17) plus 7 in the update file.
- 13 are fixed on main. 4 more fixes are written and wait for Fable's check. 6 are with an agent now. 3 can only be fixed by the build. The rest are small, cost or housekeeping, or wait on the owner.
- **No key build has run and none will** until every fix is merged, each is shown working on real saved park data, and the acreage and information bots have finished collecting. (Owner, 20 Nov 9:13 AM.)
- Every map tool on the website is down for maintenance (22 tools). They come back only on the owner's word.
- Rules fingerprints on main, unchanged all day: US `7e4883bfbb45`, Canada `dfef94b3dfd3`, world `b1f23bf0deea`, 2-fers `6a9d67ea4100`.

## 2. The root problem, in one paragraph

The key calls an outline "official" when the name and the pin fit. The owner's own rule also asks for a similar size, and the size was never connected, so wrong land gets joined by name. Measured on a blind sample of 300 random parks (19 Nov): 71% right, 8% partly right, 5.0% hold a record that is not the park, 14% cannot be told. Most wrong records come from the national layer joined by name (16 wrong of 586 records, against 8 of 1,596 for state "owned" layers). A size check alone catches about a third of the wrong parks, so it is one fix of several, not the cure.

---

## 3. What the reports found, one by one

"C-F" = the Claude review (`KPC-hand-off-07-review-report.md`). "G-F" = Grok (`KPC-pipeline-review-2026-11-19.md`). "U" = the update file.

### A. Matching (the key itself)

- **R1. A name join has no size test** (C-F3, G-F6)
  **GIVEN OUT.** Draft #306 (Cursor agent). Fable's read: not yet. Missing: the build is not handed the sizes file, no loud warning when no sizes are read, no list of the 118 parks it would hold.
- **R1b. The national layer joined by name is the biggest source of wrong land** (sample)
  **GIVEN OUT.** Job 4 (the checker): a name-only national record counts only when its manager level matches the park's (109 records, 96 parks go to a check). Rule sheet coming as a draft; Fable runs it against the sample.
- **R2. Rules already ruled but switched off in all 50 states (leased land D5, the piece rule)** (C-F4, G-F8)
  **WRITTEN, NOT CHECKED.** Opus's branch `prep/nov20-d5-piece-on`: D5 changes 18 parks in 4 states, the piece rule 9 parks in 6 states. Moves the US fingerprint to `95390d0d098f`. Needs Fable's read and stamp.
- **R3. One record held by a person's answer in one park and by name in another (70 records, 12 disagree)** (C-F2)
  **OWNER.** Draft #296 is parked: by its own count it moves 0 parks. It only helps if short names (WMA, SP, NWR) may be read as the full name.
- **R4a. A saved "no" stops working when a layer renumbers its records** (G-F7, U)
  **GIVEN OUT.** Job 10 (the checker).
- **R4b. 15 parks hold one record under both "join" and "no"** (U)
  **GIVEN OUT.** Job 10 (the checker).
- **R4c. 472 saved joins by bare name; 64 saved fingerprints fit two records** (C-F5, U)
  **NOBODY.** They are now SAID in the build report (#297, FIXED) but nobody is fixing the answers themselves.
- **R5. The key's own acres number is wrong** (C-F9)
  **PART FIXED.** The fact check now measures the outline (#298, main `80e94f05`); the measured-acres switch is on in all 50 states. Whether the key's number is right now has to be counted after the build.
- **R6. The builder carries on after an error in 4 of 5 places; a missing rule file means "no rule"** (C-F10, C-F14)
  **1 of 5 FIXED** (#295, main `45700ade`). **The other 4 GIVEN OUT:** job 9 (the checker), under way.
- **R6b. Rule settings live in the environment and the runners disagree** (C-F13)
  **NOBODY.**
- **R7. The drop guard only sees a lost outline, not a swap, a wrong gain or a quiet shrink** (C-F7, G-F4)
  **GIVEN OUT.** Job 11 (Cursor agent), report lines first.
- **G3. Plain wrong parks fixed by a saved "no" with evidence** (sample)
  **FIXED** for nine parks (#305, main `ce52fe52`). They change at the build.
- **U. A check row can take joined land off a park on the next build** (U)
  **AVOIDED.** The new drafts use notices instead of check rows. The old line (`kpc_join_check.py:232`) is unchanged. **NOBODY.**

### B. Outlines and the public map

- **R8. Outlines are not rebuilt from the key; one public outline in three is name + pin** (C-F1, G-F2)
  **BUILD ONLY.** Meanwhile the release guard refuses (#302, FIXED, main `e4257be5`): no US state can be released from today's outlines.
- **Release guard blind spots; "public map is behind the key" line** (G-F1, G-F3)
  **FIXED.** #302, #303.
- **R9. 2,379 public 2-fer rows are old and unstamped** (C-F12, C-F16)
  **OWNER said leave them** (8:59 AM): they are hidden with the tools; the first fresh 2-fer run replaces them.
- **2-fer rules fixes (hand-off 06)** (C-F15, G-F11)
  **FIXED.** #289, #290, #292 on main.
- **R10. Public coverage is far below the 85.2% in the notes** (G-F16)
  **NOBODY.** The number in the notes is not corrected. Small.
- **R11. Two side paths to public files skip the gates** (G-F17)
  **GIVEN OUT.** Job 12 (Cursor agent).
- **Release guards are US only; Canada and world have the same blind spots** (Fable's read)
  **NOBODY.** Not measured.

### C. Layers and the store

- **R12. The key builder never reads the keeper's store; the saved copies are short** (G-F10)
  **CANNOT BE FIXED THE PLANNED WAY.** Measured by Opus: the store keeps records per park, not whole layers, so it can add 0 records to the 156 open rows. After the report fix (FIXED, main `6cc6108f`) 96 rows are open and the gap that can be counted is about 28 parks. **Owner ruled (9:10 AM): build on the saved copies as they are.** Opus's branch `prep/nov20-gate-owner-approval` applies that: **WRITTEN, NOT CHECKED.**
- **The fill step skipped the Army Corps layer in 22 states (2,696 areas)** (Opus)
  **FIXED.** Main `efe36340`, proved on the real release files, passed by Opus.
- **Army Corps layers: licence**
  **OWNER RULED 9:39 AM: "Use it".** Ground: the Corps' open-data page. Job 3b dropped. Opus marks both layers allowed in the licence table.
- **R13. The store's own tests fail** (G-F15)
  **WRITTEN, NOT CHECKED.** KPC-Store branch `prep/nov20-store-tests`: 3 fixed, 1 listed (the world engine lacks a US step; copying it rebuilds every world area: owner's call).
- **R14. Two licence tables disagree** (C-F18, G-F14)
  **WRITTEN, NOT CHECKED.** Branch `prep/nov20-one-licence-answer`: one answer per layer (182 publish, 90 held). Must be changed first: it still holds the two Corps layers.
- **Layers report counted wrong** (C-F11)
  **FIXED.** #300, then `6cc6108f`.
- **Push check holes (store)** (C-F17)
  **FIXED.** KPC-Store #25.

### D. Tests, cost, housekeeping

- **R15. Main's test gate was red and its known-failures list was old** (found 19 Nov)
  **FIXED.** #308, main `e63889df`: 12 stale tests repaired, real faults listed with reasons. One fault fixed on top (`6d9dde42`). 6 real faults left: see section 4.
- **Quiet the run** (C-F22, G-F12)
  **FIXED.** #294.
- **"Verified" was too easy** (C-F6, G-F5)
  **FIXED.** #299.
- **Sample and gold answers were on a public branch** (C-F8, G-F9)
  **FIXED.** Moved to the private store. The `tools-out` squash is still to do.
- **R16a. About 430 scheduled runs a day** (C-F20)
  **PART FIXED.** 17 bots switched off (owner's rule 6:34 AM). Key timers off (`0b58c44a`).
- **R16b. A chat reads about 35,000 tokens before it starts; status written by hand** (C-F19)
  **NOBODY.**
- **R16c. Dead weight, overlap, files that churn** (C-F23, C-F24)
  **PART.** `layers.json.gz` done (KPC-Data #132). Rest **NOBODY.**
- **R16d. Repo size, history restart** (G-F13)
  **OWNER.** Held until this list is closed.

---

## 4. What is not wired together

These are the "this bot never talks to that bot" breaks. Each was read in the code, not taken from notes.

1. **Official sizes never reach the builder.** Three size tools read `data/acres.json`; the acreage bot writes its file somewhere else (KPC-Data `tools-out`, `acres/acres.json`, 1,788 parks, 430 with no source page). **GIVEN OUT:** part of #306. Only the rows with a source page (about 1,358) may hold a park.
2. **Nothing writes the grade file the Release reads** (`data/status/quality/verdicts.json`). Even after a perfect build no state could be released. **NOBODY yet:** it is a step after the next sample (the owner's yes per state is what the file records).
3. **The keeper does not refresh the saved copies the keys read.** Planned 15 Nov, never built. Opus measured that the store cannot do it as it stands (see R12). The owner's ruling to build on the copies as they are stands in for it this time. Long term: **NOBODY.**
4. **The 2-fer gate reads a file nobody saves** (`data/waiting/questions/map-audit-auto.json`; the audit bot's save line leaves it out). **NOBODY.** Fix before any 2-fer bot is turned back on.
5. **The US key workflow's held-copies step** uploads a release file in store mode, has a bare error echo and an unmarked `|| true`. **GIVEN OUT:** with job 11 (Cursor agent).
6. **The logger beta calls api.pota.app directly** (2 calls, came with app 0.9.15). **NOBODY:** belongs to the logger chat.
7. **Two rule files hold tables keyed by state or country code** against rule D6. Moving them moves fingerprints. **NOBODY yet:** Opus, as a draft for Fable.
8. **Two outline-data tests fail** because saved outlines and the key disagree. **BUILD ONLY.**
9. **Preflight master check fails on main:** 2 suspect baselines (`US-CO.sgcoa`, `US-OR.sgorf`). Cause not read. **NOBODY.**
10. **KPC-Data's "copy site data" bot** failed 3 of its last 8 runs. Cause not read. **NOBODY.**
11. **Two settings nobody could read:** `KPC_KEY_SOURCE` (must be "store" before the build) and `KPC_GATE_STALE_REFUSE` (if on, 9 more states are held: AK AL IL LA NC NE PA SC VA). **OWNER** can see both in GitHub settings, or an agent with that access reads them.
12. **The keeper starts 9 to 10 hours late every day** (GitHub's doing). Its runs are green; its public shelf carries 1,098 of 1,247 parks. Not a fault; do not read a late start as a failure.
13. **The other wiring candidates** (27 files a bot reads that no bot writes): checked by the Cursor agent (job 8, done). The one real break is number 4 above.

---

## 5. Who has what, right now

**The Cursor agent** (opened #306, #307, #309):
- Finish #306 (the size check). Then job 11 (drop guard, plus item 5 above). Then job 12 (side paths).
- Close #307 (a duplicate).

**The checker** (opened #305, #308; commits as "KPC owner"):
- Job 9 (builder stops a state after an error), under way. Then job 10 (saved answers).
- Push the job 4 rule sheet as a draft.

**Opus:**
- Change the licence-table branch so both Corps layers are allowed (owner, 9:39 AM).
- Report what the acreage run (KPC-Data 44761437443) and the page reader (Nevada 44761461335, then every state by itself every 3 hours) bring in.
- Draft for item 7 above when asked.

**Fable:**
- Read Opus's four branches: the two switches, the licence table, the 34-state gate approval, the store tests. Stamp and merge what passes.
- Read #306 when it is finished, and each job as it is handed back.
- Run the job 4 rule against the sample.

**Nobody yet** (needs a name): R4c, R6b, R10, items 2, 4, 6, 9 and 10 of section 4, Canada and world release guards.

---

## 6. What must be true before the one build

1. #306 finished, read, stamped, merged. The 118 parks it holds are listed.
2. Opus's switch-on branch read, stamped, merged.
3. The licence table merged with the Corps layers allowed.
4. The 34-state gate approval merged, and the gate's report shows no state held for a layer reason.
5. Jobs 9, 10, 11, 12 and job 4 each handed back, read and merged or set aside with a reason.
6. `KPC_KEY_SOURCE` confirmed as "store".
7. Each fix shown working on real saved park data (Fable confirms, one line each on REPAIRS).
8. The acreage bot and the page reader finished, and their counts read.
9. Then, and only then, the owner is asked for the GO.

After the build: a fresh blind sample of 300, same method. Better than 5.0% wrong = release state by state through the guard. Not better = stop and say so.

---

## 7. What waits on the owner

Small, one word each. None of them blocks the agents today.

- `kpc-engine` (nightly park-info bot that reads agency servers itself): keep or stop.
- `kpc-eu-alerts` (Europe weather warnings for the website): keep or stop.
- The 9 states in item 11 of section 4, if that setting turns out to be on.
- Licences: DC is allowed with credit. Georgia's layer says nothing. Michigan: two agents read it opposite ways, so it is treated as not allowed. Together 19 parks, less the Mississippi Corps layer now allowed.
- R3: may short names (WMA, SP, NWR) be read as the full name?
- May chats install packages (a network setting)? Without it agents predict instead of test.
- The world engine lacks one US step; copying it rebuilds every world area.
- Two Georgia fishing areas become pins at release and trip the drop guard: asked at release, not now.
- The KPC-Data history restart: after this list is closed.

---

## 8. Rules every agent follows (the owner's words are in `.claude/CLAUDE.md`)

- No key build, outline rebuild, Release or 2-fer run by anyone.
- Only the keeper fetches from agency servers. The key builder reads saved copies only.
- Only these bots run: social media, website, and the ones collecting data for the map. Never turn a stopped bot on or add a timer without his word.
- One owner per job. If your work overlaps another agent's, stop and say so.
- A change that moves a rules fingerprint goes on a branch as a draft and is merged only after Fable's read ("Reviewed: Fable, date").
- Never name a held park or a sample park in a public file. Counts only.
- Never ask the owner to paste a key or token, or to download anything by hand.
- Done means proof: a commit on main, a number that changed, a live page. "Built" or "pushed" is not done.
- Install opencv, openpyxl and pyshp before running the test gate.

## 9. Things said this week that turned out wrong

So nobody repeats them: the keeper does NOT hold whole layers; hand downloads WERE needed; the measured-acres switch is ON, not off; the saved copies are not "old"; ArcGIS has no robots.txt ban; the key bots must NOT be changed to fetch; the Corps licence line "request permission" is the map site's stock wording for a blank field, not a rule from the Corps. Details: `HANDOFF-20-Nov.md` section 8.
