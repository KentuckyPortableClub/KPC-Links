# Handoff: key builder, 26 Nov 2026 (NEWEST; the new PC takes over)

Owner (Brandon, 26 Nov 1:41 AM): "new pc is taking over tomorrow". The new PC's folder is `C:\KPC_Map_Builder_Program`. The old chat was tied to the old PC (D:\KPC GITHUB TOOL and MOre), so a new chat starts on the new PC.

## Done in the first new-PC chat (26 Nov ~1:45-3:00 AM CT)
- **The copy is on C:, not G:.** Working folder `C:\KPC_Map_Builder_Program\KPC GITHUB TOOL and MOre`; Python 3.12 user install in
  `C:\Users\brand\AppData\Local\Programs\Python\Python312`. The #380 note's move part says G:; the owner ran from C:.
- **Copy checked (read only), all equal to the old PC:** 66 website keys + layers.json = sha256.json (ref main 31101d04); kit 25x
  (.kit-main.txt, .done marker, all 41 zip files equal to what is installed); layer-records for all 66 areas, MN 11 / NY 8 layers complete;
  layer-files 1,367 files 4.5 GB incl. 63 hand files; have\ MA/OH/ME hand files + .kpc-source.json; shapely 2.2.0, pyproj 3.8.0, pyshp 3.1.9,
  numpy 2.5.5 (no pyogrio: only for Alaska). Leftovers in originals\: built-files.json, build-running-MN.txt (from before 25x; nothing
  reads them; not in the sha list; left alone).
- **MN test after the move (reports\test-2026-11-26-0153, kit 25x) = test-2026-11-25-2245** (MN REPORT block word for word, pin-only 3 same,
  row-proof 239 rows same). **29.8 min vs 46.2 min** (same-land step 22.6 -> 14.2 min).
- **Kit 26a on the PC, read back equal** (`kpc-kit-update-2026-11-26a.zip`, sha256 74003b3b4534...; sorts after 25x): #382 + #383 + #384 from
  prep/speed-nov26 51e77372; US 5b6caa7b7e90, CA d0352dfc270b, world 167bf55f79a8; the 41-file layout of 25x, .kit-website-keys kept from 25x.
  3.12 tests ALL PASS: batch16/17/18, speed_nov26, pc_kit_keep_nov25, same_land (+ selftest), round15, b1_refound, pc_kit_nov24.
  **Owner next: START-HERE MN NY; REPORT must say US 5b6caa7b7e90. Compare park by park with test-2026-11-25-2245.**
- **Housekeeping (owner 2:30 AM: "go ahead I approve ... make it nice and work great and dont let it get bloated"), on the PC, 25 files read
  back equal; nothing was moved or deleted:**
  - New `Tools\HOUSEKEEPING` (stdlib only): 1-SIZES (one line, sizes.csv kept to 200 lines), 2-CLEAN-UP (shows the list, YES, MOVES to
    ARCHIVE, never deletes: added kit zips but the newest 2, reports but the newest 6 + test-2026-11-25-2245, .before copies but the newest per
    file, top MOVE-PREP only when every file's sha256 equals Tools\MOVE-PREP, LAYER-GUIDE2.csv, 3 retired folders, old TO-CLAUDE zips),
    3-UNDO-CLEAN-UP, 4-FIX-PATHS (D:\... or last-root.txt -> its own root; old lines in fix-paths-log.txt), 5-LAYER-GUIDE (kpc_layer_guide.py
    v2: + whole-layer records/complete/made from the manifests, hand files, Layers-TIDY; LAYER-GUIDE.csv + searchable LAYER-GUIDE.html, saved
    over), 6-BACK-UP (robocopy, relative). settings.txt: archive folder (the second drive goes here) and the counts. Never touched: Layers-TIDY,
    Layers, originals, last-test, links, store results, have, PRIVATE. TEMP in the KPC folder empties files older than 7 days at panel start.
  - `Tools\kpc_control_panel.py` 2026-11-26a: + LAYER-RECORDS button (it had none), section "7. Keep it tidy", size line in the header
    (refreshed when a tool finishes), "kit waiting" hint; clean-up / undo / fix paths run alone. Same file as tools/pc-keys:
    **PR it (+ the housekeeping folder) after the 26a test passes.**
  - **D: paths -> C: (12 files):** store + world have-folders.txt, saved-outlines-folder.txt, open-data-portals.json local_folders
    (kpc_research's default said D:), 2-fer settings.json, crosswalk agency-lists-folder.txt, old fers store-folder.txt, tidy folders.txt
    (D:\layers now a note), hand helper originals-folder.txt (new; its default said D:), Tools\MOVE-PREP 3 bats. Heartbeat task (if used):
    run 2-HEARTBEAT-ON once.
- **Owner's call, not touched:** Layers-TIDY\Archive-pieces holds the same 4.15 GB zip twice; KPC-ID-crosswalk has 2 older store copies.
- **26 Nov 9:21 AM (owner: "Make the change you can and yeah we can get rid of duplicate layers"), on the PC, read back equal:**
  `C:\KPC_Map_Builder_Program\MOVE-TO-C-KPC.bat` (moves the folder to `C:\KPC` after YES, loose notes into important, SETUP-PYTHON.bat into
  Tools, then fix-paths --go + sizes) and `Tools\HOUSEKEEPING\7-DUPLICATE-LAYERS.bat` (`kpc_housekeeping.py dupes`: Layers, Layers-TIDY
  except Private, 11-14 new layers; same size then same sha256; keeps Originals first, then the cleaner name; removes the rest for good after
  YES, re-checks the hash first; log duplicates-removed.csv). Panel button added (section "7. Keep it tidy"). Seen by name + size:
  Archive-pieces 4.15 GB twice, Gordt EP.zip 217 MB x4, Wales SSSI p800 x3. The bridge cannot move or delete: the owner runs both.
  After the move this session's folder is gone: the owner adds C:\KPC in the Claude app.
- **Layout, after the 26a test:** rename `C:\KPC_Map_Builder_Program\KPC GITHUB TOOL and MOre` to one short name (e.g. `C:\KPC`), then
  4-FIX-PATHS (tools find each other by place; re-add the folder in the Claude app). Numbered inner folders need kit changes (panel FOLDERS,
  kpc_test_keys STORE, LAYER-RECORDS climb, crosswalk / page-reader / trace climbs): later.

## Done later on 26 Nov (10 AM - 12:30 PM CT, builder chat)
- **Kit 26a test PASSED** (reports\test-2026-11-26-0951, US 5b6caa7b7e90). MN 46 -> 5.5 min, NY 9.8 -> 3.9 min. MN same counts;
  NY 820 -> 823 outlined (US-0481, US-10040, US-2071 back, checked). Grader paste sent; #382 -> #383 -> #384 wait for the grader.
- **New folder layout on the PC** (REORGANIZE.bat, undo with UNDO-REORGANIZE.bat): 1-MAP-LAYERS, 2-NEW-DOWNLOADS, 3-MAP-STORE-US-CA,
  4-MAP-STORE-WORLD, 5-ANSWER-KEY-TEST, 6-TOOLS, 7-NOTES, ARCHIVE, TEMP. Every tool tries the new name first, then the old one.
  Open the panel with C:\KPC\CONTROL-PANEL.bat. Settings rewritten; old copies in ARCHIVE.
- **Tidy:** duplicates removed 9.2 GB; clean-ups moved 4.9 GB to ARCHIVE (nothing deleted); backup on F:\KPC-BACKUP (29.6 GB).
  C:\KPC 41.0 -> 26.8 GB. New buttons in 6-TOOLS\HOUSEKEEPING: 8-WHERE-IS-THE-SPACE, 9-UNPACK-NOV13-ZIP.
- **Nov 13 zip** (Archive-pieces, 42 pieces, 462 files) was never unpacked: unpacked + sorted by SORT-NEW-LAYERS (392 files filed,
  266 to Originals). Pieces go to ARCHIVE by step 3 of 9-UNPACK (needs the owner's YES).
- **Nightly layer download on the PC:** Windows task "KPC nightly layers", 2:41 AM, wakes the PC (SETUP/STOP-NIGHTLY-LAYERS.bat in
  3-MAP-STORE-US-CA). Downloads missing whole layers AND the keeper's out-of-date list (kpc_keeper_requests.py reads
  store/layer-requests.json on store-data with the owner's gh sign-in; 145 rows on 26 Nov). First run 26 Nov 11:03: 66 areas, MN and
  NY complete. kpc_layer_records.py: --again-urls, count asked 3 times, hand-file-names.csv (KPC-Store draft PR #38, updated).
- **Robots check** (CHECK-ROBOTS.bat, results\report\robots-check.csv): really blocked = BC x3 + Yukon parks (open-data downloads
  instead); certificate problems = NB, federal DFRP, NS, WA Ecology (hand download in a browser). HAND-DOWNLOADS-NOV26.txt lists them
  with ready folders; ADD-ALASKA-PADUS.bat (5-ANSWER-KEY-TEST) turns the USGS Alaska file into the store's hand file.
- **GitHub:** the owner signed in on the PC (gh + Git for Windows). Park page reader on GitHub (KPC-Data kpc-park-pages.yml)
  SWITCHED OFF 26 Nov 11:5x AM with the owner's OK ("K switch off park page reader"); the PC page reader does that job.
- **The owner's look for every tool screen** (26 Nov 11:08 + 11:39 AM): like the sort tool and the nightly screen. Title box, what it does
  and never does in plain words, short aligned table, a clear DONE line, a progress bar on slow jobs.

## Done 26 Nov afternoon (owner's GO 1:02 PM: "1 go, 2 go 3 go 4 go and go for all this")
- #382, #383, #384 MERGED by the grader (10:20-10:22 AM). Owner ruled "no terms use it": sgaki, sgutc, sgwae, St. John's Planning 5,
  federal DFRP 4 = fetch yes (PC verified-layers.csv + KPC-Store PR #38; owner-decisions.csv row).
- GitHub backup on the PC: F:\KPC-BACKUP\github-2026-11-26 (mirrors of all 3 repos, fsck ok; boundary-cache copied to
  5-ANSWER-KEY-TEST\links\cache\boundary-cache). The 2 GB history-20261102 release would not download: it STAYS on GitHub.
- Paused in KPC-Data (owner OK, Sonnet check: nothing the site, keys or 2-fers read): kpc-engine, kpc-workshop, kpc-hardlook,
  kpc-pile-solver (convert-layers and fetch-files were already off). Park page reader off earlier.
- KPC-Data size: tools-out trimmed 9,966 -> 1,194 files (engine, audit, pulloffs, picture-trace, watch, links2, site-check, fers,
  convert except report.csv), intake-files 182 -> 105 (69 world file-* layers, hand-downloads, pc-upload); then kpc-history-restart
  SQUASH dispatched (run 45887208901). Leads worth a look later (in the F: backup): engine SURE+STRONG outlines for 69 pin-only parks
  (US 27, CA 30, GB 12), engine blocked.csv (1,398 layers), data/truth "off" list (853 parks).
- Release + branch deletions need the owner's PC (this session may not delete): 6-TOOLS\HOUSEKEEPING\11-GITHUB-CLEAN-UP.bat
  (43 GB fers-bundles, app-beta-0.7.9, 7 old backups, 204 old branches; checks each against the F: backup first).
- GitHub size goal (GitHub: ideally under 1 GB): Links 0.81 OK; Data 1.69 and Store 1.85 to trim. Store: replace store-data with one
  commit after the keeper moves to the PC. A main history reset frees little while old pull-request refs keep the history alive.
- 76 tool screens redone in the owner's look (helper; read back); 4 small bugs fixed (START-HERE Enter, 2-fer RUN-ALL pause,
  crosswalk >nul). Next: progress bars (store fetch/build, layer download, key test per state, page reader, 2-fer finder).

- **Night key test (Brandon 26 Nov 2:48 PM: 'set a timer for it'):** NIGHTLY-LAYERS.bat now calls 5-ANSWER-KEY-TEST\NIGHT-TEST.bat after the downloads. It runs only when a TEST-ORDER.txt (one line of states) is there, renames it so it runs once, and writes NIGHT-TEST-last.txt. Saved copies only. Keep orders small: the Windows task stops at 6 hours.

## Next (in order)
1. 27 Nov: read the first nightly run with the keeper list (results\logs\nightly-layers-*.log, nightly-last.txt). If right, ask the
   owner's OK to switch off the GitHub keeper's downloading (keep its light change check).
2. Owner rulings waiting (licence list): NPS historic places sgaki (12 states, federal public domain, marked "not a park layer"),
   UT sgutc, St. John's and federal DFRP ("not a park layer"), WA sgwae (no terms found). AZ x2 and ID idw stay out (terms bar copying).
3. Tool screens in the owner's look, one folder at a time: control panel, START-HERE, LAYER-RECORDS, housekeeping, then the rest.
4. KPC-Data bots one at a time: PC version runs once, then the owner's OK. Biggest: park-info engine 49 h/week, workshop 19 h/week.
5. GitHub size clean-up: its own GO (backup first).

## Who does what
- This chat is the **BUILDER**, not the grader. The owner said twice: "your the builder not the grader". For every grader handoff, give the owner a **zip**: FOR-THE-GRADER.md, the patches and the tests. The grader grades; the owner merges.
- **PC first, PR last** (agreed 25 Nov): a fix goes to the PC as a kit update and the owner tests it; one PR per batch that passed.
- Never ask the owner about a rules hash, a hold or a park (rule of 25 Nov 12:07 + 12:09 PM). No builds, dispatch, Release or keeper runs. Python 3.12 for the touched tests.
- Judge tests against the owner's **earlier PC tests**, never the website ("THE WEBSITE IS NOT GREAT THATS WHY WE ARE REBUILDING").
- **Don't write on a PC unless the owner says go.** The 26 Nov 1:10 AM rule was "dont save anything" while he copies files; GitHub is fine.

## Where things stand
- **#381 (batch 16) merged** into main as 56aff3bd: US daf204f039f0, CA d0352dfc270b. It passed the owner's START-HERE MN NY on kit 25x (old PC, reports\test-2026-11-25-2245).
  - MN: 313 of 323 parks outlined, check rows 391.
  - NY: 820 of 851 outlined, check rows 211.
  - Pin only: MN 3, NY 14.
- **Open draft PRs, stacked, each waiting for the grader:**
  - **#382** batch 17, base main. US -> 3b4a7d2fa8fb. Thin shapes are can't-tell (Old Croton), twin PAD-US copies are one land (Wertheim), same-ground records count once (Helen McNitt). Tool-only commits: each PC test keeps its keys and writes CHANGES-<area>.txt; kpc_padus_gdb.py (stays out of the kit until it has run once).
  - **#383** batch 18, base #382. US -> 2b181efdb282. MN DNR's own ids for state forests and parks; publish_keys clash fix (Florida sgflf had repeated keys); id file format 14. 26 more agency-id layers wait in AGENCY_ID_LATER until their state builds from the fresh store.
  - **#384** speed, base #383. US -> 5b6caa7b7e90. Same answers, much faster (MN PAD-US 300 records: 148 s -> 9 s). Rings filed by box, and grid points worked out once.
- **Kit 26a holds #382–#384** (see above).

## First jobs on the new PC
1. DONE 26 Nov (see above). **Check what he copied** into C:\KPC_Map_Builder_Program against the old PC:
   - the 66 website keys + layers.json (sha256 list in links\.kit-website-keys\sha256.json)
   - kit version 25x
   - the store (kpc-outline-store-full\results\layer-files, plus have\)
   - originals\ (never written)
   - Python add-ons: shapely, pyproj, pyshp, numpy
2. DONE: kit 26a. **Make the next kit** (#382 + #383 + #384). The owner runs START-HERE MN NY. Compare with test-2026-11-25-2245, park by park.
3. **Hand files in the store's have\:**
   - US-MA-sgmaa.geojson.gz, US-OH-sgoha/b/c.geojson, US-ME-sgmec.geojson, each with a .kpc-source.json.
   - Made from the owner's own downloads (Sonnet on his PC). The grader settled them as his downloads.
   - Nothing reads them until he runs LAYER-RECORDS, and that is his decision.
   - Alaska PAD-US: the .gdb (785 MB) needs `py -3 -m pip install pyogrio`, then kpc_padus_gdb.py.

## Later (from the grader and the owner)
- The report compares with the website **by the proof, not by id**: 27 MN website rows carry an id the new spelling gives another parcel.
- Each test is judged against the owner's **best earlier test**. The keep-last-good guard and the join check use that test, not the website key (rule change, grader first).
- One report line per layer: "row numbers moved: yes/no, how many". Since 12 Nov they moved in MN sgmne 13,111, sgmnc 236, sgmnb 59 and NY sgnya 3,216; everything else stayed.
- Name variants (Artpark, Lock 32, Reinstein Woods, Ludlow Creek, Charles Flood, Schunnemunk); PAD-US Source_PAID as a same-land proof. Ideas only.
- Still missing layers: MS mszw/mszp, AZ and ID idw (behind terms); retired layers still joined: CO sgcod, WA sgwae, ID sgidb, sgaki, UT sgutc.
