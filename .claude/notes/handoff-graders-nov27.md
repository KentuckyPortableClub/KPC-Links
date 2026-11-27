# Hand-off for the agents who grade and run the v2 builds (27 Nov 2026, 8:15 AM CT)

Plain words, short reports: the owner (Brandon, KZ4CP) is a ham, not a programmer. He wants less work for everyone, no repair
loops, and nothing passed on that was not measured. Read this page, then `handoff-fable-nov27.md` (the day's log).

## The owner's rules of 27 Nov (his words)
- "pc does the heavy work github gets the finished work": fix and prove on the PC first, then copy to GitHub.
- "do not trust old work": check a number yourself against the files before you repeat it.
- Licences: "use them unless it tells us not to". No terms, a missing licence field, not read = use it. Only words that
  forbid or restrict sharing make a layer private. A ban on resale only is not a ban on sharing.
- Trails: "Yes to trails" and "pota could be wrong trust official": a trail-bot file joins its own park only, and only with
  the pin within 100 ft of the official line (rule sheet section 16). The typed name in a trail file is never proof.
- Never ask him about a hash, a hold or a park. Never ask him to run something again just to see.

## The chain on his PC, in order (one press each)
1. `C:\KPC\3-MAP-STORE-US-CA\LAYER-RECORDS.bat` : 1 status, 2 rebuild (no download), 3 download what is missing.
   Result page: `results\STORE-ROOM-STATUS.txt`; every layer: `results\report\status.csv`.
2. `C:\KPC\6-TOOLS\PAGE-READER\PAGE-READER.bat` : 1 status, 2 re-read kept pages, 3 read what is missing (hours).
3. `C:\KPC\5-ANSWER-KEY-TEST\PARK-FACTS-BUILD.bat`, then Y : builds `park-facts.json.gz` from the page reader's reads.
4. `C:\KPC\5-ANSWER-KEY-TEST\V2-BUILD.bat` : all areas. Output: `v2-keys\<date-time>\` (`V2-BUILD-SUMMARY.txt`, `summary.csv`,
   `pin-only-all.csv`, a folder per area with its `V2-SCORECARD.txt`). `V2-FRONT-DOOR.bat` lists the four (not yet run by him).

## What is where in GitHub (all drafts; nothing merged, nothing published, v1 untouched)
- KPC-Links #393 `feat/us-key-v2-nov26`: the v2 matcher, its one rule table, scorecard, state prep, the notes.
- KPC-Store #39 (store room, the PC copies) and #40 on top of it (trails from `trail-files.zip`, licence per record, the one
  licence list `engine/verified-layers.csv`). #38 is under #39.
- KPC-Data #202 (page reader, with the 27 Nov lock-up fix) and #203 (park facts builder + the PC button).
- The PC is the master copy. Before changing a PC tool: stage the file from the PC, compare, write, stage it back, compare.
  A file just copied to the outputs folder needs about 15 seconds before it can be sent to the PC (one send went out stale).

## State of the inputs this morning (measured)
- Store room, rebuilt 6:47 AM: 66 areas, 58 whole, 8 with a gap (12 layers: 7 need a download, 4 a hand download, 1 timed out).
  Trails read: 1,123 lines in 51 areas. Minnesota `sgmnf`: 6,709 records usable, 3 private with their own reason.
- Park facts, built on the PC 7:1x AM: 18,768 parks; sizes and agency ties carried from the 24 Nov file (not on the PC).
- Page reader: running; about 11,900 of 18,951 pages read before today's run.

## What changed in v2 today (so a grade is read the right way)
- Other spellings table: NY US-0474 and US-2147 join (name + pin). `name_fields` for Alberta and BC Parks.
- Trail rule (section 16): with trails in the store MN 306, NY 824 outlined (was 295 / 821 without). Eight trail parks whose
  pin is 112 ft or more from the line stay without it.
- Speed: Alaska hung in the size step once its two missing layers were in. Same test, faster (95 s). MN NY ND VT keys are
  park for park identical before and after.
- Licence counts are printed on the scorecard and the build summary.

## What a grader should look at first
- The fresh 50-state build started 27 Nov about 8:10 AM. The 26 Nov 10 PM build had 44 of 51 areas with a failing gate
  (mostly G6, also G7, G1, H1, H2). NOBODY HAS READ WHY YET. That is the biggest open item. Read the per-area
  `V2-SCORECARD.txt` and the gate definitions in `tools/pc-keys/kpc_v2_scorecard.py` before any other work.
- Known wrong, not yet fixed: the same thin outline saved twice is counted twice in the size (NY US-10076 shows 51 acres,
  44 is right). A pin-only reason can be loose for a trail park whose pin is too far (says name but no pin or size proof).
- BC: 42 parks changed size by over 10% when the BC Parks names came in. Look before BC is used.

## Open, in order
1. Grade the fresh build; find why the gates fail.
2. Store room: press 3 for the 7 layers; hand downloads for CA-ON ON-CH Conser, US-AZ sgazb sgazc, US-ID idw.
3. Licences: 26 list rows left alone (14 with no evidence link, 5 not park layers, 7 unclear words); the trail-source licence
   file is untouched and trail lines are still marked private in the layer files; `sgmnf`'s row says parts only.
4. Park facts workflow on GitHub: drop `--key`, add `--previous`. Sizes file and agency lists are not on the PC.
5. Page reader: 355 parks whose saved page is another park's; one kind of browser hang cannot be cut off (it now says so).
6. Canada's 30 trail files are not read. Kentucky's key has a stray trail id (`US-0.json` on the status page).
7. On hold until the build is graded (the grader's call): the frozen-matcher rule, the problem solver for the pin-only list,
   the 4-box control panel. THE PLAN IS WRITTEN DOWN: `v2-next-phase-spec-nov27.md` (the owner: do not forget it); three
   lines in `.claude/inbox/LEDGER.md`. Notes for it: v2's own reason list has `layer_not_complete` and no `park_has_no_pin`; a web
   page cannot start programs on the PC, so buttons stay `.bat` files.
8. The owner's bad-findings report page has not been brought up to date with today.

## Traps that cost time today
- A helper said three parks took a trail line past 100 ft. Wrong: those were distances to their land. It was passed on
  unmeasured and a ruling leaned on it. Measure first.
- Two blind licence readers wanted three layers private; the PC rows already held fuller text that said use it. A blind
  look sees less than the earlier readers did: check the row's own evidence before flipping a verdict.
- Buttons cannot be tested here. Keep to patterns proven on his PC (`choice`, not `set /p`). Never replace a `.bat` while
  its window is open.
- A silent tool looks frozen. Anything that can wait or work for more than a minute must print what it is doing.
