# Hand-off for the next Fable: finish the matching tools (27 Nov 2026, 4:45 AM CT)

You manage this job. The owner (Brandon, KZ4CP) asked Fable to manage, give work to Sonnet and Opus where it helps, review
their work, and make it better than planned. Plain words, short reports. He is a ham, not a programmer.

## Read these, in this order (branch `feat/us-key-v2-nov26`, KPC-Links draft PR #393, head after this note)
1. `.claude/notes/handoff-us-key-v2-nov26.md`: sections "Added 26 Nov night" and "Added 27 Nov".
2. `.claude/notes/rule-sheet-us-key-v2-nov26.md`: sections 13 to 15 (his rulings).
3. `.claude/notes/net-rules-nov26.md` (the site rule), `audit-tools-nov26.md`, `audit-facts-nov26.md`.
4. His report of every bad finding (keep it up to date when a row changes): https://claude.ai/artifact/QpFeqpJkCUoxgjmazB6gNF

## Where the work is
- v2 matcher, rule table, PC tools, tests: PR #393. v1 is untouched, no rules hash moved, nothing merged, nothing live.
- His PC is the MASTER COPY of two fixed tools that are NOT in GitHub yet: `C:\KPC\3-MAP-STORE-US-CA` (store room, 49 tests)
  and `C:\KPC\6-TOOLS\PAGE-READER` (page reader, 34 tests). The v2 kit is in `C:\KPC\5-ANSWER-KEY-TEST`.
- Old copies on the PC: `*.before-nov26-fix.*` (before Fable's fix), `*.other-builder-nov27.*` (another chat's version).

## Jobs left, in order
1. **Get the two PC tools into GitHub as draft PRs** (KPC-Store for the store room, KPC-Data for the page reader). Stage the
   files from the PC, never from GitHub. Another chat (KPC-Data draft PR #202) overwrote one fixed file from an old copy on
   27 Nov at 4:20 AM; it is merged now, but it will happen again until the PRs exist. Tell that chat what you do.
2. **Read his results.** After LAYER-RECORDS choice 2: `C:\KPC\3-MAP-STORE-US-CA\results\STORE-ROOM-STATUS.txt` (expect about
   22 areas with a real gap, no `trl` rows, Vermont clean). After V2-BUILD: the reports folder in `5-ANSWER-KEY-TEST`.
3. **Trails.** The keys' `trl` is `file:data/trails/US-{n}.json` (one line file per park, made by the trail bot), not a web
   layer. Find where those files live (not in KPC-Links main; look at `.github/scripts/kpc_us_trails.py`,
   `data/trails-layers.json`, `data/trails-hand.json`, and KPC-Data). Make the store room read them into the layer files as
   line records (`paths` + `"shape": "line"`); v2 already reads lines (rule sheet section 12). 21 MN + NY parks wait on this.
4. **The park facts builder** (GitHub, KPC-Data): `audit-facts-nov26.md` F1 to F16. Drop the old-key input, km2 guard, bad
   pins, Kentucky ids, freshness stamp, keep the page reader's new fields. Then a PC button to build the facts there.
5. **After his next page reader run:** rebuild the park facts, rerun v2 (the numbers so far use 24 Nov facts).
6. **Small v2 jobs (table rows + tests):** "other spellings" (US-0474, US-2147, US-4239); `name_fields` rows for Alberta
   and BC (PLUZ_NAME, PLREC_NAME, ParkName, PROTECTED_LANDS_NAME); licence counts on the scorecard and build summary; the
   prep tool compares web addresses letter for letter (scheme / www); one front-door button for the whole chain.
7. **Page reader, open:** 355 parks whose saved page is another park's page; the buttons do not ask for Python 3.12.
8. **For his eyes:** GA US-9795 Sandhills; the list `v2-id-other-names.csv`.

## Already ruled: do not ask him again
- Easements off by name; Lake Vermilion both pin only; the fair count stands (26 Nov).
- v2 is not a test version; US and Canada; everything stays on the PC until proven (26 Nov).
- Only a real robots.txt Disallow line is a "no". A 401 / 403 is that page or layer only; 5 in a row or one 429 stops the
  site for the run; nothing is carried into the next run (26 and 27 Nov). A bot-check page at robots.txt = no rules.
- Hectares and km2 become acres; French and mixed names match; licences: private use yes, sharing no (26 Nov).
- A points-only layer is nothing to wait for (27 Nov).
- Never ask about a hash, a hold or a park. Never ask him to rerun something to see.

## Traps that cost time
- The bridge will not write into `links\.github` on the PC. Put files beside the buttons.
- Every PC write: stage the current file first, compare it with what you last delivered, write with `expectedMtimeMs`,
  stage it back and `cmp`. That is how the other chat's overwrite was caught.
- Do not run a bot script with a flag it does not have: `kpc_docs_bot.py --selftest` started the real program.
- Bash here has no network and must never reach an agency server. Agents run no git. One Python (3.12).
- `.bat` files and part of the page reader README are CRLF: edit them as bytes.
- Check agents' numbers against the files before telling him. Fable told him trails were fixed when they were not.
- GitHub: NO BUILDING, branch + draft PR, author `KPC owner`, message ends `KPC owner, <date>`, no trailers.
- `PAGE-READER.bat` first asked with `set /p` and a typed answer; on his PC typing 2 or 3 only printed the menu again (cause
  not found; the file was clean CRLF). Changed 27 Nov 4:58 AM to one key press with `choice`, the way `LAYER-RECORDS.bat`
  asks and works. NOT YET CONFIRMED BY HIM. Buttons cannot be tested here (no Windows): keep to patterns already proven on
  his PC. Never replace a `.bat` while its window is open.
- 27 Nov about 4:50 AM, his words: "i built us tables ran 50 state v2 did layer record bat did 0". So V2-STATE-PREP, a
  50-state V2-BUILD, LAYER-RECORDS and 0-INSTALL-PAGE-BROWSER have run: read those results first.

## Done 27 Nov, 4:45 to 6:00 AM (Fable as manager; Opus and Sonnet built, Fable checked every number against the files)
- **Job 1, DONE.** Store room: KPC-Store draft PR #39 (on top of #38), the PC copies byte for byte, PC buttons in `pc/`, 49 tests
  through `tests/test_layer_records_nov26.py`; the older nov25 test brought up to the new tool (no check removed). Page reader:
  the other chat's KPC-Data #202 already holds the PC copies (compared byte for byte at 4:50 AM, 34 tests pass), so no second
  PR; that chat was told on #202. Since then `PAGE-READER.bat` changed on the PC (4:58 AM, `choice`): #202 has the older one.
  Not brought over: `verified-layers.csv` (PC and GitHub differ in 199 lines of licence answers), `fetch-settings.json`.
- **Job 2, DONE.** His rebuild finished 4:48 AM with the fixed tool: 66 areas, 58 whole, 8 with a gap, no `trl` rows, Vermont
  clean. Real gaps, 12 layers: CA-AB SK-ALL Gover and CA-YT Yukon parks (no usable records), CA-ON Hard look~16 (timed out),
  US-CO sgcod and US-FL sgflc (HTTP 404 incomplete), US-MS mszp mszw (never downloaded), held by a club host rule: CA-ON ON-CH
  Conser, US-AZ sgazb sgazc, US-ID idw. `sgaki`, `sgutc`, `sgwae`, CA-NL are whole now. His 50-state v2 build is from 26 Nov
  10 PM (`v2-keys\2026-11-26-220019`), before this rebuild: 24 of its 51 "store gap" flags are mostly `sgaki`, now whole.
- **Job 3, BUILT, NOT ON THE PC.** KPC-Store draft PR #40 (on top of #39): the store room reads KPC-Data `data/trails` from a
  folder `trail-files` beside the tool (or `--trails`) into line records; 56 tests; with v2 on today's files MN 295 -> 305,
  NY 819 -> 821, only trail parks change. HELD for two findings: (1) the name inside a trail file is typed in the trail bot's
  list (`kpc_us_trails.py` writes `x['name']`), not read from the agency record, so "exact name" is no second proof there:
  ASKED THE OWNER whether the trail bot's pick plus the pin within 100 ft is enough; (2) US-11151, US-11154, US-9382 took their
  line with the pin 46 to 92 m from it (the line came along with the park's land in the name step): close that in v2 first.
  Also open: Canada's 30 trail files, a licence for trail lines, 7 pins 34 to 86 m from their line.
- **Job 4, DONE as draft.** KPC-Data draft PR #203: the park facts builder (old key out, km2, bad pins, Kentucky ids, freshness
  and a shrink stop, page reader fields kept; `page.names` stays plain strings as #201 and `page_names_land` read it) and
  `PARK-FACTS-BUILD.bat`. On the PC in `5-ANSWER-KEY-TEST` (button, README, `park-facts-tool\`), NOT RUN THERE YET. Next, small:
  the workflow line (drop `--key`, add `--previous`). The page reader's new fields were tested on made-up pages only.
- **Job 6, DONE** (#393, on the PC, 10 files read back equal): other spellings (NY gains US-0474, US-2147; MN unchanged;
  US-4239 on made-up records only), name fields for Alberta and BC Parks (AB nameless 231 -> 3, BC Parks 929 -> 0; 42 BC parks
  change size by over 10%: look before BC is used; `BC RegionalP` needs `parkname`), licence counts, address compare, and
  `V2-FRONT-DOOR.bat` (asks with `choice`; not run on a PC yet).
- **New findings.** MN licence counts on today's file are 138 all / 97 part / 60 none (the notes said 217 / 78 / 0): all 6,712
  `sgmnf` records are now private ("NO TERMS STATED"). ND is 96 of 155 on today's files (was 93).
- **Still open:** jobs 5, 7, 8; the report artifact has not been brought up to date with the lines above.
