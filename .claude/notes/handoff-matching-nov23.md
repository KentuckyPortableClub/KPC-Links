# Hand-off: matching and accuracy (Fable, 23 Nov 2026 6:45 AM)

Owner 5:53 AM: "put in the report to make a hand off for opus once they make changes so we can update pc version to reflect ... lets make this thing work great ... tired of having issues after issue".
The owner's own write-up (plain words, all numbers): Claude doc "KPC matching and accuracy: everything I can do", 23 Nov. This note is the working copy for the chat that builds next. Counts only; no park is named.

## Where things stand

- On main: US rules `bdb245566558` (W4 page name, W5 map-link name, W-G10, W6 county; KPC-Links #350 #351). KPC-Data #176 to #185 (reader, kept pages, town + county points, park facts 10).
- DRAFT, waits for the owner's word: KPC-Links #352, rule W7 "the same land counted once" (US rules -> `e8b9c526e1f6`).
- The owner's PC: tonight's read ends about 10 AM CT, then he runs `2e-REREAD-KEPT-PAGES.bat` and uploads the pack. Park facts on KPC-Data are rebuilt from it. Until then the page facts are the 22 Nov ones.
- NO BUILDING stands. Tests and counts on the PC and in a workspace only.

## What the PC test of 22 Nov 11:49 PM shows (reports on the PC: `key builder files\reports\test-2026-11-22-2349`)

US, 49 states + DC: 13,118 parks; outline 11,547 (website 11,602); check rows 21,238 (website 14,618); 6,065 confirmed, 5,071 outlined and not confirmed, 95 pin only of 11,231 joined; 1,048 parks lost a record; 97 outline to pin.
Canada: 5,900 parks, 4,379 with an outline, 1,139 nothing found, NO second-witness checks at all. Kentucky 193 of 193.
Other counts in the logs: pin outside the joined land 2,296 of 11,547 (19.9%); saved answers not found 323 (MI 76, WI 74, UT 57) + 64 two fits (WI); wetland districts 0 of 22 joined to their tracts (not in the saved copies); 142 parks with no union acreage; closed-land joins 627 in 225 parks (ME 468).

Check rows by cause, counted on the saved website keys with today's rules (`kpc_match_checks_count.py`): 6,961 rows. Size 56 parks (about 4,260 rows, 3,928 of them the W7 fault, all Wisconsin). Place 538 parks (about 1,900 rows, not broken down). Agency 481 parks (about 790 rows). Name, national, id, map link: 36 parks.

Agency rows, by the pair "link says -> record says": FWS -> STATE 191 (NC 79); STATE -> USACE 154; STATE -> LOC 145 (OR 111); STATE -> FWS 46; STATE -> PVT 33 (MA); NPS -> STATE 27; STATE -> BOR 27; STATE -> DIST 26; STATE -> BLM 25; STATE -> TVA 16.
- OR 111: national-list records with Mang_Name CITY while Own_Type is STAT and Loc_Mang is the state parks department; the link is the state parks site. A label fault inside the record.
- STATE -> USACE / BOR / TVA 197: a state park on federal reservoir land (107 of the USACE rows are layer `sgide`, the rest national-list records with a Corps district as local manager).
- MA 33: Own_Type STAT, Mang_Name PVT (an operator or a utility).
- NC 79: the records are the state's game-lands and natural-heritage layers. Probably other land; look before changing anything.

## Update 23 Nov 7:15 AM (owner 6:42 AM: "Yes on all but 5 they has to be a better solution")

- MERGED on his word: #352 (W7). Main US rules `e8b9c526e1f6`. PC kit update 23b sent and read back equal: his next report must say `US e8b9c526e1f6, Canada c978f75b94fe`.
- DRAFT, waits for his word: #353 (W-G11 owner label, W-G12 state park on federal lake land). US rules -> `c6f3a95b1018`. After the merge: PC kit update "c" (job 1 below, same steps).
- W-G6 YES (a "near a town" point counts): build after the upload (job 11).
- Jobs 5, 8 and 9 below are NOT approved as written. Better ways for 5, counted on the saved keys (no list for a person, nothing downloaded):
  - **Pins outside the land** (2,222 of 11,098 parks tested): 1,161 are already confirmed by another proof (link 838, id 171, size 94, page name 58). Of the 1,061 not confirmed, 679 are within 500 m of the land (a gate or office pin). That leaves 382, and only 147 are over 2 km (36 over 10 km). 471 of the unconfirmed have no own page read, 530 an own page with no point: the 23 Nov read is what settles them. Recount after the upload; only the leftover number goes to the owner.
  - **Wetland districts** (22 parks): 16 already have an outline on the website key (1,989 rows, layer `fws`) and keep it (last good outline). 6 are pin only. The saved copies already hold 897 records naming a wetland district or waterfowl production area (fws 393, padus 422, state layers 82). So: look whether the 6 can be joined from what is saved before anything new is fetched.
  - **Canada**: no Canada rule sheet. Point the US proofs the owner already ruled (id, link, size, page name, page point) at the saved Canada keys as a COUNT first; bring him the number; switching it on is then one yes (the Canada hash moves, so still a draft PR).

## Jobs, in order

| # | Job | Where | Waits for |
|---|---|---|---|
| 1 | PC kit update "b" after #352 merges | steps below | owner: "merge 352" |
| 2 | Agency check reads Own_Type and Loc_Mang, not only Mang_Name (144 rows) | `kpc_match_checks.py` `record_agency` / `agency_check` | owner's ruling 1 (W-G11) |
| 3 | State link against USACE / BOR / TVA record: no agency vote when the names agree (197 rows) | same | owner's ruling 2 (W-G12) |
| 4 | Place rows: split by which place test fired, by state | count only | nothing |
| 5 | Pins outside the land: a sorting report (distance bands, confirm state, what the page says) | compare only; output on KPC-Data branch `tools-out`; the count is printed by `kpc_us_key.py` ("Boundary check") | owner's yes |
| 6 | Maryland: 11 parks whose outline is under a third of the agency's figure (they drop to a pin) | count only: which witness gave each figure | nothing |
| 7 | Saved answers that no longer find their record (323 + 64) | read key-quality.md on saved answers first | nothing |
| 8 | Second-witness checks on the Canada key | rule sheet, count on saved Canada keys, draft PR (Canada hash moves) | owner's yes |
| 9 | Wetland district tracts (22 districts) into the keeper's list | KPC-Store; the keeper is the only fetcher | owner's yes |
| 10 | Site-by-site finders for the low-confirm states (NY 679 unconfirmed, PA 325, MI 304, OR 298, UT 296) | KPC-Data reader; re-read kept pages with `--reextract` | the upload |
| 11 | W-G6: a "near a town" point as a place witness. RULED YES (owner 23 Nov 6:37 AM). Rule sheet line, count, draft PR | `kpc_match_checks.py` | the upload (the points come from the 23 Nov read) |

Every key rule change: a rule sheet line (mapping.md, rule sheet W) first; a test that fails without the fix; a scope entry in `.github/us-key-rule-scope.json`; a changelog line at the TOP of `docs/key-rules-change.txt` holding "<old hash> -> <new hash>" and the words "APPROVED, decided_by KPC owner" (the preflight looks for both); a count before and after with `kpc_match_checks_count.py`; a draft PR; merged only on the owner's word. Say whether a shared helper changed. Python 3.12 while working: the touched tests, `tests/run_match_tests.py` (73 of 73), `kpc_preflight.py --quick`.

## After every merged change: bring the PC up to date

The PC test kit is `D:\KPC GITHUB TOOL and MOre\key builder files`. `links\` is a full copy of KPC-Links; `START-HERE.bat` adds every `kpc-kit-update-*.zip` in the folder once (marker `links\.done-<zip name>`); `kpc_test_keys.py` prints the rules numbers, the park facts date and the kit updates on the first lines of every REPORT.txt.

1. Key rules: from main take every file in `kpc_key_freeze.RULE_FILES` for us-key, ca-key and world-key, `.github/key-rules-version.json`, `docs/key-rules-change.txt` and any other changed file under `.github/scripts`. Write them under `links/` in `kpc-kit-update-<yyyy-mm-dd><letter>.zip` (add `links/.kit-main.txt` with the commit and the three hashes).
2. Send the zip through the device bridge. Wait 20 seconds, stage it back, `cmp`. The bridge sometimes delivers an old copy: send again if it differs.
3. Proof: the owner double-clicks START-HERE.bat; the report's first lines must show the same numbers as `kpc_key_freeze.rules_hash` on main.
4. Park facts: after KPC-Data rebuilds `data/park-facts.json.gz`, put it at `key builder files\park-facts.json.gz` the same way (the report prints its made date and tool).
5. Reader and converter: KPC-Data `.github/scripts/kpc_park_pages*.py` -> `Tools\KPC-PC-BOTS-NOV21\page-reader\scripts`; `.github/scripts/pc/kpc_geocode_addresses.py` -> `Tools\KPC-PC-BOTS-NOV21\tools`. Never while a run is going; never touch `RUN-OVERNIGHT.bat` or `state.json` during a run.

Kit update 23a (23 Nov 6:20 AM, read back equal): main `fcc99a90b` rules, plus three inputs the GitHub build has and the kit did not: the Recreation.gov saved copy (`links\data\access-leads\keyed-pull-raw.json.gz`, missing in all 50 state runs of 22 Nov), Canada's official pins file (`links\.op\data\intake\official-pins-nov12.json`, `KPC_OFFICIAL_PINS`), and `data/acres.json` made fresh from the park facts as the workflow does.

## Things that cost time

- `import kpc_us_key` RUNS the builder (it wrote `data/us-key/index.json` once). Use `python -m py_compile`, or lift one function out with `ast`.
- The saved copies (`cache/us/US-XX.json.gz`) hold shapes under `_r`; the builder turns them into `_g.rings`.
- A park's `ac` is a true union only when it has no `ac_how`. `ac_how: measured` was a plain sum of every row until #352.
- GraphQL is closed to these sessions: open a PR with `gh api repos/<owner>/<repo>/pulls -f title=.. -f head=.. -f base=main -F draft=true -F body=@file`.
- Never list the whole `links` folder on the PC (a full copy of the website).
- `git fetch` in an old KPC-Data clone can sit in auto-pack: read single files with `gh api repos/.../contents/<path>`.
