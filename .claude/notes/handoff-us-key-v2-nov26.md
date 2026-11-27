# Hand-off: the clean v2 US key matcher (26 Nov 2026, about 8:50 PM CT)

Read this first in a new matching chat. Plain words. Owner: KPC owner. Nothing is merged. Nothing is live. NO BUILDING stays.

## Where things stand
- **KPC-Links #393** (branch `feat/us-key-v2-nov26`, draft): the v2 matcher, side by side. `kpc_us_key.py` is not touched and no
  rules hash moves (US stays as on main).
- **On the owner's PC** (`C:\KPC\5-ANSWER-KEY-TEST`, 8 new files, read back equal): `V2-SIDE-BY-SIDE.bat`, `V2-STATE-PREP.bat`,
  `V2-README.txt`, `kpc_test_v2.py`, `kpc_v2_scorecard.py`, `kpc_v2_state_prep.py`, `kpc_us_key_v2.py`, `us-key-v2-rules.json`.
  The matcher and its table sit BESIDE the button there (the bridge cannot write into `links\.github`). Nothing of the old kit changed.
- **Rule sheet:** `.claude/notes/rule-sheet-us-key-v2-nov26.md` (the five steps, the gate, the repair method, grey areas V2-G1 to G6,
  section 11 = the first full run's numbers).

## What v2 is, in five lines
1. Reads ONLY today's layer files, the park facts, the park list and one rule table. Never an old copy, `~old`, the website key, a hold.
2. Steps: check the locks (a witness, never decides) -> agency id -> name with a second proof -> pin only (one reason) -> the gate.
3. Every rule, word list and number is a row in `.github/us-key-v2-rules.json` with a "why" and the name of its test. No switches.
4. The gate is a hard stop: no `~old`, no record on two parks, every record in today's file, id joins carry the id, no park on a
   same-named park's land.
5. Same files in = the same bytes out. A run with locks = a run without.

## The numbers (Fable's own run on the PC's 26 Nov MN + NY layer files, against test-2026-11-26-1654)
- Outlined: MN 310 -> 295, NY 822 -> 819. Fair count (21 parks v1 drew from trail lines the store room does not hold, set apart):
  MN 293 -> 295, NY 818 -> 819. Scorecard: V2 PASSES, every gate.
- Pin inside the land: MN 86.9% -> 87.5%, NY 98.4% -> 98.8%. Size agrees: MN 34 -> 35 of 40, NY 29 of 36 -> 29 of 37.
- Check rows 767 -> 0. Build: MN about 16 s, NY about 21 s (v1: 4.2 and 3.0 minutes).
- Same land, on the shapes: v2 covers at least 90% of v1's land in 93.5% (MN) and 95.4% (NY) of parks. The rest: 29 parks where
  v1 held another unit's land (402,030 acres), 4 left out on purpose (easements, land under water), none where v2 misses its own.
- No park on a same-named park's land: v2 0, v1 5.

## How to work on it (the repair method; do not patch around it)
- A fix is a ROW in the rule table + its test. The test run changes every number, empties every table and switches every rule
  off; the test named for it must fail. A rule no test would miss fails the run.
- Try before you change anything: `py -3.12 kpc_test_v2.py MN NY --try my-rules.json` (a copy of the table with your row). It
  lists the parks that gain or lose an outline and whose land changes. The real key and table are not touched.
- A new state: `V2-STATE-PREP.bat` first (store room check, id fields with proof, name styles, official names against POTA's).
- Never a pass that changes the key after the matcher. Never a switch. Never read old data.
- Tests: `python3.12 tests/test_us_key_v2_nov26.py`, `tests/test_v2_scorecard_nov26.py`, `tests/test_v2_state_prep_nov26.py`.

## Waiting on the owner
1. Run `V2-SIDE-BY-SIDE.bat` on the PC (Enter = MN NY, about 2 minutes). Read `reports\v2-...\V2-SCORECARD.txt`.
2. Store room: LAYER-RECORDS for SC (`sgnca` failed, so SC, the control state, is not built); the trail-line layer is not in
   the store room (17 MN + 4 NY parks cannot be drawn).
3. Rulings: V2-G4 (Fish and Wildlife easement tracts stay off every park), V2-G5 (an agency page that groups other named land:
   list `v2-id-other-names.csv`), Lake Vermilion US-2506 / US-7148 (one record, two park numbers: both stay pins today).
4. The page reader ran again on 26 Nov evening: rebuild the park facts from it, then rerun v2 (tonight's numbers use 24 Nov facts).

## Next jobs, in order
1. Read the owner's PC run of v2. It must match the numbers above (same layer files) or the difference must be explained.
2. "Other spellings" table (the owner said yes to the idea, not yet built): US-0474 Elizabeth A. Morton / Elizabeth Alexandra
   Morton, US-2147 Sunken Meadow / Alfred E. Smith/Sunken Meadow. A spelling row only says "another way to write the name"; the
   pin or the size must still prove the land. One table, one test, tried on the workbench first.
3. SC as the control state once its layer is in (scratch run: 146 of 167 against v1's 161; the prep tool lists the SC name styles).
4. Canada: the store has the CA layer files in the same format. Check for "US-" typed in the code, then one small province with
   table rows only (agency id fields, kind words, French and English names).
5. Only when v2 beats v1 on the PC and the owner says so: v2 replaces v1, its file joins the US rule files, the hash moves once.

## Added later on 26 Nov (after the owner's PC run)
- **The owner's PC run (8:55 PM): V2 PASSES**, MN 295, NY 819, MN 9 s and NY 11 s; the key text is the same as Fable's run
  (`key_text_sha256` in v2-run.json: MN ddb89b90..., NY 2294966e...; the ZIP bytes differ between Windows and Linux, the text
  does not). It compared with test-2026-11-26-2014 (the newest finished v1 test): v1 MN 311, NY 822, fair count 294 and 818.
  That v1 key still has the 5 same-named-park hits.
- **State prep takes several states or `US`** (one state per process, about 1.5 GB at its peak). On the 14 states staged
  here: v2 can build 8 (CT IA MN NJ NY PA SD WI); 6 are blocked by the store room (sgnca: GA NC SC; sgmaa: MA, one shapeless
  record of 61,486; sgaki: ND; vta: VT). 51 proposed id rows, including a Georgia layer whose Website field holds the park's
  own page address for 118 parks.
- **Trails and far pins are built in v2** (rule sheet section 12): line records, the 100 ft pin distance, the far-pin waiver
  for parks POTA lists in several states. Fixture-tested only for lines: no layer file holds a line.
- **KPC-Store job, not started, the owner has not said go:** `kpc_layer_records.py` must keep the `trl` / `line` layers and
  save line shapes as `paths` + `"shape": "line"`; and one shapeless record should not mark a whole layer "not complete"
  (that alone blocks MA). Running it means a LAYER-RECORDS download: the owner's button.
- **Small fixes still open in the tools:** the scorecard does not name the v1 test it compared with; the scorecard and the
  map side do not know lines yet; the "other spellings" table is not built.

## For the other builder (#392 and later patches to v1)
- "Full land kept" is not a pass mark where the land is another unit's: US-5106 Bear Swamp (Otsego): PAD-US 236421 holds about
  3,626 acres of US-5107 Bear Swamp (Cayuga), 134 km away. US-4820 Red Lake State Forest: three "Red Lake WMA" rows, about
  324,500 acres. The scorecard's G11 check finds 5 such hits in the 1654 key.
- v2 folded in from #388 / #390 / #392: fresh only, the MN forest line dropped at load, agency spelling, the name gaps, the same
  place under a longer or shorter name, the lock's zero-size and all-records rules. Not taken: "name and old joined size".

## House rules that bit today
- The bridge will not write into `links\.github` on the PC: put v2 files beside the button, or ship a kit zip the owner unpacks.
- The scorecard must not import v1 code: main's `kpc_store_attrs` changed its id spelling mid-evening and the v1 numbers broke.
- Agents run no git. One Python (3.12). Read the reply's counts back from the files before telling the owner.
