# Rule sheet: the clean v2 US key matcher (26 Nov 2026)

Owner's order, 26 Nov 6:02 PM: build a clean v2 matcher, test it side by side on MN and NY first, and fix future bugs one
clean way. Fable manages it; Opus and Sonnet build; keys are made on the owner's PC from now on.
The live `kpc_us_key.py` is NOT touched until v2 beats it on MN and NY in the PC test.

## 1. What v2 reads (and what it never reads)
Reads, and nothing else:
- today's layer files (`<store>\US-<ST>.layer-records.json.gz`) for the typed states and their neighbours;
- the park facts (`park-facts.json.gz`: each park's name, kind, pin, own-page id, official size);
- the park list for the state;
- small rule tables in `.github/` (`us-key-v2-rules.json`, `link-id-ties.json`, `keep-record-fields.json`, the neighbour table);
- its own lock file (section 4, step 1).

Never reads: old saved copies, `~old` hints, the website key, saved answers, person holds or locks, a row number from another
download. Only the PC diff tool reads the website key or an older test, to compare.
v2 imports none of `kpc_us_key`, `kpc_match_checks`, `kpc_same_land`. It is one small file, plain Python 3.12, no packages.

## 2. A record's name: two ids, each with one job
- **Inside one run:** a record is named by the layer file's own `key`. It is exact and unique in that one download.
- **Between runs (locks, published ids):** only the agency's own id, spelled `<layer>0<agency digits>` (`sgmnb06`). A row number
  never starts with 0, so the two can never be the same id. One function does the spelling; nothing else writes an id.
- A layer with no agency id has no between-runs id. Such a record can be joined today, but it can never be locked.

## 3. Loading
- A typed state builds only if every layer in its own file is `complete` in the manifest. If not: that state is NOT BUILT, the
  gap is listed, exit code 3. A neighbour's gap is listed but does not stop the state.
- Layers in `drop_layers` are dropped at load, so they never reach matching and nothing has to take them off later. Today:
  `sgmnb` (the MN statutory state forest line, which holds private land) and `sgnvg` (the Forest Service's administrative
  forest line: US-4491 Superior was drawn at 3,886,760 acres from it; its owned land is 2,093,610, official 2,092,769).
  Club rule: a forest is the agency's own land, never the proclamation line.
- A record with no shape is dropped at load and counted.

## 4. Matching: five steps, straight down, best proof first
Each step runs for ALL parks before the next step starts, so the answer never depends on park order.
A park that is proven at a step is done. It is not searched again.

1. **Check the locks (a witness; it never decides).** A lock is `(layer, agency id, record names, record count, summed
   acres)` saved for a park that step 2 proved on an earlier run. Step 2 ALWAYS runs fresh for every park. The lock is only
   compared with today's answer: `held`, or `locked_broken` with one reason (id gone, renamed, size changed, record count
   changed, id now claimed by a second park, the park's page id changed or is missing, park no longer listed).
   Why not the fast path of the first plan (Fable, after the independent review, 26 Nov evening): v2 builds a state in about
   15 seconds, so there is nothing to speed up; a lock that decides is one more place old information can get in; and the
   other builder's #392 runs (1843, 1852) showed it: a reused lock kept only its id rows and 31 parks lost land. A lock that
   cannot change a join cannot do that. Only step 2 writes a lock. A record with no size both times counts as unchanged.
2. **Agency id.** The park's own page id (park facts `link.id_kind` / `id_value`, the Park Service unit code, the id inside its
   page address) equals a record's agency unit id in today's file. All of today's records with that id are taken (pieces of
   one unit share it). `confirmed`, by `id`; the lock is written. A Fish and Wildlife wetland district takes its fee (owned)
   tracts only, never easements. If two parks claim one id, neither gets it by id; both go on to step 3.
   The id must make sense on the ground (review finding 5; US-5249 Pine Hill's page id pointed at a forest 300 km away): at
   least one id record holds the pin or shares a real place word with the park's name, and the land is within 10 km of the
   pin, measured to the shape. If not, the park is not proven by id.
   Pieces with no id: a record of the same layer under the same name, with an empty id of its own, close by, is a piece of
   the unit (US-5416 Michigan Hill, US-9099 Plantation Island). A placeholder ("N/A", a bare home page) is never an id.
   An agency's own number inside a record's web address counts too (`link-id-ties.json`: the NY DEC page number). The FWS
   `LIT` code and PAD-US fields other than the Park Service unit code are NOT ids: nothing on POTA's side proves them.
   Only measured rows (id kind, layer, field) are used; never "any field that happens to hold the same value".
3. **Name, with a second proof.** The record's name equals the park's name under the proven name rules only, AND one of:
   (a) the park's pin is inside the record or within 100 m of its edge (the owner's 24 Nov distance);
   (b) the agency's size agrees with the official size within 10%;
   (c) two official sources agree: records of two different layers carry the name on the same ground with the same size
       (the owner's pick of 25 Nov 9:50 AM).
   Name alone never joins. An old joined size is never proof. Also proven rules, each a table row:
   the same place under a longer or shorter name when the record holds the pin and the kinds agree (#390 rule 5); the name
   inside the park's own page address when the link bot rated it strong; place words run together (`Jansen Kill` =
   `Jansenkill`); `X Heritage Preserve and Wildlife Management Area` read as either kind; pieces named with a direction or
   a number (`... State Forest - East`). Records grouped by NAME alone join as pieces only within 10 km of the pin or of a
   proven piece. Records that share a REAL unit value (a wetland district's complex name, a refuge's own code, a trail's
   project) are one unit at any distance: a district is scattered by nature (Windom 17,913 acres, v1 17,804).
   Never by name: an easement or lease; a Fish and Wildlife tract that is not owned in fee (V2-G4); a record that holds the
   pin of another park with the same bare name (review blocker: one PAD-US record can hold two same-named forests in two
   counties: Pine Hill, Robert Moses, Tracy Creek, Bear Swamp). The rules live in `us-key-v2-rules.json`, one row each:
   exact name (v1's own exact-name test: a lone `s` left by an apostrophe is ignored, so `Knox's Headquarters` = `Knox
   Headquarters`); a possessive written as one word only as a second try (`DEVIL'S TRACK` = `Devils Track`); `Wildlife and Fish Refuge` = `Wildlife
   Refuge`; NY DEC `Wild Forest` / `Multiple Use Area` = `State Forest` when a real place word is shared; a thin shape must also
   be long, so a small square (under 40 acres) can still be measured. Never joined: water-only land (unless the park is a lake
   or river park), offices, a record carrying another park's full name.
4. **Pin only.** Everything else. The park keeps its pin and gets ONE short reason from a fixed list (section 6).
5. **The gate (hard stop).** After matching, before anything is written:
   - 0 record ids ending in `~old`, in joins or check rows;
   - 0 records joined to two parks under two different names (counted the way the PC test's wrong-land check counts it);
   - every joined record is in today's layer file;
   - every `confirmed by id` park's records really carry that id;
   - no joined record of a name-proven park holds the pin of another park with the same bare name.
   If the gate fails the state's key is NOT written, the broken rows are listed, exit code 4.

Two parks, one record: the stronger step wins (lock or id beats name). Same step, two different park names: nobody gets it,
and both parks say so in their reason. This is decided in the step, never stripped off afterwards.

## 5. What v2 writes (one folder per run)
- `US-<ST>.json.gz`: the key, in the shape the PC diff tool already reads (`parks[ref]`: `n`, `t`, `m` rows `[id, name, acres,
  how]`, `c`, `match {status, by, step, evidence}`, `ac`, `src`).
- `v2-proof.csv`: one row per joined record: park, record key, agency id, layer, step, the proof.
- `v2-pin-only.csv`: one row per pin-only park: park, reason code, short reason.
- `v2-run.json`: seconds per state, counts per step, the layer files' sha256, the gate's result, `locked_broken` list.
- `locks/US-<ST>.json`: written only when asked (`--write-locks`). In a test this is inside the test folder, never `data/`.

## 6. Pin-only reasons (the whole list)
`no_record_with_this_name`, `name_but_no_pin_or_size_proof`, `two_records_fit`, `record_shared_with_another_park`,
`water_only`, `office_only`, `layer_not_complete`, `record_layer_not_in_store` (v1 drew it from a layer today's store room
does not hold, such as trail lines). One per park. Check rows can therefore never be more than the pin-only parks.

## 7. Extra gates Fable added (better than the first plan)
- **Same in, same out.** Two runs on the same files give byte-for-byte the same key. No answer may depend on dictionary order.
- **A lock may never change an answer.** True by design now (step 4.1): the lock only reports. The PC test still runs twice,
  without and with locks, and the two keys must be the same byte for byte.
- **Tests that notice.** The test run changes every number and empties every table in the rule table, one at a time, and
  switches each rule off; the test named for it must then FAIL. A rule no test would miss fails the run (review finding 7).
- **The workbench (the owner's "second stage", 26 Nov 7:48 PM).** Nothing ever changes the key after v2. Instead:
  `kpc_test_v2.py MN NY --try my-rules.json` runs v2 with a trial copy of the table and reports which parks gain or lose an
  outline, whose land changes, and whether every gate still passes. The real key and table are untouched. A fix lands only
  as a table row + its test + that report.
- **Graded against facts, not against the old key.** For every outlined park the scorecard counts: pin inside the land, and
  agency size agrees with the official size. v1 and v2 are shown side by side on those two honest numbers.
- **Every rule names its test.** Each row of `us-key-v2-rules.json` has a `why` and a `test`. A test fails if a rule row has no
  test of that name. That is "one regression test per real bug", enforced by the machine.
- **Reasons from a fixed list** (section 6), so the review list cannot explode.
- **Speed is a test.** MN + NY must build in under 5 minutes on the PC; the target is under 1.

## 8. The repair method (every future fix)
1. Fix the rule once, in the step it belongs to (load, lock, agency id, name). Never a pass that strips bad joins afterwards.
2. One regression test per real bug, on a tiny fixture of the exact failure, named in the rule row.
3. The PC scorecard on MN + NY + one control state must pass before a merge:
   wrong-land two-name 0; `~old` rows 0; check rows not above the pin-only parks; faster or equal; outlined and confirmed
   hold or improve against `test-2026-11-26-1654` (MN 310 of 323, NY 822 of 851).
4. Later, before any 2-fer run on zero-led ids: `kpc_fers.source_of` must stop reading `sgmnb06` as row 6.

## 9. Real examples the tests must hold
- `sgmnb06` (agency forest 6) is never `sgmnb6` (row 6).
- `Knox's Headquarters` joins `Knox Headquarters` (first try); `DEVIL'S TRACK` = `Devils Track` (second try only).
  (Fable had this backwards in the first sheet; v1's code and the owner's paste say the possessive is the SECOND try.)
- A true 28-acre square is measurable; a 25 m strip is not.
- US-0356 (a wetland district): fee tracts only, no easements.
- US-7145 Minnesota Valley SRA: all its state-land pieces come by the one unit id (`SRA00304`), not by row numbers.
- US-4236 Upper Mississippi: `National Wildlife and Fish Refuge` = `National Wildlife Refuge`; but its pin is about 350 m
  outside the outline and no size proves it, so it STAYS pin only (#392 found the same).
- US-11024 (SNA02027): a lock saved at 440 acres breaks when today's records with that id add up to 574.
- Four NY Park Service sites saved as 0 acres: the lock holds.
- US-12060 Crystal Lake: `Wild Forest` = `State Forest` with the place word `Crystal Lake`.
- US-0681: never a `~old` record.
- Two parks, one record, two names: neither gets it.

## 10. Not decided here (grey areas, numbered, none blocks the side-by-side test)
- V2-G1: when v2 replaces v1, its file joins the US rule files and the rules hash moves once. Not while it is side by side.
- V2-G2: a park proven by name whose pin is outside every record but whose size agrees: v2 joins it (size is proof). Listed in
  the scorecard so the owner's test can see them.
- V2-G4: Fish and Wildlife easement tracts (private land under an easement). v2 leaves them off every park by name, the
  same as the owner's 29 Oct ruling for wetland districts. v1 drew 35 of them on US-0367 Northern Tallgrass Prairie. The
  owner may rule otherwise for refuges.
- V2-G5: an agency page or project number that groups other named land with the park (US-10293 Raquette Boreal: 21 records
  under four names, one a fishing access site). v2 keeps them (the agency's own id) and lists them in
  `v2-id-other-names.csv` for the owner's eyes.
- V2-G6: the store room's own gaps v2 found: no trail-line layer (17 MN + 4 NY parks cannot be drawn); SC's `sgnca` download
  failed (SC is not built); a layer with one shapeless record is marked not complete (MA, NC, VT); the Iowa layer repeats
  row keys inside MN's file (290 records dropped).
- V2-G3: records published by a row number (layers with no agency id) cannot be locked; they are matched fresh every run.

## 11. What the first full run showed (26 Nov, 8:40 PM, Fable's own run on the PC's MN and NY layer files)
- Scorecard: V2 PASSES, every gate. Outlined, fair count: MN 293 -> 295, NY 818 -> 819. MN + NY build in about 40 seconds
  (v1: 7.2 minutes). Check rows 767 -> 0; every pin-only park has one reason.
- Pin inside the land: MN 86.9% -> 87.5%, NY 98.4% -> 98.8%. Size agrees: MN 34 -> 35 of 40, NY 29 of 36 -> 29 of 37.
- The same land, measured on the shapes: v2 covers at least 90% of v1's land in 93.5% of MN parks and 95.4% of NY parks.
  Where it does not: 29 parks where v1 held another unit's land (402,030 acres: Red Lake WMA on Red Lake State Forest, state
  park units on same-named state forests, PAD-US records spread over two same-named forests), 4 parks left out on purpose
  (easements, land under water), and none where v2 misses the park's own land.
- No park on a same-named park's land: v2 0, v1 5 (Pine Hill, Robert Moses, Tracy Creek).
- Still pin only on purpose in NY: US-0474, US-2147 (need an "other spelling"), US-10040 (only an old size proves it),
  US-10045 (the record names two parks), US-13624 (a trail strip with no pin on it), US-2011 (pin outside the land).

## 12. Trails and far-away pins (owner 26 Nov 9:09 PM: "go ahead and do all that")
- **Why the trail parks are missing:** the store-room tool leaves trail lines out on purpose (`kpc_layer_records.py`:
  `NOT_LAND = {'trl', 'line'}`, "Trail lines are not layers of land") and drops every record with no polygon. No layer file
  holds a line today. That is KPC-Store work; v2 is ready for it.
- **A line in a layer file** (the format v2 reads): the usual record with no `rings`, and `"paths": [[x0, y0, dx, dy, ...]]`
  in the same spelling as rings, plus `"shape": "line"`.
- **A line joins a park** by its agency id, or by the exact name with the pin within 100 ft of the line (`line_pin_m` in the
  table). Never by size, never by a longer or shorter name. Only a trail, river, route or greenway park may take a line by
  name. A line is 0 acres everywhere. The key says `"line": true` when a park is all lines.
- **A far pin** (US-4572 Lewis and Clark: pin in Omaha; the park facts hold 15 parks with "Lewis and Clark" in the name): the
  10 km limit and the pin are waived only when POTA's own list puts the park in two or more states (`locationDesc`), the
  agency id matches, and a record carries the park's full name. A one-state park never gets the waiver (Pine Hill stays refused).
- **Tested how:** the far-pin rule ran on the real MN and NY files and changed no park (no trail record is in the files).
  The line rules are tested on small made-up examples ONLY. Nothing here is proven on real trail lines yet.
- Grey area V2-G7: the Park Service boundary layer `sgmac` (in the MA file) carries unit codes and would reach US-4567 Captain
  John Smith at 168 km; it is not tied, because it is a new tie and that park is a water trail. Measure: Opus's
  `out/measure-sgmac.txt` (26 Nov). US-4239 North Country: the record's name is "North Country National Scenic Trail", the
  park's is "North Country Trail National Scenic Trail"; the exact-name check refuses it (an "other spelling" case).

## 13. Ruled (owner, 26 Nov 9:27 PM: "Sure", to the grader's three points on #393)
- V2-G4: Fish and Wildlife easement tracts are kept off by NAME, and off wetland districts by id. (Exact wording, from the
  grader: a park that is not a district and is proven by an agency id can still hold an easement tract that carries that id.)
- Lake Vermilion US-2506 / US-7148: both stay pin only. One record carries two park names; the pins are about 2,457 ft apart.
- The fair count stands: parks v1 drew only from layers the store room does not hold are set apart and listed; the scorecard
  prints the raw and the fair count every time.

## 14. Ruled later on 26 Nov (owner)
- 9:20 PM: v2 is not a test version. It builds any US state and Canada on the PC; everything stays on the PC until proven
  ("no reason to lock it down"). A store-room gap no longer stops an area: it is built and flagged.
- 9:46 + 9:49 PM, THE SITE RULE ("avoid servers if they say no plain and simple"; "it thinks it's blocked but it's not"):
  a site is blocked ONLY by a real Disallow line in its robots.txt. Everything else is "not now" at most and is never saved
  as blocked. The full table is in the PR's notes folder: `net-rules-nov26.md`.
- 9:53 PM, Canada: sizes in hectares or km2 are converted to acres ("of course"); a French-only record may join an
  English-named park, and mixed names too, when the place words and the kind agree ("of course"); place words are never
  translated; a second proof is still needed.
- 9:53 PM, licences: "we don't want to get information that's not meant to be shared; we may use it privately but not share
  it". v2 may read a private record to prove a match, and marks it: each park says share all / part / none and lists its
  private records; a record with no licence answer counts as private.

## 15. Ruled 27 Nov 2026, 4:15 AM (owner)
- **A layer that is not land is nothing to wait for** (asked: "both are held up by a layer that is points, not land (264 parks).
  Should v2 stop waiting for a layer like that?"; owner: "i guess"). Rule `load_no_wait`, two tables: `no_wait_layers` (a layer
  by name, with proof it holds no land: `sgaki`, the Park Service's National Register locations, "NOT A PARK LAYER" in the
  club's verified-layers list) and `no_wait_status` (the store room's own word `not_land` = all records are points). Such a
  layer is not a store-room gap: exit 0, no "(store gap)" on the tool line, and v2-run.json lists it under `not_waited_for`.
  Every other status (failed, missing, empty, refused, not now, held) is still a gap. No join changes.
- Measured: ND 93 of 155 outlined, clean (was flagged for `sgaki`). VT 78 of 109, still flagged for `vta` until the store-room
  rebuild says whether its 483 records are points. MN 295 and NY 819: key text unchanged.
- **The site rule changed for a 401 / 403** (owner: "sure we are just polite"): see `net-rules-nov26.md`. v2 itself never
  contacts a server; this is for the store room and the page reader.
