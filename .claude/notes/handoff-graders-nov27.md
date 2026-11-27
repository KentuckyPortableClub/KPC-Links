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
   lines in `.claude/inbox/LEDGER.md`. Notes for it: (CORRECTED 8:40 AM, the grader caught it) the live matcher HAS `park_has_no_pin` and has NO `layer_not_complete`; the rule sheet's section 6 list is out of date, go by the code; a web
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

## Added 27 Nov, 8:45 AM
- **The fresh build** `v2-keys\2026-11-27-080935`: 51 areas, 46 clean, 5 with a store gap; 9,962 of 13,321 outlined; licence 7,715
  all / 1,444 part / 803 none; 3,359 pin only (2,496 no record with this name, 666 name but no proof, 80 water only, 70 record
  shared with another park, 46 layer not in store, 1 office only). The grader is grading it.
- **OWNER, 8:34 AM: v1 is no judge** ("why judge against crap work"). The scorecard now passes or fails v2 by itself (G2, G3, G4, G5,
  G9, G10, G11); every v1 comparison is information only, at the end; pin-inside and size-agrees are plain numbers with no limit
  yet (rule sheet section 17). On the PC.
- **Size in Illinois (7 of 68 agree): right land, measured wrongly.** Layer `sgild` writes acres from a flat web map (1.6 to 1.85
  times too big in Illinois); v2 trusts that field over the outline. 39 of the 61 misses. 3 are real land faults (Shawnee took a
  private same-name record, PAD-US 69282; two refuges are partly in other states); 18 are a wrong size on the park's page.
  Work: `/home/claude/work/out/h2-il/` (in that chat only): fix = do not trust an acres field that disagrees with its outline.
- **OWNER + GRADER, 8:37 AM: one record may serve two parks** ("same land, two park numbers") only when each park proves it by
  itself (own agency id, or own name + pin inside); never a smaller park taking a bigger park's outline; every pair on a list;
  an unproved shared record stays a hard fail. Being built.
- **The grader's pre-grade and fix list of 27 Nov is saved whole:** `pregrade-grader-nov27.md`. Done from it so far: #40's red test,
  the reason-list correction. The rest is the open list.

## THE GRADE of `v2-keys\2026-11-27-080935` (the grader, 27 Nov 9:09 AM): build sound, publish / merge NO
Saved whole: `grade-grader-nov27-0809.md`. Hard gates clean in all 51 US areas, all 251 trail joins within 98 ft. But real wrong
land got past the gates. THE NEXT CHAT STARTS HERE, in this order (each: a rule row + a test + a real-data run, PC first):
1. **Fake "two sources"** (79 parks, 28 with the pin outside; Nevada's herd areas): `other_services()` counts two layers as two
   sources when the service address is blank, so two copies of one record prove a park. Need: two different, non-blank services,
   and never the same acres / ids.
2. **Wrong land, confirmed:** US-6423 Manuka (took the 14-acre wayside), US-11094 Glenwood Hatchery (took a BLM area), US-10428
   Walls of Jericho (took Tennessee's land). Partial land to review: US-3935, 7714, 1655, 8335, 2282, 5735, 9317, 12191, 4271,
   9832, 6992. Texas / Alabama unit drops: Aransas, Little River SF.
3. **Size measuring:** Illinois `sgild` (flat-map acres) AND overlapping PAD-US outlines added up twice (NJ 1.89x, VA 1.25x, PA
   1.19x). BEING BUILT 27 Nov by this chat: a general guard (an acres field that disagrees with its outline is not used). Still
   to do after it: measure the UNION of overlapping outlines, not their sum (this is also NY US-10076, 51 vs 44 acres).
4. **Michigan layer `mid`:** real extra land (over 1.5x on 41 of 93 parks): project boundaries, not owned land? Check before use.
5. **Id joins:** "NPS Easement" records joined to battlefields up to 15 miles off; four suspicious NY joins; the Appalachian
   Trail's 384 records up to 487 miles away. List: `v2-id-other-names.csv`.
6. **Park facts:** 11 new parks with blank names (US-13665 to 13672, US-6253, 6257, 6274); Kure Atoll US-0121 moved to US-KI.
7. **Pin-only reasons:** about 100 of 135 store-gap parks say "no record with this name": give them a store-gap reason.
8. **Canada** was not in the build: include it in the next one.
Then ONE rebuild on the PC and the zip to the grader. Do not ask the owner to rebuild before these are in.
