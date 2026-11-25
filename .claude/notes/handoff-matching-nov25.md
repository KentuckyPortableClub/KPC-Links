# Hand-off: the better matcher + full layer files (25 Nov 2026, ~9:10 AM CT)

Read this first in a new matching chat. Plain words. Owner: KPC owner. Nothing is merged; nothing is built (NO BUILDING stays).

## Where things stand
- **KPC-Links #380** (branch `prep/better-matcher-nov25`, head a0b1a4b2, draft): the better matcher. US rules deb61cc4084c -> **0d015ade5a34**,
  changelog line says NOT YET APPROVED. The other builder graded rounds 1-7; round 8 (+ the gap fix a0b1a4b2) is not graded yet.
- **KPC-Store #38** (branch `prep/layer-records-nov25`, head 8f1bf6d, draft): `engine/kpc_layer_records.py` + `LAYER-RECORDS.bat`
  (every record of every layer the keys join, US + Canada; world ON HOLD), G4 in `kpc_outline_store.all_parks`, Catskill allowed (read only).
  The other builder cannot see KPC-Store (no access): the owner reviews it.
- **KPC-Data #199**: revert of the US-4501 acres edit. Graded MERGE-READY; the owner merges when he likes.

- **Round 9 (ee666da, 25 Nov ~9:35 AM CT): the grade's Q1.** The key writes the layer file's identity (sha256 + made) in
  fresh_store.layer_file (kpc_store_attrs format 9); the cutter HOLDS (exit 3) on another download, no identity, or a fresh id missing
  from the file; drops only for not publishable / no shape. Canada '<label>:<n>' ids now counted in skipped_ids. US rules -> **d8e396b4cb51**
  (NOT YET APPROVED). The PC test does not run the cutter, so the 25n MN + NY test (0d015ade5a34) still stands for matching; kit 25o later.
  **Graded PASS 9:42 AM CT, no must-fixes.** Before any real cut: kpc_store_attrs, the key and the cut from ONE layer download.
- **PC test 9:11 AM (kit 25n):** MN built: outlines 315 -> 294, 17 parks pin only, 2,500 rows of 93 parks left the map. SUSPECT: whole
  state parks (US-2485, US-2520, US-2483, US-6463, US-12388) lost rows that match by name + acres on complete layers; most are sgmne
  pieces. Next: read the MN fresh layer files (needs the owner's OK for the store folder). NY held: sgnyd (Catskill) 0 records.

- **Round 10 (1f6e839, ~10:40 AM CT; grade R1-R7 after the 9:11 test, pre-approved; owner 9:50 AM pick 'Two sources agree'):** R1 agency
  record ids, R2 rough outlines by grid points, R3 two fits by shared ground, R4 old joined size + two official sources at park level, R5
  district tracts from the layer file, R6 row-proof.csv. US rules -> **3d367d4d143f** (NOT YET APPROVED). KPC-Store #38 75cfb48: R7 hand
  downloads (layer-files\hand\<area>\<layer>\). Kit **25o** + the new LAYER-RECORDS on the PC, read back equal. Not graded yet.
  Owner next: Catskill file into the hand folder, LAYER-RECORDS 1 + Y, START-HERE MN NY (report must say US 3d367d4d143f).

- **Round 11 (f119a34, ~10:35 AM CT; graded PASS 10:31 AM, no must-fixes): grade of round 10 = FIX S1 + S2, both done** (rough edge allowance capped + half strictly inside;
  old land from the old copy only). US rules -> **57cffee74bdd**. Kit **25p** on the PC, read back equal. Catskill (Nov 11 DEC file
  from D:\DOWNLOADS!) is in layer-files\hand\US-NY\sgnyd\; the owner says a newer download exists somewhere: newest file there wins.

- **11:27 AM MN gap 'sgiaa 0 of ?' (KPC-Store 839ce5e, on the PC, read back equal):** LAYER-RECORDS read only links\\data\\us-key,
  which each key test rewrites; it now also reads key builder files\\originals, counts saved joins, never drops a downloaded
  layer, warns on a layer with no address, and ends with a layer / source / stored / complete list. Round 12 (8c2bc3d, kit 25q,
  US 8ec9ea21fa07): district tract rows are code rows. Owner next: LAYER-RECORDS 1 + Y, then START-HERE MN NY.

- **Round 13 (d8a73e9 + 3aa6a48, ~12:15 PM CT): saved answers are hints only (owner 12:07 PM 'Delete any holds they maybe wrong
  idk.'; switch KPC_SAVED_HINTS_ONLY, MN NY). US rules 698b0126ee4f, changelog APPROVED (owner 12:09 PM: 'no need to ask about a
  ducking number changes I do not have to approve you all to fix this.'). Kit 25s on the PC, read back equal. The other builder
  grades and merges after the owner's MN/NY PC test. Never ask the owner about hashes, holds or parks.

- **Round 14 (b23214b grader + ab6b118 data, ~2:30 PM CT): US rules 03c3525be24b.** state-gis.json NY entry 3 (sgnyc) = APA
  BluelinePolygon (fixed name 'Adirondack Park'). KPC-Store 544ca01 on the PC (read back equal): layer-url-overrides.csv (sgnyc),
  verified row fetch yes / publish no, an old-address file is downloaded again. Kit 25u on the PC. Owner next: LAYER-RECORDS 1 + Y
  (downloads only the Adirondack polygon), START-HERE MN NY expecting US 03c3525be24b.

- **FS hand pieces (25 Nov ~3 PM):** the owner's 4 Forest Service geodatabases converted, cut into the 62 missing state/layer
  pieces (fsod sggad sgidd fwsr wld sgnvg) as .geojson.gz in the store's results\layer-files\hand\<AREA>\<layer>\; KPC-Store
  8f6bc39 (gzipped hand files) on the PC, read back equal. LAYER-RECORDS 2 + Y loads them.
- **Round 15 (d2c166c, 25 Nov ~4 PM): US rules 3438197bf50b, kit 25v on the PC (read back equal).** From the 2:28 PM MN NY test
  (03c3525be24b: 1,129 outlines vs 1,145; MN US-7145 Minnesota Valley SRA lost 339 pieces; check rows 426 -> 1,424):
  (1) store attrs read the layer's own acres field (first field with 'acre': MN DNR su_acres), format 11 (fresh MN parcels were
  sized by their section-level outline); (2) with KPC_STORE_FRESH the website key's rows (t915u carry, keep-last-good) follow
  the proven alias (fresh_old_parks), unproven = '~old' hint, D1 number check off (419 MN D1 check rows + ~74 'place' rows came from
  shifted row numbers); (3) R4 old size like with like when the website 'ac' = its rows added up (twins counted both sides or
  neither; 7145: ac 6,226 counted 49 twins, fresh sum left them out); (4) row-proof 'left the map' read after the gate.
  Left for later: NY US-2137 Schunnemunk Mountain SP (records say 'Schunnemunk State Park': name rule misses 'Mountain'), US-8319
  Palisades (old land included 'Palisades Park' 2,218 ac), MN US-2506/7148 (one PAD-US record, two POTA parks), the hint records'
  same-land step (~21 of MN's 49 minutes, the last ~480 records), MN wsrc listed 'not in store' though its file has 4 of 4.
- **25v test (4:32 PM) + the bad website copy (25 Nov ~5:30 PM):** MN check rows 1,136 -> 713, D1 rows gone; US-7145 still pin
  because the PC's originals\US-MN.json / US-NY.json were a key a TEST built ~7:30 AM (match_checks block; 290 MN / 836 NY parks
  differ from main 90e4014e; 7145 ac 8,300 vs 6,226). Restored from main (md5 read back), bad copies kept as
  originals\old-US-*-test-copy-nov25.bak. All 66 originals now match main's sha256. Owner rerunning MN NY on 25v.
- **Batch 16 (branch prep/batch16-nov25 off #380, NOT on #380 until the rerun is graded): US rules 8f54b4480d28.** (1) published
  key record ids use the agency's own id where every record has one (sgmne su_id, sgmna uniqueid): kpc_store_attrs.publish_keys,
  used by the store reader, kpc_outlines_from_key and kpc_outline_score; no agency id / a shared one = the row spelling;
  store_fields never finds an agency-keyed record ('_agk') by a row number; id file format 12; (2) _sane_ac on fresh acres;
  (3) KPC_KEY_ONLY_PARKS through fresh_old_parks; (4) kpc_test_keys: originals is READ ONLY, checked against the kit's
  links\.kit-website-keys\sha256.json (tools/pc-keys/make_kit_website_keys.py), a bad copy = that state NOT BUILT with one line;
  no built-files.json / marker in originals any more. Tests: test_batch16_nov25, test_pc_kit_nov24 (rewritten K4 part).
  Pre-existing fails (same before the batch): test_keys_store_mode_nov16 (2), test_pin_outlines_parts_nov11 (3).

## The rules now (owner's words 25 Nov)
- 6:20 / 6:28 AM: match by proof from fresh data: agency (unit) id, then shared ground (80% / 50%; piece 90% with a shared name),
  then real name + size within 10%; never a row number; unproven = POTA pin + "code to fix", no hand-offs to the reps.
- 7:18 AM: today's store records are the FRESH source; old saved copies are hints only.
- 8:21 / 8:48 AM ("simplest path"): the PC downloads every WHOLE layer the keys join; those **full layer files**
  (`results\store\<area>.layer-records.json.gz`, with a per-layer manifest: source count, saved count, complete) are the only fresh
  source. The park-by-park store is no longer the source of truth. A key build for an area **stops and lists the gap** if any joined
  layer is not complete. US + Canada now; world on hold.
- 9:07 AM: allow the NY Catskill boundary (US:sgnyd): read for matching only, never published (DEC terms forbid redistribution).
- Switches KPC_SAME_LAND, KPC_PROVEN_ONLY, KPC_STORE_FRESH: on for MN and NY only. Kentucky later (its own handling).

## Owner's PC (all byte-checked)
- Key test kit: `D:\KPC GITHUB TOOL and MOre\key builder files` (START-HERE.bat adds every kpc-kit-update zip once). Latest: **25n**
  (rules 0d015ade5a34). Reports: `reports\test-<date-time>\REPORT.txt` + lists (pin-only-parks.csv, saved-answers-moved.csv,
  rows-kept-but-listed.csv, layers-not-complete.csv, layers-not-in-store.csv, saved-answers-no-fingerprint.csv).
- Store tool: `D:\KPC GITHUB TOOL and MOre\Tools\KPC-TOOLS-NOV14\1-STORE-TOOL\kpc-outline-store-full` (engine with G4; old copy kept as
  `kpc_outline_store.before-g4.py`; `kpc_layer_records.py`, `LAYER-RECORDS.bat`; verified-layers.csv has the Catskill row).
- MN + NY whole layers downloaded 8:47 AM: MN all 10 layers complete (fws 1,768 of 1,768); NY complete except sgnyc (107 records, none
  with a polygon or id: not joined) and sgnyd (Catskill: allowed at 9:07, to download).

## What the owner is doing now
1. LAYER-RECORDS.bat -> 1 (MN + NY) -> Y (downloads only Catskill).
2. START-HERE.bat -> report must say US 0d015ade5a34 -> `MN NY`.
Expected: MN builds (all joined layers complete); NY builds once Catskill is complete. Read the new `reports\test-...` folder.

## Next jobs, in order
1. Read the MN + NY test: pin-only parks and why, saved answers moved, rows listed, gaps. Send counts to the owner (copy-paste block
   for the reviewer; the owner prefers paste-ready messages over zips).
2. One grade of #380 round 8 (+ a0b1a4b2) by the other builder; the owner reviews #38.
3. Open items the grader or owner raised: S2 (confirmed parks keep all their name rows: owner's call), the "kept by name and official
   size" count (0 so far: report says why), the GitHub boundary-rebuild workflow needs the layer files before it may run (it would HOLD).
4. Then, only on the owner's word: LAYER-RECORDS for every US + Canada area (choice 2, many hours), switches on for more states,
   the owner's quoted OK on the rules line (marks APPROVED), merge.

## The move to the new PC (owner 25 Nov 9:15 AM: "We come back to that tonight")
- Not started. The plan is on his PC: `D:\KPC GITHUB TOOL and MOre\Tools\MOVE-PREP\MOVE-LIST.txt` (24 Nov; he said yes at 8:02 PM):
  about 29 GB to copy (Layers-TIDY 19.4 GB, the US store 4.4 GB, the world store 2.3 GB, page reader, ID crosswalk, trace test, test kit
  basics); download fresh on the new PC (repos, links, park facts, Python 3.12 + packages); leave old kit zips and old tool copies behind
  only after the new PC passes its checks. Nothing on the old PC is deleted first. BACKUP-TO-DRIVE.bat and MAKE-LAYER-GUIDE.bat are there.
- After the move: heavy work on the PC (store rebuilds, LAYER-RECORDS downloads, key builds once the hold is lifted, 2-fers, trace test,
  page reader); GitHub keeps the website, posts, small feeding bots and the keeper's light nightly check. Each move needs his OK.
- GitHub size clean-up comes after the move, its own GO: full backup first, then old branches, then a history reset one repo at a time.
- NEW since the list was made: the full layer files (results\layer-files + results\store\*.layer-records.json.gz) live in the US store
  folder; they move with it (or are downloaded again by LAYER-RECORDS.bat).

## House rules that bit today
- Never push to main (branch + draft PR; author KPC owner, message ends "KPC owner, <date>", no trailers).
- Touched tests only, Python 3.12. Rule changes need the owner's quoted OK; data/** only with his OK for that exact edit.
- The device bridge sometimes delivers an OLD copy: stage it back and compare md5 every time; resend under a new output folder name.
- A PC run started before a kit lands uses the older kit: check the rules line at the top of REPORT.txt.
