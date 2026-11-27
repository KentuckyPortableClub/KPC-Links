# Hand-off for the next Opus key builder (27 Nov 2026, 5:20 AM CT)

Owner: Brandon (KZ4CP). Plain words, short reports. He is a ham, not a programmer.

## Your job, in one line
Help finish the **new key (v2)**. **Fable leads** (manager, brains, reviewer) and hands out jobs to Sonnet and Opus.
Take the jobs Fable gives you, do them the v2 way (below), and check numbers against the files before you report.
**The old key (v1) is paused** (owner 27 Nov 5:11 AM: "Moving to v2 only from here"). Do not touch v1 or #392.

## Read first, in this order
1. `.claude/notes/handoff-fable-nov27.md` (branch `feat/us-key-v2-nov26`): Fable's job list, what is ruled, the traps.
2. `.claude/notes/handoff-us-key-v2-nov26.md`: what v2 is, the numbers, how to change it. Sections "Added 26 Nov night" and "Added 27 Nov".
3. `.claude/notes/rule-sheet-us-key-v2-nov26.md`: sections 1-8 (how v2 decides), 12 (trails), 13-15 (the owner's rulings).
4. `.claude/notes/net-rules-nov26.md` (the site rule), `audit-tools-nov26.md`, `audit-facts-nov26.md` (what was wrong in the tools).
5. `.claude/notes/what-changed-nov27.txt` (branch `notes/handoff-nov26`): one plain page of every update. Same page on the PC:
   `C:\KPC\7-NOTES\WHAT-CHANGED.txt`. Add a block there when a tool changes.
6. The owner's report of every bad finding: https://claude.ai/artifact/QpFeqpJkCUoxgjmazB6gNF

## What is being built
- **v2 key matcher**: KPC-Links draft **#393**, branch `feat/us-key-v2-nov26`. Matcher `.github/scripts/kpc_us_key_v2.py`;
  every rule, word list and number in `.github/us-key-v2-rules.json`; PC tools in `tools/pc-keys/` (`kpc_test_v2.py`,
  `kpc_v2_scorecard.py`, `kpc_v2_state_prep.py`, `V2-SIDE-BY-SIDE.bat`, `V2-STATE-PREP.bat`, `V2-BUILD.bat`);
  tests `tests/test_us_key_v2_nov26.py`, `test_v2_scorecard_nov26.py`, `test_v2_state_prep_nov26.py`.
- v2 reads ONLY today's layer files, the park facts, the park list and the rule table. US and Canada. Each park is marked
  share all / part / none (licences). Proof so far: owner's PC run MN 295 of 323, NY 819 of 851, no park on another's land.

## The new SOP (how work is done now)
- **A fix is a ROW in the rule table plus its test.** Never a pass that changes the key afterwards, never a switch, never old data.
- **Try a row before changing anything:** `py -3.12 kpc_test_v2.py MN NY --try my-rules.json`.
- **A new state:** `V2-STATE-PREP.bat` first.
- **PC first, GitHub last.** The owner's PC is the master copy of the store room and the page reader (not all in GitHub yet).
  Before changing a PC tool: stage the current files from the PC, start from those, write back with `expectedMtimeMs`,
  stage it back and compare. Never start from a GitHub copy of those two tools.
- **One run each, no reruns to see.** If a status page looks wrong, stop and read it; never ask him to run it again.
- **Site rule:** only a real robots.txt Disallow line is a "no". A 401 / 403 is that page only, for that run. Five in a row
  from one site, or one 429, stops that site for the run. Nothing is carried into the next run.
- **GitHub:** branch + draft PR, author `KPC owner <KentuckyPortableClub@users.noreply.github.com>`, message ends
  `KPC owner, <date>`, no trailers. NO BUILDING (no key build, outline rebuild, Release or 2-fer run on GitHub).
- **Never ask him** about a hash, a hold or a park. Python 3.12 for tests, one line per test file.

## Goals
1. v2 builds every US state and Canadian province from the PC's layer files, with no park on another unit's land.
2. More proven outlines: agency ids first, then name with a second proof; everything else stays a pin with one reason.
3. Licences shown: share all / part / none on the scorecard and build summary (NY: 530 parks may not be shared publicly).
4. Then ONE build, when the owner lifts NO BUILDING.

## What is fixed (details in what-changed-nov27.txt)
- v2: no old answers carried, no wrong land, a lock only watches, every rule has a test, km2 / hectares to acres, French names.
- Store room (PC, `C:\KPC\3-MAP-STORE-US-CA`, `LAYER-RECORDS.bat` 1 / 2 / 3): one empty record no longer blocks a state
  (MA, NC), the right id column, no Canada double reads, national layers cut to the area, failed downloads never "fresh".
- Page reader (PC, `C:\KPC\6-TOOLS\PAGE-READER`, `PAGE-READER.bat` 1 / 2 / 3): junk headings not saved as names, km2 guard,
  failed reads keep good facts, ~5,000 "read but empty" parks read again, the page browser is switched on, sites that stop
  answering are read through the page browser. GitHub copy: KPC-Data draft **#202** (the PC copies of 27 Nov 4:35 AM).

## Still open (Fable's list, in order; take only what Fable hands you)
1. Store room into GitHub (KPC-Store draft PR) from the PC copies. Page reader: #202 needs `PAGE-READER.bat` of 4:58 AM.
2. **Trails** (Fable is on it, 27 Nov): the trail bot's line files are KPC-Data `data/trails/US-{n}.json` +
   `data/trails/index.json`; the store room must read them in as line records. 21 MN + NY parks wait on this.
3. Park facts builder (KPC-Data, `audit-facts-nov26.md` F1-F16): old-key input, km2 guard, bad pins, Kentucky ids (72),
   freshness stamp, keep the page reader's new fields; then a PC button.
4. After the next page reader run: rebuild the park facts, rerun v2 (current numbers use 24 Nov facts).
5. Small v2 rows: other spellings (US-0474, US-2147, US-4239); Alberta / BC name fields (PLUZ_NAME, PLREC_NAME, ParkName,
   PROTECTED_LANDS_NAME); licence counts on the scorecard; the prep tool's web-address compare; one front-door button.
6. Store room gaps (status page 27 Nov 4:48 AM): CA-AB, CA-ON, CA-YT, US-CO sgcod, US-FL sgflc, US-MS mszp / mszw
   (press 3); held by a club rule (hand download): CA-ON ON-CH, US-AZ sgazb / sgazc, US-ID idw.
7. Page reader: 355 parks whose saved page is another park's page; Pennsylvania State Game Lands (308 parks, no layer names them).

## Where everything is
| What | Where |
|---|---|
| v2 code, rule table, tests, notes | KPC-Links #393, branch `feat/us-key-v2-nov26` |
| v2 on the PC (beside the buttons) | `C:\KPC\5-ANSWER-KEY-TEST` (`V2-*.bat`, `kpc_us_key_v2.py`, `us-key-v2-rules.json`, `v2-keys\`, `reports\v2-*`) |
| Store room (master copy) | `C:\KPC\3-MAP-STORE-US-CA`; status `results\STORE-ROOM-STATUS.txt`; layer files `results\store\*.layer-records.json.gz` |
| Page reader (master copy) | `C:\KPC\6-TOOLS\PAGE-READER`; status `PAGE-READER-STATUS.txt`; GitHub copy KPC-Data #202 |
| Control Panel (all buttons, "What changed") | `C:\KPC\CONTROL-PANEL.bat` -> `C:\KPC\6-TOOLS\kpc_control_panel.py` (2026-11-27a); GitHub copy KPC-Links #385 |
| Trail line files | KPC-Data `data/trails/` (made by `.github/scripts/kpc_us_trails.py` in KPC-Links) |
| Park facts | KPC-Data `data/park-facts.json.gz` (PC copy `C:\KPC\5-ANSWER-KEY-TEST\park-facts.json.gz`, 24 Nov) |

## Paused or parked (do not pick up unless the owner says)
- KPC-Links **#392** (v1 locks, 11-state switches, layer-kind fallback): paused. One idea worth carrying into v2 if it is not
  there already: a state layer's kind is only a fallback; a record's own name or type field decides (Red Lake WMA joined
  Red Lake State Forest because MN's forest layer stamped "forest" on its WMAs). v2's own run had Red Lake right.
- The PC kits `kpc-kit-update-2026-11-26a..l.zip` and `START-HERE.bat` are the v1 test. Not needed for v2.
- KPC-Data #200 (bare host) and #201 (page names) sit under #202; the PC copies in #202 already carry both.

## Traps
- The bridge cannot write into `links\.github` on the PC: put files beside the buttons.
- Two chats edited the same PC tool once (27 Nov 4:20 AM). Stage first, compare, write with `expectedMtimeMs`.
- `.bat` files are CRLF: edit them as bytes. Never replace a `.bat` while its window is open. No Windows here: keep to
  patterns already proven on his PC.
- Shared code: the page reader's `kpc_manners.py` is used by GitHub bots too (the KY closures bot read its internals; fixed in #202).
- Check every number against the files before telling him. A report that says "fixed" must have proof.

## Starter line for the new chat
"Opus: you are the v2 key builder under Fable. In KPC-Links branch notes/handoff-nov26 (PR #385) read
.claude/notes/handoff-key-builder-opus-nov27.md, then Fable's .claude/notes/handoff-fable-nov27.md on branch
feat/us-key-v2-nov26 (PR #393). Ask Fable for your first job."
