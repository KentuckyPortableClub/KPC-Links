# What would be better on the PC (plan for Brandon, 23 Nov 2026)

Read-only study. Nothing was changed, pushed or started. Where I could not check something live (GitHub's run lists, your PC's real disk), I say so.

## 1. The short version

The five changes that would help most, in order:

1. **Test and grade keys on the PC first, publish from GitHub only when you say.** The PC test kit (START-HERE) already builds keys from saved copies. Adding the grade tools to it moves the biggest minute-eaters off GitHub.
2. **Stop the GitHub page reader's 3-hour timer.** Its own code says "nothing to read" once every state has facts. The PC reads pages now. (Needs your word: a timer is yours to switch.)
3. **Stop growth in KPC-Data.** It was restarted on 2 Nov at 1.9 GB and is 1.7 GB again. Big files rewritten again and again is the cause. Keep working data on the PC and send only finished results.
4. **One tidy PC layout with a HELP.txt in every folder, plus a "keep only the newest" housekeeping step.** Your PC listing shows three copies of the same map store and a pile of applied update zips.
5. **One nightly button, then (later) a Windows scheduled start.** Same steps every time, written in plain words on the control panel.

The "smaller format" you half-remember is real. See section 5.

## 2. Already done on the PC

- **Page reader** (`KPC-PC-BOTS-NOV21`): reads each park's own web page, slowly, robots.txt first, with its kept pages and `state.json`.
- **Own-page finder** (`2f-FIND-OWN-PAGES.bat`): finds pages for parks with no link or a dead one. Slow sites have their own step (`2g`). Re-read of kept pages with no website asked: `2e`.
- **Map points** (address to point) and the **upload pack** (zip you carry to GitHub; the upload workflow `kpc-pc-upload.yml` is started by hand).
- **"Run everything tonight"** (`RUN-ALL-TONIGHT.bat`): read, find own pages, slow sites, map points, pack. One start, no questions.
- **Test keys** (`key builder files\START-HERE.bat` + `kpc_test_keys.py`): builds US states and Canada from saved copies only. Nothing is downloaded or published. Reports are counts only.
- **2-fer runner** (`KPC-2FER-PC-RUNNER`, `kpc-fers-pc-v1.2`), **map store tools** (`1-STORE-TOOL`, world v4), **ID crosswalk**, **tracing test** (`KPC-TRACE-TEST`), **cross-state script** (`GET-CROSS-STATE.bat`, your one-time exception), **control panel**.

## 3. Better on the PC

| Job | Runs today | Why the PC is better | Must stay on GitHub | Risk | Needs your word? |
|---|---|---|---|---|---|
| **Build and test all keys and 2-fers** | GitHub key workflows (US, Canada, world, Kentucky; no timers, by hand) and the 2-fer workflows; PC kit already does keys from saved copies | Free minutes (a US key job has a 330-minute limit); no emails; no 5 MB-file commits; same rules as main because the kit is updated with each rule change | The finished key files the website reads; the release step | The kit must match main's rules. Each report starts with the rules id, so a mismatch shows. Kit updates are by hand (zips) | Test builds on the PC: no (counts only, nothing published). A real build or release: **yes, NO BUILDING still holds** |
| **Grade and fact-check** (`kpc_key_factcheck.py`, `kpc_key_grade.py`) | Run by agents or GitHub on built keys | Both are plain scripts in `.github/scripts` of KPC-Links; they read built keys and write reports. They are **not** in the PC kit today (the kit has only the test builder and cross-state script). Needs the saved copies and park info the kit already has. The sealed gold list must stay private (kept in KPC-Store) | The sealed list stays in KPC-Store; the grade that allows a Release | Easy to grade against the wrong files. Rule: grade only with these tools, never against the saved answers | Adding them to the kit: no. Changing what they decide: yes (reviewed rule change) |
| **GitHub page reader timer** (`kpc-park-pages.yml`, cron `23 */3 * * *` = 8 runs a day) | GitHub, one state per run | The code prints "every state has facts: nothing to read" when no state lacks facts. Park facts hold 18,951 parks. That is **consistent with** empty runs, but I **could not see the run list**, so "8 empty runs" is the schedule, not a count. The PC now reads, kept pages included | Nothing, if the PC keeps reading. The by-hand run stays for emergencies | Low. Keep the workflow file; only the timer goes | **Yes** (never touch a timer without your word) |
| **Test the keeper-to-saved-copies bridge on one state** | Not built. Notes say the keeper "does not write into the saved copies"; a 20 Nov measure said it would add 0 records today | A one-state trial on the PC costs no minutes and cannot hit an agency server (the keys never contact servers) | The keeper's daily run (the only fetcher) | Low on the PC. The PC copy must be a copy, never the master | Yes for building the bridge (it moves a key rule). A read-only trial: no |
| **Nightly PC button via Windows Task Scheduler** | By hand. I found nothing about Task Scheduler in the notes or scripts | Same run every night; you stop remembering "what runs" | Nothing | PC asleep or off = it just doesn't run (safe, it resumes). The tonight script already "carries on where it stopped" | **Yes**: it is a new timer, even if on your own PC |
| **PC pushes its upload pack itself** | You carry the zip to the `intake-files` branch; `kpc-pc-upload.yml` is started by hand. The PC script `kpc_upload_pack.py` only makes the zip (I found no push in it) | Saves a manual step and a mistake | The upload workflow (checks the pack, rebuilds park facts) | A token would live on your PC. It must be set up on the PC only, never pasted into chat. Fine-grained, one repo, branch `intake-files` | **Yes**. Token, and a new auto-start |
| **Keep big working data on the PC** (store, saved copies, kept pages, raw layers) | Store files in KPC-Store `store-data`; saved copies in a release; kept pages and raw layers partly in KPC-Data | No size limit, no history growth, privacy | Anything the site or a kept bot reads each day | The PC becomes the only home of some data: **back up first** (section 6) | Moving what GitHub bots read: yes. Stopping new copies: no |

Two corrections to the brief:
- "Grading tools on PC test keys" is not just a switch: the tools are not in the kit yet, so someone has to add and test them.
- "PC pushes the pack itself" does not exist yet in any script I read.

## 4. Must stay on GitHub

- **The website.** GitHub Pages publishes only from KPC-Links.
- **Bots that must run when the PC is off:** social and Facebook posts, Discord relay, alerts and closures for Kentucky, new-park checks, spot relay, the watchdog.
- **The keeper's daily run** (KPC-Store, 07:41 UTC, enabled 23 Nov; the world keeper stays off). It is the only thing that fetches agency servers.
- **The finished results the site reads:** the released keys, 2-fer lists, park info, the Release.
- **The upload checker** (`kpc-pc-upload.yml`) until you decide otherwise.

## 5. Making GitHub smaller

**What I could see** (my clones are shallow, so sizes are lower than GitHub's: KPC-Links 675 MB here against 815 MB; KPC-Data 1.5 GB against 1.7 GB; KPC-Store 17 MB here because the big `store-data` branch is not in my copy, against 1.7 GB):

- **KPC-Links**: `data/` is 310 MB of the working copy (outlines 84 MB, US key 51 MB, world key 38 MB, wwff 32 MB, trails 32 MB). The biggest single files are US key tract files (11 MB, 5 MB) and one 7 MB world file. History pack is 284 MB over 62 packs. Notes already forbid new screenshots and probe dumps here.
- **KPC-Data**: `data/` is 814 MB (2-fer files 198 MB, waiting room 113 MB). History pack is 552 MB. The biggest old files are a 41 MB `engine/evidence.json`, a 25 MB event-archive PDF, and 20 MB park-fact and repair files. Whole-file rewrites each run are what swell history.
- **KPC-Store**: the code is tiny. The 1.7 GB is the `store-data` branch (a commit per daily run). The handover predicted "tens of MB a month" and says: if history passes about 2 GB, start a fresh branch and keep the old one as an archive.

**What moving to the PC saves.** The store and saved copies on your PC are about 1.2 GB in the part of the listing I could see (the listing stops at 2,000 entries, so the true total is bigger). GitHub does not need them if release files hold the saved copies (releases do not count toward repo size).

**One-time history clean.** Already done once (2 Nov restart workflow `kpc-history-restart.yml`): a bundle backup goes to a release, then main becomes one fresh commit. It cut KPC-Data a lot, but it grew back. A second clean only helps if the writers stop rewriting big files first ("write only when changed" was agreed 18 Nov). KPC-Links and KPC-Store have no clean planned. Needs your word (it force-pushes) and every chat must re-clone afterwards.

**The "smaller format".** What I found, in KPC-Store `HANDOVER.md`, `README.md` and `engine/FORMAT-4.md`:
- Store files already keep outlines as **delta numbers in micro-degrees** (the "ring codec, `q: 6`"), gzipped in pieces. The handover says the engine's answer files use about **7 bytes per point against 12.5** in the store.
- Park outlines are saved **simplified to 3 m (never over 5 m)** (Rule R-G6).
- World outlines are stored **simplified**, with full detail read live and never stored.

I did **not** find a note about a new format meant to shrink GitHub, or a TopoJSON plan. If you were told of one, it was probably these two: "delta numbers" and "simplified outlines". If you meant something else (for example, storing the big layers only on the PC), say so and I will look again.

## 6. New PC layout (proposal)

```
D:\KPC\                        (one root; HELP.txt here says what is where)
  HELP.txt
  1-COLLECT\                   page reader, own-page finder, slow sites, map points
      HELP.txt   kept-pages\   state.json   PRIVATE\   SEND-BACK\
  2-MAP-STORE\                 store tool, world tool, water tiles, crosswalk
      HELP.txt   store\        (ONE copy only)
  3-TEST-KEYS\                 START-HERE, cross-state script, grade tools, reports
      HELP.txt   links\        originals\   last-test\   reports\
  4-TWO-FERS\                  2-fer runner
  5-RESEARCH\                  hand helper, research rules, TO-CLAUDE
  6-TRACING\                   trace test
  7-CONTROL\                   control panel, heartbeat, memory watch
  LAYERS\                      one folder per area, then per agency
      HELP.txt   US\<state>\<agency>\   CA\   WORLD\<country>\
  BACKUPS\                     newest few only, with a dated name
```

Each `HELP.txt` has four lines: **What it is. What reads it. What to run. What it makes.**

**Bring over:** kept pages, `state.json`, the PRIVATE lists, the store (one current copy), saved layers (`Layers-TIDY` where it is the cleaned set), `park-facts.json.gz`, the test-key tools at today's version, the control panel, the page reader and its batch files.

**Leave behind (after you confirm):**
- `kpc-tidy-tool-v2 old` (the name says it).
- `Layers` if `Layers-TIDY` holds everything (compare file counts first).
- Applied kit zips: `kpc-kit-update-2026-11-23a` to `j`, and the two 94 MB update zips, once their contents are in the kit.
- Extra store copies. The listing shows three of the same map store files (`store`, `store-pc-before`, `store-keeper-nov20`).
- `KPC-SESSION-NOTES-NOV16` (the notes live in the repos).
- `links\` (a full KPC-Links copy) can be re-made from GitHub: skip it, or keep one.
- `kpc-key-links.zip` (152 MB): skip if `links\` is rebuilt from GitHub.

**Back up first (cannot be rebuilt):** kept pages; the page reader's `state.json`; the PRIVATE lists (priority, confirmed, and the sealed gold list if you hold a copy); the store and its saved layer copies; `park-facts.json.gz` (also on GitHub, so low risk); anything in `11-14 new layers` and `important` that has no copy elsewhere. Use an external drive or a second disk, and do a test restore.

**Path note.** Batch files point to `D:\KPC GITHUB TOOL and MOre\...`. Folders are found relative to the batch file in some tools (they use `%~dp0`) and by fixed names in others (the control panel has fixed folder names such as `KPC-PC-BOTS-NOV21`). So: renaming folders means updating the control panel's `FOLDERS` list and any batch with a fixed path. Do it in one pass, test each button with `kpc_control_panel.py --check`, and give each batch a "does this path exist?" test.

**Layer codes.** Renaming a layer code (like `sgakd`) is a **reviewed rule change** with a mapping file (old code to new code), never a plain rename. Rename the *folders* (plain names), keep the *codes* inside the files and file names until a reviewed mapping exists.

## 7. Housekeeping

- **Keep-newest rule** (your 23 Nov 8:47 PM words): each tool keeps only its newest copy, or the last few, of outputs, reports, backups, kit zips (once applied), upload packs (once uploaded), state backups and test reports. Older ones are overwritten or deleted, and a short list says what was removed.
- **Suggested counts:** reports last 5; upload packs last 2 (and only after "uploaded" is confirmed); state backups last 3; kit zips none once applied (keep only the newest one).
- **Never clean:** kept pages, the page reader's `state.json`, the PRIVATE lists, the store, saved layer copies, `originals\` (the website's key kept once per state, so tests compare the same thing), park facts.
- **Safety:** a dry-run first ("would delete these 40 files, 2.1 GB"); deleting happens only with your yes.

## 8. Decisions for Brandon (yes or no)

1. Add the grade and fact-check tools to the PC test-key kit?
2. Switch off the GitHub page-reader timer (keep the file, keep by-hand runs)?
3. Plan the keeper-to-saved-copies bridge trial on ONE state on the PC (read-only first)?
4. Set up a Windows scheduled start for "Run everything tonight"?
5. Let the PC push its own upload pack (needs a small token kept only on the PC)?
6. Plan a second KPC-Data history clean, after the writers stop rewriting big files?
7. Move the working store and saved copies fully to the PC, and stop adding them to GitHub?
8. Use the layout in section 6 on the new PC (plain folder names; layer codes untouched)?
9. Leave behind the old versions and applied zips listed in section 6, after a backup?
10. Add the housekeeping step with a dry-run list before it deletes anything?
11. Fix the control-panel wording (each button says which steps it runs, in order) as part of the move?

## The owner's answers (23 Nov 2026 10:32 PM, his words: "1y2 yes kater 3 yes later 4 yes later maybe not everything why pull nightly only needed stuff 5 later 6 yes 7 yes 8 maybe will it make sense what is what 9 yes? 10 yes 11 for sure its confusing everything is")
1. Grade and fact-check tools in the PC kit: YES (later, with the new PC).
2. GitHub page-reader timer off: YES, later (read as "2 yes later"; confirm the timing with him before switching it off).
3. Keeper-to-saved-copies bridge trial on ONE state on the PC: YES, later.
4. Nightly start of the PC run: YES, later, and NOT everything: the nightly run does only what is due or changed (his words: "why pull nightly only needed stuff").
5. PC pushes its own upload pack: LATER.
6. Plan a second KPC-Data history clean: YES (plan only).
7. Move the working store and saved copies fully to the PC, stop adding them to GitHub: YES (plan only). Note for the plan: the keeper runs on GitHub and writes the store-data branch, and the GitHub key builds read the boundary-cache saved copies, so this changes the ONE MASTER COPY design (CLAUDE.md); the plan must say which bots then read from where, and the owner signs that design change.
8. The new-PC layout: MAYBE: only if it makes clear what is what (one HELP.txt per folder, plain names).
9. Leave behind old versions and applied zips after a backup: YES.
10. Housekeeping with a dry-run list first: YES.
11. Control-panel wording: YES, for sure ("its confusing everything is").

## The move, made simple (owner 24 Nov 2026 6:04 AM: "instead of renaming the layers maybe an answer key would be easier..lets make the move easy but the tools bring only what we need every labeled clearly and simply everything laid out in proper order tools need simple easy to use set up...let focus on writing etc being simple and more human like easy to understand")
This replaces renaming layers (section 6 "Layer codes" and the tidy tool's 5-CLEAR-NAMES steps are no longer the plan).
1. **No renaming. One answer key instead: `LAYER-GUIDE.csv`** (opens in Excel), made by a small script, never typed by hand. One row per layer file: file name and folder, code (sgakd...), plain name, agency, area (state / province / country), what uses it (US key, Canada key, 2-fers, store), last read. Built from what already exists: `data/us-key/layers.json`, `data/ca-key/layers.json`, the world key's list, `data/state-gis.json`, and the tidy tool's `LOOK-REPORT.csv` / `MASTER-SOURCES-v2.csv` for the files on the PC. Files and codes keep their names, so no tool or rule breaks. Remade by one button when layers change.
2. **Bring only what's needed.** A move list with three parts: MUST BRING (can't be rebuilt), REBUILD (download fresh: links\ from GitHub, kit at today's version), LEAVE (old versions, applied zips, extra copies). Nothing on the leave list is deleted from the old PC until the new one passes its checks.
3. **Folders numbered in the order you use them** (1-COLLECT, 2-MAP-STORE, 3-TEST-KEYS, 4-TWO-FERS, 5-RESEARCH, 6-TRACING, 7-CONTROL, LAYERS, BACKUPS), plain names, one `HELP.txt` each.
4. **One setup button:** `SETUP.bat` checks Python, makes the folders, unpacks the tools, sets the one root folder for every tool, and runs the control panel's check. It ends with one line: READY, or what is missing in plain words.
5. **Plain writing everywhere** (help files, buttons, reports, READMEs): short sentences, everyday words, one screen; say what to do first and what you'll see; details go in a separate "more" file. Every HELP.txt is four lines: What it is. What reads it. What to run. What it makes.

