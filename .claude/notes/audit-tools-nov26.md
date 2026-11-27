# Audit of the two data tools: the store room and the page reader (26 Nov 2026)

Read and measure only. No tool file was changed. No git. Nothing was sent to any server. The only code run was
`kpc_layer_records.py --selftest` (ALL PASS) and four tiny offline checks on made-up records
(`/home/claude/v2work/scratch/audit/fixtures.py`). Measurements: `scratch/audit/measure.py` and `scratch/audit/facts.py`
on the real files in `/home/claude/v2work/data/`. The yardstick for "parks gained" is the matcher's own output
(`out/m7-warm/v2-pin-only.csv`: MN 28 and NY 32 pin-only parks) and the 14-state prep run (`out/prep-all/v2-prep-US-2026-11-26-211025`).

## 1. The two tools

**The store room** (`store-tools/`). `kpc_layer_records.py` (697 lines) downloads each whole map layer the keys use and
writes `<AREA>.layer-records.json.gz`: a manifest (per layer: the layer's own count, the records kept, complete yes or no,
why) and the records (key, name, all attributes, rings in whole-number steps). It does not have its own network code.
It borrows the older park-by-park engine `kpc_outline_store.py` (10,914 lines, 482 functions, one file) for settings,
packs, host rules, robots.txt and the one request function (`Net`). Its paging, object-id choice, ring reading and
completeness test are its own: it re-wrote them instead of using the engine's tested ones. Helpers:
`kpc_keeper_requests.py` (reads the GitHub keeper's out-of-date list), `kpc_nightly_run.py` (the nightly screen),
`kpc_check_robots.py`. The README lists about 26 buttons. The frozen copy here holds 5 of them.

**The page reader** (`page-reader/`). `kpc_park_pages.py` plus a 2,518-line rules file reads each park's own web page and
saves the name, sizes, addresses, map links and an id from the link. `kpc_manners.py` (1,010 lines) is its polite fetcher
with its own robots.txt reader, a separate copy of the store's rule. Its results become `park-facts.json.gz` (13,062 US
parks, 5,900 Canadian). The copy here has 8 buttons, and the README names 3 more plus a control panel.

### The park facts, counted (what the matcher gets from the page reader)
| | US (13,062) | Canada (5,900) |
|---|---|---|
| no usable id at all | 3,588 | 2,249 |
| the only id is a page address (useless to the matcher's id step) | 7,281 | 3,059 |
| no official name read from the page | 6,127 | 1,345 |
| page "name" shares no place word with POTA's name (spot check: about 27 of 30 are not names) | 631 | 358 |
| page "name" is plainly a menu or error line (word list) | 21 | 21 |
| page "name" is compressed binary text | 2 | 2 |
| no official size | 9,022 | 4,076 |
| a size the matcher may use (own page, clean total) | 725 | 746 |
| two clean totals on one page that disagree by more than 10% | 31 | 7 |
| page not read (403, 404, robots, crawl-delay, rested ...) | 5,441 | 1,026 |

## 2. Findings, most serious first

**F1. Store room. LOST DATA. One record with no shape marks the whole layer "not complete", and that blocks the state.**
`kpc_layer_records.py:423`: `complete = src == len(feats) and n_ok == len(feats)`, where `n_ok` counts only records with
a polygon. Measured: MA `sgmaa` 61,485 of 61,486; NC `sgnca` 6,152 of 6,155; VT `vta` 0 of 483. Canada: NB, NS (one each).
v2 already drops records with no shape at load and counts them. So this flag gives no extra safety, and it stops whole
states. MA (421 parks) and NC (253) are not built today.
Fix (S): keep `complete` = "the download holds the layer's own count". Add `shapeless: n` and `lines: n` to the manifest.
Rebuild only (the button with N). Offline test: yes.

**F2. Store room. WRONG DATA. The real object id is ignored when a layer also has a copied OBJECTID column.**
`kpc_layer_records.py:234-243` takes the first of `OBJECTID, objectid, ... FID` before the feature's own `id`. The Iowa
layer `sgiaa` has a true id `OBJECTID_1` and an unrelated `OBJECTID`. So `sgiaa247` is three different areas (Barber Creek,
Pheasant Hills, a private IHAP tract). Measured: 290 records share keys (IA 154, MN 109, WI 27). GA `sggae` has 2 more.
v2 drops them all. 19 Iowa parks have their pin inside a dropped record (Syracuse, Loess Hills, Pilot Mound, White Pine
Hollow, Hendrickson Marsh ...). The old engine already solved this: `kpc_outline_store.py:1428` `OidPick` ("Iowa also has an
unrelated OBJECTID column"; it reads `objectIdFieldName`, then the field typed esriFieldTypeOID). Fixture: check 1 prints
`sgiaa247 sgiaa247`.
Fix (S): take the feature's GeoJSON `id` first (ArcGIS fills it with the true object id), or use `E.OidPick`. Write the
field used in the manifest, and refuse a layer whose ids still repeat. Rebuild only, if the saved .geojson files carry
`id`. I could not see the PC files, so this is not verified. Otherwise it needs a download. Offline test: yes.

**F3. Store room. WRONG DATA (doubles). Canada layers are read two or three times under a second name.**
`keep_downloaded()` (`:480-495`) adds every `*.geojson` on disk whose name is not a plan id. But file names go through
`safe_name()` (`:165`, which turns `~`, `é` and `:` into `_`). So `Québec ecolo` is saved as `Qu_bec ecolo.geojson`, and the
next run adds `Qu_bec ecolo` as a second layer that reads the same file. Measured: 9,118 duplicate records in 15 ghost
layers (QC 6,645; NS 1,456; NB 776; MB 129; SK 112). Every pair is (X, safe_name(X)). Fixture: check 3. Also, one label
with the same address twice (`Manitoba wil` and `Manitoba wil#2`, both `.../FeatureServer/0`) is downloaded twice, and both
copies get the same key `Manitoba wil:3` (142 records, 71 keys; fixture check 4). A ghost copy could also pass as "two
official sources agree" (v2 step 3c) when it is one source.
Fix (S): keep a layer only once per address. In `keep_downloaded`, compare `safe_name(plan id)`. Drop a plan row whose
address is already planned. Rebuild only. Offline test: yes.

**F4. Store room. LOST DATA. Trail lines are left out on purpose and line features are dropped.**
`:41` `NOT_LAND = {'trl', 'line'}` takes trail layers out of the plan (`:97`, `:136`). `rings_of()` (`:224-231`) returns
nothing for LineString / MultiLineString / Esri `paths`, so `record_of()` (`:245`) drops them. Fixture: check 2 prints `None`.
Measured on the matcher's output: 14 parks `record_layer_not_in_store` (MN 11, NY 3), plus 8 trail parks
`name_but_no_pin_or_size_proof` (MN 7, NY 1) whose pin may sit on a line. About 239 US park records are trail, route or
greenway parks (an upper bound). The engine already reads line layers (`kpc_outline_store.py:6208`, `:6268` paths, the
`trl` layer in the packs).
Fix (M): plan `trl` layers. Write a line record as `paths` (same integer steps as rings) plus `"shape": "line"`, no
`rings`, as rule sheet section 12 says. Needs a new LAYER-RECORDS download. Offline test: yes (fixture).

**F5. Store room. LOST DATA. A layer that is not land, or that is refused, still blocks a whole state.**
ND `sgaki` is the Park Service's historic-places POINTS layer (`verified-layers.csv:307`: "not a park layer"). It is never
downloaded, so the manifest says "no file yet" and ND (155 parks) is not built. VT `vta` (`MapServer/44`): all 483 records
have no polygon (probably points; not verified), so VT (109 parks) is not built. Today the manifest gives one reason,
"no file yet: the download failed or was not tried", for a refusal, a failure and a layer that was never asked for
(`:395-397`).
Fix (S-M): the manifest says which one it is: `refused (host rules / not a park layer)`, `failed (<server answer>)`,
`not land (points)`. v2 may then treat "not land" as nothing to wait for. That is one table row on v2's side, and the
owner's call. Rebuild only. Offline test: yes.

**F6. Store room. LOST DATA. The reason a download failed is printed, never saved.**
`pull_whole()` returns `why` (`:191-197`). `main()` prints it (`:600`) and the manifest then says "see the lines above".
GA and SC `sgnca` (0 records; NC's own download of the same address holds 6,155) show no reason anywhere. When a re-download
fails mid-way, the OLD file stays and is still counted complete. Nothing in the manifest says today's try failed (stale
without saying).
Fix (S): write a small `<layer>.kpc-fail.json` (time, answer) and copy it into the manifest `why` beside the read date.
Offline test: yes.

**F7. Store room. SLOW and blocks states. The same whole layer is downloaded once per area.**
Measured: 16 addresses appear in 2 to 14 area files (48 extra downloads in 22 areas). The NC layer `sgnca` is in the GA and
SC files, the Iowa layer in MN and WI, `Parks Canada` (53 records) in 7 provinces, Manitoba's in SK. GA and SC are blocked
only because their copy of `sgnca` failed, while NC's whole copy sits on the PC.
Fix (M): one download per address. Each area takes its box's share from that one file (`import_hand(..., clip=box)`
already does this for hand files). No new download for GA/SC. Offline test: yes.

**F8. Store room. RISKY (far records). A national layer listed under a state's own prefix is saved whole, with no box.**
`:104-105` `own = pre.startswith('sg'+st)` gives no box. MN `sgmng` (the national refuge boundaries): 887 of 1,085 records
lie outside MN's box (the Alaska refuge). MA `sgmac` (Park Service boundaries): 386 of 428. GA `sggae` (heritage areas):
56 of 62. The 10 km id guard keeps these off most parks. But the far-pin waiver (rule sheet section 12) can reach them, and
they cost memory.
Fix (S): pass the area box for every layer whose address is not the state's own server, or for every layer. Needs a new
download of those 3 layers. Offline test: yes.

**F9. Store room. HARD TO USE. The nightly screen hides every Canadian failure.**
`kpc_nightly_run.py:9-10`: `ROW = ^\s+(\S+)\s+source`. A layer id with a space ("Yukon parks", "NB Parks~1") never matches.
Tested: `sgnca` matches, `Yukon parks` and `NB Parks~1` do not. The screen can say "Every layer is on this PC" while CA-YT
Yukon is missing. Also, `kpc_layer_records.py` returns 0 even when layers failed (`:627`), so the screen says FINISHED.
Fix (S): print one tab-separated row per layer and read that, or read `layer-records-counts.csv`. Exit 3 when any own-state
layer is not complete. Offline test: yes.

**F10. Store room. House rule g (R-NET1) not kept for data requests.**
- `pull_whole()` count step (`:177-186`): asks 3 times, 15 s apart, also after a 429 or 403.
- Page step (`:192`): a 401 / 403 / 429 ends that layer only. The NEXT layer on the same host is still asked (MN has 5
  layers on `enterprise.gisdata.mn.gov`). The rule says to stop that host for the run.
- Retry-After is not kept from layer-records requests (the engine's fetch keeps it, `:4802-4812`).
- The engine's own fetch (`host_loop`) retries a 429 / 503 once after Retry-After. A 401 / 403 counts as a plain failure,
  so up to 3 failures x 2 tries happen before the host stops (`:4799-4841`).
- `pull_robots()` checks `rb.allowed(u)` on the address without its query (`:8421`), so a Disallow aimed at
  `...?f=geojson` would be missed (a suspicion: no such rule was seen).
- robots.txt itself is handled right (`read_robots`, `:4497-4536`): 401 / 403 / other 4xx but 429 = no rules; 429 and
  5xx = not this run; only Disallow lines block. Two stricter-than-the-rule cases: a robots.txt redirect to another site is
  refused and counts as "unreadable" every run (PROGRESS.txt: `services.aadnc-aandc.gc.ca -> services.sac-isc.gc.ca`; RFC
  9309 lets crawlers follow redirects across sites). A Disallow pattern the parser does not understand counts as "Disallow
  all" (`:1197-1198`). Both are grey areas for the owner, not bugs.
- `kpc_layer_records.py` takes no fetch lock, so the nightly job and a button press can download at the same time.
Fix (S): a `stopped_hosts` set in `main()`. A 401 / 403 / 429 on any data request adds the host. Every later layer on it
says "host stopped this run". No count retry after 4xx. Take `E.take_lock`. Offline test: yes, with a fake `net`.

**F11. Page reader. WRONG DATA. Headings that are not names are saved as the park's name.**
`kpc_park_pages_rules.py:715-722, 790` keeps any h1 (or else the first h2 or h3) of two words or more. Measured: 989 page
"names" share no place word with POTA's name. Top ones: "Other Name(s)" 111 (historicplaces.ca), "FISH, WILDLIFE & PARKS" 28,
"Main navigation" 23, "Search Results Page Not Found" 13, "Subscribe Now!" 6, "Topic sign-up successful." 1. A few are a
neighbour's name ("Duclos Point Provincial Park" for CA-0195 Morning Glory). v2 uses page names only with pin proof, so
matches gained: about 0. The risk is a wrong-land join when a page names a neighbour.
Fix (S): a heading becomes the name only when it shares a real place word with POTA's name or with the page title.
Otherwise the name is empty, with a question `TITLE_NOT_A_NAME`. Offline test: yes (`best_name_of` is pure). It takes
effect after the next page-reader run, or a rebuild from saved pages if those are kept (I did not check that).

**F12. Page reader. LOST DATA. Two big hosts are never read.**
`www.dec.ny.gov` robots.txt unreachable: 567 parks `robots-unreadable`. `parks.ny.gov` Crawl-delay over 120 s:
194 parks `crawl-delay`. 12 of NY's 32 pin-only parks have no page read for these reasons (Artpark, Schunnemunk, Sunken
Meadow, Beaver Island, Old Croton Aqueduct, Allegheny Reservoir ...). A size or a page name might prove some of them.
Already built, not yet shown on data: the bare-host try for an unreadable `www.` robots.txt (`kpc_manners.py:599-614`,
26 Nov) and the slow-site step (`kpc_park_pages_slow.py`). The park facts are from before both.
Fix: no code. Run the page reader's tonight button, then rebuild the park facts. Needs the network (the owner's button).

**F13. Page reader. WRONG DATA (weak proof). Several "clean total" sizes on one page.**
v2 accepts a size proof when ANY witness is within 10% (`kpc_us_key_v2.py:768-770`). 38 own pages give two clean totals
that disagree by more than 10% (CA-0006 Big Creek: 608 ha and 162 ha; CA-1280: 2,721 ha and 547 ha; US-0314 Mandalay:
4,212 and 3,619 acres). Each extra figure is one more chance of a false match.
Fix (S): when clean totals on one page disagree by more than 10%, mark them all not clean, with the question
`SIZES_DISAGREE`. Offline test: yes.

**F14. Page reader. House rule g not kept for page requests.**
`kpc_manners.py:701-716`: a 403 is retried once after 30 s, and the host stops only after 3 strikes (about 4 requests).
A 429 is retried with a pause, and the host stops after 3 strikes. A 401 returns but does not stop the host. The rule says
a page answering 401 / 403 / 429 stops that host for the run. robots.txt is right (`:484-491`), with one difference from
the store: a web page at robots.txt that is not "no rules" is saved as `robots` (a no) instead of "not this run" (`:465-468`).
Fix (S): on 401 / 403 / 429 set `self.dead[h]` for the run at once, with no retry, and list the host for a person.
Offline test: yes, with a fake opener.

**F15. Store room. WRONG DATA (names). The record name is empty for whole layers.**
The name field comes from the US pack's `layers.get(lay)[1]` (`:412`). Canada labels are not in it, and the fallback list
(`:253-254`) has no French or provincial names. Measured empty: 19,282 Canadian records (QC `DESIGNOM` / `NOM_OFFICIEL`,
NS `PROT_NAME`, NB `Park_Name`, SK `PARKNM`, Parks Canada `DESC_EN`), and NC `sgnca` 6,152 of 6,152 (it has
`ComplexName`; that this is the name is a suspicion). The attributes are kept whole, so nothing is lost: v2's
`name_fields` table can fix it. But the store gives no warning.
Fix (S): the manifest writes `name_field` per layer and warns when more than half the names are empty.

**F16. SLOW. Nothing checks for change before downloading again.**
The store room downloads a layer again only on `--again` or the keeper's list. No `lastEditDate` check, although
`E.terms_stamp_of` exists (`kpc_outline_store.py:2904`). Paging has no `orderByFields` (no evidence of harm: 0 repeated
key+shape pairs in all 22 files). The page reader saves `etag` / `last-modified` (`kpc_manners.py:517`) but never sends
If-None-Match / If-Modified-Since, and it caches only slow hosts unless `KPC_MANNERS_CACHE_ALL=1`.
`kpc_keeper_requests.py:58` compares a UTC `Z` time with the keeper's `at` as plain text. If `at` carries an offset, the
answer is wrong (a suspicion: I did not see the keeper's file).
Fix (M): one layer-JSON request (`lastEditDate`, count) before re-downloading a listed layer; skip it when nothing changed.
Conditional GETs in `kpc_manners.get()` for cached pages.

**F17. RISKY TO CHANGE.** `kpc_outline_store.py` is one 10,914-line file. `kpc_layer_records.py` copies its jobs
(object id, rings, paging) instead of calling them, and it has 2 regressions the engine had fixed: F2, and rings under
4 points dropped without a word (`:229-231`, where the engine refuses the record, `:1459-1468`). Rules sit in code:
`NOT_LAND`, `OID_FIELDS`, the name-field list, the count retries (3 x 15 s), `CRAWL_CAP` 120, `MAX_CRAWL_DELAY` 120.
Tests: `kpc_layer_records` has an 11-check selftest. `kpc_nightly_run`, `kpc_keeper_requests` and `keep_downloaded` have
none. The page-reader buttons use `py -3` (the PC ran Python 3.15, `run-log.txt`), not the house's one Python 3.12.

**F18. HARD TO USE.** The store room has about 26 buttons (README "WHICH STEP DO I RUN WHEN" plus R1-R5, A-, LAYER-RECORDS,
NIGHTLY). For the new matcher only two matter: LAYER-RECORDS and NIGHTLY-LAYERS. The page reader has two "everything"
buttons that overlap (RUN-ALL-TONIGHT, RUN-OVERNIGHT) and gaps in the numbering (1, 2, 2f, 2h, 3, 5). Neither tool has one
"what happened, what to do next" page. The layer tool's summary is a wide table, and its failures are mixed in with the
download lines. Hand downloads are clear (named folders, `hand-file-names.csv`, the HAND-DOWNLOADS list).

## 3. Do these first (ranked by how many more parks the matcher could prove)

| # | Fix | Parks the matcher could prove (yardstick) | New download? | Offline test? |
|---|---|---|---|---|
| 1 | F1: a shapeless record no longer blocks the layer | MA 348 + NC 83 = **about 431** (prep run: parks minus unproven) | no, rebuild | yes |
| 2 | F7 + F6: GA/SC take `sgnca` from NC's file on the PC; save failure reasons | GA 174 + SC 105 = **about 279** (with fix 1) | no | yes |
| 3 | F5: say "refused / failed / not land"; v2 does not wait for a not-land layer | ND 48 + VT 73 = **about 121** (needs one v2 table row, owner's call) | no | yes |
| 4 | F4: keep trail lines | MN+NY **14 to 22**; up to about 239 US trail parks | yes, LAYER-RECORDS | yes |
| 5 | F2: the real object id | Iowa **0 to 17** (19 parks' pins sit in dropped records; IA has 17 unproven) | no if saved files carry `id`, else yes | yes |
| 6 | F12: run the page reader on NY DEC and NY Parks | NY **0 to 12** | yes (page reader) | no |
| 7 | F3 + F15: no ghost layers, names written, one key per record (Canada) | cannot count (no Canada v2 run yet); 9,118 duplicates and 19,282 empty names gone | no, rebuild | yes |
| 8 | F10 + F14: stop a host on 401 / 403 / 429 | 0 (the owner's rule) | no | yes |
| 9 | F11 + F13: no non-names, no two-size pages | 0 gained; takes away false-proof chances (989 names, 38 pages) | page-reader run | yes |
| 10 | F9: the nightly screen shows Canadian gaps, nonzero exit | 0 (a failure you can see) | no | yes |

The prep figures (rows 1-3) are the prep tool's own "parks minus unproven" for states it could not build. They are an
estimate, not a v2 run. Rows 1-3 together would take v2 from 8 to 14 buildable states of the 14 staged.

## 4. Checked and sound
- Completeness against the layer's own count, same question, with a geojson-to-json fallback (`:187-201`). No paging overlap
  was seen: 0 records with the same key and shape in any file.
- Files are written whole (`.part` then replace), each with a sha256 note, and checked again at build (`:404-408`). A file
  from an old address is never counted (`:400-403`).
- The detail of shapes (`maxAllowableOffset` about 2 m, 6 decimals) is within the 3 m rule.
- A robots.txt that answers 401 / 403 / other 4xx but 429 means no rules; 429 and 5xx mean not this run. Only the
  STATUS-CODE step is right in both tools (store `:4497-4536`, page reader `:484-491`). CORRECTION (see the last section,
  "FALSE BLOCKS"): I first wrote that robots handling was right in both tools. For the page reader that was wrong. Around
  the status-code step it blocks in ways no rule line allows, and it holds the blocks over later runs.
- TLS is always verified (`:4162-4179`). Pacing is kept on disk, with hourly and daily caps per host.
- Hand downloads: newest file, partial "--KEY-RECORDS" files refused, national files cut to the area box.
- Sizes on pages: hectares and km2 converted right (Alaksen 349 ha = 862.4 acres); metric decimal commas and
  space-thousands handled (`:994-1003`).
- A cut-off .gz sitemap no longer stops the whole run (`kpc_park_pages_find.py:266-270`; `run-log.txt` shows the old crash).
- `kpc_layer_records.py --selftest`: ALL PASS.

## 5. Not done
- I could not see the raw `.geojson` layer files on the PC. So I could not check whether the GeoJSON `id` is there (F2),
  what the 5 shapeless MA / NC / NB / NS records are, or whether `vta` is points or lines.
- I did not read the store engine's build, publish, water and re-find sections (`kpc_outline_store.py` 5176-10900), or
  `kpc_research.py`, `kpc_store_read.py`, `kpc_apply_marks.py`, `kpc_licence_drafts.py`.
- I did not read the page reader's link and id bot in depth (how `id_kind` "page address" is chosen), nor the docs or
  truth bots.
- I did not run v2 with any fix. All park gains are estimates from the outputs already on disk.

## 6. FALSE BLOCKS (page reader)

**Correction first.** In F10 and section 4 I wrote that robots.txt is "handled right in both tools". For the page reader
that is wrong. Only its status-code step is right (robots.txt 401 / 403 / other 4xx but 429 = no rules; 429 / 5xx = skip
this run). Around that step the tool blocks in ways no rule line allows, and it keeps those blocks for later runs. The
owner is right: it often thinks it is blocked when it is not. Read and measure only. No network, no file changed except
this report. The offline checks are in `scratch/audit/robots_fix.py` and `scratch/audit/blocks.py`.

### 6.1 Every path that ends in "this page / host is not read"
File = `page-reader/page-reader/scripts/`. The "rule line" column is the owner's R-NET1 wording.

| # | Condition | Where | What the tool records | Rule line that supports it |
|---|---|---|---|---|
| A | robots.txt has a Disallow that matches the address | `kpc_manners.py:645-650`, `robots_allowed :355-383` | `robots` | YES: "Disallow = NO" |
| B | the Allow and the Disallow pattern are the same length: the Disallow wins | `:376-379` (offline check: `Allow: /p` + `Disallow: /p` gives not read) | `robots` | NO. RFC 9309 and the store engine (`kpc_outline_store.py:1252`) say Allow wins |
| C | robots.txt answers 200 with a web page that holds no robots lines but is from another host (even its own `www.` twin), a sign-in page, a bot challenge, a password form or a WWW-Authenticate header | `robots_final_problem :50-57`, `robots_page :60-78`, used at `:461-468` | `robots` (saved as a Disallow for the whole host: `robots_disallow`, `blocked`) | NO. No Disallow was read. A sign-in wall is the same as a 401 = no rules. At most "not this run" |
| D | robots.txt longer than 512,000 bytes, or holding a NUL byte | `parse_robots :271-274`, used at `:470-480` | `robots-unreadable` for the whole host | NO. RFC 9309 says parse the first 500 KiB. Offline check: a 600 KB file with no rule for us gives not read |
| E | robots.txt cannot be reached: time-out (30 s), TLS failure, reset, a refused redirect hop | `_load_robots :449-458`, `:487-491` | `robots-unreadable` | Partly. The rule names only 429 / 5xx = skip this run. A network error as "skip this run" is fair, but the reason is not saved in the park facts (only in memory and `for-a-person.csv`) |
| F | robots.txt answers 429 or 5xx | `:487-491` | `robots-unreadable` | YES: skip that host this run |
| G | queued addresses of a host whose robots.txt was C, D, E or F | `fetch_all :743-758`, `get :631-644` | the same status, no request | YES for F. For C, D and E it spreads the false block to every park of that host |
| H | Crawl-delay above `MAX_CRAWL_DELAY` = 120 s | `:116`, `:658-662`; browser reads `:827`, `:862`, `:906` | `crawl-delay` (next run) | NO. The rule says respect the delay and go slow. The slow pass raises the limit to 900 s through `KPC_MAX_CRAWL_DELAY` (`kpc_park_pages.py:33-38`, `RUN-ALL-TONIGHT.bat:48`); above 900 s it is still skipped |
| I | Crawl-delay of 10 s or more, after 10 live requests to that host in a run (`SLOW_BUDGET`) | `:128-129`, `_budget :537-542` | `deferred` | A slow site, not a block. The slow pass sets the budget to 5000 |
| J | a page answers 403: one retry after at least 30 s, then for a person; 3 strikes = host rests 24 h | `get :701-710` | `403`, then `rest` | Half. Stop the host: YES. The retry and the 24 h carried into the next run: NO |
| K | a page answers 429 or 5xx, or times out, or a connection error: strike; 3 strikes = host rests 24 h (`rest_s=86400`) | `:711-731` | `rest` | 429: stop for the run = YES, but the tool retries first. 5xx / time-out: no rule. Resting carried to the next run: NO |
| L | a rested host is loaded from the saved state at start | `Manners(.., resting)` `:390`; `LiveGetter` `kpc_park_pages.py:325-326`; saved `:956` (`out/state.json` `hosts`) | `rest` | NO. A remembered verdict from an earlier run |
| M | 10 different pages of a host answered 401 / 403 / a wall: the host is set aside | `kpc_park_pages.py:345, 372-382`; checked `:597-604`; `REFUSAL_DAYS = 7` (`kpc_park_pages_rules.py:19`); saved in `state.json` `refused` | `refused` | NO. The rule says for the rest of the run, not 7 days |
| N | a park whose last read was `refused` (a Disallow or a 403) is not asked for 7 days (`REFUSED_DAYS`) | `is_fresh` `kpc_park_pages.py:715`, `:45` | the old fact is kept | NO. "Check robots.txt live before repeating old notes" |
| O | BEFORE 26 Nov: a resting or refused read saved with the fingerprint of an empty page counted as "read" for 30 days (`REFRESH_DAYS`) | `is_fresh :700-722` (comment: BLM 897, NY DEC 567, Missouri 430, Forest Service 268, NY Parks 194) | the old fact is kept | NO. Fixed in the code on 26 Nov (`EMPTY_FP`, resting = due now), not yet shown on data |
| P | a redirect hop to a host the host rules refuse, or https to plain http on another site | `_install_hop_check :87-110` | `host-rule` / error | YES (owner's host rules). 0 parks in the facts |
| Q | host lists typed in code: never-contact (`services.arcgis.com/33TOOklri9xpic7U`, `ncnhde.natureserve.org`), every `services*.arcgis.com`, saved-copy-only (`services.arcgis.com`, `services1.arcgis.com`, `apps.fs.usda.gov`, plus `KPC_SAVED_ONLY_HOSTS`); WDPA addresses | `kpc_host_rules.py:21-23, 59-71`; `kpc_park_pages.py:593-596` | `host-rule` / `refused` | YES (owner's rulings). 0 parks in the facts |
| R | the address is an agency front page (no path) | `kpc_park_pages.py:791-801` | `not-asked` | Not a block (no own page) |
| S | the documents bot: its own robots reader (15 s time-out, the same too-long rule, no web-page rule); 3 strikes = 24 h rest, kept in its state | `kpc_docs_bot.py:158-189, 222-252, 1227, 1243` | `robots-unreadable`, `rest` | Same as D, E, K, L |
| T | a redirect to ANOTHER host is followed without reading that host's robots.txt (only the host rules are checked) | `_install_hop_check :92-110`; bare-host try `:599-614` | read | NO, the opposite way: "robots.txt always wins" is not checked on the hop |

Verdicts remembered from earlier runs: `out/state.json` keys `hosts` (24 h), `refused` (7 days), `read` (30 days for real
reads, 7 days for refused, due at once for resting since 26 Nov), `dead` (7 days to confirm). The robots.txt disk cache
(1 day) is on only when `KPC_MANNERS_CACHE` is set. No .bat sets it, so it is off on the PC.

### 6.2 Pages not read in the park facts (built from reads of 21-24 Nov)
Counted with `scratch/audit/blocks.py`. Dead links (US 575, Canada 305), no link (108 / 255) and agency front pages
(359 / 210) are not blocks and are left out.

| Status as recorded | US | Canada | What it is under the rules |
|---|---|---|---|
| `rest` | 2,016 | 120 | host rested after 3 strikes and carried into the next run: **FALSE BLOCK** for every run after the first |
| `robots` | 746 | 42 | a Disallow, OR a web page at robots.txt the tool refused (path C). The facts do not say which. Real block as recorded; part may be FALSE |
| `robots-unreadable` | 708 | 50 | temporary skip, but kept for up to 30 days before 26 Nov: **FALSE BLOCK in effect** |
| `deferred` | 490 | 0 | slow site, budget used (go slow: right) |
| `403` | 228 | 29 | page refused: stop the host for the run (right), but the 24 h / 7 day carry is not |
| `crawl-delay` | 202 | 0 | slow site skipped: **FALSE BLOCK** (the rule says go slow) |
| `refused` | 0 | 12 | host set aside 7 days (montreal.ca): **FALSE BLOCK** (old verdict) |
| err / 5xx | 9 | 3 | temporary |
| **Total not read (blocks and skips)** | **4,399** | **256** | |

Top 20 hosts (blocks and skips): www.blm.gov 737 (rest 732, 403 5); **www.dec.ny.gov 567 (robots-unreadable)**;
mdc.mo.gov 407 (deferred 406); www.pgc.pa.gov 306 (robots); www.fs.usda.gov 263 (rest); www2.dnr.state.mi.us 225 (rest 163,
403 62); **parks.ny.gov 194 (crawl-delay)**; www.floridastateparks.org 174 (rest 170); www.tn.gov 174 (rest 123,
robots-unreadable 48); www.dcnr.pa.gov 149 (robots); www.dnr.state.mn.us 122 (robots); outdoornebraska.gov 122 (rest 116);
dwrapps.utah.gov 84 (robots); yukon.ca 73 (rest 68); ksoutdoors.com 73 (rest); tnstateparks.com 65 (rest 60);
www.wlf.louisiana.gov 64 (rest 58); www.nh.gov 62 (403 61); map.mysuwanneeriver.com 51 (deferred); parks.ky.gov 48 (rest).
- Suspected false Disallows (cannot be checked offline). www.pgc.pa.gov (306) and www.dcnr.pa.gov (149) are `robots` for
  EVERY page, with not one page read. That is the pattern of path C (a web page at robots.txt, blocked for the whole host),
  or of a real `Disallow: /`. These 455 parks are the PA game lands and parks behind PA's 311 unproven parks.
  www.dnr.state.mn.us is different: only `/wmas?`, `/snas?` and `/amas?` addresses are blocked, while `/state-parks?` and
  `/state-forests?` are read. That looks like a real path Disallow.
- `out/slow-refs.json` (748 parks) lists `crawl-delay` and `deferred` only: mdc.mo.gov 430, parks.ny.gov 194,
  map.mysuwanneeriver.com 63, stateparks.utah.gov 33 and others. It does not hold the NY DEC parks.

### 6.3 NY DEC and NY Parks
- **NY DEC (www.dec.ny.gov, 567 parks, read 21-22 Nov).**
  - What the tool saw: robots.txt could not be reached (an error, not a status; the comment at `kpc_manners.py:600`
    says "could not be reached from the PC"). The exact error is kept only in memory and `for-a-person.csv`, which is
    not in these copies.
  - What it decided: the whole host was "unreadable" (path E). Every queued DEC page was dropped (path G). The parks
    were saved as `robots-unreadable` with an empty page. Until 26 Nov, `is_fresh` (path O) counted that as read for
    30 days, so robots.txt was never asked again. Meanwhile 17 pages on the bare host `dec.ny.gov` were read (200).
  - What the rules say: an unreachable robots.txt may be skipped for that run only. It must be asked again live on the
    next run, and the reason must be saved.
  - A suspicion, not verified: the PC runs Python 3.15, whose extra-strict certificate check
    (`VERIFY_X509_STRICT`) the store engine already works around (`kpc_outline_store.py:4384-4395`). The page reader does
    not (plain `urlopen`, `:450`). That would make the same host fail every run.
- **NY Parks (parks.ny.gov, 194 parks, read 21-22 Nov).**
  - What the tool saw: a Crawl-delay above 120 s (the value is not saved in these copies).
  - What it decided: `crawl-delay` (path H), skipped. The slow pass (2g step in RUN-ALL-TONIGHT, since 23 Nov) raises
    the limit to 900 s. But its parks were also "fresh" under the old `is_fresh` (`kind` resting, empty page), so it read
    none of them. The 26 Nov run made 115 requests for 81 parks (`out/run.json`).
  - What the rules say: obey the delay and read slowly. With a delay of D seconds, one 300-minute slow pass reads about
    18,000 / D pages (D = 300 gives 60 a night, so 194 pages in 4 nights). Skipping is not allowed by any rule line.
- **The "fix already built but not run":**
  - (1) `is_fresh` (26 Nov) puts resting and empty reads back on the due list. This is RIGHT under the rules (a live
    check every run). It also unblocks the slow pass.
  - (2) The bare-host try (`_try_bare_host_when_www_unreadable`, `:599-614`): when `www.X` robots.txt is unreachable, it
    reads the same path on `X` under `X`'s own robots.txt. Allowed in itself (another host, its own robots.txt). But as
    written it has three faults:
    - (a) it keeps ANY status: a 404 from the bare host is saved as "dead link" for the park, and any other page as the
      park's page;
    - (b) if `X` redirects back to `www.X`, urllib follows the hop and fetches the page from the host whose robots.txt
      could not be read (path T). That breaks "skip that host this run";
    - (c) it hides the cause instead of fixing it.
    Safe only with: status 200, the final address on the bare host, the same path, and robots.txt checked on every
    redirect hop.

### 6.4 The smallest safe changes (page reader only), and what each opens up for the next run
All can be tested offline. All take effect on the owner's next page-reader run.
1. **One decision table for robots.txt** (`kpc_manners.robots_verdict(status, body, final_url) -> no_rules | rules |
   skip_run`), used by `_load_robots` and the documents bot, with one test per R-NET1 line.
   - Path C becomes "skip this run" for other-site, challenge and redirect cases, and "no rules" for a sign-in wall.
     Never `robots`.
   - Path D: parse the first 500 KiB; a NUL ends the line.
   - Path B: Allow wins ties.
   Size S-M. Opens: an unknown part of the 788 `robots` parks. The 455 PA parks are the likely ones; the store's
   `kpc_check_robots.py` (robots.txt only) can confirm pgc.pa.gov, dcnr.pa.gov, dnr.state.mn.us and dwrapps.utah.gov
   live before the run.
2. **No verdict carried into the next run** (paths J, K, L, M, N, S):
   - rested and set-aside hosts last for the current run only;
   - 401 / 403 / 429 on a page stops the host at once for the run (no retry);
   - a refused page re-checks robots.txt live before the old fact is kept.
   Size S. Opens: up to **2,136** `rest` parks (BLM 732, Forest Service 263, Florida 170, Michigan 163, Tennessee 123,
   Nebraska 116 ...) and **12** `refused` parks. The 257 `403` parks are asked again once per run.
3. **Crawl-delay: queue, never skip** (path H): every page above the nightly limit goes to `slow-refs.json`. The slow pass
   obeys any delay, with no 900 s cap; its run time decides how many pages it reads. Size S. Opens: **202** parks
   (parks.ny.gov 196, mitigationcommission.gov 5, carnegiemnh.org 1) over several nights. The 490 `deferred` parks are
   already queued.
4. **An unreachable robots.txt** (path E): save the error in the park's page fact. On a TLS failure caused only by the
   extra-strict check, ask once more with only that check off (the store engine's rule, chain and host still verified).
   Asked again every run (true since the 26 Nov `is_fresh` change). Size S. Opens: up to **758** (www.dec.ny.gov 567,
   www.tn.gov 48, www2.dnr.sc.gov 44, others). How many depends on the real error, which the next run will show.
5. **A real Disallow goes on its own hand-download list:** host, the Disallow line that matched, page, park. Today it is
   mixed into `for-a-person.csv` with 403s and dead links, and `need()` lists only layer addresses (`:493-499`). Size S.
   Opens 0, but **788** parks get a clear "ask the owner" row.
6. **Redirect hops obey robots.txt** (path T). The bare-host try keeps only a 200 on the bare host and the same path.
   Size S. Opens 0, but removes a rule breach and a wrong "dead link" source.

Together, changes 2-4 put **2,926 US** parks (rest 2,016, robots-unreadable 708, crawl-delay 202) and **182 Canadian**
parks (rest 120, robots-unreadable 50, refused 12) back on the next run's list. Change 1 may add up to 788 more (455 of
them PA). Today 4,655 are not read; of these, 490 are only slow and 257 were refused by the page itself. How many then
read must be measured on that run.
Aside, store room (not in this brief): `robots-disallowed-layers.csv` keeps robots verdicts from the owner's 14 Nov run
("no request of any kind"). That is an old verdict that is never checked live, the same fault as paths L to N.
