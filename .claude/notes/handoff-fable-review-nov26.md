# Hand-off for Fable: review the matching and key code (26 Nov 2026)

You are the REVIEWER (read and judge; the owner merges). Owner: Brandon (KPC owner). Builder: the Opus builder chat.
Plain words in everything you write for the owner: short sentences, what is wrong, how sure you are, what to do.

## Read first (only these)
- `.claude/CLAUDE.md` house rules. Still in force: **NO BUILDING** (no key build, outline rebuild, Release or 2-fer run, no dispatch),
  never ask the owner about a rules hash, a hold or a park, **proof or the pin**, old saved answers are hints only.
- `.claude/RULES-NOW.md`, then `.claude/notes/rule-sheet-stable-ids-nov25.md` (THE BETTER MATCHER: same land by agency id, shared ground,
  name + size; G1-G4 ruled 25 Nov).
- `.claude/notes/key-quality.md` sections 9 (grade only with `kpc_key_factcheck.py` / `kpc_key_grade.py`, never against saved answers,
  never by name alone) and 13 (what a rule PR must bring).
- `.claude/notes/handoff-matching-nov26.md` (where things stand today).

## What to review
1. **KPC-Links main, merged 26 Nov 10:20-10:22 AM** (US rules now `5b6caa7b7e90`, CA `d0352dfc270b`):
   - #382 batch 17: `.github/scripts/kpc_same_land.py`, `kpc_us_key.py`, `us-key-rule-scope.json`, tests `test_batch17_nov25.py`.
     Thin shapes are can't-tell (Old Croton), twin PAD-US copies are one land (Wertheim), same-ground records count once (Helen McNitt).
   - #383 batch 18: `kpc_same_land.py`, `kpc_store_attrs.py` (MN DNR's own ids for state forests and parks; publish_keys clash fix;
     id file format 14; 26 agency-id layers wait in AGENCY_ID_LATER).
   - #384 speed: `kpc_same_land.py` (rings filed by box, grid points once; must give the SAME answers; `test_speed_nov26.py`).
2. **KPC-Store draft PR #38** (layer records): `engine/kpc_layer_records.py` (every record of every joined layer, per-layer manifest,
   complete only when the download holds the layer's own count), hand files and `hand-file-names.csv`, `--again-urls` (the keeper's
   out-of-date list, now served on the PC), the count asked 3 times, the owner's ruling "no terms use it" in `verified-layers.csv` /
   `owner-decisions.csv` (sgaki, sgutc, sgwae, St. John's Planning 5, federal DFRP 4: fetch yes, publish unchanged).
3. **KPC-Links draft PR #386**: PC kit finds the store in the new PC folder names (no rule change).

## The owner's PC test of the merged code (kit 26a, reports\test-2026-11-26-0951)
- MN: 323 parks, 313 outlined (same as before), 267 confirmed, 3 pin only; 60 rows of 32 parks left the map ("proof or the pin":
  25 not proven, 25 only in the old saved copy, 9 proven by named records but this record has another name, 1 layer not in store).
- NY: 851 parks, 823 outlined (820 before); US-0481 Wertheim, US-10040 Old Croton, US-2071 Helen McNitt came back.
  Outline -> pin against the website: US-0681 Upper Delaware, US-2006 Artpark, US-2097 Lock 32, US-2137 Schunnemunk,
  US-5270 Reinstein Woods, US-8319 Palisades Interstate, US-8629 Ludlow Creek, US-9124 Charles Flood.
- Time: MN 46 -> 5.5 min, NY 9.8 -> 3.9 min. Size far from official acres: MN 1 (US-0367), NY 5.

## Questions to answer
1. Same land: can shared ground, the twin rule or "count once" join two DIFFERENT lands (false yes)? Can the thin-shape rule (~656 ft)
   hide a real park? Show any case from MN / NY.
2. The 60 MN rows that left the map: real wrong records, or good records the proof misses? Give the 5 most likely good ones and which
   proof would catch them under the existing rules (no new rule without a rule sheet).
3. The 8 NY outline -> pin parks: name variants (Artpark / Earl W. Brydges, Lock 32 / Canal Park, Reinstein Woods, Ludlow Creek,
   Charles Flood). Is "name + size" too strict here, or are these right as pins?
4. #384: any path where the speed change could give a different answer (box filing, grid points, edge cases at area borders)?
5. PR #38: is "complete only when the download holds the layer's own count" applied everywhere the keys trust the manifest? Can a
   hand file under an alias (`hand-file-names.csv`) be read for the wrong area or layer?
6. Leads (owner: "dont forget"): `C:\KPC\7-NOTES\leads-nov26\LEADS-pin-only-parks-with-a-proposed-outline.csv` (194 pin-only parks with a
   SURE/STRONG proposed outline from the paused engine: US 121, CA 73). Say how to prove them with the existing matcher rules, and
   pick 10 to check first. They are leads, never answers.

## How to report
- One short list: finding, file:line, how sure (sure / likely / can't tell), what to do. Real cases with park numbers.
- Fixes only as a DRAFT PR on a branch (never main), with tests; a change that moves a rules hash follows key-quality.md section 13 and
  the 25 Nov rule (changelog line, the other builder grades, the owner's PC test).
- No builds, no dispatch, no Release. Read-only on the PC unless the owner says go.
