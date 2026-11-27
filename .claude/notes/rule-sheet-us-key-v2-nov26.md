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

## 16. Ruled 27 Nov 2026, 5:45 AM (owner)
Asked: "is the trail bot's pick enough when the park's pin is within 100 ft of the line?" Owner: "Yes to trails".
**IN FORCE since 27 Nov 2026, 6:14 AM.** At 5:47 AM the owner passed on the grader's call ("NO for now ... an official agency
trail name/ID and strict <=100 ft check"). Asked which stands, the owner: "Trails pota could be wrong trust official" and "do not
trust old work". Read together with his yes: the official line is trusted; the trail bot's pick is old work, so today's pin
within 100 ft must confirm it. A trail park whose pin is farther stays without its line until an agency id or name proves it
(the grader's condition). The 100 ft check is strict and in code (rule `trail_bot_pin`); no real park was ever past it.
Why it was asked: the name inside a trail-bot file is typed in the trail bot's own list (the club's label for that park
number). It is not read from the agency. So "exact name" proves nothing for such a file.
- **What counts:** the trail bot's file for a park (layer `trl`, key `trl<n>`, ref `US-<n>`; the key and the ref must agree)
  joins THAT park, and no other, when the park's pin is within 100 ft of the line (`line_pin_m`). It adds the line to land
  the park already has, or it is the park's only record. It works for a park proven by an agency id too. The proof reads:
  "the trail bot's file for this park (US-<n>.json), the pin N ft from the line".
- **What does not count:** the name inside the file. It is never a name proof. The file never joins another park by name,
  even one with that exact name. A file whose key and ref disagree joins nobody.
- **Any line, any layer:** a line joins only on its own proof: it carries the park's agency id itself, or it has the exact
  name with the pin within 100 ft, or it is the park's own trail-bot file. A line never comes along with a park's land, with
  a same-named group, a unit, a project, a piece word or a piece of an id unit. Lines of web layers that are not trail-bot
  files (Utah `sgute`) keep the section 12 rule.
- **When unsure:** pin farther than 100 ft from the line = no line. The park keeps any land it has; with no land it stays
  pin only with `name_but_no_pin_or_size_proof` (the file is in the store, so `record_layer_not_in_store` would be untrue).
- **Real examples (measured on the MN and NY files with the trail lines, 27 Nov):**
  - US-4239 North Country: POTA's name is "North Country Trail National Scenic Trail", the file's is "North Country
    National Scenic Trail". The file is named for the park; the pin is 18 ft from the line. Joins by its file.
  - US-11151 Cuyuna Lakes, US-11154 Taconite, US-9382 Great River Ridge: the review read 92, 46 and 54 m, but those are the
    pin's distances to the parks' LAND. To the line itself the pins are 72, 89 and 31 ft. They keep their land and their line.
  - US-4556 Appalachian Trail (NY): proven by its Park Service id; gains its own line, pin 42 ft from it.
  - US-9388 Glacial Lakes: pin 112 ft from its line (34 m). Keeps its land, gets no line. US-9383 Goodhue-Pioneer: 282 ft
    (86 m) from its line, and its land of that name does not prove it either: pin only.
  - US-11153 Matthew Lourey: pin 3,873 ft from its line. Pin only.

## 17. Ruled 27 Nov 2026, 8:34 AM (owner): v2 is judged by itself
Owner: "Old keys and old information and v1 ... why judge against any of that cause it clearly wasnt not working .. why i have
to rebuild over and over.. end goal accuracy and efficiency excellent keys why judge against crap work.. I need a system that
works end to end and gives me excellent results".
This replaces the "against v1" parts of sections 7 and 8.3.
- **A gate now (pass / fail):** only what v2 is by itself. G2 no `~old` ids. G3 two names. G4 every joined record is in
  today's layer files. G5 a reason for every pin-only park. G9 the matcher's own gate (a typed area with no v2 key fails here
  now). G10 a lock never changes an answer. G11 no park on a same-named park's land. Ids and wording are as before.
- **Not a gate any more:** G1 same parks as v1, G6 outlined parks hold, G7 confirmed parks hold, G8 speed against v1 (and the
  MN + NY under 5 minutes part with it), H1 and H2 against v1, the store room gap, H3 same land as v1.
- **G1 is dropped, not replaced.** The park facts give each park one area, so they are not POTA's list for a state (a park
  listed in two states is in one area only). The scorecard reads no other park list, and no new input was added.
- **Information only:** when a v1 key is given, its numbers come last, under "Next to the old key (v1), for information only.
  Not part of pass or fail." With no v1 key that block is left out and nothing fails. No v1 number is in the first lines, the
  gates or the pass / fail line.
- **Quality numbers:** pin inside the land and size agrees with the official size are v2's own, printed with their counts in
  each area's second line, for example "pin inside the land 96.8% (183 of 189)". They are NOT pass / fail. No limit is set yet;
  a low number is for a grader to look at. Setting a limit is a new ruling.
- **Where it shows:** `V2-SCORECARD.txt`, `v2-score.json` (gates = only the gates above), `V2-BUILD-SUMMARY.txt` (v1 after
  "| for information") and `summary.csv` (`gates_failed` = only the gates above; the v1 columns are the last two).
- **Real example (Illinois, 27 Nov, built in a scratch folder from the IL layer file only, no v1 key):** 219 parks, 189
  outlined, 30 pin only; pin inside 96.8% (183 of 189); size agrees 10.3% (7 of 68); V2 PASSES. The PC's build of the same
  day had the same counts and failed G6, G7 and H2 against v1 before this ruling.

## 18. Ruled 27 Nov 2026, 8:37 AM (owner): one record, two parks ("same land, two park numbers")
The owner, passing on the grader's words with his yes: "Both parks may share the record (marked 'same land, two park numbers')
ONLY when each proves it on its own (own agency ID, or own name + pin inside the record). Unproved shared records stay a hard
gate fail. Never let a smaller park take a bigger surrounding park's outline (e.g., if a park's official acres are much smaller
than the shared record, it stays pin-only). Write every allowed shared-record pair to a small report list so reps can spot
dual-agency 2-fers vs. POTA duplicates." The grader: "if one park's official size is much smaller than the shared record (say
under half the record's acres), it cannot inherit the whole surrounding polygon" (Marrowbone State Forest / WMA: the allowed
kind; Cumberland Falls inside Daniel Boone NF: must NOT take the forest).
- **What counts:** a record claimed in ONE step by parks of two names (the old rule gave it to nobody). Each park keeps it only
  with its own proof on that record: its own agency id on the record itself (step 2; a piece of the unit with no id does not
  count), or its own exact name on the record with its pin INSIDE it (near the edge is not enough). And it needs an official
  size on file whose smallest value is at least half the record's acres (`shared_record_share` 0.5).
- **Outcome:** two or more parks prove it = both keep it, both marked `same_land` in the key (`note: same land, two park
  numbers`, `with`: the other park, its name, the record) and one row in `v2-shared-records.csv`. One proves it = that park
  keeps it alone. None = nobody, as before (`record_shared_with_another_park`).
- **When unsure:** no official size on file = unsure = the park does not take the record (proof or the pin).
- **Not changed:** a record held by a stronger step (id beats name), a record carrying another park's full name, a record
  holding another same-named park's pin. An id two parks claim is nobody's own id (rule `id_shared`).
- **The gate:** one record on parks of two names passes only when the gate, measuring again with the same functions, finds
  every park's own proof and size. Anything else is still a gate fail (exit 4).
- **Lake Vermilion (section 13) stays pin only:** both parks carry the same id (SPK00285), so it is neither park's own; neither
  exact name is on the records (PAD-US 209838 and sgmnd18 say "Lake Vermilion-Soudan Underground Mine State Park"); and
  neither park has an official size on file. Both pins are inside, which alone is not enough.
- **Measured 27 Nov (MN, NY, IL, ND, VT, AK files):** no key changed. No real pair proves it both ways today. The only park
  where the "no size = unsure" choice matters: US-8610 Valley City WMA (ND; pin inside the "Valley City" record, exact
  name, no official size). It stays pin only; with that choice reversed it would take PAD-US 215568 + ndw152 (801 acres).

## 19. 27 Nov 2026: an agency acres field that disagrees with its own outline is not trusted
Measured on Illinois: layer `sgild` writes its acres from a flat web map (Web Mercator), median 1.73 times its own outline, so
39 parks had the right land and the wrong size. Rule `acres_field_guard`, general, for every layer:
- Per layer of each area's file, records whose field says 5 acres or more, up to 100 picked evenly in id order, field divided
  by the measured outline. At least 20 measured and a median more than 10% above 1 = the field is switched off for this run.
- Switched off = the layer behaves exactly like a layer with no acres field: the key's sizes use the measured outline, and
  the field is no size proof and no "two sources" witness. Fewer than 20 = as before. A field SMALLER than its outline is kept
  (the agency may hold only part of what is drawn).
- `v2-run.json` lists, per area, `acres_field_off` (layer, median, records measured) and `acres_field_checked` (every layer).
- **Measured 27 Nov:** switched off: only IL `sgild` (median 1.731 on 100 records). Every other layer of the IL MN NY ND VT AK
  files: 1.004 to 1.011. IL: 131 parks' key text changes (each holds an sgild record): record sizes only, a new `ac` for 129, no join changes; size agrees 7 -> 46 of 68 (the
  scorecard's own count). MN, NY, ND, VT, AK: keys byte for byte the same. Time: AK 75 -> 79 s, IL 1.8 -> 2.5 s.

## 20. 27 Nov 2026 (grader, item 1): "two sources" means two real sources, never one record read twice
Grader: 79 parks in the US build were proven only by `name+two_sources` from two copies of one record (a layer with a blank
service address), 28 with the pin outside (20 Nevada BLM herd areas, up to 6.2 miles off). Rules `two_sources_independent`
and `two_sources_not_a_copy`:
- **Counts:** two named records of different layers, boxes overlapping, agency sizes within 10%, BOTH with a service address
  (the layer's url up to MapServer / FeatureServer) and the two addresses different.
- **Does not count:** a blank service on either side (unknown source); two layers of one service; agency sizes closer than
  0.1 acre (`two_sources_same_acres`: one record twice); the same id on both (record id, file key, or an agency id of a tie).
- **When unsure:** no proof, so pin only (or another proof: pin inside, id, official size).
- **The grader sees:** `service_a` and `service_b` in the proof's evidence, beside `source_a/b` and `acres_a/b`.
- **Examples:** NV `hma` / `sgnvi` (one herd-area record in two layers, same acres): no longer proof. `cow` / `sgcoa` and
  `rst` / `sgakg` / `sgnmc`: same kind of pair, same answer. Québec register read twice (round 8): still refused.
- **Not measured on the real layer files here:** the 79 / 28 counts are the grader's; rerun the scorecard on the PC to see them go.

## 21. 27 Nov 2026: a park's size is the ground it covers, not the sum of its records (grader item 3)
PAD-US holds overlapping outlines of the same land, so sizes were counted twice: New Jersey 1.89 times, Virginia 1.25,
Pennsylvania 1.19; New York US-10076 holds the same thin outline twice and showed 51 acres where 44 is right. The land was
right; only the measuring was wrong. Rule `size_union_not_sum`:
- Per layer and class (as before), after the "same ground, same name = once" skip, the records left are put in groups whose
  boxes overlap. Per group: 400 lines of latitude (`union_lines`) across the group's box; on each line the inside stretches
  of each outline (holes are outside) are merged; ground together / sum of the outlines = the group's share.
- The group's sum of sizes is cut by that share, never below its largest record. A record skipped as the same ground is not
  in any group, so nothing is taken off twice. The very same outline saved twice is a share of exactly 0.5.
- No overlapping boxes, or less than 1% overlap (`union_floor`: two neighbours' drawn edges crossing), = the old sum, bit for bit.
- The same number goes everywhere the size goes: `ac`, `acres_by_layer`, the name+size proof and the lock. Lines: no size, as before.
- Not measured on real files yet (no layer files in this session): which keys change in MN NY ND VT AK, and NJ VA PA US-10076.

## 22. 27 Nov 2026: a pin-only park in an area with a store gap says so (grade item 7)
Rule `reason_store_gap`, new reason code `no_record_store_gap`. Before, a park with no record of its name said `no_record_with_this_name` even when a layer of its area was missing from the store, which is untrue (the record may sit in the missing layer).
- Used only where the old answer would be `no_record_with_this_name` AND the park's own area has at least one layer gap (the same list as `gaps` in the key). Plain meaning: no record with this name in the layers we have; a layer of this area is missing from the store, so look again after it is downloaded.
- Every other reason keeps its place and order. A trail park keeps `record_layer_not_in_store`. A park with a named record but no proof keeps `name_but_no_pin_or_size_proof`.
- Only the park's own area's gaps count. `neighbour_gaps` (layers of neighbour areas that are read too) do not change any reason, and a park listed in two areas gets the reason of the area being built.
- No gap = no change: keys of areas without a gap are byte for byte the same. Nothing is decided from the v1 key (owner, 27 Nov: v1 is no judge); the matcher cannot know which park is in the missing layer, so the reason says only what is true.
- The reason's words are in the table `pin_only_reasons`; the reason counts in the build summary, scorecard and pin-only csv files are counted from the key, so the new code appears there by itself. The next tool should wait for the layer, not chase these as name problems.

## 23. 27 Nov 2026 (grade item 2): same short name, other kind of land
The exact rule takes the kind word off a park's name ("Calico Mountains Wilderness Area" -> "Calico Mountains") and then took
ANY record of that bare name. Nevada: US-0464 Ash Meadows National Wildlife Refuge (about 24,000 ac) held the BLM herd-area
records "Ash Meadows" (115,783 ac); after the two-sources fix US-9242 Calico Mountains Wilderness Area took the 162,605-ac herd
area and US-9271 Muddy Mountains BLM Wilderness Area went 44,400 -> 187,798 ac. Rule `name_kind_agrees`:
- **Refused:** the park's name or type says a kind, the record itself says a kind (its own names, or its layer's kind in the
  new table `single_kind_layers`), and no kind the record is known by is the park's.
- **`single_kind_layers`** (read from each layer file's manifest): herd areas hab / hma / NV sgnvi = hma; wilderness wbl / wld;
  wsa; BLM recreation areas and sites rma / rst / sgakg / sgnmc / AZ sgazg / CO sgcoe / OR sgorf = rma; river corridors fwsr /
  wsrc / OR sgorg / UT sgute = wsr; ACECs sgakh / sgnvh = acec. Used only to refuse, never to join.
- **Never refuses alone:** a PAD-US designation type or a park layer's kind (`layer_kinds`). A park layer holds historic sites
  too (NY "Olana"); Hawaii's Lava Tree State Monument is Des_Tp SHCA. They may agree, though (Oregon's Unity Lake State
  Recreation Site, Des_Tp SREC). No kind on either side = no opinion: a bare name in a park layer is the normal case.
- **`kinds_alike`** (pairs, never chains): POTA's types for BLM parks mix up the BLM designations: wsa-wild, wsa-rma, wsa-ca,
  acec-rma, acec-ca, ca-rma, hist-rma. Utah: 54 "BLM Recreation Management Area" parks sit on a WSA of their exact name with
  the pin inside (US-6073 King Top). Wilderness and a recreation area are NOT alike (else Muddy Mountains Wilderness took the
  128,292-ac SRMA).
- **New kind words:** "water management area" is its own kind (wmgt), not a wildlife management area (FL US-8335 Yellow River
  must not take the 27,245-ac Yellow River WMA); "acec".
- **What people see:** a park left with nothing is pin only, reason `name_on_other_kind_of_land`.
- **Measured 27 Nov (NV UT TN AL HI: 196 refused (park, record) pairs before the pairs table, 101 after; then OR CO IA):** NV: Ash Meadows 115,783 -> 24,517;
  Calico Mountains Wilderness 162,605 -> 64,559; Muddy Mountains Wilderness 187,798 -> 44,400; Mormon Mountains lost the herd
  area; Gold Butte NM and High Rock Canyon SRMA lost their only (herd area / wilderness) land. UT: Swasey Mountain HMA (only a
  WSA), Horseshoe Springs WMA (only an ACEC) pin only; King Top lost the herd area; three river parks lost recreation /
  wilderness polygons. TN: four WMAs lost the Corps "Recreation Area" around them (Barkley 17,799 -> 7,322). OR: Honeycombs and
  Bear Gulch "BLM Wilderness Area" pin only (their only record is an ACEC).

## 24. 27 Nov 2026 (grade item 2): the pin's own land beats a far two-sources proof
The longer-or-shorter rule ran only when the exact names proved nothing. So two maps agreeing on a piece 1-2 km away shut out
the record holding the pin. Rule `pin_beats_far_proof`:
- When the exact names proved land ONLY by two sources, the longer-or-shorter name is tried too. A record of it that holds the
  pin and is at least as big as the far land replaces the far land. A smaller one is a part, so the far land stays.
- Name + pin, name + size and id proofs are never touched.
- **Measured 27 Nov:** TN US-3935 Chuck Swan WMA 755 -> 23,925 ac (official 24,353); AL US-10428 Walls of Jericho 759 ac in
  Tennessee -> 12,330 in Alabama (official 12,617); HI US-6423 Manuka State Preserve 14-ac wayside -> 25,714-ac Natural Area
  Reserve (official 26,044); IA US-12191 Turin Preserve 892 -> 1,107. Kept: OR US-2860 Umpqua Lighthouse State Park (two
  sources 375 ac; the record at its pin is the 25-ac visitor centre).

## 25. 27 Nov 2026 (grade item 2): two sources must not contradict the official size
Two sources prove only that two maps agree with EACH OTHER. Rule `two_sources_size_agrees`, value `two_sources_size_band` 3:
- The park has an official size (the size witnesses) and the land the two sources agree on is more than 3 times smaller or
  larger than every official value = no proof. No official size = as before.
- **Measured before the value was set:** PC build, 262 two-source parks, 12 with an official size; ratios 0.011, 0.141, 0.156,
  then a gap to 0.495 ... 1.34. Out-after (50 US areas): 192 and 11. Drops: OR US-0503 McKay Creek NWR (21 of 1,837 ac), US-0499
  Cold Springs NWR (439 of 3,117).
- **Not used here:** the acreage bot's sizes that do not count as witnesses and page sizes that are not clean. They would also
  catch Chuck Swan, Walls of Jericho, Pearl Hill and Quechee, but they are wrong too often: for parks proven by the pin they
  disagree 3 times or more in 18% (bot) and 10% (page) of cases (HI US-2226 Wailua River: bot 1.12 ac). A ruling.

## 26. 27 Nov 2026 (grade item 2): a far proof stays in the park's own state
Rule `far_proof_own_state`: a proof that is not the pin (size or two sources) uses a group only when one of its records comes
from the layer file of an area POTA lists the park in (locationDesc). Pin proofs are never touched (parks near a border keep
the neighbour's records that hold their pin). Measured over out-after (50 US areas): one park has all its land from another
state's file by a non-pin proof: US-10428 Walls of Jericho.

## 27. 27 Nov 2026: what grade item 2 found that is not a rule fault
- **Page names (Manuka):** section 24 fixes it; section 25 does not (no official size). 33 parks are proven by a page name
  with size or two sources; 4 of them have a page whose name differs from POTA's (US-6423, US-6410 Iao Valley, US-9666
  Rosemont, US-2423 Gardner). Refusing those would drop 2-3 right ones: left for a ruling.
- **Aransas (TX US-0541):** no unit is missing from the store. fws785 (25,776 ac, the Matagorda Island unit) is in the file but
  its interest is "E", so rule `fws_interest_by_name` refuses it as not fee land. That is the easement rule doing what it says.
- **Little River State Forest (AL US-4598):** PAD-US 166058 (2,164 ac, exact name) is 1.5 km from the pin, one source, no
  official size on file, so it proves nothing; the pin is in the "Addition" (704 ac). Needs an official size (acreage bot).
- **Buck Hill (RI), Beaver Brook and Avon Bottoms (WI), Campbell Falls (CT), Glenwood (UT), Blackhawk and Harrier Marsh (IA),
  JL Curran (RI):** already changed by this morning's two-sources fix (section 20).

## 28. 27 Nov 2026: an easement is not joined by an agency id either (grade item 5)
Rule `easement_not_by_id` (function `id_not_fee`), plus the type field `matype` in the table `type_field_rx`.
Before: rule `easement_by_name` kept an easement out of every NAME join, but said "an agency-id proof is unaffected". So when a park's id matched an easement record, the easement came in with the rest of the id's records. Real case: Virginia's `sgvae` layer holds "NPS Easement" records (type field `MATYPE` = "Conservation Easement", owner Private or NPS, 0 to 348 acres). Their page link names the park (`nps.gov/pete`), so the NPS unit code joined them to Petersburg, Fredericksburg-Spotsylvania, Manassas, Prince William Forest and Cumberland Gap, up to 24 km from the pin. An easement is not park land.
- What counts: a record whose type field says easement (now incl. `MATYPE`), or whose name says lease / agreement, or a Fish and Wildlife record whose interest type is not fee (E, R, A).
- What does not change: the other records of the same id still join. Fee-owned units ("National Park", "NPS Holding", "USFS Holding", "State Scenic Holding") stay.
- Measured on the 27 Nov files (the new matcher against the same matcher without the rule): VA 9 parks change, TN 2, MN 0, NY 0.
  VA: 23 "NPS Easement" records leave (Fredericksburg-Spotsylvania 14, Manassas 4, Petersburg 2, Prince William 2, Cumberland Gap 1 by the TN file); 17 refuge easements leave (Rappahannock River Valley NWR 17, 77 to 816 ac each; Eastern Shore of Virginia NWR 2) and Widewater State Park's 127-acre "DCR Easement"; one 46-acre easement leaves the Appalachian Trail. Acres: Rappahannock 9,294 -> 7,664, Widewater 1,315 -> 1,189.
  All of them are `MATYPE` Conservation Easement, owner Private (or the agency holding the right), mostly "closed".
- Every outline stays confirmed; no park lost its proof.
- Which change did what: the 23 NPS and the Appalachian Trail records left through the id rule (they were id joins). The 17 + 2 refuge records and Widewater were NAME joins (step 3); they leave only because `matype` is now a type field, i.e. the older rule `easement_by_name` now sees them.
- Grey area for the owner: the refuges' own easement records (Rappahannock, Eastern Shore) were shown as part of the refuge before; they leave too. Say if refuge easements should be shown.

## 29. 27 Nov 2026: a park the facts do not know takes its name from POTA's list (grade item 6)
Rule `facts_fallback_pota_list` (function `pota_fallback`).
Before: a park on POTA's list with no row in the park facts (new parks) got an empty name and no pin in the key. Eleven parks: US-13665 to US-13672, US-6253, US-6257, US-6274 (and US-13670).
- A listed park whose facts row is missing, or has no name, takes the name (and the pin, when the facts have none) from POTA's own saved list. A facts name is never overwritten. The type stays blank until the facts have it.
- Measured on TN: the four TN parks (US-13670, US-6253, US-6257, US-6274) now carry their names; they are still pin only, "no record with this name", because the matcher found no record under those names (no size, no type known).
- Kure Atoll US-0121 is not touched: POTA now lists it under US-KI, there is no US-KI layer file, so it is in no key (see the report; a ruling is needed).

## 30. 27 Nov 2026 (whole-country check): a refusal never hands a contested record to the other park
Before, "two parks of two names claim it = nobody" (rule `same_step_two_names`) was the real guard. Any refusal of one of the
two parks switched it off. Kansas: US-2332 Clinton State Park 1,342 -> 22,656 ac (PAD-US 2474 "Clinton Recreation Area", the
Corps project, second name CLINTON) once the kind rule refused Clinton State Wildlife Area; Hillsdale, Milford, Perry, Tuttle
Creek; Ohio Deer Creek, Delaware, Dillon, Paint Creek. Rule `contested_name`:
- **Contested:** a record the names of parks of two or more full names reach (exact, page or two-language name keys, before
  any proof or refusal).
- **It stays with a park that proved it only when** every rival that would claim it also claims it. A rival "would claim it"
  when the record holds or nears the rival's pin at least as well as the park's own pin (inside beats near: TX US-3035 LBJ
  State Park keeps its record, the National Historical Park's pin is 41 m outside it), unless the record's own source (its
  layer, PAD-US type or type field) says a kind that is not the rival's. A record that carries the park's own exact FULL name
  is always the park's (SK CA-1149 Shamrock Regional Park). When the rival claims it too, the old rules decide
  (`same_step_two_names`, `shared_record_*`).
- **Otherwise nobody**, as when both claimed it. Uncontested records, id joins and parks of one full name (rules `other_pin`,
  `same_name`) are not touched.
- Why the source and not the name word: "Clinton Recreation Area" says "recreation area" (kind sp, the same as a state park),
  so a kind word cannot settle it; the herd-area layer can (NV hma67 "Calico Mountains" is no claim of Calico Mountains
  Wilderness, so Calico Mountains HMA keeps it).
- **Measured (12 areas rebuilt, kit = this worktree, against out-final):** KS: the five state parks lose the Corps projects
  (Clinton 22,656 -> 1,342, Hillsdale 13,176 -> 3,224, Milford 45,289 -> 1,007, Perry 39,453 -> 1,787; Tuttle Creek pin only);
  the three State Wildlife Areas keep their own sgksc records. OH: the four state parks back to 3,886 / 2,003 / 3,096 / 4,883.
  WA: US-13403 Loomis Lake State Fishing Lake loses sgwaa104 + PAD-US 271578 "Loomis Lake" (411 / 401 ac: the WA State Parks
  layer's Loomis Lake, which Loomis Lake State Park would claim). NV UT WY: no change (Calico HMA, Browns Park x2, Adobe Town
  keep their records). Other areas, read from out-final with the new functions (no rebuild): DE US-10682 McGinnis Pond State
  Fishing Lake gives up five "McGinnis Pond" land records (49-142 ac) the wildlife area's pin sits in; no other area.

## 31. 27 Nov 2026 (whole-country check): the kind rule, judged right
Rule `name_kind_agrees` lost true land in four ways. Fixes:
- **Page names** are judged by the PAGE name's kind (the agency's own word); a page name with no kind word = no opinion.
  MO US-5697 Atlanta Wildlife Area, US-5707 Lost Valley, US-10386 Compton Hollow; WA US-12344, US-12578 (DNR's NRCA); NM
  US-11796 Socorro, US-8273 Angel Peak; AR US-0637 Mills Park; CA-ON CA-5363 Fletcher Creek; CA-NB CA-5194 Manawagonish.
- **A recreation area is one kind whoever runs it:** new kind word `rec` ("recreation area"; it is also `sp` as before, so the
  longer-or-shorter rule is unchanged) and `kinds_alike` rec-rma: MT US-6443 Lowry Bridge SRA on BLM's Lowry Bridge; ID
  US-7365 St. Anthony Sand Dunes NRA keeps its SRMA records. A "State Park" stays apart from a BLM recreation area.
- **hist-sp alike:** FL US-3633 Koreshan and US-3619 Fernandina Plaza State Historic Sites are "... State Park" in fnl / sgfla.
- **A record's own type field** (new table `kind_fields`: BLM nca `sma_code` BLM_NM / BLM_NCA, NV sgnvf `NLCS_TYPE`): NV
  US-4393 Gold Butte National Monument's own "Gold Butte" monument records were also claimed by the Gold Butte herd-area park,
  so nobody had them. Checked by reading the NV name groups, not by a rebuild.
- Left as they are (other land, true catches): AR US-12760 Norfork NFH and TX US-6550 Cooper WMA (Corps "Recreation Areas"),
  WY US-6230 Cumberland WMA (herd area), Gold Butte on herd areas, NV US-9254 High Rock Canyon SRMA (wilderness), UT US-5998
  Horseshoe Springs WMA (ACEC), UT US-6045 Swasey Mountain HMA (WSA / recreation area), MT US-4548 Pompeys Pillar NM (434-ac
  ACEC). For the owner: OR US-13068 Honeycombs, US-13075 Bear Gulch, US-10487 Lake Abert ("BLM Wilderness Area" on an ACEC).

## 32. 27 Nov 2026 (whole-country check): the far land that has the park's size stays
Rule `pin_beats_far_proof`: no swap when the far land is within size_tol (10%) of a size the park has on file (any witness, as
information) and the pin's land is not. WA US-0340 Spring Creek Hatchery State Park: 37 -> 10 ac again (size on file 9.6).
The other swaps keep: Chuck Swan (far 755, size on file 24,396), Turin (pin's land 1,107 = size on file), Walls of Jericho and
Manuka (no size on file).

## 33. 27 Nov 2026 (whole-country check): only a real easement refuses an id join
Rule `easement_not_by_id` narrowed: only a record TYPE FIELD that says easement refuses an id join. A lease or agreement in the
name, and a Fish and Wildlife interest code, do not. A leased state park is the park: MI US-1527 Newaygo State Park ("leased
from Consumer's Energy") and US-3329 Tippy Dam get their outlines back, US-1487 Belle Isle its id record. Measured in
out-after (all areas but AK): 41 id-joined records an id refusal could touch: 38 by the type field (25 "NPS Easement" rows: 23 in the VA key, the
Cumberland Gap one also in KY and TN; the Appalachian Trail sgvae510687 in 5 areas, 8 Nova Scotia "Wilderness Area, Conservation Easement"), 3 by a lease name (the
Michigan three), 0 by a Fish and Wildlife code. The 38 stay out. Name joins are unchanged (`easement_by_name`).

## 34. 27 Nov 2026: a park named as a piece takes no sibling pieces
Rule `piece_park_no_siblings`. Found by Fable's whole-country check on the PC's layer files, not in the grade.
- Rule piece_suffix lets a park take the records named like its own record plus a piece word (East, West, Unit 2, a number).
- When the park's OWN name ends in a piece word, the park is one of the pieces. It takes the records of its own name only.
- Real case: CA-4478 Partridge Valley East Protected Area also took "Partridge Valley West" (637 ac), the land of park CA-4479.
- A whole park (Otis Pike Pine Barrens State Forest) still takes its East and West pieces as before.


## 35. 27 Nov 2026 (grade item 5, id joins): a shared DEC page proves only the park's own name
Rule `id_shared_page` (table `shared_page_kinds`). The id value in the park facts is right; the page is shared.
- NY DEC uses ONE page for a whole management complex. Real cases: Lake George Wild Forest took 3 Hudson River Special Management Area records 34-41 km away (page 53165); Pigeon Lake took Twitchell Lake (102484); Raquette Boreal took White Hill, Raquette River and Raquette-Jordan (83175); Mount Loretto took Butler Manor Woods (8291).
- Rule: when one id of a page kind is on records of two or more different names, the id proves only the records with the park's own name. Own name = the exact name (existing exact-name rules), or the same place words with another kind word ('Pigeon Lake Wilderness'), or the part before ' - ' ('High Tor Wma - Clark Gully'). The other-name records do not join by id; a name rule may still prove them.
- One name on the page: nothing changes. No record with the park's name on a shared page: the page proves nothing (pin only unless a name rule proves land).
- Only for the NY DEC page number and the page-address kinds. Not general: the MN DNR unit id and the NPS unit code ARE the park. Measured: Blanket Flower Prairie SNA holds Ole Huseby Homestead (same SNA id, 440 + 134 = 574 ac); Upper Delaware's records are named 'Scenic and Recreational River'; Montana FWP ids hold 'Fishing Access Site' records of the same land. The general form would cut those true joins.
