# Audit: the chain that makes park-facts.json.gz, and the PC tools around it (26 Nov 2026)

Read only. No tool file was changed, no git, no network. To measure, I ran small offline scripts (kept in /tmp/aud, scratch)
and ran the v2 matcher itself offline on saved files (store, facts, rules; it opens nothing) into /tmp/aud.
Everything below was measured on the real file `park-facts.json.gz` (made 24 Nov, kpc_park_facts 10) and today's layer files,
unless it is marked SUSPICION.

## 1. The chain on one screen

```
POTA list ──> KPC-Data data/parkinfo (main; Kentucky is NOT in it)
                 │
GitHub, acreage bot (kpc_acres, "tool trial", fetches agency lists; reads the v1 key)  ──> tools-out acres/acres.json   (US only, 2,921 parks)
GitHub page reader (timer, every 3 h)  ─┐
PC page reader ──> upload pack (zip, by hand to intake-files) ──> "PC upload pack" job (by hand) ─┴─> tools-out park-pages/facts/<area>.json
keeper kpc_agency_lists / PC pack  ──> main data/agency-crosswalk/*.json  (FL, MB, WA: 214 parks tied)
                 │
GitHub "KPC park facts" (runs after any of those three jobs end, or by hand):
   kpc_link_ids  (reads ONLY data/parkinfo links)  ──> link-ids.csv
   kpc_park_facts (parkinfo + acres + page facts + link ids + crosswalk + the WEBSITE'S v1 KEYS for the size witness)
   ──> main data/park-facts.json.gz (2.3 MB)
                 │
kit update zip ──> PC folder 5-ANSWER-KEY-TEST\park-facts.json.gz ──> kpc_test_v2.py / kpc_us_key_v2.py / state prep
```
v2 reads from the file: `name`, `type`, `pin`, `link` (id_kind, id_value, usable, id_shared_by, page_kind, site, state_check,
name_match, web_name), `page` (own_page, unofficial, sizes[].total/clean/acres), `size` (acres, witness, witness_counts,
source_url). It does NOT read `link.map_tie`, `page.name_on_page`, `page.url`, `page.nps_code` (the state prep does read nps_code).

## 2. The lead first: what depends on the v1 key

Fields that change with the v1 key (`--key links/data/us-key --key links/data/ca-key`, and the acreage bot's `--keys`):
1. `size.witness` (kpc_park_facts.py 121-141): only for sizes whose address is a map layer. With the key: 831 `same_record`,
   591 `other_layer`. Without it all 1,422 become `unknown`. I recomputed every tag with no key (`witness(ref,row,None)` and `{}`):
   **0 sizes change between proof and not proof.** A map-layer size never counts either way (WITNESS_PROOF = agency_document,
   hand_copy). So this part changes no v2 join.
2. `size.outline_acres` (2,760 sizes) and the acreage bot's flag "over 50x the current outline": that outline is the v1 key's.
   tag_sizes (line 154) turns a flagged size into `witness_counts: false`. **7 good official sizes are refused because the v1 key
   had a tiny outline**: US-0492 Washita NWR 8,075 ac (key outline 26), US-0731 Columbia River Gorge 292,690 (561), US-1566
   Cunningham Falls 6,157 (46), US-1573 Gambrill 1,209 (23), US-1596 Seneca Creek 6,391 (15), US-1601 Susquehanna 2,753 (1),
   US-7741 Idylwild WMA 3,635 (8). All in OK, WA, MD: none in the 14 states.
3. The acreage bot's match rule (a) "the record id the key joined": 0 sizes use it today (all are `name+kind` or `hand copy`).

MN / NY joins that rest on it: **0.** MN's 3 name+size joins (US-0361 Hamden Slough: FWS PDF, agency_document; US-4490
Chippewa and US-4491 Superior: hand copies) use tags that do not look at the key and carry no flag. NY has no name+size join.

What a fix must guarantee: building the file with and without the key gives the same `acres` and the same `witness_counts`
for every park (a test that builds twice and compares), and no flag that comes from a v1 outline may set `witness_counts`.
Smallest fix (S, GitHub): drop `--key`/`--layers` from kpc-park-facts.yml and drop "over 50x / under 0.1" from the `bad` list
in tag_sizes (v2 already demands the record's own acres within 10% of the official size, so a wild size cannot join anyway).

## 3. Findings, most serious first

**F1. WRONG DATA: square kilometres stored as acres.** 29 page sizes written "N square kilometres/kilometers" carry acres = N
(not N x 247.1). 4 of them are own-page `total`+`clean`, so v2 counts them as official acres: CA-0062 Nahanni "30,000 square
kilometers" = 30,000 ac (true 7.4 million), CA-0566 South Atikaki 140, CA-3019 Fickle Lake 11.5, CA-6125 Porcupine Hills 1,500.
Such a size can make a false name+size join or block a true one. Parks touched: 29 (4 used). Fix S (GitHub builder): when the
`as` text has a number and a unit, recompute and drop `clean` if it disagrees by more than 5%; root fix is the page reader's
converter (other auditor). Measured by: sizes.py (number x unit against stored acres).

**F2. WRONG DATA: impossible pins pass as pins.** The builder copies POTA's pin unchecked (read_parkinfo, line 47-50). 3 Manitoba
pins have latitude over 90 (CA-2456 Maple Lake WMA [100.856, -49.514], CA-2538 Westlake, CA-2395 Churchill: numbers swapped and
signs wrong); v2's pin_of accepts them. 199 parks have 0,0 (198 Quebec, 1 NT): POTA itself has no pin and no link for them (the
saved POTA list says the same). v2 drops 0,0 correctly. Far pins (pin more than 10 km from every record carrying the park's exact
name, 22 areas): 24 parks, e.g. CA-4406 Green Island NR (NB) 367 km, US-5432 Mount Washington SF (NY) 308 km, CA-0527 Birch Island
PP 157 km, US-4238 Ice Age Trail 144 km, CA-0558 North Steeprock Lake 110 km, CA-1851 Shut-in Island 54 km, CA-6224 Long Lake Bog
78 km (SUSPICION for each: another place may carry the same name). Pins otherwise match the saved POTA list exactly (19,242 rows).
v2 proves: 3 with a fixed pin, cannot count the rest. Fix S: builder adds `pin_problem` (outside -90..90 / -180..180, 0,0,
swapped); v2 treats it as no pin with its own reason. KPC-Data `kpc_official_pins.py` pin fills (agency points for 0,0 parks)
are not read by the builder: could be carried as a separate, labelled `pin_fill` (I could not count them: data/intake not here).

**F3. LOST DATA: US layer fields that already hold the park's own page address are not used.** The facts give 7,281 US parks a
usable `page address` id, but no US tie row exists for it. I compared each park's page address (cleaned the same way as
kpc_link_ids.page_address) with every URL-like field in today's layer files:
| layer / field | parks hit | name agrees (strong) |
|---|---|---|
| US-MA `maw` Website | 220 | 218 |
| US-GA `sggaa` Website | 120 | 114 |
| US-WI `sgwic`/`sgwif` SNA_URL, `sgwib` INFO_URL | 25 | 25 |
| US-SC `sgsca`/`sgscd` prop_page_url | 19 | 18 |
| US-CT `sgctc` Map_Link | 11 | 10 |
| US-NJ `sgnjb` FACILITY_URL | 2 | 2 |
(Not usable: US-IA `sgiaa` Atlas_Link and US-PA PAD-US Comments are general links shared by many records.)
The state prep reports "page address: 364 parks, no field found" for MA because it compares whole values
(kpc_v2_state_prep.py find_id_hits, line 252+): the field keeps "https://www." and the id does not. Gain: in the built states
(WI, CT, NJ) only 4 of these parks are pin-only today (WI US-4246, US-4255, US-8209 "record shared", US-8205 water); MA and GA
cannot be built yet (store gaps), so their gain cannot be counted; all ~397 would become id joins that can be locked. Fix S:
rule-table rows with the same rx the Canadian page-address rows use, and the prep compares cleaned addresses.

**F4. LOST DATA: Quebec's own page address sits in the Quebec layer, and the parks have no POTA link.** For 69 QC parks the
page the reader actually read (official-links finder) equals the `LIEN` field of the Quebec protected-areas layers; 48 of them
are pin-only in v2 today (all have no POTA pin). The builder drops the link row of a "no link" park (combine, line 495) and never
turns the read page into an id. Gain: up to 48 QC parks, but v2's id guard needs a pin (line 805), so they also need a ruling for
a no-pin park (id + exact name). Fix S (builder: run kpc_link_ids.read_link on a sure own page's address) + a grey area for the owner.

**F5. LOST DATA: Kentucky gets no link ids.** kpc_link_ids reads only data/parkinfo, which has no Kentucky. 183 parks have no
link row. Running read_link on the address the page reader read gives 72 real ids (63 KY Fish and Wildlife area ids, 6 NPS codes
e.g. US-0050 Mammoth Cave MACA, 2 Forest Service rec ids, 1 MN) plus ~78 page addresses. Gain for v2 now: 0 (KY not in v2 yet).
Fix S (GitHub builder): link ids also from the page reader's `_pota.link`, else the sure own page.

**F6. LOST DATA: the agency crosswalk is in the file but v2 never reads it.** `link.map_tie` on 214 parks (FL 153, MB 48, WA 13).
v1 reads it (kpc_match_checks.map_tie_of); v2 has no reference to it. MB is covered by v2's own page-address rows; FL and WA
will be lost when v2 reaches them. Fix S (rule table or v2), when those states come up.

**F7. STALE: no hop checks that it has the newest input.** `made` is the build date, not the input date; the file records no
input dates or hashes (only counts and areas_read). The builder accepts any non-empty page facts folder (yml line 47:
`ls pages/*.json`), keeper sizes and crosswalk are optional with no message, and its own self-test asserts "a bot file missing is
not an error". No step compares parks per area with the previous file, so a partial pack or a shrunken area file builds a file
that looks fine. The job also runs after a FAILED trigger run (`types: [completed]`, no conclusion check); harmless only because
nothing changed. The PC file is from 24 Nov; tonight's PC page reads reach it only through 4 hops with 2 by-hand presses (zip to
intake-files, dispatch the pack job; the facts job follows; then a kit update). kpc_test_v2.py (find_facts) takes whatever file
sits beside it and never shows its age. Parks touched: all; gain: cannot count. Fix M: builder writes an `inputs` block (file,
newest read date, sha256, parks per area) and stops when any area loses more than 5% of its page facts; the PC test prints
"park facts made <date>, newest page read <date>" on its first line and warns when the PC's own reader is newer.

**F8. SLOW / HARD TO USE: the builder could run on the PC.** It is standard library only. It needs data/parkinfo, acres.json
(tools-out), park-pages/facts (tools-out), kpc_park_pages_rules.py with kpc_truth_bot / kpc_docs_bot / kpc_manners (imported for
the name check only; they import cleanly with no request; the PC page reader already has them), kpc_link_ids.py. GitHub-only
inputs: acres.json (the acreage bot fetches agency lists on GitHub), the crosswalk on main, and whatever the GitHub timed page reader
added (SUSPICION: if that timer still runs, the PC lacks its reads). Fix M: one PC button "rebuild park facts" fed by a kit snapshot
of parkinfo + acres.json + crosswalk + the tools-out page facts, merged with the PC's own reads by the same "better or newer" rule
the upload job uses; both builds stamp their inputs (F7).

**F9. HARD TO USE: two different kpc_link_ids.py with the same version label.** PC PARK-ID-MATCHER copy (539 lines) and GitHub copy
(605 lines) both say `VERSION = '2026-11-20a'`. The PC copy lacks page_address (22 Nov) and the reader's site list (23 Nov). The
GitHub copy feeds the file. PARK-ID-MATCHER reads the OLD store (`*.kpcstore.json.gz`, "only the records the key already joined")
and a frozen link-ids.csv of 20 Nov: it compares against v1 joins, and nothing in v2, the facts builder or the prep reads its
output. Its job (which field holds the park's id) is now done better by the v2 state prep. Fix S: mark it "v1 only, retired" (or
give the PC copy a distinct version), so it is not run by mistake.

**F10. HARD TO USE / RISKY: hand downloads do not reach the store room by themselves.** The hand helper files a layer as
`Originals\US\<ST>\<tag>__<original name>` (and the tidy tool renames it `<AREA>_<publisher>_<layer>.<ext>`). The layer-records
tool looks only in `layer-files\hand\<area>\<layer>\`, `have\<AREA>-<layer>[--note].geojson`, or rows of hand-file-names.csv
(kpc_layer_records.py hand_file, lines 306-326). So a filed hand download is invisible until someone copies and renames it.
Also: the store takes only .json/.geojson(.gz), while the helper accepts zip, shapefile, gpkg, CSV; the store calls a hand file
complete whenever it lacks exceededTransferLimit (import_hand, line 368-375), never comparing with the layer's own count or the
helper's "strong" proof; and the helper's "right layer" proof is the v1 key's record OBJECTIDs (judge, line 1103-1120), which
are row numbers, with a names check only when the key lists names. A wrong file in hand\<area>\<layer>\ with a newer date wins
silently (newest mtime). Parks: cannot count. Fix M (PC): the helper writes the store's name (or a hand-file-names.csv row) when
the owner types FILE, and the store refuses a hand file without the helper's .intake.json strong proof.

**F11. HARD TO USE: tidy area guess by name first.** guess_area (kpc_tidy.py 2055-2076) takes a state name inside the file name
before the box ("George Washington" -> WA, "Delaware Water Gap" -> DE). Marked "guess" and never used for renaming, so only the
folder is wrong. Low.

**F12. WRONG DATA (small): `page.nps_code` holds Fish and Wildlife refuge slugs.** 147 parks have an nps_code and no NPS link id:
139 are fws.gov slugs ("hakalau-forest"), 2 of them 4 letters long (look like NPS codes), 6 real NPS codes. The state prep uses
nps_code as an NPS unit code (build_wants). Fix S: builder keeps nps_code only for nps.gov hosts.

**F13. WRONG JOIN DECISION (matcher, outside the chain but found here): curly apostrophes.** v2 `full("Pu’tlaqne’katik")` =
"putlaqnekatik", `full("Pu'tlaqne'katik")` = "pu tlaqne katik". CA-1846's id records (pin 0.2 km) failed the id guard for that.
26 park names carry a curly apostrophe (13 US, 13 CA); 470 carry a straight one. Fix S: treat both the same in the name cleaner.

**F14. LOST DATA (page reader; for the other auditor):** for 355 MN DNR / MI DNR / Forest Service parks the page `url` holds a
DIFFERENT park's id (e.g. US-2466 Afton State Park link SPK00100, page url ...id=sra00304, used for 71 parks); all are marked
`own_page: list`, so v2 ignores them, but those parks lost their page facts. 567 NY DEC pages are `robots-unreadable`.

**F15. NOT THE BOTTLENECK: the size gap.** Why 2,921 vs 5,864: the acreage bot covers only the agency lists in its research file,
US only (0 Canadian sizes), and 1,646 of its 2,921 are not proof by design (831 same_record, 591 other_layer, 214 unknown, 40
flagged). v2 also counts own-page sizes marked `total`+`clean`: US 725, CA 746. A safe widening (own page, total, the `as` text is
only a plain number and a clear unit, stored acres agree with it; leave out 3-decimal metric numbers like "63.536 Ha") gives a size
to 1,082 US and 544 CA parks that have none (per state: MA 207, GA 109, WI 44, VT 42, NJ 33, NC 26, CT 24, SC 21, IA 11, NY 9,
MN 3; NS 149, QC 84, NB 39, MB 33, SK 21). Measured in v2 on 8 built states with the widened file: +1 park (NJ US-8058).
Pin-only parks there are 528: 433 "no record with this name" (PA State Game Lands alone 308), 39 name without pin or size proof.
No thousands-separator trap found ("1.234" or "1 234" style: 0 wrong); the reader already fixes comma decimals and space groups.

**F16. HARD TO USE (small): the name check can fail silently.** `_agree` (kpc_park_facts.py 200-216) and reader_official in
kpc_link_ids swallow an import error and fall back to the older answer; the file does not say which one ran. On the GitHub runner
the import works (checked here bare). Fix S: write `name_check: reader rules | fallback` into `sources`.

## 4. Do these first (ranked by parks gained for least risk)

| # | Fix | Where | New reader run / download? | Parks |
|---|---|---|---|---|
| 1 | Page-address tie rows for MA maw, GA sggaa, WI SNA_URL/INFO_URL, SC prop_page_url, CT Map_Link, NJ FACILITY_URL; prep compares cleaned addresses (F3) | rule table PR + PC prep | no | ~397 become lockable id joins; new proofs: 0-4 measured, MA/GA uncounted |
| 2 | Drop the v1 key from the facts build; outline flag no longer refuses a size (F2 of section 2) | GitHub builder | no | 7 sizes back; keeps v2's promise |
| 3 | km2 guard on page sizes (F1) | GitHub builder (root: page reader) | no | 29 wrong sizes, 4 in use |
| 4 | pin_problem field; v2 treats it as no pin (F2) | GitHub builder + v2 | no | 3 bad + 199 no-pin get a true reason |
| 5 | Ids from the page actually read for "no link" and Kentucky parks (F4, F5) | GitHub builder | no | 72 real ids + QC 69 page addresses (48 need a no-pin ruling) |
| 6 | Freshness stamp and shrink guard (F7) | GitHub builder + PC test | no | all (safety) |
| 7 | nps_code only from nps.gov (F12), curly apostrophe (F13) | builder / v2 | no | 147 / 26 |
| 8 | Hand download writes the store's own name; store wants the helper's proof (F10) | PC | no | cannot count |
| 9 | PC button to rebuild park facts (F8) | PC | needs the kit snapshot | all (speed) |
| 10 | Retire or relabel PARK-ID-MATCHER and its kpc_link_ids copy (F9) | PC | no | 0 (avoids mistakes) |
Widening page sizes (F15) is safe once fix 3 is in, but it gained 1 park: do it last.

## 5. Checked and sound
- Pins and names in the facts equal the saved POTA list v2 uses for its park list (19,242 rows, 1 name differs).
- Shared ids: every id on two parks is `usable: false`, and v2 also refuses them (37 tie-able ids shared; e.g. GRBA on Great Basin
  and a fish hatchery: refusing is right).
- Wrong ids: in MN, NY, MB, NS, SK, QC only US-5249 Pine Hill fails the id guard as a WRONG ID (record 297 km away); of the other 6
  guard failures, 5 carry the park's own name far from the pin (US-4239 North Country Trail 735 km, CA-0558, CA-1752, CA-1851,
  CA-6224: pin problems, F2) and 1 is the apostrophe (CA-1846, F13). None is a wrong id. 22 NY DEC ids are not
  in today's sgnya layer (likely renumbered pages; 20 of those parks are proven by name anyway).
- Separators and hectares: no "1.234"/"1 234" errors found; hectare conversions agree with the text (except km2, F1).
- Junk web names ("lands" 438, "species" ...) cannot reach v2: v2's page-name rule needs `name_match: strong`.
- Self-tests of kpc_park_facts, both kpc_link_ids copies: PASSED (offline). The GitHub frozen copies equal the KPC-Data checkout.
- v2 records the facts file's sha256 in v2-run.json; v1's reader runs on without facts, v2 refuses to run without them (good).

## 6. Not done / could not read
- `kpc_pc_upload.py` (the merge rule of the PC pack), `kpc_upload_pack.py` (PC side), `.github/agency-lists.json`, and
  `data/intake/official-pins-*.json` (pin fills for the 199 no-pin parks): not in the review copies.
- Whether the GitHub page-reader timer still runs, and how often park-facts.json.gz is committed on main (shallow clone here; check
  `git log -- data/park-facts.json.gz` for size growth).
- The acreage bot (3,045 lines) was mapped, not read through: its list matching and PDF rules are not audited.
- kpc_hand_helper.py and kpc_tidy.py were mapped by their functions; only judge/strong_match and guess_area were read.
- MA, GA, NC, ND, SC, VT could not be built (store gaps), so F3's gain there is not counted.
