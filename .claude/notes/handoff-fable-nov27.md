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
