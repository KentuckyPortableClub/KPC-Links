# KPC quick review: mapping + 2-fer code (Fable, Oct 31 2026, read-only)

Brief: `.claude/inbox/FABLE-QUICK-REVIEW.md`. Nothing was changed. Read: KPC-Links `.github/scripts/kpc_fers*.py`, `kpc_us_key.py`, `kpc_ca_key.py`, `kpc_world_key.py`, `kpc_key_*.py`, `kpc_us_trails.py`, `kpc_state_trails.py`, `kpc_ky_key.js`, the site's map scripts (`kpc-bounds.js`, `kpc-overlap-finder.js`, `kpc-park-info.js`, `kpc-in-park.js`, `kpc-kit.js`, `kpc-access.js`, `gis-overlays.js`, `kpc-park-control.js`); KPC-Data `kpc_layer_collector.py`, `kpc_tiers.py`, `kpc_key_questions.py`, `kpc_key_summary.py`, `kpc_waiting_room.py`, `kpc_release_approved.py`, `kpc_auto_flow.py`; and the data they write (`data/fers`, `data/us-key`, `data/ca-key`, `data/world-key`, `data/canada-bounds`, `data/world-bounds`, `data/trails`, `data/waiting`). Counts below come from one-off read-only scripts over those files.

How sure: **sure** = read the code and saw it in the data; **likely** = read the code, traced it, not seen in a run; **check** = needs a run or a person to confirm.

Line numbers are from commit `6f50e31` (KPC-Links) and `ebb0795` (KPC-Data), Oct 31 ~10:45 CDT.

---

## PART 1. Ranked findings (most parks / pairs affected first)

### 1. World outlines are SAVED at 60 points a ring, 4 decimals, 12 pieces (every world park drawn)
- Where: `kpc_world_key.py:36` (`THIN_N = 60`), `:403` (`thin()` = every Nth point), `:458/:497/:548/:633/:680` (every record stored only as `thin(rs)`), `:1030-1032` (shards: 50 points, `round(q, 4)`, `[:12]` pieces), `:50` (the cache saves the thinned ring); drawn by `kpc-bounds.js:405-406`.
- What is wrong: R-G6 says every saved outline is simplified by at most 3 m, never "every Nth point". The world key never keeps the full ring, so even `GEO_THIN=250` cannot help; the shards are then re-thinned to 50 points on an 11 m grid, biggest 12 pieces only.
- Example: `data/world-bounds`: 12,410 parks, 25,936 rings, median 62 points a ring, median segment 91 m, 90th percentile 628 m (GB-0010 Dee Estuary: 62-74 points a ring).
- How sure: sure.
- Smallest safe fix: keep the full ring in the record (`_r` full; a separate `_t = thin(rs)` for the pin-inside tests) and in the shard writer use `simplify(0.00003)` + 6 decimals, all pieces, gzipped. (The world finder is frozen to Nov 6: note only.)

### 2. The 0.6° pin box is a hard cut in all three keys: the agency's own same-name record farther away never joins
- Where: `kpc_us_key.py:935` (`close = ... near(la, lo, a['_bb'], .6)`), `:937` (0.1° when one name has no kind word); `kpc_ca_key.py:499`; `kpc_world_key.py:792`; the cross-state step `kpc_us_key.py:1500-1532` only writes `joined_in`, it never joins.
- What is wrong: Rule G-1 (Brandon Oct 29 12:14) says a record that NAMES the park joins at any distance. The box runs before the name test, so those records are left in `nonum` with no note. It is in degrees: 67 km at 38 N but 33 km of longitude at 60 N. A multi-state park has one pin, so the other state's half is cut the same way.
- Example: US-4424 Ouachita NF: the Oklahoma file says `pin`, Oklahoma PAD-US record 3001 (353,440 ac) sits in `nonum`; US-4385 Umatilla NF (WA half 311,020 ac); US-4481 Sawtooth (UT 71,846 ac); US-0661 Gulf Islands NS (MS 57,793 ac); US-4594 Tanana Valley SF: 11 records joined, ~50 same-name `sgakc` records (5k-200k ac) not; US-0143 Alaska Maritime NWR: 3 PAD-US records (478k / 464k / 391k ac) not joined. 27 multi-state parks joined in some states only; 107 exact-name records across ~30 parks in the top-300 `nonum` alone (undercount: `nonum` is capped at 300).
- How sure: sure.
- Smallest safe fix: let the name test see every record (`close` only for the 'words' path), keep full-name / agency-id matches at any distance (G-1 branch `:1264-1265`), hold the rest; same split in the Canada and world keys.

### 3. US record ids are fetched back with NO name check, so a renumbered id silently swaps in another park's outline (bug 5's other half)
- Where: `kpc_fers.py:389-395` (`source_of`: every US branch returns `chk=False`), `:499` (`not chk or name_ok(...)`); the by-name fallback `:473-497` only fires when the id is MISSING; `kpc-bounds.js:239-252` (`usKey` fetches by `objectIds`, no name filter) and `:400` (`worldKey`); `kpc_us_key.py:1401-1412` (`np_['m'] = om` keeps old ids when a layer did not read); `overrides.json`: 291 `no` ids and 102 `join` ids have no `fp`; `kpc_key_answers.py:135` writes `no` ids with no fingerprint.
- What is wrong: the key stores `[id, name, acres, how]`, so the name IS there, but the 2-fer download and the site draw whatever polygon now carries that OBJECTID. Iowa was caught because the ids were gone; an id that still exists but now points at a different feature is accepted with no check. Canada is protected (`chk=True`; `caKey` name filter `kpc-bounds.js:371`); the US and the 17,901 EEA-only world parks (CDDA layer, republished yearly) are not.
- Example: `data/fers/far-check.json`: 34 rows "none of X's official records holds this spot (our saved outline did)", 28 of them Florida `fnl` / `sgfla` joins (Fakahatchee Strand 737 km, Torreya 622 km): the cached polygon and the live record of the same id disagree.
- How sure: likely (the Florida evidence fits renumbering; a stale cache would look the same).
- Smallest safe fix: `source_of` returns `chk=True` for every US prefix and `name_ok` compares with `parks[ref]['names']`; `usKey` filters fetched features by the name field against `x[1]` as `caKey` does; `kpc_key_answers` writes `fp` for NO rows too.
- Also in the by-name fallback itself (`kpc_fers.py:492-495`): it keeps ONLY the nearest same-name record (`fs = fs[:1]`), so a park with several tracts of one name loses the others, and every missing id of that park maps to the same record (one tract counted twice). Fix: keep every same-name record within the park's own box (R-G5), de-duplicated by geometry.

### 4. 894 chat 11 YES answers on world layers go nowhere (`st` cut wrong, then "no state")
- Where: KPC-Data `kpc_layer_collector.py:392` (`'st': st[3:]` in `ext_row`), `:110`; consumer `kpc_key_layers.py:37-39, 71, 78-80`.
- What is wrong: for an outside-research row the area is `W-MX`, so `st[3:]` gives `X`; BOT W's `st_of()` strips only `US-` / `CA-`, so the row fails the `[A-Z]{2}` test and is skipped as "no state". The world branch at `:71` only runs for `_intake` rows, so a YES on a world layer is never wired into `data/world-key/extra-layers.json`.
- Example: `data/waiting/questions/layers.json`: 894 YES rows with area `W-*` (AU 332, DO 110, MX 90, ZA 48, IT 43, GB 42...), e.g. MX-0033 Cumbres de Monterrey = SURE on SEMARNAT's SIVECA layer. The nightly notice shows only "skipped 894".
- How sure: sure (re-ran BOT W's checks over the file: 894 "no state", 39 wired).
- Smallest safe fix: in `ext_row` write `'st': st[3:] if st[:3] in ('US-','CA-') else st.replace('W-','')` (as `test_crawled` does at `:206`); in `kpc_key_layers.py` treat a `W-` area like the intake world branch.

### 5. "NOT SURE" is read as "NO" wherever `startswith('NO')` is used (518 rows)
- Where: KPC-Data `kpc_tiers.py:146,150` (`yes = 0 if a.startswith('YES') else 1`; `if a.startswith('NO'): self.no.add(...)`); `kpc_auto_flow.py:73-74`; `kpc_week_numbers.py:47` (its `'NOT SURE'` branch is unreachable).
- What is wrong: chat 11's NOT SURE is (a) added to `Learned.no`, so the hunter / world finder never re-ask it; (b) counted as NO for the 10 %-YES demotion of a layer or area; (c) blocks AUTO-1 ("chat 11 said NO before"); (d) counted as NO in the weekly numbers. The brief's bug 6 class (a brittle text check), in the other direction.
- Example: 518 NOT SURE rows across gis-hunter / world-finder / key-pieces are in `Learned.no`; `arcgis.mma.gob.cl/.../SIMBIO_AP/FeatureServer/0` is demoted on 0 YES / 76 "NO" when all 76 are NOT SURE.
- How sure: sure (counted).
- Smallest safe fix: one shared `answer_of()` that returns YES / NO / NOT SURE from the first word (`re.match(r'(YES|NO|NOT SURE)\b', a)`), used by `kpc_tiers`, `kpc_auto_flow`, `kpc_week_numbers`, `kpc_key_answers:80-82`, `kpc_world_answers:46`, `kpc_ca_answers:47` (those three today accept only the exact words `YES` / `NO`: `Yes.` or `YES (sector)` is silently nothing).

### 6. The release gate (bug 6) is still brittle: `by` must be exactly "chat 11", and "YES ... NO ..." releases
- Where: KPC-Data `kpc_release_approved.py:80`: `re.match(r'^(?:KEY |LAYER )?(YES|PASS)\b', v, re.I) and str(it.get('by') or '').strip().lower() == 'chat 11'`.
- What is wrong: (a) an item chat 2 created (`by: chat 2`) that chat 11 then filled with its YES is skipped as "no YES / PASS written by chat 11". (b) The regex is start-anchored: a leading quote, emoji, `**YES**`, `KEY: YES`, `KEY  YES` (two spaces), `I think YES` are ignored; it reads only the first word, so `YES but NO to 3`, `YES/NO`, `PASS? No.` all release. (`.strip()` does handle `\r\n` and NBSP; `Yes.`, `yes 1-5`, `YES to all` pass.)
- Example: `data/waiting/released.jsonl` 2026-10-31 13:29Z and 15:15Z: `fers-US-MN` and `fers-US-IA` (`by: chat 2`, `chat11: "YES 2026-10-31 ..."`, chat 2 rechecked) both logged `skipped: no YES / PASS written by chat 11`. Two states approved by both chats are not live. 22 such skips in the log.
- How sure: sure.
- Smallest safe fix: accept the YES when the `chat11` field is non-empty whatever `by` says (the field name already says who wrote it); strip leading non-letters before the match; refuse when a standalone `\bNO\b` appears in the first sentence.

### 7. The 31 national trail lines are saved at ~80 m detail and used for a 100-ft rule (every national-trail pair, Kit, Am I in the Park)
- Where: `kpc_us_trails.py:47` (`TOL = 0.0008`, comment "about 80 m: plenty for a trip-planning map"), `:65` (`outFields` = the object id only); read for the 100-ft test by `kpc_fers.py:264-287` and now by the keys (`kpc_us_key.py:1341-1343`, `kpc_ky_key.js:104-108`) and `kpc-bounds.js:172-178`. State trails are at 3 m (`kpc_state_trails.py:117` `0.00003`).
- What is wrong: R-G6 says trails are saved at 3 m, never over 5 m. A line that can sit 80 m off the official one cannot support a 30.48 m test; Am I in the Park's "within 100 ft" and every trail 2-fer stretch inherit that error. Dropping every attribute also loses the Park Service's route field (land route vs water route, see 12).
- Example: all 20 NHT + 11 NST files in `data/trails` (Appalachian, Pacific Crest, North Country, Trail of Tears 13,569 points for 3,780 parts...).
- How sure: sure.
- Smallest safe fix: `TOL = 0.00003`, `geometryPrecision 6`, keep the layer's name / route fields in each part's properties (the files get bigger: gzip them).
- Related (sure): `kpc_us_trails.py:97-98` turns a POLYGON layer's rings into "lines" (`if t == 'Polygon': return c`), and `:53` falls back to a polygon layer. Ala Kahakai NHT (US-4565) has only the official CORRIDOR polygon, so `data/trails/US-4565.json` is one closed 932-point "line" and the 2-fer line tests the corridor's EDGE with a 100-ft band instead of the corridor area (the key joins the `akht1` polygon correctly). Fix: refuse Polygon/MultiPolygon in the trails bot (note it, skip), drop US-4565 from `kpc_us_trails.json`; and in `kpc_us_key.py` give the `trl` line only when the park has no polygon in ANY state file. Closed rings also appear in US-4569 (25 of 110), US-4581 (20 of 68), US-4559 (14 of 857): check whether loops or polygons.

### 8. `usKey` ignores `joined_in`, so every multi-state trail park is "Pin only" in the state POTA files it under (Kit, Park Info, Access Finder, US planner)
- Where: `kpc-bounds.js:232` (`if (grade === 'pin') return { state: 'none' ...}`), `:226-230` (only the caller's `states`).
- What is wrong: the US key marks a park `g: 'pin', joined_in: [other states]` when another state's file carries its line / outline (90 such rows). `usKey` returns `none` at the first `pin` without looking at `joined_in`, and callers pass only the first POTA state. Also: the line-carrying key files exist only in KPC-Links today; KPC-Data (read first by `KPC.dataUrl`) still holds the all-`pin` copy; the new one sits in `data/waiting/in/`.
- Example: `data/us-key/US-TN.json` US-3791 `"g": "pin", "joined_in": ["US-NC","US-AL",...]` → Kit / Park Info / typed Access Finder search / US Trip Planner say "Pin only (no official outline yet)" for the Trail of Tears; same for US-4556 Appalachian Trail (CT), US-4572 Lewis and Clark (MO / IA).
- How sure: sure.
- Smallest safe fix: in `usKey`, when `p.g === 'pin' && p.joined_in`, push those states onto the loop before returning `none`; release the waiting-room key (or let `dataUrl` prefer KPC-Links for `data/us-key` until then).

### 9. World grade: EEA (Natura 2000 / CDDA) outlines are drawn as "Official outline" (17,901 parks)
- Where: `kpc_world_key.py:1050` (`_p['g'] = 'approx'`, only for EU-compilation joins; every other world park has no `g` at all); `kpc-bounds.js:410` (`approx` derived from the `how` text, never from `p.g`); `kpc_fers.py:224-226` reads world parks without the grade.
- What is wrong: rule W-2 says an EEA outline is APPROXIMATE, labelled "EU compilation of national data", never Official. An EEA join's `how` is `name`, so the card says Official. The key writes `approx`, the US / CA keys write `approximate`; 40,017 joined world parks carry no grade (Rule G: one grade saved per park).
- Example: 17,901 of 40,017 joined world parks are EEA-only (all FR Natura sites, ES, IT, PL...).
- How sure: sure.
- Smallest safe fix: set `g` for every world park (`'approximate'` for EEA-only / pin-inside / shared-words, else `'official'`) and in `worldKey` use `p.g` first, as `usKey` does at `:268`.

### 10. Canada: 273 outlines saved at cache detail (hundreds of metres), refine falls back to 220 m, no trail carry, no R-G3 hold
- Where: `kpc_ca_key.py:18-19` (`DETAIL = 0.02`, `PREC = 3` = 111 m grid), `:338-339` and `:360-361` (`q[::k]`, `ring[::st]`, 400 points), `:33` (cache saves these); `kpc_ca_fill_bounds.py:54-56` writes `canada-bounds` straight from that cache; `kpc_ca_refine_bounds.py:15` (`OFFS` up to `(0.002, 220)`); `kpc_ca_key.py:498-508` (one pass: name + kind within 0.6°, prefix match, "EVERY piece with that name joins"), `:592-598` ("G-1 holds nothing back here"); no equivalent of `kpc_us_key.py:1341-1343` (`trl` line).
- What is wrong: R-G6 (never over 5 m); bug 2's fix (trail park carries its official line) was done for the US and Kentucky keys only; the US split_places / G-1 / name-only prune (`:780-811, :1123-1137, :1319-1336`) have no Canadian counterpart (the Little Sextons class).
- Example: `data/canada-bounds`: 2,654 files at 5 m, 273 with no `detail_m` (median segment 628 m; CA-2242 12 points, 7.9 km segments; 119 of them the BC local / regional layer, 79 Québec ZEC), 14 at 10 m, 13 at 20 m, 4 at 45 m, 2 at 220 m. 19 Canadian trail parks have an official line in `index-state.json`; 15 are `g: pin` in the key (CA-5628 Bruce Trail, CA-5344 West Coast Trail, CA-1301 Barron Canyon, the Prince Albert NP trails CA-6144..6153). 76 Canadian parks 'well outside' yet `official`.
- How sure: sure (detail, trail carry); likely (holds).
- Smallest safe fix: in `fill_bounds` skip (pin only) any record coarser than 0.00005 and let refine fetch it; cap `OFFS` at 5 m (a park that cannot be read fine keeps the old file + a waiting-room line); replace `[::k]` with `simplify(0.00003)`; port the US `TRL` block and the `_pin_km` / chain hold into `kpc_ca_key.py`.

### 11. BOT W wires a whole layer into the key from ONE record-level YES, including polyline layers the key cannot read
- Where: `kpc_key_layers.py:67, 86-92`; consumer `kpc_us_key.py:461` (`raise RuntimeError('not a polygon layer')`), `:614-616`.
- What is wrong: chat 11 answered "is this record that park", but one YES adds the URL to `state-gis.json` for the state and puts the state on tonight's rebuild, even when the layer has more NO than YES. `kind` `trail` is not in `KINDS`, so it becomes `land`; the US key then fails every night with "layer not found (not a polygon layer)".
- Example: from today's YES rows BOT W would wire 39 layers; 31 are polyline trail / byway layers (NM `Historical_Trails_Lines` 16 YES, VA `USGS Trails` 24 YES, AR `Scenic Highways And Byways`); `BLM_Natl_Recs_poly` (WY) on 1 YES / 3 NO / 2 NOT SURE; `Idaho Routes` 1 YES / 2 NO; SK `CPCAD` 1 YES / 9 NO.
- How sure: sure for the wiring; likely for the nightly failures.
- Smallest safe fix: skip rows whose `kind` is `trail` (or whose layer is polyline) and require YES >= NO for the layer before wiring; route trail YES rows to the trail-layer list (`trl`) instead of `state-gis.json`.

### 12. Water-route trails (Trail of Tears, Lewis and Clark...) are tested TWICE: from the river bank AND from the coarse NPS line (bug 1: which does the code use? both)
- Where: `kpc_fers.py:1678-1681` (`if ... water_route(): got += water_route_spots(...)` then `if l_ref in LN ...: got += line_spots(...)` — not `elif`); `water_route()` `:1474-1475` decides by the trail's NAME for the whole trail; the trail files carry no route attribute (see 7).
- What is wrong: R5 / plain answer 7: a water trail counts 100 ft from the WATER'S EDGE. The bank method (`water_route_spots`) is right by the rule and the card label "WITHIN 100 FT OF THE RIVER BANK" is right FOR THOSE rows. But `line_spots` runs as well on the same lines with kind `trail`, painting 100 ft each side of the Park Service line, which the code's own comment says sits 0.2-3 km from the river. And because the whole trail is "water", the overland Trail of Tears routes (Northern, Benge, Bell) get bank spots from any river within 3 km of them (`:1521`: any water blob with 4 route points within 3 km and one within 1 km).
- Example: Ballard WMA x Trail of Tears x Lewis and Clark: the saved rows are all `kind: river` (bank), but the Finder also lights up the band (see 13); any WMA the overland Trail of Tears crosses near a river gets a bank row it should not.
- How sure: sure (double test); likely (overland routes: needs the route field to prove which parts are water).
- Smallest safe fix: make `:1680` an `elif` for water routes (bank only), and once the trails bot keeps the NPS route field, mark only the water-route parts `water` so overland parts use the line.

### 13. Water-route rows store a POLYGON (the bank strip's outline) that `slim()` and the Finder treat as a LINE: that is the Metropolis shading (bug 1: why the picture is wrong)
- Where: `kpc_fers.py:1534-1538` (`findContours` → `approxPolyDP` → every Nth to ≤120 points → `shape`), `:1420-1436` (`merge` keeps the BIGGEST piece's shape, sums `len_m`), `:2233` (`sharp_shape(..., closed=False)` for every `river` kind); `kpc-overlap-finder.js:254-256` (`bandRing(x.shape)` for `trail` and `river`), `:353, :426-427, :454, :489` (walk-in verdict and `landAt` use the band), `:518-521` (GPX / KML write the band).
- What is wrong: for a water-route row `shape` is the OUTLINE of the 25-33 m land strip along the bank, decimated to ≤120 points, so a 20 km strip becomes a loop of 400-1,000 m straight segments. The Finder draws a 30 m band AROUND that loop: an 85 m-wide ring, 30 m of it on the water, hollow inside, cutting straight across land hundreds of metres from the river. Walk-in status, veil and exports use the same ring. Line-only river parks (WSR lines) really do have a line `shape`, so the two `river` sub-kinds have different meanings and one drawer.
- Example: `US-3791+US-3793+US-4572@river@37.184,-89.049` (Ballard): 34 points, path 11 km, first-last 30 m, segments 445-1,037 m. `US-0703+US-3791@river@36.501,-88.068` (Fort Donelson). 405 water-route rows in the data, 104 live (25 in Kentucky).
- How sure: sure (measured the saved shape).
- Smallest safe fix: in `water_route_spots` keep the contour at `sharp_shape(..., closed=True)` (400 points, 1.5 m), set `shape_kind: 'polygon'`; in `slim()` use `closed=bool(s.get('water_route'))`; in `patchRings` push `{ring: x.shape, line: null}` for `water_route` rows (draw the dashed `srcLines` line separately as now). The Oct 31 "river only" bot fix does not touch this.

### 14. The "about 25.6 mi" is strip area ÷ 25.48 m over every connected water body (bug 1: are the miles right? no)
- Where: `kpc_fers.py:1537` (`len_m = k * CELL² / max(CELL, BANK - STATION_IN)`), `:1525` (strip = land ≥ 5 m inside the park and ≤ 30.48 + 2.5 m from ANY accepted water), `:1520-1521` (Oct 31 fix: a blob is "the route's water" when it touches the TILE edge), `:1430` (`merge` adds the pieces' lengths while only the biggest is drawn); `:838` (NHD fetched with `outFields: FType` only: the river's name is thrown away); `kpc-overlap-finder.js:90, :96, :151` (text says "stretches of trail", sums `len_m`).
- What is wrong: both banks of every inlet, slough and creek that connects to the river count; the strip is 33 m wide where the park line is in the water (30 % over); the tile-edge test is a property of the tile grid, not of the water (Mayfield Creek and the Ballard sloughs connect to the Ohio in NHD, so they still pass). The real bank length is never measured.
- Example: Ballard row `len_m 41135` (25.6 mi) in a park box 8 km x 6.5 km; LBL `US-3791+US-3792@river@36.982,-88.199` `len_m 109928` = "68.3 mi" while its drawn shape is ~11 km around. (The live KY rows are still the Oct 30 run; the Oct 31 fix has not landed in the data yet.)
- How sure: likely.
- Smallest safe fix: fetch NHD with `GNIS_Name` and accept only the blob named for the river the route follows (Ohio / Mississippi / Tennessee / Cumberland / Missouri...), or the blob with the most route points; report length as half the strip's perimeter; say "river bank" not "trail" in the Finder text.

### 15. The Kentucky key now stores the three trails as a `btrail` tract the 2-fer bot cannot read (bug 2's fix, Kentucky side)
- Where: `kpc_ky_key.js:55-58` (the `kyFor` fallback pushes `['btrail', name, 0, 'pin', 0]` FIRST) vs `:104` (`!pk.tracts.length` → the Oct 31 `trl` + `line: 1` block never runs); `data/ky-answer-key.json` US-3791 / US-4572 / US-11181 = `["btrail", ..., 0, "pin", 0]`, no `line`; `kpc_fers.py:198` (`btrail` passes the tract filter), `:594-595` (`KYF` has no `btrail`), `ky_geom` → `bad`; `:2648` (`TRAIL_BY_LINE` runs only when `REGION != 'ky'`); `:3032-3035`.
- What is wrong: the three trails now reach `official_parks` WITH ids, `ky_geom` cannot read the prefix, so passes 2 / 3 mark every row with them "not sure: the official outline of ... could not be read". Before the fix they had no tracts and were handled cleanly as line parks. The review issue also lists them under "matched only because the POTA pin is inside".
- Example: 36 live Kentucky rows with US-11181 / US-3791 / US-4572 (e.g. `US-11181+US-4484@trail@37.824,-83.626`, 45 stretches) flip to NOT SURE on the next KY pass-2/3 run.
- How sure: likely (traced, not run; the KY rerun of this morning is the first with the new key).
- Smallest safe fix: in `kpc_ky_key.js` run the `trl` block when every tract is `btrail` (or skip `btrail` in the line-57 loop); in `kpc_fers.py:198` add `'btrail', 'trl'` to the excluded prefixes so a trail park falls through to the line path.

### 16. Park Info never reads the Kentucky key; PAD-US name search is labelled "Official boundary"
- Where: `kpc-park-info.js:145` (`!o.ky` skips the key), `:162-169` (PAD-US fallback), `:43-46` (no `Category` filter).
- What is wrong: for every Kentucky park `boundary()` skips `usOutline` and never calls `KPCB.kyFor`, so it falls to a PAD-US name search with no Proclamation / Easement filter and prints "Official boundary from the USGS Protected Areas Database" + acres. The three trails are filed under TN / IA, take the US-key path, get `pin`, and show "Sorry, no boundary available" + an OSM line.
- Example: US-4484 Daniel Boone NF → the PAD-US proclamation polygon (~2.1 M ac) as "Official boundary"; US-0050 Mammoth Cave → the PAD-US designation, not the owned-only outline the key rules; US-11181 / US-3791 → no line.
- How sure: sure (KY path); likely (the proclamation record comes back from the LIKE query: `kpc-bounds.js:309` filters it out for the same reason).
- Smallest safe fix: in `boundary()` for `o.ky` call `KPCB.kyFor(o.ref)` first and label it like `kpc-kit.js:248`; add `Category` to `outFields` and drop Proclamation / Easement in `padus()`.

### 17. Am I in the Park: standing ON the trail says "ON THE EDGE, move farther in"; with no typed ref, trails are never checked; Park Commander ignores its trail layers
- Where: `kpc-in-park.js:99` (`best.e.km > margin ? 'yes' : 'edge'`), `:20-31` (`gather` loads KY polygons + PAD-US only), `:100`; `gis-overlays.js:117-119` (`insideCheck` loops `bounds` only), `:132`.
- What is wrong: for a line park `e.km` is the distance TO the trail (≤ 30.48 m); the "inside" test demands `e.km > 15 m`, so 0-15 m from the trail reads "edge" and 15-30 m reads "inside ... from the nearest boundary line": inverted. Without `?ref=` the trails are not loaded at all. Park Commander has the five KY trail lines in memory (`routes[k]`, `segDistKm`) and never tests them.
- Example: on the Sheltowee Trace at a trailhead inside DBNF; on the Dawkins Line (US-1253) → "NOT INSIDE any official boundary".
- How sure: sure.
- Smallest safe fix: when `isLine(best.f.geometry)` treat `e.km <= 0.03048 - margin` as inside and say "within 100 ft of the trail (X ft from it)"; in `gather()` add the KY trail lines via `KPCB.trailLine`; in `insideCheck` add a `segDistKm <= 0.03048` hit per checked line source.

### 18. "Pin inside" and "edge" are tested on the rough working copy with no slack (all three keys)
- Where: `kpc_us_key.py:971, :980, :987, :1027` (`inside(la, lo, ...)` for alias_all / Recreation.gov / alias / same-name joins), `:1066-1069` (`far`: 'edge' = bbox + 0.02°), `:1338-1339` (`pin_may_be_wrong`), `:1240` (`_slack` uses env `DETAIL`, not the cache's `used_detail`); `kpc_world_key.py:845, :857, :883, :934` (on 60-point rings); `kpc_ca_key.py:525, :536, :554` (on the 2.2 km copy).
- What is wrong: the R-G6 note allows matching on the rough copy only if every test adds that much slack. G-1's 100 m test does; these do not, so a pin a few hundred metres inside the real line reads as outside (join missed, park flagged `pin_may_be_wrong`) and the reverse.
- Example: US key: 101 `alias name (pin inside)`, 36 `same name + pin inside`, 3,612 `far: edge`, 124 `pin_may_be_wrong`; world: 1,371 `pin inside + shared name words`, 348 `pin inside + same name`, 81 JP pin-only joins; Canada: 76 'well outside' yet official.
- How sure: likely.
- Smallest safe fix: `inside(...) or _pin_km(a, la, lo) <= _slack` (the helper exists at `:1229`) and compute `_slack` from `used_detail`; in the world key test on the full ring once finding 1 keeps it.

### 19. AUTO-2's land-class filter misses most land-type layer names; the layer collector has no such filter (bug 7 class)
- Where: KPC-Data `kpc_auto_flow.py:21-22` (`LANDCLASS = sssi|sac|spa|ramsar|special (area|protection)|scientific interest|zone|...`), `:125`; `kpc_gis_hunter.py:196`, `kpc_world_finder.py:107` (`sssi|sac|spa|ramsar` only); `kpc_layer_collector.py:105,199,344` (tier only, no name check); `kpc_key_layers.py:54` (BOT W wires on `approved_by` only, no land-class check).
- What is wrong: AUTO-2 / T-4 exclude land-class or coverage layers (SSSI, SAC, SPA, Ramsar, zones, parcels, Natura 2000 habitat, generic protected-area / land-cover). The regex has no `natura`, `habitat`, `designated`, `protected area`, `land cover`, `easement`, `surface management`, `aonb`, `biosphere`, `heritage`. A READY row with 3 SURE name matches on such a layer gets `approved: true`.
- Example: real titles in `data/intake/queue.json` / `found-layers.json` that slip: `Natura 2000 sites`, `Habitats and Birds Directive Sites`, `Nationally designated areas (NatDA)`, `Areas of Outstanding Natural Beauty (England)`, `Biosphere_Reserves_England`, `Conservation Easements 202610`, `BLM National Surface Management Agency`, `Landschaftsschutzgebiete`. `data/intake/ready.json` now carries `approved_by: "chat 9"` on the England SSSI units row, so on the next US-key plan run BOT W WILL add `SSSI_Units_England/FeatureServer/1` (28,305 unit polygons) to `extra-layers.json` for GB.
- How sure: likely (regex tested on the real titles; whether each reaches READY depends on the intake).
- Smallest safe fix: one shared `LANDCLASS` regex extended with `natura|habitat|designated|protected (area|site|land)s?|land ?cover|easement|surface management|aonb|outstanding natural beauty|biosphere|heritage|discomap\.eea|cdda|wdpa|schutzgebiet`, applied in the hunter, world finder, collector AND BOT W (a land-class layer is never wired, hand-approved or not, without Brandon's word).

### 20. The AREA_BOX / neighbour fix (bugs 3 + 4) brings in neighbours by PIN only, and files by center only
- Where: `kpc_fers.py:2669-2683` (`_in` from own-outline pins ± 0.2°; `_near` = a park filed elsewhere whose PIN lies in the box), `:2951` (every spot whose CENTER is outside the box is left "for its own area").
- What is wrong: the fix is right for the two reported cases. But a big park filed under another state whose pin is more than ~20 km from this area's pin box never joins the run, and its own state's run has the same problem in reverse, so the pair is found by neither.
- Example: Yellowstone (WY pin) x Custer Gallatin NF (MT pin near Bozeman); George Washington & Jefferson NF (VA pin) x West Virginia parks; any national forest whose pin sits one state over. (`data/fers/US-ME.json` still carries 4 AT rows at 42.7 N (MA / NH) dated Oct 29: Maine has not rerun since the fix.)
- How sure: likely.
- Smallest safe fix: in `_near` use the park's outline box from the key (`data/us-key` `parts` / the saved PAD-US box, `CLIP`) intersecting `_ab`, not only the pin; keep the center filter.

### 21. Water tiles read LIVE are saved at the pass's detail (pass 1 = 50 m) and reused in pass 3 for the 100-ft-from-bank test
- Where: `kpc_fers.py:839` (`_wlive`: `maxAllowableOffset: DET`, DET = 0.0005 in pass 1), `:812-817` (`_wsave` keeps the tile with no detail mark), `:871-898` (saved tile wins over live). The bulk tiles are 2 m (`kpc_water_bulk.py:22`).
- What is wrong: a tile the bulk job missed, read in pass 1 at 50 m, is the "bank" pass 3 measures 100 ft from.
- Example: any water-route or area water check whose tile was first read live in pass 1 (the Southeast run where USGS was down for most of pass 5 had many).
- How sure: likely.
- Smallest safe fix: `_wlive` always fetches at `0.00002`; or save the detail in the tile and re-read when a finer pass needs it.

### 22. A line-only river whose water tile is missing falls back SILENTLY to the centre line; Canada / world rivers never use the bank; the card still says "RIVER BANK"
- Where: `kpc_fers.py:1557-1559` (`kind == 'river' and PASS >= 2 and lref.startswith('US-')`; `nhd_water(...) or []` → no water = measure from the line, no NOT SURE); `kpc-overlap-finder.js:62, :75` (`g.river` is set when ANY patch is `river`, so trail-line patches of the same pair are labelled "WITHIN 100 FT OF THE RIVER BANK"); `:90` ("stretches of trail ... band along the line" for river rows).
- What is wrong: R7 / plain answer 7 = 100 ft from the water's edge; a missing tile must be NOT SURE (the water-route path does that at `:1497-1501`, this path does not). Labels promise the bank where the code used the line.
- Example: every Canadian line-only river park (`CA-` never reaches the bank branch); a US WSR line in a tile USGS did not answer for.
- How sure: sure (code paths); check (how many rows hit the missing-tile case).
- Smallest safe fix: when `nhd_water` returns `None` for a river mark the row `water_unchecked`; in the Finder set the badge per PATCH kind (and "water" only for `water_route` rows), and say "river bank" in `sizeLine` for those.

### 23. Line rows with 0-50 m of trail are live rows (no length floor), while areas under 25 yd are hidden
- Where: `kpc_fers.py:75` (`STRETCH = 0.0`), `:1576` (`if L >= STRETCH`: a one-point run passes with `len_m 0`), `rule15()` `:2184` (width only).
- What is wrong: R9 hides an area under 25 yd across; a trail that clips a park corner for 2 m becomes a "POSSIBLE TRAIL OVERLAP" row with "about 0.0 mi".
- Example: 20 live trail / river rows under 50 m: `CA-0075+CA-6151@trail` 0 m, `US-4567+US-8955@river` (DE) 2 m, `US-11904+US-4490@trail` (MN) 1 m, `US-0771+US-4571@trail` (AZ) 3 m.
- How sure: sure.
- Smallest safe fix: a numbered rule for Brandon (R9 for lines: e.g. under 25 yd of trail = not shown, 25-100 yd = 'very tight'); until then at least `STRETCH = 22.86` (25 yd) with the dropped rows kept on the review list.

### 24. The agency's own record is dropped in favour of PAD-US when names match (R-G1 order inverted)
- Where: `kpc_us_key.py:358` (FWS realty vs PAD-US by name only, no location), `:643` (`_dup(have, ...)` skips the STATE record when a same-name PAD-US record overlaps), `:520-525`.
- What is wrong: source order is agency layer → national agency layer → PAD-US last; here PAD-US is read first and the agency's record is thrown away as a "copy", so the outline drawn is PAD-US's (older, generalised, different id space). The FWS test has no overlap test at all.
- Example: 326 NWR parks joined to PAD-US only vs 14 with an `fws` record; 1,661 joined parks are PAD-US-only, 356 of them state-kind parks in states that have their own agency layer.
- How sure: likely.
- Smallest safe fix: when `_dup` finds an overlapping same-name pair keep the agency record and mark the PAD-US one as the `twin` (not drawn); give `fws_state` the same bbox-overlap test as `_dup`.

### 25. Water-only outlines are now graded `official` (the key's grade overrides the site's "shoreline, not the land" note)
- Where: `kpc_us_key.py:941` (`how += ' · water outline only'`), `:1340` (`g = 'official'` unless WEAK / approx); `kpc-bounds.js:268` (`grade ? grade === 'approximate' : (... || water ...)`).
- Example: 75 US parks whose every record is `water outline only` (Idaho / Washington / Arkansas lake layers), all `g: official`.
- How sure: likely.
- Smallest safe fix: grade `approximate` when every record is water-only (R-G4 lets the water record join; it does not make it the park's boundary).

### 26. 'candidate (saved outline only)' rows pass all three passes but the Finder hides them with no count
- Where: `kpc-overlap-finder.js:55` (`if (st !== 'candidate') return;`), `:187`.
- Example: KY `US-10140+US-3790@area@36.509,-88.057`, `US-3790+US-3791@river@36.501,-88.066`; W-GB 333 of 853 rows; W-FR 44,587.
- How sure: sure.
- Smallest safe fix: treat `/^candidate/` as live with a small "saved outline only" badge (the text is in `s.fresh`), or count them in the header.

### 27. 'Same land' rows store an every-80th-point outline (R-G6) and the Finder cannot snap it to the edges
- Where: `kpc_fers.py:2976` (`ring[::max(1, len(ring) // 80)]`); `add_lines` `:2694, :2030` runs for `area` / `trail` only, so these rows have no `lines` for `onEdges`.
- Example: 1,027 'same land' rows (the Fort Heiman / Fort Donelson row among them).
- How sure: sure.
- Smallest safe fix: `sharp_shape(ring)` instead of every Nth; include `same land` in `add_lines`.

### 28. Swapped Canadian pins are corrected in the key only
- Where: `kpc_ca_key.py:493-494` (`elif abs(la) > 90: la, lo = abs(lo), -abs(la)`); not in `kpc_fers.py:125-132` (`pins()`), `kpc_fers_far_hold.py:20`, `kpc_fers_line_check.py:93`, `kpc_fers_expected.py`.
- Example: CA-2395 Churchill WMA (92.595, -57.056), CA-2456 Maple Lake WMA, CA-2538 Westlake WMA; `data/fers/CA-MB.json`: Churchill row held "4480 km from ... POTA pin".
- How sure: sure.
- Smallest safe fix: fix the three pins in `parkinfo` once (and keep the key's swap as a guard).

### 29. Smaller findings (one line each; all sure unless marked)
- `kpc_layer_collector.py:28, :407-408`: the LAYER-line regex requires a bare ref in cell 2, so 23 of chat 8's 125 lines (`LAYER | US-4564 Potomac Heritage NST | ...`, and 18 `arcgis.com/sharing/rest/content/items/...` lines) are skipped with nothing written to `collector.json`. Fix: `([A-Z0-9]{1,4}-\d{4,5})[^|]*` + a `failed` row for any `LAYER |` line that still does not parse.
- `kpc_waiting_room.py:613, :703, :68-70`: `data/fers/W-*.json` (28 files) match no route, so `divert` leaves a changed world 2-fer file live and unchecked, with no notice (likely; world 2-fers are on hold).
- `kpc_release_approved.py:92-103`: a single-FILE YES releases whatever is in the slot even if a newer build landed after the YES (`changed_since_yes` only runs for folders); `:52 + :107`: the keyed-parking PASS is never marked used (n = 0 adds no log row) — likely.
- `kpc_release_approved.py:97, :101` + `kpc_waiting_room.py:819-822`: a `mode_release` REFUSAL (unreadable JSON, path outside `data/`) is still logged "released" and the YES consumed.
- `kpc_release_approved.py:63-64`: `changed_since_yes` keys on the first 40 characters of the verdict, so `KEY YES 2026-10-30 30/30 (names/kinds/ac` is shared by us-key and ca-key; a later `KEY NO` on the same path is not consulted — check.
- `kpc_key_summary.py:54` (`if o is None: continue`): the first build of an area (or any new POTA park) shows "gained 0, sample 0" to chat 11 — likely.
- `kpc_auto_flow.py:128`: the licence test regexes `ask` over the whole stringified terms dict, so every Alaska / Nebraska layer is "licence not open" for ever (fails closed; harmless but disables AUTO-2 there).
- `kpc_tiers.py:142` (bare `continue` on a corrupt question file = no learned NOs, everything re-asked); `kpc_layer_collector.py:173` (a crawler layer that failed once on a transient error is never retried: 97 of 163 crawl entries `failed`); `kpc_waiting_room.py:56` (`load()` → None makes an unreadable LIVE file "first publish", so the shrink checks do not run); `kpc_release_approved.py:30, :37`: all silent skips. Fix: one `notice()` line per skip.
- `kpc_fers.py:2383`: trail rows never get the water check (`land_check` is `area` only): a trail along a reservoir inside a Corps / WMA polygon gets a strip on the water (R7) — check.
- `kpc_fers.py:1107-1113, :1578`: for a `trail` row the owner is read at the row CENTER = a point ON the trail line (for an NHT, 1:100k, often off the park), so `ownership_step` can say "no public owner" for a stretch whose land is public (only when the parks' owners are not already known) — check.
- `kpc_fers.py:236, :253`: a key park with no pin is counted in `skip['no pin']` but gets no `SKIPWHY`, so the missing check cannot say why; `pins():129` accepts a lat with no lon.
- `kpc_fers.py:1874`: the Oct 31 access-pin fix (road must be within 60 m of the parks' own land) applies only when the row has an AREA park; trail x trail rows can still pick a road across a river.
- `kpc_fers_far_check.py:75`: `km from (.+?)'s POTA pin` stops at the first apostrophe ("Tate" for Tate's Hell SF): 3 FL rows match on one word.
- `kpc_us_key.py:1313`: the twin (do-not-draw-twice) test is blind when a record has 0 acres: 3,956 of 9,336 multi-record parks have one; no `twin` exists in any saved file yet.
- `kpc_us_key.py:806/809`: `split_places` decides in degrees (`max(.1, 2*size)`) and labels `round(d*100) km`: 0.1° is 11 km N-S, 8.7 km E-W at 38 N, 5.6 km in Alaska.
- `kpc_ca_key.py:506`: city / regional greenspace joins (165) graded `official`; R-G1 wants the managing body's own map (they often are; check).
- `kpc-bounds.js:478, :483`, `kpc-park-info.js:106, :112`: KML / GPX exporters iterate polygon rings only, so a trail park's download holds just the pin.
- `kpc-bounds.js:75, :170-174, :178`, `kpc-kit.js:253`: a KY layer or `data/trails` fetch that fails is swallowed; Am I in the Park then says NOT INSIDE and the Kit prints "Pin only (no official outline yet)" as if the key said so.
- `.github/workflows/kpc-ky-key.yml:21-23` (`continue-on-error` + `|| true` on the data overlay, which `kpc_overlay.sh:5-6` asks not to do): one failed overlay rebuilds the KY key with no `data/trails` and the three trails go back to `missing` — likely.
- Polygon wording on line parks: `kpc-park-control.js:36` (`btrail` → "State park land"), `kpc-access.js:106-109` ("inside / outside the park line"), `kpc-us-planner.js:405` ("Official Kentucky boundary shown (N pieces"), `kpc-in-park.js:99, :135`, `kpc-overlap-finder.js:457` ("Inside both outlines"). R5 wording: "within 100 ft of the trail".
- Zoomed-in drawing: Leaflet's default `smoothFactor` 1 (not overridden in the five outline drawers) drops sub-pixel vertices (~15 m at zoom 13: invisible, but not "exactly the stored line"); `kpc_fers.py:2218` re-simplifies a patch over 400 points up to 200 m (Mammoth Cave x Green River); `onEdges` snaps only within 20 m — check.
- `0.00003°` = 3.3 m of latitude (`kpc_us_key.py:538`, `kpc_state_trails.py:445`, `kpc-bounds.js:139`): under the 5 m limit; say "~3.3 m".
- Distance math otherwise checked clean: `Frame` (111,320·cos(lat) / 110,574), `edge()` / `segDistKm` (111.195 km/° both axes: 0.6 % high, 0.2 m at 100 ft), haversines 6371 km / 3958.8 mi, thresholds 30.48 / 45.72 / 91.44 m; `ZONE = 30.48 - 5` is 5 m STRICTER than POTA (documented).

---

## PART 2. The seven known bugs: is each fix right?

1. **KY river trails (Ballard WMA x Trail of Tears x Lewis and Clark).** Which does the code use: BOTH. The bank method (`water_route_spots`, right by R5 / plain answer 7, label right for those rows) AND the trail-line method on the same lines (finding 12). Why no line drawn: the Oct 31 Finder fix (`kpc-overlap-finder.js:394-403`) is right and will draw the dashed NPS line from `line_source` once a row carrying `line_source` is on the live data; the Oct 30 rows have it, so it should draw now — but the shaded zone is the strip's OUTLINE drawn as a line with a 100-ft band (finding 13), not the Oct 31 water fix's doing. Are the miles right: no (finding 14); the Oct 31 "river only" fix narrows which water counts but not the formula, and the live rows are still the Oct 30 run. Access pin fix (`kpc_fers.py:1872-1881`): right for rows with an area park.
2. **Trails as 'pin' in the key.** US key: code right (`kpc_us_key.py:737-746, :1341-1343`, `layers.json` `file:` entry `:1498`, read by `kpc-bounds.js:240-243`), NOT YET IN THE DATA (every US key file still `g: pin, m: []` for the national trails; last key run 09:57 UTC, code commit 15:41 UTC). Kentucky key: the `trl` block is unreachable and the `btrail` tract breaks the 2-fer bot (finding 15). Canada key: nothing (finding 10). Site: Kit, bounds drawer, Access Finder (KY list) and Park Control handle a line; Park Info does not (16); Am I in the Park is inverted (17); `usKey` ignores `joined_in` (8); KML / GPX empty (29). Note `kpc_fers.py:446` `download()` cannot read a `file:...{n}` id if a `trl` park ever reaches it (today `TRAIL_BY_LINE` pops them first, outside Kentucky).
3. **AT x Virginia filed under Maine.** Fix right (`kpc_fers.py:2949-2958`). `data/fers/US-ME.json` still has 4 AT rows at 42.7 N dated Oct 29: Maine has not rerun. Same class elsewhere: finding 2 (multi-state halves never join), 20 (neighbours by pin only).
4. **Georgia pin stretched Maine's box.** Fix right (`:2666-2670`, `_in` excludes line parks). Key side builds no box from pins, nothing to fix there. Same class: finding 20.
5. **Iowa renumbered ids.** The by-name fallback works for the case it was written for; the other half (an id that still exists but now names another feature) has no check at all, and the fallback keeps one tract: finding 3.
6. **Release only took 'YES' at the start.** Regex right for `KEY YES` / `Yes.` / `yes 1-5` / lower case / `\r\n` / NBSP; still blind to a leading quote / emoji / `**YES**` / `KEY: YES`, releases on `YES ... NO ...`, and the exact `by == 'chat 11'` test is blocking MN and IA today: finding 6. Same class: 5, 29 (LAYER regex, exact `YES` in the answer writers).
7. **SSSI nearly auto-approved.** AUTO-2 guards right (`kpc_auto_flow.py:124-125`, `kpc_key_layers.py:54`). But a hand `approved_by` is the ONLY guard in BOT W, the SSSI units row now carries one, and the land-class regex misses Natura 2000 / NatDA / AONB / easements: finding 19.

---

## PART 3. Suggested order for chat 2 (smallest fixes, biggest reach)
1. Release gate `by` test (6) — two approved states are waiting. 2. `answer_of()` shared, NOT SURE ≠ NO (5). 3. World `st` cut (4). 4. `chk=True` for US ids + fallback keeps every same-name tract (3). 5. Kentucky key `btrail` → `trl` (15) before the next KY pass. 6. Water-route rows: polygon in, polygon drawn, `elif` on the line test (12, 13). 7. `usKey` `joined_in` (8) + Park Info reads the KY key (16) + Am I in the Park line verdict (17). 8. Trails bot at 3 m with the route field, no polygons (7). 9. 0.6° box → name test first (2). 10. World grade field + shards (9, 1; world finder frozen: note for Nov 6). Then 10, 11, 18, 19 and the rest.

Grey areas for Brandon (new, numbered): (a) a length floor for trail / river rows (23); (b) should EEA-only world outlines be shown at all before a national layer is found (9).
