Finished the pre-grade on all five open PRs and the loose-ends research. Here's the scorecard, the big catches, and one paste-ready handoff for the builder.

PR Grades (nothing merged)

- KPC-Links #393 (https://github.com/KentuckyPortableClub/KPC-Links/pull/393) ("f1090e39"): YES as a draft — all 7 v2 test suites pass on Python 3.12; waits on grading today's PC build ("v2-keys\2026-11-27-080935") before merge.
- KPC-Store #39 (https://github.com/KentuckyPortableClub/KPC-Store/pull/39) ("f563a0a6"): YES — CI green on 3.12 and 3.13 (brings "#38" with it).
- KPC-Store #40 (https://github.com/KentuckyPortableClub/KPC-Store/pull/40) ("fa6bb406"): NO (needs fix) — CI red on "test_layer_records_nov25.py" line 168 (old test still expects Adirondack "sgnyc" BluelinePolygon to be private; your "use it unless" rule flipped it to share).
- KPC-Data #202 (https://github.com/KentuckyPortableClub/KPC-Data/pull/202) ("9e6c6990"): YES — 40 + 9 tests pass; sits on "#201" and replaces "#200" (close "#200").
- KPC-Data #203 (https://github.com/KentuckyPortableClub/KPC-Data/pull/203) ("2b95d371"): NO (small fix) — 49 + 6 tests pass, but conflicts with "#201"/"#202" in "kpc_park_facts.py" and still needs the one-line workflow edit.

Big Catches (saves you work & risk)

- Don't hand-download "US-AZ sgazb"/"sgazc" or "US-ID idw" — their terms forbid bulk download/copying. Leave them pin-only unless the agency gives written permission.
- "CA-ON ON-CH" needs no hand download — it's public (8 records, no sign-in) under OGL–Conservation Halton (shareable with credit).
- Other store gaps solved: "US-FL sgflc" moved from "/MapServer/0" to "/MapServer/1" (284 records); "US-MS mszp"/"mszw" are already local files in "KPC-Links" ("data/us-key/zip-ms*.json"); "US-CO sgcod" has a 924-record CPW candidate ("PropertyFinder_Map/MapServer/47", licence needs a read); "CA-ON Hard look~16" answers 1,261 records (retry smaller pages); "CA-YT" answers 27 records ("fetch=no" in list).
- Trails 100 ft rule is verified clean ("99.9 ft" joins, "100.1 ft" drops; bot-typed names are never used as proof). The earlier "151–302 ft" alarm was a misread (those 3 MN pins are 72, 89, and 31 ft from their lines). Trail licences are still missing (398 of 457 trail files don't record their source URL, so every trail line is currently marked private).
- Licences: 24 "no" rows in "#40" rest on silence, not restricting words — 23 can flip to share (keep "ON-NPCA" held; check "sgaki", which is federal public domain yet marked "no").
- GA Sandhills ("US-9795" / "US-7914") solved: West "US-9795" = "sggaa90"/"sggac821" (2,484 ac vs. 2,498 ac GA DNR, pin inside); East "US-7914" = "sggaa34"/"sggac768" (872 ac vs. 892 ac GA DNR, pin 66 ft from edge).
- Reason-code note: "handoff-graders-nov27.md" had it backwards — the live v2 code does have "park_has_no_pin" and does not have "layer_not_complete".

Paste-Ready Handoff for the Builder

KPC — FIXES FROM 27 NOV PRE-GRADE (all drafts; no merge yet)

1. KPC-Store #40 (fa6bb406) CI RED: tests/test_layer_records_nov25.py line 168 still asserts BluelinePolygon sgnyc publish = "no"; the "use it unless" rule made it yes. Update that test, run the WHOLE suite (python3.12 tests/run_all.py), and update the PR title/body (trails are on PC now).
2. Trail licences: every trl line is currently private because 398 of 457 data/trails files carry no source URL (index.json only names 52 sources as plain text). Have the trail bot write the source layer URL into each file, add those URLs to engine/verified-layers.csv under the "use it unless" rule, and read Canada's 30 trail files.
3. Licence list (#40 copy): 24 "no" rows rest on silence, not restricting words (15 no evidence link, 5 unread: sgutc bsna ON-GANA ON-CH ON-NPCA, 4 "not a park layer" incl. sgaki = federal public domain). Flip all but ON-NPCA (sibling says Restricted), reconcile with the PC's "26" list, and confirm which file is the master.
4. Store-room layers:
   - ON-CH: public item f5ef7d87ccef45f4a0de9c0e4548c39f (8 records, no sign-in, OGL–Conservation Halton). Allow through host rule, set OPEN + attribution. No hand download.
   - sgflc: update URL to .../Wildlife_Management_Areas_Florida/MapServer/1 (284 records; layer 0 = 404). Check sgflg on the same service.
   - mszp / mszw: already local in KPC-Links (data/us-key/zip-ms*.json) — copy into hand/US-MS/ or read file: layers from links like trails.
   - sgcod: High_Priority_Habitat_2026/MapServer/9 is 404; check licence on candidate ndismaps.nrel.colostate.edu/.../CPW/PropertyFinder_Map/MapServer/47 (924 records).
   - Hard look~16 (1,261 records): retry with smaller pages. Yukon: answers 27 records but marked fetch=no — decide. CA-AB SK-ALL: mark "no records in area", not a gap.
   - sgazb / sgazc / idw: terms forbid bulk download/copying — do NOT hand-download; leave pin-only unless written permission.
5. KPC-Data #203: resolve kpc_park_facts.py conflict with #201/#202 by keeping #203's copy; update .github/workflows/kpc-park-facts.yml line 65 (drop --key/--layers flags and unused KPC-Links sparse clone, add --previous data/park-facts.json.gz) and rerun test_park_facts_workflow_strict_nov20.
6. KPC-Data #200: close as replaced by #202. Merge order once ready: #201 -> #202 -> #203.
7. Page reader 355 parks (audit F14): build the page URL from the park's own agency link ID, refuse redirects whose final ID doesn't match, then re-read those 355 (--reextract --refs-file).
8. #393 cleanup: fix handoff-graders "Open 7" (v2 HAS park_has_no_pin and has NO layer_not_complete), refresh the PR body, add a CI job running the v2 test suites, and track open fixes (NY US-10076 51 vs 44 ac, BC 42 parks >10%, far-pin trail reason).
9. GA Sandhills split: add table rows for West US-9795 (sggaa90/sggac821, 2,484 ac vs 2,498 ac GA DNR, pin inside) and East US-7914 (sggaa34/sggac768, 872 ac vs 892 ac GA DNR, pin 66 ft from edge); verify gate passes.

Ready to merge KPC-Store #39 (https://github.com/KentuckyPortableClub/KPC-Store/pull/39) and KPC-Data #202 (https://github.com/KentuckyPortableClub/KPC-Data/pull/202) whenever you want, or wait until the whole bundle is green — and ready to grade "v2-keys\2026-11-27-080935" as soon as you give me PC read access (or drop the files here).